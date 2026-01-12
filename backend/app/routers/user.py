import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

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
    
    # Note : Le validateur dans schemas.py gérera la conversion String -> Dict
    # si profile_data est une string venant de la BDD.
        
    return current_user

@router.post("/complete", response_model=schemas.UserResponse)
async def complete_profile(
    profile_update: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Sauvegarde le profil complet.
    Logic : Input (Dict) -> DB (String) -> Output (Dict)
    """
    try:
        # 1. Récupération des données brutes (Dict)
        data_dict = profile_update.profile_data
        
        # 2. Sérialisation pour la BDD (Dict -> String)
        # On stocke une chaîne de caractères car la colonne SQL est TEXT
        json_str = json.dumps(data_dict)
        current_user.profile_data = json_str
        
        # 3. Mise à jour des champs relationnels (User table)
        if "basic_info" in data_dict:
            basic = data_dict["basic_info"]
            
            # Mise à jour email si fourni et non vide
            if "email" in basic and basic["email"]:
                current_user.email = basic["email"]
            
            # Mise à jour pseudo si fourni et non vide
            if "pseudo" in basic and basic["pseudo"]:
                current_user.username = basic["pseudo"]

        # Sauvegarde SQL effective
        db.commit()
        db.refresh(current_user) # Ici, current_user.profile_data redevient une String venant de la BDD
        
        # 4. [FIX CRITIQUE] Préparation de la Réponse pour Pydantic
        # Pydantic attend un Dict pour générer le JSON de réponse propre.
        # On écrase temporairement la propriété sur l'objet Python avec le Dictionnaire d'origine.
        # Cela garantit que le retour API est un JSON pur, et non une string JSON.
        current_user.profile_data = data_dict
        
        return current_user
        
    except Exception as e:
        db.rollback()
        # On log l'erreur pour le debug serveur
        print(f"🔥 ERREUR CRITIQUE SAVE PROFILE: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur sauvegarde profil : {str(e)}"
        )

# --- SUPPORT LEGACY (Optionnel, conservé pour compatibilité existante) ---
# Ces routes seront désormais préfixées par /api/v1/profiles aussi via le main.py

@router.post("/sections/{section}")
async def update_profile_section(
    section: str,
    section_data: schemas.ProfileSectionUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Mise à jour partielle d'une section.
    Gère la conversion JSON <-> Dict pour éviter les crashs sur la colonne TEXT.
    """
    try:
        # 1. Chargement sécurisé (String -> Dict)
        current_data = {}
        raw_data = current_user.profile_data
        
        if raw_data:
            if isinstance(raw_data, dict):
                current_data = raw_data
            elif isinstance(raw_data, str):
                try:
                    current_data = json.loads(raw_data)
                except json.JSONDecodeError:
                    current_data = {}
        
        # 2. Mise à jour de la section
        current_data[section] = section_data.section_data
        
        # 3. Sauvegarde sécurisée (Dict -> String)
        current_user.profile_data = json.dumps(current_data)
        
        db.commit()
        
        return {
            "status": "success",
            "section": section,
            "updated_data": section_data.section_data
        }
    except Exception as e:
        db.rollback()
        print(f"🔥 ERREUR LEGACY SECTION: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))