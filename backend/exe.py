# test_performance_validation.py
from app.schemas import PerformanceBaselineSchema

test_data = {
    "running_time_5k": "18:30",  # Format MM:SS
    "cycling_ftp": 280,
    "swimming_time_200m": "02:45",
    "custom_field": "valeur"  # Doit être conservé (extra='allow')
}

try:
    validated = PerformanceBaselineSchema(**test_data)
    print("✅ Validation réussie:", validated.dict())
except Exception as e:
    print("❌ Échec validation:", e)