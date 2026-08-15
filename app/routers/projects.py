"""Gestion du portefeuille de projets, tableaux de bord et référentiels."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import (CATEGORIES_RISQUE, FREQUENCES, LIBELLES_NIVEAUX, NIVEAUX_CADRE_LOGIQUE,
                      STATUTS_PROJET, TYPES_INDICATEUR, TYPES_QUESTION)
from ..crud import apply_payload, log_action, serialize, serialize_many
from ..database import get_db
from ..models import (Activity, Assumption, AuditLog, BudgetLine, Form, FormQuestion, Indicator,
                      IndicatorActual, IndicatorTarget, LogframeElement, Project, Risk, User)
from ..security import can_edit, can_manage, current_user
from ..services import analytics

router = APIRouter(prefix="/api", tags=["Projets"])


@router.get("/projects")
def liste_projets(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return serialize_many(db.query(Project).order_by(Project.code).all())


@router.get("/projects/{project_id}")
def detail_projet(project_id: int, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    donnees = serialize(projet)
    donnees["compteurs"] = {
        "resultats": db.query(LogframeElement).filter(
            LogframeElement.project_id == project_id).count(),
        "indicateurs": db.query(Indicator).filter(Indicator.project_id == project_id).count(),
        "activites": db.query(Activity).filter(Activity.project_id == project_id).count(),
        "risques": db.query(Risk).filter(Risk.project_id == project_id).count(),
        "hypotheses": db.query(Assumption).filter(Assumption.project_id == project_id).count(),
        "lignes_budgetaires": db.query(BudgetLine).filter(
            BudgetLine.project_id == project_id).count(),
        "formulaires": db.query(Form).filter(Form.project_id == project_id).count(),
    }
    return donnees


@router.post("/projects", status_code=201)
def creer_projet(payload: Dict[str, Any], db: Session = Depends(get_db),
                 user: User = Depends(can_manage)):
    if not payload.get("title") or not payload.get("code"):
        raise HTTPException(status_code=422, detail="Le code et l'intitulé du projet sont obligatoires.")
    projet = Project(created_by=user.id)
    apply_payload(projet, payload, Project)
    db.add(projet)
    db.flush()
    log_action(db, user, "CREATE", "Project", projet.id, projet.id, projet.code)
    db.commit()
    db.refresh(projet)
    return serialize(projet)


@router.put("/projects/{project_id}")
def modifier_projet(project_id: int, payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: User = Depends(can_manage)):
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    apply_payload(projet, payload, Project)
    log_action(db, user, "UPDATE", "Project", projet.id, projet.id)
    db.commit()
    db.refresh(projet)
    return serialize(projet)


@router.delete("/projects/{project_id}")
def supprimer_projet(project_id: int, db: Session = Depends(get_db),
                     user: User = Depends(can_manage)):
    projet = db.get(Project, project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    # Suppression explicite des dépendances (les bases SQLite n'appliquent pas
    # les contraintes ON DELETE CASCADE par défaut).
    identifiants = [i.id for i in db.query(Indicator.id).filter(
        Indicator.project_id == project_id).all()]
    if identifiants:
        db.query(IndicatorActual).filter(
            IndicatorActual.indicator_id.in_(identifiants)).delete(synchronize_session=False)
        db.query(IndicatorTarget).filter(
            IndicatorTarget.indicator_id.in_(identifiants)).delete(synchronize_session=False)
    identifiants_formulaires = [f.id for f in db.query(Form.id).filter(
        Form.project_id == project_id).all()]
    if identifiants_formulaires:
        db.query(FormQuestion).filter(
            FormQuestion.form_id.in_(identifiants_formulaires)).delete(synchronize_session=False)
    for modele in (BudgetLine, Activity, Indicator, Assumption, Risk, Form, LogframeElement):
        db.query(modele).filter(modele.project_id == project_id).delete(synchronize_session=False)
    db.delete(projet)
    log_action(db, user, "DELETE", "Project", project_id, project_id)
    db.commit()
    return {"deleted": project_id}


@router.post("/projects/{project_id}/dupliquer", status_code=201)
def dupliquer_projet(project_id: int, payload: Dict[str, Any], db: Session = Depends(get_db),
                     user: User = Depends(can_manage)):
    """Duplique la structure d'un projet (cadre logique, indicateurs, activités, budget, risques)
    sans reprendre les réalisations : utile pour créer un projet à partir d'un modèle."""
    source = db.get(Project, project_id)
    if not source:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    copie = Project()
    donnees = serialize(source)
    donnees.pop("id", None)
    apply_payload(copie, donnees, Project)
    copie.code = payload.get("code") or f"{source.code}-COPIE"
    copie.title = payload.get("title") or f"{source.title} (copie)"
    copie.created_by = user.id
    db.add(copie)
    db.flush()

    correspondance_elements: Dict[int, int] = {}
    for element in db.query(LogframeElement).filter(
            LogframeElement.project_id == project_id).order_by(LogframeElement.id).all():
        nouveau = LogframeElement(project_id=copie.id)
        apply_payload(nouveau, {k: v for k, v in serialize(element).items()
                                if k not in ("id", "project_id", "parent_id")}, LogframeElement)
        db.add(nouveau)
        db.flush()
        correspondance_elements[element.id] = nouveau.id
    for element in db.query(LogframeElement).filter(
            LogframeElement.project_id == project_id).all():
        if element.parent_id:
            cible = db.get(LogframeElement, correspondance_elements[element.id])
            cible.parent_id = correspondance_elements.get(element.parent_id)

    correspondance_activites: Dict[int, int] = {}
    for activite in db.query(Activity).filter(Activity.project_id == project_id).all():
        nouvelle = Activity(project_id=copie.id)
        apply_payload(nouvelle, {k: v for k, v in serialize(activite).items()
                                 if k not in ("id", "project_id", "element_id")}, Activity)
        nouvelle.element_id = correspondance_elements.get(activite.element_id)
        nouvelle.progress = 0
        nouvelle.status = "Planifiée"
        nouvelle.actual_cost = 0
        db.add(nouvelle)
        db.flush()
        correspondance_activites[activite.id] = nouvelle.id

    for indicateur in db.query(Indicator).filter(Indicator.project_id == project_id).all():
        nouveau = Indicator(project_id=copie.id)
        apply_payload(nouveau, {k: v for k, v in serialize(indicateur).items()
                                if k not in ("id", "project_id", "element_id")}, Indicator)
        nouveau.element_id = correspondance_elements.get(indicateur.element_id)
        db.add(nouveau)

    for ligne in db.query(BudgetLine).filter(BudgetLine.project_id == project_id).all():
        nouvelle = BudgetLine(project_id=copie.id)
        apply_payload(nouvelle, {k: v for k, v in serialize(ligne).items()
                                 if k not in ("id", "project_id", "activity_id")}, BudgetLine)
        nouvelle.activity_id = correspondance_activites.get(ligne.activity_id)
        nouvelle.committed = 0
        nouvelle.disbursed = 0
        db.add(nouvelle)

    for modele in (Risk, Assumption):
        for objet in db.query(modele).filter(modele.project_id == project_id).all():
            nouveau = modele(project_id=copie.id)
            apply_payload(nouveau, {k: v for k, v in serialize(objet).items()
                                    if k not in ("id", "project_id", "element_id")}, modele)
            db.add(nouveau)

    log_action(db, user, "DUPLICATE", "Project", copie.id, copie.id, f"depuis {source.code}")
    db.commit()
    db.refresh(copie)
    return serialize(copie)


