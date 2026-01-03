import math
from abc import ABC, abstractmethod

# --- STRATEGY PATTERN : MOTEUR 1RM ---

class OneRepMaxStrategy(ABC):
    """Interface abstraite pour les stratégies de calcul du 1RM."""
    @abstractmethod
    def calculate(self, weight: float, reps: int) -> float:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

class EpleyStrategy(OneRepMaxStrategy):
    """Formule d'Epley : W * (1 + r/30)"""
    def calculate(self, weight: float, reps: int) -> float:
        return weight * (1 + reps / 30.0)

    @property
    def name(self) -> str:
        return "Epley"

class BrzyckiStrategy(OneRepMaxStrategy):
    """Formule de Brzycki : W * (36 / (37 - r))"""
    def calculate(self, weight: float, reps: int) -> float:
        if reps >= 37: return 0.0
        return weight * (36.0 / (37.0 - reps))

    @property
    def name(self) -> str:
        return "Brzycki"

class WathanStrategy(OneRepMaxStrategy):
    """Formule de Wathan : Exponentielle"""
    def calculate(self, weight: float, reps: int) -> float:
        denominator = 48.8 + (53.8 * math.exp(-0.075 * reps))
        if denominator == 0: return 0.0
        return (100.0 * weight) / denominator

    @property
    def name(self) -> str:
        return "Wathan"

class OneRepMaxCalculator:
    """Factory : Sélectionne la bonne stratégie selon le nombre de répétitions."""
    @staticmethod
    def get_strategy(reps: int) -> OneRepMaxStrategy:
        if reps <= 5:
            return EpleyStrategy()
        elif reps <= 10:
            return BrzyckiStrategy()
        else:
            return WathanStrategy()

def calculate_1rm(weight: float, reps: int) -> dict:
    """
    Fonction principale exposée au reste de l'app.
    """
    if weight <= 0 or reps <= 0:
        return {"1rm": 0.0, "method": "N/A"}
    
    if reps == 1:
        return {"1rm": weight, "method": "Actual Lift"}
        
    if reps > 30:
        return {"1rm": 0.0, "method": "Out of Range (>30)"}

    strategy = OneRepMaxCalculator.get_strategy(reps)
    one_rm_val = strategy.calculate(weight, reps)
    
    # Arrondi au 0.5kg le plus proche
    final_val = round(one_rm_val * 2) / 2

    return {
        "1rm": final_val,
        "method": strategy.name
    }