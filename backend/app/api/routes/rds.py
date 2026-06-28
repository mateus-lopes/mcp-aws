from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.aws_token import AWSToken
from app.models.user import User
from app.services import rds_service

router = APIRouter(prefix="/rds", tags=["RDS"])


def _get_token(token_id: str, db: Session, user: User) -> AWSToken:
    token = db.query(AWSToken).filter(AWSToken.id == token_id, AWSToken.user_id == user.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token AWS não encontrado")
    return token


class CreateInstanceRequest(BaseModel):
    token_id: str
    db_instance_id: str
    engine: str = "mysql"
    instance_class: str = "db.t3.micro"
    master_username: str
    master_password: str
    storage_gb: int = 20


class InstanceActionRequest(BaseModel):
    token_id: str
    db_instance_id: str


class DeleteInstanceRequest(BaseModel):
    token_id: str
    db_instance_id: str
    skip_final_snapshot: bool = True


class CreateSnapshotRequest(BaseModel):
    token_id: str
    db_instance_id: str
    snapshot_id: str


@router.get("/instances", summary="Listar instâncias RDS")
def list_instances(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista todas as instâncias RDS da conta AWS."""
    token = _get_token(token_id, db, current_user)
    return rds_service.list_instances(token)


@router.post("/instances", status_code=201, summary="Criar instância RDS")
def create_instance(body: CreateInstanceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria uma nova instância RDS."""
    token = _get_token(body.token_id, db, current_user)
    return rds_service.create_instance(
        token, body.db_instance_id, body.engine,
        body.instance_class, body.master_username,
        body.master_password, body.storage_gb,
    )


@router.post("/instances/stop", summary="Parar instância RDS")
def stop_instance(body: InstanceActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Para uma instância RDS (disponível apenas para instâncias Single-AZ)."""
    token = _get_token(body.token_id, db, current_user)
    return rds_service.stop_instance(token, body.db_instance_id)


@router.post("/instances/start", summary="Iniciar instância RDS")
def start_instance(body: InstanceActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Inicia uma instância RDS parada."""
    token = _get_token(body.token_id, db, current_user)
    return rds_service.start_instance(token, body.db_instance_id)


@router.delete("/instances", summary="Remover instância RDS")
def delete_instance(body: DeleteInstanceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove uma instância RDS permanentemente."""
    token = _get_token(body.token_id, db, current_user)
    return rds_service.delete_instance(token, body.db_instance_id, body.skip_final_snapshot)


@router.get("/snapshots", summary="Listar snapshots RDS")
def list_snapshots(token_id: str, db_instance_id: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista snapshots RDS, opcionalmente filtrados por instância."""
    token = _get_token(token_id, db, current_user)
    return rds_service.list_snapshots(token, db_instance_id)


@router.post("/snapshots", status_code=201, summary="Criar snapshot RDS")
def create_snapshot(body: CreateSnapshotRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria um snapshot manual de uma instância RDS."""
    token = _get_token(body.token_id, db, current_user)
    return rds_service.create_snapshot(token, body.db_instance_id, body.snapshot_id)
