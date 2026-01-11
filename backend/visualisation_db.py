import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect, text

# --- 1. CONFIGURATION ---
# Votre URL est intégrée ici :
DB_URL = "postgresql://titanflow_prod_db_user:1VRDWljUne5YD0lczDfcY3gLglcgS3VU@dpg-d5ec3fruibrs738a76a0-a.frankfurt-postgres.render.com/titanflow_prod_db"

st.set_page_config(
    page_title="TitanFlow DB Admin", 
    layout="wide",  # Mode "Large" pour voir toutes les colonnes
    page_icon="👁️"
)

# CSS pour maximiser l'espace
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    div[data-testid="stDataFrame"] { width: 100%; }
</style>
""", unsafe_allow_html=True)

st.title("👁️ TitanFlow - Inspecteur de Base de Données")

# --- 2. CONNEXION ---
try:
    # Petit nettoyage au cas où (Render donne parfois postgres:// au lieu de postgresql://)
    if DB_URL.startswith("postgres://"):
        real_url = DB_URL.replace("postgres://", "postgresql://", 1)
    else:
        real_url = DB_URL

    engine = create_engine(real_url)
    inspector = inspect(engine)
    
    # Test de connexion et récupération des tables
    all_tables = inspector.get_table_names()

    if not all_tables:
        st.warning("⚠️ Connexion réussie, mais aucune table trouvée dans la base.")
    else:
        # --- 3. SIDEBAR (Navigation) ---
        st.sidebar.header("📂 Tables disponibles")
        
        # Tri : on met les tables importantes en haut
        priority = ['users', 'athlete_profiles', 'workout_sessions', 'coach_memories']
        sorted_tables = sorted(all_tables, key=lambda x: (0 if x in priority else 1, x))
        
        selected_table = st.sidebar.radio("Sélectionnez une table :", sorted_tables)

        st.divider()
        st.header(f"Table : `{selected_table}`")

        # --- 4. INSPECTION DE LA STRUCTURE (Colonnes) ---
        # C'est ici qu'on vérifie si les colonnes existent vraiment
        columns_info = inspector.get_columns(selected_table)
        col_names = [col['name'] for col in columns_info]
        
        st.info(f"📊 La table contient **{len(col_names)} colonnes**.")
        
        # Liste déroulante pour vérifier les noms exacts
        with st.expander("🔎 Cliquez ici pour voir la liste exacte des colonnes (Schéma)"):
            schema_df = pd.DataFrame([
                {"Nom": c['name'], "Type": str(c['type']), "Nullable": c['nullable']} 
                for c in columns_info
            ])
            st.table(schema_df)

        # --- 5. AFFICHAGE DES DONNÉES ---
        st.subheader("Données enregistrées")
        
        with engine.connect() as conn:
            # On récupère tout le contenu
            query = text(f"SELECT * FROM {selected_table}")
            df = pd.read_sql(query, conn)

        if df.empty:
            st.warning("Cette table est vide (0 ligne).")
        else:
            # Affichage du tableau interactif
            st.dataframe(
                df, 
                use_container_width=True, 
                height=600  # Grande hauteur pour le confort
            )

except Exception as e:
    st.error("❌ Erreur de connexion")
    st.error(f"Détails : {e}")
    st.info("Vérifiez votre connexion internet ou si l'URL a changé.")