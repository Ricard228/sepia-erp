"""Moteur de calcul de la performance : taux de réalisation, agrégations, alertes,
désagrégation (genre et groupe cible), consolidation par zone d'intervention,
qualité SMART des indicateurs et analyses périodées."""
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..config import (CATEGORIE_GENRE, CRITERES_SMART, MODALITE_FEMME, MODALITES_DESAGREGATION,
                      SEUILS_QUALITE)
from ..models import (Activity, Assumption, BudgetLine, Indicator, IndicatorActual,
                      IndicatorTarget, Project, Risk, Zone)

SEUILS = [(100, "Atteint"), (85, "En bonne voie"), (60, "À surveiller"), (0, "Critique")]
COULEURS_STATUT = {
    "Atteint": "#0f9d58", "En bonne voie": "#4CAF50", "À surveiller": "#F9A825",
    "Critique": "#D93025", "Non renseigné": "#9AA0A6",
}


def statut_performance(taux: Optional[float]) -> str:
    if taux is None:
        return "Non renseigné"
    for seuil, libelle in SEUILS:
        if taux >= seuil:
            return libelle
    return "Critique"


def taux_realisation(baseline: Optional[float], target: Optional[float],
                     actual: Optional[float], direction: str = "Croissant") -> Optional[float]:
    """Taux de réalisation en % tenant compte de la référence et du sens de progression.

    Formule GAR : (Réalisé − Référence) / (Cible − Référence) × 100.
    Si la référence est absente, on retombe sur Réalisé / Cible × 100.
    """
    if actual is None or target is None:
        return None
    if baseline is None:
        if target == 0:
            return 100.0 if actual == 0 else None
        if (direction or "").startswith("Déc"):
            # Progression décroissante sans référence : plus on est bas, mieux c'est.
            return round(min((target / actual) * 100, 300), 1) if actual else 100.0
        return round((actual / target) * 100, 1)
    denominateur = target - baseline
    if denominateur == 0:
        return 100.0 if actual == target else 0.0
    return round(((actual - baseline) / denominateur) * 100, 1)


UNITES_MOYENNE = {"%", "ratio", "score", "indice", "t/ha", "kg/ha", "taux", "pourcentage"}


def regle_agregation(indicator: Indicator) -> str:
    """Règle de consolidation des mesures d'une même période.

    Un indicateur d'effectifs collecté sur six zones doit être sommé ; un taux
    ou un rendement moyen doit être moyenné. La règle est portée par
    l'indicateur ; à défaut, elle est déduite de l'unité de mesure.
    """
    explicite = (indicator.aggregation or "").strip().lower()
    if explicite in ("somme", "moyenne", "dernière valeur", "derniere valeur", "maximum"):
        return explicite.replace("derniere", "dernière")
    return "moyenne" if (indicator.unit or "").strip().lower() in UNITES_MOYENNE else "somme"


def _mesures_de_periode(indicator: Indicator, periode: str) -> List[IndicatorActual]:
    return [a for a in indicator.actuals if a.period_label == periode and a.value is not None]


def valeur_de_periode(indicator: Indicator, periode: str) -> Optional[float]:
    """Valeur consolidée d'un indicateur sur une période, toutes zones confondues."""
    mesures = _mesures_de_periode(indicator, periode)
    if not mesures:
        return None
    valeurs = [m.value for m in mesures]
    regle = regle_agregation(indicator)
    if len(valeurs) == 1:
        return round(valeurs[0], 4)
    if regle == "moyenne":
        return round(sum(valeurs) / len(valeurs), 4)
    if regle == "dernière valeur":
        return round(sorted(mesures, key=lambda a: (a.reference_date or date.min, a.id))[-1].value, 4)
    if regle == "maximum":
        return round(max(valeurs), 4)
    return round(sum(valeurs), 4)


def derniere_periode(indicator: Indicator) -> Optional[str]:
    """Libellé de la période la plus récente pour laquelle une mesure existe."""
    mesures = [a for a in indicator.actuals if a.value is not None]
    if not mesures:
        return None
    return sorted(mesures, key=lambda a: (a.reference_date or date.min, a.id))[-1].period_label


def derniere_valeur(indicator: Indicator) -> Optional[IndicatorActual]:
    """Mesure la plus récente — sert à dater et sourcer la valeur consolidée."""
    actuals = [a for a in indicator.actuals if a.value is not None]
    if not actuals:
        return None
    return sorted(actuals, key=lambda a: (a.reference_date or date.min, a.id))[-1]


def taux_periode(cible: Optional[float], realise: Optional[float],
                 direction: str = "Croissant") -> Optional[float]:
    """Taux d'atteinte du jalon de la période : réalisé / cible de la même période."""
    if cible in (None, 0) or realise is None:
        return None
    if (direction or "").startswith("Déc"):
        # Progression décroissante : être en dessous de la cible est une réussite.
        return round(min((cible / realise) * 100, 300), 1) if realise else 100.0
    return round((realise / cible) * 100, 1)


