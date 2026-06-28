from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.aws_token import AWSToken
from app.models.user import User
from app.services import alb_service

router = APIRouter(prefix="/alb", tags=["ALB"])


def _get_token(token_id: str, db: Session, user: User) -> AWSToken:
    token = db.query(AWSToken).filter(AWSToken.id == token_id, AWSToken.user_id == user.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token AWS não encontrado")
    return token


class RegisterTargetRequest(BaseModel):
    token_id: str
    target_group_arn: str
    target_id: str
    port: int | None = None


class DeregisterTargetRequest(BaseModel):
    token_id: str
    target_group_arn: str
    target_id: str


@router.get("/load-balancers", summary="Listar load balancers")
def list_load_balancers(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista todos os Application/Network Load Balancers da conta AWS."""
    token = _get_token(token_id, db, current_user)
    return alb_service.list_load_balancers(token)


@router.get("/listeners", summary="Listar listeners de um load balancer")
def list_listeners(token_id: str, load_balancer_arn: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista os listeners de um load balancer específico."""
    token = _get_token(token_id, db, current_user)
    return alb_service.list_listeners(token, load_balancer_arn)


@router.get("/target-groups", summary="Listar target groups")
def list_target_groups(token_id: str, load_balancer_arn: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista target groups, opcionalmente filtrados por load balancer."""
    token = _get_token(token_id, db, current_user)
    return alb_service.list_target_groups(token, load_balancer_arn)


@router.get("/target-health", summary="Verificar saúde dos targets")
def describe_target_health(token_id: str, target_group_arn: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retorna o estado de saúde de todos os targets em um target group."""
    token = _get_token(token_id, db, current_user)
    return alb_service.describe_target_health(token, target_group_arn)


@router.post("/targets/register", status_code=201, summary="Registrar target em um target group")
def register_target(body: RegisterTargetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Registra uma instância ou IP em um target group."""
    token = _get_token(body.token_id, db, current_user)
    return alb_service.register_target(token, body.target_group_arn, body.target_id, body.port)


@router.delete("/targets/deregister", summary="Remover target de um target group")
def deregister_target(body: DeregisterTargetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove uma instância ou IP de um target group."""
    token = _get_token(body.token_id, db, current_user)
    return alb_service.deregister_target(token, body.target_group_arn, body.target_id)
