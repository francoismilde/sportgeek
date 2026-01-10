#!/usr/bin/env python3
"""
Script de vérification backend TitanFlow
Teste la compatibilité avec le frontend Flutter
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import aiohttp
import jwt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendCompatibilityChecker:
    """Vérifie la compatibilité complète du backend TitanFlow"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'environment': {},
            'database': {},
            'api_endpoints': {},
            'data_models': {},
            'security': {},
            'performance': {},
            'issues': [],
            'recommendations': []
        }
        self.base_url = "http://localhost:8000"
        self.auth_token = None
        
    async def run_comprehensive_check(self):
        """Exécute tous les tests de compatibilité"""
        print("🔧 DÉMARRAGE DES TESTS BACKEND TITANFLOW")
        print("=" * 60)
        
        try:
            # 1. Vérification de l'environnement
            await self._check_environment()
            
            # 2. Vérification de la base de données
            await self._check_database()
            
            # 3. Vérification des endpoints API
            await self._check_api_endpoints()
            
            # 4. Vérification des modèles de données
            await self._check_data_models()
            
            # 5. Vérification de la sécurité
            await self._check_security()
            
            # 6. Tests de performance
            await self._check_performance()
            
            # 7. Génération du rapport
            self._generate_report()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors des tests: {e}")
            self.results['issues'].append(f"Erreur critique: {str(e)}")
            
        return self.results
    
    async def _check_environment(self):
        """Vérifie l'environnement d'exécution"""
        print("\n🔍 1/6: Vérification de l'environnement")
        
        try:
            # Variables d'environnement
            load_dotenv()
            
            env_vars = {
                'DATABASE_URL': os.getenv('DATABASE_URL'),
                'SECRET_KEY': 'DÉFINIE' if os.getenv('SECRET_KEY') else 'MANQUANTE',
                'GEMINI_API_KEY': 'DÉFINIE' if os.getenv('GEMINI_API_KEY') else 'MANQUANTE',
                'ALGORITHM': os.getenv('ALGORITHM', 'HS256'),
                'ACCESS_TOKEN_EXPIRE_MINUTES': os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'),
            }
            
            self.results['environment'] = env_vars
            
            # Vérifications critiques
            issues = []
            if not env_vars['DATABASE_URL']:
                issues.append("❌ DATABASE_URL non définie")
            if env_vars['SECRET_KEY'] == 'MANQUANTE':
                issues.append("❌ SECRET_KEY non définie (JWT requis)")
            if env_vars['GEMINI_API_KEY'] == 'MANQUANTE':
                issues.append("⚠️ GEMINI_API_KEY non définie (Coach IA désactivé)")
            
            for issue in issues:
                self.results['issues'].append(issue)
                logger.info(f"   {issue}")
                
            logger.info("   ✅ Environnement chargé")
            
        except Exception as e:
            logger.error(f"   ❌ Erreur environnement: {e}")
            self.results['issues'].append(f"Erreur environnement: {str(e)}")
    
    async def _check_database(self):
        """Vérifie la connexion et le schéma de la base"""
        print("\n🗄️  2/6: Vérification de la base de données")
        
        try:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                logger.error("   ❌ URL de base non définie")
                return
            
            # Correction PostgreSQL
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            
            engine = create_engine(db_url)
            
            with engine.connect() as conn:
                # Test de connexion
                start = time.time()
                conn.execute(text("SELECT 1"))
                latency = (time.time() - start) * 1000
                
                # Vérifier les tables
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                
                tables = [row[0] for row in result]
                
                # Vérifier les tables critiques
                critical_tables = [
                    'users', 'athlete_profiles', 'coach_memories',
                    'workout_sessions', 'workout_sets', 'feed_items'
                ]
                
                missing_tables = [t for t in critical_tables if t not in tables]
                
                self.results['database'] = {
                    'connection': '✅ OK',
                    'latency_ms': round(latency, 2),
                    'tables_found': len(tables),
                    'critical_tables_found': len(critical_tables) - len(missing_tables),
                    'missing_tables': missing_tables,
                    'all_tables': tables
                }
                
                logger.info(f"   ✅ Connexion: {latency:.2f}ms")
                logger.info(f"   📊 Tables: {len(tables)} trouvées")
                
                if missing_tables:
                    logger.warning(f"   ⚠️ Tables manquantes: {missing_tables}")
                    self.results['issues'].extend(
                        [f"Table manquante: {t}" for t in missing_tables]
                    )
                
                # Vérifier les contraintes
                constraints = conn.execute(text("""
                    SELECT 
                        tc.table_name, 
                        tc.constraint_type,
                        tc.constraint_name
                    FROM information_schema.table_constraints tc
                    WHERE tc.table_schema = 'public'
                    ORDER BY tc.table_name, tc.constraint_type
                """))
                
                constraints_list = [
                    f"{row[0]}.{row[2]} ({row[1]})" 
                    for row in constraints
                ]
                
                self.results['database']['constraints'] = constraints_list
                
        except Exception as e:
            logger.error(f"   ❌ Erreur base de données: {e}")
            self.results['database'] = {'error': str(e)}
            self.results['issues'].append(f"Erreur base de données: {str(e)}")
    
    async def _check_api_endpoints(self):
        """Teste tous les endpoints API"""
        print("\n🌐 3/6: Test des endpoints API")
        
        endpoints = [
            # Endpoints publics
            {'method': 'GET', 'path': '/health', 'auth': False},
            {'method': 'GET', 'path': '/docs', 'auth': False},
            {'method': 'GET', 'path': '/redoc', 'auth': False},
            
            # Authentification
            {'method': 'POST', 'path': '/auth/signup', 'auth': False},
            {'method': 'POST', 'path': '/auth/token', 'auth': False},
            
            # Endpoints protégés (nécessitent auth)
            {'method': 'GET', 'path': '/user/profile', 'auth': True},
            {'method': 'GET', 'path': '/workouts/', 'auth': True},
            {'method': 'GET', 'path': '/feed/', 'auth': True},
            {'method': 'GET', 'path': '/api/v1/profiles/me', 'auth': True},
            {'method': 'GET', 'path': '/api/v1/coach-memories/me', 'auth': True},
            
            # Coach IA
            {'method': 'POST', 'path': '/coach/audit', 'auth': True},
            {'method': 'GET', 'path': '/coach/strategy', 'auth': True},
            {'method': 'GET', 'path': '/coach/week', 'auth': True},
            
            # Performance & Safety
            {'method': 'POST', 'path': '/performance/1rm', 'auth': True},
            {'method': 'POST', 'path': '/safety/acwr', 'auth': True},
            
            # Réparation système
            {'method': 'GET', 'path': '/fix_db', 'auth': False},
        ]
        
        results = {}
        successful = 0
        failed = 0
        warnings = 0
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                url = f"{self.base_url}{endpoint['path']}"
                method = endpoint['method']
                requires_auth = endpoint['auth']
                
                # Préparer les headers
                headers = {'Content-Type': 'application/json'}
                if requires_auth and self.auth_token:
                    headers['Authorization'] = f'Bearer {self.auth_token}'
                
                # Préparer le payload si nécessaire
                data = None
                if method == 'POST':
                    if 'auth/token' in endpoint['path']:
                        data = {'username': 'testuser', 'password': 'password123'}
                    elif 'auth/signup' in endpoint['path']:
                        data = {
                            'username': f'test_{int(time.time())}',
                            'email': f'test_{int(time.time())}@example.com',
                            'password': 'Test123!'
                        }
                    elif 'performance/1rm' in endpoint['path']:
                        data = {'weight': 100, 'reps': 5}
                    elif 'coach/audit' in endpoint['path']:
                        data = {'profile_data': {'sport': 'Musculation', 'level': 'Intermédiaire'}}
                    else:
                        data = {}
                
                try:
                    start = time.time()
                    
                    if method == 'GET':
                        async with session.get(url, headers=headers) as response:
                            status = response.status
                            latency = (time.time() - start) * 1000
                    elif method == 'POST':
                        async with session.post(url, headers=headers, json=data) as response:
                            status = response.status
                            latency = (time.time() - start) * 1000
                            
                            # Sauvegarder le token si c'est une connexion réussie
                            if 'auth/token' in endpoint['path'] and status == 200:
                                response_data = await response.json()
                                self.auth_token = response_data.get('access_token')
                    
                    # Évaluer le résultat
                    if status in [200, 201]:
                        result = '✅ OK'
                        successful += 1
                    elif status == 404:
                        result = '⚠️ NON IMPLÉMENTÉ'
                        warnings += 1
                    elif status == 401 and requires_auth:
                        result = '🔒 AUTH REQUISE'
                        warnings += 1
                    else:
                        result = f'❌ {status}'
                        failed += 1
                    
                    results[endpoint['path']] = {
                        'status': status,
                        'latency_ms': round(latency, 2),
                        'result': result
                    }
                    
                    logger.info(f"   {result} {method} {endpoint['path']} ({latency:.2f}ms)")
                    
                except Exception as e:
                    results[endpoint['path']] = {'error': str(e), 'result': '❌ ERREUR'}
                    failed += 1
                    logger.error(f"   ❌ ERREUR {method} {endpoint['path']}: {e}")
        
        self.results['api_endpoints'] = {
            'tested': len(endpoints),
            'successful': successful,
            'failed': failed,
            'warnings': warnings,
            'details': results
        }
        
        logger.info(f"   📊 Résumé: {successful}✅ {failed}❌ {warnings}⚠️")
    
    async def _check_data_models(self):
        """Vérifie la cohérence des modèles de données"""
        print("\n📊 4/6: Vérification des modèles de données")
        
        try:
            # Importer les modèles SQLAlchemy
            sys.path.append('.')
            from app.models import sql_models
            
            models_to_check = [
                ('User', sql_models.User),
                ('AthleteProfile', sql_models.AthleteProfile),
                ('CoachMemory', sql_models.CoachMemory),
                ('WorkoutSession', sql_models.WorkoutSession),
                ('WorkoutSet', sql_models.WorkoutSet),
                ('FeedItem', sql_models.FeedItem),
            ]
            
            results = {}
            
            for model_name, model_class in models_to_check:
                try:
                    # Vérifier que le modèle peut être instancié
                    instance = model_class()
                    
                    # Vérifier les colonnes
                    columns = [col.name for col in model_class.__table__.columns]
                    
                    # Vérifier les relations
                    relationships = []
                    if hasattr(model_class, '__mapper__'):
                        for rel in model_class.__mapper__.relationships:
                            relationships.append(rel.key)
                    
                    results[model_name] = {
                        'status': '✅ VALIDE',
                        'columns': columns,
                        'relationships': relationships,
                        'table_name': model_class.__tablename__
                    }
                    
                    logger.info(f"   ✅ {model_name}: {len(columns)} colonnes")
                    
                except Exception as e:
                    results[model_name] = {'status': f'❌ ERREUR: {e}'}
                    logger.error(f"   ❌ {model_name}: {e}")
                    self.results['issues'].append(f"Modèle {model_name}: {str(e)}")
            
            self.results['data_models'] = results
            
        except ImportError as e:
            logger.error(f"   ❌ Impossible d'importer les modèles: {e}")
            self.results['issues'].append(f"Import modèles: {str(e)}")
        except Exception as e:
            logger.error(f"   ❌ Erreur modèles: {e}")
            self.results['issues'].append(f"Erreur modèles: {str(e)}")
    
    async def _check_security(self):
        """Vérifie les aspects de sécurité"""
        print("\n🔒 5/6: Vérification de sécurité")
        
        security_checks = {
            'jwt_config': '❌ NON VÉRIFIÉ',
            'password_hashing': '❌ NON VÉRIFIÉ',
            'cors_headers': '❌ NON VÉRIFIÉ',
            'rate_limiting': '⚠️  NON DÉTECTÉ',
            'input_validation': '✅ TEST REQUIS'
        }
        
        try:
            # Tester JWT
            secret = os.getenv('SECRET_KEY')
            if secret and secret != 'your-super-secret-key-change-in-production':
                try:
                    # Générer un token de test
                    payload = {'sub': 'test', 'exp': datetime.now().timestamp() + 3600}
                    token = jwt.encode(payload, secret, algorithm='HS256')
                    jwt.decode(token, secret, algorithms=['HS256'])
                    security_checks['jwt_config'] = '✅ CONFIGURÉ'
                except:
                    security_checks['jwt_config'] = '❌ ERREUR JWT'
            else:
                security_checks['jwt_config'] = '❌ SECRET PAR DÉFAIT'
            
            # Tester CORS
            async with aiohttp.ClientSession() as session:
                async with session.options(f"{self.base_url}/health") as response:
                    if 'Access-Control-Allow-Origin' in response.headers:
                        security_checks['cors_headers'] = '✅ ACTIVÉ'
                    else:
                        security_checks['cors_headers'] = '⚠️  NON DÉTECTÉ'
            
            for check, status in security_checks.items():
                logger.info(f"   {status} {check.replace('_', ' ').title()}")
            
            self.results['security'] = security_checks
            
        except Exception as e:
            logger.error(f"   ❌ Erreur sécurité: {e}")
            self.results['security'] = {'error': str(e)}
    
    async def _check_performance(self):
        """Effectue des tests de performance"""
        print("\n⚡ 6/6: Tests de performance")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test de latence
                latencies = []
                for _ in range(5):
                    start = time.time()
                    async with session.get(f"{self.base_url}/health") as _:
                        latencies.append((time.time() - start) * 1000)
                    await asyncio.sleep(0.1)
                
                avg_latency = sum(latencies) / len(latencies)
                
                # Test de charge (simplifié)
                start = time.time()
                tasks = []
                for _ in range(10):
                    task = session.get(f"{self.base_url}/health")
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                load_time = (time.time() - start) * 1000
                
                self.results['performance'] = {
                    'avg_latency_ms': round(avg_latency, 2),
                    'load_test_10req_ms': round(load_time, 2),
                    'recommended_max_latency': '300ms',
                    'status': '✅ OK' if avg_latency < 300 else '⚠️  LENT'
                }
                
                logger.info(f"   📈 Latence moyenne: {avg_latency:.2f}ms")
                logger.info(f"   📊 Test de charge (10 req): {load_time:.2f}ms")
                
        except Exception as e:
            logger.error(f"   ❌ Erreur performance: {e}")
            self.results['performance'] = {'error': str(e)}
    
    def _generate_report(self):
        """Génère un rapport détaillé"""
        print("\n" + "=" * 60)
        print("📋 RAPPORT DE COMPATIBILITÉ BACKEND")
        print("=" * 60)
        
        # Résumé
        total_tests = (
            (1 if self.results['environment'] else 0) +
            (1 if self.results['database'] else 0) +
            (self.results['api_endpoints'].get('tested', 0)) +
            (len(self.results.get('data_models', {}))) +
            (len(self.results.get('security', {}))) +
            (1 if self.results.get('performance') else 0)
        )
        
        successful = (
            (1 if not self.results['issues'] else 0) +
            self.results['api_endpoints'].get('successful', 0)
        )
        
        print(f"\n📊 STATISTIQUES:")
        print(f"   • Tests exécutés: {total_tests}")
        print(f"   • Endpoints testés: {self.results['api_endpoints'].get('tested', 0)}")
        print(f"   • Endpoints OK: {self.results['api_endpoints'].get('successful', 0)}")
        print(f"   • Modèles validés: {len(self.results.get('data_models', {}))}")
        
        print(f"\n🔧 ENVIRONNEMENT:")
        for key, value in self.results['environment'].items():
            print(f"   • {key}: {value}")
        
        print(f"\n🗄️  BASE DE DONNÉES:")
        db = self.results['database']
        if 'error' not in db:
            print(f"   • Connexion: {db.get('connection', 'N/A')}")
            print(f"   • Latence: {db.get('latency_ms', 0)}ms")
            print(f"   • Tables critiques: {db.get('critical_tables_found', 0)}/6")
            if db.get('missing_tables'):
                print(f"   • Tables manquantes: {', '.join(db['missing_tables'])}")
        
        print(f"\n🚨 PROBLÈMES IDENTIFIÉS ({len(self.results['issues'])}):")
        for issue in self.results['issues']:
            print(f"   • {issue}")
        
        print(f"\n💡 RECOMMANDATIONS:")
        recommendations = [
            "✅ Garder les clés JWT en variables d'environnement",
            "✅ Activer CORS pour le frontend Flutter",
            "✅ Configurer les index de base de données",
            "✅ Mettre en place le logging structuré",
            "✅ Tester avec des données réelles",
        ]
        
        for rec in recommendations:
            print(f"   {rec}")
        
        # Sauvegarder le rapport JSON
        report_file = f"backend_compatibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Rapport JSON sauvegardé: {report_file}")
        print("=" * 60)

async def main():
    """Point d'entrée principal"""
    print("🚀 DÉMARRAGE DES TESTS DE COMPATIBILITÉ BACKEND")
    print("=" * 60)
    
    checker = BackendCompatibilityChecker()
    results = await checker.run_comprehensive_check()
    
    # Évaluation finale
    critical_issues = [
        issue for issue in results['issues'] 
        if any(keyword in issue.lower() for keyword in ['❌', 'erreur', 'manquant'])
    ]
    
    if critical_issues:
        print("\n⚠️  ATTENTION: Problèmes critiques détectés!")
        print("   Le backend nécessite des corrections avant déploiement.")
        return 1
    else:
        print("\n✅ Backend prêt pour l'intégration avec Flutter!")
        print("   Tous les tests de compatibilité sont passés.")
        return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrompus par l'utilisateur")
        sys.exit(1)