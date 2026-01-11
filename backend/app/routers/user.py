from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from typing import Dict, Any

from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/user",
    tags=["User Profile"]
)

# --- ENDPOINTS SIMPLIFIÉS (TITAN V2) ---

@router.get("/profile", response_model=schemas.UserResponse)
async def get_my_profile_data(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les données brutes de l'utilisateur (y compris le JSON profile_data).
    """
    # Si profile_data est null, on renvoie un dict vide
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
    Sauvegarde le profil complet envoyé par Flutter sans validation stricte.
    Écrase l'ancien JSON.
    """
    try:
        # On injecte directement le JSON reçu dans la colonne JSON de la BDD
        # Postgres/SQLite gèrent le stockage, nous on ne fait que passer le ballon.
        current_user.profile_data = profile_update.profile_data
        
        # Optionnel : Si tu veux aussi mettre à jour l'email s'il est présent dans le JSON
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
            detail=f"Erreur lors de la sauvegarde du profil : {str(e)}"
        )

# --- SUPPORT LEGACY / MIGRATION (Conservé pour Zéro Régression) ---
# Ces endpoints peuvent être utilisés par d'anciennes versions ou pour des updates partiels

@router.post("/profile/sections/{section}")
async def update_profile_section(
    section: str,
    section_data: schemas.ProfileSectionUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour une section spécifique du JSON profile_data.
    Utile pour changer juste le poids sans tout renvoyer.
    """
    try:
        # 1. Charger l'existant
        current_data = current_user.profile_data if current_user.profile_data else {}
        if isinstance(current_data, str): # Safety check si c'est encore une string
             try: current_data = json.loads(current_data)
             except: current_data = {}
        
        # 2. Mettre à jour la section
        current_data[section] = section_data.section_data
        
        # 3. Sauvegarder
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