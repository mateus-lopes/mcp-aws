import base64
import html
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_token, verify_password
from app.models.oauth import OAuthAccessToken, OAuthAuthorizationCode
from app.models.user import User

router = APIRouter(prefix="/oauth", tags=["OAuth"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _allowed_redirects() -> set[str]:
    return {
        uri.strip()
        for uri in settings.OAUTH_ALLOWED_REDIRECT_URIS.split(",")
        if uri.strip()
    }


def _is_redirect_uri_allowed(redirect_uri: str) -> bool:
    allowed = _allowed_redirects()
    if allowed:
        return redirect_uri in allowed
    return redirect_uri.startswith("https://chat.openai.com/aip/") or redirect_uri.startswith("https://chatgpt.com/aip/")


def _validate_authorize_request(response_type: str, client_id: str, redirect_uri: str):
    if response_type != "code":
        raise HTTPException(status_code=400, detail="response_type inválido")
    if client_id != settings.OAUTH_CLIENT_ID:
        raise HTTPException(status_code=400, detail="client_id inválido")
    if not _is_redirect_uri_allowed(redirect_uri):
        raise HTTPException(status_code=400, detail="redirect_uri não permitido")


def _error_redirect(redirect_uri: str, state: str | None, error: str, description: str) -> RedirectResponse:
    params = {"error": error, "error_description": description}
    if state:
        params["state"] = state
    return RedirectResponse(f"{redirect_uri}?{urlencode(params)}", status_code=302)


def _authorization_form(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str | None,
    error: str | None = None,
) -> str:
    hidden = {
        "response_type": response_type,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state or "",
    }
    hidden_inputs = "\n".join(
        f'<input type="hidden" name="{html.escape(key)}" value="{html.escape(value)}" />'
        for key, value in hidden.items()
    )
    error_html = f'<div class="msg error">{html.escape(error)}</div>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MCP AWS - Autorizar GPT</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, sans-serif; background: #f4f4f5; display: flex; align-items: center; justify-content: center; min-height: 100vh; }}
    .card {{ background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.1); padding: 2rem; width: 100%; max-width: 420px; }}
    h1 {{ font-size: 1.35rem; margin-bottom: .4rem; color: #111827; }}
    p {{ color: #52525b; font-size: .9rem; line-height: 1.4; margin-bottom: 1.2rem; }}
    label {{ display: block; font-size: .85rem; color: #444; margin-bottom: .25rem; }}
    input {{ width: 100%; padding: .6rem .75rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: .95rem; margin-bottom: 1rem; }}
    input:focus {{ outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.2); }}
    button {{ width: 100%; padding: .72rem; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-size: .95rem; cursor: pointer; }}
    button:hover {{ background: #1d4ed8; }}
    .msg {{ padding: .65rem; border-radius: 6px; font-size: .85rem; margin-bottom: 1rem; }}
    .msg.error {{ background: #fee2e2; color: #b91c1c; }}
  </style>
</head>
<body>
  <main class="card">
    <h1>Autorizar GPT Action</h1>
    <p>Entre com sua conta MCP AWS para permitir que o GPT acesse apenas os recursos AWS cadastrados no seu usuário.</p>
    {error_html}
    <form method="post" action="/oauth/authorize">
      {hidden_inputs}
      <label>E-mail</label>
      <input type="email" name="email" autocomplete="email" required />
      <label>Senha</label>
      <input type="password" name="password" autocomplete="current-password" required />
      <button type="submit">Autorizar</button>
    </form>
  </main>
</body>
</html>"""


def _read_basic_credentials(authorization: str | None) -> tuple[str | None, str | None]:
    if not authorization or not authorization.lower().startswith("basic "):
        return None, None
    try:
        raw = base64.b64decode(authorization.split(" ", 1)[1]).decode()
        client_id, client_secret = raw.split(":", 1)
        return client_id, client_secret
    except Exception:
        return None, None


def _validate_client(client_id: str | None, client_secret: str | None):
    if not settings.OAUTH_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="OAuth client secret não configurado")
    if client_id != settings.OAUTH_CLIENT_ID or client_secret != settings.OAUTH_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cliente OAuth inválido")


@router.get("/authorize", response_class=HTMLResponse, include_in_schema=False)
def authorize_form(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query("aws"),
    state: str | None = Query(None),
):
    _validate_authorize_request(response_type, client_id, redirect_uri)
    return HTMLResponse(_authorization_form(response_type, client_id, redirect_uri, scope, state))


@router.post("/authorize", include_in_schema=False)
def authorize_submit(
    response_type: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form("aws"),
    state: str | None = Form(None),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    _validate_authorize_request(response_type, client_id, redirect_uri)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return HTMLResponse(
            _authorization_form(response_type, client_id, redirect_uri, scope, state, "Credenciais inválidas"),
            status_code=401,
        )

    code = secrets.token_urlsafe(48)
    auth_code = OAuthAuthorizationCode(
        code_hash=hash_token(code),
        user_id=user.id,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        expires_at=_now() + timedelta(minutes=settings.OAUTH_AUTH_CODE_EXPIRE_MINUTES),
    )
    db.add(auth_code)
    db.commit()

    params = {"code": code}
    if state:
        params["state"] = state
    return RedirectResponse(f"{redirect_uri}?{urlencode(params)}", status_code=302)


@router.post("/token", include_in_schema=False)
def token(
    grant_type: str = Form(...),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    client_id: str | None = Form(None),
    client_secret: str | None = Form(None),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    basic_client_id, basic_client_secret = _read_basic_credentials(authorization)
    client_id = basic_client_id or client_id
    client_secret = basic_client_secret or client_secret
    _validate_client(client_id, client_secret)

    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="grant_type inválido")

    auth_code = db.query(OAuthAuthorizationCode).filter(OAuthAuthorizationCode.code_hash == hash_token(code)).first()
    if (
        not auth_code
        or auth_code.used_at is not None
        or auth_code.expires_at <= _now()
        or auth_code.client_id != client_id
        or auth_code.redirect_uri != redirect_uri
    ):
        raise HTTPException(status_code=400, detail="authorization code inválido")

    access_token = secrets.token_urlsafe(48)
    auth_code.used_at = _now()
    db.add(
        OAuthAccessToken(
            token_hash=hash_token(access_token),
            user_id=auth_code.user_id,
            client_id=auth_code.client_id,
            scope=auth_code.scope,
            expires_at=_now() + timedelta(minutes=settings.OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES),
        )
    )
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": auth_code.scope,
    }
