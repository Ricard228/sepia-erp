"""Évaluation selon les critères du CAD de l'OCDE et évaluation d'impact.

Deux logiques distinctes cohabitent ici :
  * l'évaluation par critères apprécie la qualité d'une intervention selon six
    dimensions normalisées, sur la base d'un jugement argumenté ;
  * l'évaluation d'impact cherche à établir un lien causal entre l'intervention
    et les changements observés, en reconstituant le contrefactuel.
La première produit un jugement, la seconde une estimation. Les confondre est
l'erreur la plus répandue dans les rapports d'évaluation.
"""
import math
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..config import CRITERES_CAD, ECHELLE_NOTATION_CAD, METHODES_IMPACT
from ..models import (Beneficiary, Evaluation, EvaluationRecommendation, ImpactStudy,
                      Indicator, Project)
from . import analytics

METHODES_PAR_CLE = {m["cle"]: m for m in METHODES_IMPACT}
NOTES_PAR_VALEUR = {e["note"]: e for e in ECHELLE_NOTATION_CAD}


def libelle_note(note: Optional[float]) -> Dict[str, Any]:
    if note is None:
        return {"note": None, "libelle": "Non noté", "couleur": "#9AA0A6"}
    arrondie = max(1, min(6, int(round(note))))
    entree = NOTES_PAR_VALEUR[arrondie]
    return {"note": note, "libelle": entree["libelle"], "couleur": entree["couleur"]}


# ---------------------------------------------------------------------------
# Évaluation par critères du CAD
# ---------------------------------------------------------------------------
def detail_evaluation(db: Session, evaluation: Evaluation) -> Dict[str, Any]:
    """Fiche complète d'une évaluation : notes par critère et suivi des recommandations."""
    scores = evaluation.scores or {}
    justifications = evaluation.justifications or {}
    criteres = []
    for critere in CRITERES_CAD:
        note = scores.get(critere["cle"])
        note = float(note) if isinstance(note, (int, float)) and note else None
        # L'appréciation de la note est nommée explicitement : la fusionner sous
        # la clé « libelle » écraserait le nom du critère lui-même.
        appreciation = libelle_note(note)
        criteres.append({
            "cle": critere["cle"], "libelle": critere["libelle"],
            "question": critere["question"], "points_examen": critere["points_examen"],
            "note": note, "justification": justifications.get(critere["cle"]),
            "libelle_note": appreciation["libelle"], "couleur": appreciation["couleur"],
        })
    recommandations = [
        {"id": r.id, "code": r.code, "critere": r.criterion, "enonce": r.statement,
         "priorite": r.priority, "responsable": r.responsible,
         "echeance": r.deadline.isoformat() if r.deadline else None,
         "reponse_management": r.management_response, "commentaire": r.response_comment,
         "statut": r.implementation_status, "taux": r.implementation_rate or 0,
         "preuve": r.evidence}
        for r in sorted(evaluation.recommendations, key=lambda x: (x.code or "", x.id))]
    mises_en_oeuvre = [r for r in recommandations if (r["taux"] or 0) >= 100]
    acceptees = [r for r in recommandations if r["reponse_management"] != "Rejetée"]
    return {
        "id": evaluation.id, "code": evaluation.code, "titre": evaluation.title,
        "type": evaluation.evaluation_type, "periode": evaluation.period_covered,
        "statut": evaluation.status, "evaluateur": evaluation.evaluator,
        "independance": evaluation.independence, "budget": evaluation.budget,
        "methodologie": evaluation.methodology, "sources": evaluation.data_sources,
        "echantillonnage": evaluation.sampling, "limites": evaluation.limitations,
        "constats": evaluation.key_findings, "lecons": evaluation.lessons_learned,
        "appreciation_generale": evaluation.overall_comment,
        "rapport": evaluation.report_reference,
        "date_debut": evaluation.start_date.isoformat() if evaluation.start_date else None,
        "date_fin": evaluation.end_date.isoformat() if evaluation.end_date else None,
        "criteres": criteres,
        "note_globale": evaluation.note_globale,
        **{f"globale_{k}": v for k, v in libelle_note(evaluation.note_globale).items()
           if k != "note"},
        "criteres_notes": len([c for c in criteres if c["note"] is not None]),
        "recommandations": recommandations,
        "nb_recommandations": len(recommandations),
        "recommandations_acceptees": len(acceptees),
        "recommandations_mises_en_oeuvre": len(mises_en_oeuvre),
        "taux_mise_en_oeuvre": round(
            sum(r["taux"] or 0 for r in recommandations) / len(recommandations), 1)
        if recommandations else None,
    }


