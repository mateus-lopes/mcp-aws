# MCP AWS — Guia de Manutenção

API FastAPI para gerenciar recursos AWS (EC2) via interface web e GPT Actions. Usuários cadastram credenciais AWS e controlam instâncias EC2 pelo dashboard ou diretamente pela API.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python + FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Banco | PostgreSQL 16 (Docker) |
| Auth | JWT (python-jose) + bcrypt |
| AWS SDK | boto3 |
| Frontend | HTML + JS vanilla (sem bundler) |

---

## Iniciar o projeto

### 1. Banco de dados (Docker)

```bash
docker compose up -d
```

Postgres sobe na porta **5433** (não 5432 — evita conflito com instâncias locais).

### 2. Backend

```bash
cd backend
.venv\Scripts\activate        # Windows
# ou: source .venv/bin/activate  # Linux/Mac

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Acessar

- Frontend: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Variáveis de ambiente

Arquivo `.env` na raiz do projeto (mesmo nível do `docker-compose.yml`):

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/mcpaws
SECRET_KEY=troque-por-uma-chave-secreta-longa-e-aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

`config.py` resolve o caminho do `.env` de forma absoluta a partir de `__file__`, então funciona independente de onde o uvicorn é chamado.

---

## Estrutura de arquivos

```
ia-aws/
├── .env                          # Variáveis locais (não commitado)
├── .env.example                  # Modelo para novos devs
├── docker-compose.yml            # PostgreSQL local
├── CLAUDE.md                     # Este arquivo
├── frontend/
│   ├── index.html                # Login e cadastro
│   └── dashboard.html            # Gerenciamento de tokens AWS
└── backend/
    ├── requirements.txt
    ├── .venv/                    # Virtualenv (não commitado)
    └── app/
        ├── main.py               # Entrypoint: registra routers, cria tabelas, serve frontend
        ├── api/routes/
        │   ├── auth.py           # /api/auth — register, login, me
        │   ├── tokens.py         # /api/tokens — CRUD de credenciais AWS
        │   └── ec2.py            # /api/ec2 — operações em instâncias EC2
        ├── core/
        │   ├── config.py         # Settings via pydantic-settings
        │   ├── database.py       # Engine SQLAlchemy + get_db()
        │   └── security.py       # hash/verify senha, JWT, get_current_user
        ├── models/
        │   ├── user.py           # Tabela users
        │   └── aws_token.py      # Tabela aws_tokens
        ├── schemas/
        │   ├── user.py           # Pydantic: UserRegister, UserLogin, UserOut, TokenResponse
        │   └── aws_token.py      # Pydantic: AWSTokenCreate, AWSTokenUpdate, AWSTokenOut
        └── services/
            └── aws_service.py    # Funções boto3: list/create/start/stop/terminate EC2
```

---

## Endpoints da API

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/api/auth/register` | Não | Cadastrar usuário |
| POST | `/api/auth/login` | Não | Login — retorna JWT |
| GET | `/api/auth/me` | Sim | Dados do usuário logado |
| GET | `/api/tokens/` | Sim | Listar tokens AWS do usuário |
| POST | `/api/tokens/` | Sim | Cadastrar token AWS |
| PUT | `/api/tokens/{id}` | Sim | Atualizar token AWS |
| DELETE | `/api/tokens/{id}` | Sim | Remover token AWS |
| GET | `/api/ec2/instances?token_id=` | Sim | Listar instâncias EC2 |
| POST | `/api/ec2/instances` | Sim | Criar instância EC2 |
| POST | `/api/ec2/instances/start` | Sim | Iniciar instância |
| POST | `/api/ec2/instances/stop` | Sim | Parar instância |
| DELETE | `/api/ec2/instances` | Sim | Terminar instância (permanente) |
| GET | `/health` | Não | Status da API |

Todas as rotas autenticadas exigem `Authorization: Bearer <token>` no header.

---

## Banco de dados

