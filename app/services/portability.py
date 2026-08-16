"""Portabilité des données : export et import complets de projets et de portefeuilles.

Le format JSON produit ici est autonome et réversible : il contient l'intégralité
des données d'un projet (cadre logique, zones, indicateurs, cibles, réalisations
désagrégées, activités, budget, risques, hypothèses, parties prenantes, matrice
RACI, formulaires et questions) et permet de le recréer à l'identique sur une
autre instance de la plateforme.

Les références internes sont réécrites à l'import : chaque identifiant d'origine
est mis en correspondance avec l'identifiant attribué par la base d'accueil, ce
qui rend l'échange indépendant des séquences de clés primaires.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from ..config import APP_NAME, APP_VERSION
from ..models import (Activity, Assumption, Beneficiary, BudgetLine, Evaluation,
                      EvaluationRecommendation, Form, FormQuestion, ImpactStudy, Indicator,
                      IndicatorActual, IndicatorTarget, LogframeElement, Partner, Project,
                      RaciAssignment, Risk, Stakeholder, Zone)

FORMAT_PROJET = "SEPIA-PROJET"
FORMAT_PORTEFEUILLE = "SEPIA-PORTEFEUILLE"
VERSION_FORMAT = "1.0"

# Champs jamais repris à l'import : ils appartiennent à la base d'origine.
CHAMPS_TECHNIQUES = {"id", "created_at", "updated_at", "project_id", "created_by"}


def _serialiser(objet) -> Dict[str, Any]:
    donnees: Dict[str, Any] = {}
    for colonne in sa_inspect(objet.__class__).columns:
        valeur = getattr(objet, colonne.key)
        if isinstance(valeur, datetime):
            valeur = valeur.isoformat(timespec="seconds")
        elif isinstance(valeur, date):
            valeur = valeur.isoformat()
        donnees[colonne.key] = valeur
    return donnees


def _appliquer(objet, donnees: Dict[str, Any], modele) -> None:
    colonnes = {c.key: c for c in sa_inspect(modele).columns}
    for cle, valeur in (donnees or {}).items():
        if cle in CHAMPS_TECHNIQUES or cle not in colonnes:
            continue
        colonne = colonnes[cle]
        try:
            type_python = colonne.type.python_type
        except NotImplementedError:      # colonnes JSON
            setattr(objet, cle, valeur)
            continue
        if valeur is None:
            setattr(objet, cle, None)
            continue
        if type_python is date and isinstance(valeur, str):
            setattr(objet, cle, date.fromisoformat(valeur[:10]))
        elif type_python is datetime and isinstance(valeur, str):
            setattr(objet, cle, datetime.fromisoformat(valeur.replace("Z", "")))
        else:
            setattr(objet, cle, valeur)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def exporter_projet(db: Session, project: Project) -> Dict[str, Any]:
    """Dump complet et autonome d'un projet."""
    elements = db.query(LogframeElement).filter(
        LogframeElement.project_id == project.id).order_by(LogframeElement.id).all()
    indicateurs = db.query(Indicator).filter(
        Indicator.project_id == project.id).order_by(Indicator.id).all()
    identifiants_indicateurs = [i.id for i in indicateurs] or [0]
    activites = db.query(Activity).filter(
        Activity.project_id == project.id).order_by(Activity.id).all()
    formulaires = db.query(Form).filter(Form.project_id == project.id).order_by(Form.id).all()

    contenu = {
        "format": FORMAT_PROJET,
        "version_format": VERSION_FORMAT,
        "application": f"{APP_NAME} {APP_VERSION}",
        "genere_le": datetime.utcnow().isoformat(timespec="seconds"),
        "projet": _serialiser(project),
        "zones": [_serialiser(z) for z in db.query(Zone).filter(
            Zone.project_id == project.id).order_by(Zone.id).all()],
        "beneficiaires": [_serialiser(b) for b in db.query(Beneficiary).filter(
            Beneficiary.project_id == project.id).order_by(Beneficiary.id).all()],
        "partenaires": [_serialiser(p) for p in db.query(Partner).filter(
            Partner.project_id == project.id).order_by(Partner.id).all()],
        "evaluations": [
            dict(_serialiser(e), recommandations=[_serialiser(r) for r in e.recommendations])
            for e in db.query(Evaluation).filter(
                Evaluation.project_id == project.id).order_by(Evaluation.id).all()],
        "etudes_impact": [_serialiser(s) for s in db.query(ImpactStudy).filter(
            ImpactStudy.project_id == project.id).order_by(ImpactStudy.id).all()],
        "cadre_logique": [_serialiser(e) for e in elements],
        "indicateurs": [_serialiser(i) for i in indicateurs],
        "cibles": [_serialiser(t) for t in db.query(IndicatorTarget).filter(
            IndicatorTarget.indicator_id.in_(identifiants_indicateurs)).all()],
        "realisations": [_serialiser(a) for a in db.query(IndicatorActual).filter(
            IndicatorActual.indicator_id.in_(identifiants_indicateurs)).all()],
        "activites": [_serialiser(a) for a in activites],
        "budget": [_serialiser(l) for l in db.query(BudgetLine).filter(
            BudgetLine.project_id == project.id).order_by(BudgetLine.id).all()],
        "risques": [_serialiser(r) for r in db.query(Risk).filter(
            Risk.project_id == project.id).order_by(Risk.id).all()],
        "hypotheses": [_serialiser(h) for h in db.query(Assumption).filter(
            Assumption.project_id == project.id).order_by(Assumption.id).all()],
        "parties_prenantes": [_serialiser(p) for p in db.query(Stakeholder).filter(
            Stakeholder.project_id == project.id).order_by(Stakeholder.id).all()],
        "raci": [_serialiser(a) for a in db.query(RaciAssignment).filter(
            RaciAssignment.project_id == project.id).all()],
        "formulaires": [
            dict(_serialiser(f), questions=[_serialiser(q) for q in sorted(
                f.questions, key=lambda x: x.order_index or 0)])
            for f in formulaires],
    }
    contenu["compteurs"] = {cle: len(valeur) for cle, valeur in contenu.items()
                            if isinstance(valeur, list)}
    return contenu


