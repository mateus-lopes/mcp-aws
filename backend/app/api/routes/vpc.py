from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.aws_token import AWSToken
from app.models.user import User
from app.services import vpc_service
from fastapi import HTTPException

router = APIRouter(prefix="/vpc", tags=["VPC"])


def _get_token(token_id: str, db: Session, user: User) -> AWSToken:
    token = db.query(AWSToken).filter(AWSToken.id == token_id, AWSToken.user_id == user.id).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token AWS não encontrado")
    return token


@router.get("/vpcs", summary="Listar VPCs")
def list_vpcs(token_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista todas as VPCs da conta AWS."""
    token = _get_token(token_id, db, current_user)
    return vpc_service.list_vpcs(token)


@router.get("/subnets", summary="Listar subnets")
def list_subnets(token_id: str, vpc_id: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista subnets, opcionalmente filtradas por VPC."""
    token = _get_token(token_id, db, current_user)
    return vpc_service.list_subnets(token, vpc_id)


@router.get("/security-groups", summary="Listar security groups")
def list_security_groups(token_id: str, vpc_id: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista security groups, opcionalmente filtrados por VPC."""
    token = _get_token(token_id, db, current_user)
    return vpc_service.list_security_groups(token, vpc_id)


@router.get("/internet-gateways", summary="Listar internet gateways")
def list_internet_gateways(token_id: str, vpc_id: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista internet gateways, opcionalmente filtrados por VPC."""
    token = _get_token(token_id, db, current_user)
    return vpc_service.list_internet_gateways(token, vpc_id)


@router.get("/route-tables", summary="Listar route tables")
def list_route_tables(token_id: str, vpc_id: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lista route tables, opcionalmente filtradas por VPC."""
    token = _get_token(token_id, db, current_user)
    return vpc_service.list_route_tables(token, vpc_id)
