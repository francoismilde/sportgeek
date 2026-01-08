from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models import schemas

class BaseTrigger(ABC):
    """
    Interface abstraite pour tous les déclencheurs d'événements (Triggers).
    Chaque Trigger est un 'spécialiste' (ex: Spécialiste Analyse, Spécialiste Santé).
    """

    @abstractmethod
    async def check(self, user_id: int, context: Dict[str, Any]) -> Optional[schemas.FeedItemCreate]:
        """
        Analyse le contexte et retourne un FeedItemCreate si la condition est remplie.
        Retourne None sinon.
        
        :param user_id: L'ID de l'athlète concerné.
        :param context: Un dictionnaire riche contenant les données (ex: {'workout': ..., 'profile': ...})
        :return: Un objet FeedItemCreate prêt à être inséré, ou None.
        """
        pass