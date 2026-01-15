from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

# --- IMPORTS PROJET (Vérifie ces chemins selon ton dossier) ---
from app.core.database import get_db
from app.models import sql_models, schemas

router = APIRouter(
    prefix="/api/v1/coach-memories",
    tags=["Coach Memory v2"]
)

# ==============================================================================
# 📥 GET ALL MEMORIES (Engrams)
# ==============================================================================
# ✅ DOUBLE ROUTE : Accepte à la fois la racine ET /engrams pour éviter les 404
@router.get("/", response_model=List[schemas.CoachMemoryOut])
@router.get("/engrams", response_model=List[schemas.CoachMemoryOut]) 
async def get_memories(
    db: Session = Depends(get_db),
    limit: int = 50,
    status: Optional[str] = None
):
    """
    Récupère la liste des souvenirs du Coach (Engrams).
    Filtre optionnel par statut (ACTIVE, ARCHIVED, FORGOTTEN).
    Trie par date de création descendante (plus récent en premier).
    """
    query = select(sql_models.CoachMemory)
    
    if status:
        query = query.where(sql_models.CoachMemory.status == status)
    
    # Tri par défaut : les plus récents d'abord
    query = query.order_by(desc(sql_models.CoachMemory.created_at))
    query = query.limit(limit)

    result = db.execute(query)
    memories = result.scalars().all()
    
    return memories

# ==============================================================================
# 📤 POST NEW MEMORY
# ==============================================================================
@router.post("/", response_model=schemas.CoachMemoryOut, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_in: schemas.CoachMemoryCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouvel Engramme dans le Cortex (Mémoire long terme).
    """
    new_memory = sql_models.CoachMemory(
        user_id=memory_in.user_id if hasattr(memory_in, 'user_id') else 1, # Fallback ID si non fourni
        type=memory_in.type,
        impact=memory_in.impact,
        status=memory_in.status,
        content=memory_in.content,
        tags=memory_in.tags,
        start_date=memory_in.start_date,
        end_date=memory_in.end_date
    )
    
    db.add(new_memory)
    try:
        db.commit()
        db.refresh(new_memory)
        return new_memory
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la sauvegarde du souvenir: {str(e)}"
        )

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