import os

# Chemins
BASE_DIR = "backend/app"
OLD_MODELS_PATH = os.path.join(BASE_DIR, "models", "sql_models.py")
NEW_MODELS_PATH = os.path.join(BASE_DIR, "models", "core_models.py")

# Contenu EXACT et COMPLET des modèles (ISO Prod)
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

def update_imports(directory):
    """Parcourt tous les fichiers .py et remplace sql_models par core_models"""
    print(f"🔄 Mise à jour des imports dans {directory}...")
    
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "final_rename.py":
                path = os.path.join(root, file)
                
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Remplacement intelligent
                new_content = content
                
                # 1. from app.models import sql_models -> from app.models import core_models
                new_content = new_content.replace("from app.models import sql_models", "from app.models import core_models")
                
                # 2. import app.models.sql_models -> import app.models.core_models
                new_content = new_content.replace("import app.models.sql_models", "import app.models.core_models")
                
                # 3. sql_models. -> core_models.
                # Attention : on remplace l'usage dans le code
                new_content = new_content.replace("sql_models.", "core_models.")
                
                # 4. Alias : as sql_models -> as core_models
                new_content = new_content.replace(" as sql_models", " as core_models")

                if content != new_content:
                    print(f"   📝 Modifié : {file}")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    count += 1
    print(f"✅ {count} fichiers mis à jour.")

def main():
    print("☢️  OPÉRATION RENOMMAGE FINAL DÉMARRÉE")
    
    # 1. Créer le nouveau fichier core_models.py
    os.makedirs(os.path.dirname(NEW_MODELS_PATH), exist_ok=True)
    with open(NEW_MODELS_PATH, "w", encoding="utf-8") as f:
        f.write(MODELS_CONTENT)
    print(f"✅ Créé : {NEW_MODELS_PATH}")

    # 2. Mettre à jour tous les imports
    update_imports("backend")

    # 3. Supprimer l'ancien fichier (et models_v2 s'il existe)
    if os.path.exists(OLD_MODELS_PATH):
        os.remove(OLD_MODELS_PATH)
        print(f"🗑️  Supprimé : {OLD_MODELS_PATH}")
    
    v2_path = os.path.join(BASE_DIR, "models", "models_v2.py")
    if os.path.exists(v2_path):
        os.remove(v2_path)
        print(f"🗑️  Supprimé : {v2_path}")
    
    print("\n🎉 Terminé ! Tout pointe maintenant vers core_models.")
    print("👉 Fais ton git add/commit/push maintenant.")

if __name__ == "__main__":
    main()