As tabelas são criadas automaticamente no startup via `Base.metadata.create_all(bind=engine)` em `main.py`. Alembic está instalado mas **não está em uso** — migrations manuais ainda não foram configuradas.

### Tabela `users`

| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID (string) | PK, gerado com `uuid4()` |
| email | VARCHAR | UNIQUE + INDEX |
| hashed_password | VARCHAR | SHA-256 + bcrypt |
| created_at | TIMESTAMP | server_default |

### Tabela `aws_tokens`

| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID (string) | PK |
| user_id | VARCHAR | FK → users.id (CASCADE DELETE) |
| label | VARCHAR | Nome descritivo |
| access_key_id | VARCHAR | Credencial AWS |
| secret_access_key | VARCHAR | Credencial AWS (plain text) |
| region | VARCHAR | Padrão: `us-east-1` |
| created_at | TIMESTAMP | server_default |

---

## Segurança — decisões e cuidados

### Hash de senha (bcrypt + SHA-256)

`bcrypt 4.x` rejeita senhas maiores que 72 bytes com erro explícito. Para contornar sem truncar silenciosamente, a senha passa primeiro por SHA-256:

```python
# security.py
def _encode_password(password: str) -> bytes:
    return hashlib.sha256(password.encode()).hexdigest().encode()
    # hexdigest = sempre 64 chars = 64 bytes → abaixo do limite de 72
```

Toda senha cadastrada ou verificada passa por `_encode_password` antes do bcrypt. **Não remover essa camada** — senhas antigas no banco foram hasheadas com ela.

### JWT

- Algoritmo: HS256
- Payload: `{ sub: user_id, exp: now + ACCESS_TOKEN_EXPIRE_MINUTES }`
- Verificado em todo request autenticado via `get_current_user` (dependency injection)

### Pontos de atenção para produção

- `secret_access_key` AWS é armazenado em **plain text** no banco — considerar criptografia em repouso (ex: AWS KMS ou Fernet)
- CORS está aberto para qualquer origem (`allow_origins=["*"]`) — restringir ao domínio real
- `SECRET_KEY` do JWT precisa ser uma string longa e aleatória (nunca o valor do `.env.example`)

---

## Frontend

Dois arquivos HTML puros, sem bundler ou framework. O FastAPI serve eles diretamente via `FileResponse`.

- **`index.html`**: toggle entre login e cadastro. Após login, salva o JWT em `localStorage` e redireciona para `/dashboard`.
- **`dashboard.html`**: lista tokens AWS cadastrados, permite adicionar e remover. Usa função `req()` helper que injeta o Bearer token automaticamente em todas as chamadas e faz logout automático em 401.

Se for adicionar arquivos estáticos (CSS, JS separados), criar `frontend/static/` — o `main.py` já verifica a existência desse diretório antes de montar.

---

## Instalação do zero

```bash
git clone <repo>
cd ia-aws

# Banco
docker compose up -d

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Configuração
cp .env.example .env
# editar .env com SECRET_KEY real

# Iniciar
uvicorn app.main:app --reload --port 8000
```

---

## Troubleshooting

**"Banco de dados indisponível"**
→ Container parado. Rodar `docker compose up -d` e aguardar o Postgres ficar healthy. Reiniciar o backend em seguida (o `create_all` roda no startup).

**"password cannot be longer than 72 bytes"**
→ Backend rodando com código antigo (sem `_encode_password`). Reiniciar o processo do uvicorn.

**"Token inválido ou expirado"**
→ JWT expirado (padrão: 60 min) ou `SECRET_KEY` diferente entre reinicializações. Fazer login novamente.

**Porta 5433 já em uso**
→ Outro container Postgres rodando. Ver `docker ps -a` e parar o conflitante, ou mudar a porta no `docker-compose.yml` e no `.env`.

**Backend não encontra o `.env`**
→ `config.py` usa path absoluto (`ROOT_DIR = Path(__file__).resolve().parents[3]`). O `.env` deve estar na raiz do repositório, não dentro de `backend/`.
