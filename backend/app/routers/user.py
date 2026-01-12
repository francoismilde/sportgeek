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
    
    # SQLAlchemy avec type JSON renvoie déjà un Dict, donc pas de parsing nécessaire ici.
    # Le validateur Pydantic (schemas.py) est là en sécurité si jamais c'était une string.
        
    return current_user

@router.post("/complete", response_model=schemas.UserResponse)
async def complete_profile(
    profile_update: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Sauvegarde le profil complet.
    Logic : Input (Dict) -> DB (JSON Type - Auto Serialize) -> Output (Dict)
    """
    try:
        # 1. Récupération des données brutes (Dict)
        data_dict = profile_update.profile_data
        
        # 2. [CORRECTION] Assignation DIRECTE du Dictionnaire
        # Le modèle SQL 'User' utilise le type JSON, SQLAlchemy gère la sérialisation.
        # On passe directement le dictionnaire Python.
        current_user.profile_data = data_dict
        
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
        db.refresh(current_user)
        
        # 4. Retour
        # SQLAlchemy a mis à jour current_user.profile_data qui est maintenant un Dict (grâce au type JSON).
        # Pydantic (UserResponse) attend un Dict. Tout est aligné.
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
    Adapté pour le type JSON de SQLAlchemy.
    """
    try:
        # 1. Chargement des données existantes
        # Avec le type JSON, SQLAlchemy nous renvoie directement un Dict ou None
        raw_data = current_user.profile_data
        
        current_data = {}
        if raw_data:
            if isinstance(raw_data, dict):
                current_data = raw_data.copy() # Copie pour éviter les effets de bord
            elif isinstance(raw_data, str):
                # Sécurité au cas où d'anciennes données String traînent
                try:
                    current_data = json.loads(raw_data)
                except json.JSONDecodeError:
                    current_data = {}
        
        # 2. Mise à jour de la section
        current_data[section] = section_data.section_data
        
        # 3. Sauvegarde (Direct Dict -> JSON Column)
        current_user.profile_data = current_data
        
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