def indicator_performance(indicator: Indicator) -> Dict[str, Any]:
    """Performance d'un indicateur.

    Deux taux sont calculés, conformément à la pratique de la gestion axée sur
    les résultats :
      * « taux » — atteinte du jalon de la période mesurée (cible périodique) ;
        c'est ce taux qui détermine le statut de performance, car comparer une
        réalisation intermédiaire à la cible de fin de projet fausserait le
        diagnostic ;
      * « taux_final » — progression vers la cible finale depuis la référence.
    À défaut de cible périodique, le statut est établi sur la progression finale.
    """
    last = derniere_valeur(indicator)
    periode_courante = derniere_periode(indicator)
    # La valeur retenue consolide toutes les mesures de la période (zones,
    # activités) selon la règle d'agrégation de l'indicateur.
    valeur = valeur_de_periode(indicator, periode_courante) if periode_courante else None
    cible_de_periode = None
    if periode_courante:
        jalon = next((t for t in indicator.targets if t.period_label == periode_courante), None)
        cible_de_periode = jalon.target_value if jalon else None
    taux_final = taux_realisation(indicator.baseline_value, indicator.target_value,
                                  valeur, indicator.direction)
    taux_jalon = taux_periode(cible_de_periode, valeur, indicator.direction)
    taux = taux_jalon if taux_jalon is not None else taux_final
    ecart = None
    if valeur is not None and cible_de_periode is not None:
        ecart = round(valeur - cible_de_periode, 2)
    elif valeur is not None and indicator.target_value is not None:
        ecart = round(valeur - indicator.target_value, 2)
    statut = statut_performance(taux)
    return {
        "id": indicator.id,
        "code": indicator.code,
        "name": indicator.name,
        "level": indicator.level,
        "classe": indicator.indicator_class or "Résultat",
        "unit": indicator.unit,
        "is_key": indicator.is_key,
        "frequency": indicator.frequency,
        "responsible": indicator.responsible,
        "baseline_value": indicator.baseline_value,
        "target_value": indicator.target_value,
        "actual_value": valeur,
        "period_label": periode_courante,
        "period_target": cible_de_periode,
        "agregation": regle_agregation(indicator),
        "nb_mesures_periode": len(_mesures_de_periode(indicator, periode_courante))
        if periode_courante else 0,
        "reference_date": last.reference_date.isoformat() if last and last.reference_date else None,
        "taux": taux,
        "taux_final": taux_final,
        "base_evaluation": "Cible de la période" if taux_jalon is not None else "Cible finale",
        "ecart": ecart,
        "statut": statut,
        "couleur": COULEURS_STATUT[statut],
        "nb_mesures": len(indicator.actuals),
        "disaggregation": indicator.disaggregation or [],
    }


def serie_temporelle(indicator: Indicator) -> Dict[str, Any]:
    """Série cibles vs réalisations consolidées, alignée sur les libellés de période."""
    cibles = {t.period_label: t.target_value for t in indicator.targets}
    periodes_mesurees = {a.period_label for a in indicator.actuals if a.value is not None}
    periodes = sorted(set(cibles.keys()) | periodes_mesurees)
    return {
        "periodes": periodes,
        "cibles": [cibles.get(p) for p in periodes],
        "reels": [valeur_de_periode(indicator, p) if p in periodes_mesurees else None
                  for p in periodes],
        "agregation": regle_agregation(indicator),
    }


def indicateurs_du_projet(db: Session, project_id: int,
                          inclure_processus: Optional[bool] = None) -> List[Indicator]:
    """Indicateurs actifs d'un projet, filtrés selon l'option d'affichage des processus.

    Les indicateurs de processus (taux d'exécution, délais, participation)
    documentent la conduite de l'action plutôt que le changement produit. Ils
    alourdissent la lecture du dispositif et ne sont donc affichés que si le
    projet a activé leur suivi — sans jamais être supprimés de la base.
    """
    requete = db.query(Indicator).filter(Indicator.project_id == project_id,
                                         Indicator.is_active.is_(True))
    if inclure_processus is None:
        projet = db.get(Project, project_id)
        inclure_processus = bool(projet and projet.show_process_indicators)
    if not inclure_processus:
        requete = requete.filter((Indicator.indicator_class.is_(None)) |
                                 (Indicator.indicator_class != "Processus"))
    return requete.all()


def synthese_indicateurs(db: Session, project_id: int,
                         inclure_processus: Optional[bool] = None) -> Dict[str, Any]:
    indicators = indicateurs_du_projet(db, project_id, inclure_processus)
    lignes = [indicator_performance(i) for i in indicators]
    par_statut: Dict[str, int] = {}
    par_niveau: Dict[str, Dict[str, Any]] = {}
    for ligne in lignes:
        par_statut[ligne["statut"]] = par_statut.get(ligne["statut"], 0) + 1
        niveau = ligne["level"] or "NON CLASSÉ"
        bucket = par_niveau.setdefault(niveau, {"nombre": 0, "taux_cumule": 0.0, "renseignes": 0})
        bucket["nombre"] += 1
        if ligne["taux"] is not None:
            bucket["taux_cumule"] += ligne["taux"]
            bucket["renseignes"] += 1
    for niveau, bucket in par_niveau.items():
        bucket["taux_moyen"] = round(bucket["taux_cumule"] / bucket["renseignes"], 1) if bucket["renseignes"] else None
        bucket.pop("taux_cumule")
    renseignes = [l["taux"] for l in lignes if l["taux"] is not None]
    nb_processus = db.query(Indicator).filter(
        Indicator.project_id == project_id, Indicator.is_active.is_(True),
        Indicator.indicator_class == "Processus").count()
    return {
        "lignes": lignes,
        "total": len(lignes),
        "renseignes": len(renseignes),
        "taux_moyen": round(sum(renseignes) / len(renseignes), 1) if renseignes else None,
        "taux_couverture": round(len(renseignes) / len(lignes) * 100, 1) if lignes else 0,
        "par_statut": par_statut,
        "par_niveau": par_niveau,
        "nb_processus_disponibles": nb_processus,
        "processus_affiches": len([l for l in lignes if l.get("classe") == "Processus"]),
    }


