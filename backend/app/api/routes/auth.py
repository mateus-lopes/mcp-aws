import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, get_current_user
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=UserOut, status_code=201, summary="Registrar novo usuário")
def register(body: UserRegister, db: Session = Depends(get_db)):
    try:
        if db.query(User).filter(User.email == body.email).first():
            raise HTTPException(status_code=400, detail="E-mail já cadastrado")
        user = User(email=body.email, hashed_password=hash_password(body.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except HTTPException:
        raise
    except OperationalError as e:
        db.rollback()
        logger.error("Banco indisponível ao registrar usuário: %s", e)
        raise HTTPException(status_code=503, detail="Banco de dados indisponível. Verifique se o serviço está em execução.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Erro de banco ao registrar usuário: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {e}")
    except Exception as e:
        db.rollback()
        logger.exception("Erro inesperado ao registrar usuário")
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


@router.post("/login", response_model=TokenResponse, summary="Login e obtenção do token JWT")
def login(body: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == body.email).first()
        if not user or not verify_password(body.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        return {"access_token": create_access_token(user.id)}
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error("Banco indisponível ao fazer login: %s", e)
        raise HTTPException(status_code=503, detail="Banco de dados indisponível. Verifique se o serviço está em execução.")
    except SQLAlchemyError as e:
        logger.error("Erro de banco ao fazer login: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {e}")
    except Exception as e:
        logger.exception("Erro inesperado ao fazer login")
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


@router.get("/me", response_model=UserOut, summary="Dados do usuário autenticado")
def me(current_user: User = Depends(get_current_user)):
    return current_user
