import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from app.core.database import Base


class OAuthAuthorizationCode(Base):
    __tablename__ = "oauth_authorization_codes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code_hash = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=False)
    scope = Column(String, nullable=False, default="aws")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OAuthAccessToken(Base):
    __tablename__ = "oauth_access_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token_hash = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(String, nullable=False)
    scope = Column(String, nullable=False, default="aws")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
