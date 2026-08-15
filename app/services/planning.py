"""Ordonnancement du projet : méthode du chemin critique (CPM/PERT),
organigramme des tâches (WBS) et matrice des responsabilités (RACI).

Les trois analyses partagent le même socle : les activités du chronogramme, leurs
antécédents et leur rattachement au cadre logique.
"""
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models import Activity, LogframeElement, Project, RaciAssignment, Stakeholder

ROLES_RACI = {
    "R": {"libelle": "Réalise", "description": "Exécute le travail (Responsible)"},
    "A": {"libelle": "Approuve", "description": "Rend compte et valide (Accountable)"},
    "C": {"libelle": "Consulté", "description": "Est consulté avant la décision (Consulted)"},
    "I": {"libelle": "Informé", "description": "Est informé après la décision (Informed)"},
}
COULEURS_RACI = {"R": "#2E75B6", "A": "#D93025", "C": "#F9A825", "I": "#0F9D58"}


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------
def _antecedents(activite: Activity) -> List[str]:
    """Codes des activités prérequises, quel que soit le séparateur employé."""
    if not activite.dependencies:
        return []
    return [c.strip() for c in re.split(r"[;,/|\n]+", activite.dependencies) if c.strip()]


def duree_activite(activite: Activity) -> int:
    """Durée en jours calendaires : durée imposée, sinon écart entre les dates."""
    if activite.duration_days and activite.duration_days > 0:
        return int(activite.duration_days)
    if activite.start_date and activite.end_date:
        return max(1, (activite.end_date - activite.start_date).days + 1)
    return 1


