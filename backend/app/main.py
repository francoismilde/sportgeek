from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import performance, safety, auth
from app.core.database import engine, Base

# --- DATABASE INIT ---
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TitanFlow API",
    description="API Backend pour l'application TitanFlow",
    version="1.3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
app.include_router(auth.router)
app.include_router(performance.router)
app.include_router(safety.router)

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "active",
        "version": "1.3.0",
        "service": "TitanFlow Backend",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)