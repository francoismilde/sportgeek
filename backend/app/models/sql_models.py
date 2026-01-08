# 📄 FICHIER : backend/app/models/sql_models.py

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    
    # Stockage du profil complet (JSON) en texte
    profile_data = Column(Text, nullable=True)
    
    # [NOUVEAU] Mémoire du Coach IA
    strategy_data = Column(Text, nullable=True)      # Stocke le JSON de la Stratégie
    weekly_plan_data = Column(Text, nullable=True)   # Stocke le JSON de la Semaine Type
    
    # [DEV-CARD #05] Brouillon de séance (Persistance en cas de crash)
    draft_workout_data = Column(Text, nullable=True)

    workouts = relationship("WorkoutSession", back_populates="owner")
    # [DEV-CARD #01] Relation avec le Feed
    feed_items = relationship("FeedItem", back_populates="owner", cascade="all, delete-orphan")

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    date = Column(Date, index=True)
    duration = Column(Float)
    rpe = Column(Float)
    energy_level = Column(Integer, default=5) 
    notes = Column(Text, nullable=True)      
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relation One-to-Many
    owner = relationship("User", back_populates="workouts")
    sets = relationship("WorkoutSet", back_populates="session", cascade="all, delete-orphan")

class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id"))
    
    exercise_name = Column(String, index=True)
    set_order = Column(Integer)
    weight = Column(Float, default=0.0)
    
    # [POLYMORPHISME] 
    # reps peut stocker : Répétitions (int), Durée (s), Distance (m) selon le mode
    reps = Column(Float, default=0.0)
    
    rpe = Column(Float, default=0.0)
    rest_seconds = Column(Integer, default=0)
    
    # [CŒUR DU SYSTÈME]
    # Définit comment interpréter 'weight' et 'reps'.
    # Valeurs possibles : LOAD_REPS, ISOMETRIC_TIME, PACE_DISTANCE, POWER_TIME, BODYWEIGHT_REPS
    metric_type = Column(String, nullable=False, default="LOAD_REPS") 
    
    session = relationship("WorkoutSession", back_populates="sets")

# [DEV-CARD #01] NEURAL FEED ARCHITECTURE
class FeedItem(BaseModel):
    __tablename__ = "feed_items"

    id = Column(String, primary_key=True, index=True) # UUID stocké en String
    user_id = Column(Integer, ForeignKey("users.id"))
    
    type = Column(String, index=True) # INFO, ANALYSIS, ACTION, ALERT
    title = Column(String)
    message = Column(String)
    
    # Stockage flexible du payload d'action (JSON stringifié)
    # Ex: {"route": "/profile", "args": {"missing": "weight"}}
    action_payload = Column(Text, nullable=True)
    
    is_read = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    
    priority = Column(Integer, default=1) # 1 (Low) à 10 (Critical)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", back_populates="feed_items")