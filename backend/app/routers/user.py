from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user
import json

router = APIRouter(
    prefix="/user",
    tags=["User Profile"]
)

@router.get("/profile", response_model=schemas.UserProfileUpdate)
async def get_profile(
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère le profil complet de l'utilisateur (JSON).
    """
    if not current_user.profile_data:
        return {"profile_data": {}}
    
    try:
        # On convertit la string stockée en BDD en dictionnaire
        data = json.loads(current_user.profile_data)
        return {"profile_data": data}
    except:
        return {"profile_data": {}}

@router.put("/profile")
async def update_profile(
    profile: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Sauvegarde le profil complet (Age, Benchmarks, Planning...).
    """
    try:
        # On convertit le dictionnaire reçu en string pour le stockage SQL
        json_str = json.dumps(profile.profile_data)
        current_user.profile_data = json_str
        
        db.commit()
        db.refresh(current_user)
        return {"message": "Profil mis à jour avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde: {str(e)}")