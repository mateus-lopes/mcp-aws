# MCP AWS — Guia de Manutenção

API FastAPI para gerenciar recursos AWS via interface web e GPT Actions. Usuários cadastram credenciais AWS e controlam recursos — EC2, S3, RDS, VPC, ALB e IAM — pelo dashboard ou diretamente pela API.

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
        │   ├── ec2.py            # /api/ec2 — instâncias EC2
        │   ├── s3.py             # /api/s3 — buckets e objetos
        │   ├── rds.py            # /api/rds — instâncias e snapshots
        │   ├── vpc.py            # /api/vpc — VPCs, subnets, SGs, IGWs, route tables
        │   ├── alb.py            # /api/alb — load balancers, listeners, target groups
        │   └── iam.py            # /api/iam — usuários, roles, grupos, políticas, access keys
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
            ├── aws_service.py    # boto3 EC2: list/create/start/stop/terminate
            ├── s3_service.py     # boto3 S3: buckets e objetos
            ├── rds_service.py    # boto3 RDS: instâncias e snapshots
            ├── vpc_service.py    # boto3 EC2 (VPC APIs): VPCs, subnets, SGs, IGWs, route tables
            ├── alb_service.py    # boto3 elbv2: LBs, listeners, target groups, health
            └── iam_service.py    # boto3 IAM + STS: usuários, roles, grupos, políticas, access keys
```

---

## Endpoints da API

Todas as rotas autenticadas exigem `Authorization: Bearer <token>` no header.

### Autenticação e tokens

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/api/auth/register` | Não | Cadastrar usuário |
| POST | `/api/auth/login` | Não | Login — retorna JWT |
| GET | `/api/auth/me` | Sim | Dados do usuário logado |
| GET | `/api/tokens/` | Sim | Listar tokens AWS do usuário |
| POST | `/api/tokens/` | Sim | Cadastrar token AWS |
| PUT | `/api/tokens/{id}` | Sim | Atualizar token AWS |
| DELETE | `/api/tokens/{id}` | Sim | Remover token AWS |

### EC2

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/ec2/instances` | Sim | Listar instâncias EC2 |
| POST | `/api/ec2/instances` | Sim | Criar instância EC2 |
| POST | `/api/ec2/instances/start` | Sim | Iniciar instância |
| POST | `/api/ec2/instances/stop` | Sim | Parar instância |
| DELETE | `/api/ec2/instances` | Sim | Terminar instância (permanente) |

### S3

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/s3/buckets` | Sim | Listar buckets |
| POST | `/api/s3/buckets` | Sim | Criar bucket |
| DELETE | `/api/s3/buckets` | Sim | Remover bucket vazio |
| GET | `/api/s3/buckets/objects` | Sim | Listar objetos (prefixo opcional) |
| PUT | `/api/s3/buckets/objects` | Sim | Criar ou substituir objeto (texto) |
| DELETE | `/api/s3/buckets/objects` | Sim | Remover objeto |

### RDS

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/rds/instances` | Sim | Listar instâncias |
| POST | `/api/rds/instances` | Sim | Criar instância |
| POST | `/api/rds/instances/start` | Sim | Iniciar instância parada |
| POST | `/api/rds/instances/stop` | Sim | Parar instância (Single-AZ) |
| DELETE | `/api/rds/instances` | Sim | Remover instância |
| GET | `/api/rds/snapshots` | Sim | Listar snapshots |
| POST | `/api/rds/snapshots` | Sim | Criar snapshot manual |

### VPC (somente leitura)

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/vpc/vpcs` | Sim | Listar VPCs |
| GET | `/api/vpc/subnets` | Sim | Listar subnets (filtro por VPC) |
| GET | `/api/vpc/security-groups` | Sim | Listar security groups (filtro por VPC) |
| GET | `/api/vpc/internet-gateways` | Sim | Listar internet gateways (filtro por VPC) |
| GET | `/api/vpc/route-tables` | Sim | Listar route tables (filtro por VPC) |

### ALB / NLB

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/alb/load-balancers` | Sim | Listar load balancers |
| GET | `/api/alb/listeners` | Sim | Listar listeners de um LB |
| GET | `/api/alb/target-groups` | Sim | Listar target groups |
| GET | `/api/alb/target-health` | Sim | Saúde dos targets de um target group |
| POST | `/api/alb/targets/register` | Sim | Registrar target em um target group |
| DELETE | `/api/alb/targets/deregister` | Sim | Remover target de um target group |

### IAM

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/api/iam/whoami` | Sim | Identidade da credencial (via STS) |
| GET | `/api/iam/users` | Sim | Listar usuários IAM |
| GET | `/api/iam/roles` | Sim | Listar roles IAM |
| GET | `/api/iam/groups` | Sim | Listar grupos IAM |
| GET | `/api/iam/policies` | Sim | Listar políticas (scope: `Local` ou `AWS`) |
| GET | `/api/iam/access-keys` | Sim | Listar access keys de um usuário |
| POST | `/api/iam/access-keys` | Sim | Criar access key (retorna secret — guardar agora) |
| DELETE | `/api/iam/access-keys` | Sim | Deletar access key |

