import os
import json
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ProfileAuditRequest, ProfileAuditResponse, StrategyResponse
from dotenv import load_dotenv
from datetime import date

load_dotenv()

router = APIRouter(
    prefix="/coach",
    tags=["AI Coach"]
)

# Configuration unique de l'IA
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- PROMPTS ---

def get_profile_analysis_prompt(profile_data):
    """Génère le prompt pour l'audit du profil."""
    profile_str = json.dumps(profile_data, ensure_ascii=False, indent=2)
    return f"""
    RÔLE : Tu es le Lead Sport Scientist d'une fédération olympique (TitanFlow).
    TACHE : Auditer le profil d'un athlète et DÉFINIR LA LIGNE DIRECTRICE.
    
    DONNÉES BRUTES ATHLÈTE (JSON) :
    {profile_str}

    CONSIGNES D'ANALYSE :
    1. Vérifie la cohérence "Niveau vs Performances".
    2. Vérifie la cohérence "Objectif vs Logistique (Dispo)".
    3. Identifie les risques de blessures ou les incohérences majeures.
    
    FORMAT DE SORTIE :
    Réponds UNIQUEMENT en Markdown bien formaté.
    Utilise des emojis. Sois direct, bienveillant mais exigeant.
    """

def get_periodization_prompt(profile_data):
    """Génère le prompt pour la stratégie de périodisation (JSON)."""
    today_str = date.today().strftime("%Y-%m-%d")
    profile_str = json.dumps(profile_data, ensure_ascii=False, indent=2)
    
    # On extrait l'objectif et la date cible du profil
    cycle_goal = profile_data.get('goal', 'Performance Générale')
    target_date_str = profile_data.get('target_date', '2025-12-31')

    return f"""
    RÔLE : Directeur de Performance Sportive (Haut Niveau).
    CONTEXTE : Créer une PÉRIODISATION MACRO (Les Grandes Phases) pour un athlète.

    1. DONNÉES ATHLÈTE :
    {profile_str}

    2. PARAMÈTRES DU CYCLE :
    - Objectif : {cycle_goal}
    - Date actuelle : {today_str}
    - Deadline : {target_date_str}

    CONSIGNES DE PÉRIODISATION (MACRO-GRANULARITÉ) :
    - Divise la période (de maintenant à la deadline) en BLOCS (PHASES) de 3 à 8 semaines.
    - Génère entre 3 et 6 phases majeures (ex: Base, Build, Peak, Taper).
    - Adapte la fréquence d'entraînement au niveau de l'athlète.

    STRUCTURE DE SORTIE (JSON STRICT - RIEN D'AUTRE) :
    {{
        "periodization_title": "Nom scientifique (ex: Périodisation Ondulatoire)",
        "periodization_logic": "Justification courte.",
        "progression_model": "Ex: RPE Progression.",
        "recommended_frequency": 4, 
        "phases": [
            {{
                "phase_name": "Phase 1 : [Nom]",
                "focus": "Objectif physiologique",
                "intensity_metric": "RPE 7-8", 
                "volume_strategy": "Ex: Volume Élevé",
                "start": "YYYY-MM-DD",
                "end": "YYYY-MM-DD"
            }}
        ]
    }}
    """

# --- ROUTES ---

@router.post("/audit", response_model=ProfileAuditResponse)
async def audit_profile(payload: ProfileAuditRequest):
    """Envoie le profil complet à Gemini pour une analyse textuelle."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Clé API Gemini manquante.")

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = get_profile_analysis_prompt(payload.profile_data)
        response = model.generate_content(prompt)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Réponse vide de l'IA.")

        return {"markdown_report": response.text}

    except Exception as e:
        print(f"❌ Erreur Audit : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy", response_model=StrategyResponse)
async def generate_strategy(payload: ProfileAuditRequest):
    """Génère la stratégie de périodisation (JSON) via Gemini."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Clé API Gemini manquante.")

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # On force le mode JSON pour s'assurer que Gemini renvoie bien la structure
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
        
        prompt = get_periodization_prompt(payload.profile_data)
        
        response = model.generate_content(prompt)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Réponse vide de l'IA.")

        # Parsing du JSON retourné par l'IA
        strategy_data = json.loads(response.text)
        
        return strategy_data

    except json.JSONDecodeError:
        print("❌ Erreur JSON Gemini : Le modèle n'a pas renvoyé un JSON valide.")
        raise HTTPException(status_code=500, detail="L'IA a généré un format invalide.")
    except Exception as e:
        print(f"❌ Erreur Strategy : {e}")
        raise HTTPException(status_code=500, detail=str(e))