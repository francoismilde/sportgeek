from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

# --- 1RM Schemas ---
class OneRepMaxRequest(BaseModel):
    weight: float = Field(..., gt=0, description="Poids soulevé en kg")
    reps: int = Field(..., gt=0, lt=100, description="Nombre de répétitions réalisées")

class OneRepMaxResponse(BaseModel):
    estimated_1rm: float
    method_used: str
    input_weight: float
    input_reps: int

# --- ACWR Schemas ---
class WorkoutLogInput(BaseModel):
    date: date
    duration: float = Field(..., ge=0, description="Durée en minutes")
    rpe: float = Field(..., ge=0, le=10, description="Intensité ressentie (0-10)")

class ACWRRequest(BaseModel):
    history: List[WorkoutLogInput]

class ACWRResponse(BaseModel):
    ratio: float
    status: str
    color: str
    acute_load: int
    chronic_load: int
    message: str

# --- USER / AUTH Schemas ---
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, description="Pseudo unique")
    email: Optional[str] = None
    password: str = Field(..., min_length=6, description="Mot de passe fort")

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- TOKEN Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- COACH / AI Schemas ---
class ProfileAuditRequest(BaseModel):
    profile_data: Dict[str, Any]

class ProfileAuditResponse(BaseModel):
    markdown_report: str

# --- STRATEGY Schemas ---
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

# --- WEEKLY PLANNING Schemas ---
class WeeklySession(BaseModel):
    day: str = Field(..., alias="Jour")
    slot: str = Field(..., alias="Créneau")
    type: str = Field(..., alias="Type") 
    focus: str = Field(..., alias="Focus")
    # CORRECTION ICI : On autorise le None et on met 0 par défaut
    rpe_target: Optional[int] = Field(0, alias="RPE Cible")

class WeeklyPlanResponse(BaseModel):
    schedule: List[WeeklySession]
    reasoning: str