from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user
import json

# Imports du Moteur de Feed
from app.services.feed.engine import TriggerEngine
from app.services.feed.triggers.workout_analysis import WorkoutAnalysisTrigger

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
    Supprime le brouillon associé une fois la séance validée.
    Active le Neural Feed pour l'analyse post-séance.
    """

    # --- VALIDATION PHYSIOLOGIQUE ---
    def validate_physiological_limits(workout: schemas.WorkoutSessionCreate):
        """Valide les limites physiologiques humaines."""
        
        # Durée réaliste (10min à 4h)
        if workout.duration < 10 or workout.duration > 240:
            raise HTTPException(
                status_code=400, 
                detail=f"Durée invalide ({workout.duration} min). Doit être entre 10 et 240 minutes."
            )
        
        # RPE 1-10
        if workout.rpe < 1 or workout.rpe > 10:
            raise HTTPException(
                status_code=400,
                detail=f"RPE invalide ({workout.rpe}). Doit être entre 1 et 10."
            )
        
        # Énergie 1-10
        if workout.energy_level < 1 or workout.energy_level > 10:
            raise HTTPException(
                status_code=400,
                detail=f"Niveau d'énergie invalide ({workout.energy_level}). Doit être entre 1 et 10."
            )
        
        # Validation des sets
        for s in workout.sets:
            # Watts max (record du monde ~2500W)
            if s.metric_type == 'POWER_TIME' and s.weight > 2000:
                raise HTTPException(
                    status_code=400,
                    detail=f"Puissance impossible ({s.weight}W). Record du monde ~2500W."
                )
            
            # Charge max (record +500kg)
            if s.metric_type == 'LOAD_REPS' and s.weight > 500:
                raise HTTPException(
                    status_code=400,
                    detail=f"Charge impossible ({s.weight}kg). Record du monde ~500kg."
                )
            
            # RPE série
            if s.rpe and (s.rpe < 1 or s.rpe > 10):
                raise HTTPException(
                    status_code=400,
                    detail=f"RPE série invalide ({s.rpe}). Doit être entre 1 et 10."
                )
        
        return True

    # Appliquer la validation
    validate_physiological_limits(workout)

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
            # Standard TitanFlow : Reps = Distance (m), Weight = 0 (ou vitesse m/s)
            if s.reps > 100000: # 100km max par série pour être sûr
                 raise HTTPException(status_code=400, detail=f"Distance suspecte : {s.reps} mètres.")

    # 2. Création de la Session (INSERT)
    db_workout = sql_models.WorkoutSession(
        date=workout.date,
        duration=workout.duration,
        rpe=workout.rpe,
        energy_level=workout.energy_level,
        notes=workout.notes,
        ai_analysis=workout.ai_analysis, # <--- AJOUT CRITIQUE POUR BE-03
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
                rest_seconds=s.rest_seconds, # <--- DEJA SUPPORTE PAR SQL MODEL
                metric_type=s.metric_type    # <--- DEJA SUPPORTE PAR SQL MODEL
            )
            db.add(db_set)
        
        # Nettoyage du brouillon après succès
        current_user.draft_workout_data = None
        
        db.commit()
        db.refresh(db_workout)

    # 4. TRIGGER NEURAL FEED (L'IA s'active ici)
    try:
        # On passe le profil complet dans le contexte via user_data
        profile_data = {}
        if current_user.profile_data:
            try:
                profile_data = json.loads(current_user.profile_data)
            except:
                pass

        engine = TriggerEngine()
        engine.register(WorkoutAnalysisTrigger())
        await engine.run_all(db, current_user.id, {
            "workout": db_workout,
            "profile": profile_data
        })
    except Exception as e:
        # On ne bloque pas la réponse si l'IA échoue, c'est du bonus
        print(f"⚠️ Feed Engine Error: {e}")
    
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