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