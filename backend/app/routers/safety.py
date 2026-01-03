from fastapi import APIRouter, HTTPException
from app.models.schemas import ACWRRequest, ACWRResponse
from app.domain import safety

router = APIRouter(
    prefix="/safety",
    tags=["Safety & Prevention"]
)

@router.post("/acwr", response_model=ACWRResponse)
async def compute_acwr_metrics(payload: ACWRRequest):
    """
    Calcule le Ratio Aigu/Chronique (ACWR) pour prévenir les blessures.
    Envoie l'historique des séances (Date, Durée, RPE).
    Retourne le statut de risque (Optimal, Surcharge, Danger).
    """
    try:
        # Conversion des modèles Pydantic en liste de dicts pour Pandas
        history_dicts = [log.dict() for log in payload.history]
        
        result = safety.calculate_acwr(history_dicts)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))