def exporter_portefeuille(db: Session,
                          identifiants: Optional[List[int]] = None) -> Dict[str, Any]:
    """Dump de plusieurs projets — sauvegarde ou transfert d'un portefeuille entier."""
    requete = db.query(Project).order_by(Project.code)
    if identifiants:
        requete = requete.filter(Project.id.in_(identifiants))
    projets = requete.all()
    return {
        "format": FORMAT_PORTEFEUILLE,
        "version_format": VERSION_FORMAT,
        "application": f"{APP_NAME} {APP_VERSION}",
        "genere_le": datetime.utcnow().isoformat(timespec="seconds"),
        "nb_projets": len(projets),
        "projets": [exporter_projet(db, p) for p in projets],
    }


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------
def _code_disponible(db: Session, code: str) -> str:
    """Retourne un code de projet libre, suffixé si nécessaire."""
    base = (code or "PROJET").strip() or "PROJET"
    if not db.query(Project).filter(Project.code == base).first():
        return base
    for suffixe in range(2, 100):
        candidat = f"{base}-{suffixe}"
        if not db.query(Project).filter(Project.code == candidat).first():
            return candidat
    return f"{base}-{datetime.utcnow().strftime('%H%M%S')}"


def importer_projet(db: Session, contenu: Dict[str, Any],
                    remplacer_existant: bool = False) -> Dict[str, Any]:
    """Recrée un projet complet à partir d'un export JSON.

    Par défaut le projet est créé à côté des projets existants ; son code est
    suffixé s'il est déjà pris. Avec `remplacer_existant`, un projet portant le
    même code est d'abord supprimé, ce qui permet de restaurer une sauvegarde.
    """
    if contenu.get("format") != FORMAT_PROJET:
        raise ValueError("Fichier non reconnu : format « " +
                         str(contenu.get("format")) + " » au lieu de " + FORMAT_PROJET + ".")
    donnees_projet = contenu.get("projet") or {}
    if not donnees_projet.get("title"):
        raise ValueError("Le fichier ne contient pas de projet exploitable.")

    code_origine = donnees_projet.get("code") or "PROJET"
    rapport: Dict[str, Any] = {"code_origine": code_origine, "cree": {}, "avertissements": []}

    if remplacer_existant:
        existant = db.query(Project).filter(Project.code == code_origine).first()
        if existant:
            _supprimer_projet(db, existant)
            rapport["avertissements"].append(
                f"Le projet « {code_origine} » présent dans la base a été remplacé.")

    projet = Project()
    _appliquer(projet, donnees_projet, Project)
    projet.code = _code_disponible(db, code_origine)
    if projet.code != code_origine:
        rapport["avertissements"].append(
            f"Le code « {code_origine} » étant déjà utilisé, le projet importé porte le code "
            f"« {projet.code} ».")
    db.add(projet)
    db.flush()
    rapport["projet_id"] = projet.id
    rapport["code_importe"] = projet.code

    def creer(modele, lignes, correspondance_cle=None, remaps=None):
        """Recrée une collection en réécrivant les références internes."""
        correspondance: Dict[Any, int] = {}
        compteur = 0
        for ligne in lignes or []:
            objet = modele(project_id=projet.id) if hasattr(modele, "project_id") else modele()
            _appliquer(objet, ligne, modele)
            for champ, table in (remaps or {}).items():
                ancienne = ligne.get(champ)
                setattr(objet, champ, table.get(ancienne) if ancienne is not None else None)
            if hasattr(objet, "project_id"):
                objet.project_id = projet.id
            db.add(objet)
            db.flush()
            if correspondance_cle:
                correspondance[ligne.get(correspondance_cle)] = objet.id
            compteur += 1
        return correspondance, compteur

    # Zones puis leur hiérarchie interne
    zones, nb = creer(Zone, contenu.get("zones"), "id")
    for ligne in contenu.get("zones") or []:
        if ligne.get("parent_id") and ligne["id"] in zones:
            objet = db.get(Zone, zones[ligne["id"]])
            objet.parent_id = zones.get(ligne["parent_id"])
    rapport["cree"]["zones"] = nb

    beneficiaires, nb = creer(Beneficiary, contenu.get("beneficiaires"), "id",
                              {"zone_id": zones})
    rapport["cree"]["beneficiaires"] = nb
    _, nb = creer(Partner, contenu.get("partenaires"), None)
    rapport["cree"]["partenaires"] = nb

    elements, nb = creer(LogframeElement, contenu.get("cadre_logique"), "id")
    for ligne in contenu.get("cadre_logique") or []:
        if ligne.get("parent_id") and ligne["id"] in elements:
            objet = db.get(LogframeElement, elements[ligne["id"]])
            objet.parent_id = elements.get(ligne["parent_id"])
    rapport["cree"]["resultats"] = nb

    activites, nb = creer(Activity, contenu.get("activites"), "id",
                          {"element_id": elements})
    rapport["cree"]["activites"] = nb

    indicateurs, nb = creer(Indicator, contenu.get("indicateurs"), "id",
                            {"element_id": elements, "beneficiary_id": beneficiaires})
    rapport["cree"]["indicateurs"] = nb

    _, nb = creer(IndicatorTarget, contenu.get("cibles"), None, {"indicator_id": indicateurs})
    rapport["cree"]["cibles"] = nb
    _, nb = creer(IndicatorActual, contenu.get("realisations"), None,
                  {"indicator_id": indicateurs, "zone_id": zones, "activity_id": activites})
    rapport["cree"]["realisations"] = nb

    _, nb = creer(BudgetLine, contenu.get("budget"), None, {"activity_id": activites})
    rapport["cree"]["lignes_budgetaires"] = nb
    _, nb = creer(Risk, contenu.get("risques"), None, {"element_id": elements})
    rapport["cree"]["risques"] = nb
    _, nb = creer(Assumption, contenu.get("hypotheses"), None, {"element_id": elements})
    rapport["cree"]["hypotheses"] = nb

    parties, nb = creer(Stakeholder, contenu.get("parties_prenantes"), "id")
    rapport["cree"]["parties_prenantes"] = nb
    _, nb = creer(RaciAssignment, contenu.get("raci"), None,
                  {"activity_id": activites, "stakeholder_id": parties})
    rapport["cree"]["affectations_raci"] = nb

    evaluations: Dict[Any, int] = {}
    nb_evaluations, nb_recommandations = 0, 0
    for ligne in contenu.get("evaluations") or []:
        evaluation = Evaluation(project_id=projet.id)
        _appliquer(evaluation, ligne, Evaluation)
        evaluation.project_id = projet.id
        db.add(evaluation)
        db.flush()
        evaluations[ligne.get("id")] = evaluation.id
        nb_evaluations += 1
        for recommandation in ligne.get("recommandations") or []:
            objet = EvaluationRecommendation(evaluation_id=evaluation.id)
            _appliquer(objet, recommandation, EvaluationRecommendation)
            objet.evaluation_id = evaluation.id
            db.add(objet)
            nb_recommandations += 1
    rapport["cree"]["evaluations"] = nb_evaluations
    rapport["cree"]["recommandations"] = nb_recommandations
    _, nb = creer(ImpactStudy, contenu.get("etudes_impact"), None,
                  {"evaluation_id": evaluations})
    rapport["cree"]["etudes_impact"] = nb

    nb_formulaires, nb_questions = 0, 0
    for ligne in contenu.get("formulaires") or []:
        formulaire = Form(project_id=projet.id)
        _appliquer(formulaire, ligne, Form)
        formulaire.project_id = projet.id
        db.add(formulaire)
        db.flush()
        nb_formulaires += 1
        for question in ligne.get("questions") or []:
            objet = FormQuestion(form_id=formulaire.id)
            _appliquer(objet, question, FormQuestion)
            objet.form_id = formulaire.id
            db.add(objet)
            nb_questions += 1
    rapport["cree"]["formulaires"] = nb_formulaires
    rapport["cree"]["questions"] = nb_questions

    db.commit()
    # Les affectations RACI dont l'activité ou l'acteur n'a pas été retrouvé sont
    # écartées : elles n'auraient plus de sens dans la base d'accueil.
    orphelines = db.query(RaciAssignment).filter(
        RaciAssignment.project_id == projet.id,
        (RaciAssignment.activity_id.is_(None)) |
        (RaciAssignment.stakeholder_id.is_(None))).all()
    if orphelines:
        for affectation in orphelines:
            db.delete(affectation)
        db.commit()
        rapport["cree"]["affectations_raci"] -= len(orphelines)
        rapport["avertissements"].append(
            f"{len(orphelines)} affectation(s) RACI sans activité ou sans acteur correspondant "
            f"ont été écartées.")
    return rapport


