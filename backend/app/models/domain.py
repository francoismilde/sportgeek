from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional, Dict, Any
from app.models.enums import CoachingMandate, SlotStatus, LocationContext, EnergyLevel

# --- SOUS-STRUCTURES ---

class ExternalLoad(BaseModel):
    """
    Charge externe imposée (ex: Entraînement Club, Match).
    """
    type: str = Field(..., description="Type d'activité (ex: Rugby, Match, Crossfit Class)")
    estimated_rpe: int = Field(..., ge=1, le=10, description="Intensité perçue (1-10)")
    duration_min: int = Field(..., gt=0, description="Durée en minutes")

    @field_validator('estimated_rpe')
    def validate_rpe(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("Le RPE doit être compris entre 1 et 10")
        return v

class TimeSlot(BaseModel):
    """
    Représente un créneau unique dans la matrice hebdomadaire.
    """
    day_of_week: str = Field(..., pattern="^(Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche)$")
    time_of_day: str = Field(..., pattern="^(Matin|Midi|Soir)$")
    status: SlotStatus = Field(default=SlotStatus.AVAILABLE)
    location: Optional[LocationContext] = None
    energy_level: EnergyLevel = Field(default=EnergyLevel.MEDIUM)
    
    # Charge externe (optionnel, seulement si SlotStatus.EXTERNAL_LOCKED)
    external_load: Optional[ExternalLoad] = None
    
    # [NOUVEAU] Tags pour le moteur de contraintes (ex: "RESTRICTED_LEG_VOLUME", "NO_DEADLIFT")
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def validate_slot_coherence(self):
        """Vérifie la cohérence entre le statut et la charge."""
        if self.status == SlotStatus.EXTERNAL_LOCKED and not self.external_load:
            raise ValueError("Un créneau EXTERNAL_LOCKED doit avoir une 'external_load' définie.")
        return self

# --- PROFIL ATHLÉTIQUE V2 (DOMAINE) ---

class AthleteProfileDomain(BaseModel):
    """
    Représentation 'Domaine' du profil athlète.
    C'est la version stricte utilisée par le moteur IA, indépendante de la BDD.
    """
    # Identité Sportive
    primary_sport: str
    mandate: CoachingMandate = Field(default=CoachingMandate.SUPPORT_HYBRID)
    
    # Matrice Temporelle (Disponibilités)
    time_matrix: List[TimeSlot] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def validate_sport_locations(self):
        """
        Règle Métier : Interdire LocationContext.POOL si le sport principal 
        n'est pas lié à la natation (Triathlon, Natation, etc.).
        """
        water_sports = ["Natation", "Triathlon", "Swimrun", "Water-polo"]
        is_water_sport = self.primary_sport in water_sports

        for slot in self.time_matrix:
            if slot.location in [LocationContext.POOL_25M, LocationContext.POOL_50M]:
                if not is_water_sport:
                    raise ValueError(
                        f"Impossible d'assigner une piscine ({slot.location}) "
                        f"pour le sport '{self.primary_sport}'. Réservé aux sports aquatiques."
                    )
        return self