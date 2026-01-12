from typing import List, Dict, Optional
from dataclasses import dataclass
from app.models.domain import AthleteProfileDomain, TimeSlot
from app.models.enums import SlotStatus, LocationContext, CoachingMandate

@dataclass
class ConstraintWarning:
    """
    Avertissement généré par le validateur pour l'interface utilisateur.
    """
    code: str
    message: str
    affected_days: List[str]

class ScheduleValidatorService:
    """
    Moteur de règles physiologiques et logistiques.
    Vérifie la cohérence du planning AVANT la génération du programme.
    """

    # Mapping temporel pour identifier les contiguïtés
    TIME_ORDER = {"Matin": 0, "Midi": 1, "Soir": 2}
    DAYS_ORDER = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    @staticmethod
    def validate_and_tag(profile: AthleteProfileDomain) -> List[ConstraintWarning]:
        """
        Applique les règles strictes (Hard Rules).
        Modifie le profil IN-PLACE (ajout de tags) et retourne des warnings.
        """
        warnings: List[ConstraintWarning] = []
        
        # On trie la matrice pour faciliter l'analyse séquentielle
        # (Même si elle devrait l'être, on s'assure de l'ordre Lundi Matin -> Dimanche Soir)
        sorted_slots = sorted(
            profile.time_matrix,
            key=lambda s: (
                ScheduleValidatorService.DAYS_ORDER.index(s.day_of_week),
                ScheduleValidatorService.TIME_ORDER[s.time_of_day]
            )
        )

        # --- RÈGLE 1 : CONFLIT mTOR/AMPK AIGU ---
        # Si slot EXTERNE INTENSE (PPS, RPE >= 7), le slot PRÉCÉDENT (<6h) est bridé.
        
        for i, slot in enumerate(sorted_slots):
            if slot.status == SlotStatus.EXTERNAL_LOCKED and slot.external_load:
                # Vérification des conditions déclenchantes
                is_pps = "PPS" in slot.external_load.type.upper() or "MATCH" in slot.external_load.type.upper()
                is_high_intensity = slot.external_load.estimated_rpe >= 7
                
                if (is_pps or is_high_intensity):
                    # Identifier le slot précédent
                    # Condition < 6h : On regarde uniquement le créneau d'avant LE MÊME JOUR.
                    # (Soir J-1 -> Matin J est > 6h de sommeil en général, donc hors scope conflit aigu immédiat)
                    if i > 0:
                        prev_slot = sorted_slots[i-1]
                        same_day = prev_slot.day_of_week == slot.day_of_week
                        
                        # Si c'est le même jour et que le slot précédent est contigu
                        # Matin -> Midi OU Midi -> Soir
                        time_diff = ScheduleValidatorService.TIME_ORDER[slot.time_of_day] - ScheduleValidatorService.TIME_ORDER[prev_slot.time_of_day]
                        
                        if same_day and time_diff == 1:
                            # APPLICATION DE LA SANCTION PHYSIOLOGIQUE
                            if "RESTRICTED_LEG_VOLUME" not in prev_slot.tags:
                                prev_slot.tags.append("RESTRICTED_LEG_VOLUME")
                                warnings.append(ConstraintWarning(
                                    code="INTERFERENCE_ALERT",
                                    message=f"Interférence détectée le {slot.day_of_week}. Le volume jambes sera réduit avant votre séance de {slot.external_load.type}.",
                                    affected_days=[slot.day_of_week]
                                ))

        # --- RÈGLE 2 : RÉCUPÉRATION SYSTÈME NERVEUX (CNS) ---
        # Si PPG_ONLY + Charge Externe > 10h/semaine -> Cap Force
        
        if profile.mandate == CoachingMandate.PPG_ONLY:
            total_external_minutes = sum(
                s.external_load.duration_min 
                for s in sorted_slots 
                if s.status == SlotStatus.EXTERNAL_LOCKED and s.external_load
            )
            
            if total_external_minutes > 600: # 10 heures
                warnings.append(ConstraintWarning(
                    code="CNS_PROTECTION",
                    message="Charge externe élevée (>10h). Programme de force plafonné à 2 séances/semaine pour préserver le système nerveux.",
                    affected_days=[]
                ))
                # On taggue tous les slots disponibles pour informer le générateur
                for s in sorted_slots:
                    if s.status == SlotStatus.AVAILABLE:
                        s.tags.append("FORCE_VOLUME_CAP_2_SESSIONS")

        # --- RÈGLE 3 : LOGISTIQUE (MATÉRIEL) ---
        # Si Location == HOME -> Pas de Deadlift (Lourd)
        
        home_days = []
        for slot in sorted_slots:
            if slot.location == LocationContext.HOME:
                if "NO_DEADLIFT" not in slot.tags:
                    slot.tags.append("NO_DEADLIFT")
                    # On évite les doublons de jours pour le warning
                    if slot.day_of_week not in home_days:
                        home_days.append(slot.day_of_week)
        
        if home_days:
            warnings.append(ConstraintWarning(
                code="LOGISTICS_LIMIT",
                message="Séances à domicile détectées : Les exercices nécessitant une barre olympique (ex: Deadlift) seront adaptés.",
                affected_days=home_days
            ))

        return warnings