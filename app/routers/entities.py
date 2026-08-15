"""Routeurs CRUD des entités métier, générés à partir du modèle de données."""
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..crud import apply_payload, make_crud_router, serialize, serialize_many
from ..database import get_db
from ..models import (Activity, Assumption, BudgetLine, Form, FormQuestion, FormSubmission,
                      Indicator, IndicatorActual, IndicatorTarget, LogframeElement, Project,
                      RaciAssignment, Risk, Stakeholder, User, Zone)
from ..security import can_edit, current_user
from ..services import analytics, planning

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

router.include_router(make_crud_router(
    Zone, "/api/zones", "Zones d'intervention", order_by="order_index",
    search_fields=["name", "code"]))

router.include_router(make_crud_router(
    Stakeholder, "/api/stakeholders", "Parties prenantes", order_by="order_index",
    search_fields=["name", "organisation"]))

router.include_router(make_crud_router(
    RaciAssignment, "/api/raci", "Matrice RACI", order_by="activity_id"))


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
    """Saisie ou mise à jour d'une réalisation, avec désagrégation et localisation.

    Lorsque la valeur globale n'est pas fournie mais que la ventilation l'est,
    la valeur est déduite de la somme des modalités de la première catégorie
    renseignée — ce qui évite une double saisie et garantit la cohérence entre
    le total et sa ventilation.
    """
    indicateur = db.get(Indicator, indicator_id)
    if not indicateur:
        raise HTTPException(status_code=404, detail="Indicateur introuvable.")
    periode = payload.get("period_label")
    if not periode:
        raise HTTPException(status_code=422, detail="La période de mesure est obligatoire.")

    ventilation = payload.get("disaggregated_values") or {}
    ventilation = {categorie: {modalite: float(valeur)
                               for modalite, valeur in modalites.items()
                               if valeur not in (None, "")}
                   for categorie, modalites in ventilation.items()
                   if isinstance(modalites, dict)}
    ventilation = {c: m for c, m in ventilation.items() if m}
    if payload.get("value") in (None, "") and ventilation:
        premiere = next(iter(ventilation.values()))
        payload["value"] = round(sum(premiere.values()), 2)
    payload["disaggregated_values"] = ventilation

    # Une mesure est identifiée par le triplet indicateur / période / zone :
    # deux zones distinctes peuvent produire une mesure sur la même période.
    zone_id = payload.get("zone_id") or None
    existante = next((a for a in indicateur.actuals
                      if a.period_label == periode and (a.zone_id or None) == zone_id), None)
    objet = existante or IndicatorActual(indicator_id=indicator_id, period_label=periode)
    apply_payload(objet, payload, IndicatorActual)
    objet.indicator_id = indicator_id
    objet.collected_by = objet.collected_by or user.full_name
    if objet.validation_status == "Validé":
        objet.validated_by = user.full_name
    if existante is None:
        db.add(objet)
    db.commit()
    db.refresh(objet)
    return {"realisation": serialize(objet),
            "creee": existante is None,
            "performance": analytics.indicator_performance(db.get(Indicator, indicator_id))}


@detail.post("/actuals/{actual_id}/valider")
def valider_mesure(actual_id: int, payload: Dict[str, Any] = None,
                   db: Session = Depends(get_db), user: User = Depends(can_edit)):
    """Validation ou rejet d'une mesure par le responsable de suivi-évaluation."""
    mesure = db.get(IndicatorActual, actual_id)
    if not mesure:
        raise HTTPException(status_code=404, detail="Mesure introuvable.")
    statut = (payload or {}).get("validation_status", "Validé")
    if statut not in ("Brouillon", "Validé", "Rejeté"):
        raise HTTPException(status_code=422, detail="Statut de validation inconnu.")
    mesure.validation_status = statut
    mesure.validated_by = user.full_name if statut != "Brouillon" else None
    if (payload or {}).get("comment"):
        mesure.comment = payload["comment"]
    db.commit()
    db.refresh(mesure)
    return serialize(mesure)


