from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    # AJOUT DE L'EMAIL
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    
    workouts = relationship("WorkoutSession", back_populates="owner")

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    duration = Column(Float)
    rpe = Column(Float)
    
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="workouts")