def synthese_risques(db: Session, project_id: int) -> Dict[str, Any]:
    risks = db.query(Risk).filter(Risk.project_id == project_id).all()
    matrice = [[0] * 5 for _ in range(5)]   # matrice[impact-1][proba-1]
    par_severite: Dict[str, int] = {}
    par_categorie: Dict[str, int] = {}
    for r in risks:
        p = min(max(r.probability or 1, 1), 5)
        i = min(max(r.impact or 1, 1), 5)
        matrice[i - 1][p - 1] += 1
        par_severite[r.severity] = par_severite.get(r.severity, 0) + 1
        if r.category:
            par_categorie[r.category] = par_categorie.get(r.category, 0) + 1
    ouverts = [r for r in risks if r.status in ("Ouvert", "Survenu")]
    return {
        "total": len(risks),
        "ouverts": len(ouverts),
        "critiques": len([r for r in risks if r.severity == "Critique"]),
        "score_moyen": round(sum(r.score for r in risks) / len(risks), 1) if risks else 0,
        "matrice": matrice,
        "par_severite": par_severite,
        "par_categorie": par_categorie,
        "top": [
            {"id": r.id, "code": r.code, "title": r.title, "category": r.category,
             "probability": r.probability, "impact": r.impact, "score": r.score,
             "severity": r.severity, "status": r.status, "owner": r.owner}
            for r in sorted(risks, key=lambda x: x.score, reverse=True)[:10]
        ],
    }


def synthese_activites(db: Session, project_id: int) -> Dict[str, Any]:
    activities = db.query(Activity).filter(Activity.project_id == project_id).all()
    today = date.today()
    par_statut: Dict[str, int] = {}
    en_retard = []
    for a in activities:
        par_statut[a.status or "Planifiée"] = par_statut.get(a.status or "Planifiée", 0) + 1
        if a.end_date and a.end_date < today and (a.progress or 0) < 100 and a.status != "Annulée":
            en_retard.append({"id": a.id, "code": a.code, "name": a.name,
                              "end_date": a.end_date.isoformat(), "progress": a.progress or 0,
                              "retard_jours": (today - a.end_date).days, "responsible": a.responsible})
    avancement = [a.progress or 0 for a in activities]
    return {
        "total": len(activities),
        "avancement_moyen": round(sum(avancement) / len(avancement), 1) if avancement else 0,
        "achevees": len([a for a in activities if (a.progress or 0) >= 100]),
        "en_retard": sorted(en_retard, key=lambda x: -x["retard_jours"]),
        "nb_en_retard": len(en_retard),
        "par_statut": par_statut,
        "jalons": [{"id": a.id, "code": a.code, "name": a.name,
                    "end_date": a.end_date.isoformat() if a.end_date else None,
                    "status": a.status, "progress": a.progress or 0}
                   for a in activities if a.milestone],
    }


def synthese_budget(db: Session, project_id: int) -> Dict[str, Any]:
    lines = db.query(BudgetLine).filter(BudgetLine.project_id == project_id).all()
    planifie = sum(l.total_planned for l in lines)
    engage = sum(l.committed or 0 for l in lines)
    decaisse = sum(l.disbursed or 0 for l in lines)
    par_categorie: Dict[str, Dict[str, float]] = {}
    par_annee: Dict[int, Dict[str, float]] = {}
    trimestres = {"T1": 0.0, "T2": 0.0, "T3": 0.0, "T4": 0.0}
    for l in lines:
        cat = par_categorie.setdefault(l.category or "Non catégorisé", {"planifie": 0, "engage": 0, "decaisse": 0})
        cat["planifie"] += l.total_planned
        cat["engage"] += l.committed or 0
        cat["decaisse"] += l.disbursed or 0
        annee = par_annee.setdefault(l.year or 0, {"planifie": 0, "engage": 0, "decaisse": 0})
        annee["planifie"] += l.total_planned
        annee["engage"] += l.committed or 0
        annee["decaisse"] += l.disbursed or 0
        for key, val in (("T1", l.q1), ("T2", l.q2), ("T3", l.q3), ("T4", l.q4)):
            trimestres[key] += val or 0
    return {
        "planifie": round(planifie, 2),
        "engage": round(engage, 2),
        "decaisse": round(decaisse, 2),
        "solde": round(planifie - decaisse, 2),
        "taux_execution": round(decaisse / planifie * 100, 1) if planifie else 0,
        "taux_engagement": round(engage / planifie * 100, 1) if planifie else 0,
        "par_categorie": {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in par_categorie.items()},
        "par_annee": {str(k): {kk: round(vv, 2) for kk, vv in v.items()} for k, v in sorted(par_annee.items())},
        "par_trimestre": {k: round(v, 2) for k, v in trimestres.items()},
        "nb_lignes": len(lines),
    }


def avancement_temporel(project: Project) -> Dict[str, Any]:
    if not project.start_date or not project.end_date:
        return {"taux_temps": None, "jours_ecoules": None, "jours_restants": None}
    total = (project.end_date - project.start_date).days or 1
    ecoules = max(0, min((date.today() - project.start_date).days, total))
    return {
        "taux_temps": round(ecoules / total * 100, 1),
        "jours_ecoules": ecoules,
        "jours_restants": max(0, (project.end_date - date.today()).days),
        "duree_totale_jours": total,
    }


