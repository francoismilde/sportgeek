"""
Service de gestion de la mémoire du coach
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models import sql_models
from app.domain.bioenergetics import BioenergeticService

logger = logging.getLogger(__name__)

class CoachMemoryService:
    """Service principal pour la mémoire du coach"""
    
    @staticmethod
    def initialize_coach_memory(athlete_profile: sql_models.AthleteProfile, db: Session) -> sql_models.CoachMemory:
        """Initialise la mémoire du coach à partir du profil"""
        logger.info(f"Initialisation de la mémoire du coach pour l'athlète {athlete_profile.user_id}")
        
        # Extraire les données du profil
        basic_info = json.loads(athlete_profile.basic_info) if athlete_profile.basic_info else {}
        sport_context = json.loads(athlete_profile.sport_context) if athlete_profile.sport_context else {}
        performance_baseline = json.loads(athlete_profile.performance_baseline) if athlete_profile.performance_baseline else {}
        
        # Calculer les insights initiaux
        sport_insights = CoachMemoryService._calculate_initial_sport_insights(sport_context, basic_info)
        performance_baselines = CoachMemoryService._extract_initial_baselines(performance_baseline)
        initial_phase = CoachMemoryService._determine_initial_phase(athlete_profile)
        
        # Créer la mémoire
        memory = sql_models.CoachMemory(
            athlete_profile_id=athlete_profile.id,
            metadata=json.dumps({
                "athlete_id": athlete_profile.user_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "total_interactions": 0,
                "trust_score": 50,
                "data_points": 0
            }),
            current_context=json.dumps({
                'season_week': 1,
                'macrocycle_phase': initial_phase,
                'mesocycle_focus': 'base_fitness',
                'training_priority': 'volume',
                'next_competition': None,
                'days_to_competition': None,
                'fatigue_state': 'fresh',
                'readiness_score': 80,
                'current_constraints': json.loads(athlete_profile.constraints) if athlete_profile.constraints else {},
                'environmental_factors': {},
                'last_session_type': None,
                'last_session_rpe': None
            }),
            response_patterns=json.dumps({
                "volume_response": "neutral",
                "optimal_volumes": {},
                "intensity_tolerance": "medium",
                "recovery_profile": "normal",
                "fatigue_indicators": []
            }),
            performance_baselines=json.dumps(performance_baselines),
            adaptation_signals=json.dumps({
                "positive_adaptations": [],
                "last_adaptation_phase": None,
                "current_adaptation_status": "initial",
                "stagnation_signals": [],
                "regression_signals": [],
                "adaptation_windows": [],
                "next_suggested_focus": "base_fitness"
            }),
            sport_specific_insights=json.dumps(sport_insights),
            training_history_summary=json.dumps({
                "total_volume_by_type": {},
                "average_rpe_by_type": {},
                "successful_strategies": [],
                "failed_strategies": [],
                "lessons_learned": [],
                "seasonal_patterns": {},
                "best_training_weeks": [],
                "peak_periods": []
            }),
            athlete_preferences=json.dumps(json.loads(athlete_profile.training_preferences) if athlete_profile.training_preferences else {}),
            coach_notes=json.dumps({}),
            memory_flags=json.dumps({
                "needs_deload": False,
                "approaching_overtraining": False,
                "detraining_risk": False,
                "technique_regression": False,
                "adaptation_window_open": True,
                "pr_potential": False,
                "skill_integration_ready": False,
                "external_stress_high": False,
                "recovery_impaired": False,
                "motivation_low": False
            })
        )
        
        db.add(memory)
        db.commit()
        logger.info(f"Mémoire du coach créée avec ID: {memory.id}")
        
        return memory
    
    @staticmethod
    def process_workout_session(
        coach_memory: sql_models.CoachMemory,
        athlete_profile: sql_models.AthleteProfile,
        session_data: Dict[str, Any],
        db: Session
    ) -> None:
        """Traite une séance d'entraînement et met à jour la mémoire"""
        logger.info(f"Traitement de la séance pour la mémoire {coach_memory.id}")
        
        # Mettre à jour les métadonnées
        metadata = json.loads(coach_memory.metadata) if coach_memory.metadata else {}
        metadata['total_interactions'] = metadata.get('total_interactions', 0) + 1
        metadata['last_updated'] = datetime.utcnow().isoformat()
        
        # Mettre à jour le contexte
        context = json.loads(coach_memory.current_context) if coach_memory.current_context else {}
        context['last_session_type'] = session_data.get('type', 'unknown')
        context['last_session_rpe'] = session_data.get('rpe', 0)
        context['last_session_date'] = datetime.now().isoformat()
        
        # Mettre à jour l'historique d'entraînement
        history = json.loads(coach_memory.training_history_summary) if coach_memory.training_history_summary else {}
        
        session_type = session_data.get('type', 'strength')
        volume = session_data.get('volume', 0)
        rpe = session_data.get('rpe', 5)
        
        if 'total_volume_by_type' not in history:
            history['total_volume_by_type'] = {}
        
        history['total_volume_by_type'][session_type] = history['total_volume_by_type'].get(session_type, 0) + volume
        
        if 'average_rpe_by_type' not in history:
            history['average_rpe_by_type'] = {}
        
        if session_type not in history['average_rpe_by_type']:
            history['average_rpe_by_type'][session_type] = {'total': 0, 'count': 0}
        
        history['average_rpe_by_type'][session_type]['total'] += rpe
        history['average_rpe_by_type'][session_type]['count'] += 1
        
        # Calculer les réponses à l'entraînement
        response_patterns = json.loads(coach_memory.response_patterns) if coach_memory.response_patterns else {}
        
        # Mettre à jour la mémoire
        coach_memory.metadata = json.dumps(metadata)
        coach_memory.current_context = json.dumps(context)
        coach_memory.training_history_summary = json.dumps(history)
        coach_memory.response_patterns = json.dumps(response_patterns)
        
        db.commit()
        logger.info(f"Séance traitée pour la mémoire {coach_memory.id}")
    
    @staticmethod
    def update_daily_context(
        coach_memory: sql_models.CoachMemory,
        checkin_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Met à jour le contexte quotidien"""
        logger.info(f"Mise à jour du contexte quotidien pour la mémoire {coach_memory.id}")
        
        context = json.loads(coach_memory.current_context) if coach_memory.current_context else {}
        
        # Calculer le score de préparation
        readiness_score = CoachMemoryService._calculate_readiness_score(checkin_data, context)
        context['readiness_score'] = readiness_score
        
        # Mettre à jour l'état de fatigue
        context['fatigue_state'] = CoachMemoryService._determine_fatigue_state(readiness_score)
        
        # Mettre à jour les flags de mémoire
        memory_flags = json.loads(coach_memory.memory_flags) if coach_memory.memory_flags else {}
        memory_flags['needs_deload'] = readiness_score < 40
        memory_flags['adaptation_window_open'] = readiness_score > 70
        memory_flags['recovery_impaired'] = checkin_data.get('sleep_quality', 5) < 4
        
        # Mettre à jour la mémoire
        coach_memory.current_context = json.dumps(context)
        coach_memory.memory_flags = json.dumps(memory_flags)
        
        db.commit()
        
        logger.info(f"Contexte mis à jour - Readiness: {readiness_score}, Fatigue: {context['fatigue_state']}")
        
        return context
    
    @staticmethod
    def generate_insights(
        coach_memory: sql_models.CoachMemory,
        athlete_profile: sql_models.AthleteProfile,
        db: Session
    ) -> Dict[str, Any]:
        """Génère des insights basés sur la mémoire"""
        context = json.loads(coach_memory.current_context) if coach_memory.current_context else {}
        performance_baselines = json.loads(coach_memory.performance_baselines) if coach_memory.performance_baselines else {}
        sport_insights = json.loads(coach_memory.sport_specific_insights) if coach_memory.sport_specific_insights else {}
        
        insights = {
            "readiness_insight": CoachMemoryService._generate_readiness_insight(context),
            "fatigue_management": CoachMemoryService._generate_fatigue_insight(context),
            "progression_opportunities": CoachMemoryService._generate_progression_insights(performance_baselines),
            "sport_specific_recommendations": CoachMemoryService._generate_sport_recommendations(sport_insights),
            "risk_assessment": CoachMemoryService._generate_risk_assessment(coach_memory)
        }
        
        return insights
    
    @staticmethod
    def recalculate_memory(
        coach_memory: sql_models.CoachMemory,
        athlete_profile: sql_models.AthleteProfile,
        db: Session
    ) -> None:
        """Recalcule complètement la mémoire"""
        logger.info(f"Recalcul complet de la mémoire {coach_memory.id}")
        
        # Recalculer tous les composants
        metadata = json.loads(coach_memory.metadata) if coach_memory.metadata else {}
        metadata['last_recalculated'] = datetime.utcnow().isoformat()
        metadata['version'] = metadata.get('version', 1) + 1
        
        # Recalculer les performances de base
        performance_baseline = json.loads(athlete_profile.performance_baseline) if athlete_profile.performance_baseline else {}
        updated_baselines = CoachMemoryService._extract_initial_baselines(performance_baseline)
        
        # Mettre à jour la mémoire
        coach_memory.metadata = json.dumps(metadata)
        coach_memory.performance_baselines = json.dumps(updated_baselines)
        coach_memory.version = metadata['version']
        
        db.commit()
        logger.info(f"Mémoire {coach_memory.id} recalculée - version {metadata['version']}")
    
    # Méthodes privées helper
    @staticmethod
    def _calculate_initial_sport_insights(sport_context: Dict[str, Any], basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule les insights sportifs initiaux"""
        primary_sport = sport_context.get('primary_sport', 'Musculation')
        position = sport_context.get('playing_position')
        level = sport_context.get('competition_level', 'Amateur')
        
        insights = {
            "primary_sport": primary_sport,
            "sport_requirements": CoachMemoryService._get_sport_requirements(primary_sport, position),
            "transfer_efficiency": 0.0,
            "high_transfer_exercises": CoachMemoryService._get_high_transfer_exercises(primary_sport),
            "low_transfer_exercises": [],
            "position_demands": CoachMemoryService._get_position_demands(primary_sport, position),
            "sport_skills_to_maintain": CoachMemoryService._get_sport_skills(primary_sport),
            "specificity_index": 0.5,
            "training_age_factor": basic_info.get('training_age', 1) / 10.0
        }
        
        return insights
    
    @staticmethod
    def _extract_initial_baselines(performance_baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les performances de base"""
        return {
            "current_prs": performance_baseline.get('current_prs', {}),
            "metric_trends": {},
            "progress_rate": 0.0,
            "strength_ratios": CoachMemoryService._calculate_strength_ratios(performance_baseline.get('current_prs', {})),
            "balance_scores": {},
            "last_assessment_date": datetime.now().strftime('%Y-%m-%d')
        }
    
    @staticmethod
    def _determine_initial_phase(athlete_profile: sql_models.AthleteProfile) -> str:
        """Détermine la phase initiale du macrocycle"""
        goals = json.loads(athlete_profile.goals) if athlete_profile.goals else {}
        target_date = goals.get('target_date')
        
        if target_date:
            target = datetime.strptime(target_date, '%Y-%m-%d')
            days_until = (target - datetime.now()).days
            
            if days_until > 120:
                return "base_fitness"
            elif days_until > 60:
                return "build"
            elif days_until > 30:
                return "peak"
            else:
                return "competition"
        else:
            return "base_fitness"
    
    @staticmethod
    def _calculate_readiness_score(checkin_data: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calcule le score de préparation quotidien"""
        sleep_quality = checkin_data.get('sleep_quality', 5) / 10.0 * 30  # 30%
        sleep_duration = min(checkin_data.get('sleep_duration', 7) / 9.0 * 20, 20)  # 20%
        stress = (10 - checkin_data.get('perceived_stress', 5)) / 10.0 * 20  # 20%
        soreness = (10 - checkin_data.get('muscle_soreness', 5)) / 10.0 * 15  # 15%
        energy = checkin_data.get('energy_level', 5) / 10.0 * 15  # 15%
        
        readiness = sleep_quality + sleep_duration + stress + soreness + energy
        
        # Ajuster basé sur l'historique récent
        last_readiness = context.get('readiness_score', 70)
        adjusted_readiness = (readiness * 0.7) + (last_readiness * 0.3)
        
        return round(adjusted_readiness, 1)
    
    @staticmethod
    def _determine_fatigue_state(readiness_score: float) -> str:
        """Détermine l'état de fatigue basé sur le score de préparation"""
        if readiness_score >= 80:
            return "fresh"
        elif readiness_score >= 60:
            return "normal"
        elif readiness_score >= 40:
            return "accumulated"
        else:
            return "exhausted"
    
    @staticmethod
    def _generate_readiness_insight(context: Dict[str, Any]) -> str:
        """Génère un insight basé sur le score de préparation"""
        readiness = context.get('readiness_score', 70)
        
        if readiness >= 80:
            return "État de récupération optimal - prêt pour des séances exigeantes"
        elif readiness >= 60:
            return "État normal - bon pour l'entraînement planifié"
        elif readiness >= 40:
            return "Fatigue accumulée - envisager une réduction du volume"
        else:
            return "Fatigue importante - nécessite une récupération active ou repos"
    
    @staticmethod
    def _generate_fatigue_insight(context: Dict[str, Any]) -> str:
        """Génère un insight sur la gestion de la fatigue"""
        fatigue_state = context.get('fatigue_state', 'normal')
        last_session_rpe = context.get('last_session_rpe', 5)
        
        if fatigue_state == "fresh" and last_session_rpe > 7:
            return "Bonne adaptation à l'intensité - peut progresser"
        elif fatigue_state == "accumulated":
            return "Fatigue en accumulation - surveiller les signes de surentraînement"
        elif fatigue_state == "exhausted":
            return "État d'épuisement - prioriser la récupération"
        else:
            return "Gestion de fatigue équilibrée"
    
    @staticmethod
    def _generate_progression_insights(performance_baselines: Dict[str, Any]) -> List[str]:
        """Génère des insights sur la progression"""
        insights = []
        current_prs = performance_baselines.get('current_prs', {})
        
        if 'squat_1rm' in current_prs and 'deadlift_1rm' in current_prs:
            squat = current_prs['squat_1rm']
            deadlift = current_prs['deadlift_1rm']
            
            if deadlift > squat * 1.2:
                insights.append("Rapport squat/deadlift déséquilibré - travailler le squat")
            elif squat > deadlift * 0.9:
                insights.append("Bon équilibre de force entre squat et deadlift")
        
        if 'bench_1rm' in current_prs:
            bench = current_prs['bench_1rm']
            if 'bodyweight' in current_prs:
                bw = current_prs['bodyweight']
                if bench > bw * 1.5:
                    insights.append("Force au bench excellente")
                elif bench < bw:
                    insights.append("Potentiel d'amélioration au bench")
        
        return insights
    
    @staticmethod
    def _generate_sport_recommendations(sport_insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des recommandations spécifiques au sport"""
        recommendations = []
        primary_sport = sport_insights.get('primary_sport', 'Musculation')
        
        if primary_sport == 'Rugby':
            recommendations.append({
                "focus": "Puissance",
                "exercices": ["Squat explosif", "Power clean", "Sprints"],
                "ratio": "70% puissance / 30% endurance"
            })
        elif primary_sport == 'Football':
            recommendations.append({
                "focus": "Endurance intermittente",
                "exercices": ["Sprints répétés", "Pliométrie", "Circuits"],
                "ratio": "60% endurance / 40% puissance"
            })
        elif primary_sport == 'Natation':
            recommendations.append({
                "focus": "Endurance et technique",
                "exercices": ["Tirage élastique", "Gainage", "Mobilité épaules"],
                "ratio": "50% natation / 30% PPG / 20% muscu"
            })
        
        return recommendations
    
    @staticmethod
    def _generate_risk_assessment(coach_memory: sql_models.CoachMemory) -> Dict[str, Any]:
        """Évalue les risques basés sur la mémoire"""
        memory_flags = json.loads(coach_memory.memory_flags) if coach_memory.memory_flags else {}
        context = json.loads(coach_memory.current_context) if coach_memory.current_context else {}
        
        risks = {
            "overtraining_risk": "low",
            "injury_risk": "low",
            "detraining_risk": "low",
            "motivation_risk": "low"
        }
        
        if memory_flags.get('approaching_overtraining'):
            risks["overtraining_risk"] = "high"
        
        if memory_flags.get('needs_deload'):
            risks["injury_risk"] = "medium"
        
        if memory_flags.get('detraining_risk'):
            risks["detraining_risk"] = "high"
        
        if memory_flags.get('motivation_low'):
            risks["motivation_risk"] = "high"
        
        readiness = context.get('readiness_score', 70)
        if readiness < 40:
            risks["overtraining_risk"] = "high"
            risks["injury_risk"] = "high"
        
        return risks
    
    @staticmethod
    def _get_sport_requirements(sport: str, position: Optional[str] = None) -> Dict[str, Any]:
        """Retourne les exigences spécifiques au sport"""
        requirements = {
            "Musculation": {
                "strength": "high",
                "power": "medium",
                "endurance": "low",
                "mobility": "medium",
                "recovery": "high"
            },
            "Rugby": {
                "strength": "very high",
                "power": "very high",
                "endurance": "high",
                "mobility": "medium",
                "recovery": "high"
            },
            "Football": {
                "strength": "medium",
                "power": "high",
                "endurance": "very high",
                "mobility": "high",
                "recovery": "medium"
            },
            "Natation": {
                "strength": "medium",
                "power": "medium",
                "endurance": "very high",
                "mobility": "very high",
                "recovery": "medium"
            }
        }
        
        return requirements.get(sport, requirements["Musculation"])
    
    @staticmethod
    def _get_high_transfer_exercises(sport: str) -> List[str]:
        """Retourne les exercices à haut transfert pour le sport"""
        transfers = {
            "Rugby": ["Squat", "Deadlift", "Power clean", "Bench press", "Sprints"],
            "Football": ["Squat", "Lunges", "Box jumps", "Sprints", "Plyometrics"],
            "Natation": ["Pull-ups", "Lat pulldowns", "Shoulder press", "Core work", "Rotator cuff"],
            "Musculation": ["Squat", "Deadlift", "Bench press", "Overhead press", "Rows"]
        }
        
        return transfers.get(sport, transfers["Musculation"])
    
    @staticmethod
    def _get_position_demands(sport: str, position: Optional[str] = None) -> Dict[str, Any]:
        """Retourne les exigences spécifiques à la position"""
        if sport == "Rugby" and position:
            if position in ["Pilier", "Talonneur", "2ème ligne"]:
                return {"strength": "very high", "power": "high", "endurance": "medium"}
            elif position in ["3ème ligne", "Demi"]:
                return {"strength": "high", "power": "very high", "endurance": "high"}
            else:  # Arrières
                return {"strength": "medium", "power": "high", "endurance": "very high"}
        
        return {"strength": "medium", "power": "medium", "endurance": "medium"}
    
    @staticmethod
    def _get_sport_skills(sport: str) -> List[str]:
        """Retourne les compétences techniques à maintenir"""
        skills = {
            "Rugby": ["Passe", "Jeu au pied", "Plaquage", "Ruck", "Maul"],
            "Football": ["Dribble", "Passe", "Tir", "Contrôle", "Positionnement"],
            "Natation": ["Crawl", "Dos", "Brasse", "Papillon", "Virage"],
            "Musculation": ["Technique squat", "Technique deadlift", "Technique bench", "Stabilité", "Respiration"]
        }
        
        return skills.get(sport, [])
    
    @staticmethod
    def _calculate_strength_ratios(current_prs: Dict[str, Any]) -> Dict[str, float]:
        """Calcule les ratios de force"""
        ratios = {}
        
        if 'squat_1rm' in current_prs and 'bodyweight' in current_prs:
            ratios['squat_to_bw'] = current_prs['squat_1rm'] / current_prs['bodyweight']
        
        if 'bench_1rm' in current_prs and 'bodyweight' in current_prs:
            ratios['bench_to_bw'] = current_prs['bench_1rm'] / current_prs['bodyweight']
        
        if 'deadlift_1rm' in current_prs and 'bodyweight' in current_prs:
            ratios['deadlift_to_bw'] = current_prs['deadlift_1rm'] / current_prs['bodyweight']
        
        if 'squat_1rm' in current_prs and 'bench_1rm' in current_prs:
            ratios['squat_to_bench'] = current_prs['squat_1rm'] / current_prs['bench_1rm']
        
        return ratios

# Fonctions d'interface pour compatibilité avec les routeurs
def initialize_coach_memory(athlete_profile: sql_models.AthleteProfile, db: Session) -> sql_models.CoachMemory:
    return CoachMemoryService.initialize_coach_memory(athlete_profile, db)

def process_workout_session(coach_memory: sql_models.CoachMemory, athlete_profile: sql_models.AthleteProfile, 
                          session_data: Dict[str, Any], db: Session) -> None:
    return CoachMemoryService.process_workout_session(coach_memory, athlete_profile, session_data, db)

def update_daily_context(coach_memory: sql_models.CoachMemory, checkin_data: Dict[str, Any], 
                        db: Session) -> Dict[str, Any]:
    return CoachMemoryService.update_daily_context(coach_memory, checkin_data, db)

def generate_insights(coach_memory: sql_models.CoachMemory, athlete_profile: sql_models.AthleteProfile,
                     db: Session) -> Dict[str, Any]:
    return CoachMemoryService.generate_insights(coach_memory, athlete_profile, db)

def recalculate_memory(coach_memory: sql_models.CoachMemory, athlete_profile: sql_models.AthleteProfile,
                      db: Session) -> None:
    return CoachMemoryService.recalculate_memory(coach_memory, athlete_profile, db)
