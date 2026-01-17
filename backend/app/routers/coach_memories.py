from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

# Imports Core
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import sql_models, schemas
from app.models.enums import MemoryStatus

router = APIRouter(
    prefix="/api/v1/coach-memories",
    tags=["Coach Memory v2"]
)

# ==============================================================================
# 🧠 GET MY MEMORY (Route Principale - AVEC AUTO-HEALING)
# ==============================================================================
@router.get("/me", response_model=schemas.CoachMemoryResponse)
async def get_my_coach_memory(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la mémoire du coach pour l'utilisateur connecté.
    AUTO-HEALING : Si la mémoire n'existe pas, elle est créée immédiatement.
    """
    # 1. Vérifier le profil
    if not current_user.athlete_profile:
        raise HTTPException(status_code=404, detail="Profil athlète introuvable. Veuillez compléter votre profil.")
    
    profile_id = current_user.athlete_profile.id

    # 2. Requête Explicite avec Chargement Eager (Immédiat) des Engrammes
    memory = db.query(sql_models.CoachMemory)\
        .options(selectinload(sql_models.CoachMemory.engrams))\
        .filter(sql_models.CoachMemory.athlete_profile_id == profile_id)\
        .first()

    # [CORRECTIF CRITIQUE] : Auto-healing
    # Si pas de mémoire, on la crée à la volée pour ne pas bloquer l'UI
    if not memory:
        memory = sql_models.CoachMemory(athlete_profile_id=profile_id)
        db.add(memory)
        db.commit()
        db.refresh(memory)
    
    # 3. HYGIÈNE DES DONNÉES : Filtrage Python
    # On garde ACTIVE et RESOLVED (historique visible), on vire ARCHIVED (poubelle).
    if memory.engrams:
        active_engrams = [
            e for e in memory.engrams 
            if e.status != MemoryStatus.ARCHIVED
        ]
        memory.engrams = active_engrams
    
    return memory

# ==============================================================================
# 📥 GET ALL MEMORIES (Admin / Debug)
# ==============================================================================
@router.get("/", response_model=List[schemas.CoachMemoryOut])
async def get_memories(
    db: Session = Depends(get_db),
    limit: int = 50,
    status: Optional[str] = None
):
    query = select(sql_models.CoachMemory)
    if status:
        query = query.where(sql_models.CoachMemory.status == status)
    query = query.order_by(desc(sql_models.CoachMemory.last_updated))
    query = query.limit(limit)
    result = db.execute(query)
    return result.scalars().all()

# ==============================================================================
# ➕ ADD ENGRAM (LA ROUTE QUI MANQUAIT)
# ==============================================================================
@router.post("/engrams", response_model=schemas.CoachEngramResponse, status_code=status.HTTP_201_CREATED)
async def create_engram(
    engram_in: schemas.CoachEngramCreate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Ajoute un nouvel engramme (souvenir/contrainte) à la mémoire du coach.
    """
    # 1. Récupérer la mémoire du coach via le user connecté
    if not current_user.athlete_profile:
        raise HTTPException(status_code=404, detail="Profil introuvable.")
    
    profile_id = current_user.athlete_profile.id
    
    memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.athlete_profile_id == profile_id
    ).first()

    # Sécurité : Si pas de mémoire, on la crée (Auto-healing backend)
    if not memory:
        memory = sql_models.CoachMemory(athlete_profile_id=profile_id)
        db.add(memory)
        db.commit()
        db.refresh(memory)

    # 2. Création de l'engramme
    new_engram = sql_models.CoachEngram(
        memory_id=memory.id,
        content=engram_in.content,
        type=engram_in.type,
        impact=engram_in.impact,
        status=engram_in.status,
        tags=engram_in.tags,
        start_date=datetime.utcnow()
    )

    db.add(new_engram)
    
    # 3. Update Meta (Pour dire à l'IA qu'il y a du nouveau)
    memory.last_updated = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(new_engram)
        return new_engram
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur DB: {str(e)}")

