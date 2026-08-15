"""Authentification, gestion du compte et des utilisateurs."""
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..crud import serialize, serialize_many
from ..database import get_db
from ..models import User
from ..security import create_token, current_user, hash_password, is_admin, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentification"])

ROLES = {
    "admin": "Administrateur — accès complet et gestion des comptes",
    "coordonnateur": "Coordonnateur — pilotage du projet et validation",
    "suivi_evaluation": "Responsable S&E — paramétrage et analyse",
    "operateur": "Opérateur de saisie — collecte et mise à jour des données",
    "lecteur": "Lecteur — consultation et téléchargement des livrables",
}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.strip().lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Ce compte est désactivé.")
    user.last_login = datetime.utcnow()
    db.commit()
    return {"access_token": create_token(user), "token_type": "bearer",
            "utilisateur": serialize(user)}


@router.get("/moi")
def profil(user: User = Depends(current_user)):
    donnees = serialize(user)
    donnees.pop("password_hash", None)
    donnees["role_libelle"] = ROLES.get(user.role, user.role)
    return donnees


@router.put("/moi")
def modifier_profil(payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: User = Depends(current_user)):
    for champ in ("full_name", "organisation", "phone"):
        if champ in payload:
            setattr(user, champ, payload[champ])
    if payload.get("nouveau_mot_de_passe"):
        if not verify_password(payload.get("mot_de_passe_actuel", ""), user.password_hash):
            raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect.")
        if len(payload["nouveau_mot_de_passe"]) < 8:
            raise HTTPException(status_code=400,
                                detail="Le mot de passe doit comporter au moins 8 caractères.")
        user.password_hash = hash_password(payload["nouveau_mot_de_passe"])
    db.commit()
    return {"message": "Profil mis à jour."}


@router.get("/roles")
def liste_roles(user: User = Depends(current_user)):
    return [{"code": code, "libelle": libelle} for code, libelle in ROLES.items()]


@router.get("/utilisateurs")
def liste_utilisateurs(db: Session = Depends(get_db), user: User = Depends(is_admin)):
    utilisateurs = serialize_many(db.query(User).order_by(User.full_name).all())
    for u in utilisateurs:
        u.pop("password_hash", None)
    return utilisateurs


@router.post("/utilisateurs", status_code=201)
def creer_utilisateur(payload: Dict[str, Any], db: Session = Depends(get_db),
                      user: User = Depends(is_admin)):
    email = (payload.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Adresse électronique invalide.")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Un compte existe déjà pour cette adresse.")
    mot_de_passe = payload.get("password") or "sepia2024"
    nouvel_utilisateur = User(
        email=email, full_name=payload.get("full_name") or email.split("@")[0],
        password_hash=hash_password(mot_de_passe),
        role=payload.get("role") if payload.get("role") in ROLES else "lecteur",
        organisation=payload.get("organisation"), phone=payload.get("phone"),
    )
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)
    donnees = serialize(nouvel_utilisateur)
    donnees.pop("password_hash", None)
    return donnees


@router.put("/utilisateurs/{user_id}")
def modifier_utilisateur(user_id: int, payload: Dict[str, Any], db: Session = Depends(get_db),
                         user: User = Depends(is_admin)):
    cible = db.get(User, user_id)
    if not cible:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    for champ in ("full_name", "organisation", "phone", "is_active"):
        if champ in payload:
            setattr(cible, champ, payload[champ])
    if payload.get("role") in ROLES:
        cible.role = payload["role"]
    if payload.get("password"):
        cible.password_hash = hash_password(payload["password"])
    db.commit()
    donnees = serialize(cible)
    donnees.pop("password_hash", None)
    return donnees


@router.delete("/utilisateurs/{user_id}")
def supprimer_utilisateur(user_id: int, db: Session = Depends(get_db),
                          user: User = Depends(is_admin)):
    cible = db.get(User, user_id)
    if not cible:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if cible.id == user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte.")
    db.delete(cible)
    db.commit()
    return {"deleted": user_id}
