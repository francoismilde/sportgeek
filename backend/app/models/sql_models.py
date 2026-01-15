from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import MemoryType, ImpactLevel, MemoryStatus

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    
    # Legacy fields
    profile_data = Column(JSON, default={}) 
    strategy_data = Column(Text, nullable=True)
    weekly_plan_data = Column(Text, nullable=True)
    draft_workout_data = Column(Text, nullable=True)

    workouts = relationship("WorkoutSession", back_populates="owner")
    feed_items = relationship("FeedItem", back_populates="owner", cascade="all, delete-orphan")
    athlete_profile = relationship("AthleteProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class AthleteProfile(Base):
    __tablename__ = "athlete_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

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

    @property
    def completion_percentage(self):
        sections = [
            self.basic_info, self.physical_metrics, self.sport_context,
            self.performance_baseline, self.injury_prevention,
            self.training_preferences, self.goals, self.constraints
        ]
        filled = sum(1 for section in sections if section and section != {})
        total = len(sections)
        return int((filled / total) * 100) if total > 0 else 0

    @property
    def is_complete(self):
        return self.completion_percentage >= 80

class CoachMemory(Base):
    __tablename__ = "coach_memories"

    id = Column(Integer, primary_key=True, index=True)
    athlete_profile_id = Column(Integer, ForeignKey("athlete_profiles.id"), unique=True)

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
    
    # [NOUVEAU] Relation vers les Engrammes
    engrams = relationship("CoachEngram", back_populates="memory", cascade="all, delete-orphan")

class CoachEngram(Base):
    """
    Unité de mémoire structurée (Souvenir/Règle) pour le Coach IA.
    """
    __tablename__ = "coach_engrams"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("coach_memories.id"), nullable=False)
    
    author = Column(String, default="COACH_AI")
    type = Column(SQLEnum(MemoryType), nullable=False)
    impact = Column(SQLEnum(ImpactLevel), nullable=False, default=ImpactLevel.INFO)
    status = Column(SQLEnum(MemoryStatus), nullable=False, default=MemoryStatus.ACTIVE)
    
    content = Column(Text, nullable=False)
    
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    tags = Column(JSON, default=[]) # Ex: ["genou", "squat", "douleur"]

    # Relation parente
    memory = relationship("CoachMemory", back_populates="engrams")

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