from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import date
import re

# --- SHARED ---
class WorkoutSetBase(BaseModel):
    exercise_name: str
    set_order: int
    
    # On accepte float ou str pour gérer les entrées type "5:30" (Pace)
    # Mais le modèle nettoiera ça en float pour la suite
    weight: Union[float, str] = 0.0
    reps: Union[float, str] = 0.0
    
    rpe: Optional[float] = 0.0
    rest_seconds: int = 0
    metric_type: str = "LOAD_REPS" # C'est notre recording_mode

    @field_validator('weight', 'reps', mode='before')
    def parse_polymorphic_fields(cls, v):
        """
        Convertit les formats humains (MM:SS) en secondes (float)
        et nettoie les chaînes en nombres.
        """
        if isinstance(v, str):
            v = v.strip().replace(',', '.')
            # Cas du format MM:SS ou HH:MM:SS
            if ':' in v:
                parts = v.split(':')
                try:
                    seconds = 0.0
                    if len(parts) == 2: # MM:SS
                        seconds = float(parts[0]) * 60 + float(parts[1])
                    elif len(parts) == 3: # HH:MM:SS
                        seconds = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    return seconds
                except ValueError:
                    return 0.0
            # Cas standard nombre string "10.5"
            try:
                return float(v)
            except ValueError:
                return 0.0
        return v

# --- INPUTS (Création) ---
class WorkoutSetCreate(WorkoutSetBase):
    pass

class WorkoutSessionCreate(BaseModel):
    date: date
    duration: float
    rpe: float
    energy_level: int = 5
    notes: Optional[str] = None
    sets: List[WorkoutSetCreate] = []

# --- OUTPUTS (Lecture) ---
class WorkoutSetResponse(WorkoutSetBase):
    id: int
    # On force le type float en sortie pour la cohérence JSON
    weight: float
    reps: float
    
    class Config:
        from_attributes = True

class WorkoutSessionResponse(WorkoutSessionCreate):
    id: int
    sets: List[WorkoutSetResponse] = []
    class Config:
        from_attributes = True

# --- AI GENERATION SCHEMAS ---
class GenerateWorkoutRequest(BaseModel):
    profile_data: Dict[str, Any]
    context: Dict[str, Any]

class AIExercise(BaseModel):
    name: str
    sets: int
    # [FIX] On accepte int ou str en entrée, mais on force la conversion en str
    reps: Union[str, int]
    rest: int
    tips: str
    recording_mode: str = "LOAD_REPS"

    # [NOUVEAU] Validateur pour convertir "8" (int) en "8" (str) automatiquement
    @field_validator('reps')
    def force_string_reps(cls, v):
        return str(v)

class AIWorkoutPlan(BaseModel):
    title: str
    coach_comment: str
    warmup: List[str]
    exercises: List[AIExercise]
    cooldown: List[str]

# --- OTHER SCHEMAS (Keep existing ones) ---
class OneRepMaxRequest(BaseModel):
    weight: float
    reps: int

class OneRepMaxResponse(BaseModel):
    estimated_1rm: float
    method_used: str
    input_weight: float
    input_reps: int

class ACWRRequest(BaseModel):
    history: List[Dict[str, Any]]

class ACWRResponse(BaseModel):
    ratio: float
    status: str
    color: str
    acute_load: int
    chronic_load: int
    message: str

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    profile_data: Optional[str] = None 
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ProfileAuditRequest(BaseModel):
    profile_data: Dict[str, Any]

class ProfileAuditResponse(BaseModel):
    markdown_report: str

class Phase(BaseModel):
    phase_name: str
    focus: str
    intensity_metric: str
    volume_strategy: str
    start: str
    end: str

class StrategyResponse(BaseModel):
    periodization_title: str
    periodization_logic: str
    progression_model: str
    recommended_frequency: int
    phases: List[Phase]

class WeeklySession(BaseModel):
    day: str = Field(..., alias="Jour")
    slot: str = Field(..., alias="Créneau")
    type: str = Field(..., alias="Type") 
    focus: str = Field(..., alias="Focus")
    rpe_target: Optional[int] = Field(0, alias="RPE Cible")

class WeeklyPlanResponse(BaseModel):
    schedule: List[WeeklySession]
    reasoning: str

class UserProfileUpdate(BaseModel):
    profile_data: Dict[str, Any]