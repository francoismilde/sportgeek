from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# --- IMPORTS DES ROUTEURS ---
# C'est ici qu'il manquait 'auth' et 'workouts'
from app.routers import performance, safety, auth, workouts
from app.core.database import engine, Base

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE INIT ---
# Création des tables au démarrage (si elles n'existent pas)
try:
    logger.info("Tentative de création des tables SQL...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables vérifiées/créées.")
except Exception as e:
    logger.error(f"ERREUR CRITIQUE DÉMARRAGE DB : {e}")

app = FastAPI(
    title="TitanFlow API",
    description="API Backend pour l'application TitanFlow",
    version="1.5.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS (Pour autoriser le mobile et le web à se connecter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En prod, on restreindra ça, mais pour le MVP c'est OK
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
# On branche tous les câbles
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(performance.router)
app.include_router(safety.router)

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "active",
        "version": "1.5.0",
        "service": "TitanFlow Backend",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)