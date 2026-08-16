"""Authentification et contrôle d'accès.

Choix retenus et raisons :
  * hachage PBKDF2-HMAC-SHA256 à 240 000 itérations avec sel aléatoire par compte ;
  * jetons signés HMAC-SHA256 transportés par cookie « HttpOnly », inaccessible au
    JavaScript de la page, donc hors de portée d'une injection de script ;
  * comparaisons en temps constant et message d'erreur unique à la connexion, pour
    ne pas révéler l'existence d'un compte ;
  * verrouillage temporaire du compte après une série d'échecs ;
  * clés d'accès dédiées, révocables et limitées à la lecture, pour les
    connecteurs de business intelligence — le jeton de session ne circule jamais
    dans une URL.
Aucune dépendance externe n'est utilisée : la bibliothèque standard suffit et
supprime autant de rustines de sécurité à suivre.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from .config import (EST_PRODUCTION, MOTS_DE_PASSE_INTERDITS, MOT_DE_PASSE_CLASSES_MIN,
                     MOT_DE_PASSE_LONGUEUR_MIN, SECRET_KEY, TOKEN_INACTIVITE_SECONDS,
                     TOKEN_TTL_SECONDS, VERROU_APRES_ECHECS, VERROU_DUREE_MINUTES)
from .database import get_db
from .models import ApiKey, User

PBKDF2_ROUNDS = 240_000
NOM_COOKIE = "sepia_session"
ROLE_RANK = {"lecteur": 1, "operateur": 2, "suivi_evaluation": 3, "coordonnateur": 4, "admin": 5}
MOTIF_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


# ---------------------------------------------------------------------------
# Mots de passe
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return (f"pbkdf2_sha256${PBKDF2_ROUNDS}${base64.b64encode(salt).decode()}"
            f"${base64.b64encode(digest).decode()}")


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_b64, digest_b64 = (stored or "").split("$")
        if algo != "pbkdf2_sha256":
            return False
        attendu = base64.b64decode(digest_b64)
        candidat = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                       base64.b64decode(salt_b64), int(rounds))
        return hmac.compare_digest(attendu, candidat)
    except Exception:
        return False


def _classes_caracteres(mot_de_passe: str) -> int:
    return sum([
        bool(re.search(r"[a-z]", mot_de_passe)),
        bool(re.search(r"[A-Z]", mot_de_passe)),
        bool(re.search(r"[0-9]", mot_de_passe)),
        bool(re.search(r"[^A-Za-z0-9]", mot_de_passe)),
    ])


def _normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFD", (texte or "").lower())
    return "".join(c for c in texte if unicodedata.category(c) != "Mn")


def valider_mot_de_passe(mot_de_passe: str, email: str = "", nom: str = "") -> None:
    """Refuse un mot de passe trop court, trop simple ou dérivé de l'identité.

    Lève une HTTPException décrivant précisément l'exigence non satisfaite, afin
    que l'utilisateur puisse corriger sans tâtonner.
    """
    mot_de_passe = mot_de_passe or ""
    if len(mot_de_passe) < MOT_DE_PASSE_LONGUEUR_MIN:
        raise HTTPException(
            status_code=422,
            detail=f"Le mot de passe doit comporter au moins {MOT_DE_PASSE_LONGUEUR_MIN} "
                   f"caractères. Une phrase de passe de plusieurs mots est le choix le plus sûr "
                   f"et le plus simple à retenir.")
    if len(mot_de_passe) > 200:
        raise HTTPException(status_code=422, detail="Le mot de passe ne peut excéder 200 caractères.")
    if _classes_caracteres(mot_de_passe) < MOT_DE_PASSE_CLASSES_MIN:
        raise HTTPException(
            status_code=422,
            detail=f"Le mot de passe doit combiner au moins {MOT_DE_PASSE_CLASSES_MIN} types de "
                   f"caractères parmi : minuscules, majuscules, chiffres, caractères spéciaux.")
    normalise = _normaliser(mot_de_passe)
    if normalise in MOTS_DE_PASSE_INTERDITS or normalise.replace(" ", "") in MOTS_DE_PASSE_INTERDITS:
        raise HTTPException(status_code=422,
                            detail="Ce mot de passe figure parmi les plus utilisés : il serait "
                                   "trouvé immédiatement. Choisissez-en un autre.")
    if re.fullmatch(r"(.)\1+", mot_de_passe) or normalise in ("0123456789", "abcdefghijkl"):
        raise HTTPException(status_code=422,
                            detail="Le mot de passe ne peut être une répétition ou une suite "
                                   "de caractères.")
    identite = [p for p in re.split(r"[@.\s\-_]+", _normaliser(email) + " " + _normaliser(nom))
                if len(p) >= 4]
    for morceau in identite:
        if morceau in normalise:
            raise HTTPException(
                status_code=422,
                detail="Le mot de passe ne doit pas contenir votre nom ni votre adresse "
                       "électronique : ce sont les premiers essais d'un attaquant.")


def engendrer_mot_de_passe(longueur: int = 20) -> str:
    """Mot de passe aléatoire conforme à la politique, pour l'amorçage ou une réinitialisation."""
    alphabet = ("abcdefghijkmnopqrstuvwxyz" "ABCDEFGHJKLMNPQRSTUVWXYZ" "23456789" "!@#%*-_=+")
    while True:
        candidat = "".join(secrets.choice(alphabet) for _ in range(longueur))
        if _classes_caracteres(candidat) >= MOT_DE_PASSE_CLASSES_MIN:
            return candidat