def synthese_evaluations(db: Session, project_id: int) -> Dict[str, Any]:
    """Vue consolidée des exercices évaluatifs d'un projet."""
    evaluations = db.query(Evaluation).filter(
        Evaluation.project_id == project_id).order_by(Evaluation.start_date).all()
    fiches = [detail_evaluation(db, e) for e in evaluations]
    achevees = [f for f in fiches if f["statut"] in ("Achevée", "Validée")]

    # Moyenne par critère sur les évaluations achevées : elle montre la dimension
    # sur laquelle le projet est systématiquement le plus faible.
    par_critere = {}
    for critere in CRITERES_CAD:
        notes = [c["note"] for f in achevees for c in f["criteres"]
                 if c["cle"] == critere["cle"] and c["note"] is not None]
        moyenne = round(sum(notes) / len(notes), 2) if notes else None
        appreciation = libelle_note(moyenne)
        par_critere[critere["libelle"]] = {
            "cle": critere["cle"], "moyenne": moyenne, "nb_evaluations": len(notes),
            "libelle_note": appreciation["libelle"], "couleur": appreciation["couleur"],
        }

    recommandations = [r for f in fiches for r in f["recommandations"]]
    en_retard = [r for r in recommandations
                 if r["echeance"] and r["echeance"] < date.today().isoformat()
                 and (r["taux"] or 0) < 100 and r["reponse_management"] != "Rejetée"]
    notes_globales = [f["note_globale"] for f in fiches if f["note_globale"] is not None]
    return {
        "evaluations": fiches,
        "total": len(fiches),
        "achevees": len(achevees),
        "note_moyenne": round(sum(notes_globales) / len(notes_globales), 2)
        if notes_globales else None,
        "par_critere": par_critere,
        "nb_recommandations": len(recommandations),
        "recommandations_en_retard": en_retard,
        "taux_mise_en_oeuvre": round(
            sum(r["taux"] or 0 for r in recommandations) / len(recommandations), 1)
        if recommandations else None,
        "referentiel": CRITERES_CAD,
        "echelle": ECHELLE_NOTATION_CAD,
    }


# ---------------------------------------------------------------------------
# Évaluation d'impact
# ---------------------------------------------------------------------------
def taille_echantillon_requise(effet_minimal: float, ecart_type: float = 1.0,
                               puissance: float = 0.8, alpha: float = 0.05,
                               ratio: float = 1.0, correlation_intra: float = 0.0,
                               taille_grappe: int = 1) -> Dict[str, Any]:
    """Taille d'échantillon nécessaire pour détecter un effet donné.

    Formule classique de comparaison de deux moyennes :
        n par groupe = (z(1−α/2) + z(puissance))² × σ² × (1 + 1/ratio) / effet²
    Lorsque l'assignation se fait par grappes, la taille est multipliée par
    l'effet de plan 1 + (m − 1) × ρ, où m est la taille de grappe et ρ la
    corrélation intra-grappe : ignorer ce facteur est la cause la plus fréquente
    d'évaluations sous-dimensionnées.
    """
    if not effet_minimal or effet_minimal <= 0 or not ecart_type or ecart_type <= 0:
        return {"erreur": "L'effet minimal détectable et l'écart-type doivent être positifs."}
    # Quantiles de la loi normale, table restreinte aux valeurs usuelles.
    z_alpha = {0.10: 1.6449, 0.05: 1.9600, 0.01: 2.5758}.get(round(alpha, 2), 1.9600)
    z_puissance = {0.80: 0.8416, 0.90: 1.2816, 0.95: 1.6449}.get(round(puissance, 2), 0.8416)
    base = ((z_alpha + z_puissance) ** 2) * (ecart_type ** 2) * (1 + 1 / max(ratio, 0.01))
    n_traitement = base / (effet_minimal ** 2)
    effet_de_plan = 1 + (max(taille_grappe, 1) - 1) * max(correlation_intra, 0.0)
    n_traitement *= effet_de_plan
    n_controle = n_traitement / max(ratio, 0.01)
    return {
        "n_traitement": int(math.ceil(n_traitement)),
        "n_controle": int(math.ceil(n_controle)),
        "n_total": int(math.ceil(n_traitement + n_controle)),
        "effet_de_plan": round(effet_de_plan, 3),
        "grappes_requises": int(math.ceil((n_traitement + n_controle) / max(taille_grappe, 1)))
        if taille_grappe > 1 else None,
        "hypotheses": {
            "effet_minimal_detectable": effet_minimal, "ecart_type": ecart_type,
            "puissance": puissance, "seuil_de_signification": alpha,
            "ratio_traitement_controle": ratio,
            "correlation_intra_grappe": correlation_intra, "taille_de_grappe": taille_grappe,
        },
        "avertissement": "Prévoyez une marge pour l'attrition : une perte de 20 % entre la "
                         "mesure initiale et la mesure finale impose de recruter environ 25 % "
                         "d'unités supplémentaires.",
    }


