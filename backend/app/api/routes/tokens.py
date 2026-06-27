from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.aws_token import AWSToken
from app.models.user import User
from app.schemas.aws_token import AWSTokenCreate, AWSTokenUpdate, AWSTokenOut

router = APIRouter(prefix="/tokens", tags=["Tokens AWS"])


@router.get("/", response_model=list[AWSTokenOut], summary="Listar tokens AWS do usuário")
def list_tokens(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(AWSToken).filter(AWSToken.user_id == current_user.id).all()


@router.post("/", response_model=AWSTokenOut, status_code=201, summary="Cadastrar token AWS")
def create_token(body: AWSTokenCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token = AWSToken(**body.model_dump(), user_id=current_user.id)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


@router.put("/{token_id}", response_model=AWSTokenOut, summary="Atualizar token AWS")
def update_token(token_id: str, body: AWSTokenUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token = db.query(AWSToken).filter(AWSToken.id == token_id, AWSToken.user_id == current_user.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token não encontrado")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(token, field, value)
    db.commit()
    db.refresh(token)
    return token


@router.delete("/{token_id}", status_code=204, summary="Remover token AWS")
def delete_token(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token = db.query(AWSToken).filter(AWSToken.id == token_id, AWSToken.user_id == current_user.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token não encontrado")
    db.delete(token)
    db.commit()
