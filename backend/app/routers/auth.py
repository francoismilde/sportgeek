from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import sql_models, schemas
from app.core import security

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Inscription d'un nouvel utilisateur.
    Initialise immédiatement le 'sac de sport' (profile_data) pour éviter les erreurs 500.
    """
    # 1. Vérifier si le pseudo existe déjà
    db_user = db.query(sql_models.User).filter(sql_models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Ce pseudo est déjà pris.")
    
    # 2. Vérifier si l'email existe déjà (si fourni)
    if user.email:
        db_email = db.query(sql_models.User).filter(sql_models.User.email == user.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
    
    # 3. Hasher le mot de passe
    hashed_pwd = security.get_password_hash(user.password)
    
    # 4. Préparer le Casier (Profile Data JSON)
    # On initialise une structure propre pour que le reste de l'app ne plante pas sur du NULL.
    initial_profile_data = {
        "basic_info": {
            "pseudo": user.username,
            "email": user.email,
            "created_at": datetime.utcnow().isoformat()
        },
        "onboarding_completed": False,
        "physical_metrics": {},
        "goals": {},
        "stats": {
            "level": 1,
            "xp": 0
        }
    }
    
    # 5. Créer l'utilisateur
    new_user = sql_models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd,
        profile_data=initial_profile_data # <--- C'est ici que la magie opère
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        # On log l'erreur pour le debug serveur, mais on renvoie une erreur propre au client
        print(f"🔥 ERREUR CRITIQUE SIGNUP DB : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la création du compte. Vérifiez les données."
        )

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login : Vérifie pseudo/mot de passe et renvoie un Token JWT."""
    user = db.query(sql_models.User).filter(sql_models.User.username == form_data.username).first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pseudo ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}