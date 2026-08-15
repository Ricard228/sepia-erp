"""Production et téléchargement des livrables Word, Excel et XLSForm."""
import re
from datetime import date
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..crud import ensure_project
from ..database import get_db
from ..models import Form, Project, User
from ..security import current_user
from ..services import excel_export, word_export, xlsform

router = APIRouter(prefix="/api/exports", tags=["Exports"])

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _nom_fichier(projet: Project, libelle: str, extension: str) -> str:
    base = re.sub(r"[^0-9A-Za-z_-]+", "_", f"{projet.code}_{libelle}").strip("_")
    return f"{base}_{date.today().isoformat()}.{extension}"


def _reponse(buffer, nom: str, mime: str) -> StreamingResponse:
    return StreamingResponse(
        buffer, media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{nom}"',
                 "Access-Control-Expose-Headers": "Content-Disposition"})


# --- Catalogue -------------------------------------------------------------
LIVRABLES = [
    {"cle": "cadre-logique-excel", "libelle": "Cadre logique", "format": "Excel",
     "description": "Matrice complète avec IOV, sources de vérification et hypothèses."},
    {"cle": "cadre-logique-word", "libelle": "Cadre logique", "format": "Word",
     "description": "Matrice mise en page en paysage, prête à insérer dans un document projet."},
    {"cle": "cadre-rendement-excel", "libelle": "Cadre de rendement", "format": "Excel",
     "description": "Performance Measurement Framework avec taux de réalisation calculés."},
    {"cle": "cadre-rendement-word", "libelle": "Cadre de rendement", "format": "Word",
     "description": "Cadre de mesure du rendement pour rapport officiel."},
    {"cle": "iptt-excel", "libelle": "Cadre de suivi des indicateurs (IPTT)", "format": "Excel",
     "description": "Cibles et réalisations par période, avec taux et mise en forme conditionnelle."},
    {"cle": "chronogramme-excel", "libelle": "Chronogramme (Gantt)", "format": "Excel",
     "description": "Diagramme de Gantt mensuel coloré selon l'état d'avancement."},
    {"cle": "ptba-excel", "libelle": "Plan de travail et budget annuel", "format": "Excel",
     "description": "PTBA détaillé, ventilation trimestrielle et synthèse graphique."},
    {"cle": "risques-excel", "libelle": "Registre des risques", "format": "Excel",
     "description": "Registre coté et matrice de criticité 5×5."},
    {"cle": "risques-word", "libelle": "Plan de gestion des risques", "format": "Word",
     "description": "Registre, matrice et plans de contingence rédigés."},
    {"cle": "fiches-indicateurs-word", "libelle": "Fiches métadonnées des indicateurs",
     "format": "Word", "description": "Une fiche documentée par indicateur, avec séries périodiques."},
    {"cle": "plan-se-word", "libelle": "Plan et manuel de suivi-évaluation", "format": "Word",
     "description": "Document maître en 15 chapitres, généré à partir des données du projet."},
    {"cle": "rapport-performance-word", "libelle": "Rapport de performance", "format": "Word",
     "description": "Rapport périodique : résumé exécutif, indicateurs, alertes, mesures correctrices."},
    {"cle": "tableau-de-bord-excel", "libelle": "Tableau de bord automatisé", "format": "Excel",
     "description": "KPI, graphiques, alertes et détail des indicateurs."},
    {"cle": "powerbi-dataset", "libelle": "Jeu de données Power BI", "format": "Excel",
     "description": "Modèle en étoile (dimensions et faits) avec notice de branchement."},
    {"cle": "modele-import", "libelle": "Modèle d'import", "format": "Excel",
     "description": "Classeur type à remplir pour charger un projet complet."},
    {"cle": "dossier-complet", "libelle": "Dossier complet de S&E", "format": "ZIP",
     "description": "Archive regroupant l'ensemble des livrables du projet."},
]


@router.get("/catalogue")
def catalogue(user: User = Depends(current_user)):
    return LIVRABLES