def alertes(db: Session, project_id: int) -> List[Dict[str, Any]]:
    """Alertes opérationnelles priorisées, alimentant le tableau de bord."""
    result: List[Dict[str, Any]] = []
    indicateurs = synthese_indicateurs(db, project_id)
    for ligne in indicateurs["lignes"]:
        if ligne["statut"] == "Critique":
            result.append({"niveau": "danger", "type": "Indicateur",
                           "message": f"{ligne['code'] or ''} {ligne['name'][:80]} — taux de réalisation "
                                      f"{ligne['taux']}%", "objet_id": ligne["id"]})
        elif ligne["taux"] is None and ligne["is_key"]:
            result.append({"niveau": "warning", "type": "Indicateur",
                           "message": f"Indicateur clé non renseigné : {ligne['code'] or ''} "
                                      f"{ligne['name'][:80]}", "objet_id": ligne["id"]})
    for r in synthese_risques(db, project_id)["top"]:
        if r["severity"] in ("Critique", "Élevé") and r["status"] in ("Ouvert", "Survenu"):
            result.append({"niveau": "danger" if r["severity"] == "Critique" else "warning",
                           "type": "Risque",
                           "message": f"{r['code'] or ''} {r['title'][:80]} — score {r['score']}/25 ({r['severity']})",
                           "objet_id": r["id"]})
    for a in synthese_activites(db, project_id)["en_retard"][:10]:
        result.append({"niveau": "warning", "type": "Activité",
                       "message": f"{a['code'] or ''} {a['name'][:70]} — {a['retard_jours']} jours de retard "
                                  f"({a['progress']}% réalisé)", "objet_id": a["id"]})
    for h in db.query(Assumption).filter(Assumption.project_id == project_id,
                                         Assumption.validation_status == "Invalidée").all():
        result.append({"niveau": "danger", "type": "Hypothèse",
                       "message": f"Hypothèse invalidée : {h.statement[:90]}", "objet_id": h.id})
    ordre = {"danger": 0, "warning": 1, "info": 2}
    return sorted(result, key=lambda x: ordre.get(x["niveau"], 3))


def tableau_de_bord(db: Session, project_id: int) -> Dict[str, Any]:
    project = db.get(Project, project_id)
    if not project:
        return {}
    indicateurs = synthese_indicateurs(db, project_id)
    budget = synthese_budget(db, project_id)
    activites = synthese_activites(db, project_id)
    temps = avancement_temporel(project)
    desagregation = synthese_desagregation(db, project_id)
    zones = consolidation_par_zone(db, project_id)
    qualite = synthese_qualite_smart(db, project_id)
    derniere = db.query(IndicatorActual).join(Indicator).filter(
        Indicator.project_id == project_id).order_by(IndicatorActual.updated_at.desc()).first()
    return {
        "desagregation": {
            "equite_genre": desagregation["equite_genre"],
            "taux_desagregation": desagregation["taux_desagregation"],
            "indicateurs_a_desagreger": desagregation["indicateurs_a_desagreger"],
            "indicateurs_desagreges": desagregation["indicateurs_desagreges"],
            "par_categorie": desagregation["par_categorie"],
        },
        "zones": {
            "nb_zones": zones["nb_zones"], "zones_couvertes": zones["zones_couvertes"],
            "taux_couverture_zones": zones["taux_couverture_zones"],
            "mesures_non_localisees": zones["mesures_non_localisees"],
            "detail": [{"nom": z["nom"], "code": z["code"], "niveau": z["niveau"],
                        "nb_mesures": z["nb_mesures"],
                        "beneficiaires_atteints": z["beneficiaires_atteints"],
                        "cible_beneficiaires": z["cible_beneficiaires"],
                        "taux_couverture": z["taux_couverture"],
                        "part_femmes": (z["equite_genre"] or {}).get("part_femmes")}
                       for z in zones["zones"]],
        },
        "qualite": {"score_systeme": qualite["score_systeme"],
                    "appreciation": qualite["appreciation"],
                    "conformes": qualite["conformes"], "a_reprendre": qualite["a_reprendre"],
                    "par_critere": qualite["par_critere"]},
        "derniere_mise_a_jour": derniere.updated_at.isoformat(timespec="seconds")
        if derniere and derniere.updated_at else None,
        "periodes": periodes_disponibles(db, project_id),
        "projet": {
            "id": project.id, "code": project.code, "title": project.title, "acronym": project.acronym,
            "status": project.status, "donor": project.donor, "currency": project.currency,
            "total_budget": project.total_budget, "country": project.country,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
        },
        "temps": temps,
        "indicateurs": indicateurs,
        "risques": synthese_risques(db, project_id),
        "activites": activites,
        "budget": budget,
        "alertes": alertes(db, project_id),
        "sante_globale": _sante_globale(indicateurs, activites, budget, temps),
    }


def _sante_globale(indicateurs, activites, budget, temps) -> Dict[str, Any]:
    """Indice de santé du projet : moyenne pondérée résultats / exécution / calendrier."""
    composantes = []
    if indicateurs["taux_moyen"] is not None:
        composantes.append(("Résultats", min(indicateurs["taux_moyen"], 120), 0.45))
    composantes.append(("Exécution physique", activites["avancement_moyen"], 0.30))
    composantes.append(("Exécution financière", min(budget["taux_execution"], 120), 0.25))
    poids_total = sum(p for _, _, p in composantes) or 1
    score = sum(v * p for _, v, p in composantes) / poids_total
    return {
        "score": round(score, 1),
        "statut": statut_performance(score),
        "couleur": COULEURS_STATUT[statut_performance(score)],
        "composantes": [{"libelle": lib, "valeur": round(val, 1), "poids": p} for lib, val, p in composantes],
        "ecart_calendrier": round(score - (temps["taux_temps"] or 0), 1) if temps.get("taux_temps") is not None else None,
    }


