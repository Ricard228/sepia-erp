"""Génération des livrables Excel : cadre logique, IPTT, PTBA, chronogramme,
tableau de bord et jeu de données normalisé pour Power BI."""
from datetime import date
from io import BytesIO
from typing import Any, Dict, List

import xlsxwriter
from sqlalchemy.orm import Session

from ..config import LIBELLES_NIVEAUX
from ..models import (Activity, Assumption, BudgetLine, Form, FormQuestion, Indicator,
                      LogframeElement, Project, Risk)
from . import analytics

BLEU = "#1F4E79"
BLEU_CLAIR = "#DCE6F1"
GRIS = "#F2F2F2"
NIVEAU_COULEURS = {"IMPACT": "#1F4E79", "EFFET": "#2E75B6", "PRODUIT": "#5B9BD5", "ACTIVITE": "#9DC3E6"}


# ---------------------------------------------------------------------------
# Fabrique de styles
# ---------------------------------------------------------------------------
def _formats(wb) -> Dict[str, Any]:
    return {
        "titre": wb.add_format({"bold": True, "font_size": 16, "font_color": BLEU}),
        "soustitre": wb.add_format({"italic": True, "font_size": 10, "font_color": "#555555"}),
        "entete": wb.add_format({"bold": True, "bg_color": BLEU, "font_color": "white", "border": 1,
                                 "align": "center", "valign": "vcenter", "text_wrap": True}),
        "sous_entete": wb.add_format({"bold": True, "bg_color": BLEU_CLAIR, "border": 1,
                                      "align": "center", "valign": "vcenter", "text_wrap": True}),
        "cellule": wb.add_format({"border": 1, "valign": "top", "text_wrap": True}),
        "cellule_c": wb.add_format({"border": 1, "valign": "vcenter", "align": "center"}),
        "cellule_g": wb.add_format({"border": 1, "valign": "top", "text_wrap": True, "bg_color": GRIS}),
        "nombre": wb.add_format({"border": 1, "num_format": "#,##0.00", "valign": "vcenter"}),
        "entier": wb.add_format({"border": 1, "num_format": "#,##0", "valign": "vcenter"}),
        "pourcent": wb.add_format({"border": 1, "num_format": "0.0\\%", "align": "center", "valign": "vcenter"}),
        "date": wb.add_format({"border": 1, "num_format": "dd/mm/yyyy", "align": "center"}),
        "gras": wb.add_format({"bold": True, "border": 1, "bg_color": GRIS, "valign": "vcenter"}),
        "total": wb.add_format({"bold": True, "border": 1, "bg_color": BLEU_CLAIR,
                                "num_format": "#,##0.00", "valign": "vcenter"}),
        "kpi_label": wb.add_format({"bold": True, "font_size": 10, "font_color": "#555555",
                                    "align": "center", "border": 1, "bg_color": GRIS}),
        "kpi_valeur": wb.add_format({"bold": True, "font_size": 20, "font_color": BLEU,
                                     "align": "center", "border": 1, "num_format": "#,##0.0"}),
        "gantt": wb.add_format({"bg_color": "#2E75B6", "border": 1}),
        "gantt_fait": wb.add_format({"bg_color": "#0f9d58", "border": 1}),
        "gantt_retard": wb.add_format({"bg_color": "#D93025", "border": 1}),
        "wrap": wb.add_format({"text_wrap": True, "valign": "top"}),
    }


def _niveau_format(wb, niveau: str):
    return wb.add_format({"bold": True, "bg_color": NIVEAU_COULEURS.get(niveau, "#BFBFBF"),
                          "font_color": "white", "border": 1, "valign": "vcenter", "text_wrap": True})


def _entete_feuille(ws, fmt, projet: Project, titre: str, nb_colonnes: int = 8):
    ws.write(0, 0, titre, fmt["titre"])
    ws.write(1, 0, f"{projet.code} — {projet.title}", fmt["soustitre"])
    ws.write(2, 0, f"Bailleur : {projet.donor or 'N/A'} | Période : "
                   f"{projet.start_date or 'N/A'} → {projet.end_date or 'N/A'} | "
                   f"Édité le {date.today().strftime('%d/%m/%Y')} par SEPIA", fmt["soustitre"])
    ws.freeze_panes(5, 0)
    return 4


def _elements_tries(db: Session, project_id: int) -> List[LogframeElement]:
    """Retourne la hiérarchie du cadre logique aplatie dans l'ordre de lecture."""
    elements = db.query(LogframeElement).filter(LogframeElement.project_id == project_id).all()
    par_parent: Dict[Any, List[LogframeElement]] = {}
    for e in elements:
        par_parent.setdefault(e.parent_id, []).append(e)
    for enfants in par_parent.values():
        enfants.sort(key=lambda x: (x.order_index or 0, x.code or "", x.id))
    ordre_niveaux = {"IMPACT": 0, "EFFET": 1, "PRODUIT": 2, "ACTIVITE": 3}
    resultat: List[LogframeElement] = []

    def descendre(parent_id):
        for enfant in par_parent.get(parent_id, []):
            resultat.append(enfant)
            descendre(enfant.id)

    racines = par_parent.get(None, [])
    racines.sort(key=lambda x: (ordre_niveaux.get(x.level, 9), x.order_index or 0, x.code or ""))
    for racine in racines:
        resultat.append(racine)
        descendre(racine.id)
    # Éléments orphelins (parent supprimé) ajoutés en fin de liste
    vus = {e.id for e in resultat}
    for e in sorted(elements, key=lambda x: (ordre_niveaux.get(x.level, 9), x.code or "")):
        if e.id not in vus:
            resultat.append(e)
    return resultat


