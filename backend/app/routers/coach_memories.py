from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload # <--- IMPORTANT : Import nécessaire
from sqlalchemy import select, desc

# Imports Core
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import sql_models, schemas

router = APIRouter(
    prefix="/api/v1/coach-memories",
    tags=["Coach Memory v2"]
)

# ==============================================================================
# 🧠 GET MY MEMORY (Route Principale)
# ==============================================================================
@router.get("/me", response_model=schemas.CoachMemoryResponse)
async def get_my_coach_memory(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la mémoire du coach pour l'utilisateur connecté.
    Utilise selectinload pour forcer le chargement des engrammes (Souvenirs).
    """
    # 1. Vérifier le profil
    if not current_user.athlete_profile:
        raise HTTPException(status_code=404, detail="Profil athlète introuvable.")
    
    profile_id = current_user.athlete_profile.id

    # 2. Requête Explicite avec Chargement Eager (Immédiat) des Engrammes
    # C'est ici que la magie opère : .options(selectinload(...))
    memory = db.query(sql_models.CoachMemory)\
        .options(selectinload(sql_models.CoachMemory.engrams))\
        .filter(sql_models.CoachMemory.athlete_profile_id == profile_id)\
        .first()

    if not memory:
        raise HTTPException(status_code=404, detail="Mémoire du coach introuvable.")
    
    return memory

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
    uid = memory_in.user_id if memory_in.user_id else 1
    
    # Création simplifiée pour éviter les crashs si métadonnées incomplètes
    new_memory = sql_models.CoachMemory(
        athlete_profile_id=uid,
        metadata_info={"type": memory_in.type, "content": memory_in.content}
    )
    
    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)
    return new_memory

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