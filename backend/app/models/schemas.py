from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

# --- SHARED ---
class WorkoutSetBase(BaseModel):
    exercise_name: str
    set_order: int
    weight: float = 0.0
    reps: float = 0.0
    rpe: float = 0.0
    rest_seconds: int = 0
    metric_type: str = "LOAD_REPS"

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
    context: Dict[str, Any] # { "duration": 60, "energy": 7, "focus": "Legs" }

class AIExercise(BaseModel):
    name: str
    sets: int
    reps: str # String pour gérer "10-12" ou "AMRAP"
    rest: int
    tips: str
    recording_mode: str = "LOAD_REPS" # LOAD_REPS, PACE_DISTANCE, etc.

class AIWorkoutPlan(BaseModel):
    title: str
    coach_comment: str
    warmup: List[str]
    exercises: List[AIExercise]
    cooldown: List[str]

# --- EXISTING SCHEMAS (Keep them for compatibility if needed) ---
class OneRepMaxRequest(BaseModel):
    weight: float
    reps: int

class OneRepMaxResponse(BaseModel):
    estimated_1rm: float
    method_used: str
    input_weight: float
    input_reps: int

class ACWRRequest(BaseModel):
    history: List[Dict[str, Any]] # Simplifié pour éviter import circulaire

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