def importer_portefeuille(db: Session, contenu: Dict[str, Any],
                          remplacer_existant: bool = False) -> Dict[str, Any]:
    """Importe un portefeuille complet, ou un projet unique si le format le désigne."""
    if contenu.get("format") == FORMAT_PROJET:
        return {"format": FORMAT_PROJET, "projets": [
            importer_projet(db, contenu, remplacer_existant)]}
    if contenu.get("format") != FORMAT_PORTEFEUILLE:
        raise ValueError("Fichier non reconnu : le format attendu est « " + FORMAT_PROJET +
                         " » ou « " + FORMAT_PORTEFEUILLE + " ».")
    rapports = []
    for projet in contenu.get("projets") or []:
        try:
            rapports.append(importer_projet(db, projet, remplacer_existant))
        except Exception as exc:
            db.rollback()
            rapports.append({"code_origine": (projet.get("projet") or {}).get("code"),
                             "erreur": f"{type(exc).__name__} — {exc}"})
    return {"format": FORMAT_PORTEFEUILLE, "projets": rapports,
            "importes": len([r for r in rapports if "erreur" not in r]),
            "en_echec": len([r for r in rapports if "erreur" in r])}


def _supprimer_projet(db: Session, projet: Project) -> None:
    """Suppression ordonnée de toutes les dépendances d'un projet."""
    identifiants = [i.id for i in db.query(Indicator.id).filter(
        Indicator.project_id == projet.id).all()]
    if identifiants:
        db.query(IndicatorActual).filter(
            IndicatorActual.indicator_id.in_(identifiants)).delete(synchronize_session=False)
        db.query(IndicatorTarget).filter(
            IndicatorTarget.indicator_id.in_(identifiants)).delete(synchronize_session=False)
    formulaires = [f.id for f in db.query(Form.id).filter(Form.project_id == projet.id).all()]
    if formulaires:
        db.query(FormQuestion).filter(
            FormQuestion.form_id.in_(formulaires)).delete(synchronize_session=False)
    db.query(EvaluationRecommendation).filter(
        EvaluationRecommendation.evaluation_id.in_(
            db.query(Evaluation.id).filter(Evaluation.project_id == projet.id))).delete(
        synchronize_session=False)
    for modele in (RaciAssignment, Stakeholder, BudgetLine, Activity, ImpactStudy, Evaluation,
                   Indicator, Beneficiary, Partner, Assumption, Risk, Form, Zone,
                   LogframeElement):
        db.query(modele).filter(modele.project_id == projet.id).delete(synchronize_session=False)
    db.delete(projet)
    db.flush()
