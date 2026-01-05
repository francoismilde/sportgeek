import streamlit as st
import requests
import pandas as pd
import os  # <--- Ajout de l'import os

# Configuration de la page
st.set_page_config(page_title="TitanFlow Pro", page_icon="⚡", layout="wide")

# L'URL de ton API (Backend)
# En PROD (Render) : Il utilisera la variable d'environnement BACKEND_URL
# En LOCAL (Ton PC) : Il utilisera http://127.0.0.1:8000 par défaut
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- GESTION DE LA SESSION (Token) ---
if "token" not in st.session_state:
    st.session_state.token = None

def login():
    st.sidebar.header("🔐 Connexion")
    username = st.sidebar.text_input("Pseudo")
    password = st.sidebar.text_input("Mot de passe", type="password")
    
    if st.sidebar.button("Se connecter"):
        try:
            # Appel à l'API pour récupérer le token
            response = requests.post(
                f"{API_URL}/auth/token",
                data={"username": username, "password": password}
            )
            if response.status_code == 200:
                st.session_state.token = response.json()["access_token"]
                st.sidebar.success("Connecté !")
                st.rerun()
            else:
                st.sidebar.error("Erreur de connexion")
        except Exception as e:
            st.sidebar.error(f"API introuvable : {e}")

def logout():
    if st.sidebar.button("Se déconnecter"):
        st.session_state.token = None
        st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title("⚡ TitanFlow : Monitoring Athlétique")

# Vérification de l'état de l'API
try:
    health = requests.get(f"{API_URL}/health").json()
    st.success(f"Backend connecté v{health['version']}")
except:
    st.error("🚨 Le Backend semble éteint. Vérifie que l'URL est correcte.")

# Gestion Login/Logout
if not st.session_state.token:
    st.info("Veuillez vous connecter dans la barre latérale pour accéder aux données.")
    login()
else:
    logout()
    st.write("---")
    
    # Onglets de l'application
    tab1, tab2 = st.tabs(["🏋️‍♂️ Historique", "➕ Nouvelle Séance"])
    
    # --- ONGLET 1 : HISTORIQUE ---
    with tab1:
        st.subheader("Vos séances enregistrées")
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        
        try:
            res = requests.get(f"{API_URL}/workouts/", headers=headers)
            if res.status_code == 200:
                workouts = res.json()
                if workouts:
                    df = pd.DataFrame(workouts)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Aucune séance trouvée.")
            else:
                st.error("Erreur chargement données")
        except Exception as e:
            st.error(f"Erreur : {e}")

    # --- ONGLET 2 : AJOUTER SÉANCE ---
    with tab2:
        st.subheader("Enregistrer un entraînement")
        with st.form("new_workout"):
            col1, col2 = st.columns(2)
            date = col1.date_input("Date")
            duration = col2.number_input("Durée (min)", min_value=0, value=60)
            rpe = st.slider("Intensité (RPE)", 0, 10, 5)
            
            submitted = st.form_submit_button("Sauvegarder")
            
            if submitted:
                payload = {
                    "date": str(date),
                    "duration": duration,
                    "rpe": rpe
                }
                res = requests.post(f"{API_URL}/workouts/", json=payload, headers=headers)
                
                if res.status_code == 200:
                    st.success("Séance enregistrée ! 🎉")
                    st.rerun()
                else:
                    st.error(f"Erreur : {res.text}")