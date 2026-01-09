"""
Cache intelligent pour les appels Gemini IA.
Économise les coûts API et améliore la réactivité.
"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class IntelligentCache:
    """Cache mémoire avec expiration et invalidation intelligente."""
    
    def __init__(self, default_ttl_hours: int = 24):
        self._cache = {}
        self.default_ttl = default_ttl_hours
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Génère une clé unique à partir des paramètres."""
        data = json.dumps({
            'args': args,
            'kwargs': kwargs
        }, sort_keys=True)
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
ai_cache = IntelligentCache(default_ttl_hours=6)  # 6h pour les plans IA

def cached_response(ttl_hours: int = 6):
    """Décorateur pour mettre en cache les réponses IA."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Générer une clé unique
            cache_key = f"{func.__name__}:{ai_cache._generate_key(*args, **kwargs)}"
            
            # Vérifier le cache
            cached = ai_cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Exécuter la fonction
            result = await func(*args, **kwargs)
            
            # Mettre en cache
            if result is not None:
                ai_cache.set(cache_key, result, ttl_hours)
            
            return result
        return wrapper
    return decorator
