from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # On ajoute workouts dans les imports
    from app.routers import performance, safety, auth, workouts
    from app.core.database import engine, Base
    
    logger.info("Tentative de création des tables SQL...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées.")
except Exception as e:
    logger.error(f"ERREUR DÉMARRAGE : {e}")

app = FastAPI(
    title="TitanFlow API",
    description="API Backend pour l'application TitanFlow",
    version="1.4.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
app.include_router(auth.router)
app.include_router(workouts.router) # <--- NOUVEAU
app.include_router(performance.router)
app.include_router(safety.router)

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "active", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)