# --- Livrables par projet --------------------------------------------------
def _produire(cle: str, db: Session, projet: Project, annee: Optional[int] = None,
              periode: str = ""):
    """Retourne (buffer, nom_de_fichier, mime) pour un livrable donné."""
    if cle == "cadre-logique-excel":
        return excel_export.cadre_logique_xlsx(db, projet), \
            _nom_fichier(projet, "Cadre_logique", "xlsx"), MIME_XLSX
    if cle == "cadre-logique-word":
        return word_export.cadre_logique_docx(db, projet), \
            _nom_fichier(projet, "Cadre_logique", "docx"), MIME_DOCX
    if cle == "cadre-rendement-excel":
        return excel_export.cadre_rendement_xlsx(db, projet), \
            _nom_fichier(projet, "Cadre_de_rendement", "xlsx"), MIME_XLSX
    if cle == "cadre-rendement-word":
        return word_export.cadre_rendement_docx(db, projet), \
            _nom_fichier(projet, "Cadre_de_rendement", "docx"), MIME_DOCX
    if cle == "iptt-excel":
        return excel_export.iptt_xlsx(db, projet), \
            _nom_fichier(projet, "Cadre_suivi_indicateurs_IPTT", "xlsx"), MIME_XLSX
    if cle == "chronogramme-excel":
        return excel_export.chronogramme_xlsx(db, projet), \
            _nom_fichier(projet, "Chronogramme", "xlsx"), MIME_XLSX
    if cle == "ptba-excel":
        return excel_export.ptba_xlsx(db, projet, annee), \
            _nom_fichier(projet, f"PTBA_{annee or 'pluriannuel'}", "xlsx"), MIME_XLSX
    if cle == "risques-excel":
        return excel_export.risques_xlsx(db, projet), \
            _nom_fichier(projet, "Registre_des_risques", "xlsx"), MIME_XLSX
    if cle == "risques-word":
        return word_export.risques_docx(db, projet), \
            _nom_fichier(projet, "Plan_gestion_des_risques", "docx"), MIME_DOCX
    if cle == "fiches-indicateurs-word":
        return word_export.fiches_indicateurs_docx(db, projet), \
            _nom_fichier(projet, "Fiches_indicateurs", "docx"), MIME_DOCX
    if cle == "plan-se-word":
        return word_export.plan_suivi_evaluation_docx(db, projet), \
            _nom_fichier(projet, "Plan_et_manuel_de_suivi_evaluation", "docx"), MIME_DOCX
    if cle == "rapport-performance-word":
        return word_export.rapport_performance_docx(db, projet, periode), \
            _nom_fichier(projet, "Rapport_de_performance", "docx"), MIME_DOCX
    if cle == "tableau-de-bord-excel":
        return excel_export.tableau_de_bord_xlsx(db, projet), \
            _nom_fichier(projet, "Tableau_de_bord", "xlsx"), MIME_XLSX
    if cle == "powerbi-dataset":
        return excel_export.powerbi_dataset_xlsx(db, projet), \
            _nom_fichier(projet, "Dataset_PowerBI", "xlsx"), MIME_XLSX
    raise HTTPException(status_code=404, detail=f"Livrable « {cle} » inconnu.")


@router.get("/modele-import")
def modele_import(user: User = Depends(current_user)):
    return _reponse(excel_export.modele_import_xlsx(),
                    f"SEPIA_Modele_import_{date.today().isoformat()}.xlsx", MIME_XLSX)


@router.get("/{project_id}/{cle}")
def telecharger(project_id: int, cle: str, annee: Optional[int] = Query(None),
                periode: str = Query(""), db: Session = Depends(get_db),
                user: User = Depends(current_user)):
    projet = ensure_project(db, project_id)
    if cle == "dossier-complet":
        return _dossier_complet(db, projet)
    buffer, nom, mime = _produire(cle, db, projet, annee, periode)
    return _reponse(buffer, nom, mime)