# ---------------------------------------------------------------------------
# Tableaux de bord
# ---------------------------------------------------------------------------
@router.get("/dashboard/{project_id}")
def tableau_de_bord(project_id: int, db: Session = Depends(get_db),
                    user: User = Depends(current_user)):
    donnees = analytics.tableau_de_bord(db, project_id)
    if not donnees:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    return donnees


@router.get("/portefeuille")
def vue_portefeuille(db: Session = Depends(get_db), user: User = Depends(current_user)):
    projets = analytics.portefeuille(db)
    total_budget = sum(p["total_budget"] or 0 for p in projets)
    return {
        "projets": projets,
        "consolidation": {
            "nb_projets": len(projets),
            "budget_total": round(total_budget, 2),
            "sante_moyenne": round(sum(p["sante"] for p in projets) / len(projets), 1) if projets else 0,
            "nb_risques_critiques": sum(p["nb_risques_critiques"] for p in projets),
            "nb_alertes": sum(p["nb_alertes"] for p in projets),
            "par_statut": {statut: len([p for p in projets if p["status"] == statut])
                           for statut in {p["status"] for p in projets if p["status"]}},
        },
    }


@router.get("/indicateurs/suivi/{project_id}")
def tableau_suivi_indicateurs(project_id: int, db: Session = Depends(get_db),
                              user: User = Depends(current_user)):
    """Cadre de suivi des indicateurs : cibles et réalisations par période."""
    indicateurs = db.query(Indicator).filter(Indicator.project_id == project_id).all()
    periodes = sorted({t.period_label for i in indicateurs for t in i.targets} |
                      {a.period_label for i in indicateurs for a in i.actuals})
    lignes = []
    for ind in indicateurs:
        cibles = {t.period_label: t.target_value for t in ind.targets}
        reels = {a.period_label: a.value for a in ind.actuals}
        lignes.append({
            **analytics.indicator_performance(ind),
            "cibles": {p: cibles.get(p) for p in periodes},
            "realisations": {p: reels.get(p) for p in periodes},
        })
    ordre = {"IMPACT": 0, "EFFET": 1, "PRODUIT": 2, "ACTIVITE": 3}
    lignes.sort(key=lambda l: (ordre.get(l["level"], 9), l["code"] or ""))
    return {"periodes": periodes, "lignes": lignes}


