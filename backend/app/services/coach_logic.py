from datetime import date
from typing import Dict, Any
from app.models import sql_models

VALID_SPORT_POSITIONS = {
    'Rugby': ['Pilier', 'Talonneur', '2ème ligne', '3ème ligne', 'Demi', 'Centre', 'Ailier', 'Arrière'],
    'Football': ['Gardien', 'Défenseur', 'Milieu', 'Attaquant'],
}

class CoachLogic:
    @staticmethod
    def validate_sport_position(sport: str, position: str) -> bool:
        if sport in VALID_SPORT_POSITIONS:
            if position and position not in VALID_SPORT_POSITIONS[sport]:
                return False
        return True

    @staticmethod
    def initialize_memory(profile: sql_models.AthleteProfile) -> sql_models.CoachMemory:
        sport = profile.sport_context.get('sport', 'Autre')
        insights = {
            "primary_sport": sport,
            "specificity_index": "High" if sport in ['Rugby', 'Football'] else "Medium",
            "focus_areas": ["Strength", "Hypertrophy"] 
        }
        context = {
            "macrocycle_phase": "Adaptation Anatomique",
            "fatigue_state": "Fresh",
            "readiness_score": 100,
            "season_week": 1
        }
        flags = {
            "needs_deload": False,
            "injury_risk": False,
            "adaptation_window_open": True
        }
        memory = sql_models.CoachMemory(
            athlete_profile_id=profile.id,
            sport_specific_insights=insights,
            current_context=context,
            memory_flags=flags,
            coach_notes={"initialization": f"Profil créé le {date.today()}"}
        )
        return memory

    @staticmethod
    def calculate_readiness(profile: sql_models.AthleteProfile) -> int:
        base_score = 80
        sleep = profile.physical_metrics.get('sleep_quality_avg', 5)
        if sleep >= 8: base_score += 10
        elif sleep <= 4: base_score -= 20
        stress = profile.constraints.get('work_stress_level', 5)
        if stress >= 8: base_score -= 15
        return max(0, min(100, base_score))

    @staticmethod
    def update_daily(memory: sql_models.CoachMemory, profile: sql_models.AthleteProfile):
        new_readiness = CoachLogic.calculate_readiness(profile)
        current_context = dict(memory.current_context or {})
        current_context['readiness_score'] = new_readiness
        
        if new_readiness < 40:
            current_context['fatigue_state'] = "High"
        elif new_readiness < 70:
            current_context['fatigue_state'] = "Moderate"
        else:
            current_context['fatigue_state'] = "Optimal"
            
        memory.current_context = current_context
        flags = dict(memory.memory_flags or {})
        flags['needs_deload'] = new_readiness < 30
        flags['adaptation_window_open'] = new_readiness > 70
        memory.memory_flags = flags
