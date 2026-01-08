import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import sql_models, schemas
from app.services.feed.triggers.base import BaseTrigger

# Configuration des logs pour ne pas perdre une miette du match
logger = logging.getLogger(__name__)

class TriggerEngine:
    """
    Le Moteur de Jeu.
    Il possède un registre de Triggers et les exécute tous pour un contexte donné.
    Il gère aussi la sécurité (Anti-Crash) et la filtration (Déduplication).
    """
    def __init__(self):
        self._registry: List[BaseTrigger] = []

    def register(self, trigger: BaseTrigger):
        """Enrôle un nouveau Trigger dans l'équipe."""
        self._registry.append(trigger)
        logger.info(f"✅ Trigger enregistré : {trigger.__class__.__name__}")

    async def run_all(self, db: Session, user_id: int, context: Dict[str, Any]) -> List[sql_models.FeedItem]:
        """
        Lance tous les Triggers enregistrés.
        
        Règles du jeu :
        1. Isolation : Si un trigger plante, les autres continuent.
        2. Déduplication : On évite de spammer le même message (ex: 1x par 24h).
        3. Persistance : Sauvegarde immédiate en base.
        """
        generated_events = []

        for trigger in self._registry:
            try:
                # Le Trigger analyse le jeu...
                event_schema = await trigger.check(user_id, context)
                
                if event_schema:
                    # Arbitrage vidéo (Déduplication)
                    if not self._should_discard(db, user_id, event_schema):
                        
                        # Transformation Schema -> SQL Model
                        db_item = sql_models.FeedItem(
                            id=str(uuid.uuid4()),
                            user_id=user_id,
                            type=event_schema.type,
                            title=event_schema.title,
                            message=event_schema.message,
                            priority=event_schema.priority,
                            is_read=False,
                            is_completed=False,
                            # Gestion propre du JSON payload
                            action_payload=json.dumps(event_schema.action_payload) if event_schema.action_payload else None
                        )
                        
                        db.add(db_item)
                        generated_events.append(db_item)
                        logger.info(f"📢 Event généré : {db_item.title} ({trigger.__class__.__name__})")
                    else:
                        logger.info(f"🔇 Event ignoré (Doublon) : {event_schema.title}")

            except Exception as e:
                # Carton jaune : Le trigger a planté, mais le match continue
                logger.error(f"⚠️ Erreur Trigger {trigger.__class__.__name__}: {str(e)}")
                continue

        # Coup de sifflet final : on valide les buts
        if generated_events:
            db.commit()
            for ev in generated_events:
                db.refresh(ev)
                
        return generated_events

    def _should_discard(self, db: Session, user_id: int, event: schemas.FeedItemCreate) -> bool:
        """
        Vérifie si un événement similaire existe déjà récemment.
        Règle actuelle : Pas de doublon (Même Titre + Même Type) non traité.
        Ou pas de doublon identique créé dans les dernières 24h.
        """
        # 1. Chercher si le même event est déjà en attente (Non complété)
        existing_active = db.query(sql_models.FeedItem).filter(
            sql_models.FeedItem.user_id == user_id,
            sql_models.FeedItem.type == event.type,
            sql_models.FeedItem.title == event.title,
            sql_models.FeedItem.is_completed == False
        ).first()

        if existing_active:
            return True # On jette, l'utilisateur a déjà ça dans son feed

        # 2. Chercher si le même event a été créé il y a moins de 24h (Anti-Spam)
        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        recent_duplicate = db.query(sql_models.FeedItem).filter(
            sql_models.FeedItem.user_id == user_id,
            sql_models.FeedItem.type == event.type,
            sql_models.FeedItem.title == event.title,
            sql_models.FeedItem.created_at >= one_day_ago
        ).first()

        if recent_duplicate:
            return True

        return False