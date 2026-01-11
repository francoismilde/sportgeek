from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from typing import Dict, Any

from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user
from app.services.coach_logic import CoachLogic

router = APIRouter(
    prefix="/user",
    tags=["User Profile"]
)

# --- UTILITAIRES DE MIGRATION ---

def _migrate_legacy_to_v2(user: sql_models.User, db: Session) -> sql_models.AthleteProfile:
    """
    Fonction Helper : Convertit les données Legacy (string) en Profil V2 (table).
    Assure la continuité de service (Zéro Régression).
    """
    profile_data = {}
    if user.profile_data:
        try:
            profile_data = json.loads(user.profile_data)
        except:
            pass # JSON corrompu ou vide
    
    # 1. Création de la structure V2
    new_profile = sql_models.AthleteProfile(
        user_id=user.id,
        basic_info=json.dumps({
            "pseudo": user.username,
            "email": user.email,
            **profile_data.get('basic_info', {})
        }),
        physical_metrics=json.dumps(profile_data.get('physical_metrics', {})),
        sport_context=json.dumps(profile_data.get('sport_context', {})),
        training_preferences=json.dumps(profile_data.get('training_preferences', {})),
        goals=json.dumps(profile_data.get('goals', {})),
        constraints=json.dumps(profile_data.get('constraints', {})),
        injury_prevention=json.dumps(profile_data.get('injury_prevention', {})),
        performance_baseline=json.dumps(profile_data.get('performance_baseline', {}))
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    # 2. Initialisation de la mémoire Coach par défaut
    if not new_profile.coach_memory:
        memory = CoachLogic.initialize_memory(new_profile)
        db.add(memory)
        db.commit()
        
    return new_profile

# --- ENDPOINTS ---

@router.get("/profile", response_model=schemas.AthleteProfileResponse)
async def get_profile_v2(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le profil athlète structuré (V2).
    Si le profil V2 n'existe pas encore, tente une migration automatique depuis les données Legacy.
    """
    # Cas 1 : Le profil V2 existe déjà
    if current_user.athlete_profile:
        return current_user.athlete_profile
    
    # Cas 2 : Pas de V2, mais des données Legacy existent (Migration Lazy)
    if current_user.profile_data:
        migrated_profile = _migrate_legacy_to_v2(current_user, db)
        return migrated_profile
    
    # Cas 3 : Nouvel utilisateur vide -> Création profil vierge
    empty_profile = sql_models.AthleteProfile(user_id=current_user.id)
    db.add(empty_profile)
    db.commit()
    db.refresh(empty_profile)
    
    # Init mémoire coach vierge
    memory = CoachLogic.initialize_memory(empty_profile)
    db.add(memory)
    db.commit()
    
    return empty_profile

@router.put("/profile", response_model=schemas.AthleteProfileResponse)
async def update_profile_v2(
    profile_update: schemas.AthleteProfileCreate, # On utilise Create car il contient tous les champs
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour le profil athlète.
    Synchronise AUTOMATIQUEMENT les données vers le système Legacy pour compatibilité.
    """
    # 1. Récupération ou Création (via Migration)
    profile = current_user.athlete_profile
    if not profile:
        profile = _migrate_legacy_to_v2(current_user, db)
    
    # 2. Mise à jour des colonnes V2 (JSONb)
    # On convertit les modèles Pydantic en dict, puis en JSON string pour la DB
    if profile_update.basic_info:
        profile.basic_info = json.dumps(profile_update.basic_info.dict())
    if profile_update.physical_metrics:
        profile.physical_metrics = json.dumps(profile_update.physical_metrics.dict())
    if profile_update.sport_context:
        profile.sport_context = json.dumps(profile_update.sport_context.dict())
    if profile_update.training_preferences:
        profile.training_preferences = json.dumps(profile_update.training_preferences.dict())
    
    # Champs dict directs
    if profile_update.goals:
        profile.goals = json.dumps(profile_update.goals)
    if profile_update.constraints:
        profile.constraints = json.dumps(profile_update.constraints)
    if profile_update.injury_prevention:
        profile.injury_prevention = json.dumps(profile_update.injury_prevention)
    if profile_update.performance_baseline:
        profile.performance_baseline = json.dumps(profile_update.performance_baseline)

    # 3. SYNC LEGACY (Anti-Régression)
    # On reconstruit un gros JSON plat pour l'ancien champ 'profile_data'
    legacy_data = {
        "basic_info": json.loads(profile.basic_info) if profile.basic_info else {},
        "physical_metrics": json.loads(profile.physical_metrics) if profile.physical_metrics else {},
        "sport_context": json.loads(profile.sport_context) if profile.sport_context else {},
        "training_preferences": json.loads(profile.training_preferences) if profile.training_preferences else {},
        "goals": json.loads(profile.goals) if profile.goals else {},
        "constraints": json.loads(profile.constraints) if profile.constraints else {},
        "injury_prevention": json.loads(profile.injury_prevention) if profile.injury_prevention else {},
        "performance_baseline": json.loads(profile.performance_baseline) if profile.performance_baseline else {}
    }
    current_user.profile_data = json.dumps(legacy_data)

    db.commit()
    db.refresh(profile)
    
    return profile

@router.post("/profile/sections/{section}")
async def update_profile_section(
    section: str,
    section_data: schemas.ProfileSectionUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour une section spécifique du profil (Optimisation Mobile).
    Évite d'envoyer tout le profil pour changer juste le poids.
    """
    valid_sections = [
        'basic_info', 'physical_metrics', 'sport_context',
        'training_preferences', 'goals', 'constraints',
        'injury_prevention', 'performance_baseline'
    ]
    
    if section not in valid_sections:
        raise HTTPException(
            status_code=400,
            detail=f"Section invalide. Options: {', '.join(valid_sections)}"
        )
    
    # 1. Récupération / Migration
    profile = current_user.athlete_profile
    if not profile:
        profile = _migrate_legacy_to_v2(current_user, db)
    
    # 2. Mise à jour de la section spécifique
    setattr(profile, section, json.dumps(section_data.section_data))
    
    # 3. Sync Legacy (nécessaire même pour une update partielle)
    legacy_data = {}
    if current_user.profile_data:
        try:
            legacy_data = json.loads(current_user.profile_data)
        except:
            pass
    
    legacy_data[section] = section_data.section_data
    current_user.profile_data = json.dumps(legacy_data)
    
    db.commit()
    
    return {
        "status": "success",
        "section": section,
        "updated_data": section_data.section_data
    }

# --- SUPPORT LEGACY (Compatibilité Frontend V1) ---

@router.get("/profile/complete", response_model=schemas.AthleteProfileResponse)
async def get_profile_complete_alias(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias pour compatibilité avec l'ancien routeur profiles.py"""
    return await get_profile_v2(current_user, db)

@router.post("/profile/complete", response_model=schemas.AthleteProfileResponse)
async def create_profile_complete_alias(
    profile_data: schemas.AthleteProfileCreate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """Alias pour compatibilité avec l'ancien routeur profiles.py"""
    return await update_profile_v2(profile_data, db, current_user)  