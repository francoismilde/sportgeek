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
# 🧠 GET MY MEMORY (Route Principale - Filtrée)
# ==============================================================================
@router.get("/me", response_model=schemas.CoachMemoryResponse)
async def get_my_coach_memory(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la mémoire du coach pour l'utilisateur connecté.
    FILTRE : Ne renvoie PAS les souvenirs archivés.
    """
    # 1. Vérifier le profil
    if not current_user.athlete_profile:
        raise HTTPException(status_code=404, detail="Profil athlète introuvable.")
    
    profile_id = current_user.athlete_profile.id

    # 2. Requête Explicite avec Chargement Eager (Immédiat) des Engrammes
    memory = db.query(sql_models.CoachMemory)\
        .options(selectinload(sql_models.CoachMemory.engrams))\
        .filter(sql_models.CoachMemory.athlete_profile_id == profile_id)\
        .first()

    if not memory:
        raise HTTPException(status_code=404, detail="Mémoire du coach introuvable.")
    
    # 3. HYGIÈNE DES DONNÉES : Filtrage Python
    # On garde ACTIVE et RESOLVED (historique visible), on vire ARCHIVED (poubelle).
    # SQLAlchemy a chargé tous les objets en mémoire, on peut trier la liste avant sérialisation.
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
# 🔄 UPDATE ENGRAM (DEV-CARD #04 - Logique Réactivation)
# ==============================================================================
@router.put("/engrams/{engram_id}", response_model=schemas.CoachEngramResponse)
async def update_engram(
    engram_id: int,
    engram_update: schemas.CoachEngramCreate, # On utilise le schéma existant comme DTO
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Met à jour un souvenir (Engramme).
    Gère la logique temporelle : 
    - RESOLVED : Fige la date de fin.
    - ACTIVE (depuis RESOLVED) : Efface la date de fin (Réactivation).
    """
    # 1. Fetch & Check de propriété via Jointure (Plus sécure)
    # On vérifie que l'engramme est lié à une mémoire, elle-même liée au profil du user connecté.
    engram = db.query(sql_models.CoachEngram)\
        .join(sql_models.CoachMemory)\
        .join(sql_models.AthleteProfile)\
        .filter(
            sql_models.CoachEngram.id == engram_id,
            sql_models.AthleteProfile.user_id == current_user.id
        ).first()

    if not engram:
        raise HTTPException(status_code=404, detail="Engramme introuvable ou accès refusé.")

    # 2. LOGIQUE TEMPORELLE (Le Chronomètre)
    # Cas : Résolution -> On date la fin
    if engram_update.status == MemoryStatus.RESOLVED:
        # On ne met à jour la date que si elle n'est pas déjà fixée
        if not engram.end_date:
            engram.end_date = datetime.utcnow()
    
    # Cas : Réactivation -> On efface la date (Le joueur retourne sur le terrain)
    elif engram_update.status == MemoryStatus.ACTIVE:
        engram.end_date = None

    # 3. Application des mises à jour
    # On met à jour manuellement pour contrôler ce qui change
    engram.content = engram_update.content
    engram.type = engram_update.type
    engram.impact = engram_update.impact
    engram.status = engram_update.status
    engram.tags = engram_update.tags
    
    # Si une date manuelle spécifique est envoyée, elle prime (sauf logique ci-dessus)
    if engram_update.end_date is not None and engram_update.status != MemoryStatus.ACTIVE:
        engram.end_date = engram_update.end_date

    # 4. Meta updates (On signale à la mémoire parente qu'il y a eu du mouvement)
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