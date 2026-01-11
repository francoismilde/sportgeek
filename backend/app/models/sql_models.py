from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    
    # ✅ LA SEULE SOURCE DE VÉRITÉ POUR LE PROFIL
    # Plus de relation complexe. Tout le JSON de Flutter arrive ici.
    profile_data = Column(JSON, default={}) 
    
    # Legacy fields (on garde pour éviter de casser des vieux logics au cas où)
    strategy_data = Column(Text, nullable=True)
    weekly_plan_data = Column(Text, nullable=True)
    draft_workout_data = Column(Text, nullable=True)

    # Relations conservées (Essentielles)
    workouts = relationship("WorkoutSession", back_populates="owner")
    feed_items = relationship("FeedItem", back_populates="owner", cascade="all, delete-orphan")
    
    # 🗑️ SUPPRIMÉ : relationship("AthleteProfile") -> Cause du crash mapper

# 🗑️ SUPPRIMÉ : class AthleteProfile(...)
# 🗑️ SUPPRIMÉ : class CoachMemory(...) 
# (Ces tables disparaissent au profit du profile_data JSON)

# --- ON GARDE LES SÉANCES (CRITIQUE POUR L'HISTORIQUE) ---
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

# --- ON GARDE LE FEED (CRITIQUE POUR LES NOTIFS) ---
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