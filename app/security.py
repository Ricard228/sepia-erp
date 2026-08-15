"""Authentification : hachage PBKDF2 et jetons signés HMAC (sans dépendance externe)."""
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import SECRET_KEY, TOKEN_TTL_SECONDS
from .database import get_db
from .models import User

PBKDF2_ROUNDS = 180_000
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

ROLE_RANK = {"lecteur": 1, "operateur": 2, "suivi_evaluation": 3, "coordonnateur": 4, "admin": 5}


# --- Mots de passe ---------------------------------------------------------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_b64, digest_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        expected = base64.b64decode(digest_b64)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(rounds))
        return hmac.compare_digest(expected, candidate)
    except Exception:
        return False


# --- Jetons ----------------------------------------------------------------
def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64url(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_token(user: User) -> str:
    payload = {
        "sub": user.email,
        "uid": user.id,
        "role": user.role,
        "name": user.full_name,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64url(hmac.new(SECRET_KEY.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def decode_token(token: str) -> Optional[dict]:
    try:
        body, signature = token.split(".")
        expected = _b64url(hmac.new(SECRET_KEY.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expected, signature):
            return None
        payload = json.loads(_unb64url(body))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# --- Dépendances FastAPI ---------------------------------------------------
def current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expirée ou invalide. Veuillez vous reconnecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    payload = decode_token(token)
    if not payload:
        raise credentials_error
    user = db.query(User).filter(User.email == payload["sub"], User.is_active.is_(True)).first()
    if not user:
        raise credentials_error
    return user


def require_role(minimum: str):
    """Dépendance de contrôle d'accès hiérarchique."""
    threshold = ROLE_RANK.get(minimum, 99)

    def _check(user: User = Depends(current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < threshold:
            raise HTTPException(status_code=403, detail="Droits insuffisants pour cette opération.")
        return user

    return _check


can_edit = require_role("operateur")
can_manage = require_role("suivi_evaluation")
is_admin = require_role("admin")