def valider_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not MOTIF_EMAIL.fullmatch(email) or len(email) > 160:
        raise HTTPException(status_code=422, detail="Adresse électronique invalide.")
    return email


# ---------------------------------------------------------------------------
# Jetons de session
# ---------------------------------------------------------------------------
def _b64url(brut: bytes) -> str:
    return base64.urlsafe_b64encode(brut).decode().rstrip("=")


def _unb64url(donnees: str) -> bytes:
    return base64.urlsafe_b64decode(donnees + "=" * (-len(donnees) % 4))


def _seuil_jetons(user: User) -> float:
    """Instant UTC avant lequel les jetons de ce compte sont périmés.

    La date est stockée par ``datetime.utcnow()``, qui produit un objet *naïf* :
    appeler ``.timestamp()`` dessus l'interpréterait comme une heure locale et
    décalerait la comparaison de tout le fuseau du serveur — d'où le rattachement
    explicite à UTC.
    """
    return user.tokens_valid_from.replace(tzinfo=timezone.utc).timestamp()


def create_token(user: User) -> str:
    # « iat » conserve les fractions de seconde. Tronqué à la seconde, il serait
    # antérieur à l'instant d'invalidation inscrit au même moment lors d'un
    # changement de mot de passe : le jeton tout juste émis serait rejeté par sa
    # propre invalidation, déconnectant l'utilisateur au moment où il se
    # reconnecte. À l'inverse, arrondir la comparaison à la seconde laisserait
    # survivre une seconde entière de jetons à une déconnexion globale.
    maintenant = time.time()
    charge = {
        "sub": user.email,
        "uid": user.id,
        "role": user.role,
        "name": user.full_name,
        "iat": maintenant,
        "exp": int(maintenant) + TOKEN_TTL_SECONDS,
        "jti": secrets.token_urlsafe(9),
    }
    corps = _b64url(json.dumps(charge, separators=(",", ":")).encode())
    signature = _b64url(hmac.new(SECRET_KEY.encode(), corps.encode(), hashlib.sha256).digest())
    return f"{corps}.{signature}"


