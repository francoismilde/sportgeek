#!/usr/bin/env python3
"""
Script de migration des données existantes vers les nouveaux modèles v2
"""
import sys
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Ajouter le chemin du backend
sys.path.append('.')

from app.core.database import SessionLocal, engine
from app.models import sql_models
from app.services.coach_memory.service import CoachMemoryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_existing_users():
    """Migre les utilisateurs existants vers les nouveaux modèles"""
    logger.info("🚀 Démarrage de la migration vers v2...")
    
    db = SessionLocal()
    try:
        # Vérifier si les nouvelles tables existent
        inspector = sql_models.inspect(engine)
        table_names = inspector.get_table_names()
        
        if 'athlete_profiles' not in table_names:
            logger.error("❌ Table 'athlete_profiles' non trouvée. Exécutez d'abord les migrations SQL.")
            return False
        
        # Récupérer tous les utilisateurs
        users = db.query(sql_models.User).all()
        logger.info(f"👥 {len(users)} utilisateurs à migrer")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for user in users:
            try:
                # Vérifier si l'utilisateur a déjà un profil
                existing_profile = db.query(sql_models.AthleteProfile).filter(
                    sql_models.AthleteProfile.user_id == user.id
                ).first()
                
                if existing_profile:
                    logger.info(f"⏭️  Utilisateur {user.username} déjà migré")
                    skipped_count += 1
                    continue
                
                # Extraire les données existantes
                profile_data = json.loads(user.profile_data) if user.profile_data else {}
                
                # Construire le profil enrichi
                athlete_profile = sql_models.AthleteProfile(
                    user_id=user.id,
                    basic_info=json.dumps({
                        "pseudo": user.username,
                        "email": user.email,
                        "birth_date": None,
                        "biological_sex": profile_data.get('gender', 'Homme'),
                        "dominant_hand": None,
                        "biological_age": None,
                        "training_age": None
                    }),
                    physical_metrics=json.dumps({
                        "height": profile_data.get('height'),
                        "weight": profile_data.get('weight'),
                        "body_fat_estimate": None,
                        "resting_heart_rate": None,
                        "hrv_baseline": None,
                        "sleep_quality_average": None,
                        "last_updated": None
                    }),
                    sport_context=json.dumps({
                        "primary_sport": profile_data.get('sport', 'Musculation'),
                        "secondary_sports": [],
                        "playing_position": None,
                        "competition_level": profile_data.get('level', 'Amateur'),
                        "training_environment": None,
                        "available_equipment": profile_data.get('equipment', ['Standard']),
                        "training_history_years": None
                    }),
                    performance_baseline=json.dumps({
                        "strength_level": None,
                        "endurance_level": None,
                        "power_level": None,
                        "mobility_level": None,
                        "current_prs": {},
                        "last_test_dates": {}
                    }),
                    injury_prevention=json.dumps({
                        "chronic_issues": profile_data.get('injuries', []),
                        "injury_history": [],
                        "weak_links_identified": [],
                        "prehab_focus": [],
                        "medical_clearance": True
                    }),
                    training_preferences=json.dumps({
                        "preferred_training_split": None,
                        "max_session_duration": 60,
                        "ideal_training_times": [],
                        "disliked_exercises": [],
                        "enjoyed_exercises": [],
                        "motivation_drivers": [],
                        "feedback_style": "Direct",
                        "autonomy_preference": "Medium"
                    }),
                    goals=json.dumps({
                        "primary_goal": profile_data.get('goal', 'Performance Générale'),
                        "secondary_goals": [],
                        "target_date": profile_data.get('target_date', '2025-12-31'),
                        "target_metrics": {},
                        "milestones": []
                    }),
                    constraints=json.dumps({
                        "time_availability": profile_data.get('availability', []),
                        "travel_schedule": [],
                        "work_stress_level": None,
                        "family_commitments": None,
                        "budget_constraints": None
                    })
                )
                
                db.add(athlete_profile)
                db.commit()
                db.refresh(athlete_profile)
                
                # Calculer le pourcentage de complétion
                athlete_profile.completion_percentage = athlete_profile.calculate_completion()
                athlete_profile.is_complete = athlete_profile.completion_percentage >= 80
                
                # Initialiser la mémoire du coach
                try:
                    CoachMemoryService.initialize_coach_memory(athlete_profile, db)
                    migrated_count += 1
                    logger.info(f"✅ {user.username} migré (complétion: {athlete_profile.completion_percentage}%)")
                except Exception as e:
                    logger.error(f"❌ Erreur initialisation mémoire pour {user.username}: {str(e)}")
                    db.rollback()
                    error_count += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur migration utilisateur {user.username}: {str(e)}")
                error_count += 1
                db.rollback()
                continue
        
        db.commit()
        
        logger.info(f"""
🎉 Migration terminée!
━━━━━━━━━━━━━━━━━━━━━━
📊 Statistiques:
   • Migrés: {migrated_count}
   • Déjà migrés: {skipped_count}
   • Erreurs: {error_count}
   • Total: {len(users)}
━━━━━━━━━━━━━━━━━━━━━━
""")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Erreur critique de migration: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def create_tables_if_not_exist():
    """Crée les tables si elles n'existent pas"""
    logger.info("🏗️  Vérification/Création des tables...")
    
    try:
        sql_models.Base.metadata.create_all(bind=engine, tables=[
            sql_models.AthleteProfile.__table__,
            sql_models.CoachMemory.__table__
        ])
        logger.info("✅ Tables vérifiées/créées")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur création tables: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("""
╔══════════════════════════════════════════╗
║   MIGRATION TITANFLOW v1 → v2            ║
╚══════════════════════════════════════════╝
""")
    
    # 1. Créer les tables
    if not create_tables_if_not_exist():
        print("❌ Échec création tables. Arrêt.")
        sys.exit(1)
    
    # 2. Migrer les données
    print("\n🔁 Migration des données utilisateurs...")
    if not migrate_existing_users():
        print("❌ Échec migration données. Vérifiez les logs.")
        sys.exit(1)
    
    print("\n✅ Migration terminée avec succès!")
    print("   Redémarrez le serveur pour activer les nouvelles fonctionnalités.")

if __name__ == "__main__":
    main()
