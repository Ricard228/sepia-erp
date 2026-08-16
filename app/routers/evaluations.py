"""Bénéficiaires, partenaires, évaluation CAD-OCDE et évaluation d'impact."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import (APPROCHES_IMPACT, CATEGORIES_BENEFICIAIRES, CRITERES_CAD,
                      ECHELLE_NOTATION_CAD, METHODES_IMPACT, MODES_CIBLAGE,
                      NIVEAUX_VULNERABILITE, STATUTS_IMPACT, TYPES_CONTRIBUTION,
                      TYPES_EVALUATION, TYPES_PARTENAIRE, TYPOLOGIES_BENEFICIAIRES)
from ..crud import make_crud_router, serialize, verifier_acces_projet
from ..database import get_db
from ..models import Beneficiary, Evaluation, EvaluationRecommendation, ImpactStudy, Partner, User
from ..security import can_edit, can_manage, current_user
from ..services import evaluation as service

router = APIRouter()

router.include_router(make_crud_router(
    Beneficiary, "/api/beneficiaires", "Bénéficiaires", order_by="order_index",
    computed=["taux_atteinte", "part_femmes_atteintes"], search_fields=["name", "code"]))

router.include_router(make_crud_router(
    Partner, "/api/partenaires", "Partenaires", order_by="order_index",
    computed=["taux_decaissement"], search_fields=["name", "code", "organisation"]
    if hasattr(Partner, "organisation") else ["name", "code"]))

router.include_router(make_crud_router(
    Evaluation, "/api/evaluations", "Évaluations", order_by="start_date",
    computed=["note_globale"], search_fields=["title", "code"]))

router.include_router(make_crud_router(
    EvaluationRecommendation, "/api/recommandations", "Recommandations",
    project_scoped=False, order_by="code"))

router.include_router(make_crud_router(
    ImpactStudy, "/api/etudes-impact", "Évaluations d'impact", order_by="code",
    computed=["significatif", "taille_echantillon"], search_fields=["title", "code"]))


analyse = APIRouter(prefix="/api", tags=["Évaluation"])


@analyse.get("/beneficiaires/synthese/{project_id}")
def synthese_beneficiaires(project_id: int, db: Session = Depends(get_db),
                           user: User = Depends(current_user)):
    """Ciblage, atteinte et indicateurs rattachés, groupe de bénéficiaires par groupe."""
    verifier_acces_projet(db, user, project_id)
    return service.synthese_beneficiaires(db, project_id)


@analyse.get("/partenaires/synthese/{project_id}")
def synthese_partenaires(project_id: int, db: Session = Depends(get_db),
                         user: User = Depends(current_user)):
    verifier_acces_projet(db, user, project_id)
    return service.synthese_partenaires(db, project_id)


@analyse.get("/evaluations/synthese/{project_id}")
def synthese_evaluations(project_id: int, db: Session = Depends(get_db),
                         user: User = Depends(current_user)):
    """Notes par critère du CAD, suivi des recommandations et retards."""
    verifier_acces_projet(db, user, project_id)
    return service.synthese_evaluations(db, project_id)


@analyse.get("/evaluations/{evaluation_id}/detail")
def detail_evaluation(evaluation_id: int, db: Session = Depends(get_db),
                      user: User = Depends(current_user)):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Évaluation introuvable.")
    verifier_acces_projet(db, user, evaluation.project_id)
    return service.detail_evaluation(db, evaluation)


@analyse.post("/evaluations/{evaluation_id}/notation")
def enregistrer_notation(evaluation_id: int, payload: Dict[str, Any],
                         db: Session = Depends(get_db), user: User = Depends(can_edit)):
    """Enregistre la note et la justification de chaque critère du CAD.

    Une note sans justification n'a pas de valeur évaluative : la justification
    est donc conservée au même rang que la note elle-même.
    """
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Évaluation introuvable.")
    verifier_acces_projet(db, user, evaluation.project_id)
    cles_valides = {c["cle"] for c in CRITERES_CAD}
    scores, justifications = dict(evaluation.scores or {}), dict(evaluation.justifications or {})
    for cle, valeur in (payload.get("scores") or {}).items():
        if cle not in cles_valides:
            continue
        if valeur in (None, "", 0):
            scores.pop(cle, None)
            continue
        try:
            note = float(valeur)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail=f"Note invalide pour « {cle} ».")
        if not 1 <= note <= 6:
            raise HTTPException(status_code=422,
                                detail="Les notes du CAD s'échelonnent de 1 à 6.")
        scores[cle] = note
    for cle, texte in (payload.get("justifications") or {}).items():
        if cle in cles_valides:
            justifications[cle] = str(texte)[:4000] if texte else None
    evaluation.scores = scores
    evaluation.justifications = justifications
    for champ in ("key_findings", "lessons_learned", "overall_comment"):
        if champ in payload:
            setattr(evaluation, champ, str(payload[champ])[:8000] if payload[champ] else None)
    db.commit()
    return service.detail_evaluation(db, evaluation)


@analyse.get("/impact/synthese/{project_id}")
def synthese_impact(project_id: int, db: Session = Depends(get_db),
                    user: User = Depends(current_user)):
    verifier_acces_projet(db, user, project_id)
    return service.synthese_impact(db, project_id)


@analyse.get("/impact/{etude_id}/detail")
def detail_impact(etude_id: int, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    etude = db.get(ImpactStudy, etude_id)
    if not etude:
        raise HTTPException(status_code=404, detail="Étude d'impact introuvable.")
    verifier_acces_projet(db, user, etude.project_id)
    return service.detail_etude_impact(db, etude)


@analyse.get("/impact/calcul-echantillon")
def calcul_echantillon(effet_minimal: float = Query(..., gt=0),
                       ecart_type: float = Query(1.0, gt=0),
                       puissance: float = Query(0.8, gt=0, lt=1),
                       alpha: float = Query(0.05, gt=0, lt=1),
                       ratio: float = Query(1.0, gt=0),
                       correlation_intra: float = Query(0.0, ge=0, lt=1),
                       taille_grappe: int = Query(1, ge=1, le=10000),
                       user: User = Depends(current_user)):
    """Taille d'échantillon requise pour détecter un effet donné, effet de grappe compris."""
    return service.taille_echantillon_requise(effet_minimal, ecart_type, puissance, alpha,
                                              ratio, correlation_intra, taille_grappe)


