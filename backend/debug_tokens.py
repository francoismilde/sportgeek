#!/usr/bin/env python3
"""
Debug JWT tokens - Vérifie pourquoi les tokens sont rejetés
"""

import jwt
import os
from datetime import datetime
import sys

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_if_env_missing")
ALGORITHM = "HS256"

def decode_and_verify(token: str):
    """Décode et vérifie un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        print("✅ TOKEN VALIDE")
        print(f"📋 Payload: {payload}")
        
        # Vérifier l'expiration
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            exp_date = datetime.fromtimestamp(exp_timestamp)
            now = datetime.now()
            time_left = exp_date - now
            
            print(f"⏰ Expiration: {exp_date}")
            print(f"⏳ Temps restant: {time_left}")
            
            if time_left.total_seconds() < 0:
                print("❌ TOKEN EXPIRE !")
            else:
                print("✅ Token encore valide")
        
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ ERREUR: Token expiré")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ ERREUR: Token invalide - {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_tokens.py <token>")
        print("Ou: python debug_tokens.py --check-all")
        return
    
    if sys.argv[1] == "--check-all":
        # Vérifier les tokens stockés dans un échantillon
        sample_tokens = []
        # Vous pouvez ajouter des tokens de test ici
        for token in sample_tokens:
            decode_and_verify(token)
    else:
        token = sys.argv[1]
        decode_and_verify(token)

if __name__ == "__main__":
    main()