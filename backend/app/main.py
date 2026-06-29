from copy import deepcopy
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth, tokens, ec2, s3, rds, vpc, alb, iam, oauth
import app.models.user  # noqa: F401
import app.models.aws_token  # noqa: F401
import app.models.oauth  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MCP AWS",
    description="API para gerenciar recursos AWS via GPT Actions. Cadastre seu token AWS e use o ChatGPT para controlar instâncias EC2.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(tokens.router, prefix="/api")
app.include_router(ec2.router, prefix="/api")
app.include_router(s3.router, prefix="/api")
app.include_router(rds.router, prefix="/api")
app.include_router(vpc.router, prefix="/api")
app.include_router(alb.router, prefix="/api")
app.include_router(iam.router, prefix="/api")
app.include_router(oauth.router)

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

if FRONTEND_DIR.exists():
    STATIC_DIR = FRONTEND_DIR / "static"
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/dashboard", include_in_schema=False)
    def serve_dashboard():
        return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

    @app.get("/privacy", include_in_schema=False)
    def serve_privacy():
        return FileResponse(str(FRONTEND_DIR / "privacy.html"))


@app.get("/health", tags=["Sistema"], summary="Verificar status da API")
def health():
    return {"status": "ok"}


GPT_ACTION_OPERATIONS = {
    ("get", "/api/tokens/"),
    ("get", "/api/ec2/instances"),
    ("get", "/api/ec2/images"),
    ("post", "/api/ec2/instances"),
    ("post", "/api/ec2/instances/start"),
    ("post", "/api/ec2/instances/stop"),
    ("delete", "/api/ec2/instances"),
    ("get", "/api/s3/buckets"),
    ("post", "/api/s3/buckets"),
    ("delete", "/api/s3/buckets"),
    ("get", "/api/s3/buckets/objects"),
    ("put", "/api/s3/buckets/objects"),
    ("delete", "/api/s3/buckets/objects"),
    ("get", "/api/rds/instances"),
    ("post", "/api/rds/instances"),
    ("post", "/api/rds/instances/start"),
    ("post", "/api/rds/instances/stop"),
    ("delete", "/api/rds/instances"),
    ("get", "/api/rds/snapshots"),
    ("post", "/api/rds/snapshots"),
    ("get", "/api/vpc/vpcs"),
    ("get", "/api/vpc/subnets"),
    ("get", "/api/vpc/security-groups"),
    ("get", "/api/vpc/internet-gateways"),
    ("get", "/api/vpc/route-tables"),
    ("get", "/api/iam/whoami"),
    ("get", "/api/iam/users"),
    ("get", "/api/iam/roles"),
    ("get", "/api/iam/groups"),
    ("get", "/api/iam/policies"),
}


@app.get("/openapi-gpt.json", include_in_schema=False)
def openapi_gpt(request: Request):
    schema = deepcopy(app.openapi())
    schema["servers"] = [{"url": settings.PUBLIC_BASE_URL.rstrip("/") or str(request.base_url).rstrip("/")}]
    schema["paths"] = {
        path: {
            method: operation
            for method, operation in path_item.items()
            if (method, path) in GPT_ACTION_OPERATIONS
        }
        for path, path_item in schema["paths"].items()
    }
    schema["paths"] = {path: path_item for path, path_item in schema["paths"].items() if path_item}
    return schema
