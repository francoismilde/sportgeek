from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.models import sql_models, schemas

# C'est ici qu'on dit à FastAPI où aller chercher le token si on ne l'a pas
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Cette fonction est un 'Dependency'. 
    Elle sera appelée avant chaque route protégée.
    1. Elle récupère le token.
    2. Elle le décode.
    3. Elle vérifie si l'utilisateur existe en BDD.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Décodage du token
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Recherche de l'utilisateur en BDD
    user = db.query(sql_models.User).filter(sql_models.User.username == username).first()
    if user is None:
        raise credentials_exception
        
    return user