# ---------------------------------------------------------------------------
# Désagrégation : genre, âge, groupe cible…
# ---------------------------------------------------------------------------
def _cumuler(destination: Dict[str, Dict[str, float]], valeurs: Optional[Dict[str, Any]]) -> None:
    """Additionne un dictionnaire de valeurs désagrégées dans un accumulateur."""
    for categorie, modalites in (valeurs or {}).items():
        if not isinstance(modalites, dict):
            continue
        cible = destination.setdefault(categorie, {})
        for modalite, valeur in modalites.items():
            try:
                cible[modalite] = round(cible.get(modalite, 0.0) + float(valeur), 2)
            except (TypeError, ValueError):
                continue


def desagregation_indicateur(indicator: Indicator,
                             periode: Optional[str] = None) -> Dict[str, Any]:
    """Cumul des valeurs désagrégées d'un indicateur, toutes périodes ou une seule."""
    cumul: Dict[str, Dict[str, float]] = {}
    mesures = [a for a in indicator.actuals if periode is None or a.period_label == periode]
    for mesure in mesures:
        _cumuler(cumul, mesure.disaggregated_values)
    total_desagrege = {categorie: round(sum(modalites.values()), 2)
                       for categorie, modalites in cumul.items()}
    return {
        "id": indicator.id,
        "code": indicator.code,
        "name": indicator.name,
        "unit": indicator.unit,
        "categories_attendues": indicator.disaggregation or [],
        "valeurs": cumul,
        "totaux": total_desagrege,
        "nb_mesures": len(mesures),
        "renseigne": bool(cumul),
    }


