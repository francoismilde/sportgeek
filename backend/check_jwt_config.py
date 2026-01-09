import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

print("🔧 Configuration JWT Actuelle:")
print(f"   SECRET_KEY: {'SET' if SECRET_KEY else 'NOT SET'}")
print(f"   ALGORITHM: {ALGORITHM}")
print(f"   ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES} min")

# Vérifier si on peut générer un token
if SECRET_KEY:
    print("\n🧪 Test de génération de token...")
    
    data = {"sub": "testuser", "exp": datetime.utcnow() + timedelta(minutes=30)}
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    
    print(f"   Token généré: {token[:50]}...")
    
    # Vérifier qu'on peut le décoder
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"   ✅ Token décodé: {decoded}")
    except Exception as e:
        print(f"   ❌ Erreur décodage: {e}")
else:
    print("\n❌ SECRET_KEY non définie!")
    print("   Définissez-la dans .env:")
    print("   SECRET_KEY=votre_clef_secrete_tres_longue_ici")
