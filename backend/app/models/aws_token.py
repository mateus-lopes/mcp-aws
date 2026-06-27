import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from app.core.database import Base


class AWSToken(Base):
    __tablename__ = "aws_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)
    access_key_id = Column(String, nullable=False)
    secret_access_key = Column(String, nullable=False)
    region = Column(String, nullable=False, default="us-east-1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
