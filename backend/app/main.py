# ROUTE SPÉCIALE DE RÉPARATION (SELF-REPAIR V6 - COMPLÉTION SCHÉMA)
@app.get("/fix_db", tags=["System"])
def fix_database_schema():
    """
    🛠️ ROUTE D'URGENCE V6 : Création complète des tables + Index + Foreign Keys.
    """
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            
            # 1. CRÉATION DES TABLES V2 (Si elles n'existent pas)
            
            # Table Profil Athlète
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS athlete_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    basic_info JSON DEFAULT '{}',
                    physical_metrics JSON DEFAULT '{}',
                    sport_context JSON DEFAULT '{}',
                    performance_baseline JSON DEFAULT '{}',
                    injury_prevention JSON DEFAULT '{}',
                    training_preferences JSON DEFAULT '{}',
                    goals JSON DEFAULT '{}',
                    constraints JSON DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            
            # Table Mémoire Coach
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS coach_memories (
                    id SERIAL PRIMARY KEY,
                    athlete_profile_id INTEGER UNIQUE REFERENCES athlete_profiles(id) ON DELETE CASCADE,
                    metadata_info JSON DEFAULT '{}',
                    current_context JSON DEFAULT '{}',
                    response_patterns JSON DEFAULT '{}',
                    performance_baselines JSON DEFAULT '{}',
                    adaptation_signals JSON DEFAULT '{}',
                    sport_specific_insights JSON DEFAULT '{}',
                    training_history_summary JSON DEFAULT '{}',
                    athlete_preferences JSON DEFAULT '{}',
                    coach_notes JSON DEFAULT '{}',
                    memory_flags JSON DEFAULT '{}',
                    last_updated TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            
            # Table Feed Items (CRITIQUE pour le Neural Feed)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS feed_items (
                    id VARCHAR PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    type VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    message VARCHAR NOT NULL,
                    action_payload TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    is_completed BOOLEAN DEFAULT FALSE,
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            
            # 2. CRÉATION DES INDEX POUR PERFORMANCE
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_feed_items_user_id 
                ON feed_items(user_id) WHERE is_completed = FALSE;
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_feed_items_type 
                ON feed_items(type);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_feed_items_priority_created 
                ON feed_items(priority DESC, created_at DESC);
            """))
            
            # 3. PATCH DES TABLES EXISTANTES (Colonnes manquantes)
            
            # Table USERS
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data TEXT;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS strategy_data TEXT;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_plan_data TEXT;"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS draft_workout_data TEXT;"))

            # Table WORKOUT_SESSIONS (Colonnes pour l'analyse IA)
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS energy_level INTEGER DEFAULT 5;"))
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes TEXT;"))
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"))
            connection.execute(text("ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS ai_analysis TEXT;"))
            
            # Table WORKOUT_SETS (Colonnes pour le polymorphisme des métriques)
            connection.execute(text("ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS metric_type VARCHAR DEFAULT 'LOAD_REPS';"))
            connection.execute(text("ALTER TABLE workout_sets ADD COLUMN IF NOT EXISTS rest_seconds INTEGER DEFAULT 0;"))
            
            # 4. CONTRAINTES DE SÉCURITÉ SUPPLÉMENTAIRES
            connection.execute(text("""
                ALTER TABLE feed_items 
                ADD CONSTRAINT check_feed_item_priority 
                CHECK (priority BETWEEN 1 AND 10);
            """))
            
            connection.execute(text("""
                ALTER TABLE workout_sessions 
                ADD CONSTRAINT check_rpe_range 
                CHECK (rpe BETWEEN 0 AND 10);
            """))
            
            connection.execute(text("""
                ALTER TABLE workout_sessions 
                ADD CONSTRAINT check_energy_range 
                CHECK (energy_level BETWEEN 1 AND 10);
            """))
            
            trans.commit()
            
            # 5. VÉRIFICATION POST-MIGRATION
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            return {
                "status": "SUCCESS", 
                "message": "✅ Base de données migrée V6 avec succès !",
                "tables_created": [
                    "athlete_profiles" if "athlete_profiles" in tables else "❌",
                    "coach_memories" if "coach_memories" in tables else "❌",
                    "feed_items" if "feed_items" in tables else "❌"
                ],
                "missing_columns_fixed": [
                    "users.email ✅" if "email" in [col['name'] for col in inspector.get_columns('users')] else "❌",
                    "workout_sessions.ai_analysis ✅" if "ai_analysis" in [col['name'] for col in inspector.get_columns('workout_sessions')] else "❌",
                    "workout_sets.metric_type ✅" if "metric_type" in [col['name'] for col in inspector.get_columns('workout_sets')] else "❌"
                ]
            }
            
    except Exception as e:
        return {"status": "ERROR", "message": f"❌ Erreur lors de la migration : {str(e)}"}