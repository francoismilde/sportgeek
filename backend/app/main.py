from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# --- IMPORTS DES ROUTEURS ---
# On ajoute 'user' ici
from app.routers import performance, safety, auth, workouts, coach, user
from app.core.database import engine, Base

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE INIT ---
try:
    logger.info("Tentative de création des tables SQL...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables vérifiées/créées.")
except Exception as e:
    logger.error(f"ERREUR CRITIQUE DÉMARRAGE DB : {e}")

app = FastAPI(
    title="TitanFlow API",
    description="API Backend pour l'application TitanFlow",
    version="1.7.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(performance.router)
app.include_router(safety.router)
app.include_router(coach.router)
app.include_router(user.router) # <--- NOUVEAU ROUTEUR ENREGISTRÉ

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "active",
        "version": "1.7.0",
        "service": "TitanFlow Backend",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)