"""
Validateurs pour les profils athlètes
"""
import re
from datetime import datetime
from typing import Dict, Any, Optional

# Sport ↔ Position cohérence
VALID_SPORT_POSITIONS = {
    'Rugby': ['Pilier', 'Talonneur', '2ème ligne', '3ème ligne', 'Demi', 'Centre', 'Ailier', 'Arrière'],
    'Football': ['Gardien', 'Défenseur', 'Milieu', 'Attaquant'],
    'Basketball': ['Meneur', 'Arrière', 'Ailier', 'Ailier fort', 'Pivot'],
    'Natation': ['Nage libre', 'Dos', 'Brasse', 'Papillon', '4 nages'],
    'Athlétisme': ['Sprint', 'Demi-fond', 'Fond', 'Haies', 'Saut', 'Lancer'],
    'Musculation': ['Powerlifting', 'Weightlifting', 'Bodybuilding', 'CrossFit', 'Général'],
    'Cyclisme': ['Route', 'Piste', 'VTT', 'Cyclocross'],
    'Triathlon': ['Sprint', 'Olympique', 'Half-Ironman', 'Ironman'],
    'Escalade': ['Bloc', 'Difficulté', 'Vitesse'],
    'Arts martiaux': ['Judo', 'BJJ', 'Boxe', 'Muay Thai', 'MMA']
}

VALID_COMPETITION_LEVELS = ['Débutant', 'Amateur', 'Compétiteur', 'Élite', 'Professionnel']

def validate_athlete_profile(profile_data: Dict[str, Any]) -> bool:
    """
    Valide la cohérence globale d'un profil athlète
    """
    errors = []
    
    # Valider le contexte sportif
    if 'sport_context' in profile_data:
        errors.extend(validate_sport_context(profile_data['sport_context']))
    
    # Valider les métriques physiques
    if 'physical_metrics' in profile_data:
        errors.extend(validate_physical_metrics(profile_data['physical_metrics']))
    
    # Valider les objectifs
    if 'goals' in profile_data:
        errors.extend(validate_goals(profile_data['goals']))
    
    # Valider les informations de base
    if 'basic_info' in profile_data:
        errors.extend(validate_basic_info(profile_data['basic_info']))
    
    if errors:
        raise ValueError(" | ".join(errors))
    
    return True

def validate_sport_context(sport_context: Dict[str, Any]) -> list:
    """Valide le contexte sportif"""
    errors = []
    
    primary_sport = sport_context.get('primary_sport')
    if not primary_sport:
        errors.append("Le sport principal est requis")
    
    playing_position = sport_context.get('playing_position')
    if playing_position and primary_sport in VALID_SPORT_POSITIONS:
        if playing_position not in VALID_SPORT_POSITIONS[primary_sport]:
            errors.append(f"Position '{playing_position}' invalide pour le sport '{primary_sport}'")
    
    competition_level = sport_context.get('competition_level')
    if competition_level and competition_level not in VALID_COMPETITION_LEVELS:
        errors.append(f"Niveau de compétition invalide: {competition_level}")
    
    training_history = sport_context.get('training_history_years')
    if training_history and (training_history < 0 or training_history > 50):
        errors.append(f"Années d'entraînement invalides: {training_history}")
    
    return errors

def validate_physical_metrics(metrics: Dict[str, Any]) -> list:
    """Valide les métriques physiques"""
    errors = []
    
    # Validation BMI
    if metrics.get('weight') and metrics.get('height'):
        weight = float(metrics['weight'])
        height = float(metrics['height']) / 100  # Convertir en mètres
        
        if height <= 0:
            errors.append("La taille doit être positive")
        elif weight <= 0:
            errors.append("Le poids doit être positif")
        else:
            bmi = weight / (height ** 2)
            if not (16 <= bmi <= 40):
                errors.append(f"BMI {bmi:.1f} hors des limites plausibles (16-40)")
    
    # Validation fréquence cardiaque
    resting_hr = metrics.get('resting_heart_rate')
    if resting_hr:
        hr = float(resting_hr)
        if not (30 <= hr <= 120):
            errors.append(f"Fréquence cardiaque au repos {hr} hors limites (30-120 bpm)")
    
    # Validation pourcentage de graisse
    body_fat = metrics.get('body_fat_estimate')
    if body_fat:
        bf = float(body_fat)
        if not (5 <= bf <= 50):
            errors.append(f"Pourcentage de graisse {bf}% hors limites (5-50%)")
    
    # Validation qualité de sommeil
    sleep_quality = metrics.get('sleep_quality_average')
    if sleep_quality:
        sq = float(sleep_quality)
        if not (1 <= sq <= 10):
            errors.append(f"Qualité de sommeil {sq} hors échelle (1-10)")
    
    return errors