@analyse.get("/evaluation/referentiels")
def referentiels_evaluation(user: User = Depends(current_user)):
    """Listes de valeurs des modules bénéficiaires, partenaires et évaluation."""
    return {
        "categories_beneficiaires": CATEGORIES_BENEFICIAIRES,
        "typologies_beneficiaires": TYPOLOGIES_BENEFICIAIRES,
        "niveaux_vulnerabilite": NIVEAUX_VULNERABILITE,
        "modes_ciblage": MODES_CIBLAGE,
        "types_partenaire": TYPES_PARTENAIRE,
        "types_contribution": TYPES_CONTRIBUTION,
        "criteres_cad": CRITERES_CAD,
        "echelle_cad": ECHELLE_NOTATION_CAD,
        "types_evaluation": TYPES_EVALUATION,
        "methodes_impact": METHODES_IMPACT,
        "approches_impact": APPROCHES_IMPACT,
        "statuts_impact": STATUTS_IMPACT,
        "statuts_evaluation": ["Planifiée", "En cours", "Achevée", "Validée"],
        "independance": ["Interne", "Externe indépendante", "Mixte"],
        "priorites": ["Élevée", "Moyenne", "Faible"],
        "reponses_management": ["Acceptée", "Partiellement acceptée", "Rejetée"],
        "statuts_recommandation": ["Non démarrée", "En cours", "Achevée", "Abandonnée"],
        "statuts_partenaire": ["Actif", "Suspendu", "Clos"],
    }


router.include_router(analyse)
