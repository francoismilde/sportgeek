"""
Job quotidien pour mettre à jour les mémoires du coach
Exécuté automatiquement à 02:00 chaque jour
"""
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import SessionLocal
from app.models import sql_models
from app.services.coach_memory.service import CoachMemoryService

logger = logging.getLogger(__name__)

async def daily_coach_memory_update():
    """
    Met à jour toutes les mémoires du coach quotidiennement
    """
    logger.info("🚀 Démarrage du job quotidien de mise à jour des mémoires du coach")
    
    db = SessionLocal()
    try:
        # Récupérer toutes les mémoires actives
        coach_memories = db.query(sql_models.CoachMemory).all()
        
        logger.info(f"📊 {len(coach_memories)} mémoires à mettre à jour")
        
        updated_count = 0
        error_count = 0
        
        for memory in coach_memories:
            try:
                # Récupérer le profil associé
                athlete_profile = db.query(sql_models.AthleteProfile).filter(
                    sql_models.AthleteProfile.id == memory.athlete_profile_id
                ).first()
                
                if not athlete_profile:
                    logger.warning(f"Profil non trouvé pour la mémoire {memory.id}")
                    continue
                
                # Mettre à jour le contexte avec des valeurs par défaut
                default_checkin = {
                    "sleep_quality": 7,
                    "sleep_duration": 7.5,
                    "perceived_stress": 5,
                    "muscle_soreness": 3,
                    "energy_level": 7
                }
                
                # Mettre à jour le contexte
                CoachMemoryService.update_daily_context(memory, default_checkin, db)
                
                # Mettre à jour les métadonnées
                metadata = json.loads(memory.metadata) if memory.metadata else {}
                metadata['last_daily_update'] = datetime.utcnow().isoformat()
                metadata['total_updates'] = metadata.get('total_updates', 0) + 1
                memory.metadata = json.dumps(metadata)
                
                updated_count += 1
                
                # Log tous les 10 profils
                if updated_count % 10 == 0:
                    logger.info(f"✅ {updated_count} mémoires mises à jour")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Erreur mise à jour mémoire {memory.id}: {str(e)}")
                continue
        
        db.commit()
        
        logger.info(f"🎉 Job terminé: {updated_count} mises à jour, {error_count} erreurs")
        
        # Générer un rapport
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_memories": len(coach_memories),
            "updated": updated_count,
            "errors": error_count,
            "success_rate": (updated_count / len(coach_memories) * 100) if coach_memories else 100
        }
        
        logger.info(f"📈 Rapport: {report}")
        
        return report
        
    except Exception as e:
        logger.error(f"💥 Erreur critique dans le job quotidien: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

async def update_memory_flags_batch():
    """
    Met à jour les flags de mémoire en batch
    """
    logger.info("🚀 Mise à jour batch des flags de mémoire")
    
    db = SessionLocal()
    try:
        # Récupérer les mémoires avec contexte récent
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        
        coach_memories = db.query(sql_models.CoachMemory).filter(
            sql_models.CoachMemory.last_updated >= one_day_ago
        ).all()
        
        for memory in coach_memories:
            try:
                context = json.loads(memory.current_context) if memory.current_context else {}
                readiness = context.get('readiness_score', 70)
                
                memory_flags = json.loads(memory.memory_flags) if memory.memory_flags else {}
                
                # Mettre à jour les flags basés sur le contexte
                memory_flags['needs_deload'] = readiness < 40
                memory_flags['adaptation_window_open'] = readiness > 70
                memory_flags['pr_potential'] = readiness > 80 and context.get('fatigue_state') == 'fresh'
                
                memory.memory_flags = json.dumps(memory_flags)
                
            except Exception as e:
                logger.error(f"❌ Erreur mise à jour flags mémoire {memory.id}: {str(e)}")
                continue
        
        db.commit()
        logger.info(f"✅ Flags mis à jour pour {len(coach_memories)} mémoires")
        
    except Exception as e:
        logger.error(f"💥 Erreur batch flags: {str(e)}")
        db.rollback()
    finally:
        db.close()

async def cleanup_old_data():
    """
    Nettoie les données anciennes
    """
    logger.info("🧹 Nettoyage des données anciennes")
    
    db = SessionLocal()
    try:
        # Supprimer les profils incomplets de plus de 30 jours
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        incomplete_profiles = db.query(sql_models.AthleteProfile).filter(
            and_(
                sql_models.AthleteProfile.is_complete == False,
                sql_models.AthleteProfile.created_at < thirty_days_ago
            )
        ).all()
        
        deleted_count = 0
        for profile in incomplete_profiles:
            try:
                db.delete(profile)
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Erreur suppression profil {profile.id}: {str(e)}")
        
        db.commit()
        logger.info(f"🗑️  {deleted_count} profils incomplets supprimés")
        
    except Exception as e:
        logger.error(f"💥 Erreur nettoyage: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Pour exécution manuelle
    import asyncio
    import json
    
    async def main():
        logger.info("🧪 Exécution manuelle du job quotidien")
        
        # Exécuter les tâches
        report = await daily_coach_memory_update()
        await update_memory_flags_batch()
        await cleanup_old_data()
        
        print(json.dumps(report, indent=2))
    
    asyncio.run(main())
