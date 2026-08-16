"""Flux de données pour Power BI, Excel Web et tout outil de BI externe.

L'authentification se fait par un jeton passé en paramètre d'URL, afin que le
connecteur « Web » de Power BI Desktop puisse interroger la plateforme sans
en-tête HTTP personnalisé.
"""
import csv
import io
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..crud import verifier_acces_projet
from ..database import get_db
from ..models import (Activity, BudgetLine, Indicator, LogframeElement, Project, Risk, User, Zone)
from ..security import NOM_COOKIE, current_user, decode_token, resoudre_cle_api
from ..services import analytics

router = APIRouter(prefix="/api/powerbi", tags=["Power BI"])


def _autoriser(request: Request, cle: Optional[str], db: Session,
               project_id: Optional[int] = None) -> User:
    """Authentifie un connecteur de business intelligence.

    Trois modes, du plus sûr au moins sûr : en-tête « X-API-Key », paramètre
    « cle » d'URL — le connecteur Web de Power BI n'accepte pas d'en-tête
    personnalisé —, ou cookie de session pour un appel depuis l'interface.
    Le jeton de session n'est plus accepté en paramètre d'URL : il finissait
    dans les journaux du serveur, l'historique du navigateur et le presse-papiers.
    """
    valeur = request.headers.get("x-api-key") or cle
    if valeur:
        acces = resoudre_cle_api(db, valeur)
        if not acces:
            raise HTTPException(status_code=401,
                                detail="Clé d'accès inconnue, révoquée ou expirée.")
        user = db.query(User).filter(User.id == acces.user_id,
                                     User.is_active.is_(True)).first()
        if not user:
            raise HTTPException(status_code=401, detail="Compte associé à la clé désactivé.")
        # Une clé peut être restreinte à un projet unique.
        if acces.project_id and project_id and acces.project_id != int(project_id):
            raise HTTPException(status_code=403,
                                detail="Cette clé ne donne pas accès à ce projet.")
        verifier_acces_projet(db, user, project_id)
        return user

    # Repli : session ouverte dans le navigateur (cookie ou en-tête Authorization).
    charge = None
    cookie = request.cookies.get(NOM_COOKIE)
    entete = request.headers.get("authorization") or ""
    if cookie:
        charge = decode_token(cookie)
    elif entete.lower().startswith("bearer "):
        charge = decode_token(entete[7:].strip())
    if not charge:
        raise HTTPException(
            status_code=401,
            detail="Accès refusé. Créez une clé de lecture depuis votre profil et transmettez-la "
                   "par l'en-tête X-API-Key ou le paramètre ?cle=.")
    user = db.query(User).filter(User.email == charge.get("sub"),
                                 User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Compte introuvable ou désactivé.")
    verifier_acces_projet(db, user, project_id)
    return user


def _tables(db: Session, project: Project) -> Dict[str, List[Dict[str, Any]]]:
    indicateurs = db.query(Indicator).filter(Indicator.project_id == project.id).all()
    zones = {z.id: z for z in db.query(Zone).filter(Zone.project_id == project.id).all()}
    activites = {a.id: a for a in db.query(Activity).filter(
        Activity.project_id == project.id).all()}
    faits_realisation, faits_cible, faits_desagregation = [], [], []
    for i in indicateurs:
        for t in i.targets:
            faits_cible.append({"CibleID": t.id, "IndicateurID": i.id, "CodeIndicateur": i.code,
                                "Periode": t.period_label, "Annee": t.year,
                                "ValeurCible": t.target_value})
        for a in i.actuals:
            taux = analytics.taux_realisation(i.baseline_value, i.target_value, a.value, i.direction)
            zone = zones.get(a.zone_id)
            activite = activites.get(a.activity_id)
            faits_realisation.append({
                "RealisationID": a.id, "IndicateurID": i.id, "CodeIndicateur": i.code,
                "Periode": a.period_label, "Annee": a.year,
                "DateReference": a.reference_date.isoformat() if a.reference_date else None,
                "ValeurRealisee": a.value, "Source": a.source,
                "ZoneID": a.zone_id, "Zone": zone.name if zone else None,
                "ActiviteID": a.activity_id, "Activite": activite.name if activite else None,
                "Validation": a.validation_status, "TauxRealisation": taux,
                "StatutPerformance": analytics.statut_performance(taux)})
            # Table de faits dépliée : une ligne par modalité, exploitable telle
            # quelle dans un graphique Power BI segmenté par sexe ou groupe cible.
            for categorie, modalites in (a.disaggregated_values or {}).items():
                if not isinstance(modalites, dict):
                    continue
                for modalite, valeur in modalites.items():
                    faits_desagregation.append({
                        "RealisationID": a.id, "IndicateurID": i.id, "CodeIndicateur": i.code,
                        "Periode": a.period_label, "Annee": a.year,
                        "ZoneID": a.zone_id, "Zone": zone.name if zone else None,
                        "Categorie": categorie, "Modalite": modalite, "Valeur": valeur})
    return {
        "Dim_Zone": [{
            "ZoneID": z.id, "ProjetID": z.project_id, "ParentID": z.parent_id, "Code": z.code,
            "Zone": z.name, "Niveau": z.level, "Population": z.population,
            "CibleBeneficiaires": z.beneficiaries_target, "Latitude": z.latitude,
            "Longitude": z.longitude, "Responsable": z.responsible} for z in zones.values()],
        "Fait_Desagregation": faits_desagregation,
        "Dim_Projet": [{
            "ProjetID": project.id, "Code": project.code, "Titre": project.title,
            "Acronyme": project.acronym, "Secteur": project.sector, "Pays": project.country,
            "Bailleur": project.donor, "Agence": project.executing_agency,
            "Statut": project.status, "Devise": project.currency,
            "BudgetTotal": project.total_budget,
            "DateDebut": project.start_date.isoformat() if project.start_date else None,
            "DateFin": project.end_date.isoformat() if project.end_date else None}],
        "Dim_Resultat": [{
            "ResultatID": e.id, "ProjetID": e.project_id, "ParentID": e.parent_id,
            "Niveau": e.level, "Code": e.code, "Enonce": e.statement,
            "SourcesVerification": e.means_of_verification, "Hypotheses": e.assumptions,
            "Responsable": e.responsible}
            for e in db.query(LogframeElement).filter(
                LogframeElement.project_id == project.id).all()],
        "Dim_Indicateur": [{
            "IndicateurID": i.id, "ProjetID": i.project_id, "ResultatID": i.element_id,
            "Code": i.code, "Libelle": i.name, "Niveau": i.level, "Type": i.indicator_type,
            "Unite": i.unit, "Desagregation": ", ".join(i.disaggregation or []),
            "Reference": i.baseline_value, "Cible": i.target_value, "Sens": i.direction,
            "Frequence": i.frequency, "SourceDonnees": i.data_source,
            "MethodeCollecte": i.collection_method, "Responsable": i.responsible,
            "IndicateurCle": "Oui" if i.is_key else "Non"} for i in indicateurs],
        "Fait_Cible": faits_cible,
        "Fait_Realisation": faits_realisation,
        "Fait_Activite": [{
            "ActiviteID": a.id, "ProjetID": a.project_id, "ResultatID": a.element_id,
            "Code": a.code, "Libelle": a.name, "Responsable": a.responsible,
            "DateDebut": a.start_date.isoformat() if a.start_date else None,
            "DateFin": a.end_date.isoformat() if a.end_date else None,
            "Avancement": a.progress, "Statut": a.status, "CoutPrevu": a.planned_cost,
            "CoutReel": a.actual_cost, "Annee": a.year, "Jalon": "Oui" if a.milestone else "Non"}
            for a in db.query(Activity).filter(Activity.project_id == project.id).all()],
        "Fait_Budget": [{
            "LigneID": l.id, "ProjetID": l.project_id, "ActiviteID": l.activity_id,
            "Code": l.code, "Libelle": l.label, "Categorie": l.category, "Unite": l.unit,
            "Quantite": l.quantity, "CoutUnitaire": l.unit_cost, "Nombre": l.frequency_count,
            "TotalPlanifie": l.total_planned, "T1": l.q1, "T2": l.q2, "T3": l.q3, "T4": l.q4,
            "Engage": l.committed, "Decaisse": l.disbursed,
            "SourceFinancement": l.funding_source, "Annee": l.year}
            for l in db.query(BudgetLine).filter(BudgetLine.project_id == project.id).all()],
        "Fait_Risque": [{
            "RisqueID": r.id, "ProjetID": r.project_id, "Code": r.code, "Titre": r.title,
            "Categorie": r.category, "Probabilite": r.probability, "Impact": r.impact,
            "Score": r.score, "Niveau": r.severity, "Statut": r.status, "Responsable": r.owner,
            "DateRevue": r.review_date.isoformat() if r.review_date else None}
            for r in db.query(Risk).filter(Risk.project_id == project.id).all()],
    }


@router.get("/{project_id}/dataset")
def dataset(project_id: int, request: Request, cle: Optional[str] = Query(None),
            db: Session = Depends(get_db)):
    """Modèle complet au format JSON, à consommer via Power BI > Obtenir des données > Web."""
    _autoriser(request, cle, db, project_id)
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    tables = _tables(db, projet)
    return {"projet": projet.code, "genere_le": date.today().isoformat(),
            "tables": tables,
            "compteurs": {nom: len(lignes) for nom, lignes in tables.items()}}


@router.get("/{project_id}/table/{nom_table}")
def table_json(project_id: int, nom_table: str, request: Request,
               cle: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Une table unique en JSON — pratique pour créer une requête Power BI par table."""
    _autoriser(request, cle, db, project_id)
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    tables = _tables(db, projet)
    if nom_table not in tables:
        raise HTTPException(status_code=404,
                            detail=f"Table inconnue. Tables disponibles : {', '.join(tables)}")
    return tables[nom_table]


@router.get("/{project_id}/csv/{nom_table}")
def table_csv(project_id: int, nom_table: str, request: Request,
              cle: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Export CSV (UTF-8 BOM, séparateur point-virgule) directement ouvrable dans Excel."""
    _autoriser(request, cle, db, project_id)
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    tables = _tables(db, projet)
    if nom_table not in tables:
        raise HTTPException(status_code=404,
                            detail=f"Table inconnue. Tables disponibles : {', '.join(tables)}")
    lignes = tables[nom_table]
    tampon = io.StringIO()
    if lignes:
        writer = csv.DictWriter(tampon, fieldnames=list(lignes[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(lignes)
    contenu = "﻿" + tampon.getvalue()
    return StreamingResponse(
        io.BytesIO(contenu.encode("utf-8")), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition":
                 f'attachment; filename="{projet.code}_{nom_table}.csv"'})


@router.get("/{project_id}/lien")
def lien_powerbi(project_id: int, db: Session = Depends(get_db),
                 user: User = Depends(current_user)):
    """Retourne les URL prêtes à coller dans Power BI pour le projet courant."""
    verifier_acces_projet(db, user, project_id)
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return {
        "instructions": [
            "Créer d'abord une clé de lecture depuis votre profil (Administration > Clés d'accès).",
            "Power BI Desktop > Accueil > Obtenir des données > Web.",
            "Coller l'URL « dataset » ci-dessous en remplaçant <CLE> par la clé obtenue, puis "
            "développer la colonne « tables ».",
            "Ou créer une requête par table à partir des URL « tables ».",
            "La clé est révocable à tout moment et n'ouvre qu'un accès en lecture ; elle ne donne "
            "pas accès à l'interface d'administration.",
        ],
        "dataset": f"/api/powerbi/{project_id}/dataset?cle=<CLE>",
        "tables": [f"/api/powerbi/{project_id}/table/{nom}?cle=<CLE>"
                   for nom in _tables(db, projet)],
        "csv": [f"/api/powerbi/{project_id}/csv/{nom}?cle=<CLE>"
                for nom in _tables(db, projet)],
    }