def _dossier_complet(db: Session, projet: Project) -> StreamingResponse:
    """Archive ZIP regroupant tous les livrables du projet."""
    archive = BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_fichier:
        for livrable in LIVRABLES:
            cle = livrable["cle"]
            if cle in ("dossier-complet", "modele-import"):
                continue
            try:
                buffer, nom, _ = _produire(cle, db, projet)
                zip_fichier.writestr(f"{livrable['format']}/{nom}", buffer.getvalue())
            except Exception as exc:  # un livrable en échec ne bloque pas l'archive
                zip_fichier.writestr(f"ERREURS/{cle}.txt",
                                     f"Livrable non généré : {type(exc).__name__} — {exc}")
        for form in db.query(Form).filter(Form.project_id == projet.id).all():
            try:
                zip_fichier.writestr(
                    f"Collecte/Questionnaire_{re.sub(r'[^0-9A-Za-z]+', '_', form.name)[:50]}.docx",
                    word_export.questionnaire_docx(db, form, projet).getvalue())
                zip_fichier.writestr(
                    f"Collecte/XLSForm_{re.sub(r'[^0-9A-Za-z]+', '_', form.name)[:50]}.xlsx",
                    xlsform.xlsform_xlsx(form, projet).getvalue())
            except Exception as exc:
                zip_fichier.writestr(f"ERREURS/form_{form.id}.txt", str(exc))
        zip_fichier.writestr("LISEZ-MOI.txt", _notice_dossier(projet))
    archive.seek(0)
    return _reponse(archive, _nom_fichier(projet, "Dossier_complet_SE", "zip"), "application/zip")


def _notice_dossier(projet: Project) -> str:
    return f"""DOSSIER DE SUIVI-ÉVALUATION — {projet.code} : {projet.title}
Généré le {date.today().strftime('%d/%m/%Y')} par la plateforme SEPIA.

CONTENU DE L'ARCHIVE
  Excel/   Cadre logique, cadre de rendement, IPTT, chronogramme, PTBA, registre des
           risques, tableau de bord automatisé et jeu de données Power BI.
  Word/    Cadre logique, cadre de rendement, plan de gestion des risques, fiches
           métadonnées des indicateurs, plan et manuel de suivi-évaluation, rapport
           de performance.
  Collecte/ Questionnaires au format Word (administration papier) et XLSForm
           (déploiement KoboToolbox / ODK Collect).

UTILISATION
  * Les fichiers Excel sont directement exploitables et imprimables (format paysage A3).
  * Le classeur « Dataset_PowerBI » contient un modèle en étoile et une notice de
    branchement pour Power BI Desktop.
  * Le manuel de suivi-évaluation est un document Word modifiable : il peut être
    complété puis validé par le comité de pilotage.
  * Les XLSForm se téléversent tels quels dans KoboToolbox.

Toutes les données proviennent de la base du projet au moment de la génération.
"""


# --- Livrables liés aux formulaires ---------------------------------------
@router.get("/forms/{form_id}/word")
def questionnaire_word(form_id: int, db: Session = Depends(get_db),
                       user: User = Depends(current_user)):
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire introuvable.")
    projet = ensure_project(db, form.project_id)
    nom = re.sub(r"[^0-9A-Za-z_-]+", "_", f"{projet.code}_{form.name}")[:60]
    return _reponse(word_export.questionnaire_docx(db, form, projet), f"{nom}.docx", MIME_DOCX)


@router.get("/forms/{form_id}/xlsform")
def questionnaire_xlsform(form_id: int, db: Session = Depends(get_db),
                          user: User = Depends(current_user)):
    form = db.get(Form, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Formulaire introuvable.")
    projet = ensure_project(db, form.project_id)
    nom = re.sub(r"[^0-9A-Za-z_-]+", "_", f"XLSForm_{projet.code}_{form.name}")[:60]
    return _reponse(xlsform.xlsform_xlsx(form, projet), f"{nom}.xlsx", MIME_XLSX)


@router.get("/indicators/{indicator_id}/fiche")
def fiche_indicateur(indicator_id: int, db: Session = Depends(get_db),
                     user: User = Depends(current_user)):
    from ..models import Indicator
    indicateur = db.get(Indicator, indicator_id)
    if not indicateur:
        raise HTTPException(status_code=404, detail="Indicateur introuvable.")
    projet = ensure_project(db, indicateur.project_id)
    return _reponse(word_export.fiches_indicateurs_docx(db, projet, indicator_id),
                    _nom_fichier(projet, f"Fiche_{indicateur.code or indicator_id}", "docx"),
                    MIME_DOCX)
