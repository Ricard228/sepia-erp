"""Vérifie la reprise de main sur le compte d'administration de SEPIA.

Simule la perte du compte — mot de passe inutilisable, verrouillage, compte
désactivé, rôle rétrogradé — puis contrôle que SEPIA_ADMIN_RESET le rétablit,
qu'un démarrage ordinaire ne touche à rien, et qu'aucun point d'entrée réseau
de réinitialisation n'existe.

Usage :  python scripts/verifier_reprise_admin.py

Travaille sur une base temporaire. Sortie 0 si tous les contrôles passent.
"""
import importlib
import os
import pathlib
import sys
import tempfile

RACINE = str(pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, RACINE)

BASE = tempfile.mkdtemp(prefix="sepia-reset-")
os.environ["SEPIA_DATA_DIR"] = BASE
os.environ["SEPIA_ENV"] = "developpement"
os.environ["SEPIA_SECRET_KEY"] = "cle-de-test"
os.environ["SEPIA_SEED_DEMO"] = "0"
os.environ["SEPIA_ADMIN_PASSWORD"] = ""

ok, ko = [], []


def verifier(libelle, condition, detail=""):
    (ok if condition else ko).append(libelle)
    print(f"  {'OK   ' if condition else 'ECHEC'} {libelle}" + (f" — {detail}" if detail else ""))


def demarrer():
    """Recharge la configuration et relance l'application, comme un redémarrage."""
    for module in [m for m in list(sys.modules) if m == "app" or m.startswith("app.")]:
        del sys.modules[module]
    from fastapi.testclient import TestClient
    app = importlib.import_module("app.main").app
    client = TestClient(app)
    client.__enter__()
    return client


def mot_de_passe_journalise(capture):
    for ligne in capture.splitlines():
        if "Mot de passe :" in ligne:
            return ligne.split("Mot de passe :", 1)[1].strip()
    return None


import io                                                              # noqa: E402
import logging                                                         # noqa: E402

tampon = io.StringIO()
logging.basicConfig(level=logging.WARNING, stream=tampon, force=True)

print("== PREMIER DÉMARRAGE ==")
c = demarrer()
initial = mot_de_passe_journalise(tampon.getvalue())
verifier("mot de passe engendré et journalisé", bool(initial), initial)
r = c.post("/api/auth/login", data={"username": "admin@sepia.org", "password": initial})
verifier("connexion avec le mot de passe journalisé", r.status_code == 200, str(r.status_code))

print("\n== COMPTE PERDU : verrouillé, désactivé, rétrogradé ==")
from app.database import SessionLocal                                   # noqa: E402
from app.models import User                                             # noqa: E402
from datetime import datetime, timedelta                                # noqa: E402
db = SessionLocal()
u = db.query(User).filter(User.email == "admin@sepia.org").first()
u.role = "lecteur"
u.is_active = False
u.failed_attempts = 12
u.locked_until = datetime.utcnow() + timedelta(days=30)
u.password_hash = "empreinte-devenue-inutilisable"
db.commit()
db.close()
c2 = demarrer()
r = c2.post("/api/auth/login", data={"username": "admin@sepia.org", "password": initial})
verifier("compte effectivement inaccessible", r.status_code != 200, str(r.status_code))

print("\n== RÉINITIALISATION PAR SEPIA_ADMIN_RESET ==")
tampon.truncate(0), tampon.seek(0)
os.environ["SEPIA_ADMIN_RESET"] = "1"
c3 = demarrer()
nouveau = mot_de_passe_journalise(tampon.getvalue())
verifier("nouveau mot de passe journalisé", bool(nouveau), nouveau)
verifier("avertissement de retrait de la variable",
         "RETIREZ MAINTENANT SEPIA_ADMIN_RESET" in tampon.getvalue())
r = c3.post("/api/auth/login", data={"username": "admin@sepia.org", "password": nouveau})
verifier("connexion rétablie", r.status_code == 200, str(r.status_code))
if r.status_code == 200:
    verifier("changement de mot de passe exigé",
             r.json().get("doit_changer_mot_de_passe") is True)
    profil = c3.get("/api/auth/moi").json()
    verifier("rôle d'administrateur rétabli", profil["role"] == "admin", profil["role"])
    verifier("compte réactivé", profil["is_active"] is True)
    verifier("verrouillage effacé", c3.get("/api/auth/utilisateurs").status_code == 200)
verifier("ancien mot de passe refusé",
         c3.post("/api/auth/login",
                 data={"username": "admin@sepia.org", "password": initial}).status_code != 200)

print("\n== MOT DE PASSE IMPOSÉ PAR L'ENVIRONNEMENT ==")
os.environ["SEPIA_ADMIN_PASSWORD"] = "Antilope-Cuivre-Sillon-6"
c4 = demarrer()
r = c4.post("/api/auth/login",
            data={"username": "admin@sepia.org", "password": "Antilope-Cuivre-Sillon-6"})
verifier("connexion avec le mot de passe imposé", r.status_code == 200, str(r.status_code))

print("\n== SANS LA VARIABLE, AUCUNE RÉINITIALISATION ==")
os.environ["SEPIA_ADMIN_RESET"] = ""
os.environ["SEPIA_ADMIN_PASSWORD"] = "Otarie-Grenat-Falaise-3"
c5 = demarrer()
r = c5.post("/api/auth/login",
            data={"username": "admin@sepia.org", "password": "Otarie-Grenat-Falaise-3"})
verifier("le mot de passe n'est pas remplacé au démarrage ordinaire",
         r.status_code != 200, str(r.status_code))
r = c5.post("/api/auth/login",
            data={"username": "admin@sepia.org", "password": "Antilope-Cuivre-Sillon-6"})
verifier("le mot de passe précédent reste valable", r.status_code == 200, str(r.status_code))

print("\n== AUCUN POINT D'ENTRÉE RÉSEAU DE RÉINITIALISATION ==")
for chemin in ("/api/auth/reinitialiser", "/api/auth/reset", "/api/admin/reset",
               "/api/auth/mot-de-passe-oublie"):
    r = c5.post(chemin, json={"email": "admin@sepia.org"})
    verifier(f"{chemin} inexistant", r.status_code in (404, 405), str(r.status_code))

print(f"\n{len(ok)} contrôles réussis, {len(ko)} en échec.")
sys.exit(1 if ko else 0)
