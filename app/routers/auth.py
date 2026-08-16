"""Authentification, gestion du compte, des utilisateurs et des clés d'accès."""
import secrets
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..config import (LIMITE_CONNEXIONS_PAR_MINUTE, MOT_DE_PASSE_CLASSES_MIN,
                      MOT_DE_PASSE_LONGUEUR_MIN, TOKEN_TTL_SECONDS, VERROU_APRES_ECHECS,
                      VERROU_DUREE_MINUTES)
from ..crud import log_action, serialize, serialize_many
from ..database import get_db
from ..models import ApiKey, Project, ProjectMember, User
from ..security import (compte_verrouille, create_token, creer_cle_api, current_user,
                        engendrer_mot_de_passe, enregistrer_echec, enregistrer_succes,
                        hash_password, is_admin, poser_cookie_session, retirer_cookie_session,
                        valider_email, valider_mot_de_passe, verify_password)

router = APIRouter(prefix="/api/auth", tags=["Authentification"])

ROLES = {
    "admin": "Administrateur — accès complet et gestion des comptes",
    "coordonnateur": "Coordonnateur — pilotage de l'ensemble du portefeuille",
    "suivi_evaluation": "Responsable S&E — paramétrage et analyse de ses projets",
    "operateur": "Opérateur de saisie — collecte et mise à jour de ses projets",
    "lecteur": "Lecteur — consultation et téléchargement des livrables de ses projets",
}
# Message unique quels que soient l'inexistence du compte ou l'erreur de mot de
# passe : distinguer les deux cas permettrait d'énumérer les comptes existants.
ECHEC_CONNEXION = "Identifiants incorrects."


def _profil(user: User) -> Dict[str, Any]:
    donnees = serialize(user)
    for champ in ("password_hash", "verification_token", "failed_attempts", "locked_until"):
        donnees.pop(champ, None)
    donnees["role_libelle"] = ROLES.get(user.role, user.role)
    return donnees