# ==============================================================================
# 📤 POST NEW MEMORY (Container Principal)
# ==============================================================================
@router.post("/", response_model=schemas.CoachMemoryOut, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_in: schemas.CoachMemoryCreate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Crée une nouvelle instance de mémoire Coach (Container).
    """
    if not current_user.athlete_profile:
        raise HTTPException(status_code=400, detail="Aucun profil athlète associé.")

    profile_id = current_user.athlete_profile.id

    existing_memory = db.query(sql_models.CoachMemory).filter(
        sql_models.CoachMemory.athlete_profile_id == profile_id
    ).first()

    if existing_memory:
        raise HTTPException(status_code=409, detail="Une mémoire existe déjà.")
    
    new_memory = sql_models.CoachMemory(
        athlete_profile_id=profile_id,
        metadata_info={"type": memory_in.type, "content": memory_in.content}
    )
    
    try:
        db.add(new_memory)
        db.commit()
        db.refresh(new_memory)
        return new_memory
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# 🔄 UPDATE ENGRAM (Logique Temporelle & Réactivation)
# ==============================================================================
@router.put("/engrams/{engram_id}", response_model=schemas.CoachEngramResponse)
async def update_engram(
    engram_id: int,
    engram_update: schemas.CoachEngramCreate,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour un souvenir (Engramme).
    Gère la logique temporelle : RESOLVED vs ACTIVE.
    """
    # 1. Fetch & Check de propriété via Jointure
    engram = db.query(sql_models.CoachEngram)\
        .join(sql_models.CoachMemory)\
        .join(sql_models.AthleteProfile)\
        .filter(
            sql_models.CoachEngram.id == engram_id,
            sql_models.AthleteProfile.user_id == current_user.id
        ).first()

    if not engram:
        raise HTTPException(status_code=404, detail="Engramme introuvable.")

    # 2. LOGIQUE TEMPORELLE
    if engram_update.status == MemoryStatus.RESOLVED:
        if not engram.end_date:
            engram.end_date = datetime.utcnow()
    
    elif engram_update.status == MemoryStatus.ACTIVE:
        engram.end_date = None

    # 3. Application des mises à jour
    engram.content = engram_update.content
    engram.type = engram_update.type
    engram.impact = engram_update.impact
    engram.status = engram_update.status
    engram.tags = engram_update.tags
    
    if engram_update.end_date is not None and engram_update.status != MemoryStatus.ACTIVE:
        engram.end_date = engram_update.end_date

    engram.memory.last_updated = datetime.utcnow()

    db.commit()
    db.refresh(engram)
    
    return engram

# ==============================================================================
# 🗑️ DELETE MEMORY
# ==============================================================================
@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db)
):
    query = select(sql_models.CoachMemory).where(sql_models.CoachMemory.id == memory_id)
    result = db.execute(query)
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="Souvenir introuvable")

    db.delete(memory)
    db.commit()
    return None

# ==============================================================================
# 🗑️ DELETE ENGRAM (La route manquante pour corriger l'erreur 405)
# ==============================================================================
@router.delete("/engrams/{engram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_engram(
    engram_id: int,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Supprime un souvenir spécifique (Engramme).
    """
    # 1. Vérification de propriété (Sécurité)
    # On s'assure que l'engramme appartient bien à une mémoire liée au user connecté
    engram = db.query(sql_models.CoachEngram)\
        .join(sql_models.CoachMemory)\
        .join(sql_models.AthleteProfile)\
        .filter(
            sql_models.CoachEngram.id == engram_id,
            sql_models.AthleteProfile.user_id == current_user.id
        ).first()

    if not engram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Engramme introuvable ou accès refusé."
        )

    # 2. Suppression physique
    db.delete(engram)
    
    # 3. Update Meta (Optionnel : dire à la mémoire qu'elle a changé)
    engram.memory.last_updated = datetime.utcnow()
    
    db.commit()
    return None