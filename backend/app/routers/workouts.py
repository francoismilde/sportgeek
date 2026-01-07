from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/workouts",
    tags=["Workouts"]
)

@router.post("/", response_model=schemas.WorkoutSessionResponse)
async def create_workout(
    workout: schemas.WorkoutSessionCreate, 
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Enregistre une séance complète avec ses séries.
    🔒 Nécessite d'être connecté.
    """
    # 1. Création de la Session
    db_workout = sql_models.WorkoutSession(
        date=workout.date,
        duration=workout.duration,
        rpe=workout.rpe,
        energy_level=workout.energy_level,
        notes=workout.notes,
        user_id=current_user.id
    )
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    
    # 2. Ajout des Séries (Sets)
    if workout.sets:
        for s in workout.sets:
            db_set = sql_models.WorkoutSet(
                session_id=db_workout.id,
                exercise_name=s.exercise_name,
                set_order=s.set_order,
                weight=s.weight,
                reps=s.reps,
                rpe=s.rpe,
                rest_seconds=s.rest_seconds,
                metric_type=s.metric_type
            )
            db.add(db_set)
        
        db.commit()
        db.refresh(db_workout)
    
    return db_workout

@router.get("/", response_model=List[schemas.WorkoutSessionResponse])
async def read_workouts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère l'historique complet (avec sets).
    """
    workouts = db.query(sql_models.WorkoutSession)\
        .filter(sql_models.WorkoutSession.user_id == current_user.id)\
        .order_by(sql_models.WorkoutSession.date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return workouts