def detail_etude_impact(db: Session, etude: ImpactStudy) -> Dict[str, Any]:
    """Fiche d'une étude d'impact, enrichie de la documentation de sa méthode."""
    methode = METHODES_PAR_CLE.get((etude.method or "").lower()) or next(
        (m for m in METHODES_IMPACT if m["libelle"] == etude.method), None)
    indicateurs = []
    for code in etude.outcome_indicators or []:
        indicateur = db.query(Indicator).filter(Indicator.project_id == etude.project_id,
                                                Indicator.code == code).first()
        if indicateur:
            indicateurs.append(analytics.indicator_performance(indicateur))

    # Le contrôle de puissance n'est produit que si l'écart-type de l'indicateur
    # de résultat est renseigné : le calculer sur une valeur implicite donnerait
    # un chiffre faux et faussement rassurant.
    puissance_atteinte = None
    if not (etude.treatment_size and etude.control_size and etude.minimum_detectable_effect):
        puissance_atteinte = {"indisponible": "Effectifs des groupes ou effet minimal "
                                              "détectable non renseignés."}
    elif not etude.outcome_sd:
        puissance_atteinte = {"indisponible": "Écart-type de l'indicateur de résultat non "
                                              "renseigné : le calcul de puissance ne peut être "
                                              "conduit sans lui."}
    else:
        taille_grappe = int((etude.treatment_size + etude.control_size) /
                            max(etude.clusters, 1)) if etude.clusters else 1
        requis = taille_echantillon_requise(
            etude.minimum_detectable_effect, etude.outcome_sd, etude.power or 0.8,
            etude.significance_level or 0.05,
            ratio=(etude.treatment_size / max(etude.control_size, 1)),
            correlation_intra=etude.intra_cluster_correlation or 0.0,
            taille_grappe=taille_grappe)
        if "n_total" in requis:
            puissance_atteinte = {
                "n_requis": requis["n_total"], "n_prevu": etude.taille_echantillon,
                "suffisant": etude.taille_echantillon >= requis["n_total"],
                "effet_de_plan": requis["effet_de_plan"],
                "taille_grappe": taille_grappe,
                "ecart_type": etude.outcome_sd,
            }

    return {
        "id": etude.id, "code": etude.code, "titre": etude.title,
        "question": etude.research_question, "hypothese": etude.hypothesis,
        "approche": etude.approach, "methode": etude.method,
        "methode_documentee": methode,
        "hypothese_identification": etude.identification_assumption,
        "regle_affectation": etude.assignment_rule,
        "unite_analyse": etude.unit_of_analysis,
        "covariables": etude.covariates,
        "indicateurs_resultat": indicateurs,
        "codes_indicateurs": etude.outcome_indicators or [],
        "traitement": etude.treatment_size, "controle": etude.control_size,
        "echantillon_total": etude.taille_echantillon, "grappes": etude.clusters,
        "correlation_intra": etude.intra_cluster_correlation,
        "effet_minimal_detectable": etude.minimum_detectable_effect,
        "ecart_type_resultat": etude.outcome_sd,
        "puissance": etude.power, "seuil": etude.significance_level,
        "attrition": etude.attrition_rate,
        "controle_puissance": puissance_atteinte,
        "date_baseline": etude.baseline_date.isoformat() if etude.baseline_date else None,
        "date_intermediaire": etude.midline_date.isoformat() if etude.midline_date else None,
        "date_finale": etude.endline_date.isoformat() if etude.endline_date else None,
        "statut": etude.status,
        "effet_estime": etude.effect_estimate, "erreur_type": etude.standard_error,
        "p_value": etude.p_value, "intervalle_confiance": etude.confidence_interval,
        "unite_effet": etude.effect_unit,
        "significatif": etude.significatif,
        "tests_robustesse": etude.robustness_checks,
        "menaces_validite": etude.threats_to_validity,
        "conclusion": etude.conclusion,
        "ethique": etude.ethical_clearance,
        "depot_donnees": etude.data_repository,
    }


