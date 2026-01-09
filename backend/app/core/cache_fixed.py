"""
Version corrigée du décorateur de cache qui ignore les objets non sérialisables
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class FixedIntelligentCache:
    """Cache mémoire avec gestion des objets non sérialisables."""
    
    def __init__(self, default_ttl_hours: int = 24):
        self._cache = {}
        self.default_ttl = default_ttl_hours
    
    def _safe_serialize(self, obj: Any) -> Any:
        """Sérialise en toute sécurité, convertissant les objets SQLAlchemy en dict."""
        if hasattr(obj, '__dict__'):
            # Si c'est un modèle SQLAlchemy, on prend son ID
            if hasattr(obj, 'id'):
                return f"{obj.__class__.__name__}:{obj.id}"
            # Sinon, on convertit en dict sans les relations
            return {k: self._safe_serialize(v) for k, v in obj.__dict__.items() 
                    if not k.startswith('_')}
        elif isinstance(obj, (list, tuple)):
            return [self._safe_serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._safe_serialize(v) for k, v in obj.items()}
        else:
            return obj
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Génère une clé unique en sérialisant en toute sécurité."""
        safe_args = self._safe_serialize(args)
        safe_kwargs = self._safe_serialize(kwargs)
        
        data = json.dumps({
            'args': safe_args,
            'kwargs': safe_kwargs
        }, sort_keys=True, default=str)
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère un élément du cache s'il est valide."""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry['expires_at']:
                logger.debug(f"📦 Cache hit: {key}")
                return entry['data']
            else:
                del self._cache[key]
                logger.debug(f"🧹 Cache expired: {key}")
        return None
    
    def set(self, key: str, data: Any, ttl_hours: Optional[int] = None):
        """Stocke un élément dans le cache."""
        ttl = ttl_hours if ttl_hours is not None else self.default_ttl
        self._cache[key] = {
            'data': data,
            'expires_at': datetime.now() + timedelta(hours=ttl),
            'created_at': datetime.now()
        }
        logger.debug(f"💾 Cache stored: {key} (TTL: {ttl}h)")
    
    def clear_old_entries(self):
        """Nettoie les entrées expirées."""
        now = datetime.now()
        expired_keys = [
            k for k, v in self._cache.items() 
            if now >= v['expires_at']
        ]
        for k in expired_keys:
            del self._cache[k]
        if expired_keys:
            logger.info(f"🧹 Cache cleanup: {len(expired_keys)} entrées expirées")

# Instance globale
ai_cache_fixed = FixedIntelligentCache(default_ttl_hours=6)

def cached_response_fixed(ttl_hours: int = 6, ignore_args: list = None):
    """
    Décorateur corrigé pour mettre en cache les réponses IA.
    ignore_args: liste des noms d'arguments à ignorer (ex: ['current_user'])
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Créer une copie des kwargs pour la génération de clé
            cache_kwargs = kwargs.copy()
            
            # Ignorer les arguments spécifiés
            if ignore_args:
                for arg_name in ignore_args:
                    cache_kwargs.pop(arg_name, None)
            
            # Générer une clé unique (sans les arguments ignorés)
            cache_key = f"{func.__name__}:{ai_cache_fixed._generate_key(*args, **cache_kwargs)}"
            
            # Vérifier le cache
            cached = ai_cache_fixed.get(cache_key)
            if cached is not None:
                return cached
            
            # Exécuter la fonction
            result = await func(*args, **kwargs)
            
            # Mettre en cache
            if result is not None:
                ai_cache_fixed.set(cache_key, result, ttl_hours)
            
            return result
        return wrapper
    return decorator
