from app.core.cache import cached_response, ai_cache
import os
import json
import re
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import sql_models, schemas
from app.models.schemas import (
    ProfileAuditRequest, ProfileAuditResponse, 
    StrategyResponse, WeeklyPlanResponse,
    GenerateWorkoutRequest, AIWorkoutPlan
)
from dotenv import load_dotenv
from datetime import date

load_dotenv()

router = APIRouter(
    prefix="/coach",
    tags=["AI Coach"]
)

# Configuration unique de l'IA
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- UTILITAIRES ---

def clean_ai_json(text: str) -> str:
    """
    Nettoie la réponse de l'IA pour extraire uniquement le bloc JSON valide.
    Gère les cas où l'IA ajoute des balises markdown ```json ... ```.
    """
    try:
        # On cherche le contenu entre ```json et ``` ou juste ``` et ```
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return text.strip()
    except Exception:
        return text

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
    
    user_sport = profile_data.get('sport', 'Musculation')
    avail = profile_data.get('availability', [])
    
    slots_context = []
    for slot in avail:
        if slot.get('isActive', False): # Adaptation au format Flutter (isActive vs Active)
             slots_context.append({
                "Jour": slot.get('day'),
                "Moment": slot.get('moment'),
                "Dispo_Max": f"{slot.get('duration')} min",
                "Type_Cible": slot.get('type')
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
    4. "RPE Cible" doit être un ENTIER (ex: 0 pour Repos, 7 pour une séance). Ne jamais mettre null.

    FORMAT DE SORTIE (JSON OBJET) :
    {{
        "schedule": [
            {{ "Jour": "Lundi", "Créneau": "Soir", "Type": "Spécifique (PPS)", "Focus": "...", "RPE Cible": 7 }},
            ... (14 entrées pour couvrir la semaine)
        ],
        "reasoning": "Explication courte de la logique de la semaine."
    }}
    """

def get_workout_generation_prompt(profile_data, context):
    """
    Génère une séance détaillée avec gestion stricte des MODES D'ENREGISTREMENT.
    """
    sport = profile_data.get('sport', 'Musculation')
    user_level = profile_data.get('level', 'Intermédiaire')
    
    duration = context.get('duration', 60)
    energy = context.get('energy', 5)
    focus = context.get('focus', 'Full Body')
    equipment = context.get('equipment', 'Standard')

    return f"""
    RÔLE : Coach Sportif d'Élite (SmartCoach).
    MISSION : Concevoir une séance sur-mesure (JSON).

    ATHLÈTE :
    - Sport : {sport} ({user_level})
    - Blessures : {profile_data.get('injuries', 'Aucune')}
    
    CONTEXTE DU JOUR :
    - Durée Max : {duration} min
    - Énergie : {energy}/10
    - Focus demandé : {focus}
    - Matériel : {equipment}

    INSTRUCTIONS TECHNIQUES CRITIQUES :
    1. Adapte le volume (Séries/Reps) à l'énergie du jour.
    2. Pour CHAQUE exercice, tu DOIS choisir le 'recording_mode' adapté à la nature de l'effort :
       - "LOAD_REPS" : Pour la musculation classique (Haltères, Barres, Machines). Champs : Poids/Reps.
       - "BODYWEIGHT_REPS" : Pour le poids du corps (Pompes, Tractions). Champs : Lest/Reps.
       - "ISOMETRIC_TIME" : Pour le statique (Gainage, Chaise). Champs : Lest/Temps(s).
       - "PACE_DISTANCE" : Pour le Cardio/Running/Natation. Champs : Allure/Distance(m).
       - "POWER_TIME" : Pour le Vélo/Ergo. Champs : Watts/Temps(s).
    
    3. Le champ 'reps' peut être une string (ex: "10-12" ou "AMRAP") ou un nombre.
    4. Le champ 'rest' est en secondes.

    STRUCTURE DE SORTIE (JSON STRICT) :
    {{
        "title": "Nom de la séance",
        "coach_comment": "Phrase de motivation ou conseil technique.",
        "warmup": ["Exo 1", "Exo 2"],
        "exercises": [
            {{
                "name": "Squat",
                "sets": 4,
                "reps": "8-10",
                "rest": 90,
                "tips": "Dos droit, descendre sous la parallèle.",
                "recording_mode": "LOAD_REPS"
            }}
        ],
        "cooldown": ["Etirement 1"]
    }}
    """

# --- ROUTES ---

@router.post("/audit", response_model=ProfileAuditResponse)
async def audit_profile(
    payload: ProfileAuditRequest,
    current_user: sql_models.User = Depends(get_current_user)
):
    if not GEMINI_API_KEY: raise HTTPException(status_code=500, detail="Clé API manquante.")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(get_profile_analysis_prompt(payload.profile_data))
        # Ici on garde le texte brut car c'est du Markdown
        return {"markdown_report": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- STRATÉGIE (Lecture & Écriture Persistante) ---

@router.get("/strategy", response_model=StrategyResponse)
async def get_strategy(
    current_user: sql_models.User = Depends(get_current_user)
):
    """Récupère la stratégie sauvegardée (si elle existe)."""
    if not current_user.strategy_data:
        raise HTTPException(status_code=404, detail="Aucune stratégie trouvée.")
    try:
        data = json.loads(current_user.strategy_data)
        return data
    except:
        raise HTTPException(status_code=500, detail="Erreur lecture stratégie.")

@router.post("/strategy", response_model=StrategyResponse)
async def generate_strategy(
    payload: ProfileAuditRequest,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """Génère ET sauvegarde la stratégie."""
    if not GEMINI_API_KEY: raise HTTPException(status_code=500, detail="Clé API manquante.")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(get_periodization_prompt(payload.profile_data))
        
        # Nettoyage et Validation JSON
        clean_text = clean_ai_json(response.text)
        strategy_data = json.loads(clean_text)
        
        # Sauvegarde en BDD
        current_user.strategy_data = json.dumps(strategy_data)
        db.commit()
        db.refresh(current_user)
        
        return strategy_data
    except Exception as e:
        print(f"❌ Erreur Strategy Gen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- PLANNING SEMAINE (Lecture & Écriture Persistante) ---

@router.get("/week", response_model=WeeklyPlanResponse)
async def get_week(
    current_user: sql_models.User = Depends(get_current_user)
):
    """Récupère la semaine type sauvegardée."""
    if not current_user.weekly_plan_data:
         raise HTTPException(status_code=404, detail="Aucune semaine trouvée.")
    try:
        data = json.loads(current_user.weekly_plan_data)
        return data
    except:
        raise HTTPException(status_code=500, detail="Erreur lecture semaine.")

@router.post("/week", response_model=WeeklyPlanResponse)
async def generate_week(
    payload: ProfileAuditRequest,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """Génère ET sauvegarde la semaine type."""
    if not GEMINI_API_KEY: raise HTTPException(status_code=500, detail="Clé API manquante.")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
        
        prompt = get_weekly_planning_prompt(payload.profile_data)
        response = model.generate_content(prompt)
        
        # Nettoyage et Parsing
        clean_text = clean_ai_json(response.text)
        result = json.loads(clean_text)
        
        if "schedule" not in result and isinstance(result, list):
            result = {"schedule": result, "reasoning": "Généré automatiquement."}
        
        # Sauvegarde en BDD
        current_user.weekly_plan_data = json.dumps(result)
        db.commit()
        db.refresh(current_user)
            
        return result
    except Exception as e:
        print(f"❌ Erreur Week Gen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- GESTION DES SÉANCES & BROUILLONS ---

@router.get("/workout/draft", response_model=AIWorkoutPlan)
async def get_draft_workout(
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    [DEV-CARD #05] Récupère le brouillon de séance en cours (si existant).
    Utile pour reprendre une session après un crash.
    """
    if not current_user.draft_workout_data:
        raise HTTPException(status_code=404, detail="Aucun brouillon trouvé.")
    
    try:
        return json.loads(current_user.draft_workout_data)
    except:
        raise HTTPException(status_code=500, detail="Erreur lecture brouillon.")

@router.delete("/workout/draft")
async def discard_draft_workout(
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    [DEV-CARD #05-B] Supprime explicitement le brouillon (Abandon).
    """
    try:
        current_user.draft_workout_data = None
        db.commit()
        return {"status": "success", "message": "Brouillon supprimé."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workout", response_model=AIWorkoutPlan)
@cached_response(ttl_hours=6)  # Cache de 6h pour les séances similaires
async def generate_workout(
    payload: GenerateWorkoutRequest,
    db: Session = Depends(get_db),
    current_user: sql_models.User = Depends(get_current_user)
):
    """
    Génère une séance détaillée ET la sauvegarde en brouillon.
    """
    if not GEMINI_API_KEY: raise HTTPException(status_code=500, detail="Clé API manquante.")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
        
        prompt = get_workout_generation_prompt(payload.profile_data, payload.context)
        response = model.generate_content(prompt)
        
        # Nettoyage et Parsing
        clean_text = clean_ai_json(response.text)
        parsed_response = json.loads(clean_text)
        
        if isinstance(parsed_response, list):
            if parsed_response:
                parsed_response = parsed_response[0]
            else:
                raise ValueError("L'IA a renvoyé une liste vide.")
        
        # [DEV-CARD #05] Sauvegarde automatique du brouillon
        current_user.draft_workout_data = json.dumps(parsed_response)
        db.commit()
        db.refresh(current_user)

        return parsed_response
    except Exception as e:
        print(f"❌ Erreur Workout Gen: {e}")
        raise HTTPException(status_code=500, detail=str(e))