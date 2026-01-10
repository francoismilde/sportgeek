import os
import sys

# --- 1. CORRECT CONTENT FOR SCHEMAS.PY ---
# This version fixes the AttributeError by removing .get() from the Field definition
CORRECT_SCHEMAS_CONTENT = """from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime
from enum import Enum
import json

# --- ENUMS & TYPES ---

class SportType(str, Enum):
    RUGBY = "Rugby"
    FOOTBALL = "Football"
    CROSSFIT = "CrossFit"
    HYBRID = "Hybrid"
    RUNNING = "Running"
    OTHER = "Autre"

# --- SUB-SCHEMAS FOR PROFILE ---

class BasicInfo(BaseModel):
    pseudo: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[str] = None
    training_age: Optional[int] = 0

class PhysicalMetrics(BaseModel):
    height: float = 0
    weight: float = 0
    body_fat: Optional[float] = None
    resting_hr: Optional[int] = None
    sleep_quality_avg: Optional[int] = 5

class SportContext(BaseModel):
    sport: SportType = SportType.OTHER
    position: Optional[str] = None
    level: str = "Intermédiaire"
    equipment: List[str] = ["Standard"]

class TrainingPreferences(BaseModel):
    days_available: List[str] = []
    duration_min: int = 60
    preferred_split: str = "Upper/Lower"

# --- MAIN PROFILE SCHEMAS ---

class AthleteProfileBase(BaseModel):
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    physical_metrics: PhysicalMetrics = Field(default_factory=PhysicalMetrics)
    sport_context: SportContext = Field(default_factory=SportContext)
    training_preferences: TrainingPreferences = Field(default_factory=TrainingPreferences)
    goals: Dict[str, Any] = {}
    constraints: Dict[str, Any] = {}
    injury_prevention: Dict[str, Any] = {}
    performance_baseline: Dict[str, Any] = {}

class AthleteProfileCreate(AthleteProfileBase):
    pass

class AthleteProfileResponse(AthleteProfileBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- MEMORY SCHEMAS (FIXED) ---

class CoachMemoryResponse(BaseModel):
    id: int
    # [FIX] Removed invalid .get() call here
    readiness_score: int = Field(alias="current_context", default=50)
    current_phase: str = "Général"
    flags: Dict[str, bool] = {}
    insights: Dict[str, Any] = {}
    
    @field_validator('readiness_score', mode='before')
    def extract_readiness(cls, v):
        if isinstance(v, dict):
            return v.get('readiness_score', 50)
        return v

    class Config:
        from_attributes = True

# --- LEGACY SCHEMAS (KEPT FOR COMPATIBILITY) ---

class WorkoutSetBase(BaseModel):
    exercise_name: str
    set_order: int
    weight: Union[float, str] = 0.0
    reps: Union[float, str] = 0.0
    rpe: Optional[float] = 0.0
    rest_seconds: int = 0
    metric_type: str = "LOAD_REPS"

    @field_validator('weight', 'reps', mode='before')
    def parse_polymorphic_fields(cls, v):
        if isinstance(v, str):
            v = v.strip().replace(',', '.')
            if ':' in v:
                parts = v.split(':')
                try:
                    seconds = 0.0
                    if len(parts) == 2:
                        seconds = float(parts[0]) * 60 + float(parts[1])
                    elif len(parts) == 3:
                        seconds = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    return seconds
                except ValueError:
                    return 0.0
            try:
                return float(v)
            except ValueError:
                return 0.0
        return v

class WorkoutSetCreate(WorkoutSetBase):
    pass

class WorkoutSessionCreate(BaseModel):
    date: date
    duration: float
    rpe: float
    energy_level: int = 5
    notes: Optional[str] = None
    sets: List[WorkoutSetCreate] = []

class WorkoutSetResponse(WorkoutSetBase):
    id: int
    weight: float
    reps: float
    class Config:
        from_attributes = True

class WorkoutSessionResponse(WorkoutSessionCreate):
    id: int
    ai_analysis: Optional[str] = None
    sets: List[WorkoutSetResponse] = []
    class Config:
        from_attributes = True

class GenerateWorkoutRequest(BaseModel):
    profile_data: Dict[str, Any]
    context: Dict[str, Any]

class AIExercise(BaseModel):
    name: str
    sets: int
    reps: Union[str, int]
    rest: int
    tips: str
    recording_mode: str = "LOAD_REPS"
    @field_validator('reps')
    def force_string_reps(cls, v):
        return str(v)

class AIWorkoutPlan(BaseModel):
    title: str
    coach_comment: str
    warmup: List[str]
    exercises: List[AIExercise]
    cooldown: List[str]

# --- USER & AUTH ---
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

# --- FEED ---
class FeedItemType(str, Enum):
    INFO = "INFO"
    ANALYSIS = "ANALYSIS"
    ACTION = "ACTION"
    ALERT = "ALERT"

class FeedItemCreate(BaseModel):
    type: FeedItemType
    title: str
    message: str
    priority: int = 1
    action_payload: Optional[Dict[str, Any]] = None

class FeedItemResponse(FeedItemCreate):
    id: str
    is_read: bool
    is_completed: bool
    created_at: datetime
    
    @field_validator('action_payload', mode='before')
    def parse_payload(cls, v):
        if isinstance(v, str) and v.strip():
            try: return json.loads(v)
            except: return None
        return v
    class Config:
        from_attributes = True

# --- PERFORMANCE ---
class OneRepMaxRequest(BaseModel):
    weight: float
    reps: int
class OneRepMaxResponse(BaseModel):
    estimated_1rm: float
    method_used: str
class ACWRRequest(BaseModel):
    history: List[Dict[str, Any]]
class ACWRResponse(BaseModel):
    ratio: float
    status: str
    color: str
    message: str
class ProfileAuditRequest(BaseModel):
    profile_data: Dict[str, Any]
class ProfileAuditResponse(BaseModel):
    markdown_report: str
class StrategyResponse(BaseModel):
    periodization_title: str
    phases: List[Any]
class WeeklyPlanResponse(BaseModel):
    schedule: List[Any]
    reasoning: str
class UserProfileUpdate(BaseModel):
    profile_data: Dict[str, Any]
"""

# --- 2. FIND AND OVERWRITE ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# List of potential paths to schemas.py
potential_paths = [
    "backend/app/models/schemas.py",
    "app/models/schemas.py",
    "models/schemas.py"
]

target_file = None
for p in potential_paths:
    full_path = os.path.join(BASE_DIR, p)
    if os.path.exists(full_path):
        target_file = full_path
        break

if target_file:
    print(f"🎯 Target found: {target_file}")
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(CORRECT_SCHEMAS_CONTENT)
        print("✅ SUCCESS: schemas.py has been completely overwritten with the fix.")
        print("🚀 Please restart your server now.")
    except Exception as e:
        print(f"❌ Failed to write file: {e}")
else:
    print("❌ ERROR: Could not find schemas.py in any expected location.")
    print(f"Current Directory: {BASE_DIR}")
    print("Files in current dir:", os.listdir(BASE_DIR))