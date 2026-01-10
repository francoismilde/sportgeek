from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user
import json

from fastapi import APIRouter, Depends, HTTPException, status
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


@router.get("/profile/complete", response_model=schemas.AthleteProfileResponse)
async def get_complete_profile(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le profil athlète complet.
    Compatibilité avec l'ancien système (profile_data) et le nouveau (AthleteProfile).
    """
    # Vérifier d'abord si l'utilisateur a un profil athlète v2
    if current_user.athlete_profile:
        return current_user.athlete_profile
    
    # Fallback : retourner les données du profil legacy
    if current_user.profile_data:
        try:
            profile_data = json.loads(current_user.profile_data)
            return {
                "id": current_user.id,
                "user_id": current_user.id,
                "created_at": current_user.created_at if hasattr(current_user, 'created_at') else None,
                "basic_info": {
                    "pseudo": current_user.username,
                    "email": current_user.email,
                    **profile_data.get('basic_info', {})
                },
                "physical_metrics": profile_data.get('physical_metrics', {}),
                "sport_context": profile_data.get('sport_context', {}),
                "training_preferences": profile_data.get('training_preferences', {}),
                "goals": profile_data.get('goals', {}),
                "constraints": profile_data.get('constraints', {}),
                "injury_prevention": profile_data.get('injury_prevention', {}),
                "performance_baseline": profile_data.get('performance_baseline', {})
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lecture profil: {str(e)}"
            )
    
    raise HTTPException(
        status_code=404,
        detail="Profil non trouvé. Complétez votre profil d'abord."
    )

@router.post("/profile/complete", response_model=schemas.AthleteProfileResponse)
async def create_complete_profile(
    profile_data: dict,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Crée ou met à jour un profil athlète complet.
    Supporte à la fois l'ancien format (profile_data) et le nouveau (sections).
    """
    try:
        # Vérifier si l'utilisateur a déjà un profil athlète v2
        if current_user.athlete_profile:
            # Mettre à jour le profil existant
            profile = current_user.athlete_profile
            for section, data in profile_data.items():
                if hasattr(profile, section):
                    setattr(profile, section, json.dumps(data))
        else:
            # Créer un nouveau profil athlète
            profile = sql_models.AthleteProfile(
                user_id=current_user.id,
                basic_info=json.dumps(profile_data.get('basic_info', {})),
                physical_metrics=json.dumps(profile_data.get('physical_metrics', {})),
                sport_context=json.dumps(profile_data.get('sport_context', {})),
                training_preferences=json.dumps(profile_data.get('training_preferences', {})),
                goals=json.dumps(profile_data.get('goals', {})),
                constraints=json.dumps(profile_data.get('constraints', {})),
                injury_prevention=json.dumps(profile_data.get('injury_prevention', {})),
                performance_baseline=json.dumps(profile_data.get('performance_baseline', {}))
            )
            db.add(profile)
        
        # Mettre à jour aussi le profil legacy pour compatibilité
        current_user.profile_data = json.dumps(profile_data)
        
        db.commit()
        db.refresh(profile)
        
        return profile
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur création profil: {str(e)}"
        )

