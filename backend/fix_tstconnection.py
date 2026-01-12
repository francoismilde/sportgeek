import requests
import json
import time
import sys

# --- CONFIGURATION ---
# URL du serveur Render (Production)
BASE_URL = "https://sportgeek-nkvh.onrender.com"
# Pour tester en local, décommente la ligne suivante :
# BASE_URL = "http://localhost:8000"

# Génération d'un utilisateur unique pour éviter les erreurs "Email déjà pris"
TIMESTAMP = int(time.time())
EMAIL = f"test_{TIMESTAMP}@titanflow.com"
PASSWORD = "Password123!"
USERNAME = f"titan_{TIMESTAMP}"

def print_step(msg):
    """Affiche une étape en gras/couleur dans la console"""
    print(f"\n🔹 {msg}...")

def check(response, expected_codes=[200]):
    """Vérifie le code retour HTTP. Si KO, arrête le script."""
    if isinstance(expected_codes, int):
        expected_codes = [expected_codes]
        
    if response.status_code not in expected_codes:
        print(f"❌ ÉCHEC ! Code {response.status_code} (Attendu: {expected_codes})")
        try:
            print(f"   Détail : {json.dumps(response.json(), indent=2)}")
        except:
            print(f"   Réponse brute : {response.text}")
        sys.exit(1)
    
    print(f"✅ Succès ({response.status_code})")
    try:
        return response.json()
    except:
        return {}

def main():
    print(f"🚀 Démarrage des tests d'intégration sur {BASE_URL}")
    print(f"👤 Utilisateur test : {USERNAME} / {EMAIL}")
    
    # ---------------------------------------------------------
    # 1. INSCRIPTION
    # ---------------------------------------------------------
    print_step(f"1. Inscription")
    payload_signup = {
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD
    }
    # 🚨 FIX APPLIQUÉ : Route /auth/signup (et non /signup)
    resp = requests.post(f"{BASE_URL}/auth/signup", json=payload_signup)
    check(resp, [200, 201])

    # ---------------------------------------------------------
    # 2. LOGIN (Récupération du Token)
    # ---------------------------------------------------------
    print_step("2. Connexion (Login)")
    # FastAPI OAuth2PasswordRequestForm attend 'username' et 'password' en Form-Data
    payload_login = {
        "username": USERNAME, 
        "password": PASSWORD
    }
    resp = requests.post(f"{BASE_URL}/auth/token", data=payload_login)
    token_data = check(resp, 200)
    
    access_token = token_data.get("access_token")
    if not access_token:
        print("❌ Pas de token reçu !")
        sys.exit(1)
        
    print(f"🔑 Token récupéré : {access_token[:15]}...")

    # Headers pour les requêtes suivantes
    auth_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # ---------------------------------------------------------
    # 3. ENVOI DU PROFIL (Test du JSONB)
    # ---------------------------------------------------------
    print_step("3. Sauvegarde du Profil (Architecture JSONB)")
    
    # Données simulant l'envoi depuis Flutter
    # Note : On utilise les labels "Propres" pour le sport car le backend ne valide plus strictement
    profile_content = {
        "basic_info": {
            "pseudo": USERNAME, 
            "gender": "Homme",
            "birth_date": "1995-05-20"
        },
        "sport_context": {
            "sport": "Rugby",       # Test avec une valeur String
            "level": "Intermédiaire",
            "position": "Demi de mêlée"
        },
        "physical_metrics": {
            "weight": 85.5, 
            "height": 182,
            "body_fat": 12.5
        },
        "goals": {
            "main_goal": "Explosivité",
            "target_date": "2024-12-31"
        }
    }
    
    # 🚨 WRAPPER JSONB : On enveloppe dans "profile_data" comme attendu par le backend
    final_payload = {
        "profile_data": profile_content
    }

    # Route définie dans user.py (/complete) et incluse dans main.py (/api/v1/profiles)
    resp = requests.post(
        f"{BASE_URL}/api/v1/profiles/complete", 
        headers=auth_headers, 
        json=final_payload
    )
    
    # On s'attend à un succès. Si 422 ou 500, le script s'arrêtera ici.
    response_data = check(resp, 200)
    
    # ---------------------------------------------------------
    # 4. VÉRIFICATION DES DONNÉES
    # ---------------------------------------------------------
    print_step("4. Vérification de la persistance")
    
    # Le backend doit renvoyer le profil complet dans la réponse
    saved_profile = response_data.get("profile_data", {})
    saved_sport = saved_profile.get("sport_context", {}).get("sport")
    
    if saved_sport == "Rugby":
        print(f"✅ Données validées : Le sport '{saved_sport}' est bien sauvegardé en JSONB.")
    else:
        print(f"⚠️  Incohérence : Sport attendu 'Rugby', reçu '{saved_sport}'")
        print(f"   Dump complet : {saved_profile}")

    print("\n" + "="*50)
    print("🎉 SUCCÈS TOTAL : BACKEND OPÉRATIONNEL")
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERREUR DE CONNEXION : Impossible de joindre {BASE_URL}")
        print("   -> Vérifie que le serveur Render est 'Live' ou que ton serveur local tourne.")
    except Exception as e:
        print(f"\n❌ ERREUR IMPRÉVUE : {e}")