def indice_equite_genre(valeurs_genre: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """Part des femmes et écart à la parité, à partir des modalités de la catégorie Sexe."""
    if not valeurs_genre:
        return None
    total = sum(v for v in valeurs_genre.values() if isinstance(v, (int, float)))
    if not total:
        return None
    femmes = float(valeurs_genre.get(MODALITE_FEMME, 0) or 0)
    part = round(femmes / total * 100, 1)
    return {
        "total": round(total, 2),
        "femmes": round(femmes, 2),
        "hommes": round(total - femmes, 2),
        "part_femmes": part,
        "ecart_parite": round(part - 50, 1),
        "appreciation": ("Parité atteinte" if abs(part - 50) <= 5 else
                         "Sous-représentation des femmes" if part < 45 else
                         "Sous-représentation des hommes"),
    }


def synthese_desagregation(db: Session, project_id: int,
                           periode: Optional[str] = None,
                           inclure_processus: Optional[bool] = None) -> Dict[str, Any]:
    """Analyse d'équité consolidée : par catégorie, par modalité et par indicateur."""
    indicateurs = indicateurs_du_projet(db, project_id, inclure_processus)
    global_cumul: Dict[str, Dict[str, float]] = {}
    lignes = []
    attendus, renseignes = 0, 0
    for indicateur in indicateurs:
        detail = desagregation_indicateur(indicateur, periode)
        if detail["categories_attendues"]:
            attendus += 1
            if detail["renseigne"]:
                renseignes += 1
        if detail["renseigne"]:
            _cumuler(global_cumul, detail["valeurs"])
            genre = detail["valeurs"].get(CATEGORIE_GENRE)
            detail["equite_genre"] = indice_equite_genre(genre) if genre else None
            manquantes = [c for c in detail["categories_attendues"] if c not in detail["valeurs"]]
            detail["categories_manquantes"] = manquantes
            lignes.append(detail)
        elif detail["categories_attendues"]:
            detail["equite_genre"] = None
            detail["categories_manquantes"] = detail["categories_attendues"]
            lignes.append(detail)

    par_categorie = []
    for categorie, modalites in sorted(global_cumul.items()):
        total = sum(modalites.values())
        par_categorie.append({
            "categorie": categorie,
            "total": round(total, 2),
            "modalites": [{"modalite": m, "valeur": round(v, 2),
                           "part": round(v / total * 100, 1) if total else 0}
                          for m, v in sorted(modalites.items(), key=lambda x: -x[1])],
            "modalites_referentielles": MODALITES_DESAGREGATION.get(categorie, []),
        })
    return {
        "periode": periode,
        "par_categorie": par_categorie,
        "equite_genre": indice_equite_genre(global_cumul.get(CATEGORIE_GENRE, {})),
        "lignes": lignes,
        "indicateurs_a_desagreger": attendus,
        "indicateurs_desagreges": renseignes,
        "taux_desagregation": round(renseignes / attendus * 100, 1) if attendus else None,
    }


# ---------------------------------------------------------------------------
# Consolidation par zone d'intervention et par activité
# ---------------------------------------------------------------------------
def consolidation_par_zone(db: Session, project_id: int,
                           periode: Optional[str] = None) -> Dict[str, Any]:
    """Cumul des réalisations par zone, avec taux de couverture des bénéficiaires."""
    zones = db.query(Zone).filter(Zone.project_id == project_id).order_by(
        Zone.order_index, Zone.name).all()
    indicateurs = {i.id: i for i in db.query(Indicator).filter(
        Indicator.project_id == project_id).all()}
    requete = db.query(IndicatorActual).filter(
        IndicatorActual.indicator_id.in_(list(indicateurs.keys()) or [0]))
    if periode:
        requete = requete.filter(IndicatorActual.period_label == periode)
    mesures = requete.all()

    par_zone: Dict[Any, Dict[str, Any]] = {}
    for zone in zones:
        par_zone[zone.id] = {
            "id": zone.id, "code": zone.code, "nom": zone.name, "niveau": zone.level,
            "population": zone.population, "cible_beneficiaires": zone.beneficiaries_target,
            "responsable": zone.responsible, "latitude": zone.latitude, "longitude": zone.longitude,
            "nb_mesures": 0, "indicateurs": {}, "desagregation": {}, "beneficiaires_atteints": 0.0,
        }
    par_zone[None] = {"id": None, "code": "—", "nom": "Non localisé", "niveau": "—",
                      "population": None, "cible_beneficiaires": None, "responsable": None,
                      "latitude": None, "longitude": None,
                      "nb_mesures": 0, "indicateurs": {}, "desagregation": {},
                      "beneficiaires_atteints": 0.0}

    for mesure in mesures:
        bloc = par_zone.get(mesure.zone_id) or par_zone[None]
        bloc["nb_mesures"] += 1
        indicateur = indicateurs.get(mesure.indicator_id)
        if indicateur is None:
            continue
        cle = indicateur.code or f"IND{indicateur.id}"
        entree = bloc["indicateurs"].setdefault(
            cle, {"code": cle, "libelle": indicateur.name, "unite": indicateur.unit,
                  "valeur": 0.0, "nb_mesures": 0})
        entree["valeur"] = round(entree["valeur"] + (mesure.value or 0), 2)
        entree["nb_mesures"] += 1
        _cumuler(bloc["desagregation"], mesure.disaggregated_values)
        # Les indicateurs exprimés en effectifs alimentent le décompte de bénéficiaires.
        if (indicateur.unit or "").strip().lower() in ("nombre", "effectif", "personne", "ménage"):
            bloc["beneficiaires_atteints"] += mesure.value or 0

    resultat = []
    for bloc in par_zone.values():
        if not bloc["nb_mesures"] and bloc["id"] is None:
            continue
        bloc["indicateurs"] = sorted(bloc["indicateurs"].values(), key=lambda x: x["code"])
        bloc["beneficiaires_atteints"] = round(bloc["beneficiaires_atteints"], 2)
        bloc["taux_couverture"] = (
            round(bloc["beneficiaires_atteints"] / bloc["cible_beneficiaires"] * 100, 1)
            if bloc["cible_beneficiaires"] else None)
        bloc["equite_genre"] = indice_equite_genre(bloc["desagregation"].get(CATEGORIE_GENRE, {}))
        resultat.append(bloc)
    resultat.sort(key=lambda z: (z["id"] is None, -(z["beneficiaires_atteints"] or 0)))

    zones_couvertes = len([z for z in resultat if z["nb_mesures"] and z["id"] is not None])
    return {
        "periode": periode,
        "zones": resultat,
        "nb_zones": len(zones),
        "zones_couvertes": zones_couvertes,
        "taux_couverture_zones": round(zones_couvertes / len(zones) * 100, 1) if zones else None,
        "mesures_non_localisees": par_zone[None]["nb_mesures"],
        "total_mesures": len(mesures),
    }


def consolidation_par_activite(db: Session, project_id: int,
                               periode: Optional[str] = None) -> List[Dict[str, Any]]:
    """Réalisations rattachées à chaque activité : lien collecte ↔ mise en œuvre."""
    activites = db.query(Activity).filter(Activity.project_id == project_id).order_by(
        Activity.order_index, Activity.code).all()
    indicateurs = {i.id: i for i in db.query(Indicator).filter(
        Indicator.project_id == project_id).all()}
    requete = db.query(IndicatorActual).filter(
        IndicatorActual.indicator_id.in_(list(indicateurs.keys()) or [0]),
        IndicatorActual.activity_id.isnot(None))
    if periode:
        requete = requete.filter(IndicatorActual.period_label == periode)
    mesures = requete.all()

    par_activite: Dict[int, Dict[str, Any]] = {
        a.id: {"id": a.id, "code": a.code, "libelle": a.name, "responsable": a.responsible,
               "avancement": a.progress or 0, "statut": a.status, "cout_prevu": a.planned_cost,
               "cout_reel": a.actual_cost, "nb_mesures": 0, "indicateurs": {},
               "desagregation": {}} for a in activites}
    for mesure in mesures:
        bloc = par_activite.get(mesure.activity_id)
        if bloc is None:
            continue
        bloc["nb_mesures"] += 1
        indicateur = indicateurs.get(mesure.indicator_id)
        if indicateur is None:
            continue
        cle = indicateur.code or f"IND{indicateur.id}"
        entree = bloc["indicateurs"].setdefault(
            cle, {"code": cle, "libelle": indicateur.name, "unite": indicateur.unit, "valeur": 0.0})
        entree["valeur"] = round(entree["valeur"] + (mesure.value or 0), 2)
        _cumuler(bloc["desagregation"], mesure.disaggregated_values)
    for bloc in par_activite.values():
        bloc["indicateurs"] = sorted(bloc["indicateurs"].values(), key=lambda x: x["code"])
        bloc["equite_genre"] = indice_equite_genre(bloc["desagregation"].get(CATEGORIE_GENRE, {}))
    return [b for b in par_activite.values() if b["nb_mesures"]]


# ---------------------------------------------------------------------------
# Qualité SMART des indicateurs
# ---------------------------------------------------------------------------
def _controles_smart(indicator: Indicator) -> Dict[str, bool]:
    """Contrôles automatiques adossés aux données réellement saisies."""
    return {
        "specifique": bool((indicator.name or "").strip()) and
                      bool((indicator.definition or "").strip()),
        "mesurable": bool((indicator.unit or "").strip()) and
                     bool((indicator.formula or "").strip() or
                          (indicator.collection_method or "").strip()),
        "atteignable": indicator.baseline_value is not None and indicator.target_value is not None
                       and indicator.baseline_value != indicator.target_value,
        "pertinent": indicator.element_id is not None,
        "temporel": indicator.target_date is not None and bool((indicator.frequency or "").strip()),
    }


def qualite_smart_indicateur(indicator: Indicator) -> Dict[str, Any]:
    """Note SMART d'un indicateur : contrôles automatiques et revue manuelle."""
    automatiques = _controles_smart(indicator)
    manuels = indicator.smart_check or {}
    criteres = []
    for critere in CRITERES_SMART:
        cle = critere["cle"]
        auto = automatiques.get(cle, False)
        manuel = manuels.get(cle)
        # La revue manuelle prime lorsqu'elle a été renseignée.
        satisfait = bool(manuel) if manuel is not None else auto
        criteres.append({
            "cle": cle, "libelle": critere["libelle"], "question": critere["question"],
            "controle": critere["controle"], "automatique": auto,
            "revue_manuelle": manuel, "satisfait": satisfait,
        })
    satisfaits = len([c for c in criteres if c["satisfait"]])
    score = round(satisfaits / len(CRITERES_SMART) * 100, 1)
    appreciation = next(libelle for seuil, libelle in SEUILS_QUALITE if score >= seuil)

    recommandations = []
    for critere in criteres:
        if critere["satisfait"]:
            continue
        recommandations.append({
            "specifique": "Rédiger la définition opérationnelle de l'indicateur.",
            "mesurable": "Renseigner l'unité de mesure et le mode de calcul ou la méthode "
                         "de collecte.",
            "atteignable": "Renseigner une valeur de référence et une cible finale distinctes.",
            "pertinent": "Rattacher l'indicateur à un résultat du cadre logique.",
            "temporel": "Fixer une échéance de cible et une fréquence de collecte.",
        }[critere["cle"]])
    if not (indicator.disaggregation or []):
        recommandations.append("Préciser les désagrégations exigées (au minimum le sexe) pour "
                               "permettre l'analyse d'équité.")
    if not (indicator.data_source or "").strip():
        recommandations.append("Documenter la source de données de l'indicateur.")
    if not (indicator.responsible or "").strip():
        recommandations.append("Désigner le responsable de la collecte.")

    return {
        "id": indicator.id, "code": indicator.code, "name": indicator.name,
        "level": indicator.level, "is_key": indicator.is_key,
        "criteres": criteres, "score": score, "criteres_satisfaits": satisfaits,
        "appreciation": appreciation,
        "couleur": ("#0F9D58" if score >= 90 else "#4CAF50" if score >= 75 else
                    "#F9A825" if score >= 60 else "#D93025"),
        "recommandations": recommandations,
        "revue_le": indicator.smart_reviewed_at.isoformat() if indicator.smart_reviewed_at else None,
        "commentaire": indicator.smart_comment,
    }


def synthese_qualite_smart(db: Session, project_id: int,
                           inclure_processus: Optional[bool] = None) -> Dict[str, Any]:
    indicateurs = indicateurs_du_projet(db, project_id, inclure_processus)
    lignes = [qualite_smart_indicateur(i) for i in indicateurs]
    par_critere = {}
    for critere in CRITERES_SMART:
        satisfaits = len([l for l in lignes
                          for c in l["criteres"] if c["cle"] == critere["cle"] and c["satisfait"]])
        par_critere[critere["libelle"]] = {
            "satisfaits": satisfaits, "total": len(lignes),
            "taux": round(satisfaits / len(lignes) * 100, 1) if lignes else 0,
        }
    scores = [l["score"] for l in lignes]
    score_systeme = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "lignes": sorted(lignes, key=lambda l: l["score"]),
        "total": len(lignes),
        "score_systeme": score_systeme,
        "appreciation": next(libelle for seuil, libelle in SEUILS_QUALITE if score_systeme >= seuil),
        "par_critere": par_critere,
        "conformes": len([l for l in lignes if l["score"] >= 90]),
        "a_reprendre": len([l for l in lignes if l["score"] < 60]),
    }


