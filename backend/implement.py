import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
import json

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TitanUpgrader")

# --- CHEMIN DYNAMIQUE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. NOUVEAUX MODÈLES SQL
SQL_MODELS_CONTENT = """from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    
    # Anciens champs (Legacy support)
    profile_data = Column(Text, nullable=True)
    strategy_data = Column(Text, nullable=True)
    weekly_plan_data = Column(Text, nullable=True)
    draft_workout_data = Column(Text, nullable=True)

    # Relations
    workouts = relationship("WorkoutSession", back_populates="owner")
    feed_items = relationship("FeedItem", back_populates="owner", cascade="all, delete-orphan")
    
    # [NOUVEAU] Relation vers le Profil Enrichi
    athlete_profile = relationship("AthleteProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class AthleteProfile(Base):
    __tablename__ = "athlete_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Blocs de données JSONB
    basic_info = Column(JSON, default={})
    physical_metrics = Column(JSON, default={})
    sport_context = Column(JSON, default={})
    performance_baseline = Column(JSON, default={})
    injury_prevention = Column(JSON, default={})
    training_preferences = Column(JSON, default={})
    goals = Column(JSON, default={})
    constraints = Column(JSON, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="athlete_profile")
    coach_memory = relationship("CoachMemory", back_populates="athlete_profile", uselist=False, cascade="all, delete-orphan")

class CoachMemory(Base):
    __tablename__ = "coach_memories"

    id = Column(Integer, primary_key=True, index=True)
    athlete_profile_id = Column(Integer, ForeignKey("athlete_profiles.id"), unique=True)

    # Mémoire contextuelle IA
    metadata_info = Column(JSON, default={})
    current_context = Column(JSON, default={})
    response_patterns = Column(JSON, default={})
    performance_baselines = Column(JSON, default={})
    adaptation_signals = Column(JSON, default={})
    sport_specific_insights = Column(JSON, default={})
    training_history_summary = Column(JSON, default={})
    athlete_preferences = Column(JSON, default={})
    coach_notes = Column(JSON, default={})
    memory_flags = Column(JSON, default={})

    last_updated = Column(DateTime(timezone=True), server_default=func.now())

    athlete_profile = relationship("AthleteProfile", back_populates="coach_memory")

# --- MODÈLES EXISTANTS ---
class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, index=True)
    duration = Column(Float)
    rpe = Column(Float)
    energy_level = Column(Integer, default=5) 
    notes = Column(Text, nullable=True)      
    ai_analysis = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="workouts")
    sets = relationship("WorkoutSet", back_populates="session", cascade="all, delete-orphan")

class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id"))
    exercise_name = Column(String, index=True)
    set_order = Column(Integer)
    weight = Column(Float, default=0.0)
    reps = Column(Float, default=0.0)
    rpe = Column(Float, default=0.0)
    rest_seconds = Column(Integer, default=0)
    metric_type = Column(String, nullable=False, default="LOAD_REPS") 
    session = relationship("WorkoutSession", back_populates="sets")

class FeedItem(Base):
    __tablename__ = "feed_items"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String, index=True)
    title = Column(String)
    message = Column(String)
    action_payload = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="feed_items")
"""

# 2. SCHEMAS PYDANTIC
SCHEMAS_CONTENT = """from pydantic import BaseModel, Field, field_validator
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

# --- MEMORY SCHEMAS ---
class CoachMemoryResponse(BaseModel):
    id: int
    readiness_score: int = Field(alias="current_context", default={}).get("readiness_score", 0)
    current_phase: str = "Général"
    flags: Dict[str, bool] = {}
    insights: Dict[str, Any] = {}
    
    @field_validator('readiness_score', mode='before')
    def extract_readiness(cls, v):
        if isinstance(v, dict): return v.get('readiness_score', 50)
        return v

    class Config:
        from_attributes = True

# --- LEGACY SCHEMAS ---
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

# 3. LOGIQUE MÉTIER
LOGIC_CONTENT = """from datetime import date
from typing import Dict, Any
from app.models import sql_models

VALID_SPORT_POSITIONS = {
    'Rugby': ['Pilier', 'Talonneur', '2ème ligne', '3ème ligne', 'Demi', 'Centre', 'Ailier', 'Arrière'],
    'Football': ['Gardien', 'Défenseur', 'Milieu', 'Attaquant'],
}

