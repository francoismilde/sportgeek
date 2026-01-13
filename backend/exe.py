import os

# Contenu EXACT et COMPLET de sql_models.py
SQL_MODELS_CONTENT = r"""from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text, Boolean, JSON
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

# Détection automatique du chemin
POSSIBLE_PATHS = [
    os.path.join("backend", "app", "models", "sql_models.py"),
    os.path.join("app", "models", "sql_models.py"),
]

def fix_models():
    target_path = next((p for p in POSSIBLE_PATHS if os.path.exists(os.path.dirname(p))), None)
    
    if not target_path:
        # Si le dossier n'existe pas, on tente de le créer à la racine backend standard
        target_path = os.path.join("backend", "app", "models", "sql_models.py")
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

    print(f"🚑 Réparation d'urgence de : {target_path}")

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(SQL_MODELS_CONTENT)
        
    print("✅ Fichier sql_models.py réécrit avec succès.")
    print("👉 ACTION REQUISE : git add . && git commit -m 'fix: Restore sql_models' && git push")

if __name__ == "__main__":
    fix_models()