@router.post("/login")
def login(reponse: Response, request: Request,
          form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Ouvre une session et dépose le jeton dans un cookie inaccessible au script."""
    email = (form.username or "").strip().lower()[:160]
    user = db.query(User).filter(User.email == email).first()

    minutes = compte_verrouille(user) if user else None
    if minutes:
        raise HTTPException(
            status_code=429,
            detail=f"Compte temporairement verrouillé après plusieurs tentatives infructueuses. "
                   f"Réessayez dans {minutes} minute(s).")

    # La vérification est effectuée même lorsque le compte n'existe pas, afin que
    # la durée de réponse ne trahisse pas son existence.
    empreinte = user.password_hash if user else hash_password(secrets.token_urlsafe(16))
    mot_de_passe_correct = verify_password(form.password or "", empreinte)

    if not user or not mot_de_passe_correct:
        enregistrer_echec(db, user)
        raise HTTPException(status_code=401, detail=ECHEC_CONNEXION)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Ce compte est désactivé.")
    # L'adresse électronique doit être confirmée avant tout accès : sans quoi un
    # compte pourrait être ouvert au nom d'une adresse que l'on ne contrôle pas,
    # et la réinitialisation du mot de passe deviendrait un moyen d'usurpation.
    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Adresse électronique non confirmée. Ouvrez le lien de confirmation qui vous "
                   "a été transmis, ou demandez-en un nouveau à votre administrateur.")

    enregistrer_succes(db, user)
    jeton = create_token(user)
    poser_cookie_session(reponse, jeton)
    log_action(db, user, "LOGIN", "User", user.id, None,
               (request.headers.get("user-agent") or "")[:120])
    db.commit()
    return {
        "access_token": jeton,          # conservé pour les intégrations en en-tête
        "token_type": "bearer",
        "expire_dans": TOKEN_TTL_SECONDS,
        "utilisateur": _profil(user),
        "doit_changer_mot_de_passe": bool(user.must_change_password),
    }


@router.post("/verifier-adresse")
def verifier_adresse(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Confirme une adresse électronique à partir du jeton transmis au titulaire.

    Le jeton est à usage unique : il est effacé dès la confirmation. La réponse
    est identique qu'il soit valide ou non, afin qu'un jeton ne puisse pas être
    deviné par essais successifs.
    """
    jeton = str(payload.get("jeton") or "").strip()
    reponse = {"message": "Si ce lien est valide, l'adresse est désormais confirmée."}
    if not jeton or len(jeton) < 16:
        return reponse
    user = db.query(User).filter(User.verification_token == jeton).first()
    if user:
        user.email_verified = True
        user.verification_token = None
        log_action(db, user, "VERIFY_EMAIL", "User", user.id, None, user.email)
        db.commit()
    return reponse


@router.post("/utilisateurs/{user_id}/lien-verification")
def lien_verification(user_id: int, db: Session = Depends(get_db),
                      user: User = Depends(is_admin)):
    """Réémet le jeton de confirmation d'adresse d'un compte (réservé à l'administration)."""
    cible = db.get(User, user_id)
    if not cible:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if cible.email_verified:
        return {"deja_confirmee": True,
                "message": "L'adresse de ce compte est déjà confirmée."}
    cible.verification_token = secrets.token_urlsafe(24)
    log_action(db, user, "REISSUE_VERIFICATION", "User", cible.id, None, cible.email)
    db.commit()
    return {
        "deja_confirmee": False,
        "jeton": cible.verification_token,
        "chemin": f"/#verifier={cible.verification_token}",
        "message": "Transmettez ce lien au titulaire du compte par un canal sûr. "
                   "Il confirme l'adresse et autorise la première connexion.",
    }


@router.post("/logout")
def logout(reponse: Response, db: Session = Depends(get_db),
           user: User = Depends(current_user)):
    retirer_cookie_session(reponse)
    log_action(db, user, "LOGOUT", "User", user.id, None)
    db.commit()
    return {"message": "Session close."}


@router.post("/deconnexion-globale")
def deconnexion_globale(reponse: Response, db: Session = Depends(get_db),
                        user: User = Depends(current_user)):
    """Invalide tous les jetons déjà émis pour ce compte, sur tous les appareils."""
    user.tokens_valid_from = datetime.utcnow()
    db.commit()
    retirer_cookie_session(reponse)
    return {"message": "Toutes les sessions de ce compte ont été fermées."}


@router.get("/moi")
def profil(user: User = Depends(current_user)):
    return _profil(user)


@router.put("/moi")
def modifier_profil(payload: Dict[str, Any], reponse: Response,
                    db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Modification de son propre profil.

    Seuls le nom, l'organisation, le téléphone et le mot de passe sont
    modifiables ici : le rôle et l'état du compte relèvent de l'administration,
    faute de quoi tout utilisateur s'octroierait les droits d'administrateur.
    """
    for champ in ("full_name", "organisation", "phone"):
        if champ in payload:
            valeur = payload[champ]
            setattr(user, champ, str(valeur)[:160] if valeur else None)

    if payload.get("nouveau_mot_de_passe"):
        if not verify_password(payload.get("mot_de_passe_actuel", ""), user.password_hash):
            raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect.")
        valider_mot_de_passe(payload["nouveau_mot_de_passe"], user.email, user.full_name)
        user.password_hash = hash_password(payload["nouveau_mot_de_passe"])
        user.password_changed_at = datetime.utcnow()
        user.must_change_password = False
        # Un changement de mot de passe ferme les sessions ouvertes ailleurs.
        user.tokens_valid_from = datetime.utcnow()
        db.commit()
        poser_cookie_session(reponse, create_token(user))
        log_action(db, user, "PASSWORD_CHANGE", "User", user.id, None)
        db.commit()
        return {"message": "Mot de passe modifié. Les autres sessions ont été fermées."}
    db.commit()
    return {"message": "Profil mis à jour."}


@router.get("/politique-mot-de-passe")
def politique_mot_de_passe():
    """Exigences appliquées, affichées dans l'interface avant la saisie."""
    return {
        "longueur_minimale": MOT_DE_PASSE_LONGUEUR_MIN,
        "classes_minimales": MOT_DE_PASSE_CLASSES_MIN,
        "classes": ["minuscules", "majuscules", "chiffres", "caractères spéciaux"],
        "interdits": ["mots de passe courants", "répétitions et suites",
                      "votre nom ou votre adresse électronique"],
        "verrouillage": f"{VERROU_APRES_ECHECS} échecs entraînent un verrouillage de "
                        f"{VERROU_DUREE_MINUTES} minutes",
        "limite_connexions": f"{LIMITE_CONNEXIONS_PAR_MINUTE} tentatives par minute et par adresse",
    }


@router.get("/roles")
def liste_roles(user: User = Depends(current_user)):
    return [{"code": code, "libelle": libelle} for code, libelle in ROLES.items()]


# ---------------------------------------------------------------------------
# Administration des comptes
# ---------------------------------------------------------------------------
@router.get("/utilisateurs")
def liste_utilisateurs(db: Session = Depends(get_db), user: User = Depends(is_admin)):
    return [_profil(u) for u in db.query(User).order_by(User.full_name).all()]


@router.post("/utilisateurs", status_code=201)
def creer_utilisateur(payload: Dict[str, Any], db: Session = Depends(get_db),
                      user: User = Depends(is_admin)):
    email = valider_email(payload.get("email"))
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Un compte existe déjà pour cette adresse.")
    mot_de_passe = payload.get("password") or ""
    engendre = False
    if mot_de_passe:
        valider_mot_de_passe(mot_de_passe, email, payload.get("full_name", ""))
    else:
        mot_de_passe = engendrer_mot_de_passe()
        engendre = True
    nouveau = User(
        email=email,
        full_name=str(payload.get("full_name") or email.split("@")[0])[:160],
        password_hash=hash_password(mot_de_passe),
        role=payload.get("role") if payload.get("role") in ROLES else "lecteur",
        organisation=str(payload.get("organisation") or "")[:160] or None,
        phone=str(payload.get("phone") or "")[:40] or None,
        must_change_password=True,
        email_verified=False,
        verification_token=secrets.token_urlsafe(24),
        password_changed_at=datetime.utcnow(),
    )
    db.add(nouveau)
    db.flush()
    log_action(db, user, "CREATE_USER", "User", nouveau.id, None, email)
    db.commit()
    db.refresh(nouveau)
    resultat = _profil(nouveau)
    # Le mot de passe engendré n'est montré qu'une fois, à l'administrateur qui
    # crée le compte, et devra être changé à la première connexion.
    resultat["mot_de_passe_initial"] = mot_de_passe if engendre else None
    # Le lien de confirmation n'est montré qu'ici, à l'administrateur qui crée le
    # compte : tant qu'il n'est pas ouvert, la connexion est refusée.
    resultat["lien_verification"] = f"/#verifier={nouveau.verification_token}"
    resultat["message"] = ("Mot de passe provisoire engendré : transmettez-le par un canal "
                           "distinct de l'adresse électronique. Il devra être changé à la "
                           "première connexion." if engendre else
                           "Compte créé. Le mot de passe devra être changé à la première "
                           "connexion.") + " Transmettez également le lien de confirmation " \
                          "d'adresse : la connexion reste refusée tant qu'il n'est pas ouvert."
    return resultat


@router.put("/utilisateurs/{user_id}")
def modifier_utilisateur(user_id: int, payload: Dict[str, Any], db: Session = Depends(get_db),
                         user: User = Depends(is_admin)):
    cible = db.get(User, user_id)
    if not cible:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    for champ in ("full_name", "organisation", "phone"):
        if champ in payload:
            setattr(cible, champ, str(payload[champ])[:160] if payload[champ] else None)
    if "is_active" in payload:
        # Un administrateur ne peut se désactiver lui-même : la plateforme
        # resterait sans compte d'administration si c'était le dernier.
        if cible.id == user.id and not payload["is_active"]:
            raise HTTPException(status_code=400,
                                detail="Vous ne pouvez pas désactiver votre propre compte.")
        cible.is_active = bool(payload["is_active"])
        if not cible.is_active:
            cible.tokens_valid_from = datetime.utcnow()
    if payload.get("role") in ROLES:
        if cible.id == user.id and payload["role"] != "admin":
            raise HTTPException(status_code=400,
                                detail="Vous ne pouvez pas retirer votre propre rôle "
                                       "d'administrateur.")
        if cible.role != payload["role"]:
            log_action(db, user, "ROLE_CHANGE", "User", cible.id, None,
                       f"{cible.role} -> {payload['role']}")
        cible.role = payload["role"]
    if payload.get("password"):
        valider_mot_de_passe(payload["password"], cible.email, cible.full_name)
        cible.password_hash = hash_password(payload["password"])
        cible.must_change_password = True
        cible.password_changed_at = datetime.utcnow()
        cible.tokens_valid_from = datetime.utcnow()
        log_action(db, user, "PASSWORD_RESET", "User", cible.id, None)
    db.commit()
    return _profil(cible)


@router.delete("/utilisateurs/{user_id}")
def supprimer_utilisateur(user_id: int, db: Session = Depends(get_db),
                          user: User = Depends(is_admin)):
    cible = db.get(User, user_id)
    if not cible:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if cible.id == user.id:
        raise HTTPException(status_code=400,
                            detail="Vous ne pouvez pas supprimer votre propre compte.")
    if cible.role == "admin" and db.query(User).filter(
            User.role == "admin", User.is_active.is_(True)).count() <= 1:
        raise HTTPException(status_code=400,
                            detail="Ce compte est le dernier administrateur actif.")
    db.query(ProjectMember).filter(ProjectMember.user_id == cible.id).delete()
    db.query(ApiKey).filter(ApiKey.user_id == cible.id).delete()
    log_action(db, user, "DELETE_USER", "User", user_id, None, cible.email)
    db.delete(cible)
    db.commit()
    return {"deleted": user_id}


# ---------------------------------------------------------------------------
# Affectation des utilisateurs aux projets
# ---------------------------------------------------------------------------
@router.get("/utilisateurs/{user_id}/projets")
def projets_de_lutilisateur(user_id: int, db: Session = Depends(get_db),
                            user: User = Depends(is_admin)):
    membres = db.query(ProjectMember).filter(ProjectMember.user_id == user_id).all()
    projets = {p.id: p for p in db.query(Project).all()}
    return [{"project_id": m.project_id, "role": m.role,
             "code": projets[m.project_id].code if m.project_id in projets else None,
             "titre": projets[m.project_id].title if m.project_id in projets else None}
            for m in membres]


@router.post("/utilisateurs/{user_id}/projets")
def affecter_projet(user_id: int, payload: Dict[str, Any], db: Session = Depends(get_db),
                    user: User = Depends(is_admin)):
    cible = db.get(User, user_id)
    projet = db.get(Project, payload.get("project_id"))
    if not cible or not projet:
        raise HTTPException(status_code=404, detail="Utilisateur ou projet introuvable.")
    existante = db.query(ProjectMember).filter(
        ProjectMember.user_id == user_id, ProjectMember.project_id == projet.id).first()
    if existante:
        existante.role = str(payload.get("role") or existante.role)[:60]
    else:
        db.add(ProjectMember(user_id=user_id, project_id=projet.id,
                             role=str(payload.get("role") or "lecteur")[:60]))
    log_action(db, user, "GRANT_PROJECT", "User", user_id, projet.id, projet.code)
    db.commit()
    return {"message": f"Accès au projet « {projet.code} » accordé."}


@router.delete("/utilisateurs/{user_id}/projets/{project_id}")
def retirer_projet(user_id: int, project_id: int, db: Session = Depends(get_db),
                   user: User = Depends(is_admin)):
    db.query(ProjectMember).filter(ProjectMember.user_id == user_id,
                                   ProjectMember.project_id == project_id).delete()
    log_action(db, user, "REVOKE_PROJECT", "User", user_id, project_id)
    db.commit()
    return {"deleted": project_id}


# ---------------------------------------------------------------------------
# Clés d'accès en lecture seule
# ---------------------------------------------------------------------------
@router.get("/cles")
def liste_cles(db: Session = Depends(get_db), user: User = Depends(current_user)):
    cles = db.query(ApiKey).filter(ApiKey.user_id == user.id).order_by(
        ApiKey.created_at.desc()).all()
    return [{"id": c.id, "label": c.label, "prefixe": c.prefix, "portee": c.scope,
             "project_id": c.project_id, "revoquee": c.revoked,
             "expire_le": c.expires_at.isoformat(timespec="seconds") if c.expires_at else None,
             "derniere_utilisation": c.last_used_at.isoformat(timespec="seconds")
             if c.last_used_at else None} for c in cles]


@router.post("/cles", status_code=201)
def creer_cle(payload: Dict[str, Any], db: Session = Depends(get_db),
              user: User = Depends(current_user)):
    """Crée une clé de lecture pour un connecteur externe (Power BI, Excel, script)."""
    if db.query(ApiKey).filter(ApiKey.user_id == user.id,
                               ApiKey.revoked.is_(False)).count() >= 10:
        raise HTTPException(status_code=422,
                            detail="Dix clés actives au maximum. Révoquez-en une avant d'en "
                                   "créer une nouvelle.")
    cle, secret = creer_cle_api(db, user, payload.get("label", "Connecteur"),
                                payload.get("project_id"), int(payload.get("jours", 90)))
    log_action(db, user, "CREATE_API_KEY", "ApiKey", cle.id, cle.project_id, cle.label)
    db.commit()
    return {
        "id": cle.id, "label": cle.label, "prefixe": cle.prefix,
        "expire_le": cle.expires_at.isoformat(timespec="seconds"),
        "cle": secret,
        "avertissement": "Cette clé n'est affichée qu'une seule fois : conservez-la dans un "
                         "gestionnaire de mots de passe. Elle donne un accès en lecture aux "
                         "données du projet et doit être révoquée dès qu'elle n'est plus utile.",
    }


@router.delete("/cles/{cle_id}")
def revoquer_cle(cle_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    cle = db.get(ApiKey, cle_id)
    if not cle or cle.user_id != user.id:
        raise HTTPException(status_code=404, detail="Clé introuvable.")
    cle.revoked = True
    log_action(db, user, "REVOKE_API_KEY", "ApiKey", cle.id, cle.project_id)
    db.commit()
    return {"revoquee": cle_id}