# ---------------------------------------------------------------------------
# Analyses périodées (rapports trimestriels, semestriels et annuels)
# ---------------------------------------------------------------------------
def periodes_disponibles(db: Session, project_id: int) -> List[str]:
    """Liste ordonnée des périodes pour lesquelles une cible ou une mesure existe."""
    indicateurs = db.query(Indicator).filter(Indicator.project_id == project_id).all()
    periodes = {t.period_label for i in indicateurs for t in i.targets} | \
               {a.period_label for i in indicateurs for a in i.actuals}
    return sorted(p for p in periodes if p)


def _periodes_couvertes(periode: str) -> List[str]:
    """Périodes élémentaires couvertes par une période de rapportage.

    « 2025 » couvre 2025, 2025-S1, 2025-S2 et 2025-T1 à 2025-T4 ;
    « 2025-S1 » couvre 2025-S1, 2025-T1 et 2025-T2.
    """
    if not periode:
        return []
    if "-T" in periode:
        return [periode]
    if "-S" in periode:
        annee, semestre = periode.split("-S")
        trimestres = ("1", "2") if semestre == "1" else ("3", "4")
        return [periode] + [f"{annee}-T{t}" for t in trimestres]
    return [periode] + [f"{periode}-S{s}" for s in (1, 2)] + \
           [f"{periode}-T{t}" for t in (1, 2, 3, 4)]