def synthese_impact(db: Session, project_id: int) -> Dict[str, Any]:
    etudes = db.query(ImpactStudy).filter(
        ImpactStudy.project_id == project_id).order_by(ImpactStudy.code).all()
    fiches = [detail_etude_impact(db, e) for e in etudes]
    par_approche: Dict[str, int] = {}
    for fiche in fiches:
        par_approche[fiche["approche"] or "Non précisée"] = \
            par_approche.get(fiche["approche"] or "Non précisée", 0) + 1
    concluantes = [f for f in fiches if f["significatif"] is True]
    return {
        "etudes": fiches,
        "total": len(fiches),
        "par_approche": par_approche,
        "analysees": len([f for f in fiches if f["statut"] in ("Analysée", "Publiée")]),
        "effets_significatifs": len(concluantes),
        "echantillon_cumule": sum(f["echantillon_total"] or 0 for f in fiches),
        "methodes": METHODES_IMPACT,
    }


# ---------------------------------------------------------------------------
# Bénéficiaires : consolidation et rattachement des indicateurs
# ---------------------------------------------------------------------------
def synthese_beneficiaires(db: Session, project_id: int) -> Dict[str, Any]:
    """Ciblage, atteinte et indicateurs rattachés, groupe par groupe."""
    groupes = db.query(Beneficiary).filter(
        Beneficiary.project_id == project_id).order_by(
        Beneficiary.order_index, Beneficiary.name).all()
    indicateurs = db.query(Indicator).filter(Indicator.project_id == project_id).all()
    par_groupe: Dict[Any, List[Dict[str, Any]]] = {}
    for indicateur in indicateurs:
        if indicateur.beneficiary_id:
            par_groupe.setdefault(indicateur.beneficiary_id, []).append(
                analytics.indicator_performance(indicateur))

    lignes = []
    for groupe in groupes:
        performances = par_groupe.get(groupe.id, [])
        taux = [p["taux"] for p in performances if p["taux"] is not None]
        lignes.append({
            "id": groupe.id, "code": groupe.code, "nom": groupe.name,
            "categorie": groupe.category, "typologie": groupe.typology,
            "zone": groupe.zone.name if groupe.zone else None,
            "vulnerabilite": groupe.vulnerability_level,
            "cible_total": groupe.target_total, "cible_femmes": groupe.target_women,
            "cible_jeunes": groupe.target_youth, "cible_handicap": groupe.target_disabled,
            "atteint_total": groupe.reached_total, "atteint_femmes": groupe.reached_women,
            "atteint_jeunes": groupe.reached_youth, "atteint_handicap": groupe.reached_disabled,
            "menages": groupe.households, "taille_menage": groupe.average_household_size,
            "revenu_reference": groupe.baseline_income, "taux_pauvrete": groupe.poverty_rate,
            "taux_atteinte": groupe.taux_atteinte,
            "part_femmes_atteintes": groupe.part_femmes_atteintes,
            "criteres_selection": groupe.selection_criteria,
            "methode_ciblage": groupe.selection_method,
            "besoins": groupe.needs, "contraintes": groupe.constraints,
            "benefices_attendus": groupe.expected_benefits,
            "participation": groupe.participation_mode,
            "mecanisme_plainte": groupe.grievance_mechanism,
            "commentaire": groupe.comment,
            "indicateurs": performances,
            "nb_indicateurs": len(performances),
            "taux_moyen_indicateurs": round(sum(taux) / len(taux), 1) if taux else None,
            # Le nombre de personnes touchées estimé à partir des ménages éclaire
            # la portée réelle d'un projet dont les indicateurs comptent des ménages.
            "personnes_touchees_estimees": round(
                (groupe.households or 0) * (groupe.average_household_size or 0))
            if groupe.households and groupe.average_household_size else None,
        })

    cible_totale = sum(l["cible_total"] or 0 for l in lignes)
    atteint_total = sum(l["atteint_total"] or 0 for l in lignes)
    cible_femmes = sum(l["cible_femmes"] or 0 for l in lignes)
    atteint_femmes = sum(l["atteint_femmes"] or 0 for l in lignes)
    non_rattaches = len([i for i in indicateurs if not i.beneficiary_id])
    return {
        "groupes": lignes,
        "total_groupes": len(lignes),
        "cible_totale": cible_totale,
        "atteint_total": atteint_total,
        "taux_atteinte_global": round(atteint_total / cible_totale * 100, 1)
        if cible_totale else None,
        "cible_femmes": cible_femmes,
        "atteint_femmes": atteint_femmes,
        "part_femmes_ciblee": round(cible_femmes / cible_totale * 100, 1) if cible_totale else None,
        "part_femmes_atteinte": round(atteint_femmes / atteint_total * 100, 1)
        if atteint_total else None,
        "menages": sum(l["menages"] or 0 for l in lignes),
        "personnes_touchees_estimees": sum(l["personnes_touchees_estimees"] or 0 for l in lignes),
        "indicateurs_rattaches": len(indicateurs) - non_rattaches,
        "indicateurs_non_rattaches": non_rattaches,
        "taux_rattachement": round(
            (len(indicateurs) - non_rattaches) / len(indicateurs) * 100, 1)
        if indicateurs else None,
    }


