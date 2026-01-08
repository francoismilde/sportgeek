import math
from typing import Dict, Any, List

class BioenergeticService:
    """
    Service de calcul physiologique (Bio-Twin v1).
    Estime la dépense énergétique et les besoins nutritionnels post-effort.
    Ne dépend PAS de l'IA, mais de formules métaboliques.
    """

    @staticmethod
    def calculate_needs(profile_data: Dict[str, Any], workout_sets: List[Any], duration_min: float, rpe: float) -> Dict[str, Any]:
        """
        Calcule les KPIs physiologiques de la séance.
        """
        # 1. Extraction du profil (valeurs par défaut de sécurité)
        weight = float(profile_data.get('weight', 70.0))
        if weight <= 0: weight = 70.0
        
        gender = profile_data.get('gender', 'Homme')
        
        # 2. Estimation de la Dépense Énergétique (Kcal)
        # Méthode A : Précise si Watts disponibles
        total_work_kj = 0.0
        has_power_data = False
        
        for s in workout_sets:
            if s.metric_type == 'POWER_TIME':
                # Watts * secondes / 1000 = kJ
                # weight = watts, reps = duration(s) dans ce mode (selon schemas.py)
                # Mais attention, le frontend envoie parfois des minutes converties.
                # Dans sql_models/schemas, on a standardisé : weight=Watts, reps=Secondes (via validateur polymorphique)
                watts = s.weight
                seconds = s.reps 
                total_work_kj += (watts * seconds) / 1000.0
                has_power_data = True
        
        kcal_burn = 0.0
        
        if has_power_data:
            # Rendement mécanique humain ~20-25% => x4 à x5 pour passer de kJ mécanique à kcal métabolique
            # Formule standard: kJ * 1.1 est une approx basse, kJ / 4.18 * 4 (rendement) est mieux.
            # Simplification robuste : kJ mécanique * 1.0 = Kcal métabolique (approx très courante en cyclisme)
            kcal_burn = total_work_kj * 1.0 
            # Si on ajoute le métabolisme de base pendant la durée... Restons sur l'activité pure.
        else:
            # Méthode B : Estimation METs (Metabolic Equivalent of Task)
            # RPE 1-3 (Repos/Recup) : 3 METs
            # RPE 4-6 (Endurance) : 6 METs
            # RPE 7-8 (Seuil) : 9 METs
            # RPE 9-10 (Max) : 12 METs
            mets = 3.0
            if rpe > 8: mets = 11.0
            elif rpe > 6: mets = 9.0
            elif rpe > 4: mets = 6.0
            else: mets = 3.5
            
            # Formule : Kcal = METs * Poids(kg) * Durée(h)
            duration_hours = duration_min / 60.0
            kcal_burn = mets * weight * duration_hours

        # 3. Partition Macro-nutritionnelle (Filières énergétiques)
        # Ratio Glucides/Lipides dépend de l'intensité relative
        # RPE élevé -> Glycolytique -> Besoin Glucides
        carbs_ratio = 0.5 # 50% par défaut
        
        if rpe >= 8: carbs_ratio = 0.8  # 80% glucides
        elif rpe >= 6: carbs_ratio = 0.6 # 60% glucides
        elif rpe <= 4: carbs_ratio = 0.3 # 30% glucides (LIPOX max)
        
        kcal_carbs = kcal_burn * carbs_ratio
        carbs_g = kcal_carbs / 4.0 # 4 kcal/g
        
        # 4. Protéines (Réparation tissulaire)
        # Base : 0.3g / kg de poids de corps après une séance standard
        # Boost si séance de force (RPE > 7)
        protein_factor = 0.25
        if rpe > 7: protein_factor = 0.35
        
        protein_g = weight * protein_factor
        
        # 5. Hydratation (Estimation sudation standard)
        # ~10ml / min / kg est trop. 
        # Standard : 0.5L à 1L par heure selon intensité.
        sweat_rate_ml_h = 500
        if rpe > 7: sweat_rate_ml_h = 800
        water_ml = (duration_min / 60.0) * sweat_rate_ml_h

        return {
            "kcal_total": int(kcal_burn),
            "carbs_g": int(carbs_g),
            "protein_g": int(protein_g),
            "water_ml": int(water_ml),
            "source": "Wattmeter" if has_power_data else "METs Estimator"
        }