"""Routeurs CRUD des entités métier, générés à partir du modèle de données."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..crud import apply_payload, make_crud_router, serialize, serialize_many
from ..database import get_db
from ..models import (Activity, Assumption, BudgetLine, Form, FormQuestion, FormSubmission,
                      Indicator, IndicatorActual, IndicatorTarget, LogframeElement, Risk, User)
from ..security import can_edit, current_user
from ..services import analytics

router = APIRouter()

# --- Routeurs générés ------------------------------------------------------
router.include_router(make_crud_router(
    LogframeElement, "/api/logframe", "Cadre logique",
    order_by="order_index", search_fields=["statement", "code"]))

router.include_router(make_crud_router(
    Indicator, "/api/indicators", "Indicateurs",
    order_by="code", search_fields=["name", "code"]))

router.include_router(make_crud_router(
    IndicatorTarget, "/api/targets", "Cibles", project_scoped=False, order_by="period_label"))

router.include_router(make_crud_router(
    IndicatorActual, "/api/actuals", "Réalisations", project_scoped=False, order_by="period_label"))

router.include_router(make_crud_router(
    Risk, "/api/risks", "Risques", order_by="code",
    computed=["score", "severity"], search_fields=["title", "code", "category"]))

router.include_router(make_crud_router(
    Assumption, "/api/assumptions", "Hypothèses", order_by="code", search_fields=["statement"]))

router.include_router(make_crud_router(
    Activity, "/api/activities", "Activités", order_by="order_index",
    search_fields=["name", "code"]))

router.include_router(make_crud_router(
    BudgetLine, "/api/budget", "Budget", order_by="code",
    computed=["total_planned"], search_fields=["label", "code", "category"]))

router.include_router(make_crud_router(
    Form, "/api/forms", "Formulaires", order_by="code", search_fields=["name", "code"]))

router.include_router(make_crud_router(
    FormQuestion, "/api/questions", "Questions", project_scoped=False, order_by="order_index"))

router.include_router(make_crud_router(
    FormSubmission, "/api/submissions", "Réponses", project_scoped=False, order_by="submitted_at"))


# --- Points d'entrée spécialisés ------------------------------------------
detail = APIRouter(prefix="/api", tags=["Vues spécialisées"])


@detail.get("/logframe/tree/{project_id}")
def arbre_cadre_logique(project_id: int, db: Session = Depends(get_db),
                        user: User = Depends(current_user)):
    """Arborescence complète du cadre logique avec indicateurs rattachés."""
    elements = db.query(LogframeElement).filter(
        LogframeElement.project_id == project_id).order_by(LogframeElement.order_index).all()
    indicateurs: Dict[Any, List[Dict[str, Any]]] = {}
    for ind in db.query(Indicator).filter(Indicator.project_id == project_id).all():
        indicateurs.setdefault(ind.element_id, []).append(analytics.indicator_performance(ind))
    par_parent: Dict[Any, List[LogframeElement]] = {}
    for element in elements:
        par_parent.setdefault(element.parent_id, []).append(element)

    def construire(parent_id):
        noeuds = []
        for element in par_parent.get(parent_id, []):
            noeud = serialize(element)
            noeud["indicateurs"] = indicateurs.get(element.id, [])
            noeud["enfants"] = construire(element.id)
            noeuds.append(noeud)
        return noeuds

    ordre = {"IMPACT": 0, "EFFET": 1, "PRODUIT": 2, "ACTIVITE": 3}
    racines = construire(None)
    racines.sort(key=lambda n: (ordre.get(n.get("level"), 9), n.get("order_index") or 0))
    orphelins = [serialize(e) for e in elements
                 if e.parent_id and e.parent_id not in {x.id for x in elements}]
    return {"racines": racines, "orphelins": orphelins, "total": len(elements)}


@detail.get("/indicators/{indicator_id}/serie")
def serie_indicateur(indicator_id: int, db: Session = Depends(get_db),
                     user: User = Depends(current_user)):
    indicateur = db.get(Indicator, indicator_id)
    if not indicateur:
        raise HTTPException(status_code=404, detail="Indicateur introuvable.")
    return {
        "indicateur": serialize(indicateur),
        "performance": analytics.indicator_performance(indicateur),
        "serie": analytics.serie_temporelle(indicateur),
        "cibles": serialize_many(indicateur.targets),
        "realisations": serialize_many(indicateur.actuals),
    }


@detail.post("/indicators/{indicator_id}/saisie")
def saisir_valeur(indicator_id: int, payload: Dict[str, Any],
                  db: Session = Depends(get_db), user: User = Depends(can_edit)):
    """Saisie rapide d'une réalisation depuis le tableau de suivi."""
    indicateur = db.get(Indicator, indicator_id)
    if not indicateur:
        raise HTTPException(status_code=404, detail="Indicateur introuvable.")
    periode = payload.get("period_label")
    if not periode:
        raise HTTPException(status_code=422, detail="La période est obligatoire.")
    existante = next((a for a in indicateur.actuals if a.period_label == periode), None)
    objet = existante or IndicatorActual(indicator_id=indicator_id, period_label=periode)
    apply_payload(objet, payload, IndicatorActual)
    objet.indicator_id = indicator_id
    objet.collected_by = objet.collected_by or user.full_name
    if existante is None:
        db.add(objet)
    db.commit()
    db.refresh(objet)
    return {"realisation": serialize(objet),
            "performance": analytics.indicator_performance(db.get(Indicator, indicator_id))}


@detail.get("/forms/{form_id}/complet")
def formulaire_complet(form_id: int, db: Session = Depends(get_db),
                       user: User = Depends(current_user)):
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire introuvable.")
    return {"formulaire": serialize(form), "questions": serialize_many(form.questions)}


@detail.post("/forms/{form_id}/questions/reordonner")
def reordonner_questions(form_id: int, payload: List[int],
                         db: Session = Depends(get_db), user: User = Depends(can_edit)):
    for position, question_id in enumerate(payload):
        question = db.get(FormQuestion, question_id)
        if question and question.form_id == form_id:
            question.order_index = position
    db.commit()
    return {"reordonne": len(payload)}


@detail.get("/activities/gantt/{project_id}")
def donnees_gantt(project_id: int, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    activites = db.query(Activity).filter(Activity.project_id == project_id).order_by(
        Activity.order_index, Activity.code).all()
    elements = {e.id: e for e in db.query(LogframeElement).filter(
        LogframeElement.project_id == project_id).all()}
    lignes = []
    for a in activites:
        element = elements.get(a.element_id)
        ligne = serialize(a)
        ligne["resultat"] = f"{element.code or ''} {element.statement}"[:80] if element else None
        lignes.append(ligne)
    return {"activites": lignes, "synthese": analytics.synthese_activites(db, project_id)}


router.include_router(detail)
