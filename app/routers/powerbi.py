"""Flux de données pour Power BI, Excel Web et tout outil de BI externe.

L'authentification se fait par un jeton passé en paramètre d'URL, afin que le
connecteur « Web » de Power BI Desktop puisse interroger la plateforme sans
en-tête HTTP personnalisé.
"""
import csv
import io
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (Activity, BudgetLine, Indicator, LogframeElement, Project, Risk, User)
from ..security import current_user, decode_token
from ..services import analytics

router = APIRouter(prefix="/api/powerbi", tags=["Power BI"])


def _autoriser(token: Optional[str], db: Session) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Jeton requis (paramètre ?token=).")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expiré.")
    user = db.query(User).filter(User.email == payload["sub"], User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Compte introuvable ou désactivé.")
    return user


def _tables(db: Session, project: Project) -> Dict[str, List[Dict[str, Any]]]:
    indicateurs = db.query(Indicator).filter(Indicator.project_id == project.id).all()
    faits_realisation, faits_cible = [], []
    for i in indicateurs:
        for t in i.targets:
            faits_cible.append({"CibleID": t.id, "IndicateurID": i.id, "CodeIndicateur": i.code,
                                "Periode": t.period_label, "Annee": t.year,
                                "ValeurCible": t.target_value})
        for a in i.actuals:
            taux = analytics.taux_realisation(i.baseline_value, i.target_value, a.value, i.direction)
            faits_realisation.append({
                "RealisationID": a.id, "IndicateurID": i.id, "CodeIndicateur": i.code,
                "Periode": a.period_label, "Annee": a.year,
                "DateReference": a.reference_date.isoformat() if a.reference_date else None,
                "ValeurRealisee": a.value, "Source": a.source,
                "Validation": a.validation_status, "TauxRealisation": taux,
                "StatutPerformance": analytics.statut_performance(taux)})
    return {
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
def dataset(project_id: int, token: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Modèle complet au format JSON, à consommer via Power BI > Obtenir des données > Web."""
    _autoriser(token, db)
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    tables = _tables(db, projet)
    return {"projet": projet.code, "genere_le": date.today().isoformat(),
            "tables": tables,
            "compteurs": {nom: len(lignes) for nom, lignes in tables.items()}}


@router.get("/{project_id}/table/{nom_table}")
def table_json(project_id: int, nom_table: str, token: Optional[str] = Query(None),
               db: Session = Depends(get_db)):
    """Une table unique en JSON — pratique pour créer une requête Power BI par table."""
    _autoriser(token, db)
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    tables = _tables(db, projet)
    if nom_table not in tables:
        raise HTTPException(status_code=404,
                            detail=f"Table inconnue. Tables disponibles : {', '.join(tables)}")
    return tables[nom_table]


@router.get("/{project_id}/csv/{nom_table}")
def table_csv(project_id: int, nom_table: str, token: Optional[str] = Query(None),
              db: Session = Depends(get_db)):
    """Export CSV (UTF-8 BOM, séparateur point-virgule) directement ouvrable dans Excel."""
    _autoriser(token, db)
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
def lien_powerbi(project_id: int, request_token: str = Query(None, alias="token"),
                 db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Retourne les URL prêtes à coller dans Power BI pour le projet courant."""
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return {
        "instructions": [
            "Power BI Desktop > Accueil > Obtenir des données > Web.",
            "Coller l'URL « dataset » ci-dessous, puis développer la colonne « tables ».",
            "Ou créer une requête par table à partir des URL « tables ».",
            "Le jeton expire au bout de 12 heures : régénérez-le depuis la plateforme.",
        ],
        "dataset": f"/api/powerbi/{project_id}/dataset?token=<JETON>",
        "tables": [f"/api/powerbi/{project_id}/table/{nom}?token=<JETON>"
                   for nom in _tables(db, projet)],
        "csv": [f"/api/powerbi/{project_id}/csv/{nom}?token=<JETON>"
                for nom in _tables(db, projet)],
    }
