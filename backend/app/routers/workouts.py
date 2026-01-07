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
    Enregistre une séance complète avec gestion du Polymorphisme (Metric Type).
    Vérifie la cohérence des données (ex: Watts max, RPE bounds).
    [DEV-CARD #05] Supprime le brouillon associé une fois la séance validée.
    """
    # 1. Validation de haut niveau avant insertion
    for s in workout.sets:
        # Validation RPE
        if s.rpe is not None and (s.rpe < 0 or s.rpe > 10):
            # On cap plutôt que de crasher
            s.rpe = max(0, min(10, s.rpe))
            
        # Validation Physiologique selon le mode
        if s.metric_type == 'POWER_TIME':
            # Check Watts (weight)
            if s.weight > 2000:
                raise HTTPException(status_code=400, detail=f"Valeur impossible : {s.weight} Watts sur l'exercice {s.exercise_name}. Vérifiez la saisie.")
        
        elif s.metric_type == 'PACE_DISTANCE':
            # Dans ce mode : weight = Vitesse/Pace (souvent 0 si calculée) ou Distance, reps = Distance ou Temps
            # Standard TitanFlow : Reps = Distance (m), Weight = 0 (ou vitesse m/s)
            if s.reps > 100000: # 100km max par série pour être sûr
                 raise HTTPException(status_code=400, detail=f"Distance suspecte : {s.reps} mètres.")

    # 2. Création de la Session
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
    
    # 3. Ajout des Séries (Sets)
    if workout.sets:
        for s in workout.sets:
            # Conversion explicite Pydantic -> SQL Model
            db_set = sql_models.WorkoutSet(
                session_id=db_workout.id,
                exercise_name=s.exercise_name,
                set_order=s.set_order,
                weight=s.weight, # Déjà nettoyé par Pydantic (float)
                reps=s.reps,     # Déjà nettoyé par Pydantic (float, secondes inclues)
                rpe=s.rpe,
                rest_seconds=s.rest_seconds,
                metric_type=s.metric_type # Le fameux recording_mode
            )
            db.add(db_set)
        
        # [DEV-CARD #05] Nettoyage du brouillon après succès
        current_user.draft_workout_data = None
        
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
    Récupère l'historique complet.
    Les champs polymorphes (weight/reps) sont renvoyés tels quels,
    le Frontend utilisera 'metric_type' pour savoir si c'est des kg ou des watts.
    """
    workouts = db.query(sql_models.WorkoutSession)\
        .filter(sql_models.WorkoutSession.user_id == current_user.id)\
        .order_by(sql_models.WorkoutSession.date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return workouts