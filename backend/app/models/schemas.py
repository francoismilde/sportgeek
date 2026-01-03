from pydantic import BaseModel, Field

class OneRepMaxRequest(BaseModel):
    weight: float = Field(..., gt=0, description="Poids soulevé en kg")
    reps: int = Field(..., gt=0, lt=100, description="Nombre de répétitions réalisées")

class OneRepMaxResponse(BaseModel):
    estimated_1rm: float
    method_used: str
    input_weight: float
    input_reps: int