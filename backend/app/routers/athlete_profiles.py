"""
Routeur unifié pour la gestion des profils athlètes
Gère toutes les routes /api/v1/profiles/*
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import sql_models, schemas
from app.services.coach_memory.service import initialize_coach_memory
from app.validators.athlete_profile_validators import validate_athlete_profile

# Configuration du Logger pour le debugging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    tags=["Profiles"]  # Tags unifiés
)

def transform_mobile_performance_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforme les données brutes du mobile en format API compatible.
    """
    if not raw_data:
        return {}
    
    # Nettoyer d'abord les valeurs vides, nulles ou invalides
    cleaned_data = {}
    for key, value in raw_data.items():
        # Filtrer les valeurs vraiment vides
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        if value == 0 or value == "0" or value == 0.0:
            continue
        if value == "null" or value == "undefined":
            continue
        
        cleaned_data[key] = value
    
    transformed = {}
    
    # 1. Extraire les valeurs numériques des résultats formatés
    if cleaned_data.get('run_vma_est'):
        try:
            match = re.search(r'(\d+\.?\d*)', str(cleaned_data['run_vma_est']))
            if match:
                vma_value = float(match.group(1))
                transformed['run_vma'] = vma_value
                # Optionnel: calculer le temps 5k équivalent
                if vma_value > 0:
                    transformed['running_time_5k'] = int(5000 / (vma_value * 1000/3600))
        except Exception as e:
            logger.debug(f"Erreur extraction run_vma_est: {e}")
    
    if cleaned_data.get('cycling_ftp_est'):
        try:
            match = re.search(r'(\d+\.?\d*)', str(cleaned_data['cycling_ftp_est']))
            if match:
                transformed['cycling_ftp'] = int(float(match.group(1)))
        except Exception as e:
            logger.debug(f"Erreur extraction cycling_ftp_est: {e}")
    
    if cleaned_data.get('swim_css_est'):
        try:
            match = re.search(r'(\d+):(\d+)', str(cleaned_data['swim_css_est']))
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                transformed['swimming_time_200m'] = minutes * 60 + seconds
        except Exception as e:
            logger.debug(f"Erreur extraction swim_css_est: {e}")
    
    # 2. Calculer les valeurs dérivées à partir des inputs bruts
    # Course à pied - Calcul VMA/CS
    try:
        required_fields = ['run_short_dist', 'run_short_min', 'run_short_sec', 
                          'run_long_dist', 'run_long_min', 'run_long_sec']
        
        # Vérifier que tous les champs requis sont présents et valides
        fields_present = all(k in cleaned_data for k in required_fields)
        fields_valid = all(cleaned_data.get(k) not in [None, "", 0, 0.0] for k in required_fields)
        
        if fields_present and fields_valid:
            d1 = float(cleaned_data['run_short_dist'])
            t1 = float(cleaned_data['run_short_min']) * 60 + float(cleaned_data['run_short_sec'])
            d2 = float(cleaned_data['run_long_dist'])
            t2 = float(cleaned_data['run_long_min']) * 60 + float(cleaned_data['run_long_sec'])
            
            if t2 > t1 and d2 > d1:
                cs_mps = (d2 - d1) / (t2 - t1)
                vma_kmh = cs_mps * 3.6
                if 'run_vma' not in transformed:
                    transformed['run_vma'] = round(vma_kmh, 1)
                # Convertir en temps 5k pour compatibilité API
                if vma_kmh > 0 and 'running_time_5k' not in transformed:
                    transformed['running_time_5k'] = int(5000 / (vma_kmh * 1000/3600))
    except Exception as e:
        logger.debug(f"Calcul running non effectué: {e}")
    
    # Vélo - Calcul FTP/CP
    try:
        required_fields = ['bike_short_min', 'bike_short_sec', 'bike_short_watts',
                          'bike_long_min', 'bike_long_sec', 'bike_long_watts']
        
        fields_present = all(k in cleaned_data for k in required_fields)
        fields_valid = all(cleaned_data.get(k) not in [None, "", 0, 0.0] for k in required_fields)
        
        if fields_present and fields_valid:
            t1 = float(cleaned_data['bike_short_min']) * 60 + float(cleaned_data['bike_short_sec'])
            p1 = float(cleaned_data['bike_short_watts'])
            t2 = float(cleaned_data['bike_long_min']) * 60 + float(cleaned_data['bike_long_sec'])
            p2 = float(cleaned_data['bike_long_watts'])
            
            if t2 != t1:
                w1 = p1 * t1
                w2 = p2 * t2
                cp = (w2 - w1) / (t2 - t1)
                if 'cycling_ftp' not in transformed:
                    transformed['cycling_ftp'] = int(cp)
    except Exception as e:
        logger.debug(f"Calcul cycling non effectué: {e}")
    
    # 3. Copier les autres champs numériques directement
    numeric_fields = ['run_sprint_max', 'bike_peak_5s', 'squat_1rm', 'bench_1rm', 
                     'deadlift_1rm', 'pull_load', 'run_vma', 'cycling_ftp']
    
    for field in numeric_fields:
        if field in cleaned_data:
            try:
                transformed[field] = float(cleaned_data[field])
            except (ValueError, TypeError):
                pass
    
    # 4. Pour compatibilité avec le schéma Pydantic
    # Convertir les champs spécifiques vers les noms d'API attendus
    if 'run_vma' in transformed:
        transformed['running_vma'] = transformed.pop('run_vma')
    
    # 5. Garder les données brutes nettoyées pour référence
    if cleaned_data:
        transformed['raw_mobile_data'] = cleaned_data
    
    logger.info(f"📊 Données performance transformées: {transformed}")
    return transformed

