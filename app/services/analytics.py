"""Moteur de calcul de la performance : taux de réalisation, agrégations, alertes."""
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import Activity, Assumption, BudgetLine, Indicator, IndicatorActual, IndicatorTarget, Project, Risk

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


def derniere_valeur(indicator: Indicator) -> Optional[IndicatorActual]:
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
    valeur = last.value if last else None
    cible_de_periode = None
    if last:
        jalon = next((t for t in indicator.targets if t.period_label == last.period_label), None)
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
        "unit": indicator.unit,
        "is_key": indicator.is_key,
        "frequency": indicator.frequency,
        "responsible": indicator.responsible,
        "baseline_value": indicator.baseline_value,
        "target_value": indicator.target_value,
        "actual_value": valeur,
        "period_label": last.period_label if last else None,
        "period_target": cible_de_periode,
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
    """Série cibles vs réalisations, alignée sur les libellés de période."""
    cibles = {t.period_label: t.target_value for t in indicator.targets}
    reels = {}
    for a in sorted(indicator.actuals, key=lambda x: (x.reference_date or date.min, x.id)):
        reels[a.period_label] = a.value
    periodes = sorted(set(list(cibles.keys()) + list(reels.keys())))
    return {
        "periodes": periodes,
        "cibles": [cibles.get(p) for p in periodes],
        "reels": [reels.get(p) for p in periodes],
    }


def synthese_indicateurs(db: Session, project_id: int) -> Dict[str, Any]:
    indicators = db.query(Indicator).filter(Indicator.project_id == project_id,
                                            Indicator.is_active.is_(True)).all()
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
    return {
        "lignes": lignes,
        "total": len(lignes),
        "renseignes": len(renseignes),
        "taux_moyen": round(sum(renseignes) / len(renseignes), 1) if renseignes else None,
        "taux_couverture": round(len(renseignes) / len(lignes) * 100, 1) if lignes else 0,
        "par_statut": par_statut,
        "par_niveau": par_niveau,
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
    return {
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