def decode_token(token: str) -> Optional[dict]:
    try:
        corps, signature = (token or "").split(".")
        attendue = _b64url(hmac.new(SECRET_KEY.encode(), corps.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(attendue, signature):
            return None
        charge = json.loads(_unb64url(corps))
        if charge.get("exp", 0) < time.time():
            return None
        return charge
    except Exception:
        return None


def poser_cookie_session(reponse: Response, token: str) -> None:
    """Dépose le jeton dans un cookie inaccessible au JavaScript.

    « HttpOnly » met le jeton hors de portée d'un script injecté dans la page ;
    « SameSite=Strict » empêche qu'il soit envoyé lors d'une requête déclenchée
    depuis un autre site ; « Secure » impose HTTPS en production.
    """
    reponse.set_cookie(
        key=NOM_COOKIE, value=token, max_age=TOKEN_TTL_SECONDS, httponly=True,
        samesite="strict", secure=EST_PRODUCTION, path="/")


def retirer_cookie_session(reponse: Response) -> None:
    reponse.delete_cookie(key=NOM_COOKIE, path="/", httponly=True,
                          samesite="strict", secure=EST_PRODUCTION)


# ---------------------------------------------------------------------------
# Clés d'accès en lecture seule (connecteurs BI)
# ---------------------------------------------------------------------------
def creer_cle_api(db: Session, user: User, label: str, project_id: Optional[int] = None,
                  jours: int = 90) -> Tuple[ApiKey, str]:
    """Engendre une clé ; le secret n'est retourné qu'une fois et n'est jamais stocké."""
    secret = secrets.token_urlsafe(32)
    prefixe = "sk_" + secrets.token_hex(4)
    cle = ApiKey(
        user_id=user.id, label=(label or "Connecteur")[:120], prefix=prefixe,
        key_hash=hashlib.sha256(f"{prefixe}.{secret}".encode()).hexdigest(),
        project_id=project_id, scope="lecture",
        expires_at=datetime.utcnow() + timedelta(days=max(1, min(jours, 365))))
    db.add(cle)
    db.commit()
    db.refresh(cle)
    return cle, f"{prefixe}.{secret}"


def resoudre_cle_api(db: Session, valeur: str) -> Optional[ApiKey]:
    if not valeur or "." not in valeur:
        return None
    prefixe = valeur.split(".", 1)[0]
    cle = db.query(ApiKey).filter(ApiKey.prefix == prefixe,
                                  ApiKey.revoked.is_(False)).first()
    if not cle:
        return None
    empreinte = hashlib.sha256(valeur.encode()).hexdigest()
    if not hmac.compare_digest(cle.key_hash, empreinte):
        return None
    if cle.expires_at and cle.expires_at < datetime.utcnow():
        return None
    cle.last_used_at = datetime.utcnow()
    db.commit()
    return cle


# ---------------------------------------------------------------------------
# Verrouillage après échecs répétés
# ---------------------------------------------------------------------------
def compte_verrouille(user: User) -> Optional[int]:
    """Minutes restantes de verrouillage, ou None si le compte est ouvert."""
    if user.locked_until and user.locked_until > datetime.utcnow():
        return max(1, int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1)
    return None


def enregistrer_echec(db: Session, user: Optional[User]) -> None:
    if user is None:
        return
    user.failed_attempts = (user.failed_attempts or 0) + 1
    if user.failed_attempts >= VERROU_APRES_ECHECS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=VERROU_DUREE_MINUTES)
        user.failed_attempts = 0
    db.commit()


def enregistrer_succes(db: Session, user: User) -> None:
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()


# ---------------------------------------------------------------------------
# Dépendances FastAPI
# ---------------------------------------------------------------------------
def _jeton_de_la_requete(request: Request) -> Optional[str]:
    """Cookie de session en priorité ; en-tête Authorization accepté en repli."""
    cookie = request.cookies.get(NOM_COOKIE)
    if cookie:
        return cookie
    entete = request.headers.get("authorization") or ""
    if entete.lower().startswith("bearer "):
        return entete[7:].strip()
    return None


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    erreur = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expirée ou invalide. Veuillez vous reconnecter.")
    charge = decode_token(_jeton_de_la_requete(request) or "")
    if not charge:
        raise erreur
    user = db.query(User).filter(User.email == charge.get("sub"),
                                 User.is_active.is_(True)).first()
    if not user:
        raise erreur
    # Une déconnexion globale ou un changement de mot de passe invalide les jetons
    # émis auparavant, y compris ceux déjà distribués.
    if user.tokens_valid_from and charge.get("iat", 0) < _seuil_jetons(user):
        raise erreur
    # Le rôle est relu en base : une élévation de privilège inscrite dans un jeton
    # volé resterait sans effet.
    request.state.utilisateur = user
    return user


def require_role(minimum: str):
    seuil = ROLE_RANK.get(minimum, 99)

    def _verifier(user: User = Depends(current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < seuil:
            raise HTTPException(status_code=403,
                                detail="Droits insuffisants pour cette opération.")
        return user

    return _verifier


can_edit = require_role("operateur")
can_manage = require_role("suivi_evaluation")
is_admin = require_role("admin")
