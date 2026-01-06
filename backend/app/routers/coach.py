import os
import json
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ProfileAuditRequest, ProfileAuditResponse, StrategyResponse, WeeklyPlanResponse
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

    CONSIGNES DE PÉRIODISATION :
    - Divise la période en BLOCS (PHASES) de 3 à 8 semaines.
    - Génère entre 3 et 6 phases majeures.

    STRUCTURE DE SORTIE (JSON STRICT) :
    {{
        "periodization_title": "Nom scientifique",
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

def get_weekly_planning_prompt(profile_data):
    """Génère le prompt complexe pour la semaine type."""
    
    # 1. Extraction contextuelle
    user_sport = profile_data.get('sport', 'Musculation')
    avail = profile_data.get('availability', [])
    
    # On reformate les dispos pour l'IA (plus lisible)
    slots_context = []
    for slot in avail:
        # On ne garde que les champs pertinents
        if slot.get('isActive', False): # Attention: Flutter envoie 'isActive', Streamlit 'Active'
             slots_context.append({
                "Jour": slot.get('day'),
                "Moment": slot.get('moment'),
                "Dispo_Max": f"{slot.get('duration')} min",
                "Type_Cible": slot.get('type') # 'PPS', 'PPG', 'Libre'
            })
    
    avail_json = json.dumps(slots_context, ensure_ascii=False, indent=2)

    return f"""
    RÔLE : Entraîneur Expert en {user_sport}.
    MISSION : Générer la SEMAINE TYPE (Lundi-Dimanche) pour cet athlète.

    CONTEXTE ATHLÈTE :
    - Sport : {user_sport}
    - Niveau : {profile_data.get('level')}
    - Objectif : {profile_data.get('goal')}

    === CONTRAINTES STRICTES (MATRICE DE DISPONIBILITÉ) ===
    Tu DOIS respecter ces créneaux à la lettre. Si un jour n'est pas listé ci-dessous, c'est REPOS.
    {avail_json}

    RÈGLES D'ALLOCATION :
    1. Pour chaque créneau disponible, assigne une séance précise.
    2. Respecte le "Type_Cible" imposé par l'utilisateur :
       - "PPS" = Sport Spécifique (Terrain, Piste, Bassin).
       - "PPG" = Renforcement / Muscu.
       - "Libre" = Choisis le mieux adapté pour l'équilibre.
    3. Si pas de créneau dispo un jour -> "Type": "Repos", "Focus": "Récupération".

    FORMAT DE SORTIE (JSON OBJET) :
    {{
        "schedule": [
            {{ "Jour": "Lundi", "Créneau": "Soir", "Type": "Spécifique (PPS)", "Focus": "...", "RPE Cible": 7 }},
            ... (14 entrées pour couvrir Matin/Soir ou juste les jours pertinents, mais assure toi de couvrir la semaine)
        ],
        "reasoning": "Explication courte de la logique de la semaine."
    }}
    Important : Le tableau "schedule" doit être complet et cohérent.
    """

# --- ROUTES ---

@router.post("/audit", response_model=ProfileAuditResponse)
async def audit_profile(payload: ProfileAuditRequest):
    if not GEMINI_API_KEY: raise HTTPException(status_code=500, detail="Clé API manquante.")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(get_profile_analysis_prompt(payload.profile_data))
        return {"markdown_report": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy", response_model=StrategyResponse)
async def generate_strategy(payload: ProfileAuditRequest):
    if not GEMINI_API_KEY: raise HTTPException(status_code=500, detail="Clé API manquante.")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(get_periodization_prompt(payload.profile_data))
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/week", response_model=WeeklyPlanResponse)
async def generate_week(payload: ProfileAuditRequest):
    """Génère la semaine type."""
    if not GEMINI_API_KEY: raise HTTPException(status_code=500, detail="Clé API manquante.")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # On force le JSON pour avoir la structure exacte
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
        
        prompt = get_weekly_planning_prompt(payload.profile_data)
        response = model.generate_content(prompt)
        
        # Parsing et nettoyage
        result = json.loads(response.text)
        
        # Petit filet de sécurité si l'IA oublie la clé racine
        if "schedule" not in result and isinstance(result, list):
            result = {"schedule": result, "reasoning": "Généré automatiquement."}
            
        return result
    except Exception as e:
        print(f"❌ Erreur Week Gen: {e}")
        raise HTTPException(status_code=500, detail=str(e))