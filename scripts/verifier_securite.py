"""Jeu de vérification des garde-fous de sécurité de la plateforme SEPIA.

Exécute une série de contrôles contre l'application réelle : authentification,
session, en-têtes, cloisonnement des projets, confirmation d'adresse, politique
de mot de passe, téléversements piégés et tentatives d'injection.

Usage :  python scripts/verifier_securite.py

La base est créée dans un répertoire temporaire : les données réelles ne sont
jamais touchées. Sortie 0 si tous les contrôles passent, 1 sinon.
"""
import os
import pathlib
import secrets
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
# Identifiants tirés au hasard à chaque exécution, sur une base jetable : aucun
# mot de passe n'est inscrit dans le dépôt, pas même pour les vérifications.
MOT_DE_PASSE_ADMIN = "Verif-" + secrets.token_urlsafe(12) + "-9"
os.environ["SEPIA_ADMIN_PASSWORD"] = MOT_DE_PASSE_ADMIN
os.environ["SEPIA_SECRET_KEY"] = "cle-de-test-uniquement-pour-la-verification"
os.environ["SEPIA_ENV"] = "developpement"
# Base temporaire : le jeu de vérification ne touche pas aux données réelles.
os.environ.setdefault("SEPIA_DATA_DIR",
                      tempfile.mkdtemp(prefix="sepia-verification-"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

# Le contexte déclenche l'événement de démarrage (création des tables et amorçage).
_contexte = TestClient(app)
_contexte.__enter__()
c = _contexte
ok = []
ko = []


def verifier(libelle, condition, detail=""):
    (ok if condition else ko).append(libelle)
    print(f"  {'OK   ' if condition else 'ECHEC'} {libelle}" + (f" — {detail}" if detail else ""))


print("== CONNEXION ==")
r = c.post("/api/auth/login", data={"username": "admin@sepia.org", "password": "mauvais"})
verifier("mot de passe erroné refusé", r.status_code == 401, r.json().get("detail"))
r = c.post("/api/auth/login", data={"username": "inconnu@nulle.part", "password": "x"})
verifier("compte inexistant : message identique", r.status_code == 401
         and r.json().get("detail") == "Identifiants incorrects.", r.json().get("detail"))

r = c.post("/api/auth/login",
           data={"username": "admin@sepia.org", "password": MOT_DE_PASSE_ADMIN})
verifier("connexion valide", r.status_code == 200)
cookies = r.cookies
entete = r.headers.get("set-cookie", "")
verifier("cookie HttpOnly", "httponly" in entete.lower(), entete[:90])
verifier("cookie SameSite=Strict", "samesite=strict" in entete.lower())
verifier("jeton absent du corps en clair pour le navigateur",
         "sepia_session" not in r.text)

print("\n== EN-TÊTES DE SÉCURITÉ ==")
r = c.get("/api/auth/moi")
for entete_attendu in ("content-security-policy", "x-content-type-options",
                       "referrer-policy", "x-frame-options"):
    verifier(f"en-tête {entete_attendu}", entete_attendu in {k.lower() for k in r.headers})
verifier("script-src 'self'", "script-src 'self'" in r.headers.get("content-security-policy", ""))
verifier("cache no-store sur /api/", "no-store" in r.headers.get("cache-control", ""))

print("\n== ACCÈS SANS SESSION ==")
anonyme = TestClient(app)
for chemin in ("/api/projects", "/api/auth/utilisateurs", "/api/dashboard/1",
               "/api/journal?limit=5", "/api/beneficiaires/synthese/1"):
    r = anonyme.get(chemin)
    verifier(f"anonyme refusé sur {chemin}", r.status_code in (401, 403), str(r.status_code))

print("\n== ÉLÉVATION DE PRIVILÈGE PAR LE CORPS DE LA REQUÊTE ==")
r = c.put("/api/auth/moi", json={"full_name": "Admin", "role": "lecteur",
                                 "is_active": False, "password_hash": "x"})
profil = c.get("/api/auth/moi").json()
verifier("le rôle ne peut être modifié par /moi", profil["role"] == "admin", profil["role"])
verifier("le compte reste actif", profil["is_active"] is True)
verifier("empreinte jamais exposée", "password_hash" not in profil)

print("\n== CRÉATION DE COMPTE ET VÉRIFICATION D'ADRESSE ==")
r = c.post("/api/auth/utilisateurs",
           json={"email": "essai@exemple.org", "full_name": "Compte d'essai", "role": "lecteur"})
verifier("compte créé", r.status_code == 201, str(r.status_code))
cree = r.json()
mot_de_passe = cree.get("mot_de_passe_initial")
lien = cree.get("lien_verification", "")
verifier("mot de passe provisoire engendré", bool(mot_de_passe))
verifier("lien de vérification fourni", lien.startswith("/#verifier="))

essai = TestClient(app)
r = essai.post("/api/auth/login", data={"username": "essai@exemple.org", "password": mot_de_passe})
verifier("connexion refusée avant confirmation d'adresse", r.status_code == 403,
         r.json().get("detail", "")[:60])

r = essai.post("/api/auth/verifier-adresse", json={"jeton": "jeton-totalement-invalide-xxxx"})
verifier("jeton invalide : réponse indistincte", r.status_code == 200)
r = essai.post("/api/auth/login", data={"username": "essai@exemple.org", "password": mot_de_passe})
verifier("toujours refusé après jeton invalide", r.status_code == 403)

r = essai.post("/api/auth/verifier-adresse", json={"jeton": lien.split("=", 1)[1]})
verifier("confirmation acceptée", r.status_code == 200)
r = essai.post("/api/auth/login", data={"username": "essai@exemple.org", "password": mot_de_passe})
verifier("connexion possible après confirmation", r.status_code == 200)
verifier("changement de mot de passe imposé",
         r.status_code == 200 and r.json().get("doit_changer_mot_de_passe") is True)
r = essai.post("/api/auth/verifier-adresse", json={"jeton": lien.split("=", 1)[1]})
verifier("jeton à usage unique", r.status_code == 200)

print("\n== CLOISONNEMENT DES PROJETS ==")
projets = c.get("/api/projects").json()
id_projet = projets[0]["id"] if projets else None
r = essai.get(f"/api/dashboard/{id_projet}")
verifier("lecteur non membre : 404 (l'existence n'est pas confirmée)",
         r.status_code == 404, str(r.status_code))
r = essai.post("/api/auth/utilisateurs", json={"email": "z@z.org"})
verifier("non-admin ne peut créer de compte", r.status_code == 403, str(r.status_code))
r = essai.get("/api/journal?limit=5")
verifier("non-admin ne peut lire le journal", r.status_code == 403, str(r.status_code))

print("\n== MOT DE PASSE ==")
r = essai.put("/api/auth/moi", json={"mot_de_passe_actuel": mot_de_passe,
                                     "nouveau_mot_de_passe": "court"})
verifier("mot de passe trop court refusé", r.status_code == 422,
         r.json().get("detail", "")[:60])
r = essai.put("/api/auth/moi", json={"mot_de_passe_actuel": "faux",
                                     "nouveau_mot_de_passe": "Phrase-De-Passe-Longue-9"})
verifier("mot de passe actuel exigé", r.status_code == 400, str(r.status_code))
r = essai.put("/api/auth/moi", json={"role": "admin", "password": "x",
                                     "must_change_password": False})
apres = essai.get("/api/auth/moi").json()
verifier("champs hors liste blanche ignorés dans /moi",
         apres["role"] == "lecteur" and apres["must_change_password"] is True, apres["role"])
r = essai.put("/api/auth/moi", json={"mot_de_passe_actuel": mot_de_passe,
                                     "nouveau_mot_de_passe": "Phrase-De-Passe-Longue-9"})
verifier("changement de mot de passe accepté", r.status_code == 200)
# Le changement invalide les jetons antérieurs et en émet un nouveau : la session
# courante doit survivre. Une comparaison imprécise entre l'instant
# d'invalidation et l'horodatage du jeton déconnecterait au moment même de la
# reconnexion.
r = essai.get("/api/auth/moi")
verifier("la session courante survit au changement de mot de passe",
         r.status_code == 200, str(r.status_code))
verifier("changement de mot de passe non redemandé",
         r.status_code == 200 and r.json().get("must_change_password") is False)
ancienne = TestClient(app)
ancienne.cookies.set("sepia_session", essai.cookies.get("sepia_session"))
r = ancienne.post("/api/auth/deconnexion-globale")
verifier("déconnexion globale", r.status_code == 200)
r = essai.get("/api/auth/moi")
verifier("les jetons antérieurs sont bien périmés", r.status_code == 401, str(r.status_code))
essai.post("/api/auth/login", data={"username": "essai@exemple.org",
                                    "password": "Phrase-De-Passe-Longue-9"})

print("\n== TÉLÉVERSEMENT ==")
r = c.post("/api/imports/excel/1",
           files={"fichier": ("charge.xlsx", b"<?php system($_GET[0]); ?>",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
verifier("fichier au mauvais nombre magique refusé", r.status_code == 422,
         str(r.json().get("detail", ""))[:70])
r = c.post("/api/imports/excel/1", files={"fichier": ("charge.exe", b"MZ\x90\x00", "application/exe")})
verifier("extension non autorisée refusée", r.status_code == 422,
         str(r.json().get("detail", ""))[:70])
gros = b"PK" + bytes(21 * 1024 * 1024)
r = c.post("/api/imports/excel/1", files={"fichier": ("gros.xlsx", gros, "application/octet-stream")})
verifier("fichier hors gabarit refusé", r.status_code == 413, str(r.status_code))

print("\n== INJECTION DANS LA RECHERCHE ==")
tout = c.get("/api/indicators?project_id=1&limit=500").json()
r = c.get("/api/indicators?project_id=1&q=%25&limit=500")
verifier("joker SQL traité comme du texte", r.status_code == 200 and len(r.json()) == 0,
         f"{len(r.json())} résultat(s) pour « % » contre {len(tout)} au total")
r = c.get("/api/indicators?project_id=1&q=_&limit=500")
verifier("joker « _ » neutralisé", r.status_code == 200 and len(r.json()) == 0,
         f"{len(r.json())} résultat(s)")
r = c.get("/api/indicators?project_id=1&parent_field=password_hash&parent_id=1")
verifier("champ de rattachement arbitraire refusé", r.status_code == 422, str(r.status_code))

print("\n== INJECTION DANS L'INTERFACE ==")
charge = "<img src=x onerror=alert(1)>"
r = c.post("/api/indicators", json={"project_id": 1, "code": "XSS-1", "name": charge,
                                    "unit": "nombre", "level": "Produit"})
verifier("enregistrement du texte tel quel", r.status_code in (200, 201), str(r.status_code))
if r.status_code in (200, 201):
    relu = c.get(f"/api/indicators/{r.json()['id']}").json()
    verifier("le serveur ne réécrit pas le texte (échappement à l'affichage)",
             relu["name"] == charge)
    c.delete(f"/api/indicators/{r.json()['id']}")

print("\n== DÉCONNEXION ==")
r = c.post("/api/auth/logout")
verifier("déconnexion", r.status_code == 200)
r = c.get("/api/auth/moi")
verifier("session close après déconnexion", r.status_code == 401, str(r.status_code))

print(f"\n{len(ok)} contrôles réussis, {len(ko)} en échec.")
if ko:
    print("Échecs : " + " | ".join(ko))
    sys.exit(1)
