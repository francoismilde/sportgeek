import sys
import os
import pytest

# Ajout du path pour trouver le module app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.onboarding import AthleteOnboardingService

def test_null_state_flags():
    """Vérifie que les flags sont levés si les données manquent."""
    raw_data = {
        "physical_metrics": {"weight": 75},
        "performance_baseline": {} # Vide
    }
    
    result = AthleteOnboardingService.process_profile(raw_data)
    
    assert result.success is True
    flags = result.data['memory_flags']
    assert flags['NEEDS_TESTING_FORCE'] is True
    assert flags['NEEDS_TESTING_AEROBIC'] is True
    assert flags['force_status'] == "Unknown"

def test_sanity_check_vma():
    """Vérifie le rejet d'une VMA impossible."""
    raw_data = {
        "performance_baseline": {"vma": 30.0} # Trop rapide
    }
    
    result = AthleteOnboardingService.process_profile(raw_data)
    
    assert result.success is False
    assert result.errors[0].field == "vma"

def test_css_calculation_success():
    """Vérifie le calcul correct du CSS."""
    # Exemple : 
    # 200m en 2:30 (150s) -> 1.33 m/s
    # 400m en 5:20 (320s) -> 1.25 m/s
    # Delta Dist = 200m
    # Delta Time = 320 - 150 = 170s
    # CSS = 200 / 170 = 1.176... -> 1.18 m/s
    
    raw_data = {
        "performance_baseline": {
            "swim_200m_time_sec": 150,
            "swim_400m_time_sec": 320
        }
    }
    
    result = AthleteOnboardingService.process_profile(raw_data)
    
    assert result.success is True
    assert result.data['performance_baseline']['critical_swim_speed'] == 1.18

def test_css_sanity_failure():
    """Vérifie le rejet d'un CSS incohérent (ex: temps 400m < 200m)."""
    raw_data = {
        "performance_baseline": {
            "swim_200m_time_sec": 300,
            "swim_400m_time_sec": 200 # Impossible, plus rapide sur plus long
        }
    }
    
    result = AthleteOnboardingService.process_profile(raw_data)
    
    assert result.success is False
    assert "swim_times" in [e.field for e in result.errors]

def test_relative_strength():
    """Vérifie le calcul de la force relative."""
    raw_data = {
        "physical_metrics": {"weight": 80},
        "performance_baseline": {"squat_1rm": 120}
    }
    # Ratio = 120 / 80 = 1.5
    
    result = AthleteOnboardingService.process_profile(raw_data)
    assert result.data['performance_baseline']['relative_strength_squat'] == 1.5

if __name__ == "__main__":
    # Petit runner manuel si on n'a pas pytest installé globalement
    try:
        test_null_state_flags()
        print("✅ test_null_state_flags PASSED")
        test_sanity_check_vma()
        print("✅ test_sanity_check_vma PASSED")
        test_css_calculation_success()
        print("✅ test_css_calculation_success PASSED")
        test_css_sanity_failure()
        print("✅ test_css_sanity_failure PASSED")
        test_relative_strength()
        print("✅ test_relative_strength PASSED")
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")