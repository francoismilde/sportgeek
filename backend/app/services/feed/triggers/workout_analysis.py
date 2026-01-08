import os
import google.generativeai as genai
from typing import Dict, Any, Optional
from app.services.feed.triggers.base import BaseTrigger
from app.models import schemas, sql_models

class WorkoutAnalysisTrigger(BaseTrigger):
    """
    Trigger : Analyse Post-Séance.
    Condition : Une séance vient d'être terminée (présente dans le contexte).
    Action : Génère un FeedItem de type ANALYSIS avec un feedback court.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    async def check(self, user_id: int, context: Dict[str, Any]) -> Optional[schemas.FeedItemCreate]:
        # 1. Vérifie si le contexte contient une séance
        workout: sql_models.WorkoutSession = context.get("workout")
        if not workout:
            return None

        # 2. Si pas de clé API, on ne fait rien (ou on loggue une erreur silencieuse)
        if not self.api_key:
            return None

        try:
            # 3. Préparation du Prompt pour l'IA
            # On construit un résumé textuel de la séance pour que l'IA comprenne
            sets_summary = "\n".join([
                f"- {s.exercise_name}: {s.weight}kg x {s.reps} ({s.metric_type})"
                for s in workout.sets
            ])
            
            prompt = f"""
            RÔLE : Coach Sportif Expert.
            TACHE : Analyser cette séance qui vient de se terminer et donner un feedback immédiat.
            
            DONNÉES SÉANCE :
            - Date : {workout.date}
            - Durée : {workout.duration} min
            - RPE (Intensité) : {workout.rpe}/10
            - Énergie ressentie : {workout.energy_level}/10
            - Exercices :
            {sets_summary}
            
            CONSIGNE DE SORTIE :
            Réponds UNIQUEMENT avec une phrase d'accroche percutante (Max 15 mots) pour féliciter ou conseiller l'athlète.
            Ton ton doit être motivant et professionnel.
            Exemple : "Grosse intensité sur les jambes, pense à bien t'hydrater ce soir !"
            """

            # 4. Appel Gemini
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            feedback_message = response.text.strip()

            # 5. Création de l'événement Feed
            return schemas.FeedItemCreate(
                type=schemas.FeedItemType.ANALYSIS,
                title="Débrief Séance",
                message=feedback_message,
                priority=5, # Priorité moyenne
                action_payload={
                    "route": "/history", # Au clic, on renvoie vers l'historique (pour l'instant)
                    "args": {"workout_id": workout.id}
                }
            )

        except Exception as e:
            print(f"⚠️ Erreur IA Analysis: {e}")
            return None