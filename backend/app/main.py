from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.database import engine, Base
from app.api.routes import auth, tokens, ec2, s3, rds, vpc, alb, iam
import app.models.user  # noqa: F401
import app.models.aws_token  # noqa: F401

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


@app.get("/health", tags=["Sistema"], summary="Verificar status da API")
def health():
    return {"status": "ok"}
