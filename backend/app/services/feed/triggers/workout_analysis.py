import os
import json
import re
import google.generativeai as genai
from typing import Dict, Any, Optional
from app.services.feed.triggers.base import BaseTrigger
from app.models import schemas, sql_models
from app.domain.bioenergetics import BioenergeticService

class WorkoutAnalysisTrigger(BaseTrigger):
    """
    Trigger : Analyse Post-Séance Avancée (Bio-Twin + Gemini).
    Condition : Une séance vient d'être terminée.
    Action : 
        1. Calcule les métriques bioénergétiques (Kcal, Macros).
        2. Génère un rapport JSON complet via IA.
        3. Sauvegarde le rapport dans la séance (Persistance).
        4. Crée une carte Feed pour notifier l'athlète.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    async def check(self, user_id: int, context: Dict[str, Any]) -> Optional[schemas.FeedItemCreate]:
        # 1. Vérifie si le contexte contient les données requises
        workout: sql_models.WorkoutSession = context.get("workout")
        profile_data: Dict[str, Any] = context.get("profile", {})
        
        if not workout:
            return None

        # 2. Si pas de clé API, on sort silencieusement
        if not self.api_key:
            return None

        try:
            # 3. PHASE 1 : CALCULS BIOÉNERGÉTIQUES (Les Maths)
            bio_metrics = BioenergeticService.calculate_needs(
                profile_data, 
                workout.sets, 
                workout.duration, 
                workout.rpe
            )
            
            # 4. PHASE 2 : GÉNÉRATION IA (Le Cerveau)
            sets_summary = "\n".join([
                f"- {s.exercise_name}: {s.weight} (load/watts) x {s.reps} (reps/sec/m) [{s.metric_type}]"
                for s in workout.sets
            ])
            
            prompt = f"""
            RÔLE : Expert en Physiologie Sportive et Nutrition (TitanFlow).
            TACHE : Analyser la séance et générer un rapport JSON strict.

            === DONNÉES ATHLÈTE ===
            - Profil : {json.dumps(profile_data, ensure_ascii=False)}
            
            === DONNÉES SÉANCE ===
            - Durée : {workout.duration} min
            - RPE : {workout.rpe}/10 (Intensité Ressentie)
            - Contenu :
            {sets_summary}
            
            === DONNÉES BIO-TWIN (CALCULÉES) ===
            - Dépense : ~{bio_metrics['kcal_total']} kcal
            - Besoins Post-Effort (Estimés) : 
              * Protéines : {bio_metrics['protein_g']}g
              * Glucides : {bio_metrics['carbs_g']}g
              * Eau : {bio_metrics['water_ml']}ml
            
            === STRUCTURE DE SORTIE (JSON UNIQUEMENT) ===
            {{
              "performance_analysis": "Analyse technique de la charge et du volume en 2 phrases max.",
              "nutrition_comment": "Conseil précis validant ou ajustant les macros calculées ci-dessus.",
              "recovery_score": 8,
              "coach_questions": ["Question pertinente 1?", "Question pertinente 2?"],
              "food_suggestion": {{
                  "option_shake": "Ex: Whey + Banane",
                  "option_solid": "Ex: Poulet + Riz + Légumes"
              }},
              "feed_message": "Une phrase d'accroche très courte (max 12 mots) pour la notification."
            }}
            """

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
            response = model.generate_content(prompt)
            
            # Nettoyage JSON
            json_str = self._clean_json(response.text)
            analysis_result = json.loads(json_str)

            # 5. PHASE 3 : PERSISTANCE (Sauvegarde en BDD)
            # On fusionne les métriques calculées avec l'analyse IA
            full_report = {
                **analysis_result,
                "bio_metrics": bio_metrics
            }
            
            # On stocke le JSON stringifié dans la colonne ai_analysis de la séance
            # Note: L'objet 'workout' est attaché à la session DB, donc le commit du TriggerEngine validera cette modif.
            workout.ai_analysis = json.dumps(full_report)

            # 6. PHASE 4 : NOTIFICATION (Le Feed)
            # On utilise le message court généré par l'IA pour le feed
            feed_msg = analysis_result.get("feed_message", "Analyse de séance disponible.")

            return schemas.FeedItemCreate(
                type=schemas.FeedItemType.ANALYSIS,
                title="Rapport de Séance",
                message=feed_msg,
                priority=5,
                action_payload={
                    "route": "/history", 
                    # On pourra passer des args pour ouvrir directement le détail plus tard
                    "args": {"workout_id": workout.id}
                }
            )

        except Exception as e:
            print(f"⚠️ Erreur IA Analysis: {e}")
            # Fallback : Si l'IA plante, on ne crée pas de FeedItem, 
            # ou on pourrait en créer un générique. Ici on choisit la discrétion.
            return None

    def _clean_json(self, text: str) -> str:
        """Extrait le JSON si l'IA ajoute du markdown."""
        try:
            pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
            return text.strip()
        except:
            return text