@router.post("/profile/sections/{section}")
async def update_profile_section(
    section: str,
    section_data: dict,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour une section spécifique du profil.
    Section peut être: basic_info, physical_metrics, sport_context, etc.
    """
    # Liste des sections valides
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
    
    try:
        # Mettre à jour le profil athlète v2 si existant
        if current_user.athlete_profile:
            profile = current_user.athlete_profile
            setattr(profile, section, json.dumps(section_data))
        else:
            # Si pas de profil athlète, créer un profil minimal
            profile = sql_models.AthleteProfile(user_id=current_user.id)
            setattr(profile, section, json.dumps(section_data))
            db.add(profile)
        
        # Mettre à jour aussi le profil legacy
        legacy_data = {}
        if current_user.profile_data:
            try:
                legacy_data = json.loads(current_user.profile_data)
            except:
                pass
        
        legacy_data[section] = section_data
        current_user.profile_data = json.dumps(legacy_data)
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Section '{section}' mise à jour",
            "section": section,
            "data": section_data
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur mise à jour section: {str(e)}"
        )



@router.get("/profile/complete", response_model=schemas.AthleteProfileResponse)
async def get_complete_profile(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère le profil athlète complet.
    Compatibilité avec l'ancien système (profile_data) et le nouveau (AthleteProfile).
    """
    # Vérifier d'abord si l'utilisateur a un profil athlète v2
    if current_user.athlete_profile:
        return current_user.athlete_profile
    
    # Fallback : retourner les données du profil legacy
    if current_user.profile_data:
        try:
            profile_data = json.loads(current_user.profile_data)
            return {
                "id": current_user.id,
                "user_id": current_user.id,
                "created_at": current_user.created_at if hasattr(current_user, 'created_at') else None,
                "basic_info": {
                    "pseudo": current_user.username,
                    "email": current_user.email,
                    **profile_data.get('basic_info', {})
                },
                "physical_metrics": profile_data.get('physical_metrics', {}),
                "sport_context": profile_data.get('sport_context', {}),
                "training_preferences": profile_data.get('training_preferences', {}),
                "goals": profile_data.get('goals', {}),
                "constraints": profile_data.get('constraints', {}),
                "injury_prevention": profile_data.get('injury_prevention', {}),
                "performance_baseline": profile_data.get('performance_baseline', {})
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lecture profil: {str(e)}"
            )
    
    raise HTTPException(
        status_code=404,
        detail="Profil non trouvé. Complétez votre profil d'abord."
    )

@router.post("/profile/complete", response_model=schemas.AthleteProfileResponse)
async def create_complete_profile(
    profile_data: dict,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Crée ou met à jour un profil athlète complet.
    Supporte à la fois l'ancien format (profile_data) et le nouveau (sections).
    """
    try:
        # Vérifier si l'utilisateur a déjà un profil athlète v2
        if current_user.athlete_profile:
            # Mettre à jour le profil existant
            profile = current_user.athlete_profile
            for section, data in profile_data.items():
                if hasattr(profile, section):
                    setattr(profile, section, json.dumps(data))
        else:
            # Créer un nouveau profil athlète
            profile = sql_models.AthleteProfile(
                user_id=current_user.id,
                basic_info=json.dumps(profile_data.get('basic_info', {})),
                physical_metrics=json.dumps(profile_data.get('physical_metrics', {})),
                sport_context=json.dumps(profile_data.get('sport_context', {})),
                training_preferences=json.dumps(profile_data.get('training_preferences', {})),
                goals=json.dumps(profile_data.get('goals', {})),
                constraints=json.dumps(profile_data.get('constraints', {})),
                injury_prevention=json.dumps(profile_data.get('injury_prevention', {})),
                performance_baseline=json.dumps(profile_data.get('performance_baseline', {}))
            )
            db.add(profile)
        
        # Mettre à jour aussi le profil legacy pour compatibilité
        current_user.profile_data = json.dumps(profile_data)
        
        db.commit()
        db.refresh(profile)
        
        return profile
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur création profil: {str(e)}"
        )

@router.post("/profile/sections/{section}")
async def update_profile_section(
    section: str,
    section_data: dict,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour une section spécifique du profil.
    Section peut être: basic_info, physical_metrics, sport_context, etc.
    """
    # Liste des sections valides
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
    
    try:
        # Mettre à jour le profil athlète v2 si existant
        if current_user.athlete_profile:
            profile = current_user.athlete_profile
            setattr(profile, section, json.dumps(section_data))
        else:
            # Si pas de profil athlète, créer un profil minimal
            profile = sql_models.AthleteProfile(user_id=current_user.id)
            setattr(profile, section, json.dumps(section_data))
            db.add(profile)
        
        # Mettre à jour aussi le profil legacy
        legacy_data = {}
        if current_user.profile_data:
            try:
                legacy_data = json.loads(current_user.profile_data)
            except:
                pass
        
        legacy_data[section] = section_data
        current_user.profile_data = json.dumps(legacy_data)
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Section '{section}' mise à jour",
            "section": section,
            "data": section_data
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur mise à jour section: {str(e)}"
        )

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