from fastapi import APIRouter, HTTPException
from app.models.schemas import OneRepMaxRequest, OneRepMaxResponse
from app.domain import calculations

router = APIRouter(
    prefix="/performance",
    tags=["Performance & Metrics"]
)

@router.post("/1rm", response_model=OneRepMaxResponse)
async def compute_one_rep_max(payload: OneRepMaxRequest):
    """
    Calcule le 1RM (One Rep Max) estimé basé sur une performance.
    Sélectionne automatiquement la meilleure formule (Epley, Brzycki, Wathan).
    """
    try:
        result = calculations.calculate_1rm(payload.weight, payload.reps)
        
        return {
            "estimated_1rm": result["1rm"],
            "method_used": result["method"],
            "input_weight": payload.weight,
            "input_reps": payload.reps
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))