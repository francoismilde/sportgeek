"""
Routeur pour la gestion des profils athlètes enrichis
"""
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import sql_models, schemas
from app.services.coach_memory.service import initialize_coach_memory
from app.validators.athlete_profile_validators import validate_athlete_profile

router = APIRouter(
    prefix="/api/v1/profiles",
    tags=["Athlete Profiles v2"]
)

@router.post("/complete", response_model=schemas.AthleteProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_complete_profile(
    profile_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Crée un profil athlète complet via le wizard
    """
    # Vérifier si l'utilisateur a déjà un profil
    existing_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un profil existe déjà pour cet utilisateur"
        )
    
    # Valider les données du profil
    try:
        validate_athlete_profile(profile_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Créer le profil
    athlete_profile = sql_models.AthleteProfile(
        user_id=current_user.id,
        basic_info=json.dumps(profile_data.get('basic_info', {})),
        physical_metrics=json.dumps(profile_data.get('physical_metrics', {})),
        sport_context=json.dumps(profile_data.get('sport_context', {})),
        performance_baseline=json.dumps(profile_data.get('performance_baseline', {})),
        injury_prevention=json.dumps(profile_data.get('injury_prevention', {})),
        training_preferences=json.dumps(profile_data.get('training_preferences', {})),
        goals=json.dumps(profile_data.get('goals', {})),
        constraints=json.dumps(profile_data.get('constraints', {}))
    )
    
    try:
        db.add(athlete_profile)
        db.commit()
        db.refresh(athlete_profile)
        
        # Calculer le pourcentage de complétion
        athlete_profile.completion_percentage = athlete_profile.calculate_completion()
        athlete_profile.is_complete = athlete_profile.completion_percentage >= 80
        db.commit()
        
        # Initialiser la mémoire du coach
        initialize_coach_memory(athlete_profile, db)
        
        return athlete_profile
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur d'intégrité des données"
        )

@router.get("/{profile_id}", response_model=schemas.AthleteProfileResponse)
async def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère un profil athlète par ID
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé"
        )
    
    return profile

@router.put("/{profile_id}", response_model=schemas.AthleteProfileResponse)
async def update_profile(
    profile_id: int,
    profile_update: schemas.AthleteProfileUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour complètement un profil
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé"
        )
    
    # Mettre à jour chaque section
    update_dict = profile_update.dict(exclude_unset=True)
    for section, data in update_dict.items():
        if data is not None:
            setattr(profile, section, json.dumps(data))
    
    # Recalculer la complétion
    profile.completion_percentage = profile.calculate_completion()
    profile.is_complete = profile.completion_percentage >= 80
    
    db.commit()
    db.refresh(profile)
    
    return profile

@router.patch("/{profile_id}/section/{section_name}")
async def update_profile_section(
    profile_id: int,
    section_name: str,
    section_update: schemas.ProfileSectionUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour une section spécifique du profil
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé"
        )
    
    # Vérifier que la section existe
    valid_sections = [
        'basic_info', 'physical_metrics', 'sport_context',
        'performance_baseline', 'injury_prevention',
        'training_preferences', 'goals', 'constraints'
    ]
    
    if section_name not in valid_sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section invalide. Options: {', '.join(valid_sections)}"
        )
    
    # Mettre à jour la section
    setattr(profile, section_name, json.dumps(section_update.section_data))
    
    # Recalculer la complétion
    profile.completion_percentage = profile.calculate_completion()
    profile.is_complete = profile.completion_percentage >= 80
    
    db.commit()
    
    return {
        "message": "Section mise à jour avec succès",
        "completion_percentage": profile.completion_percentage,
        "is_complete": profile.is_complete
    }

@router.post("/{profile_id}/metrics")
async def add_daily_metrics(
    profile_id: int,
    metrics: schemas.DailyMetrics,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Ajoute des métriques quotidiennes au profil
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé"
        )
    
    # Ici, on pourrait stocker les métriques dans une table séparée
    # Pour l'instant, on les ajoute aux métriques physiques
    physical_metrics = json.loads(profile.physical_metrics) if profile.physical_metrics else {}
    
    if 'daily_metrics' not in physical_metrics:
        physical_metrics['daily_metrics'] = []
    
    physical_metrics['daily_metrics'].append(metrics.dict())
    
    # Garder seulement les 30 derniers jours
    if len(physical_metrics['daily_metrics']) > 30:
        physical_metrics['daily_metrics'] = physical_metrics['daily_metrics'][-30:]
    
    # Mettre à jour les métriques agrégées
    if metrics.resting_heart_rate:
        physical_metrics['resting_heart_rate'] = metrics.resting_heart_rate
        physical_metrics['last_updated'] = metrics.date
    
    profile.physical_metrics = json.dumps(physical_metrics)
    db.commit()
    
    return {"message": "Métriques quotidiennes enregistrées"}

@router.post("/{profile_id}/goals", status_code=status.HTTP_201_CREATED)
async def add_goal(
    profile_id: int,
    goal_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Ajoute un nouvel objectif au profil
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé"
        )
    
    goals = json.loads(profile.goals) if profile.goals else {"secondary_goals": [], "milestones": []}
    
    if goal_data.get('is_primary', False):
        goals['primary_goal'] = goal_data.get('description', '')
        goals['target_date'] = goal_data.get('target_date')
        goals['target_metrics'] = goal_data.get('target_metrics', {})
    else:
        if 'secondary_goals' not in goals:
            goals['secondary_goals'] = []
        goals['secondary_goals'].append(goal_data.get('description', ''))
    
    profile.goals = json.dumps(goals)
    db.commit()
    
    return {"message": "Objectif ajouté avec succès"}

@router.put("/{profile_id}/goals/{goal_id}/progress")
async def update_goal_progress(
    profile_id: int,
    goal_id: str,  # Pour les objectifs principaux: "primary", pour secondaires: index
    progress: schemas.GoalProgressUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour la progression d'un objectif
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé"
        )
    
    goals = json.loads(profile.goals) if profile.goals else {}
    
    if goal_id == "primary":
        if 'milestones' not in goals:
            goals['milestones'] = []
        
        goals['milestones'].append({
            "date": progress.progress_note.split(" - ")[0] if progress.progress_note else "",
            "description": progress.progress_note or f"Progression: {progress.progress_value}%",
            "progress": progress.progress_value,
            "achieved": progress.achieved
        })
    else:
        # Pour les objectifs secondaires, on pourrait avoir une structure différente
        pass
    
    profile.goals = json.dumps(goals)
    db.commit()
    
    return {"message": "Progression mise à jour"}

@router.post("/{profile_id}/import")
async def import_external_data(
    profile_id: int,
    import_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Importe des données depuis des sources externes (Strava, Garmin, etc.)
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé"
        )
    
    source = import_data.get('source', '').lower()
    data = import_data.get('data', {})
    
    if source == 'strava':
        # Importer les données Strava
        if 'weight' in data:
            physical_metrics = json.loads(profile.physical_metrics) if profile.physical_metrics else {}
            physical_metrics['weight'] = data['weight']
            profile.physical_metrics = json.dumps(physical_metrics)
    
    elif source == 'garmin':
        # Importer les données Garmin
        if 'resting_heart_rate' in data:
            physical_metrics = json.loads(profile.physical_metrics) if profile.physical_metrics else {}
            physical_metrics['resting_heart_rate'] = data['resting_heart_rate']
            profile.physical_metrics = json.dumps(physical_metrics)
    
    elif source == 'whoop':
        # Importer les données Whoop
        if 'recovery' in data:
            physical_metrics = json.loads(profile.physical_metrics) if profile.physical_metrics else {}
            physical_metrics['hrv_baseline'] = data.get('hrv', physical_metrics.get('hrv_baseline'))
            profile.physical_metrics = json.dumps(physical_metrics)
    
    db.commit()
    
    return {
        "message": f"Données importées depuis {source}",
        "imported_fields": list(data.keys())
    }

@router.get("/{profile_id}/completion")
async def get_profile_completion(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère le statut de complétion du profil
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil non trouvé"
        )
    
    # Calculer les sections manquantes
    sections = {
        'basic_info': profile.basic_info,
        'physical_metrics': profile.physical_metrics,
        'sport_context': profile.sport_context,
        'performance_baseline': profile.performance_baseline,
        'injury_prevention': profile.injury_prevention,
        'training_preferences': profile.training_preferences,
        'goals': profile.goals,
        'constraints': profile.constraints
    }
    
    missing_sections = []
    for name, value in sections.items():
        if not value or value == '{}' or value == 'null':
            missing_sections.append(name)
    
    return {
        "completion_percentage": profile.completion_percentage,
        "is_complete": profile.is_complete,
        "missing_sections": missing_sections,
        "total_sections": 8,
        "completed_sections": 8 - len(missing_sections)
    }