# --- ROUTE CRITIQUE POUR LE MOBILE ---

@router.get("/me", response_model=schemas.AthleteProfileResponse)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère le profil de l'utilisateur connecté.
    Si aucun profil n'existe, crée un profil vide automatiquement.
    Route appelée par le mobile: GET /api/v1/profiles/me
    """
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        logger.info(f"📝 Aucun profil trouvé pour user {current_user.id}, création d'un profil vide")
        
        # Créer un profil vide
        profile = sql_models.AthleteProfile(
            user_id=current_user.id,
            basic_info={"pseudo": current_user.username},
            physical_metrics={},
            sport_context={},
            performance_baseline={},
            injury_prevention={},
            training_preferences={},
            goals={},
            constraints={}
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        logger.info(f"✅ Profil vide créé pour user {current_user.id}")
    
    return profile

@router.put("/me", response_model=schemas.AthleteProfileResponse)
async def update_my_profile(
    profile_update: schemas.AthleteProfileUpdate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour le profil de l'utilisateur connecté.
    Si le profil n'existe pas, le crée automatiquement.
    Route appelée par le mobile: PUT /api/v1/profiles/me
    """
    logger.info(f"⚡ UPDATE /me demandé pour user : {current_user.id}")
    
    profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        logger.info(f"📝 Création de profil via PUT /me pour user {current_user.id}")
        
        # Valider les données du profil
        try:
            validate_athlete_profile(profile_update.model_dump(exclude_unset=True))
        except ValueError as e:
            logger.error(f"Erreur de validation : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Créer le profil
        profile = sql_models.AthleteProfile(
            user_id=current_user.id,
            basic_info=profile_update.basic_info or {},
            physical_metrics=profile_update.physical_metrics or {},
            sport_context=profile_update.sport_context or {},
            performance_baseline=profile_update.performance_baseline or {},
            injury_prevention=profile_update.injury_prevention or {},
            training_preferences=profile_update.training_preferences or {},
            goals=profile_update.goals or {},
            constraints=profile_update.constraints or {}
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        logger.info(f"✅ Profil créé via PUT /me pour user {current_user.id}")
        return profile
    
    # Si profil existe, mise à jour
    # Conversion Pydantic -> Dict en excluant les valeurs None
    update_dict = profile_update.model_dump(exclude_unset=True)
    
    # Traiter les données de performance spécialement
    if 'performance_baseline' in update_dict:
        perf_data = update_dict['performance_baseline']
        if perf_data:
            logger.info(f"📊 Données performance brutes reçues: {perf_data}")
            transformed_perf = transform_mobile_performance_data(perf_data)
            logger.info(f"🔄 Données performance transformées: {transformed_perf}")
            update_dict['performance_baseline'] = transformed_perf
    
    # Liste des champs JSON dans le modèle SQL
    json_fields = [
        'basic_info', 'physical_metrics', 'sport_context',
        'performance_baseline', 'injury_prevention', 
        'training_preferences', 'goals', 'constraints'
    ]
    
    try:
        updated_sections = []
        
        for section, data in update_dict.items():
            if section in json_fields and data is not None:
                setattr(profile, section, data)
                updated_sections.append(section)
            elif hasattr(profile, section) and data is not None:
                setattr(profile, section, data)
        
        # Mettre à jour le timestamp
        profile.updated_at = func.now()
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"✅ Profil /me mis à jour. Sections: {updated_sections}")
        return profile
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur update /me: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur de mise à jour: {str(e)}"
        )

