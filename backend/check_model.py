from app.models.sql_models import User
from sqlalchemy import inspect

print("📋 Colonnes définies dans le modèle User:")
for column in User.__table__.columns:
    print(f"  • {column.name} ({column.type})")