def analyse_periode(db: Session, project_id: int, periode: str,
                    inclure_processus: Optional[bool] = None) -> Dict[str, Any]:
    """Photographie de la performance sur une période de rapportage donnée."""
    couvertes = set(_periodes_couvertes(periode))
    indicateurs = indicateurs_du_projet(db, project_id, inclure_processus)
    lignes = []
    cumul_desagrege: Dict[str, Dict[str, float]] = {}
    for indicateur in indicateurs:
        cibles = {t.period_label: t.target_value for t in indicateur.targets
                  if t.period_label in couvertes}
        mesures = [a for a in indicateur.actuals if a.period_label in couvertes]
        if not cibles and not mesures:
            continue
        # On privilégie la période exacte du rapport ; à défaut, la période
        # élémentaire mesurée la plus récente parmi celles qu'il couvre.
        periodes_mesurees = {a.period_label for a in mesures}
        periode_retenue = periode if periode in periodes_mesurees else (
            sorted(mesures, key=lambda a: (a.reference_date or date.min, a.id))[-1].period_label
            if mesures else None)
        retenue = next((a for a in mesures if a.period_label == periode_retenue), None)
        cible = cibles.get(periode_retenue if periode_retenue in cibles else periode)
        if cible is None and cibles:
            cible = sum(v for v in cibles.values() if v is not None) or None
        realise = (valeur_de_periode(indicateur, periode_retenue)
                   if periode_retenue else None)
        taux = taux_periode(cible, realise, indicateur.direction)
        if taux is None:
            taux = taux_realisation(indicateur.baseline_value, indicateur.target_value,
                                    realise, indicateur.direction)
        for mesure in mesures:
            _cumuler(cumul_desagrege, mesure.disaggregated_values)
        desagregation: Dict[str, Dict[str, float]] = {}
        for mesure in mesures:
            _cumuler(desagregation, mesure.disaggregated_values)
        lignes.append({
            "id": indicateur.id, "code": indicateur.code, "name": indicateur.name,
            "level": indicateur.level, "unit": indicateur.unit, "is_key": indicateur.is_key,
            "baseline_value": indicateur.baseline_value, "target_value": indicateur.target_value,
            "cible_periode": cible, "realise_periode": realise,
            "periode_mesure": periode_retenue,
            "agregation": regle_agregation(indicateur),
            "taux": taux, "statut": statut_performance(taux),
            "couleur": COULEURS_STATUT[statut_performance(taux)],
            "responsable": indicateur.responsible,
            "source": retenue.source if retenue else None,
            "validation": retenue.validation_status if retenue else None,
            "desagregation": desagregation,
            "equite_genre": indice_equite_genre(desagregation.get(CATEGORIE_GENRE, {})),
            "nb_mesures": len(mesures),
        })

    renseignes = [l["taux"] for l in lignes if l["taux"] is not None]
    par_statut: Dict[str, int] = {}
    for ligne in lignes:
        par_statut[ligne["statut"]] = par_statut.get(ligne["statut"], 0) + 1

    activites = db.query(Activity).filter(Activity.project_id == project_id).all()
    annee = None
    try:
        annee = int(str(periode)[:4])
    except (TypeError, ValueError):
        pass
    lignes_budget = db.query(BudgetLine).filter(BudgetLine.project_id == project_id)
    if annee:
        lignes_budget = lignes_budget.filter(BudgetLine.year == annee)
    lignes_budget = lignes_budget.all()
    planifie = sum(l.total_planned for l in lignes_budget)
    decaisse = sum(l.disbursed or 0 for l in lignes_budget)

    return {
        "periode": periode,
        "periodes_couvertes": sorted(couvertes),
        "lignes": lignes,
        "total_indicateurs": len(lignes),
        "renseignes": len(renseignes),
        "taux_moyen": round(sum(renseignes) / len(renseignes), 1) if renseignes else None,
        "par_statut": par_statut,
        "desagregation": {
            categorie: {"total": round(sum(modalites.values()), 2),
                        "modalites": {m: round(v, 2) for m, v in modalites.items()}}
            for categorie, modalites in cumul_desagrege.items()},
        "equite_genre": indice_equite_genre(cumul_desagrege.get(CATEGORIE_GENRE, {})),
        "zones": consolidation_par_zone(db, project_id, periode if "-T" in str(periode) else None),
        "activites": {
            "total": len(activites),
            "achevees": len([a for a in activites if (a.progress or 0) >= 100]),
            "avancement_moyen": round(sum(a.progress or 0 for a in activites) / len(activites), 1)
            if activites else 0,
        },
        "budget": {
            "annee": annee, "planifie": round(planifie, 2), "decaisse": round(decaisse, 2),
            "taux_execution": round(decaisse / planifie * 100, 1) if planifie else 0,
        },
        "alertes": [l for l in lignes if l["statut"] in ("Critique", "À surveiller")],
    }


def portefeuille(db: Session) -> List[Dict[str, Any]]:
    """Vue consolidée multi-projets (niveau programme)."""
    resultat = []
    for project in db.query(Project).order_by(Project.code).all():
        indicateurs = synthese_indicateurs(db, project.id)
        budget = synthese_budget(db, project.id)
        activites = synthese_activites(db, project.id)
        risques = synthese_risques(db, project.id)
        temps = avancement_temporel(project)
        sante = _sante_globale(indicateurs, activites, budget, temps)
        resultat.append({
            "id": project.id, "code": project.code, "title": project.title, "acronym": project.acronym,
            "status": project.status, "donor": project.donor, "sector": project.sector,
            "currency": project.currency, "total_budget": project.total_budget,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "nb_indicateurs": indicateurs["total"], "taux_indicateurs": indicateurs["taux_moyen"],
            "taux_execution": budget["taux_execution"], "avancement": activites["avancement_moyen"],
            "nb_risques_critiques": risques["critiques"], "nb_alertes": len(alertes(db, project.id)),
            "sante": sante["score"], "statut_sante": sante["statut"], "couleur": sante["couleur"],
            "taux_temps": temps["taux_temps"],
        })
    return resultat