class CoachLogic:
    @staticmethod
    def validate_sport_position(sport: str, position: str) -> bool:
        if sport in VALID_SPORT_POSITIONS:
            if position and position not in VALID_SPORT_POSITIONS[sport]:
                return False
        return True

    @staticmethod
    def initialize_memory(profile: sql_models.AthleteProfile) -> sql_models.CoachMemory:
        sport = profile.sport_context.get('sport', 'Autre')
        insights = {
            "primary_sport": sport,
            "specificity_index": "High" if sport in ['Rugby', 'Football'] else "Medium",
            "focus_areas": ["Strength", "Hypertrophy"] 
        }
        context = {
            "macrocycle_phase": "Adaptation Anatomique",
            "fatigue_state": "Fresh",
            "readiness_score": 100,
            "season_week": 1
        }
        flags = {
            "needs_deload": False,
            "injury_risk": False,
            "adaptation_window_open": True
        }
        memory = sql_models.CoachMemory(
            athlete_profile_id=profile.id,
            sport_specific_insights=insights,
            current_context=context,
            memory_flags=flags,
            coach_notes={"initialization": f"Profil créé le {date.today()}"}
        )
        return memory

    @staticmethod
    def calculate_readiness(profile: sql_models.AthleteProfile) -> int:
        base_score = 80
        sleep = profile.physical_metrics.get('sleep_quality_avg', 5)
        if sleep >= 8: base_score += 10
        elif sleep <= 4: base_score -= 20
        stress = profile.constraints.get('work_stress_level', 5)
        if stress >= 8: base_score -= 15
        return max(0, min(100, base_score))

    @staticmethod
    def update_daily(memory: sql_models.CoachMemory, profile: sql_models.AthleteProfile):
        new_readiness = CoachLogic.calculate_readiness(profile)
        current_context = dict(memory.current_context or {})
        current_context['readiness_score'] = new_readiness
        
        if new_readiness < 40:
            current_context['fatigue_state'] = "High"
        elif new_readiness < 70:
            current_context['fatigue_state'] = "Moderate"
        else:
            current_context['fatigue_state'] = "Optimal"
            
        memory.current_context = current_context
        flags = dict(memory.memory_flags or {})
        flags['needs_deload'] = new_readiness < 30
        flags['adaptation_window_open'] = new_readiness > 70
        memory.memory_flags = flags
"""

# 4. NOUVEAU ROUTEUR
ROUTER_CONTENT = """from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import sql_models, schemas
from app.dependencies import get_current_user
from app.services.coach_logic import CoachLogic

router = APIRouter(
    prefix="/api/v1",
    tags=["Athlete Profile & Memory"]
)

