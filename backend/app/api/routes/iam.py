from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.aws_token import AWSToken
from app.models.user import User
from app.services import iam_service

router = APIRouter(prefix="/iam", tags=["IAM"])


def _get_token(token_id: str, db: Session, user: User) -> AWSToken:
    token = db.query(AWSToken).filter(AWSToken.id == token_id, AWSToken.user_id == user.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token AWS não encontrado")
    return token


class AccessKeyRequest(BaseModel):
    token_id: str
    username: str


class DeleteAccessKeyRequest(BaseModel):
    token_id: str
    username: str
    access_key_id: str


@router.get("/whoami", summary="Identificar credencial atual")
def whoami(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna a identidade associada às credenciais AWS (account ID, ARN)."""
    token = _get_token(token_id, db, current_user)
    return iam_service.whoami(token)


@router.get("/users", summary="Listar usuários IAM")
def list_users(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista todos os usuários IAM da conta."""
    token = _get_token(token_id, db, current_user)
    return iam_service.list_users(token)


@router.get("/roles", summary="Listar roles IAM")
def list_roles(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista todas as roles IAM da conta."""
    token = _get_token(token_id, db, current_user)
    return iam_service.list_roles(token)


@router.get("/groups", summary="Listar grupos IAM")
def list_groups(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista todos os grupos IAM da conta."""
    token = _get_token(token_id, db, current_user)
    return iam_service.list_groups(token)


@router.get("/policies", summary="Listar políticas IAM")
def list_policies(token_id: str, scope: str = "Local", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista políticas IAM. scope: Local (criadas na conta) ou AWS (gerenciadas pela AWS)."""
    token = _get_token(token_id, db, current_user)
    return iam_service.list_policies(token, scope)


@router.get("/access-keys", summary="Listar access keys de um usuário")
def list_access_keys(token_id: str, username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista as access keys de um usuário IAM."""
    token = _get_token(token_id, db, current_user)
    return iam_service.list_access_keys(token, username)


@router.post("/access-keys", status_code=201, summary="Criar access key para um usuário")
def create_access_key(body: AccessKeyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria uma nova access key. Retorna secret_access_key — guarde agora, não é recuperável depois."""
    token = _get_token(body.token_id, db, current_user)
    return iam_service.create_access_key(token, body.username)


@router.delete("/access-keys", summary="Deletar access key de um usuário")
def delete_access_key(body: DeleteAccessKeyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove permanentemente uma access key de um usuário IAM."""
    token = _get_token(body.token_id, db, current_user)
    return iam_service.delete_access_key(token, body.username, body.access_key_id)