@detail.get("/analyse/desagregation/{project_id}")
def analyse_desagregation(project_id: int, periode: Optional[str] = Query(None),
                          db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Analyse d'équité : ventilation par sexe, âge, groupe cible et autres catégories."""
    return analytics.synthese_desagregation(db, project_id, periode)


@detail.get("/analyse/zones/{project_id}")
def analyse_zones(project_id: int, periode: Optional[str] = Query(None),
                  db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Consolidation des réalisations par zone d'intervention et par activité."""
    return {"zones": analytics.consolidation_par_zone(db, project_id, periode),
            "activites": analytics.consolidation_par_activite(db, project_id, periode)}


@detail.get("/analyse/smart/{project_id}")
def analyse_smart(project_id: int, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    """Diagnostic de la qualité SMART du système d'indicateurs."""
    return analytics.synthese_qualite_smart(db, project_id)


@detail.post("/indicators/{indicator_id}/smart")
def enregistrer_revue_smart(indicator_id: int, payload: Dict[str, Any],
                            db: Session = Depends(get_db), user: User = Depends(can_edit)):
    """Enregistre la revue SMART manuelle d'un indicateur."""
    indicateur = db.get(Indicator, indicator_id)
    if not indicateur:
        raise HTTPException(status_code=404, detail="Indicateur introuvable.")
    criteres = payload.get("smart_check") or {}
    indicateur.smart_check = {cle: bool(valeur) for cle, valeur in criteres.items()}
    indicateur.smart_comment = payload.get("smart_comment")
    indicateur.smart_reviewed_at = date.today()
    diagnostic = analytics.qualite_smart_indicateur(indicateur)
    indicateur.smart_score = diagnostic["score"]
    db.commit()
    return diagnostic


@detail.get("/analyse/periode/{project_id}")
def analyse_de_periode(project_id: int, periode: str = Query(...),
                       db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Photographie de la performance sur une période de rapportage."""
    return analytics.analyse_periode(db, project_id, periode)


@detail.get("/analyse/periodes/{project_id}")
def liste_periodes(project_id: int, db: Session = Depends(get_db),
                   user: User = Depends(current_user)):
    """Périodes pour lesquelles une cible ou une mesure existe, plus les périodes suggérées."""
    existantes = analytics.periodes_disponibles(db, project_id)
    projet = db.get(Project, project_id)
    suggerees = []
    if projet and projet.start_date and projet.end_date:
        for annee in range(projet.start_date.year, projet.end_date.year + 1):
            suggerees.append(str(annee))
            suggerees += [f"{annee}-S{s}" for s in (1, 2)]
            suggerees += [f"{annee}-T{t}" for t in (1, 2, 3, 4)]
    return {"existantes": existantes,
            "suggerees": sorted(set(suggerees) | set(existantes))}


@detail.get("/saisie/contexte/{project_id}")
def contexte_saisie(project_id: int, db: Session = Depends(get_db),
                    user: User = Depends(current_user)):
    """Données nécessaires à l'écran de saisie rapide : indicateurs, zones, activités."""
    indicateurs = db.query(Indicator).filter(Indicator.project_id == project_id,
                                             Indicator.is_active.is_(True)).order_by(
        Indicator.code).all()
    return {
        "indicateurs": [{"id": i.id, "code": i.code, "name": i.name, "unit": i.unit,
                         "level": i.level, "frequency": i.frequency,
                         "disaggregation": i.disaggregation or [],
                         "target_value": i.target_value, "is_key": i.is_key,
                         "derniere": analytics.indicator_performance(i)} for i in indicateurs],
        "zones": [{"id": z.id, "code": z.code, "name": z.name, "level": z.level}
                  for z in db.query(Zone).filter(Zone.project_id == project_id).order_by(
                      Zone.order_index, Zone.name).all()],
        "activites": [{"id": a.id, "code": a.code, "name": a.name}
                      for a in db.query(Activity).filter(
                          Activity.project_id == project_id).order_by(Activity.code).all()],
        "periodes": analytics.periodes_disponibles(db, project_id),
    }


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
        ligne["duree_calculee"] = planning.duree_activite(a)
        lignes.append(ligne)
    return {"activites": lignes, "synthese": analytics.synthese_activites(db, project_id),
            "ordonnancement": planning.chemin_critique(db, project_id)}


# --- Ordonnancement : chemin critique, PERT, WBS, RACI ---------------------
@detail.get("/planning/chemin-critique/{project_id}")
def api_chemin_critique(project_id: int, db: Session = Depends(get_db),
                        user: User = Depends(current_user)):
    """Ordonnancement au plus tôt et au plus tard, marges, chemin critique, durée du projet."""
    return planning.chemin_critique(db, project_id)


@detail.get("/planning/wbs/{project_id}")
def api_wbs(project_id: int, db: Session = Depends(get_db),
            user: User = Depends(current_user)):
    """Organigramme des tâches : décomposition hiérarchique et consolidation des coûts."""
    return planning.organigramme_taches(db, project_id)


@detail.get("/planning/raci/{project_id}")
def api_raci(project_id: int, db: Session = Depends(get_db),
             user: User = Depends(current_user)):
    """Matrice des responsabilités, charge par partie prenante et anomalies de cohérence."""
    return planning.matrice_raci(db, project_id)


@detail.post("/planning/raci/{project_id}/cellule")
def definir_role_raci(project_id: int, payload: Dict[str, Any],
                      db: Session = Depends(get_db), user: User = Depends(can_edit)):
    """Attribue, modifie ou retire le rôle d'une partie prenante sur une activité."""
    activity_id = payload.get("activity_id")
    stakeholder_id = payload.get("stakeholder_id")
    role = (payload.get("role") or "").strip().upper()
    if not activity_id or not stakeholder_id:
        raise HTTPException(status_code=422, detail="Activité et partie prenante obligatoires.")
    if role and role not in planning.ROLES_RACI:
        raise HTTPException(status_code=422,
                            detail="Rôle invalide : utilisez R, A, C ou I, ou une valeur vide.")
    existante = db.query(RaciAssignment).filter(
        RaciAssignment.activity_id == activity_id,
        RaciAssignment.stakeholder_id == stakeholder_id).first()
    if not role:
        if existante:
            db.delete(existante)
            db.commit()
        return {"supprime": True, "activity_id": activity_id, "stakeholder_id": stakeholder_id}
    if existante:
        existante.role = role
    else:
        db.add(RaciAssignment(project_id=project_id, activity_id=activity_id,
                              stakeholder_id=stakeholder_id, role=role))
    db.commit()
    return {"activity_id": activity_id, "stakeholder_id": stakeholder_id, "role": role}


@detail.post("/planning/wbs/{project_id}/codifier")
def codifier_wbs(project_id: int, db: Session = Depends(get_db),
                 user: User = Depends(can_edit)):
    """Inscrit le code WBS calculé sur chaque activité, pour usage dans les exports."""
    arbre = planning.organigramme_taches(db, project_id)
    compteur = 0
    for ligne in arbre["lignes"]:
        if ligne["type"] != "Lot de travail" or not ligne.get("id"):
            continue
        activite = db.get(Activity, ligne["id"])
        if activite and activite.project_id == project_id:
            activite.wbs_code = ligne["wbs"]
            compteur += 1
    db.commit()
    return {"activites_codifiees": compteur, "nb_niveaux": arbre["nb_niveaux"]}


router.include_router(detail)
