from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- 1RM Schemas ---
class OneRepMaxRequest(BaseModel):
    weight: float = Field(..., gt=0, description="Poids soulevé en kg")
    reps: int = Field(..., gt=0, lt=100, description="Nombre de répétitions réalisées")

class OneRepMaxResponse(BaseModel):
    estimated_1rm: float
    method_used: str
    input_weight: float
    input_reps: int

# --- ACWR Schemas ---
class WorkoutLogInput(BaseModel):
    date: date
    duration: float = Field(..., ge=0, description="Durée en minutes")
    rpe: float = Field(..., ge=0, le=10, description="Intensité ressentie (0-10)")

class ACWRRequest(BaseModel):
    history: List[WorkoutLogInput]

class ACWRResponse(BaseModel):
    ratio: float
    status: str
    color: str
    acute_load: int
    chronic_load: int
    message: str

# --- USER / AUTH Schemas ---
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, description="Pseudo unique")
    # AJOUT DU CHAMP EMAIL
    email: Optional[str] = None
    password: str = Field(..., min_length=6, description="Mot de passe fort")

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- TOKEN Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None