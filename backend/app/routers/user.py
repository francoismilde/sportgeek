from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user

# 🚨 CORRECTIF ROUTING : On retire le préfixe ici.
# Il sera injecté depuis le main.py pour plus de contrôle.
router = APIRouter()

# --- ENDPOINTS PROFIL (Nouvelle Route: /api/v1/profiles/...) ---

@router.get("/me", response_model=schemas.UserResponse)
async def get_my_profile_data(
    current_user: sql_models.User = Depends(get_current_user),
):
    """
    Récupère le profil connecté.
    URL Finale : GET /api/v1/profiles/me
    """
    if current_user.profile_data is None:
        current_user.profile_data = {}
    return current_user

@router.post("/complete", response_model=schemas.UserResponse)
async def complete_profile(
    profile_update: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Sauvegarde le profil complet (JSON).
    URL Finale : POST /api/v1/profiles/complete
    """
    try:
        # On injecte le JSON brut reçu du frontend
        current_user.profile_data = profile_update.profile_data
        
        # Mise à jour du pseudo/email si présents dans le JSON (synchro champs User)
        if "basic_info" in profile_update.profile_data:
            basic = profile_update.profile_data["basic_info"]
            if "email" in basic and basic["email"]:
                current_user.email = basic["email"]
            if "pseudo" in basic and basic["pseudo"]:
                current_user.username = basic["pseudo"]

        db.commit()
        db.refresh(current_user)
        return current_user
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur sauvegarde profil : {str(e)}"
        )

# --- SUPPORT LEGACY (Optionnel, conservé si besoin de compatibilité) ---
# Ces routes seront désormais préfixées par /api/v1/profiles aussi.
# Ex: POST /api/v1/profiles/sections/basic_info

@router.post("/sections/{section}")
async def update_profile_section(
    section: str,
    section_data: schemas.ProfileSectionUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Mise à jour partielle d'une section.
    """
    try:
        current_data = current_user.profile_data if current_user.profile_data else {}
        # Safety check type
        if not isinstance(current_data, dict):
            current_data = {}
        
        current_data[section] = section_data.section_data
        current_user.profile_data = current_data
        
        db.commit()
        
        return {
            "status": "success",
            "section": section,
            "updated_data": section_data.section_data
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))