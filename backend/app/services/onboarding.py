import math
from typing import Dict, Any, Optional, List, Generic, TypeVar, Union
from pydantic import BaseModel
from dataclasses import dataclass

# --- TYPES GÉNÉRIQUES POUR LE PATTERN RESULT ---

T = TypeVar('T')

@dataclass
class ValidationError:
    field: str
    message: str
    value: Any

@dataclass
class ServiceResult(Generic[T]):
    success: bool
    data: Optional[T] = None
    errors: List[ValidationError] = None

    @staticmethod
    def ok(data: T) -> 'ServiceResult[T]':
        return ServiceResult(success=True, data=data)

    @staticmethod
    def fail(errors: List[ValidationError]) -> 'ServiceResult[T]':
        return ServiceResult(success=False, errors=errors)

# --- SERVICE D'ONBOARDING ---

class AthleteOnboardingService:
    """
    Service responsable de l'ingestion, de la validation et de l'enrichissement
    du profil athlète avant persistance.
    Agit comme un 'Expert Filter'.
    """

    @staticmethod
    def process_profile(raw_profile_data: Dict[str, Any]) -> ServiceResult[Dict[str, Any]]:
        """
        Traite les données brutes du profil.
        1. Valide les garde-fous (Sanity Checks).
        2. Gère les Null-States (Flags).
        3. Calcule les métriques dérivées (CSS, Relative Strength).
        """
        errors = []
        enriched_data = raw_profile_data.copy()
        
        # Initialisation des sous-structures si absentes
        if 'performance_baseline' not in enriched_data:
            enriched_data['performance_baseline'] = {}
        if 'physical_metrics' not in enriched_data:
            enriched_data['physical_metrics'] = {}
        if 'memory_flags' not in enriched_data:
            enriched_data['memory_flags'] = {}

        perf = enriched_data['performance_baseline']
        phys = enriched_data['physical_metrics']
        flags = enriched_data['memory_flags']

        # --- 1. NULL-STATE LOGIC (Les drapeaux) ---
        
        # Check Force
        squat_1rm = perf.get('squat_1rm')
        if not squat_1rm:
            flags['NEEDS_TESTING_FORCE'] = True
            flags['force_status'] = "Unknown"
        else:
            flags['NEEDS_TESTING_FORCE'] = False
            flags['force_status'] = "Tested"

        # Check Aérobie (VMA)
        vma = perf.get('vma')
        if not vma:
            flags['NEEDS_TESTING_AEROBIC'] = True
            flags['aerobic_status'] = "Unknown"
        else:
            flags['NEEDS_TESTING_AEROBIC'] = False
            flags['aerobic_status'] = "Tested"

        # --- 2. SANITY CHECKS (Les Garde-fous) ---

        # VMA Humaine Max (~26km/h pour Kipchoge sur marathon, on est large mais safe)
        if vma and (isinstance(vma, (int, float))):
            if vma > 26.0:
                errors.append(ValidationError(
                    field="vma", 
                    message="VMA suspecte (> 26 km/h). Êtes-vous sûr ?", 
                    value=vma
                ))
            if vma < 3.0: # Marcher c'est 4-5km/h
                 errors.append(ValidationError(
                    field="vma", 
                    message="VMA trop faible (< 3 km/h).", 
                    value=vma
                ))

        # Poids de corps
        weight = phys.get('weight')
        if weight and (weight < 30 or weight > 250):
             errors.append(ValidationError(
                field="weight", 
                message="Poids hors normes physiologiques (30-250kg).", 
                value=weight
            ))

        # --- 3. COMPUTED FIELDS (Calculs Automatiques) ---

        # Relative Strength (Force Relative)
        if squat_1rm and weight and weight > 0:
            try:
                ratio = round(float(squat_1rm) / float(weight), 2)
                perf['relative_strength_squat'] = ratio
            except (ValueError, TypeError):
                pass # On ignore silencieusement si les types sont foireux (cleanés par Pydantic ailleurs normalement)

        # Critical Swim Speed (CSS)
        # Formule : CSS = (400 - 200) / (T400 - T200)
        # T en secondes.
        t400 = perf.get('swim_400m_time_sec')
        t200 = perf.get('swim_200m_time_sec')

        if t400 and t200:
            try:
                t400_f = float(t400)
                t200_f = float(t200)
                
                delta_dist = 200.0 # 400m - 200m
                delta_time = t400_f - t200_f

                if delta_time <= 0:
                    errors.append(ValidationError(
                        field="swim_times", 
                        message="Le temps au 400m doit être supérieur au temps au 200m.", 
                        value=f"400:{t400}, 200:{t200}"
                    ))
                else:
                    css = round(delta_dist / delta_time, 2) # m/s

                    # Sanity Check CSS
                    if css < 0.5 or css > 2.5:
                        errors.append(ValidationError(
                            field="calculated_css", 
                            message=f"CSS calculé ({css} m/s) hors limites (0.5 - 2.5 m/s). Vérifiez les temps.", 
                            value=css
                        ))
                    else:
                        perf['critical_swim_speed'] = css
                        
            except (ValueError, TypeError):
                # Si les inputs ne sont pas des nombres propres
                errors.append(ValidationError(
                    field="swim_times", 
                    message="Format des temps de natation invalide.", 
                    value=f"400:{t400}, 200:{t200}"
                ))

        # Si erreurs bloquantes, on rejette tout
        if errors:
            return ServiceResult.fail(errors)

        # Mise à jour des données enrichies
        enriched_data['performance_baseline'] = perf
        enriched_data['memory_flags'] = flags
        
        return ServiceResult.ok(enriched_data)