### Sistema

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/health` | Não | Status da API |

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
| session_token | TEXT | Nullable — obrigatório para chaves `ASIA*` (AWS Academy / STS) |
| region | VARCHAR | Padrão: `us-east-1` |
| created_at | TIMESTAMP | server_default |

> **Atenção:** a coluna `session_token` foi adicionada via `ALTER TABLE` após a criação inicial da tabela. Em ambientes novos, o `create_all` já a cria automaticamente. Em bancos existentes sem a coluna, executar:
> ```sql
> ALTER TABLE aws_tokens ADD COLUMN IF NOT EXISTS session_token TEXT;
> ```

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

### Credenciais temporárias AWS (STS / AWS Academy)

Chaves que começam com `ASIA*` são temporárias e exigem um `session_token` além de `access_key_id` e `secret_access_key`. O campo é opcional no modelo — se omitido, o boto3 tenta autenticar sem ele (funciona para chaves `AKIA*` permanentes).

Todos os clientes boto3 (EC2, S3, RDS, elbv2, IAM, STS) repassam o `session_token` da mesma forma:

```python
boto3.client("ec2",  # ou "s3", "rds", "elbv2", "iam", "sts"
    aws_access_key_id=token.access_key_id,
    aws_secret_access_key=token.secret_access_key,
    aws_session_token=token.session_token,   # None quando não informado
    region_name=token.region,
)
```

O dashboard exibe um badge amarelo **temp** ao lado do label quando o token possui `session_token`, indicando que são credenciais temporárias que expiram.

### Peculiaridades por serviço

**S3 — `create_bucket` e `us-east-1`**  
A API S3 rejeita `CreateBucketConfiguration` quando a região é `us-east-1` (é a única região que não aceita o parâmetro `LocationConstraint`). O `s3_service.create_bucket` já trata isso omitindo o parâmetro nesse caso.

**RDS — stop/start**  
`stop_db_instance` só funciona em instâncias Single-AZ. Multi-AZ retorna erro da AWS. O `skip_final_snapshot` no delete é `true` por padrão — passar `false` dispara um snapshot automático com sufixo `-final`.

**ALB — ARNs em query params**  
ARNs AWS contêm `//` e `:` — não podem ir em path params (quebram o roteamento). Todos os endpoints que recebem ARN os leem via query string ou body.

**IAM — `whoami` usa STS, não IAM**  
`GET /api/iam/whoami` chama `sts.get_caller_identity()`, não a API IAM. É o único jeito confiável de identificar a conta com credenciais temporárias.

**IAM — secret retornado uma única vez**  
`POST /api/iam/access-keys` retorna `secret_access_key` na resposta. A AWS não permite recuperar esse valor depois — se perdido, deletar e criar uma nova chave.

### Pontos de atenção para produção

- `secret_access_key` e `session_token` AWS são armazenados em **plain text** no banco — considerar criptografia em repouso (ex: AWS KMS ou Fernet)
- CORS está aberto para qualquer origem (`allow_origins=["*"]`) — restringir ao domínio real
- `SECRET_KEY` do JWT precisa ser uma string longa e aleatória (nunca o valor do `.env.example`)
- Credenciais `ASIA*` do AWS Academy expiram periodicamente — ao receber `InvalidClientTokenId` ou `ExpiredTokenException`, cadastrar um novo token com as credenciais atualizadas

---

## Frontend

Dois arquivos HTML puros, sem bundler ou framework. O FastAPI serve eles diretamente via `FileResponse`.

- **`index.html`**: toggle entre login e cadastro. Após login, salva o JWT em `localStorage` e redireciona para `/dashboard`.
- **`dashboard.html`**: lista tokens AWS cadastrados, permite adicionar e remover. Formulário inclui campo `session_token` (textarea, pois o valor é longo — 500+ caracteres). Tokens com session token recebem badge **temp** na listagem. Usa função `req()` helper que injeta o Bearer token automaticamente em todas as chamadas e faz logout automático em 401.

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

**"InvalidClientTokenId" ou "ExpiredTokenException" ao listar/criar EC2**
→ Credenciais temporárias (`ASIA*`) do AWS Academy expiraram. Obter novas credenciais no painel do Academy e atualizar o `session_token` do token cadastrado via `PUT /api/tokens/{id}` ou diretamente no banco:
```sql
UPDATE aws_tokens SET access_key_id = '...', secret_access_key = '...', session_token = '...' WHERE id = '...';
```

**"cannot be stopped as it has never reached the 'running' state"**
→ Comportamento esperado da AWS — instância ainda em `pending`. Aguardar o estado `running` antes de tentar parar.

**"BucketAlreadyExists" ou "BucketAlreadyOwnedByYou" ao criar bucket S3**
→ Nome de bucket é global na AWS. Escolher um nome único. Se o bucket já pertence à sua conta, o erro é `BucketAlreadyOwnedByYou` — não precisa criar de novo.

**"InvalidParameterCombination" ao parar instância RDS**
→ `stop_db_instance` não é suportado em instâncias Multi-AZ. Apenas Single-AZ pode ser parada temporariamente.

**"AccessDenied" em endpoints IAM**
→ Credenciais do AWS Academy geralmente têm permissões restritas para IAM. `whoami` (STS) costuma funcionar, mas `list_users` e `create_access_key` podem retornar `AccessDenied` dependendo da política da conta Academy.
