from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/feed",
    tags=["Neural Feed"]
)

@router.get("/", response_model=List[schemas.FeedItemResponse])
async def get_my_feed(
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Récupère le flux d'événements de l'utilisateur.
    Filtre : Uniquement les items NON COMPLÉTÉS.
    Tri : Priorité (DESC) puis Date de création (DESC).
    """
    items = db.query(sql_models.FeedItem)\
        .filter(sql_models.FeedItem.user_id == current_user.id)\
        .filter(sql_models.FeedItem.is_completed == False)\
        .order_by(sql_models.FeedItem.priority.desc(), sql_models.FeedItem.created_at.desc())\
        .all()
    return items

@router.patch("/{item_id}/read")
async def mark_as_read(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """Marque un item comme LU (mais le laisse dans le flux tant que pas complété)."""
    item = db.query(sql_models.FeedItem).filter(sql_models.FeedItem.id == item_id, sql_models.FeedItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item introuvable")
    
    item.is_read = True
    db.commit()
    return {"status": "success"}

@router.patch("/{item_id}/complete")
async def mark_as_completed(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """Marque un item comme COMPLÉTÉ (Disparaît du flux)."""
    item = db.query(sql_models.FeedItem).filter(sql_models.FeedItem.id == item_id, sql_models.FeedItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item introuvable")
    
    item.is_completed = True
    db.commit()
    return {"status": "success"}