# ---------------------------------------------------------------------------
# Chemin critique (Critical Path Method)
# ---------------------------------------------------------------------------
def chemin_critique(db: Session, project_id: int) -> Dict[str, Any]:
    """Ordonnancement au plus tôt et au plus tard, marges et chemin critique.

    Les relations sont de type fin-début : une activité ne peut démarrer qu'une
    fois tous ses antécédents achevés. Les activités sans antécédent démarrent à
    la date de début du projet (ou à leur propre date de début si elle est
    postérieure, afin de respecter un démarrage différé volontaire).
    """
    projet = db.get(Project, project_id)
    activites = db.query(Activity).filter(Activity.project_id == project_id).order_by(
        Activity.order_index, Activity.code).all()
    if not activites:
        return {"activites": [], "duree_projet_jours": 0, "chemin_critique": [],
                "avertissements": ["Aucune activité n'est enregistrée pour ce projet."],
                "date_debut": None, "date_fin_calculee": None, "nb_activites": 0,
                "nb_critiques": 0, "marge_moyenne": None}

    par_code = {a.code: a for a in activites if a.code}
    avertissements: List[str] = []
    origine = projet.start_date if projet and projet.start_date else min(
        [a.start_date for a in activites if a.start_date] or [date.today()])

    # Décalage de démarrage propre à chaque activité, exprimé en jours depuis l'origine.
    decalage: Dict[int, int] = {}
    for a in activites:
        decalage[a.id] = max(0, (a.start_date - origine).days) if a.start_date else 0

    predecesseurs: Dict[int, List[int]] = {}
    successeurs: Dict[int, List[int]] = {a.id: [] for a in activites}
    for a in activites:
        liste = []
        for code in _antecedents(a):
            precedente = par_code.get(code)
            if precedente is None:
                avertissements.append(
                    f"Activité {a.code or a.id} : antécédent « {code} » introuvable, ignoré.")
                continue
            if precedente.id == a.id:
                avertissements.append(
                    f"Activité {a.code or a.id} : elle se référence elle-même, lien ignoré.")
                continue
            liste.append(precedente.id)
            successeurs[precedente.id].append(a.id)
            # Incohérence fréquente : un antécédent qui s'achève après le début
            # planifié de son successeur. L'ordonnancement reste calculé sur la
            # relation déclarée, mais le calendrier saisi devient irréaliste.
            if (precedente.end_date and a.start_date
                    and precedente.end_date > a.start_date):
                avertissements.append(
                    f"Activité {a.code or a.id} : son antécédent {code} s'achève le "
                    f"{precedente.end_date.strftime('%d/%m/%Y')}, après son début planifié du "
                    f"{a.start_date.strftime('%d/%m/%Y')} — le calendrier saisi et le lien "
                    f"d'antécédence sont contradictoires.")
        predecesseurs[a.id] = liste

    # Tri topologique (Kahn) : détecte les circuits de dépendances.
    degres = {a.id: len(predecesseurs[a.id]) for a in activites}
    file = [a.id for a in activites if degres[a.id] == 0]
    ordre: List[int] = []
    while file:
        courant = file.pop(0)
        ordre.append(courant)
        for suivant in successeurs[courant]:
            degres[suivant] -= 1
            if degres[suivant] == 0:
                file.append(suivant)
    if len(ordre) < len(activites):
        restants = [a for a in activites if a.id not in ordre]
        avertissements.append(
            "Circuit de dépendances détecté entre les activités "
            + ", ".join(a.code or str(a.id) for a in restants[:6])
            + " : elles sont ordonnancées sur leurs seules dates.")
        ordre += [a.id for a in restants]

    par_id = {a.id: a for a in activites}
    durees = {a.id: duree_activite(a) for a in activites}

    # Passe avant : dates au plus tôt.
    debut_tot: Dict[int, int] = {}
    fin_tot: Dict[int, int] = {}
    for identifiant in ordre:
        precedentes = [fin_tot.get(p, 0) for p in predecesseurs[identifiant]
                       if p in fin_tot]
        debut = max(precedentes + [decalage[identifiant]])
        debut_tot[identifiant] = debut
        fin_tot[identifiant] = debut + durees[identifiant]

    duree_projet = max(fin_tot.values()) if fin_tot else 0

    # Passe arrière : dates au plus tard.
    debut_tard: Dict[int, int] = {}
    fin_tard: Dict[int, int] = {}
    for identifiant in reversed(ordre):
        suivantes = [debut_tard[s] for s in successeurs[identifiant] if s in debut_tard]
        fin = min(suivantes) if suivantes else duree_projet
        fin_tard[identifiant] = fin
        debut_tard[identifiant] = fin - durees[identifiant]

    lignes = []
    for a in activites:
        marge_totale = debut_tard[a.id] - debut_tot[a.id]
        marge_libre = min(
            [debut_tot[s] for s in successeurs[a.id]] + [fin_tot[a.id]]) - fin_tot[a.id] \
            if successeurs[a.id] else duree_projet - fin_tot[a.id]
        critique = marge_totale <= 0
        lignes.append({
            "id": a.id, "code": a.code, "name": a.name, "responsable": a.responsible,
            "duree": durees[a.id],
            "antecedents": _antecedents(a),
            "successeurs": [par_id[s].code or str(s) for s in successeurs[a.id]],
            "debut_tot": debut_tot[a.id], "fin_tot": fin_tot[a.id],
            "debut_tard": debut_tard[a.id], "fin_tard": fin_tard[a.id],
            "marge_totale": marge_totale, "marge_libre": max(0, marge_libre),
            "critique": critique,
            "date_debut_tot": (origine + timedelta(days=debut_tot[a.id])).isoformat(),
            "date_fin_tot": (origine + timedelta(days=fin_tot[a.id] - 1)).isoformat(),
            "date_debut_tard": (origine + timedelta(days=debut_tard[a.id])).isoformat(),
            "date_fin_tard": (origine + timedelta(days=fin_tard[a.id] - 1)).isoformat(),
            "start_date": a.start_date.isoformat() if a.start_date else None,
            "end_date": a.end_date.isoformat() if a.end_date else None,
            "progress": a.progress or 0, "status": a.status, "milestone": a.milestone,
            "planned_cost": a.planned_cost or 0,
            "niveau_pert": 0,
        })

    # Niveau de tracé du diagramme PERT : rang topologique de chaque activité.
    index_par_id = {ligne["id"]: ligne for ligne in lignes}
    for identifiant in ordre:
        precedentes = predecesseurs[identifiant]
        index_par_id[identifiant]["niveau_pert"] = (
            max((index_par_id[p]["niveau_pert"] for p in precedentes), default=-1) + 1)

    critiques = [l for l in lignes if l["critique"]]
    # Le chemin critique est reconstitué en suivant les activités sans marge.
    chemin: List[str] = []
    courant = next((l for l in sorted(critiques, key=lambda x: x["debut_tot"])), None)
    vus = set()
    while courant and courant["id"] not in vus:
        vus.add(courant["id"])
        chemin.append(courant["code"] or str(courant["id"]))
        suivants = [index_par_id[s] for s in successeurs[courant["id"]]
                    if index_par_id[s]["critique"]]
        courant = min(suivants, key=lambda x: x["debut_tot"]) if suivants else None

    marges = [l["marge_totale"] for l in lignes if not l["critique"]]
    ecart_calendrier = None
    date_fin_calculee = origine + timedelta(days=duree_projet - 1) if duree_projet else None
    if projet and projet.end_date and date_fin_calculee:
        ecart_calendrier = (date_fin_calculee - projet.end_date).days

    return {
        "activites": sorted(lignes, key=lambda l: (l["debut_tot"], l["code"] or "")),
        "duree_projet_jours": duree_projet,
        "duree_projet_mois": round(duree_projet / 30.44, 1) if duree_projet else 0,
        "date_debut": origine.isoformat(),
        "date_fin_calculee": date_fin_calculee.isoformat() if date_fin_calculee else None,
        "date_fin_planifiee": projet.end_date.isoformat() if projet and projet.end_date else None,
        "ecart_calendrier_jours": ecart_calendrier,
        "chemin_critique": chemin,
        "nb_activites": len(lignes),
        "nb_critiques": len(critiques),
        "part_critique": round(len(critiques) / len(lignes) * 100, 1) if lignes else 0,
        "marge_moyenne": round(sum(marges) / len(marges), 1) if marges else 0,
        "cout_chemin_critique": round(sum(l["planned_cost"] for l in critiques), 2),
        "avancement_chemin_critique": round(
            sum(l["progress"] for l in critiques) / len(critiques), 1) if critiques else None,
        "avertissements": avertissements,
        "niveaux_pert": (max(l["niveau_pert"] for l in lignes) + 1) if lignes else 0,
    }


