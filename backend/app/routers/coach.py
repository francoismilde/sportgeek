import os
import json
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ProfileAuditRequest, ProfileAuditResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/coach",
    tags=["AI Coach"]
)

# Configuration unique de l'IA
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_profile_analysis_prompt(profile_data):
    """
    Génère le prompt pour l'audit (Adapté de ton code Streamlit).
    """
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
    Utilise des emojis. Sois direct, bienveillant mais exigeant (Style "Titan").
    
    Structure ta réponse ainsi :
    ### ✅ Points Forts
    ...
    ### ⚠️ Risques & Incohérences
    ...
    ### 🏆 Recommandation Stratégique
    (Donne une direction claire pour les 3 prochains mois)
    """

@router.post("/audit", response_model=ProfileAuditResponse)
async def audit_profile(payload: ProfileAuditRequest):
    """
    Envoie le profil complet à Gemini pour une analyse textuelle.
    """
    if not GEMINI_API_KEY:
        print("❌ Erreur : GEMINI_API_KEY est vide sur le serveur.")
        raise HTTPException(status_code=500, detail="Clé API Gemini manquante sur le serveur.")

    try:
        # 1. Configurer Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash') # Ou gemini-pro selon dispo

        # 2. Préparer le prompt
        prompt = get_profile_analysis_prompt(payload.profile_data)

        # 3. Appel IA
        response = model.generate_content(prompt)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Réponse vide de l'IA.")

        return {"markdown_report": response.text}

    except Exception as e:
        print(f"❌ Erreur Gemini : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse IA : {str(e)}")