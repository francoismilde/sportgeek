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

@router.post("/", response_model=schemas.WorkoutLogInput)
async def create_workout(
    workout: schemas.WorkoutLogInput, 
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Enregistre une nouvelle séance.
    🔒 Nécessite d'être connecté.
    """
    # On crée l'objet SQL en liant l'ID de l'utilisateur connecté
    db_workout = sql_models.WorkoutSession(
        date=workout.date,
        duration=workout.duration,
        rpe=workout.rpe,
        user_id=current_user.id
    )
    
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    
    return db_workout

@router.get("/", response_model=List[schemas.WorkoutLogInput])
async def read_workouts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère l'historique des séances de l'utilisateur connecté.
    🔒 Nécessite d'être connecté.
    """
    workouts = db.query(sql_models.WorkoutSession)\
        .filter(sql_models.WorkoutSession.user_id == current_user.id)\
        .order_by(sql_models.WorkoutSession.date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return workouts