# ---------------------------------------------------------------------------
# Organigramme des tâches (Work Breakdown Structure)
# ---------------------------------------------------------------------------
def _numeroter(noeuds: List[Dict[str, Any]], prefixe: str = "") -> None:
    for index, noeud in enumerate(noeuds, start=1):
        noeud["wbs"] = f"{prefixe}{index}"
        _numeroter(noeud["enfants"], f"{noeud['wbs']}.")


def organigramme_taches(db: Session, project_id: int) -> Dict[str, Any]:
    """Décomposition hiérarchique du projet en lots de travail.

    Le WBS est déduit de la chaîne de résultats : le projet se décompose en
    effets, chaque effet en produits, chaque produit en activités, qui
    constituent les lots de travail élémentaires. Les activités non rattachées
    sont regroupées dans un lot « Gestion et coordination ».
    """
    projet = db.get(Project, project_id)
    elements = db.query(LogframeElement).filter(
        LogframeElement.project_id == project_id).order_by(LogframeElement.order_index).all()
    activites = db.query(Activity).filter(Activity.project_id == project_id).order_by(
        Activity.order_index, Activity.code).all()

    activites_par_element: Dict[Any, List[Activity]] = {}
    for a in activites:
        activites_par_element.setdefault(a.element_id, []).append(a)

    # Le cadre logique peut comporter des éléments de niveau ACTIVITE qui doublonnent
    # les enregistrements du chronogramme. Le chronogramme fait foi pour les lots de
    # travail : un élément de niveau ACTIVITE n'est retenu que s'il ne correspond à
    # aucune activité programmée (même code ou même énoncé).
    codes_activites = {(a.code or "").strip().lower() for a in activites if a.code}
    libelles_activites = {(a.name or "").strip().lower() for a in activites}
    elements = [
        e for e in elements
        if e.level != "ACTIVITE"
        or ((e.code or "").strip().lower() not in codes_activites
            and (e.statement or "").strip().lower() not in libelles_activites)
    ]
    identifiants_retenus = {e.id for e in elements}
    enfants_par_parent: Dict[Any, List[LogframeElement]] = {}
    for e in elements:
        parent = e.parent_id if e.parent_id in identifiants_retenus else None
        enfants_par_parent.setdefault(parent, []).append(e)

    def noeud_activite(a: Activity) -> Dict[str, Any]:
        return {
            "type": "Lot de travail", "id": a.id, "code": a.code, "libelle": a.name,
            "responsable": a.responsible, "cout": a.planned_cost or 0,
            "duree": duree_activite(a), "avancement": a.progress or 0,
            "livrable": a.deliverable, "jalon": bool(a.milestone),
            "date_debut": a.start_date.isoformat() if a.start_date else None,
            "date_fin": a.end_date.isoformat() if a.end_date else None,
            "enfants": [],
        }

    def construire(element: LogframeElement) -> Dict[str, Any]:
        noeud = {
            "type": {"IMPACT": "Objectif global", "EFFET": "Composante",
                     "PRODUIT": "Sous-composante", "ACTIVITE": "Lot de travail"}.get(
                         element.level, element.level),
            "id": element.id, "code": element.code, "libelle": element.statement,
            "responsable": element.responsible, "cout": 0, "duree": 0, "avancement": 0,
            "livrable": None, "jalon": False, "date_debut": None, "date_fin": None,
            "enfants": [construire(e) for e in enfants_par_parent.get(element.id, [])] +
                       [noeud_activite(a) for a in activites_par_element.get(element.id, [])],
        }
        return noeud

    racines = [construire(e) for e in enfants_par_parent.get(None, [])]
    orphelines = activites_par_element.get(None, [])
    if orphelines:
        racines.append({
            "type": "Composante", "id": None, "code": "GC",
            "libelle": "Gestion, coordination et suivi-évaluation",
            "responsable": "Unité de gestion du projet", "cout": 0, "duree": 0,
            "avancement": 0, "livrable": None, "jalon": False,
            "date_debut": None, "date_fin": None,
            "enfants": [noeud_activite(a) for a in orphelines],
        })
    _numeroter(racines)

    # Consolidation ascendante des coûts, durées et avancements.
    def consolider(noeud: Dict[str, Any]) -> Tuple[float, int, float, int]:
        if not noeud["enfants"]:
            return noeud["cout"], noeud["duree"], noeud["avancement"], 1
        cout, duree, avancement, nombre = 0.0, 0, 0.0, 0
        for enfant in noeud["enfants"]:
            c, d, av, n = consolider(enfant)
            cout += c
            duree = max(duree, d)
            avancement += av * n
            nombre += n
        noeud["cout"] = round(cout, 2)
        noeud["duree"] = duree
        noeud["avancement"] = round(avancement / nombre, 1) if nombre else 0
        dates_debut = [e["date_debut"] for e in noeud["enfants"] if e["date_debut"]]
        dates_fin = [e["date_fin"] for e in noeud["enfants"] if e["date_fin"]]
        noeud["date_debut"] = min(dates_debut) if dates_debut else None
        noeud["date_fin"] = max(dates_fin) if dates_fin else None
        return noeud["cout"], noeud["duree"], noeud["avancement"], nombre

    total_cout = 0.0
    for racine in racines:
        cout, _, _, _ = consolider(racine)
        total_cout += cout

    def aplatir(noeuds: List[Dict[str, Any]], profondeur: int = 0) -> List[Dict[str, Any]]:
        plat = []
        for noeud in noeuds:
            copie = {k: v for k, v in noeud.items() if k != "enfants"}
            copie["profondeur"] = profondeur
            copie["nb_enfants"] = len(noeud["enfants"])
            plat.append(copie)
            plat += aplatir(noeud["enfants"], profondeur + 1)
        return plat

    plat = aplatir(racines)
    return {
        "projet": {"code": projet.code if projet else "", "titre": projet.title if projet else "",
                   "wbs": "0"},
        "racines": racines,
        "lignes": plat,
        "nb_niveaux": (max(l["profondeur"] for l in plat) + 1) if plat else 0,
        "nb_lots": len([l for l in plat if l["type"] == "Lot de travail"]),
        "cout_total": round(total_cout, 2),
        "activites_non_rattachees": len(orphelines),
    }