# ---------------------------------------------------------------------------
# 1. Cadre logique
# ---------------------------------------------------------------------------
def cadre_logique_xlsx(db: Session, project: Project) -> BytesIO:
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True, "default_date_format": "dd/mm/yyyy"})
    fmt = _formats(wb)
    ws = wb.add_worksheet("Cadre logique")
    ws.set_landscape()
    ws.set_paper(8)  # A3
    ws.fit_to_pages(1, 0)
    ligne = _entete_feuille(ws, fmt, project, "CADRE LOGIQUE DU PROJET")

    entetes = ["Niveau", "Code", "Logique d'intervention", "Indicateurs objectivement vérifiables (IOV)",
               "Référence (Baseline)", "Cible finale", "Sources de vérification", "Hypothèses / Risques", "Responsable"]
    largeurs = [16, 10, 46, 46, 14, 14, 30, 34, 20]
    for col, (titre, largeur) in enumerate(zip(entetes, largeurs)):
        ws.write(ligne, col, titre, fmt["entete"])
        ws.set_column(col, col, largeur)
    ws.set_row(ligne, 34)
    ligne += 1

    indicateurs_par_element: Dict[int, List[Indicator]] = {}
    for ind in db.query(Indicator).filter(Indicator.project_id == project.id).all():
        indicateurs_par_element.setdefault(ind.element_id, []).append(ind)

    for element in _elements_tries(db, project.id):
        inds = indicateurs_par_element.get(element.id, [])
        texte_iov = "\n".join(
            f"• {i.code or ''} {i.name}" + (f" ({i.unit})" if i.unit else "") for i in inds) or "—"
        baseline = "\n".join(
            f"{i.baseline_value if i.baseline_value is not None else '—'}" for i in inds) or "—"
        cible = "\n".join(f"{i.target_value if i.target_value is not None else '—'}" for i in inds) or "—"
        ws.write(ligne, 0, LIBELLES_NIVEAUX.get(element.level, element.level), _niveau_format(wb, element.level))
        ws.write(ligne, 1, element.code or "", fmt["cellule_c"])
        ws.write(ligne, 2, element.statement, fmt["cellule"])
        ws.write(ligne, 3, texte_iov, fmt["cellule"])
        ws.write(ligne, 4, baseline, fmt["cellule_c"])
        ws.write(ligne, 5, cible, fmt["cellule_c"])
        ws.write(ligne, 6, element.means_of_verification or "\n".join(
            i.data_source or "" for i in inds) or "—", fmt["cellule"])
        ws.write(ligne, 7, element.assumptions or "—", fmt["cellule"])
        ws.write(ligne, 8, element.responsible or "—", fmt["cellule"])
        ws.set_row(ligne, max(28, 13 * max(1, len(inds))))
        ligne += 1

    # Feuille annexe : hypothèses critiques
    hypotheses = db.query(Assumption).filter(Assumption.project_id == project.id).all()
    if hypotheses:
        ws2 = wb.add_worksheet("Hypothèses critiques")
        l2 = _entete_feuille(ws2, fmt, project, "REGISTRE DES HYPOTHÈSES CRITIQUES")
        cols = ["Code", "Niveau", "Énoncé de l'hypothèse", "Criticité", "Statut de validation",
                "Méthode de vérification", "Responsable", "Date de revue", "Commentaire"]
        for col, (titre, largeur) in enumerate(zip(cols, [10, 14, 50, 12, 20, 30, 20, 14, 30])):
            ws2.write(l2, col, titre, fmt["entete"])
            ws2.set_column(col, col, largeur)
        l2 += 1
        for h in hypotheses:
            valeurs = [h.code or "", h.level or "", h.statement, h.criticality or "",
                       h.validation_status or "", h.verification_method or "", h.responsible or "",
                       h.review_date.strftime("%d/%m/%Y") if h.review_date else "", h.comment or ""]
            for col, valeur in enumerate(valeurs):
                ws2.write(l2, col, valeur, fmt["cellule"])
            l2 += 1

    wb.close()
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 2. Cadre de rendement / performance
# ---------------------------------------------------------------------------
def cadre_rendement_xlsx(db: Session, project: Project) -> BytesIO:
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = _formats(wb)
    ws = wb.add_worksheet("Cadre de rendement")
    ws.set_landscape()
    ws.set_paper(8)
    ligne = _entete_feuille(ws, fmt, project, "CADRE DE RENDEMENT (Performance Measurement Framework)")

    entetes = ["Niveau de résultat", "Énoncé du résultat", "Indicateur de rendement", "Unité",
               "Désagrégation", "Référence", "Cible finale", "Période mesurée",
               "Cible de la période", "Réalisé", "Taux de la période (%)",
               "Progression vers la cible finale (%)", "Statut",
               "Source de données", "Méthode de collecte", "Fréquence", "Responsable", "Coût estimé"]
    largeurs = [16, 40, 44, 12, 22, 12, 13, 14, 14, 12, 12, 14, 16, 26, 24, 14, 18, 14]
    for col, (titre, largeur) in enumerate(zip(entetes, largeurs)):
        ws.write(ligne, col, titre, fmt["entete"])
        ws.set_column(col, col, largeur)
    ws.set_row(ligne, 34)
    ligne += 1

    elements = {e.id: e for e in db.query(LogframeElement).filter(LogframeElement.project_id == project.id).all()}
    perf = {p["id"]: p for p in analytics.synthese_indicateurs(db, project.id)["lignes"]}
    ordre = {"IMPACT": 0, "EFFET": 1, "PRODUIT": 2, "ACTIVITE": 3}
    indicateurs = sorted(db.query(Indicator).filter(Indicator.project_id == project.id).all(),
                         key=lambda i: (ordre.get(i.level, 9), i.code or ""))
    debut_tableau = ligne
    for ind in indicateurs:
        element = elements.get(ind.element_id)
        p = perf.get(ind.id, {})
        ws.write(ligne, 0, LIBELLES_NIVEAUX.get(ind.level, ind.level or ""), _niveau_format(wb, ind.level or ""))
        ws.write(ligne, 1, element.statement if element else "—", fmt["cellule"])
        ws.write(ligne, 2, f"{ind.code or ''} {ind.name}".strip(), fmt["cellule"])
        ws.write(ligne, 3, ind.unit or "", fmt["cellule_c"])
        ws.write(ligne, 4, ", ".join(ind.disaggregation or []) or "—", fmt["cellule"])
        ws.write(ligne, 5, ind.baseline_value if ind.baseline_value is not None else "—", fmt["cellule_c"])
        ws.write(ligne, 6, ind.target_value if ind.target_value is not None else "—", fmt["cellule_c"])
        ws.write(ligne, 7, p.get("period_label") or "—", fmt["cellule_c"])
        ws.write(ligne, 8, p.get("period_target") if p.get("period_target") is not None else "—", fmt["cellule_c"])
        ws.write(ligne, 9, p.get("actual_value") if p.get("actual_value") is not None else "—", fmt["cellule_c"])
        ws.write(ligne, 10, p.get("taux") if p.get("taux") is not None else "—", fmt["cellule_c"])
        ws.write(ligne, 11, p.get("taux_final") if p.get("taux_final") is not None else "—", fmt["cellule_c"])
        statut = p.get("statut", "Non renseigné")
        ws.write(ligne, 12, statut, wb.add_format({
            "border": 1, "align": "center", "bold": True, "font_color": "white",
            "bg_color": analytics.COULEURS_STATUT.get(statut, "#9AA0A6")}))
        ws.write(ligne, 13, ind.data_source or "", fmt["cellule"])
        ws.write(ligne, 14, ind.collection_method or "", fmt["cellule"])
        ws.write(ligne, 15, ind.frequency or "", fmt["cellule_c"])
        ws.write(ligne, 16, ind.responsible or "", fmt["cellule"])
        ws.write(ligne, 17, ind.cost_estimate or 0, fmt["nombre"])
        ligne += 1

    if indicateurs:
        ws.autofilter(debut_tableau - 1, 0, ligne - 1, len(entetes) - 1)
    wb.close()
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 3. IPTT — cadre de suivi des indicateurs (cibles vs réalisations par période)
# ---------------------------------------------------------------------------
def iptt_xlsx(db: Session, project: Project) -> BytesIO:
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = _formats(wb)
    ws = wb.add_worksheet("IPTT")
    ws.set_landscape()
    ws.set_paper(8)
    ligne = _entete_feuille(ws, fmt, project, "CADRE DE SUIVI DES INDICATEURS (IPTT)")

    indicateurs = db.query(Indicator).filter(Indicator.project_id == project.id).all()
    periodes: List[str] = sorted({t.period_label for i in indicateurs for t in i.targets} |
                                 {a.period_label for i in indicateurs for a in i.actuals})
    if not periodes:
        annee_debut = project.start_date.year if project.start_date else date.today().year
        annee_fin = project.end_date.year if project.end_date else annee_debut + 2
        periodes = [f"{an}-T{t}" for an in range(annee_debut, annee_fin + 1) for t in range(1, 5)]

    fixes = ["Niveau", "Code", "Indicateur", "Unité", "Référence", "Cible finale"]
    for col, (titre, largeur) in enumerate(zip(fixes, [14, 10, 46, 12, 12, 12])):
        ws.merge_range(ligne, col, ligne + 1, col, titre, fmt["entete"])
        ws.set_column(col, col, largeur)
    col = len(fixes)
    for periode in periodes:
        ws.merge_range(ligne, col, ligne, col + 2, periode, fmt["entete"])
        ws.write(ligne + 1, col, "Cible", fmt["sous_entete"])
        ws.write(ligne + 1, col + 1, "Réalisé", fmt["sous_entete"])
        ws.write(ligne + 1, col + 2, "%", fmt["sous_entete"])
        ws.set_column(col, col + 2, 9)
        col += 3
    ws.merge_range(ligne, col, ligne + 1, col, "Cumul réalisé", fmt["entete"])
    ws.merge_range(ligne, col + 1, ligne + 1, col + 1, "Taux global (%)", fmt["entete"])
    ws.set_column(col, col + 1, 14)
    ws.set_row(ligne, 22)
    ws.set_row(ligne + 1, 20)
    ligne += 2
    premiere_ligne = ligne

    ordre = {"IMPACT": 0, "EFFET": 1, "PRODUIT": 2, "ACTIVITE": 3}
    for ind in sorted(indicateurs, key=lambda i: (ordre.get(i.level, 9), i.code or "")):
        cibles = {t.period_label: t.target_value for t in ind.targets}
        reels = {a.period_label: a.value for a in ind.actuals}
        ws.write(ligne, 0, ind.level or "", _niveau_format(wb, ind.level or ""))
        ws.write(ligne, 1, ind.code or "", fmt["cellule_c"])
        ws.write(ligne, 2, ind.name, fmt["cellule"])
        ws.write(ligne, 3, ind.unit or "", fmt["cellule_c"])
        ws.write(ligne, 4, ind.baseline_value if ind.baseline_value is not None else "", fmt["cellule_c"])
        ws.write(ligne, 5, ind.target_value if ind.target_value is not None else "", fmt["cellule_c"])
        col = len(fixes)
        cumul = 0.0
        for periode in periodes:
            cible = cibles.get(periode)
            reel = reels.get(periode)
            ws.write(ligne, col, cible if cible is not None else "", fmt["cellule_c"])
            ws.write(ligne, col + 1, reel if reel is not None else "", fmt["cellule_c"])
            taux = round(reel / cible * 100, 1) if (cible and reel is not None) else ""
            ws.write(ligne, col + 2, taux, fmt["cellule_c"])
            if reel is not None:
                cumul += reel
            col += 3
        perf = analytics.indicator_performance(ind)
        ws.write(ligne, col, cumul, fmt["nombre"])
        ws.write(ligne, col + 1, perf["taux_final"] if perf["taux_final"] is not None else "",
                 fmt["cellule_c"])
        ligne += 1

    # Mise en forme conditionnelle sur la colonne du taux global
    if ligne > premiere_ligne:
        col_taux = len(fixes) + 3 * len(periodes) + 1
        ws.conditional_format(premiere_ligne, col_taux, ligne - 1, col_taux, {
            "type": "3_color_scale", "min_color": "#F4C7C3", "mid_color": "#FCE8B2", "max_color": "#B7E1CD"})
        ws.autofilter(premiere_ligne - 1, 0, ligne - 1, 5)
    wb.close()
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 4. Chronogramme (Gantt)
# ---------------------------------------------------------------------------
def chronogramme_xlsx(db: Session, project: Project) -> BytesIO:
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = _formats(wb)
    ws = wb.add_worksheet("Chronogramme")
    ws.set_landscape()
    ws.set_paper(8)
    ligne = _entete_feuille(ws, fmt, project, "CHRONOGRAMME D'EXÉCUTION (diagramme de Gantt)")

    activites = db.query(Activity).filter(Activity.project_id == project.id).order_by(
        Activity.order_index, Activity.code).all()
    dates = [a.start_date for a in activites if a.start_date] + [a.end_date for a in activites if a.end_date]
    debut = project.start_date or (min(dates) if dates else date.today())
    fin = project.end_date or (max(dates) if dates else date.today())
    mois: List[tuple] = []
    an, m = debut.year, debut.month
    while (an, m) <= (fin.year, fin.month) and len(mois) < 120:
        mois.append((an, m))
        m += 1
        if m > 12:
            m, an = 1, an + 1

    fixes = ["Code", "Activité", "Responsable", "Début", "Fin", "Avanc. (%)", "Statut", "Coût prévu"]
    for col, (titre, largeur) in enumerate(zip(fixes, [10, 48, 20, 12, 12, 11, 14, 14])):
        ws.merge_range(ligne, col, ligne + 1, col, titre, fmt["entete"])
        ws.set_column(col, col, largeur)
    col = len(fixes)
    noms_mois = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
    # Bandeau des années : une plage fusionnée par année couverte
    blocs_annee: List[List[int]] = []   # [colonne_debut, colonne_fin, annee]
    for index, (an, m) in enumerate(mois):
        position = col + index
        if blocs_annee and blocs_annee[-1][2] == an:
            blocs_annee[-1][1] = position
        else:
            blocs_annee.append([position, position, an])
        ws.write(ligne + 1, position, noms_mois[m - 1], fmt["sous_entete"])
        ws.set_column(position, position, 4.5)
    for debut_bloc, fin_bloc, an in blocs_annee:
        if fin_bloc > debut_bloc:
            ws.merge_range(ligne, debut_bloc, ligne, fin_bloc, str(an), fmt["entete"])
        else:
            ws.write(ligne, debut_bloc, str(an), fmt["entete"])
    ligne += 2

    aujourdhui = date.today()
    for a in activites:
        ws.write(ligne, 0, a.code or "", fmt["cellule_c"])
        ws.write(ligne, 1, ("★ " if a.milestone else "") + a.name, fmt["cellule"])
        ws.write(ligne, 2, a.responsible or "", fmt["cellule"])
        ws.write(ligne, 3, a.start_date.strftime("%d/%m/%Y") if a.start_date else "", fmt["cellule_c"])
        ws.write(ligne, 4, a.end_date.strftime("%d/%m/%Y") if a.end_date else "", fmt["cellule_c"])
        ws.write(ligne, 5, (a.progress or 0) / 100, wb.add_format(
            {"border": 1, "num_format": "0%", "align": "center"}))
        ws.write(ligne, 6, a.status or "", fmt["cellule_c"])
        ws.write(ligne, 7, a.planned_cost or 0, fmt["nombre"])
        if a.start_date and a.end_date:
            style = fmt["gantt"]
            if (a.progress or 0) >= 100:
                style = fmt["gantt_fait"]
            elif a.end_date < aujourdhui:
                style = fmt["gantt_retard"]
            for index, (an, m) in enumerate(mois):
                dans_periode = (an, m) >= (a.start_date.year, a.start_date.month) and \
                               (an, m) <= (a.end_date.year, a.end_date.month)
                if dans_periode:
                    ws.write_blank(ligne, len(fixes) + index, None, style)
        ligne += 1

    ligne += 1
    ws.write(ligne, 1, "Légende :", fmt["gras"])
    ws.write_blank(ligne, 2, None, fmt["gantt"])
    ws.write(ligne, 3, "Planifié / en cours", fmt["wrap"])
    ws.write_blank(ligne, 4, None, fmt["gantt_fait"])
    ws.write(ligne, 5, "Achevé", fmt["wrap"])
    ws.write_blank(ligne, 6, None, fmt["gantt_retard"])
    ws.write(ligne, 7, "En retard", fmt["wrap"])
    wb.close()
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 5. PTBA — Plan de travail et budget annuel
# ---------------------------------------------------------------------------
def ptba_xlsx(db: Session, project: Project, annee: int = None) -> BytesIO:
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = _formats(wb)
    ws = wb.add_worksheet(f"PTBA {annee or ''}".strip())
    ws.set_landscape()
    ws.set_paper(8)
    titre = f"PLAN DE TRAVAIL ET BUDGET ANNUEL (PTBA) {annee}" if annee else \
            "PLAN DE TRAVAIL ET BUDGET PLURIANNUEL"
    ligne = _entete_feuille(ws, fmt, project, titre)

    requete = db.query(BudgetLine).filter(BudgetLine.project_id == project.id)
    if annee:
        requete = requete.filter(BudgetLine.year == annee)
    lignes_budget = requete.order_by(BudgetLine.code).all()
    activites = {a.id: a for a in db.query(Activity).filter(Activity.project_id == project.id).all()}
    elements = {e.id: e for e in db.query(LogframeElement).filter(LogframeElement.project_id == project.id).all()}

    entetes = ["Code", "Résultat / Produit", "Activité", "Ligne budgétaire", "Catégorie", "Unité",
               "Qté", "Coût unitaire", "Nb", f"Total ({project.currency})", "T1", "T2", "T3", "T4",
               "Source de financement", "Engagé", "Décaissé", "Taux exéc. (%)", "Responsable"]
    largeurs = [10, 30, 36, 34, 18, 12, 8, 14, 6, 16, 13, 13, 13, 13, 20, 14, 14, 12, 18]
    for col, (t, largeur) in enumerate(zip(entetes, largeurs)):
        ws.write(ligne, col, t, fmt["entete"])
        ws.set_column(col, col, largeur)
    ws.set_row(ligne, 34)
    ligne += 1
    premiere = ligne

    for l in lignes_budget:
        activite = activites.get(l.activity_id)
        element = elements.get(activite.element_id) if activite else None
        total = l.total_planned
        taux = round((l.disbursed or 0) / total * 100, 1) if total else 0
        valeurs = [
            l.code or "", element.statement if element else "—", activite.name if activite else "—",
            l.label, l.category or "", l.unit or "", l.quantity or 0, l.unit_cost or 0,
            l.frequency_count or 1, total, l.q1 or 0, l.q2 or 0, l.q3 or 0, l.q4 or 0,
            l.funding_source or "", l.committed or 0, l.disbursed or 0, taux,
            activite.responsible if activite else "",
        ]
        for col, valeur in enumerate(valeurs):
            if col in (7, 9, 10, 11, 12, 13, 15, 16):
                ws.write(ligne, col, valeur, fmt["nombre"])
            elif col in (6, 8, 17):
                ws.write(ligne, col, valeur, fmt["cellule_c"])
            else:
                ws.write(ligne, col, valeur, fmt["cellule"])
        ligne += 1

    if lignes_budget:
        ws.write(ligne, 3, "TOTAL GÉNÉRAL", fmt["gras"])
        for col in (9, 10, 11, 12, 13, 15, 16):
            lettre = xlsxwriter.utility.xl_col_to_name(col)
            ws.write_formula(ligne, col, f"=SUM({lettre}{premiere + 1}:{lettre}{ligne})", fmt["total"])
        ws.autofilter(premiere - 1, 0, ligne - 1, len(entetes) - 1)

    # Feuille de synthèse budgétaire
    synthese = analytics.synthese_budget(db, project.id)
    ws2 = wb.add_worksheet("Synthèse budgétaire")
    l2 = _entete_feuille(ws2, fmt, project, "SYNTHÈSE DE L'EXÉCUTION BUDGÉTAIRE")
    ws2.set_column(0, 0, 34)
    ws2.set_column(1, 3, 18)
    ws2.write(l2, 0, "Catégorie", fmt["entete"])
    for col, t in enumerate(["Planifié", "Engagé", "Décaissé", "Taux d'exécution (%)"], start=1):
        ws2.write(l2, col, t, fmt["entete"])
    l2 += 1
    depart = l2
    for categorie, montants in sorted(synthese["par_categorie"].items()):
        ws2.write(l2, 0, categorie, fmt["cellule"])
        ws2.write(l2, 1, montants["planifie"], fmt["nombre"])
        ws2.write(l2, 2, montants["engage"], fmt["nombre"])
        ws2.write(l2, 3, montants["decaisse"], fmt["nombre"])
        ws2.write(l2, 4, round(montants["decaisse"] / montants["planifie"] * 100, 1)
                  if montants["planifie"] else 0, fmt["cellule_c"])
        l2 += 1
    if synthese["par_categorie"]:
        graphique = wb.add_chart({"type": "column"})
        graphique.add_series({"name": "Planifié",
                              "categories": ["Synthèse budgétaire", depart, 0, l2 - 1, 0],
                              "values": ["Synthèse budgétaire", depart, 1, l2 - 1, 1],
                              "fill": {"color": "#2E75B6"}})
        graphique.add_series({"name": "Décaissé",
                              "categories": ["Synthèse budgétaire", depart, 0, l2 - 1, 0],
                              "values": ["Synthèse budgétaire", depart, 3, l2 - 1, 3],
                              "fill": {"color": "#0f9d58"}})
        graphique.set_title({"name": "Exécution budgétaire par catégorie"})
        graphique.set_size({"width": 760, "height": 380})
        ws2.insert_chart(l2 + 2, 0, graphique)
    wb.close()
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 6. Registre des risques
# ---------------------------------------------------------------------------
def risques_xlsx(db: Session, project: Project) -> BytesIO:
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = _formats(wb)
    ws = wb.add_worksheet("Registre des risques")
    ws.set_landscape()
    ws.set_paper(8)
    ligne = _entete_feuille(ws, fmt, project, "REGISTRE ET MATRICE DES RISQUES")

    entetes = ["Code", "Catégorie", "Risque identifié", "Cause", "Conséquence", "Prob. (1-5)",
               "Impact (1-5)", "Score", "Niveau", "Mesures d'atténuation", "Plan de contingence",
               "Prob. rés.", "Impact rés.", "Score rés.", "Responsable", "Statut", "Date de revue"]
    largeurs = [8, 22, 40, 28, 28, 10, 10, 8, 12, 40, 32, 10, 10, 10, 18, 14, 13]
    for col, (t, largeur) in enumerate(zip(entetes, largeurs)):
        ws.write(ligne, col, t, fmt["entete"])
        ws.set_column(col, col, largeur)
    ws.set_row(ligne, 34)
    ligne += 1
    premiere = ligne

    couleurs_niveau = {"Critique": "#D93025", "Élevé": "#EA8600", "Modéré": "#F9A825", "Faible": "#0f9d58"}
    risques = sorted(db.query(Risk).filter(Risk.project_id == project.id).all(),
                     key=lambda r: -r.score)
    for r in risques:
        score_res = (r.residual_probability or 0) * (r.residual_impact or 0)
        valeurs = [r.code or "", r.category or "", r.title, r.cause or "", r.consequence or "",
                   r.probability or "", r.impact or "", r.score, r.severity, r.mitigation or "",
                   r.contingency or "", r.residual_probability or "", r.residual_impact or "",
                   score_res or "", r.owner or "", r.status or "",
                   r.review_date.strftime("%d/%m/%Y") if r.review_date else ""]
        for col, valeur in enumerate(valeurs):
            if col == 8:
                ws.write(ligne, col, valeur, wb.add_format({
                    "border": 1, "align": "center", "bold": True, "font_color": "white",
                    "bg_color": couleurs_niveau.get(r.severity, "#9AA0A6")}))
            elif col in (5, 6, 7, 11, 12, 13):
                ws.write(ligne, col, valeur, fmt["cellule_c"])
            else:
                ws.write(ligne, col, valeur, fmt["cellule"])
        ligne += 1
    if risques:
        ws.autofilter(premiere - 1, 0, ligne - 1, len(entetes) - 1)

    # Matrice 5x5
    synthese = analytics.synthese_risques(db, project.id)
    ws2 = wb.add_worksheet("Matrice P x I")
    ws2.write(0, 0, "MATRICE DES RISQUES — Probabilité × Impact", fmt["titre"])
    ws2.write(2, 0, "Impact ↓ / Probabilité →", fmt["entete"])
    ws2.set_column(0, 0, 26)
    ws2.set_column(1, 5, 14)
    for p in range(1, 6):
        ws2.write(2, p, f"P{p}", fmt["entete"])
    libelles_impact = {5: "5 — Catastrophique", 4: "4 — Majeur", 3: "3 — Modéré", 2: "2 — Mineur", 1: "1 — Négligeable"}
    for index, i in enumerate(range(5, 0, -1)):
        ws2.write(3 + index, 0, libelles_impact[i], fmt["entete"])
        for p in range(1, 6):
            score = i * p
            couleur = "#D93025" if score >= 15 else "#EA8600" if score >= 10 else \
                      "#F9A825" if score >= 5 else "#0f9d58"
            nb = synthese["matrice"][i - 1][p - 1]
            ws2.write(3 + index, p, f"{nb} risque(s)" if nb else "",
                      wb.add_format({"border": 1, "align": "center", "valign": "vcenter",
                                     "bg_color": couleur, "font_color": "white", "bold": True}))
            ws2.set_row(3 + index, 26)
    ws2.write(10, 0, f"Total : {synthese['total']} risques — {synthese['critiques']} critiques — "
                     f"score moyen {synthese['score_moyen']}/25", fmt["soustitre"])
    wb.close()
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 7. Tableau de bord Excel automatisé
# ---------------------------------------------------------------------------
def tableau_de_bord_xlsx(db: Session, project: Project) -> BytesIO:
    tdb = analytics.tableau_de_bord(db, project.id)
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = _formats(wb)

    ws = wb.add_worksheet("Tableau de bord")
    ws.set_landscape()
    ws.hide_gridlines(2)
    ws.set_column(0, 12, 15)
    ws.write(0, 0, "TABLEAU DE BORD DE PERFORMANCE", fmt["titre"])
    ws.write(1, 0, f"{project.code} — {project.title}", fmt["soustitre"])
    ws.write(2, 0, f"Généré le {date.today().strftime('%d/%m/%Y')} — Plateforme SEPIA", fmt["soustitre"])

    kpis = [
        ("Santé globale (%)", tdb["sante_globale"]["score"]),
        ("Taux moyen des indicateurs (%)", tdb["indicateurs"]["taux_moyen"] or 0),
        ("Avancement physique (%)", tdb["activites"]["avancement_moyen"]),
        ("Exécution budgétaire (%)", tdb["budget"]["taux_execution"]),
        ("Temps écoulé (%)", tdb["temps"]["taux_temps"] or 0),
        ("Risques critiques", tdb["risques"]["critiques"]),
    ]
    for index, (libelle, valeur) in enumerate(kpis):
        col = index * 2
        ws.merge_range(4, col, 4, col + 1, libelle, fmt["kpi_label"])
        ws.merge_range(5, col, 6, col + 1, valeur, fmt["kpi_valeur"])
    ws.set_row(5, 26)

    # Données pour les graphiques
    wsd = wb.add_worksheet("Données")
    wsd.write(0, 0, "Statut", fmt["entete"])
    wsd.write(0, 1, "Nombre d'indicateurs", fmt["entete"])
    ligne = 1
    for statut, nombre in tdb["indicateurs"]["par_statut"].items():
        wsd.write(ligne, 0, statut, fmt["cellule"])
        wsd.write(ligne, 1, nombre, fmt["entier"])
        ligne += 1
    fin_statuts = ligne

    wsd.write(0, 3, "Niveau", fmt["entete"])
    wsd.write(0, 4, "Taux moyen (%)", fmt["entete"])
    l_niveau = 1
    for niveau, valeurs in tdb["indicateurs"]["par_niveau"].items():
        wsd.write(l_niveau, 3, LIBELLES_NIVEAUX.get(niveau, niveau), fmt["cellule"])
        wsd.write(l_niveau, 4, valeurs["taux_moyen"] or 0, fmt["nombre"])
        l_niveau += 1

    wsd.write(0, 6, "Trimestre", fmt["entete"])
    wsd.write(0, 7, "Budget planifié", fmt["entete"])
    for index, (trimestre, montant) in enumerate(tdb["budget"]["par_trimestre"].items(), start=1):
        wsd.write(index, 6, trimestre, fmt["cellule"])
        wsd.write(index, 7, montant, fmt["nombre"])

    if fin_statuts > 1:
        camembert = wb.add_chart({"type": "pie"})
        camembert.add_series({
            "name": "Répartition des indicateurs par statut",
            "categories": ["Données", 1, 0, fin_statuts - 1, 0],
            "values": ["Données", 1, 1, fin_statuts - 1, 1],
            "data_labels": {"percentage": True, "category": True},
        })
        camembert.set_title({"name": "Indicateurs par statut de performance"})
        camembert.set_size({"width": 520, "height": 330})
        ws.insert_chart(8, 0, camembert)

    if l_niveau > 1:
        barres = wb.add_chart({"type": "bar"})
        barres.add_series({
            "name": "Taux moyen de réalisation",
            "categories": ["Données", 1, 3, l_niveau - 1, 3],
            "values": ["Données", 1, 4, l_niveau - 1, 4],
            "fill": {"color": "#2E75B6"},
            "data_labels": {"value": True},
        })
        barres.set_title({"name": "Performance par niveau de résultat (%)"})
        barres.set_size({"width": 520, "height": 330})
        ws.insert_chart(8, 6, barres)

    colonnes = wb.add_chart({"type": "column"})
    colonnes.add_series({
        "name": "Budget planifié par trimestre",
        "categories": ["Données", 1, 6, 4, 6],
        "values": ["Données", 1, 7, 4, 7],
        "fill": {"color": "#0f9d58"},
        "data_labels": {"value": True},
    })
    colonnes.set_title({"name": f"Programmation budgétaire trimestrielle ({project.currency})"})
    colonnes.set_size({"width": 520, "height": 330})
    ws.insert_chart(26, 0, colonnes)

    # Feuille des alertes
    wsa = wb.add_worksheet("Alertes")
    wsa.set_column(0, 0, 14)
    wsa.set_column(1, 1, 16)
    wsa.set_column(2, 2, 110)
    for col, t in enumerate(["Niveau", "Type", "Message"]):
        wsa.write(0, col, t, fmt["entete"])
    for index, alerte in enumerate(tdb["alertes"], start=1):
        couleur = "#D93025" if alerte["niveau"] == "danger" else "#F9A825"
        wsa.write(index, 0, alerte["niveau"].upper(), wb.add_format(
            {"border": 1, "bg_color": couleur, "font_color": "white", "bold": True, "align": "center"}))
        wsa.write(index, 1, alerte["type"], fmt["cellule"])
        wsa.write(index, 2, alerte["message"], fmt["cellule"])

    # Détail des indicateurs
    wsi = wb.add_worksheet("Détail indicateurs")
    entetes = ["Code", "Indicateur", "Niveau", "Unité", "Référence", "Cible", "Réalisé",
               "Taux (%)", "Statut", "Période", "Responsable"]
    for col, (t, largeur) in enumerate(zip(entetes, [10, 50, 14, 12, 12, 12, 12, 10, 16, 14, 20])):
        wsi.write(0, col, t, fmt["entete"])
        wsi.set_column(col, col, largeur)
    for index, ligne_ind in enumerate(tdb["indicateurs"]["lignes"], start=1):
        valeurs = [ligne_ind["code"] or "", ligne_ind["name"], ligne_ind["level"] or "",
                   ligne_ind["unit"] or "", ligne_ind["baseline_value"], ligne_ind["target_value"],
                   ligne_ind["actual_value"], ligne_ind["taux"], ligne_ind["statut"],
                   ligne_ind["period_label"] or "", ligne_ind["responsible"] or ""]
        for col, valeur in enumerate(valeurs):
            wsi.write(index, col, valeur if valeur is not None else "", fmt["cellule"])
    if tdb["indicateurs"]["lignes"]:
        wsi.autofilter(0, 0, len(tdb["indicateurs"]["lignes"]), len(entetes) - 1)
        wsi.conditional_format(1, 7, len(tdb["indicateurs"]["lignes"]), 7, {
            "type": "3_color_scale", "min_color": "#F4C7C3", "mid_color": "#FCE8B2", "max_color": "#B7E1CD"})
    wb.close()
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 8. Jeu de données normalisé pour Power BI
# ---------------------------------------------------------------------------
def powerbi_dataset_xlsx(db: Session, project: Project) -> BytesIO:
    """Modèle en étoile prêt à charger dans Power BI Desktop (Obtenir des données > Excel)."""
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = _formats(wb)

    def ecrire_table(nom: str, entetes: List[str], lignes: List[List[Any]]):
        ws = wb.add_worksheet(nom)
        for col, titre in enumerate(entetes):
            ws.write(0, col, titre, fmt["entete"])
            ws.set_column(col, col, max(12, min(46, len(titre) + 6)))
        for r, valeurs in enumerate(lignes, start=1):
            for col, valeur in enumerate(valeurs):
                ws.write(r, col, valeur if valeur is not None else "", fmt["cellule"])
        if lignes:
            ws.autofilter(0, 0, len(lignes), len(entetes) - 1)
        ws.freeze_panes(1, 0)

    ecrire_table("Dim_Projet",
                 ["ProjetID", "Code", "Titre", "Acronyme", "Secteur", "Pays", "Bailleur",
                  "Agence", "Statut", "Devise", "BudgetTotal", "DateDebut", "DateFin"],
                 [[project.id, project.code, project.title, project.acronym, project.sector,
                   project.country, project.donor, project.executing_agency, project.status,
                   project.currency, project.total_budget,
                   project.start_date.isoformat() if project.start_date else None,
                   project.end_date.isoformat() if project.end_date else None]])

    elements = _elements_tries(db, project.id)
    ecrire_table("Dim_Resultat",
                 ["ResultatID", "ProjetID", "ParentID", "Niveau", "Code", "Enonce",
                  "SourcesVerification", "Hypotheses", "Responsable"],
                 [[e.id, e.project_id, e.parent_id, e.level, e.code, e.statement,
                   e.means_of_verification, e.assumptions, e.responsible] for e in elements])

    indicateurs = db.query(Indicator).filter(Indicator.project_id == project.id).all()
    ecrire_table("Dim_Indicateur",
                 ["IndicateurID", "ProjetID", "ResultatID", "Code", "Libelle", "Niveau", "Type",
                  "Unite", "Desagregation", "Reference", "Cible", "Sens", "Frequence",
                  "SourceDonnees", "MethodeCollecte", "Responsable", "IndicateurCle"],
                 [[i.id, i.project_id, i.element_id, i.code, i.name, i.level, i.indicator_type,
                   i.unit, ", ".join(i.disaggregation or []), i.baseline_value, i.target_value,
                   i.direction, i.frequency, i.data_source, i.collection_method, i.responsible,
                   "Oui" if i.is_key else "Non"] for i in indicateurs])

    faits_cibles, faits_reels = [], []
    for i in indicateurs:
        for t in i.targets:
            faits_cibles.append([t.id, i.id, i.code, t.period_label, t.year,
                                 t.period_start.isoformat() if t.period_start else None,
                                 t.period_end.isoformat() if t.period_end else None, t.target_value])
        for a in i.actuals:
            perf = analytics.taux_realisation(i.baseline_value, i.target_value, a.value, i.direction)
            faits_reels.append([a.id, i.id, i.code, a.period_label, a.year,
                                a.reference_date.isoformat() if a.reference_date else None,
                                a.value, a.source, a.validation_status, perf,
                                analytics.statut_performance(perf)])
    ecrire_table("Fait_Cible", ["CibleID", "IndicateurID", "CodeIndicateur", "Periode", "Annee",
                                "DebutPeriode", "FinPeriode", "ValeurCible"], faits_cibles)
    ecrire_table("Fait_Realisation", ["RealisationID", "IndicateurID", "CodeIndicateur", "Periode",
                                      "Annee", "DateReference", "ValeurRealisee", "Source",
                                      "Validation", "TauxRealisation", "StatutPerformance"], faits_reels)

    activites = db.query(Activity).filter(Activity.project_id == project.id).all()
    ecrire_table("Fait_Activite",
                 ["ActiviteID", "ProjetID", "ResultatID", "Code", "Libelle", "Responsable",
                  "DateDebut", "DateFin", "Avancement", "Statut", "CoutPrevu", "CoutReel", "Annee", "Jalon"],
                 [[a.id, a.project_id, a.element_id, a.code, a.name, a.responsible,
                   a.start_date.isoformat() if a.start_date else None,
                   a.end_date.isoformat() if a.end_date else None, a.progress, a.status,
                   a.planned_cost, a.actual_cost, a.year, "Oui" if a.milestone else "Non"]
                  for a in activites])

    lignes_budget = db.query(BudgetLine).filter(BudgetLine.project_id == project.id).all()
    ecrire_table("Fait_Budget",
                 ["LigneID", "ProjetID", "ActiviteID", "Code", "Libelle", "Categorie", "Unite",
                  "Quantite", "CoutUnitaire", "Nombre", "TotalPlanifie", "T1", "T2", "T3", "T4",
                  "Engage", "Decaisse", "SourceFinancement", "Annee"],
                 [[l.id, l.project_id, l.activity_id, l.code, l.label, l.category, l.unit,
                   l.quantity, l.unit_cost, l.frequency_count, l.total_planned, l.q1, l.q2, l.q3,
                   l.q4, l.committed, l.disbursed, l.funding_source, l.year] for l in lignes_budget])

    risques = db.query(Risk).filter(Risk.project_id == project.id).all()
    ecrire_table("Fait_Risque",
                 ["RisqueID", "ProjetID", "Code", "Titre", "Categorie", "Probabilite", "Impact",
                  "Score", "Niveau", "Statut", "Responsable", "DateRevue"],
                 [[r.id, r.project_id, r.code, r.title, r.category, r.probability, r.impact,
                   r.score, r.severity, r.status, r.owner,
                   r.review_date.isoformat() if r.review_date else None] for r in risques])

    # Dimension calendrier (facilite les analyses temporelles dans Power BI)
    debut = project.start_date or date.today()
    fin = project.end_date or date.today()
    lignes_calendrier = []
    an, m = debut.year, debut.month
    identifiant = 1
    while (an, m) <= (fin.year, fin.month) and identifiant < 200:
        trimestre = (m - 1) // 3 + 1
        lignes_calendrier.append([identifiant, f"{an}-{m:02d}", an, m, f"T{trimestre}",
                                  f"{an}-T{trimestre}", f"{an}-{m:02d}-01"])
        identifiant += 1
        m += 1
        if m > 12:
            m, an = 1, an + 1
    ecrire_table("Dim_Calendrier", ["CalendrierID", "AnneeMois", "Annee", "Mois", "Trimestre",
                                    "AnneeTrimestre", "Date"], lignes_calendrier)

    # Notice de branchement Power BI
    ws = wb.add_worksheet("LISEZ-MOI")
    ws.set_column(0, 0, 120)
    notice = [
        "MODÈLE DE DONNÉES POWER BI — PLATEFORME SEPIA",
        "",
        "1. Ouvrir Power BI Desktop > Accueil > Obtenir des données > Classeur Excel > sélectionner ce fichier.",
        "2. Cocher toutes les tables (Dim_* et Fait_*) puis « Charger ».",
        "3. Onglet Modèle : créer les relations (1 → *) suivantes :",
        "     Dim_Projet[ProjetID]        →  Dim_Resultat[ProjetID], Fait_Activite[ProjetID],",
        "                                     Fait_Budget[ProjetID], Fait_Risque[ProjetID]",
        "     Dim_Resultat[ResultatID]    →  Dim_Indicateur[ResultatID], Fait_Activite[ResultatID]",
        "     Dim_Indicateur[IndicateurID]→  Fait_Cible[IndicateurID], Fait_Realisation[IndicateurID]",
        "     Dim_Calendrier[AnneeTrimestre] → Fait_Realisation[Periode] (relation *:* si besoin)",
        "4. Mesures DAX recommandées :",
        "     Taux de réalisation = DIVIDE(SUM(Fait_Realisation[ValeurRealisee]), SUM(Fait_Cible[ValeurCible]))",
        "     Taux d'exécution budgétaire = DIVIDE(SUM(Fait_Budget[Decaisse]), SUM(Fait_Budget[TotalPlanifie]))",
        "     Avancement physique moyen = AVERAGE(Fait_Activite[Avancement])",
        "     Risques critiques = CALCULATE(COUNTROWS(Fait_Risque), Fait_Risque[Niveau] = \"Critique\")",
        "",
        "ACTUALISATION AUTOMATIQUE (recommandée) : plutôt que ce fichier, connectez Power BI",
        "directement au flux web de la plateforme :",
        "     Obtenir des données > Web > URL :",
        f"     https://<votre-domaine-render>/api/powerbi/{project.id}/dataset?token=<jeton>",
        "Le flux renvoie les mêmes tables au format JSON et se rafraîchit à la demande.",
    ]
    for index, texte in enumerate(notice):
        ws.write(index, 0, texte, fmt["titre"] if index == 0 else fmt["wrap"])
    wb.close()
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# 9. Modèle d'import
# ---------------------------------------------------------------------------
def modele_import_xlsx() -> BytesIO:
    """Classeur type à remplir puis à réimporter dans SEPIA."""
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = _formats(wb)

    ws = wb.add_worksheet("MODE D'EMPLOI")
    ws.set_column(0, 0, 118)
    instructions = [
        "MODÈLE D'IMPORT SEPIA — CADRE LOGIQUE, INDICATEURS, ACTIVITÉS, BUDGET, RISQUES",
        "",
        "Renseignez les onglets ci-après puis importez ce fichier dans SEPIA (menu « Importer »).",
        "Règles à respecter :",
        "  • Ne modifiez pas les intitulés de colonnes (ligne 1) ni les noms des onglets.",
        "  • Colonne « Niveau » : IMPACT, EFFET, PRODUIT ou ACTIVITE (en majuscules, sans accent).",
        "  • Colonne « Code parent » : code du résultat de niveau supérieur (ex. le produit P1.1 a",
        "    pour parent l'effet OS1). Laissez vide pour l'impact.",
        "  • Les dates s'écrivent au format JJ/MM/AAAA ou AAAA-MM-JJ.",
        "  • Les nombres décimaux utilisent le point ou la virgule ; pas de séparateur de milliers.",
        "  • Onglet Indicateurs : « Code résultat » relie l'indicateur au cadre logique.",
        "  • Onglet Budget : « Code activité » relie la ligne budgétaire au chronogramme.",
        "  • Les lignes vides sont ignorées ; un code déjà présent met à jour l'enregistrement existant.",
    ]
    for index, texte in enumerate(instructions):
        ws.write(index, 0, texte, fmt["titre"] if index == 0 else fmt["wrap"])

    feuilles = {
        "Cadre logique": (
            ["Niveau", "Code", "Code parent", "Énoncé du résultat", "Sources de vérification",
             "Hypothèses", "Responsable"],
            [["IMPACT", "OG", "", "Contribuer à l'amélioration durable des conditions de vie…",
              "Enquête nationale EHCVM", "Stabilité politique maintenue", "Coordination"],
             ["EFFET", "OS1", "OG", "Les rendements agricoles des ménages ciblés sont accrus",
              "Enquête de suivi annuelle", "Pluviométrie normale", "Chef de composante 1"],
             ["PRODUIT", "P1.1", "OS1", "Les producteurs sont formés aux itinéraires techniques améliorés",
              "Rapports de formation", "Disponibilité des formateurs", "Responsable formation"],
             ["ACTIVITE", "A1.1.1", "P1.1", "Organiser 20 sessions de formation en champs-écoles",
              "Fiches de présence", "", "Animateur terrain"]],
        ),
        "Indicateurs": (
            ["Code", "Libellé de l'indicateur", "Code résultat", "Niveau", "Type", "Unité",
             "Mode de calcul", "Désagrégation", "Référence", "Date référence", "Cible finale",
             "Date cible", "Sens", "Fréquence", "Source de données", "Méthode de collecte",
             "Responsable", "Indicateur clé (Oui/Non)"],
            [["IOI1", "Incidence de la pauvreté dans la zone du projet", "OG", "IMPACT",
              "Quantitatif", "%", "Population pauvre / population totale × 100", "Sexe;Milieu",
              45.5, "2024-12-31", 38.0, "2028-12-31", "Décroissant", "Annuelle", "EHCVM",
              "Enquête ménages", "INSEED", "Oui"],
             ["IOS1.1", "Rendement moyen du maïs", "OS1", "EFFET", "Quantitatif", "t/ha",
              "Production totale / superficie emblavée", "Sexe;Région", 1.2, "2024-12-31", 2.0,
              "2028-12-31", "Croissant", "Annuelle", "Enquête agricole", "Mesure de parcelles",
              "Expert S&E", "Oui"],
             ["IP1.1", "Nombre de producteurs formés", "P1.1", "PRODUIT", "Quantitatif", "Nombre",
              "Somme des participants uniques", "Sexe;Âge", 0, "2024-12-31", 5000, "2027-12-31",
              "Croissant", "Trimestrielle", "Fiches de présence", "Registre", "Animateur", "Non"]],
        ),
        "Cibles": (
            ["Code indicateur", "Période", "Année", "Début période", "Fin période", "Valeur cible"],
            [["IP1.1", "2025-T1", 2025, "2025-01-01", "2025-03-31", 500],
             ["IP1.1", "2025-T2", 2025, "2025-04-01", "2025-06-30", 1200]],
        ),
        "Réalisations": (
            ["Code indicateur", "Période", "Année", "Date de référence", "Valeur réalisée",
             "Source", "Collecté par", "Statut"],
            [["IP1.1", "2025-T1", 2025, "2025-03-31", 465, "Fiches de présence", "Animateur Nord", "Validé"]],
        ),
        "Activités": (
            ["Code", "Libellé de l'activité", "Code résultat", "Responsable", "Partenaires",
             "Lieu", "Date début", "Date fin", "Avancement (%)", "Statut", "Coût prévu",
             "Année", "Jalon (Oui/Non)", "Livrable"],
            [["A1.1.1", "Organiser 20 sessions de formation en champs-écoles", "P1.1",
              "Animateur terrain", "ICAT", "Région des Savanes", "2025-01-15", "2025-06-30", 40,
              "En cours", 12000000, 2025, "Non", "Rapport de formation"]],
        ),
        "Budget": (
            ["Code", "Libellé de la ligne", "Code activité", "Catégorie", "Unité", "Quantité",
             "Coût unitaire", "Nombre", "T1", "T2", "T3", "T4", "Source de financement", "Année",
             "Engagé", "Décaissé"],
            [["B1.1.1", "Honoraires formateurs", "A1.1.1", "Prestations", "Homme/jour", 20, 50000,
              4, 1000000, 1000000, 1000000, 1000000, "Bailleur principal", 2025, 2000000, 1500000]],
        ),
        "Risques": (
            ["Code", "Catégorie", "Risque identifié", "Cause", "Conséquence", "Probabilité (1-5)",
             "Impact (1-5)", "Mesures d'atténuation", "Plan de contingence", "Responsable",
             "Statut", "Date de revue"],
            [["R1", "Environnemental / Climatique", "Sécheresse prolongée en saison culturale",
              "Variabilité climatique", "Baisse des rendements et non-atteinte de l'effet 1", 4, 5,
              "Promotion de variétés à cycle court et de l'irrigation d'appoint",
              "Réallocation budgétaire vers l'appui d'urgence", "Coordonnateur", "Ouvert", "2025-06-30"]],
        ),
        "Hypothèses": (
            ["Code", "Niveau", "Énoncé de l'hypothèse", "Criticité", "Statut de validation",
             "Méthode de vérification", "Responsable", "Date de revue"],
            [["H1", "EFFET", "La pluviométrie reste dans la normale saisonnière", "Élevée",
              "Non vérifiée", "Bulletins météorologiques trimestriels", "Expert S&E", "2025-06-30"]],
        ),
    }
    for nom, (entetes, exemples) in feuilles.items():
        ws = wb.add_worksheet(nom)
        for col, titre in enumerate(entetes):
            ws.write(0, col, titre, fmt["entete"])
            ws.set_column(col, col, max(14, min(48, len(str(titre)) + 8)))
        for r, ligne in enumerate(exemples, start=1):
            for col, valeur in enumerate(ligne):
                ws.write(r, col, valeur, fmt["cellule"])
        ws.freeze_panes(1, 0)
        ws.set_row(0, 32)
    wb.close()
    buffer.seek(0)
    return buffer
