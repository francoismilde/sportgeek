"""
Routeur pour la gestion de la mémoire du coach
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import sql_models, schemas
from app.models.enums import MemoryStatus
from app.services.coach_memory.service import (
    initialize_coach_memory,
    process_workout_session,
    update_daily_context,
    generate_insights,
    recalculate_memory
)

router = APIRouter(
    prefix="/api/v1/coach-memories",
    tags=["Coach Memory v2"]
)

@router.get("/athlete/{athlete_id}", response_model=schemas.CoachMemoryResponse)
async def get_coach_memory_by_athlete(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère la mémoire du coach pour un athlète spécifique
    """
    # Vérifier que l'athlète appartient à l'utilisateur
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == athlete_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil athlète non trouvé"
        )
    
    # Récupérer ou créer la mémoire du coach
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.athlete_profile_id == athlete_id
    ).first()
    
    if not coach_memory:
        # Initialiser la mémoire si elle n'existe pas
        coach_memory = initialize_coach_memory(athlete_profile, db)
    
    return coach_memory

@router.get("/{memory_id}/context")
async def get_memory_context(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère uniquement le contexte actuel de la mémoire
    """
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mémoire du coach non trouvée"
        )
    
    # Vérifier les permissions
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    context = json.loads(coach_memory.current_context) if coach_memory.current_context else {}
    
    return {
        "context": context,
        "last_updated": coach_memory.last_updated,
        "readiness_score": context.get('readiness_score', 0),
        "fatigue_state": context.get('fatigue_state', 'unknown')
    }

@router.get("/{memory_id}/insights")
async def get_memory_insights(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère les insights générés par la mémoire
    """
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mémoire du coach non trouvée"
        )
    
    # Vérifier les permissions
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Générer des insights si nécessaire
    insights = generate_insights(coach_memory, athlete_profile, db)
    
    return {
        "sport_specific_insights": json.loads(coach_memory.sport_specific_insights) if coach_memory.sport_specific_insights else {},
        "performance_baselines": json.loads(coach_memory.performance_baselines) if coach_memory.performance_baselines else {},
        "adaptation_signals": json.loads(coach_memory.adaptation_signals) if coach_memory.adaptation_signals else {},
        "memory_flags": json.loads(coach_memory.memory_flags) if coach_memory.memory_flags else {},
        "generated_insights": insights
    }

@router.post("/{memory_id}/process-session")
async def process_session(
    memory_id: int,
    session_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Traite une séance d'entraînement et met à jour la mémoire
    """
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mémoire du coach non trouvée"
        )
    
    # Vérifier les permissions
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Traiter la séance en arrière-plan
    background_tasks.add_task(
        process_workout_session,
        coach_memory,
        athlete_profile,
        session_data,
        db
    )
    
    return {
        "message": "Séance en cours de traitement",
        "session_id": session_data.get('id'),
        "processing": True
    }

@router.post("/{memory_id}/daily-checkin")
async def daily_checkin(
    memory_id: int,
    checkin_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Effectue un check-in quotidien et met à jour le contexte
    """
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mémoire du coach non trouvée"
        )
    
    # Vérifier les permissions
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Mettre à jour le contexte quotidien
    updated_context = update_daily_context(coach_memory, checkin_data, db)
    
    return {
        "message": "Check-in quotidien enregistré",
        "updated_context": updated_context,
        "readiness_score": updated_context.get('readiness_score', 0),
        "next_recommendations": updated_context.get('recommendations', [])
    }

@router.post("/{memory_id}/notes")
async def add_coach_note(
    memory_id: int,
    note_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Ajoute une note du coach à la mémoire
    """
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mémoire du coach non trouvée"
        )
    
    # Vérifier les permissions
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Ajouter la note
    coach_notes = json.loads(coach_memory.coach_notes) if coach_memory.coach_notes else {}
    
    note_id = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    coach_notes[note_id] = {
        "timestamp": datetime.now().isoformat(),
        "content": note_data.get('content', ''),
        "type": note_data.get('type', 'observation'),
        "priority": note_data.get('priority', 1),
        "tags": note_data.get('tags', [])
    }
    
    coach_memory.coach_notes = json.dumps(coach_notes)
    db.commit()
    
    return {
        "message": "Note ajoutée",
        "note_id": note_id,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/{memory_id}/recalculate")
async def force_recalculate_memory(
    memory_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Force le recalcul complet de la mémoire
    """
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mémoire du coach non trouvée"
        )
    
    # Vérifier les permissions
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Recalculer en arrière-plan
    background_tasks.add_task(
        recalculate_memory,
        coach_memory,
        athlete_profile,
        db
    )
    
    return {
        "message": "Recalcul de la mémoire démarré",
        "memory_id": memory_id,
        "recalculating": True
    }

