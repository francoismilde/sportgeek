from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime
from enum import Enum
import json
import re
import logging

logger = logging.getLogger(__name__)

# --- ENUMS & TYPES ---

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

# --- PERFORMANCE METRICS SUB-SCHEMAS ---

class CyclingMetrics(BaseModel):
    cycling_max_power_15s: Optional[int] = Field(None, description="Puissance Max 15s (Watts)")
    cycling_max_power_3min: Optional[int] = Field(None, description="Puissance Max 3min (Watts)")
    cycling_max_power_20min: Optional[int] = Field(None, description="Puissance Max 20min (Watts)")
    cycling_ftp: Optional[int] = Field(None, description="Functional Threshold Power (Watts)")

class RunningMetrics(BaseModel):
    running_time_5k: Optional[Union[int, str]] = Field(None, description="Temps 5k (Secondes)")
    running_time_10k: Optional[Union[int, str]] = Field(None, description="Temps 10k (Secondes)")
    running_time_21k: Optional[Union[int, str]] = Field(None, description="Temps Semi (Secondes)")
    running_max_sprint_time: Optional[Union[int, str]] = Field(None, description="Sprint Max (Secondes)")

    @field_validator('running_time_5k', 'running_time_10k', 'running_time_21k', 'running_max_sprint_time', mode='before')
    def transform_time_to_seconds(cls, v):
        if v is None: return None
        if isinstance(v, int): return v
        if isinstance(v, float): return int(v)
        if isinstance(v, str):
            v = v.strip()
            if not v: return None
            parts = v.split(':')
            try:
                if len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2]))
                elif len(parts) == 2:
                    return int(parts[0]) * 60 + int(float(parts[1]))
                elif v.isdigit():
                    return int(v)
            except ValueError:
                return v
        return v

class SwimmingMetrics(BaseModel):
    swimming_time_200m: Optional[Union[int, str]] = Field(None, description="Temps 200m (Secondes)")
    swimming_time_400m: Optional[Union[int, str]] = Field(None, description="Temps 400m (Secondes)")

    @field_validator('swimming_time_200m', 'swimming_time_400m', mode='before')
    def transform_swim_time(cls, v):
        if v is None: return None
        if isinstance(v, int): return v
        if isinstance(v, float): return int(v)
        if isinstance(v, str):
            v = v.strip()
            if not v: return None
            parts = v.split(':')
            try:
                if len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2]))
                elif len(parts) == 2:
                    return int(parts[0]) * 60 + int(float(parts[1]))
                elif v.isdigit():
                    return int(v)
            except ValueError:
                return v
        return v

class PerformanceBaselineSchema(CyclingMetrics, RunningMetrics, SwimmingMetrics):
    # Champs supplémentaires pour accepter les données brutes du mobile
    run_vma_est: Optional[str] = None
    cycling_ftp_est: Optional[str] = None
    swim_css_est: Optional[str] = None
    run_short_dist: Optional[float] = None
    run_short_min: Optional[float] = None
    run_short_sec: Optional[float] = None
    run_long_dist: Optional[float] = None
    run_long_min: Optional[float] = None
    run_long_sec: Optional[float] = None
    bike_short_min: Optional[float] = None
    bike_short_sec: Optional[float] = None
    bike_short_watts: Optional[float] = None
    bike_long_min: Optional[float] = None
    bike_long_sec: Optional[float] = None
    bike_long_watts: Optional[float] = None
    swim_200_min: Optional[float] = None
    swim_200_sec: Optional[float] = None
    swim_400_min: Optional[float] = None
    swim_400_sec: Optional[float] = None
    run_vma: Optional[float] = None
    bike_peak_5s: Optional[float] = None
    run_sprint_max: Optional[float] = None
    squat_1rm: Optional[float] = None
    bench_1rm: Optional[float] = None
    deadlift_1rm: Optional[float] = None
    pull_load: Optional[float] = None
    
    model_config = ConfigDict(extra='allow')

    @field_validator('*', mode='before')
    def clean_none_values(cls, v, info):
        """Nettoie les valeurs None et chaînes vides."""
        if info.field_name not in ['run_vma_est', 'cycling_ftp_est', 'swim_css_est']:
            if v in [None, "", "null", "undefined"]:
                return None
        return v

# --- SUB-SCHEMAS FOR PROFILE ---

class BasicInfo(BaseModel):
    pseudo: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[str] = None
    training_age: Optional[int] = 0
    biological_sex: Optional[str] = "MALE"

class PhysicalMetrics(BaseModel):
    height: float = 0
    weight: float = 0
    body_fat: Optional[float] = None
    resting_hr: Optional[int] = None
    sleep_quality_avg: Optional[int] = 5

class SportContext(BaseModel):
    sport: SportType = SportType.OTHER
    position: Optional[str] = None
    level: Optional[str] = "INTERMEDIATE"
    equipment: List[EquipmentType] = [EquipmentType.BODYWEIGHT_ZERO]

    @field_validator('equipment', mode='before')
    def migrate_legacy_equipment(cls, v):
        """Transforme les anciennes valeurs 'Standard' en 'COMMERCIAL_GYM'."""
        if not v:
            return [EquipmentType.BODYWEIGHT_ZERO]
        
        cleaned_list = []
        if isinstance(v, list):
            for item in v:
                if item == "Standard":
                    cleaned_list.append(EquipmentType.COMMERCIAL_GYM)
                else:
                    cleaned_list.append(item)
        return cleaned_list

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
    
    performance_baseline: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('performance_baseline', mode='before')
    def parse_performance(cls, v):
        """Nettoie et valide les données de performance."""
        if v is None:
            return {}
        
        try:
            # Si c'est déjà un dict, le nettoyer
            if isinstance(v, dict):
                # Supprimer les valeurs None et chaînes vides (sauf les résultats formatés)
                cleaned = {}
                for key, value in v.items():
                    if value in [None, "", "null", "undefined"]:
                        continue
                    # Pour les résultats formatés, garder même les chaînes vides
                    if key in ['run_vma_est', 'cycling_ftp_est', 'swim_css_est'] and value == "":
                        continue
                    cleaned[key] = value
                return cleaned
            return {}
        except Exception as e:
            logger.error(f"Erreur validation performance_baseline: {e}")
            return {}

class AthleteProfileCreate(AthleteProfileBase):
    pass

class AthleteProfileResponse(AthleteProfileBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# --- MEMORY SCHEMAS ---

class CoachMemoryResponse(BaseModel):
    id: int
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

# --- WORKOUT SCHEMAS ---

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
    ai_analysis: Optional[str] = None
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

# --- AI & GENERATION ---

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
    profile_data: Optional[Dict[str, Any]] = None 
    
    @field_validator('profile_data', mode='before')
    def parse_profile_data(cls, v):
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            if not v.strip():
                return {}
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

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

# --- PERFORMANCE & MISC ---

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

class ProfileUpdate(BaseModel):
    profile_data: Dict[str, Any]
    
class ProfileSectionUpdate(BaseModel):
    section_data: Dict[str, Any]

class DailyMetrics(BaseModel):
    date: str
    weight: Optional[float] = None
    sleep_quality: Optional[int] = None
    resting_heart_rate: Optional[int] = None
    hrv: Optional[int] = None
    energy_level: Optional[int] = None
    muscle_soreness: Optional[int] = None
    perceived_stress: Optional[int] = None
    sleep_duration: Optional[float] = None

class GoalProgressUpdate(BaseModel):
    progress_value: int
    progress_note: Optional[str] = None
    achieved: bool = False

class AthleteProfileUpdate(AthleteProfileBase):
    pass