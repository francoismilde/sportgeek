from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/user",
    tags=["User Profile"]
)

# --- ENDPOINTS PROFIL FLEXIBLE (JSON) ---

@router.get("/profile", response_model=schemas.UserResponse)
async def get_my_profile_data(
    current_user: sql_models.User = Depends(get_current_user),
):
    """
    Récupère le profil. Pas de requête DB complexe, tout est dans l'user.
    """
    # Sécurité : on s'assure que c'est un dict vide et pas None
    if current_user.profile_data is None:
        current_user.profile_data = {}
    return current_user

@router.post("/profile/complete", response_model=schemas.UserResponse)
async def update_profile_complete(
    profile_update: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Sauvegarde le profil complet (JSON).
    """
    try:
        # On injecte le JSON brut
        current_user.profile_data = profile_update.profile_data
        
        # Mise à jour de l'email si présent (pour le login)
        if "basic_info" in profile_update.profile_data:
            basic = profile_update.profile_data["basic_info"]
            if "email" in basic and basic["email"]:
                current_user.email = basic["email"]

        db.commit()
        db.refresh(current_user)
        return current_user
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur sauvegarde profil : {str(e)}"
        )