@router.get("/{memory_id}/flags")
async def get_memory_flags(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère les flags (indicateurs) de la mémoire
    """
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mémoire du coach non trouvée"
        )
    
    # Vérifier les permissions
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    flags = json.loads(coach_memory.memory_flags) if coach_memory.memory_flags else {}
    
    # Filtrer les flags actifs
    active_flags = {k: v for k, v in flags.items() if v is True}
    warning_flags = []
    
    # Déterminer les priorités
    if active_flags.get('needs_deload'):
        warning_flags.append({"flag": "needs_deload", "priority": "high", "message": "Besoin de décharge détecté"})
    if active_flags.get('approaching_overtraining'):
        warning_flags.append({"flag": "approaching_overtraining", "priority": "high", "message": "Risque de surentraînement"})
    if active_flags.get('detraining_risk'):
        warning_flags.append({"flag": "detraining_risk", "priority": "medium", "message": "Risque de désentraînement"})
    if active_flags.get('adaptation_window_open'):
        warning_flags.append({"flag": "adaptation_window_open", "priority": "low", "message": "Fenêtre d'adaptation ouverte"})
    
    return {
        "active_flags": active_flags,
        "warnings": warning_flags,
        "total_flags": len(flags),
        "active_count": len(active_flags)
    }

@router.get("/{memory_id}/recommendations")
async def get_recommendations(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Génère des recommandations basées sur la mémoire
    """
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mémoire du coach non trouvée"
        )
    
    # Vérifier les permissions
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    context = json.loads(coach_memory.current_context) if coach_memory.current_context else {}
    flags = json.loads(coach_memory.memory_flags) if coach_memory.memory_flags else {}
    
    recommendations = []
    
    # Générer des recommandations basées sur le contexte et les flags
    readiness = context.get('readiness_score', 50)
    
    if readiness < 40:
        recommendations.append({
            "type": "recovery",
            "priority": "high",
            "action": "Réduire le volume d'entraînement de 30% cette semaine",
            "reason": f"Score de préparation bas ({readiness}/100)"
        })
    
    if flags.get('needs_deload'):
        recommendations.append({
            "type": "deload",
            "priority": "high",
            "action": "Planifier une semaine de décharge",
            "reason": "Accumulation de fatigue détectée"
        })
    
    if flags.get('adaptation_window_open') and readiness > 70:
        recommendations.append({
            "type": "progression",
            "priority": "medium",
            "action": "Augmenter l'intensité de 5-10%",
            "reason": "Fenêtre d'adaptation optimale"
        })
    
    if not recommendations:
        recommendations.append({
            "type": "maintenance",
            "priority": "low",
            "action": "Continuer le programme actuel",
            "reason": "État d'entraînement optimal"
        })
    
    return {
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat(),
        "context_used": {
            "readiness_score": readiness,
            "fatigue_state": context.get('fatigue_state', 'unknown'),
            "macrocycle_phase": context.get('macrocycle_phase', 'base')
        }
    }

# --- NOUVEAUX ENDPOINTS POUR LES ENGRAMMES ---

@router.get("/{memory_id}/engrams", response_model=List[schemas.CoachEngramResponse])
async def get_engrams(
    memory_id: int,
    status_filter: Optional[MemoryStatus] = MemoryStatus.ACTIVE,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère les engrammes (souvenirs structurés) de la mémoire.
    """
    # 1. Vérification d'accès (Sécurité)
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(status_code=404, detail="Mémoire introuvable")
        
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(status_code=403, detail="Accès interdit à cette mémoire")

    # 2. Requête filtrée
    query = db.query(sql_models.CoachEngram).filter(
        sql_models.CoachEngram.memory_id == memory_id
    )
    
    if status_filter:
        query = query.filter(sql_models.CoachEngram.status == status_filter)
        
    return query.all()

@router.post("/{memory_id}/engrams", response_model=schemas.CoachEngramResponse)
async def create_engram(
    memory_id: int,
    engram_data: schemas.CoachEngramCreate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Crée un nouvel engramme dans la mémoire.
    """
    # 1. Vérification d'accès
    coach_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.id == memory_id
    ).first()
    
    if not coach_memory:
        raise HTTPException(status_code=404, detail="Mémoire introuvable")
        
    athlete_profile = db.query(sql_models.AthleteProfile).filter(
        sql_models.AthleteProfile.id == coach_memory.athlete_profile_id,
        sql_models.AthleteProfile.user_id == current_user.id
    ).first()
    
    if not athlete_profile:
        raise HTTPException(status_code=403, detail="Accès interdit")

    # 2. Création de l'objet SQL
    new_engram = sql_models.CoachEngram(
        memory_id=memory_id,
        author="USER", # Ou "COACH_AI" si généré automatiquement plus tard
        type=engram_data.type,
        impact=engram_data.impact,
        status=engram_data.status,
        content=engram_data.content,
        tags=engram_data.tags,
        start_date=engram_data.start_date or datetime.now(),
        end_date=engram_data.end_date
    )
    
    db.add(new_engram)
    db.commit()
    db.refresh(new_engram)
    
    return new_engram