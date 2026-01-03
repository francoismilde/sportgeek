import pandas as pd
from datetime import date, timedelta
import re

def _safe_float(val):
    """Helper pour convertir n'importe quoi en float."""
    if val is None: return 0.0
    try:
        clean = str(val).replace(',', '.').strip()
        match = re.search(r"[-+]?\d*\.\d+|\d+", clean)
        return float(match.group()) if match else 0.0
    except:
        return 0.0

def calculate_acwr(history_logs: list) -> dict:
    """
    Calcule le Ratio Aigu/Chronique (ACWR).
    Entrée : Liste de dictionnaires (date, duration, rpe).
    Sortie : Dict avec ratio, status, charges.
    """
    default_res = {
        "ratio": 0.0,
        "status": "Inactif",
        "color": "gray",
        "acute_load": 0,
        "chronic_load": 0,
        "message": "Pas assez de données."
    }
    
    if not history_logs:
        return default_res

    try:
        # 1. Création DataFrame
        df = pd.DataFrame(history_logs)
        
        # Conversion et tri des dates
        df['date_dt'] = pd.to_datetime(df['date'], errors='coerce').dt.floor('D')
        df = df.dropna(subset=['date_dt']).sort_values('date_dt')
        
        if df.empty:
            return default_res

        # 2. Calcul de la charge (Load = Durée * RPE)
        # On sécurise les valeurs
        df['duration'] = df['duration'].apply(_safe_float)
        df['rpe'] = df['rpe'].apply(_safe_float)
        df['load'] = df['duration'] * df['rpe']
        
        # Agrégation par jour (si plusieurs séances le même jour)
        daily_loads = df.groupby('date_dt')['load'].sum()
        
        # 3. Timeline Continue (J-27 à Aujourd'hui)
        end_date = pd.Timestamp.now().floor('D')
        idx_ref = pd.date_range(end=end_date, periods=28, freq='D')
        
        # On remplit les trous avec 0
        timeline = daily_loads.reindex(idx_ref, fill_value=0)
        
        # 4. Calculs Fenêtres Glissantes
        acute_avg = timeline.tail(7).mean()   # Fatigue (7j)
        chronic_avg = timeline.mean()         # Forme (28j)
        
        # 5. Ratio
        ratio = 0.0
        if chronic_avg > 0:
            ratio = acute_avg / chronic_avg
        elif acute_avg > 0:
            ratio = 2.0 # Reprise brutale
            
        # 6. Diagnostic
        ratio = round(ratio, 2)
        status, color, msg = "Inactif", "gray", "Reprends progressivement."
        
        if ratio > 0:
            if ratio <= 0.80:
                status, color, msg = "Sous-entraînement", "blue", "Charge faible."
            elif 0.80 < ratio <= 1.30:
                status, color, msg = "Optimal", "green", "Zone de progression."
            elif 1.30 < ratio <= 1.50:
                status, color, msg = "Surcharge", "orange", "Attention fatigue."
            else:
                status, color, msg = "DANGER", "red", "Pic de charge critique (>1.5)."

        return {
            "ratio": ratio,
            "status": status,
            "color": color,
            "acute_load": int(acute_avg),
            "chronic_load": int(chronic_avg),
            "message": msg
        }
        
    except Exception as e:
        print(f"Erreur ACWR: {e}")
        return default_res