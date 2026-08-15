"""Génération de fichiers XLSForm compatibles KoboToolbox, ODK Collect et Ona,
à partir des questionnaires paramétrés dans SEPIA."""
import re
from datetime import date
from io import BytesIO
from typing import Any, Dict, List

import xlsxwriter

from ..models import Form, Project

# Colonnes standard de la feuille « survey » d'un XLSForm
COLONNES_SURVEY = ["type", "name", "label", "hint", "required", "required_message", "relevant",
                   "constraint", "constraint_message", "calculation", "appearance", "default",
                   "read_only"]
COLONNES_CHOICES = ["list_name", "name", "label"]
COLONNES_SETTINGS = ["form_title", "form_id", "version", "default_language", "instance_name",
                     "style", "allow_choice_duplicates"]

TYPES_XLSFORM = {
    "text": "text", "integer": "integer", "decimal": "decimal", "date": "date", "time": "time",
    "geopoint": "geopoint", "note": "note", "calculate": "calculate", "image": "image",
    "barcode": "barcode",
}


def _nom_technique(valeur: str, secours: str = "q") -> str:
    """Normalise un nom de variable conforme aux contraintes XLSForm/ODK."""
    nettoye = re.sub(r"[^0-9a-zA-Z_]", "_", (valeur or "").strip().lower())
    nettoye = re.sub(r"_+", "_", nettoye).strip("_")
    if not nettoye or nettoye[0].isdigit():
        nettoye = f"{secours}_{nettoye}" if nettoye else secours
    return nettoye[:60]


def construire_lignes(form: Form) -> Dict[str, List[List[Any]]]:
    """Construit les trois feuilles du XLSForm à partir du formulaire SEPIA."""
    survey: List[List[Any]] = []
    choices: List[List[Any]] = []
    listes_creees: Dict[str, str] = {}
    section_courante = None
    noms_utilises: set = set()

    # Bloc d'identification standard, systématiquement ajouté en tête
    survey.append(["start", "start", None, None, None, None, None, None, None, None, None, None, None])
    survey.append(["end", "end", None, None, None, None, None, None, None, None, None, None, None])
    survey.append(["today", "today", None, None, None, None, None, None, None, None, None, None, None])
    survey.append(["deviceid", "deviceid", None, None, None, None, None, None, None, None, None, None, None])

    survey.append(["begin group", "identification", "A. Identification de la collecte", None, None,
                   None, None, None, None, None, "field-list", None, None])
    survey.append(["date", "date_collecte", "Date de la collecte", None, "yes", None, None, None,
                   None, None, None, "today()", None])
    survey.append(["text", "enqueteur", "Nom de l'enquêteur", None, "yes", None, None, None, None,
                   None, None, None, None])
    survey.append(["text", "localite", "Localité / village", None, "yes", None, None, None, None,
                   None, None, None, None])
    survey.append(["geopoint", "gps", "Coordonnées GPS du point de collecte", None, None, None,
                   None, None, None, None, None, None, None])
    survey.append(["end group", "identification", None, None, None, None, None, None, None, None,
                   None, None, None])

    for question in form.questions:
        # Regroupement par section
        if question.section and question.section != section_courante:
            if section_courante is not None:
                survey.append(["end group", _nom_technique(section_courante, "grp"), None, None,
                               None, None, None, None, None, None, None, None, None])
            section_courante = question.section
            survey.append(["begin group", _nom_technique(section_courante, "grp"), section_courante,
                           None, None, None, None, None, None, None, None, None, None])

        nom = _nom_technique(question.name or question.label, f"q{question.order_index or 0}")
        while nom in noms_utilises:
            nom = f"{nom}_{len(noms_utilises)}"
        noms_utilises.add(nom)

        type_question = question.question_type or "text"
        if type_question in ("select_one", "select_multiple"):
            liste = _nom_technique(f"liste_{nom}", "liste")
            signature = str(question.choices)
            if signature in listes_creees:
                liste = listes_creees[signature]
            else:
                listes_creees[signature] = liste
                for choix in question.choices or []:
                    if isinstance(choix, dict):
                        code = str(choix.get("name", "")) or _nom_technique(str(choix.get("label", "")))
                        libelle = choix.get("label", code)
                    else:
                        code, libelle = _nom_technique(str(choix)), str(choix)
                    choices.append([liste, code, libelle])
            type_xls = f"{type_question} {liste}"
        else:
            type_xls = TYPES_XLSFORM.get(type_question, "text")

        survey.append([
            type_xls, nom, question.label,
            question.hint or None,
            "yes" if question.required else None,
            "Cette question est obligatoire." if question.required else None,
            question.relevant or None,
            question.constraint or None,
            question.constraint_message or None,
            question.calculation or None,
            question.appearance or None,
            question.default_value or None,
            None,
        ])

    if section_courante is not None:
        survey.append(["end group", _nom_technique(section_courante, "grp"), None, None, None,
                       None, None, None, None, None, None, None, None])

    settings = [[
        form.name,
        _nom_technique(form.code or form.name, "form"),
        (form.version or "1.0").replace(".", "") + date.today().strftime("%y%m%d"),
        form.language or "fr",
        f"concat('{_nom_technique(form.code or 'FORM')}-', ${{date_collecte}})",
        "pages",
        "yes",
    ]]
    return {"survey": survey, "choices": choices, "settings": settings}


