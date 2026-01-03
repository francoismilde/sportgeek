from datetime import timedelta
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
    """Inscription d'un nouvel utilisateur."""
    db_user = db.query(sql_models.User).filter(sql_models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Ce pseudo est déjà pris.")
    
    hashed_pwd = security.get_password_hash(user.password)
    new_user = sql_models.User(username=user.username, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login : Vérifie pseudo/mot de passe et renvoie un Token JWT.
    Note: Utilise un formulaire standard OAuth2 (username/password) au lieu d'un JSON.
    """
    # 1. Chercher l'utilisateur
    user = db.query(sql_models.User).filter(sql_models.User.username == form_data.username).first()
    
    # 2. Vérifier les identifiants
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pseudo ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Créer le token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}