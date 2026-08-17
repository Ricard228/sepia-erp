"""Vérifie le chargement des projets d'exemple sur une base déjà en service.

Reproduit la situation d'une instance mise en route avant l'ajout d'un exemple :
la base contient déjà un projet, et l'exemple manquant doit néanmoins être chargé
au redémarrage suivant, sans que les projets existants soient touchés.

Usage :  python scripts/verifier_exemples.py

Travaille sur une base temporaire. Sortie 0 si tous les contrôles passent.
"""
import importlib
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

os.environ["SEPIA_DATA_DIR"] = tempfile.mkdtemp(prefix="sepia-exemples-")
os.environ["SEPIA_ENV"] = "developpement"
os.environ["SEPIA_SECRET_KEY"] = "cle-de-test"
os.environ["SEPIA_ADMIN_PASSWORD"] = "Antilope-Cuivre-Sillon-6"

ok, ko = [], []


def verifier(libelle, condition, detail=""):
    (ok if condition else ko).append(libelle)
    print(f"  {'OK   ' if condition else 'ECHEC'} {libelle}" + (f" — {detail}" if detail else ""))


def amorcer(avec_demo=True):
    """Rejoue un démarrage complet de l'application."""
    for module in [m for m in list(sys.modules) if m == "app" or m.startswith("app.")]:
        del sys.modules[module]
    base = importlib.import_module("app.database")
    importlib.import_module("app.models")
    base.Base.metadata.create_all(bind=base.engine)
    db = base.SessionLocal()
    try:
        importlib.import_module("app.seed").initialiser(db, avec_demo=avec_demo)
    finally:
        db.close()


def codes():
    import importlib as i
    base = i.import_module("app.database")
    Project = i.import_module("app.models").Project
    db = base.SessionLocal()
    try:
        return sorted(p.code for p in db.query(Project).all())
    finally:
        db.close()


print("== PREMIER DÉMARRAGE ==")
amorcer()
verifier("les deux exemples sont chargés", codes() == ["PADRA-2025", "PASSE-2026"], str(codes()))

print("\n== REDÉMARRAGE ORDINAIRE ==")
amorcer()
verifier("aucun doublon", codes() == ["PADRA-2025", "PASSE-2026"], str(codes()))

print("\n== INSTANCE ANCIENNE : un exemple manque ==")
import importlib as _i                                                     # noqa: E402
_base = _i.import_module("app.database")
_m = _i.import_module("app.models")
_supprimer = _i.import_module("app.services.portability")._supprimer_projet
_db = _base.SessionLocal()
_supprimer(_db, _db.query(_m.Project).filter(_m.Project.code == "PASSE-2026").first())
_db.commit()
_db.close()
verifier("PASSE-2026 retiré, PADRA-2025 subsiste", codes() == ["PADRA-2025"], str(codes()))

print("\n== REDÉMARRAGE : l'exemple manquant est chargé ==")
amorcer()
verifier("PASSE-2026 rechargé sur une base non vide",
         codes() == ["PADRA-2025", "PASSE-2026"], str(codes()))

_db = _base.SessionLocal()
_passe = _db.query(_m.Project).filter(_m.Project.code == "PASSE-2026").first()
compteurs = {
    "zones": _db.query(_m.Zone).filter(_m.Zone.project_id == _passe.id).count(),
    "indicateurs": _db.query(_m.Indicator).filter(_m.Indicator.project_id == _passe.id).count(),
    "beneficiaires": _db.query(_m.Beneficiary).filter(
        _m.Beneficiary.project_id == _passe.id).count(),
    "partenaires": _db.query(_m.Partner).filter(_m.Partner.project_id == _passe.id).count(),
    "evaluations": _db.query(_m.Evaluation).filter(_m.Evaluation.project_id == _passe.id).count(),
    "etudes": _db.query(_m.ImpactStudy).filter(_m.ImpactStudy.project_id == _passe.id).count(),
}
_db.close()
verifier("rechargé intégralement",
         compteurs == {"zones": 8, "indicateurs": 17, "beneficiaires": 5,
                       "partenaires": 6, "evaluations": 2, "etudes": 2}, str(compteurs))

print("\n== UN EXEMPLE MODIFIÉ N'EST PAS ÉCRASÉ ==")
_db = _base.SessionLocal()
_padra = _db.query(_m.Project).filter(_m.Project.code == "PADRA-2025").first()
_padra.title = "Titre remanié par l'utilisateur"
_db.commit()
_db.close()
amorcer()
_db = _base.SessionLocal()
_padra = _db.query(_m.Project).filter(_m.Project.code == "PADRA-2025").first()
_intact = _padra.title == "Titre remanié par l'utilisateur"
_nb = _db.query(_m.Project).filter(_m.Project.code == "PADRA-2025").count()
_db.close()
verifier("le projet repris conserve ses modifications", _intact)
verifier("aucun second exemplaire créé", _nb == 1, f"{_nb} exemplaire(s)")

print("\n== SEPIA_SEED_DEMO=0 ==")
_db = _base.SessionLocal()
for _projet in _db.query(_m.Project).all():
    _supprimer(_db, _projet)
_db.commit()
_db.close()
amorcer(avec_demo=False)
verifier("aucun exemple chargé quand l'option est désactivée", codes() == [], str(codes()))

print(f"\n{len(ok)} contrôles réussis, {len(ko)} en échec.")
sys.exit(1 if ko else 0)
