from enum import Enum, IntEnum

class CoachingMandate(str, Enum):
    """
    Niveau d'intervention du Coach IA.
    - FULL_AUTO_PILOT : L'IA gère tout (Volume, Intensité, Sélection d'exos).
    - PPG_ONLY : L'IA ne gère que la préparation physique (pas le sport spé).
    - SUPPORT_HYBRID : L'IA propose, l'athlète dispose (mode assistant).
    """
    FULL_AUTO_PILOT = "FULL_AUTO_PILOT"
    PPG_ONLY = "PPG_ONLY"
    SUPPORT_HYBRID = "SUPPORT_HYBRID"

class SlotStatus(str, Enum):
    """
    État d'un créneau horaire dans la matrice temporelle.
    """
    AVAILABLE = "AVAILABLE"           # Créneau libre pour l'entraînement
    UNAVAILABLE = "UNAVAILABLE"       # Pris (Travail, Famille, etc.)
    EXTERNAL_LOCKED = "EXTERNAL_LOCKED" # Pris par une contrainte sportive externe (Match, Club)

class LocationContext(str, Enum):
    """
    Lieu d'entraînement disponible pour un créneau donné.
    """
    HOME = "HOME"                     # Maison (poids du corps, élastiques)
    HOME_GYM_PRO = "HOME_GYM_PRO"     # Garage gym équipé
    COMMERCIAL_GYM = "COMMERCIAL_GYM" # Salle de sport classique
    OUTDOOR_TRACK = "OUTDOOR_TRACK"   # Piste d'athlé / Extérieur
    POOL_25M = "POOL_25M"             # Piscine petit bain
    POOL_50M = "POOL_50M"             # Piscine olympique

class EnergyLevel(IntEnum):
    """
    Niveau d'énergie allouable sur un créneau (Score).
    Utilisé pour le calcul de la charge (Load Management).
    """
    HIGH_FOCUS = 3    # Performance maximale
    MEDIUM = 2        # Entraînement standard / Développement
    LOW_RECOVERY = 1  # Récupération active / Technique légère

# --- MEMORY ENUMS ---

class MemoryType(str, Enum):
    """Type de souvenir structurel."""
    INJURY_REPORT = "INJURY_REPORT"         # Blessure signalée
    LIFE_CONSTRAINT = "LIFE_CONSTRAINT"     # Contrainte vie (voyage, examen...)
    STRATEGIC_OVERRIDE = "STRATEGIC_OVERRIDE" # Changement de cap manuel
    BIOFEEDBACK_LOG = "BIOFEEDBACK_LOG"     # Retour sensation spécifique

class ImpactLevel(str, Enum):
    """Impact du souvenir sur la génération du plan."""
    INFO = "INFO"           # À titre informatif
    MODERATE = "MODERATE"   # Nécessite un ajustement mineur
    SEVERE = "SEVERE"       # Bloque ou modifie drastiquement le plan

class MemoryStatus(str, Enum):
    """Cycle de vie du souvenir."""
    ACTIVE = "ACTIVE"       # En cours, pris en compte
    SCHEDULED = "SCHEDULED" # Futur (ex: vacances prévues)
    RESOLVED = "RESOLVED"   # Terminé, mais gardé en historique
    ARCHIVED = "ARCHIVED"   # Supprimé logiquement

# --- NEW ENUMS (MIGRATED FROM SCHEMAS) ---

class SportType(str, Enum):
    RUGBY = "Rugby"
    FOOTBALL = "Football"
    CROSSFIT = "CrossFit"
    HYBRID = "Hybrid"
    RUNNING = "Running"
    OTHER = "Autre"
    BODYBUILDING = "BODYBUILDING"
    CYCLING = "CYCLING"
    TRIATHLON = "TRIATHLON"
    POWERLIFTING = "POWERLIFTING"
    SWIMMING = "SWIMMING"
    COMBAT_SPORTS = "COMBAT_SPORTS"

class EquipmentType(str, Enum):
    PERFORMANCE_LAB = "PERFORMANCE_LAB"
    COMMERCIAL_GYM = "COMMERCIAL_GYM"
    HOME_GYM_BARBELL = "HOME_GYM_BARBELL"
    HOME_GYM_DUMBBELL = "HOME_GYM_DUMBBELL"
    CALISTHENICS_KIT = "CALISTHENICS_KIT"
    BODYWEIGHT_ZERO = "BODYWEIGHT_ZERO"
    ENDURANCE_SUITE = "ENDURANCE_SUITE"
    STANDARD = "Standard"
    HOME_GYM_FULL = "HOME_GYM_FULL"
    CROSSFIT_BOX = "CROSSFIT_BOX"
    DUMBBELLS = "DUMBBELLS"
    BARBELL = "BARBELL"
    KETTLEBELLS = "KETTLEBELLS"
    PULL_UP_BAR = "PULL_UP_BAR"
    BENCH = "BENCH"
    DIP_STATION = "DIP_STATION"
    BANDS = "BANDS"
    RINGS_TRX = "RINGS_TRX"
    JUMP_ROPE = "JUMP_ROPE"
    WEIGHT_VEST = "WEIGHT_VEST"
    BIKE = "BIKE"
    HOME_TRAINER = "HOME_TRAINER"
    ROWER = "ROWER"
    TREADMILL = "TREADMILL"
    POOL = "POOL"

class FeedItemType(str, Enum):
    INFO = "INFO"
    ANALYSIS = "ANALYSIS"
    ACTION = "ACTION"
    ALERT = "ALERT"