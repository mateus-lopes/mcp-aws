from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.aws_token import AWSToken
from app.models.user import User
from app.services import s3_service

router = APIRouter(prefix="/s3", tags=["S3"])


def _get_token(token_id: str, db: Session, user: User) -> AWSToken:
    token = db.query(AWSToken).filter(AWSToken.id == token_id, AWSToken.user_id == user.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token AWS não encontrado")
    return token


class CreateBucketRequest(BaseModel):
    token_id: str
    bucket_name: str


class BucketActionRequest(BaseModel):
    token_id: str
    bucket_name: str


class PutObjectRequest(BaseModel):
    token_id: str
    bucket_name: str
    key: str
    content: str
    content_type: str = "text/plain"


class DeleteObjectRequest(BaseModel):
    token_id: str
    bucket_name: str
    key: str


@router.get("/buckets", summary="Listar buckets S3")
def list_buckets(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista todos os buckets S3 da conta AWS."""
    token = _get_token(token_id, db, current_user)
    return s3_service.list_buckets(token)


@router.post("/buckets", status_code=201, summary="Criar bucket S3")
def create_bucket(body: CreateBucketRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria um novo bucket S3."""
    token = _get_token(body.token_id, db, current_user)
    return s3_service.create_bucket(token, body.bucket_name)


@router.delete("/buckets", summary="Remover bucket S3")
def delete_bucket(body: BucketActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove um bucket S3 vazio."""
    token = _get_token(body.token_id, db, current_user)
    s3_service.delete_bucket(token, body.bucket_name)
    return {"deleted": body.bucket_name}


@router.get("/buckets/objects", summary="Listar objetos de um bucket")
def list_objects(token_id: str, bucket_name: str, prefix: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista objetos dentro de um bucket, com prefixo opcional."""
    token = _get_token(token_id, db, current_user)
    return s3_service.list_objects(token, bucket_name, prefix)


@router.put("/buckets/objects", summary="Fazer upload de objeto")
def put_object(body: PutObjectRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Cria ou substitui um objeto no bucket."""
    token = _get_token(body.token_id, db, current_user)
    return s3_service.put_object(token, body.bucket_name, body.key, body.content, body.content_type)


@router.delete("/buckets/objects", summary="Remover objeto do bucket")
def delete_object(body: DeleteObjectRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove um objeto de um bucket S3."""
    token = _get_token(body.token_id, db, current_user)
    s3_service.delete_object(token, body.bucket_name, body.key)
    return {"deleted": body.key}
