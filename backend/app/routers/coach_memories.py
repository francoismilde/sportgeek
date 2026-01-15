from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

# Imports Core
from app.core.database import get_db
from app.dependencies import get_current_user  # ✅ AJOUT CRITIQUE
from app.models import sql_models, schemas

router = APIRouter(
    prefix="/api/v1/coach-memories",
    tags=["Coach Memory v2"]
)

# ==============================================================================
# 🧠 GET MY MEMORY (Prioritaire sur /{id})
# ==============================================================================
@router.get("/me", response_model=schemas.CoachMemoryResponse)
async def get_my_coach_memory(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la mémoire du coach pour l'utilisateur connecté.
    Route spécifique : Doit être déclarée AVANT les routes dynamiques.
    """
    if not current_user.athlete_profile:
        raise HTTPException(status_code=404, detail="Profil athlète introuvable.")
        
    if not current_user.athlete_profile.coach_memory:
        raise HTTPException(status_code=404, detail="Mémoire du coach introuvable.")
    
    return current_user.athlete_profile.coach_memory

# ==============================================================================
# 📥 GET ALL MEMORIES (Admin / Debug)
# ==============================================================================
@router.get("/", response_model=List[schemas.CoachMemoryOut])
@router.get("/engrams", response_model=List[schemas.CoachMemoryOut]) 
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
# 📤 POST NEW MEMORY
# ==============================================================================
@router.post("/", response_model=schemas.CoachMemoryOut, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_in: schemas.CoachMemoryCreate,
    db: Session = Depends(get_db)
):
    # Si user_id n'est pas fourni, on met une valeur par défaut safe (ex: 1) ou on gère l'erreur
    uid = memory_in.user_id if memory_in.user_id else 1
    
    # Attention: CoachMemoryCreate ici semble être designé pour des Engrammes ou test
    # On crée une entrée basique pour éviter le crash
    new_memory = sql_models.CoachMemory(
        athlete_profile_id=uid, # Simplification pour le debug
        metadata_info={"type": memory_in.type, "content": memory_in.content}
    )
    
    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)
    return new_memory

# ==============================================================================
# 🗑️ DELETE MEMORY (Route Dynamique - Doit être en dernier)
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