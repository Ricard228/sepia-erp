"""Protections transverses appliquées à toutes les requêtes.

Trois mécanismes complémentaires :
  * limitation du débit, pour qu'un client ne puisse ni saturer le service ni
    tenter des mots de passe en série ;
  * en-têtes de sécurité, qui cadrent ce que le navigateur s'autorise à faire de
    la page — notamment l'interdiction d'exécuter du script non prévu ;
  * gestion des erreurs, qui journalise le détail côté serveur et ne renvoie au
    client qu'un identifiant de corrélation.
"""
import logging
import time
import uuid
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import (EST_PRODUCTION, LIMITE_CONNEXIONS_PAR_MINUTE, LIMITE_EXPORTS_PAR_MINUTE,
                     LIMITE_REQUETES_PAR_MINUTE, TAILLE_MAX_TELEVERSEMENT)

logger = logging.getLogger("sepia.securite")

# Politique de sécurité du contenu : la page ne peut charger de script que
# depuis sa propre origine, ce qui neutralise l'injection d'un script distant.
# 'unsafe-inline' est nécessaire aux styles en attribut des graphiques SVG ;
# il n'est pas accordé aux scripts.
CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https://tile.openstreetmap.org; "
    "connect-src 'self'; "
    "font-src 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

ENTETES_SECURITE = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


class EntetesSecurite(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        reponse = await call_next(request)
        for cle, valeur in ENTETES_SECURITE.items():
            reponse.headers.setdefault(cle, valeur)
        if EST_PRODUCTION:
            reponse.headers.setdefault("Strict-Transport-Security",
                                       "max-age=31536000; includeSubDomains")
        # Les réponses de l'API ne doivent jamais être mises en cache par un
        # intermédiaire : elles contiennent des données de projet.
        if request.url.path.startswith("/api/"):
            reponse.headers.setdefault("Cache-Control", "no-store")
        return reponse


class LimitationDebit(BaseHTTPMiddleware):
    """Fenêtre glissante d'une minute, par adresse et par catégorie de route.

    La tentative de connexion et la génération de livrables ont leurs propres
    quotas : la première parce qu'elle est la cible des attaques par essais
    successifs, la seconde parce qu'elle est coûteuse en ressources.
    """

    def __init__(self, app):
        super().__init__(app)
        self._compteurs: Dict[str, Deque[float]] = defaultdict(deque)

    def _client(self, request: Request) -> str:
        # Derrière Render, l'adresse d'origine est transmise par l'en-tête.
        transmise = request.headers.get("x-forwarded-for", "")
        if transmise:
            return transmise.split(",")[0].strip()
        return request.client.host if request.client else "inconnu"

    def _quota(self, chemin: str) -> int:
        if chemin.startswith("/api/auth/login"):
            return LIMITE_CONNEXIONS_PAR_MINUTE
        if chemin.startswith("/api/exports") or chemin.startswith("/api/imports"):
            return LIMITE_EXPORTS_PAR_MINUTE
        return LIMITE_REQUETES_PAR_MINUTE

    async def dispatch(self, request: Request, call_next):
        chemin = request.url.path
        if not chemin.startswith("/api/") or chemin == "/api/sante":
            return await call_next(request)

        categorie = ("connexion" if chemin.startswith("/api/auth/login")
                     else "lourd" if chemin.startswith(("/api/exports", "/api/imports"))
                     else "general")
        cle = f"{self._client(request)}|{categorie}"
        quota = self._quota(chemin)
        maintenant = time.time()
        fenetre = self._compteurs[cle]
        while fenetre and maintenant - fenetre[0] > 60:
            fenetre.popleft()
        if len(fenetre) >= quota:
            attente = int(60 - (maintenant - fenetre[0])) + 1
            logger.warning("Débit dépassé (%s) sur %s", cle, chemin)
            return JSONResponse(
                status_code=429,
                content={"detail": f"Trop de requêtes. Réessayez dans {attente} seconde(s)."},
                headers={"Retry-After": str(attente)})
        fenetre.append(maintenant)

        # Purge périodique pour éviter que la table ne croisse indéfiniment.
        if len(self._compteurs) > 4000:
            for identifiant in [k for k, v in self._compteurs.items()
                                if not v or maintenant - v[-1] > 300]:
                self._compteurs.pop(identifiant, None)
        return await call_next(request)


class TailleRequete(BaseHTTPMiddleware):
    """Refuse un corps de requête surdimensionné avant même de le lire."""

    async def dispatch(self, request: Request, call_next):
        longueur = request.headers.get("content-length")
        if longueur and longueur.isdigit() and int(longueur) > TAILLE_MAX_TELEVERSEMENT:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Contenu trop volumineux : la limite est de "
                                   f"{TAILLE_MAX_TELEVERSEMENT // (1024 * 1024)} Mo."})
        return await call_next(request)


def enregistrer_erreur(request: Request, exc: Exception) -> JSONResponse:
    """Journalise l'erreur complète et ne renvoie qu'un identifiant de corrélation.

    Le message d'exception peut contenir des noms de tables, des chemins de
    fichiers ou des fragments de requête : autant d'indications précieuses pour
    qui cherche une faille. Le détail reste dans les journaux du serveur.
    """
    correlation = uuid.uuid4().hex[:12]
    logger.exception("Erreur %s sur %s %s", correlation, request.method, request.url.path)
    contenu = {
        "detail": "Une erreur interne est survenue. L'équipe technique dispose du détail "
                  "dans les journaux du serveur.",
        "reference": correlation,
    }
    if not EST_PRODUCTION:
        contenu["diagnostic"] = f"{type(exc).__name__} — {exc}"
    return JSONResponse(status_code=500, content=contenu)