def xlsform_xlsx(form: Form, project: Project) -> BytesIO:
    """Produit le classeur XLSForm téléversable dans KoboToolbox."""
    donnees = construire_lignes(form)
    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    entete = wb.add_format({"bold": True, "bg_color": "#1F4E79", "font_color": "white", "border": 1})
    cellule = wb.add_format({"border": 1, "valign": "top", "text_wrap": True})
    groupe = wb.add_format({"border": 1, "bg_color": "#DCE6F1", "bold": True})

    def ecrire(nom_feuille: str, colonnes: List[str], lignes: List[List[Any]]):
        ws = wb.add_worksheet(nom_feuille)
        for col, titre in enumerate(colonnes):
            ws.write(0, col, titre, entete)
            ws.set_column(col, col, 24 if titre == "label" else 16)
        for r, valeurs in enumerate(lignes, start=1):
            style = groupe if str(valeurs[0]).startswith(("begin", "end")) else cellule
            for col in range(len(colonnes)):
                valeur = valeurs[col] if col < len(valeurs) else None
                if valeur is None:
                    ws.write_blank(r, col, None, style)
                else:
                    ws.write(r, col, valeur, style)
        ws.freeze_panes(1, 0)

    ecrire("survey", COLONNES_SURVEY, donnees["survey"])
    ecrire("choices", COLONNES_CHOICES, donnees["choices"])
    ecrire("settings", COLONNES_SETTINGS, donnees["settings"])

    ws = wb.add_worksheet("LISEZ-MOI")
    ws.set_column(0, 0, 110)
    wrap = wb.add_format({"text_wrap": True, "valign": "top"})
    titre = wb.add_format({"bold": True, "font_size": 14, "font_color": "#1F4E79"})
    notice = [
        f"XLSFORM — {form.name}",
        "",
        f"Projet : {project.code} — {project.title}",
        f"Instrument : {form.form_type or 'Questionnaire'} — version {form.version or '1.0'}",
        f"Indicateurs renseignés : {', '.join(form.linked_indicators or []) or 'non précisé'}",
        "",
        "DÉPLOIEMENT SUR KOBOTOOLBOX",
        "1. Se connecter à https://kf.kobotoolbox.org (ou à votre serveur Kobo).",
        "2. Nouveau projet > « Téléverser un fichier XLSForm » > sélectionner ce classeur.",
        "3. Vérifier l'aperçu du formulaire, puis « Déployer ».",
        "4. Les enquêteurs collectent avec l'application KoboCollect ou ODK Collect (mode hors ligne).",
        "",
        "DÉPLOIEMENT SUR ODK CENTRAL",
        "1. Convertir si nécessaire le XLSForm en XForm (pyxform ou l'outil en ligne).",
        "2. Créer un projet dans ODK Central puis téléverser le formulaire.",
        "",
        "RÉINJECTION DES DONNÉES DANS SEPIA",
        "Exporter les données collectées au format XLSX/CSV depuis Kobo, puis les importer dans",
        "SEPIA via le menu « Collecte > Importer des réponses ». Les valeurs des questions reliées",
        "à un indicateur alimentent automatiquement les réalisations correspondantes.",
        "",
        "CONVENTIONS APPLIQUÉES",
        "• Les noms de variables sont normalisés (minuscules, sans accent ni espace).",
        "• Les métadonnées start/end/today/deviceid sont ajoutées automatiquement.",
        "• Un groupe « Identification de la collecte » précède les sections métier.",
        "• Les contraintes et logiques de saut paramétrées dans SEPIA sont reportées telles quelles.",
    ]
    for index, texte in enumerate(notice):
        ws.write(index, 0, texte, titre if index == 0 else wrap)
    wb.close()
    buffer.seek(0)
    return buffer
