from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.aws_token import AWSToken
from app.models.user import User
from app.services import aws_service

router = APIRouter(prefix="/ec2", tags=["EC2"])


def _get_token(token_id: str, db: Session, user: User) -> AWSToken:
    token = db.query(AWSToken).filter(AWSToken.id == token_id, AWSToken.user_id == user.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token AWS não encontrado")
    return token


class CreateInstanceRequest(BaseModel):
    token_id: str
    name: str
    instance_type: str = "t2.micro"
    ami_id: str


class InstanceActionRequest(BaseModel):
    token_id: str
    instance_id: str


@router.get("/instances", summary="Listar instâncias EC2")
def list_instances(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista todas as instâncias EC2 associadas ao token AWS informado."""
    token = _get_token(token_id, db, current_user)
    return aws_service.list_instances(token)


@router.get("/images", summary="Listar AMIs EC2")
def list_images(
    token_id: str,
    os: str = "amazon-linux-2023",
    architecture: str = "x86_64",
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista AMIs recentes e válidas na região do token AWS informado."""
    token = _get_token(token_id, db, current_user)
    return aws_service.list_images(token, os, architecture, limit)


@router.post("/instances", status_code=201, summary="Criar instância EC2")
def create_instance(body: CreateInstanceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria uma nova instância EC2 com o tipo e AMI especificados."""
    token = _get_token(body.token_id, db, current_user)
    return aws_service.create_instance(token, body.instance_type, body.ami_id, body.name)


@router.post("/instances/stop", summary="Parar instância EC2")
def stop_instance(body: InstanceActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Para (stop) uma instância EC2 pelo ID."""
    token = _get_token(body.token_id, db, current_user)
    return aws_service.stop_instance(token, body.instance_id)


@router.post("/instances/start", summary="Iniciar instância EC2")
def start_instance(body: InstanceActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Inicia (start) uma instância EC2 parada."""
    token = _get_token(body.token_id, db, current_user)
    return aws_service.start_instance(token, body.instance_id)


@router.delete("/instances", summary="Terminar instância EC2")
def terminate_instance(body: InstanceActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Termina (encerra permanentemente) uma instância EC2."""
    token = _get_token(body.token_id, db, current_user)
    return aws_service.terminate_instance(token, body.instance_id)