def synthese_partenaires(db: Session, project_id: int) -> Dict[str, Any]:
    from ..models import Partner
    partenaires = db.query(Partner).filter(
        Partner.project_id == project_id).order_by(Partner.order_index, Partner.name).all()
    lignes = [{
        "id": p.id, "code": p.code, "nom": p.name, "type": p.partner_type, "role": p.role,
        "pays": p.country, "convention": p.agreement_reference,
        "debut": p.agreement_start.isoformat() if p.agreement_start else None,
        "fin": p.agreement_end.isoformat() if p.agreement_end else None,
        "engage": p.financial_commitment, "verse": p.financial_disbursed,
        "devise": p.currency, "taux_decaissement": p.taux_decaissement,
        "type_contribution": p.contribution_type, "nature": p.in_kind_description,
        "obligations": p.obligations, "livrables": p.deliverables,
        "note": p.performance_rating, "appreciation": p.performance_comment,
        "risques": p.risks, "contact": p.contact_name, "courriel": p.contact_email,
        "telephone": p.contact_phone, "statut": p.status,
    } for p in partenaires]
    par_type: Dict[str, int] = {}
    for ligne in lignes:
        par_type[ligne["type"] or "Non précisé"] = par_type.get(ligne["type"] or "Non précisé", 0) + 1
    notes = [l["note"] for l in lignes if l["note"]]
    engage = sum(l["engage"] or 0 for l in lignes)
    verse = sum(l["verse"] or 0 for l in lignes)
    return {
        "partenaires": lignes,
        "total": len(lignes),
        "actifs": len([l for l in lignes if l["statut"] == "Actif"]),
        "par_type": par_type,
        "engagement_total": round(engage, 2),
        "verse_total": round(verse, 2),
        "taux_decaissement_global": round(verse / engage * 100, 1) if engage else None,
        "note_moyenne": round(sum(notes) / len(notes), 2) if notes else None,
    }
