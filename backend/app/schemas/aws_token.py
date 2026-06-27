from pydantic import BaseModel


class AWSTokenCreate(BaseModel):
    label: str
    access_key_id: str
    secret_access_key: str
    region: str = "us-east-1"


class AWSTokenUpdate(BaseModel):
    label: str | None = None
    access_key_id: str | None = None
    secret_access_key: str | None = None
    region: str | None = None


class AWSTokenOut(BaseModel):
    id: str
    label: str
    access_key_id: str
    region: str

    class Config:
        from_attributes = True