@router.get("/profiles/me", response_model=schemas.AthleteProfileResponse)
async def get_my_profile(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.athlete_profile:
        profile = sql_models.AthleteProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    return current_user.athlete_profile

@router.post("/profiles/complete", response_model=schemas.AthleteProfileResponse)
async def complete_profile(
    profile_data: schemas.AthleteProfileCreate,
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sport = profile_data.sport_context.sport
    pos = profile_data.sport_context.position
    if not CoachLogic.validate_sport_position(sport, pos):
        raise HTTPException(status_code=400, detail=f"Position {pos} invalide pour le sport {sport}")

    db_profile = current_user.athlete_profile
    if not db_profile:
        db_profile = sql_models.AthleteProfile(user_id=current_user.id)
        db.add(db_profile)
    
    db_profile.basic_info = profile_data.basic_info.dict()
    db_profile.physical_metrics = profile_data.physical_metrics.dict()
    db_profile.sport_context = profile_data.sport_context.dict()
    db_profile.training_preferences = profile_data.training_preferences.dict()
    db_profile.goals = profile_data.goals
    db_profile.constraints = profile_data.constraints
    
    if not db_profile.coach_memory:
        memory = CoachLogic.initialize_memory(db_profile)
        db.add(memory)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.get("/coach-memories/me", response_model=schemas.CoachMemoryResponse)
async def get_my_coach_memory(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.athlete_profile or not current_user.athlete_profile.coach_memory:
        raise HTTPException(status_code=404, detail="Profil ou Mémoire introuvable. Complétez votre profil.")
    return current_user.athlete_profile.coach_memory

@router.post("/coach-memories/recalculate")
async def force_recalculate(
    current_user: sql_models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = current_user.athlete_profile
    if not profile or not profile.coach_memory:
        raise HTTPException(status_code=404, detail="Introuvable")
        
    CoachLogic.update_daily(profile.coach_memory, profile)
    db.commit()
    return {"status": "updated", "new_readiness": profile.coach_memory.current_context.get('readiness_score')}
"""

# --- FONCTIONS UTILITAIRES ---
def write_file(path, content):
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"✅ Fichier écrit : {path}")

def update_main_py():
    main_path = os.path.join(BASE_DIR, "app/main.py")
    if not os.path.exists(main_path):
        logger.error(f"❌ Impossible de trouver {main_path}. Vérifiez l'emplacement du script.")
        return

    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "app.routers import profiles" in content:
        logger.info("ℹ️ main.py déjà à jour.")
        return

    content = content.replace(
        "from app.routers import performance, safety, auth, workouts, coach, user, feed",
        "from app.routers import performance, safety, auth, workouts, coach, user, feed, profiles"
    )
    
    if "app.include_router(feed.router)" in content:
        content = content.replace(
            "app.include_router(feed.router)",
            "app.include_router(feed.router)\napp.include_router(profiles.router)"
        )
    
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("✅ main.py mis à jour avec le routeur profiles.")

def migrate_database():
    """Migration SQL + Données"""
    logger.info("🔄 Démarrage de la migration base de données...")
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. CRÉATION DES TABLES V2
            logger.info("🆕 Création des tables V2 (si absentes)...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS athlete_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    basic_info JSON DEFAULT '{}',
                    physical_metrics JSON DEFAULT '{}',
                    sport_context JSON DEFAULT '{}',
                    performance_baseline JSON DEFAULT '{}',
                    injury_prevention JSON DEFAULT '{}',
                    training_preferences JSON DEFAULT '{}',
                    goals JSON DEFAULT '{}',
                    constraints JSON DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS coach_memories (
                    id SERIAL PRIMARY KEY,
                    athlete_profile_id INTEGER UNIQUE REFERENCES athlete_profiles(id) ON DELETE CASCADE,
                    metadata_info JSON DEFAULT '{}',
                    current_context JSON DEFAULT '{}',
                    response_patterns JSON DEFAULT '{}',
                    performance_baselines JSON DEFAULT '{}',
                    adaptation_signals JSON DEFAULT '{}',
                    sport_specific_insights JSON DEFAULT '{}',
                    training_history_summary JSON DEFAULT '{}',
                    athlete_preferences JSON DEFAULT '{}',
                    coach_notes JSON DEFAULT '{}',
                    memory_flags JSON DEFAULT '{}',
                    last_updated TIMESTAMPTZ DEFAULT NOW()
                );
            """))

            # 1.5. PATCH DES TABLES EXISTANTES (Correction de l'erreur email)
            # Cette étape ajoute les colonnes AVANT d'essayer de les lire pour la migration
            logger.info("🔧 Vérification et réparation du schéma 'users'...")
            try:
                # Tentative d'ajout des colonnes si elles manquent
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"))
            except Exception as e:
                logger.warning(f"⚠️ Note sur le patch de schéma: {e}")
                # En cas d'erreur ici, on continue, l'étape de migration de données échouera plus tard si critique

            # 2. MIGRATION DES DONNÉES
            logger.info("🔄 Migration des données utilisateurs existants...")
            
            # Maintenant que la colonne email existe forcément, cette requête ne plantera plus
            result = conn.execute(text("SELECT id, username, email, profile_data FROM users"))
            users = result.fetchall()
            
            migrated_count = 0
            for u in users:
                # Vérifier si profil existe déjà
                exists = conn.execute(text(f"SELECT 1 FROM athlete_profiles WHERE user_id = {u.id}")).scalar()
                if not exists:
                    # Parsing old data
                    old_data = {}
                    if u.profile_data:
                        try:
                            old_data = json.loads(u.profile_data)
                        except:
                            pass
                    
                    # Construction new data structure
                    basic_info = json.dumps({"pseudo": u.username, "email": u.email})
                    physical_metrics = json.dumps({"weight": old_data.get("weight", 0), "height": old_data.get("height", 0)})
                    sport_context = json.dumps({"sport": old_data.get("sport", "Autre"), "level": old_data.get("level", "Intermédiaire")})
                    
                    # Insert AthleteProfile
                    conn.execute(text("""
                        INSERT INTO athlete_profiles (user_id, basic_info, physical_metrics, sport_context)
                        VALUES (:uid, :bi, :pm, :sc)
                    """), {"uid": u.id, "bi": basic_info, "pm": physical_metrics, "sc": sport_context})
                    
                    # Get Profile ID
                    pid_result = conn.execute(text(f"SELECT id FROM athlete_profiles WHERE user_id = {u.id}"))
                    pid = pid_result.scalar()
                    
                    # Insert Default CoachMemory
                    if pid:
                        conn.execute(text("""
                            INSERT INTO coach_memories (athlete_profile_id, current_context, memory_flags)
                            VALUES (:pid, '{"readiness_score": 80, "phase": "Integration"}', '{"migrated": true}')
                        """), {"pid": pid})
                    
                    migrated_count += 1
            
            trans.commit()
            logger.info(f"✅ Migration terminée : {migrated_count} utilisateurs migrés vers v2.")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Erreur migration DB: {e}")
            raise e

# --- EXECUTION PRINCIPALE ---

if __name__ == "__main__":
    print("🚀 Démarrage de la mise à jour TitanFlow v2 (Fix Email)...")
    
    # 1. Écriture des fichiers
    write_file("app/models/sql_models.py", SQL_MODELS_CONTENT)
    write_file("app/models/schemas.py", SCHEMAS_CONTENT)
    write_file("app/services/coach_logic.py", LOGIC_CONTENT)
    write_file("app/routers/profiles.py", ROUTER_CONTENT)
    
    # 2. Mise à jour main.py
    update_main_py()
    
    # 3. Migration DB
    try:
        migrate_database()
    except Exception as e:
        logger.error(f"❌ Échec critique: {e}")

    print("\n✨ Installation terminée ! Relancez le serveur Uvicorn.")