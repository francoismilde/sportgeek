import os
import re

# Chemins
BASE_DIR = "backend/app"
OLD_MODELS = os.path.join(BASE_DIR, "models", "sql_models.py")
NEW_MODELS = os.path.join(BASE_DIR, "models", "models_v2.py")

# Le contenu correct des modèles (Copie certifiée ISO)
MODELS_CONTENT = r"""from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    profile_data = Column(Text, nullable=True)
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

def replace_imports(directory):
    """Parcourt tous les fichiers .py et remplace sql_models par models_v2"""
    print(f"🔄 Mise à jour des imports dans {directory}...")
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "nuke_cache.py":
                path = os.path.join(root, file)
                
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Remplacement intelligent
                # 1. from app.models import sql_models -> from app.models import models_v2
                # 2. import app.models.sql_models -> import app.models.models_v2
                # 3. sql_models.User -> models_v2.User
                
                new_content = content.replace("app.models.sql_models", "app.models.models_v2")
                new_content = new_content.replace("import sql_models", "import models_v2")
                new_content = new_content.replace("from app.models import sql_models", "from app.models import models_v2")
                
                # Cas spécifique : alias (as sql_models)
                new_content = new_content.replace(" as sql_models", " as models_v2")
                
                # Si on utilise l'alias dans le code
                new_content = new_content.replace("sql_models.", "models_v2.")

                if content != new_content:
                    print(f"   📝 Modifié : {file}")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)

def main():
    print("☢️  OPÉRATION NUKE CACHE DÉMARRÉE")
    
    # 1. Créer le nouveau fichier
    os.makedirs(os.path.dirname(NEW_MODELS), exist_ok=True)
    with open(NEW_MODELS, "w", encoding="utf-8") as f:
        f.write(MODELS_CONTENT)
    print(f"✅ Créé : {NEW_MODELS}")

    # 2. Mettre à jour tous les imports
    # On cible le dossier backend/app
    replace_imports(BASE_DIR)
    
    # On cible aussi la racine backend pour les scripts (init_db, etc.)
    replace_imports("backend")

    # 3. Supprimer l'ancien fichier (Optionnel mais recommandé pour forcer l'erreur si oubli)
    if os.path.exists(OLD_MODELS):
        os.remove(OLD_MODELS)
        print(f"🗑️  Supprimé : {OLD_MODELS}")
    
    print("\n🎉 Terminé ! L'ancien fichier est mort, vive models_v2 !")
    print("👉 Fais ton git add/commit/push maintenant.")

if __name__ == "__main__":
    main()