@router.post("/complete", response_model=schemas.AthleteProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_complete_profile(
    profile_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Crée un profil athlète complet via le wizard
    Route alternative pour création via wizard
    """
    logger.info(f"Création de profil wizard pour l'utilisateur : {current_user.id}")
    
    # Vérifier si l'utilisateur a déjà un profil
    existing_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if existing_profile:
        logger.warning(f"Profil déjà existant pour user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un profil existe déjà pour cet utilisateur. Utilisez PUT /me pour mettre à jour."
        )
    
    # Valider les données du profil
    try:
        validate_athlete_profile(profile_data)
    except ValueError as e:
        logger.error(f"Erreur de validation : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Traiter les données de performance
    if 'performance_baseline' in profile_data:
        perf_data = profile_data['performance_baseline']
        if perf_data:
            transformed_perf = transform_mobile_performance_data(perf_data)
            profile_data['performance_baseline'] = transformed_perf
    
    # Créer le profil
    athlete_profile = sql_models.AthleteProfile(
        user_id=current_user.id,
        basic_info=profile_data.get('basic_info', {}),
        physical_metrics=profile_data.get('physical_metrics', {}),
        sport_context=profile_data.get('sport_context', {}),
        performance_baseline=profile_data.get('performance_baseline', {}),
        injury_prevention=profile_data.get('injury_prevention', {}),
        training_preferences=profile_data.get('training_preferences', {}),
        goals=profile_data.get('goals', {}),
        constraints=profile_data.get('constraints', {})
    )
    
    try:
        db.add(athlete_profile)
        db.commit()
        db.refresh(athlete_profile)
        
        # Initialiser la mémoire du coach
        initialize_coach_memory(athlete_profile, db)
        
        logger.info(f"Profil wizard créé avec succès pour user {current_user.id}")
        return athlete_profile
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Erreur d'intégrité DB : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur d'intégrité des données"
        )

# --- AUTRES ROUTES (optionnelles, pour compatibilité) ---

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
    Met à jour complètement un profil par ID
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
    
    # Conversion Pydantic -> Dict
    update_dict = profile_update.model_dump(exclude_unset=True)
    
    # Traiter les données de performance
    if 'performance_baseline' in update_dict:
        perf_data = update_dict['performance_baseline']
        if perf_data:
            transformed_perf = transform_mobile_performance_data(perf_data)
            update_dict['performance_baseline'] = transformed_perf
    
    # Mettre à jour chaque section
    for section, data in update_dict.items():
        if data is not None and hasattr(profile, section):
            setattr(profile, section, data)
    
    # Mettre à jour le timestamp
    profile.updated_at = func.now()
    
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
    
    # Traiter les données de performance spécialement
    if section_name == 'performance_baseline':
        perf_data = section_update.section_data
        if perf_data:
            transformed_perf = transform_mobile_performance_data(perf_data)
            setattr(profile, section_name, transformed_perf)
        else:
            setattr(profile, section_name, {})
    else:
        setattr(profile, section_name, section_update.section_data)
    
    # Mettre à jour le timestamp
    profile.updated_at = func.now()
    
    db.commit()
    
    return {
        "message": "Section mise à jour avec succès"
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
        if not value or value == {}:
            missing_sections.append(name)
    
    total_sections = 8
    completed_sections = total_sections - len(missing_sections)
    completion_percentage = int((completed_sections / total_sections) * 100)
    
    return {
        "completion_percentage": completion_percentage,
        "is_complete": completion_percentage >= 80,
        "missing_sections": missing_sections,
        "total_sections": total_sections,
        "completed_sections": completed_sections
    }