# ---------------------------------------------------------------------------
# Matrice des responsabilités (RACI)
# ---------------------------------------------------------------------------
def matrice_raci(db: Session, project_id: int) -> Dict[str, Any]:
    """Matrice activités × parties prenantes, avec contrôle de cohérence.

    Deux règles sont vérifiées : une activité doit compter exactement un
    approbateur (A) et au moins un réalisateur (R). Une activité sans A n'a pas
    de responsable identifié ; une activité avec plusieurs A dilue la
    responsabilité et constitue la faiblesse la plus fréquente des matrices RACI.
    """
    parties = db.query(Stakeholder).filter(Stakeholder.project_id == project_id).order_by(
        Stakeholder.order_index, Stakeholder.name).all()
    activites = db.query(Activity).filter(Activity.project_id == project_id).order_by(
        Activity.order_index, Activity.code).all()
    affectations = db.query(RaciAssignment).filter(
        RaciAssignment.project_id == project_id).all()

    grille: Dict[int, Dict[int, str]] = {}
    for affectation in affectations:
        grille.setdefault(affectation.activity_id, {})[affectation.stakeholder_id] = \
            affectation.role

    lignes, anomalies = [], []
    for a in activites:
        roles = grille.get(a.id, {})
        approbateurs = [pid for pid, role in roles.items() if role == "A"]
        realisateurs = [pid for pid, role in roles.items() if role == "R"]
        if len(approbateurs) == 0:
            anomalies.append({"activite": a.code or str(a.id), "libelle": a.name,
                              "anomalie": "Aucun approbateur (A) désigné",
                              "gravite": "danger"})
        elif len(approbateurs) > 1:
            anomalies.append({"activite": a.code or str(a.id), "libelle": a.name,
                              "anomalie": f"{len(approbateurs)} approbateurs (A) désignés : la "
                                          f"responsabilité doit être unique",
                              "gravite": "danger"})
        if not realisateurs:
            anomalies.append({"activite": a.code or str(a.id), "libelle": a.name,
                              "anomalie": "Aucun réalisateur (R) désigné", "gravite": "warning"})
        if not roles:
            anomalies.append({"activite": a.code or str(a.id), "libelle": a.name,
                              "anomalie": "Activité non couverte par la matrice",
                              "gravite": "warning"})
        lignes.append({
            "id": a.id, "code": a.code, "libelle": a.name, "responsable": a.responsible,
            "statut": a.status, "roles": roles,
            "nb_a": len(approbateurs), "nb_r": len(realisateurs),
            "conforme": len(approbateurs) == 1 and len(realisateurs) >= 1,
        })

    charge = []
    for partie in parties:
        compte = {"R": 0, "A": 0, "C": 0, "I": 0}
        for roles in grille.values():
            role = roles.get(partie.id)
            if role in compte:
                compte[role] += 1
        charge.append({
            "id": partie.id, "code": partie.code, "nom": partie.name,
            "organisation": partie.organisation, "categorie": partie.category,
            **compte, "total": sum(compte.values()),
            "taux_couverture": round(sum(compte.values()) / len(activites) * 100, 1)
            if activites else 0,
        })

    surcharges = [c for c in charge if c["A"] > max(3, len(activites) * 0.4)]
    for surcharge in surcharges:
        anomalies.append({
            "activite": "—", "libelle": surcharge["nom"],
            "anomalie": f"Cette partie prenante approuve {surcharge['A']} activités : "
                        f"risque de goulot d'étranglement décisionnel",
            "gravite": "warning"})

    return {
        "parties_prenantes": charge,
        "activites": lignes,
        "roles": ROLES_RACI,
        "couleurs": COULEURS_RACI,
        "nb_activites": len(activites),
        "nb_parties": len(parties),
        "nb_affectations": len(affectations),
        "activites_conformes": len([l for l in lignes if l["conforme"]]),
        "taux_conformite": round(
            len([l for l in lignes if l["conforme"]]) / len(lignes) * 100, 1) if lignes else 0,
        "taux_couverture": round(len([l for l in lignes if l["roles"]]) / len(lignes) * 100, 1)
        if lignes else 0,
        "anomalies": anomalies,
    }