def validate_goals(goals: Dict[str, Any]) -> list:
    """Valide les objectifs"""
    errors = []
    
    primary_goal = goals.get('primary_goal')
    if not primary_goal:
        errors.append("L'objectif principal est requis")
    
    target_date = goals.get('target_date')
    if target_date:
        try:
            target = datetime.strptime(target_date, '%Y-%m-%d')
            if target < datetime.now():
                errors.append("La date cible ne peut pas être dans le passé")
        except ValueError:
            errors.append(f"Format de date invalide: {target_date}")
    
    # Valider les métriques cibles
    target_metrics = goals.get('target_metrics', {})
    for metric, value in target_metrics.items():
        if isinstance(value, (int, float)) and value <= 0:
            errors.append(f"Métrique cible '{metric}' doit être positive")
    
    return errors

def validate_basic_info(basic_info: Dict[str, Any]) -> list:
    """Valide les informations de base"""
    errors = []
    
    # Validation email
    email = basic_info.get('email')
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append("Format d'email invalide")
    
    # Validation date de naissance
    birth_date = basic_info.get('birth_date')
    if birth_date:
        try:
            birth = datetime.strptime(birth_date, '%Y-%m-%d')
            if birth > datetime.now():
                errors.append("La date de naissance ne peut pas être dans le futur")
            
            # Calculer l'âge
            age = datetime.now().year - birth.year
            if not (10 <= age <= 100):
                errors.append(f"Âge {age} hors limites plausibles (10-100 ans)")
        except ValueError:
            errors.append(f"Format de date de naissance invalide: {birth_date}")
    
    # Validation âge biologique
    bio_age = basic_info.get('biological_age')
    if bio_age and (bio_age < 10 or bio_age > 100):
        errors.append(f"Âge biologique {bio_age} hors limites (10-100)")
    
    # Validation âge d'entraînement
    training_age = basic_info.get('training_age')
    if training_age and (training_age < 0 or training_age > 50):
        errors.append(f"Âge d'entraînement {training_age} hors limites (0-50)")
    
    # Validation sexe biologique
    biological_sex = basic_info.get('biological_sex')
    if biological_sex and biological_sex not in ['Homme', 'Femme', 'Autre']:
        errors.append(f"Sexe biologique invalide: {biological_sex}")
    
    # Validation main dominante
    dominant_hand = basic_info.get('dominant_hand')
    if dominant_hand and dominant_hand not in ['Droitier', 'Gaucher', 'Ambidextre']:
        errors.append(f"Main dominante invalide: {dominant_hand}")
    
    return errors

def validate_sport_position(sport: str, position: Optional[str]) -> bool:
    """Valide la cohérence sport/position"""
    if not position:
        return True
    
    if sport in VALID_SPORT_POSITIONS:
        return position in VALID_SPORT_POSITIONS[sport]
    
    return True

def validate_competition_level(level: str) -> bool:
    """Valide le niveau de compétition"""
    return level in VALID_COMPETITION_LEVELS if level else True

def validate_training_preferences(preferences: Dict[str, Any]) -> list:
    """Valide les préférences d'entraînement"""
    errors = []
    
    max_duration = preferences.get('max_session_duration')
    if max_duration and (max_duration < 15 or max_duration > 240):
        errors.append(f"Durée maximale de session {max_duration} hors limites (15-240 min)")
    
    feedback_style = preferences.get('feedback_style')
    if feedback_style and feedback_style not in ['Direct', 'Encourageant', 'Technique', 'Mixte']:
        errors.append(f"Style de feedback invalide: {feedback_style}")
    
    autonomy_preference = preferences.get('autonomy_preference')
    if autonomy_preference and autonomy_preference not in ['Faible', 'Moyenne', 'Forte']:
        errors.append(f"Préférence d'autonomie invalide: {autonomy_preference}")
    
    return errors

def validate_injury_prevention(injury_data: Dict[str, Any]) -> list:
    """Valide les données de prévention des blessures"""
    errors = []
    
    medical_clearance = injury_data.get('medical_clearance')
    if medical_clearance is False:
        errors.append("Avis médical requis pour l'entraînement")
    
    return errors
