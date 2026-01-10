#!/usr/bin/env python3
"""
Script de test pour les nouveaux endpoints
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = None  # Remplacer par votre token JWT

def test_endpoint(method, endpoint, data=None):
    """Test un endpoint et affiche le résultat"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, headers=headers, json=data)
        else:
            print(f"❌ Méthode non supportée: {method}")
            return
        
        print(f"
🔍 Test {method} {endpoint}")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Succès!")
            try:
                result = response.json()
                print(f"   Réponse: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}...")
            except:
                print(f"   Réponse: {response.text[:200]}...")
        else:
            print(f"   ❌ Erreur!")
            print(f"   Message: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
    
    if not TOKEN:
        print("⚠️  Aucun token fourni. Seuls les endpoints publics seront testés.")
        print("   Usage: python test_new_endpoints.py <votre_token_jwt>")
    
    # Test des nouveaux endpoints
    print("🧪 TEST DES NOUVEAUX ENDPOINTS")
    print("=" * 50)
    
    # 1. Test GET /user/profile/complete
    test_endpoint("GET", "/user/profile/complete")
    
    # 2. Test POST /user/profile/complete (avec des données d'exemple)
    sample_profile = {
        "basic_info": {
            "pseudo": "test_athlete",
            "email": "test@example.com",
            "training_age": 3
        },
        "physical_metrics": {
            "weight": 75.5,
            "height": 180,
            "body_fat": 15.0
        },
        "sport_context": {
            "sport": "Rugby",
            "level": "Intermédiaire",
            "position": "Demi"
        }
    }
    test_endpoint("POST", "/user/profile/complete", sample_profile)
    
    # 3. Test POST /user/profile/sections/basic_info
    basic_info_update = {
        "pseudo": "athlete_updated",
        "email": "updated@example.com",
        "birth_date": "1990-01-01"
    }
    test_endpoint("POST", "/user/profile/sections/basic_info", basic_info_update)
    
    # 4. Test POST /user/profile/sections/physical_metrics
    physical_update = {
        "weight": 76.0,
        "height": 180,
        "body_fat": 14.5
    }
    test_endpoint("POST", "/user/profile/sections/physical_metrics", physical_update)
    
    print("
" + "=" * 50)
    print("✅ Tests terminés!")
