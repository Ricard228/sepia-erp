"""Point d'entrée de la plateforme SEPIA (FastAPI)."""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import (APP_LONG_NAME, APP_NAME, APP_VERSION, DATABASE_URL, EST_PRODUCTION,
                     SEED_DEMO)
from .database import Base, SessionLocal, assurer_schema, engine
from .middleware import EntetesSecurite, LimitationDebit, TailleRequete, enregistrer_erreur
from .routers import auth, entities, evaluations, exports, imports, powerbi, projects
from .seed import initialiser

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_STATIQUE = os.path.join(RACINE, "static")

app = FastAPI(
    title=f"{APP_NAME} — {APP_LONG_NAME}",
    description=(
        "API de la plateforme de planification et de suivi-évaluation des projets et "
        "programmes de développement : cadre logique, indicateurs, cadre de rendement, "
        "risques et hypothèses, chronogramme, PTBA, fiches de collecte et XLSForm, "
        "tableaux de bord et flux Power BI."
    ),
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# L'interface est servie par la même origine que l'API : aucune origine tierce
# n'a donc besoin d'y accéder. Autoriser « * » avec des cookies de session
# reviendrait à laisser n'importe quel site interroger la plateforme au nom de
# l'utilisateur connecté.
_origines = [o.strip() for o in os.getenv("SEPIA_CORS_ORIGINS", "").split(",") if o.strip()]
if _origines:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origines,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
        max_age=600,
    )

app.add_middleware(EntetesSecurite)
app.add_middleware(LimitationDebit)
app.add_middleware(TailleRequete)


@app.on_event("startup")
def demarrage() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    Base.metadata.create_all(bind=engine)
    assurer_schema()
    db = SessionLocal()
    try:
        initialiser(db, avec_demo=SEED_DEMO)
    finally:
        db.close()
    if not EST_PRODUCTION:
        logging.getLogger("sepia").warning(
            "Instance démarrée en mode développement : messages d'erreur détaillés, "
            "cookies non restreints à HTTPS. Définissez SEPIA_ENV=production avant "
            "toute mise en service.")


@app.exception_handler(Exception)
async def erreur_non_geree(request: Request, exc: Exception):
    return enregistrer_erreur(request, exc)


app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(entities.router)
app.include_router(evaluations.router)
app.include_router(imports.router)
app.include_router(exports.router)
app.include_router(powerbi.router)


@app.get("/api/sante", tags=["Système"])
def sante():
    """Sonde de disponibilité utilisée par Render."""
    moteur = "PostgreSQL" if DATABASE_URL.startswith("postgresql") else "SQLite"
    return {"statut": "operationnel", "application": APP_NAME, "version": APP_VERSION,
            "base_de_donnees": moteur}


if os.path.isdir(DOSSIER_STATIQUE):
    app.mount("/static", StaticFiles(directory=DOSSIER_STATIQUE), name="static")

    @app.get("/", include_in_schema=False)
    def accueil():
        return FileResponse(os.path.join(DOSSIER_STATIQUE, "index.html"))

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifeste():
        return FileResponse(os.path.join(DOSSIER_STATIQUE, "manifest.webmanifest"),
                            media_type="application/manifest+json")

    @app.get("/{chemin:path}", include_in_schema=False)
    def application_monopage(chemin: str):
        """Toute route non-API renvoie l'interface (navigation côté client).

        Les chemins commençant par /api restent en 404 afin que les erreurs de
        l'API ne soient pas masquées par la page d'accueil, et le service de
        fichiers est confiné au dossier statique (protection contre la
        traversée de répertoire).
        """
        if chemin.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Ressource API introuvable."})
        candidat = os.path.realpath(os.path.join(DOSSIER_STATIQUE, chemin))
        racine_statique = os.path.realpath(DOSSIER_STATIQUE)
        if chemin and candidat.startswith(racine_statique + os.sep) and os.path.isfile(candidat):
            return FileResponse(candidat)
        return FileResponse(os.path.join(DOSSIER_STATIQUE, "index.html"))
