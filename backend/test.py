import requests
import sys
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"
# Génération d'identifiants uniques pour le test
TIMESTAMP = int(time.time())
USERNAME = f"ci_bot_{TIMESTAMP}"
PASSWORD = "TestPassword123!"
EMAIL = f"ci_{TIMESTAMP}@test.com"

def run_test():
    print(f"🚀 Démarrage du test de validation FIX-500 sur {BASE_URL}")

    # 1. INSCRIPTION
    print("🔹 Étape 1 : Inscription...")
    signup_payload = {"username": USERNAME, "email": EMAIL, "password": PASSWORD}
    try:
        r = requests.post(f"{BASE_URL}/auth/signup", json=signup_payload)
        if r.status_code not in [200, 201]:
            print(f"❌ Échec Inscription: {r.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Le serveur semble éteint : {e}")
        sys.exit(1)

    # 2. CONNEXION (TOKEN)
    print("🔹 Étape 2 : Connexion...")
    login_data = {"username": USERNAME, "password": PASSWORD}
    r = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    if r.status_code != 200:
        print(f"❌ Échec Connexion: {r.text}")
        sys.exit(1)
    
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 3. TEST SAUVEGARDE PROFIL (LE COEUR DU BUG)
    print("🔹 Étape 3 : Sauvegarde Profil (Test de régression)...")
    
    # Payload complexe (Dictionnaire imbriqué) pour provoquer l'erreur 500
    # si le backend ne fait pas le json.dumps()
    profile_payload = {
        "profile_data": {
            "basic_info": {
                "pseudo": USERNAME,
                "email": EMAIL,
                "biography": "Test CI/CD avec caractères spéciaux éàù"
            },
            "sport_context": {
                "sport": "Crossfit",
                "stats": {"max_pullups": 20, "run_5k": "20:00"}
            },
            "goals": {
                "primary": "Survivre au déploiement"
            }
        }
    }

    r = requests.post(f"{BASE_URL}/api/v1/profiles/complete", json=profile_payload, headers=headers)

    # 4. VERIFICATION
    if r.status_code == 200:
        print("✅ SUCCÈS : Le profil a été sauvegardé sans erreur 500.")
        print("   Le correctif `json.dumps` est actif.")
        
        # Vérification optionnelle du retour
        data = r.json()
        if isinstance(data.get("profile_data"), dict):
             print("✅ Le backend a bien retourné un JSON (Dict) propre.")
        else:
             print("⚠️ Warning: Le backend a retourné une String au lieu d'un Dict (Pydantic parsing warning).")
             
        sys.exit(0)
    elif r.status_code == 500:
        print("🔥 ÉCHEC CRITIQUE : Erreur 500 détectée.")
        print("   Cause probable : Le dictionnaire Python est passé directement à SQLAlchemy sans sérialisation.")
        print(f"   Réponse : {r.text}")
        sys.exit(1)
    else:
        print(f"❌ Échec inattendu (Code {r.status_code}): {r.text}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()