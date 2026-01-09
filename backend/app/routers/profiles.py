from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user
from app.services.coach_logic import CoachLogic

router = APIRouter(
    prefix="/api/v1",
    tags=["Athlete Profile & Memory"]
)

@router.get("/profiles/me", response_model=schemas.AthleteProfileResponse)
async def get_my_profile(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.athlete_profile:
        profile = sql_models.AthleteProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    return current_user.athlete_profile

@router.post("/profiles/complete", response_model=schemas.AthleteProfileResponse)
async def complete_profile(
    profile_data: schemas.AthleteProfileCreate,
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sport = profile_data.sport_context.sport
    pos = profile_data.sport_context.position
    if not CoachLogic.validate_sport_position(sport, pos):
        raise HTTPException(status_code=400, detail=f"Position {pos} invalide pour le sport {sport}")

    db_profile = current_user.athlete_profile
    if not db_profile:
        db_profile = sql_models.AthleteProfile(user_id=current_user.id)
        db.add(db_profile)
    
    db_profile.basic_info = profile_data.basic_info.dict()
    db_profile.physical_metrics = profile_data.physical_metrics.dict()
    db_profile.sport_context = profile_data.sport_context.dict()
    db_profile.training_preferences = profile_data.training_preferences.dict()
    db_profile.goals = profile_data.goals
    db_profile.constraints = profile_data.constraints
    
    if not db_profile.coach_memory:
        memory = CoachLogic.initialize_memory(db_profile)
        db.add(memory)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.get("/coach-memories/me", response_model=schemas.CoachMemoryResponse)
async def get_my_coach_memory(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.athlete_profile or not current_user.athlete_profile.coach_memory:
        raise HTTPException(status_code=404, detail="Profil ou Mémoire introuvable. Complétez votre profil.")
    return current_user.athlete_profile.coach_memory

@router.post("/coach-memories/recalculate")
async def force_recalculate(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = current_user.athlete_profile
    if not profile or not profile.coach_memory:
        raise HTTPException(status_code=404, detail="Introuvable")
        
    CoachLogic.update_daily(profile.coach_memory, profile)
    db.commit()
    return {"status": "updated", "new_readiness": profile.coach_memory.current_context.get('readiness_score')}
