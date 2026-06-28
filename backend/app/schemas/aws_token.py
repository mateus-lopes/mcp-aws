from pydantic import BaseModel


class AWSTokenCreate(BaseModel):
    label: str
    access_key_id: str
    secret_access_key: str
    session_token: str | None = None
    region: str = "us-east-1"


class AWSTokenUpdate(BaseModel):
    label: str | None = None
    access_key_id: str | None = None
    secret_access_key: str | None = None
    session_token: str | None = None
    region: str | None = None


class AWSTokenOut(BaseModel):
    id: str
    label: str
    access_key_id: str
    region: str
    session_token: str | None = None

    class Config:
        from_attributes = True