@router.get("/referentiels")
def referentiels(user: User = Depends(current_user)):
    """Listes de valeurs alimentant les formulaires de l'interface."""
    return {
        "niveaux": [{"code": n, "libelle": LIBELLES_NIVEAUX[n]} for n in NIVEAUX_CADRE_LOGIQUE],
        "frequences": FREQUENCES,
        "types_indicateur": TYPES_INDICATEUR,
        "statuts_projet": STATUTS_PROJET,
        "categories_risque": CATEGORIES_RISQUE,
        "types_question": TYPES_QUESTION,
        "unites": ["Nombre", "%", "Ratio", "Score", "Indice", "Tonne", "Hectare", "km",
                   "FCFA", "USD", "EUR", "Jour", "Mois", "t/ha", "kg", "Litre"],
        "desagregations": ["Sexe", "Âge", "Région", "Milieu (urbain/rural)", "Handicap",
                           "Statut socio-économique", "Type de bénéficiaire", "Commune"],
        "statuts_activite": ["Planifiée", "En cours", "Achevée", "Retardée", "Annulée"],
        "statuts_risque": ["Ouvert", "Maîtrisé", "Clos", "Survenu"],
        "categories_budget": ["Personnel", "Équipements", "Formations", "Prestations",
                              "Missions et déplacements", "Fonctionnement", "Investissements",
                              "Communication", "Suivi-évaluation", "Imprévus"],
        "criticites": ["Faible", "Moyenne", "Élevée"],
        "statuts_hypothese": ["Non vérifiée", "Partiellement vérifiée", "Vérifiée", "Invalidée"],
        "sens_progression": ["Croissant", "Décroissant", "Stable"],
        "types_formulaire": ["Questionnaire", "Fiche de suivi", "Grille d'entretien",
                             "Grille de focus group", "Fiche de présence", "Fiche d'observation"],
    }


@router.get("/journal")
def journal_audit(project_id: int = Query(None), limit: int = Query(200, le=1000),
                  db: Session = Depends(get_db), user: User = Depends(can_manage)):
    requete = db.query(AuditLog).order_by(AuditLog.at.desc())
    if project_id:
        requete = requete.filter(AuditLog.project_id == project_id)
    return serialize_many(requete.limit(limit).all())


@router.post("/projects/{project_id}/periodes", status_code=201)
def generer_periodes(project_id: int, payload: Dict[str, Any], db: Session = Depends(get_db),
                     user: User = Depends(can_edit)):
    """Crée automatiquement les cibles périodiques d'un indicateur par interpolation linéaire
    entre la valeur de référence et la cible finale."""
    indicateur = db.get(Indicator, payload.get("indicator_id"))
    if not indicateur or indicateur.project_id != project_id:
        raise HTTPException(status_code=404, detail="Indicateur introuvable pour ce projet.")
    projet = db.get(Project, project_id)
    granularite = payload.get("granularite", "trimestre")
    annee_debut = payload.get("annee_debut") or (projet.start_date.year if projet.start_date else 2025)
    annee_fin = payload.get("annee_fin") or (projet.end_date.year if projet.end_date else annee_debut + 3)
    if annee_fin < annee_debut:
        raise HTTPException(status_code=422, detail="L'année de fin doit être postérieure à l'année de début.")

    periodes: List[Dict[str, Any]] = []
    for annee in range(annee_debut, annee_fin + 1):
        if granularite == "annee":
            periodes.append({"label": str(annee), "annee": annee,
                             "debut": f"{annee}-01-01", "fin": f"{annee}-12-31"})
        elif granularite == "semestre":
            for s in (1, 2):
                periodes.append({"label": f"{annee}-S{s}", "annee": annee,
                                 "debut": f"{annee}-{1 if s == 1 else 7:02d}-01",
                                 "fin": f"{annee}-{6 if s == 1 else 12:02d}-30"})
        else:
            for t in (1, 2, 3, 4):
                mois_debut = 3 * (t - 1) + 1
                mois_fin = 3 * t
                dernier_jour = 31 if mois_fin in (3, 12) else 30
                periodes.append({"label": f"{annee}-T{t}", "annee": annee,
                                 "debut": f"{annee}-{mois_debut:02d}-01",
                                 "fin": f"{annee}-{mois_fin:02d}-{dernier_jour}"})

    reference = indicateur.baseline_value or 0
    cible = indicateur.target_value
    if cible is None:
        raise HTTPException(status_code=422,
                            detail="Renseignez d'abord la cible finale de l'indicateur.")
    existantes = {t.period_label for t in indicateur.targets}
    cumulatif = payload.get("cumulatif", True)
    creees = 0
    for position, periode in enumerate(periodes, start=1):
        if periode["label"] in existantes:
            continue
        fraction = position / len(periodes)
        valeur = reference + (cible - reference) * fraction if cumulatif else \
            (cible - reference) / len(periodes)
        db.add(IndicatorTarget(indicator_id=indicateur.id, period_label=periode["label"],
                               year=periode["annee"], target_value=round(valeur, 2)))
        creees += 1
    db.commit()
    return {"periodes_creees": creees, "total_periodes": len(periodes),
            "granularite": granularite}
