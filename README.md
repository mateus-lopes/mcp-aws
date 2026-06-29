# mcp-aws

API para gerenciar recursos AWS via interface web e GPT Actions (Custom GPT do ChatGPT).  
Cada usuário cadastra suas credenciais AWS e controla recursos — EC2, S3, RDS, VPC, ALB e IAM — pelo dashboard ou diretamente pela API.

---

## Requisitos

- Python 3.11+
- Docker + Docker Compose (para o PostgreSQL local)
- [ngrok](https://ngrok.com/download) (para expor a API ao ChatGPT durante testes locais)

---

## Rodando localmente

### 1. Clonar e configurar variáveis de ambiente

```bash
git clone https://github.com/seu-usuario/mcp-aws.git
cd mcp-aws

cp .env.example .env
# edite o .env e troque SECRET_KEY e OAUTH_CLIENT_SECRET por strings aleatórias longas
```

### 2. Subir o banco de dados

```bash
docker compose up -d
```

Postgres sobe na porta **5433** (não 5432 — evita conflito com instâncias locais).

### 3. Instalar dependências e rodar a API

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: http://localhost:8000  
Documentação automática (Swagger): http://localhost:8000/docs  
Frontend: http://localhost:8000

---

## Expondo para o GPT Actions com ngrok

GPT Actions exige uma URL pública com HTTPS. Use o ngrok para isso durante testes locais.

### 1. Instalar ngrok

Acesse https://ngrok.com/download, baixe e extraia o executável.  
Crie uma conta gratuita em https://ngrok.com e copie seu authtoken.

### 2. Configurar authtoken (só na primeira vez)

```bash
ngrok config add-authtoken SEU_TOKEN_AQUI
```

### 3. Expor a porta 8000

```bash
ngrok http 8000
```

O ngrok vai exibir algo como:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

Use essa URL (`https://abc123.ngrok-free.app`) para configurar o Custom GPT.

---

## Configurando o Custom GPT

1. Acesse https://chat.openai.com e crie um novo GPT
2. Vá em **Configure → Actions → Create new action**
3. Em **Schema**, cole a URL do OpenAPI filtrado para GPT Actions: `https://SUA-URL-NGROK/openapi-gpt.json`
4. Em **Authentication**, escolha **OAuth**
5. Configure:
   - Client ID: valor de `OAUTH_CLIENT_ID`
   - Client Secret: valor de `OAUTH_CLIENT_SECRET`
   - Authorization URL: `https://SUA-URL-NGROK/oauth/authorize`
   - Token URL: `https://SUA-URL-NGROK/oauth/token`
   - Scope: `aws`
   - Token Exchange Method: `Default (POST request)`
6. Copie a URL de callback/redirect exibida pelo GPT e coloque em `OAUTH_ALLOWED_REDIRECT_URIS`
7. Reinicie a API e teste pedindo ao GPT para listar instâncias EC2

O OAuth autentica o usuário no MCP AWS, não diretamente na AWS. Depois do login, a API usa apenas os tokens AWS cadastrados para aquele usuário.

### Campos sugeridos para o GPT

**Name**

```text
MCP AWS
```

**Description**

```text
Gerencie recursos AWS do usuário autenticado via MCP AWS, incluindo EC2, S3, RDS, VPC, ALB/NLB, IAM e credenciais AWS cadastradas.
```

**Instructions**

```text
Você é um assistente para gerenciamento de recursos AWS usando a API MCP AWS.

Use sempre as Actions configuradas para consultar ou executar operações na AWS. As Actions já autenticam o usuário via OAuth; nunca peça, armazene ou exponha credenciais AWS diretamente na conversa.

Antes de executar ações destrutivas ou com custo, como criar instâncias, parar serviços, terminar EC2, remover buckets, deletar instâncias RDS, remover targets ou criar/deletar access keys IAM, explique brevemente o impacto e peça confirmação explícita.

Quando uma operação exigir token_id, liste os tokens AWS cadastrados do usuário e peça que ele escolha qual conta/região usar caso isso não esteja claro.

Antes de criar uma EC2, use /api/ec2/images para buscar um AMI ID válido na região do token escolhido. Não invente AMI IDs.

Nunca tente acessar recursos de outro usuário. Considere apenas os dados retornados pela API para o usuário autenticado.

Se uma chamada AWS falhar por permissão, região, credenciais expiradas ou token temporário ausente, explique o erro de forma objetiva e diga qual credencial/configuração o usuário deve revisar no MCP AWS.
```

**Conversation starters**

```text
Liste minhas instâncias EC2
```

```text
Quais buckets S3 existem na minha conta?
```

```text
Mostre quem sou eu na AWS com o token configurado
```

```text
Liste meus tokens AWS cadastrados
```

**Action**

```text
Schema URL: https://SUA-URL-NGROK/openapi-gpt.json
Privacy policy: https://SUA-URL-NGROK/privacy
Authentication: OAuth
Authorization URL: https://SUA-URL-NGROK/oauth/authorize
Token URL: https://SUA-URL-NGROK/oauth/token
Scope: aws
Token Exchange Method: Default (POST request)
```

---

## Estrutura do projeto

```
mcp-aws/
├── backend/
│   ├── app/
│   │   ├── main.py               # entrypoint FastAPI — registra todos os routers
│   │   ├── api/routes/
│   │   │   ├── auth.py           # /api/auth
│   │   │   ├── tokens.py         # /api/tokens
│   │   │   ├── ec2.py            # /api/ec2
│   │   │   ├── s3.py             # /api/s3
│   │   │   ├── rds.py            # /api/rds
│   │   │   ├── vpc.py            # /api/vpc
│   │   │   ├── alb.py            # /api/alb
│   │   │   └── iam.py            # /api/iam
│   │   ├── core/                 # config, database, security/JWT
│   │   ├── models/               # SQLAlchemy (user, aws_token)
│   │   ├── schemas/              # Pydantic
│   │   └── services/
│   │       ├── aws_service.py    # boto3 EC2
│   │       ├── s3_service.py     # boto3 S3
│   │       ├── rds_service.py    # boto3 RDS
│   │       ├── vpc_service.py    # boto3 EC2 (VPC APIs)
│   │       ├── alb_service.py    # boto3 elbv2
│   │       └── iam_service.py    # boto3 IAM + STS
│   └── requirements.txt
├── frontend/
│   ├── index.html                # login / cadastro
│   └── dashboard.html            # gerenciamento de tokens AWS
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Endpoints

Todas as rotas autenticadas exigem `Authorization: Bearer <token>` no header.

### Autenticação

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/api/auth/register` | Não | Cadastrar usuário |
| POST | `/api/auth/login` | Não | Login — retorna JWT |
| GET | `/api/auth/me` | Sim | Dados do usuário autenticado |

### Tokens AWS

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/api/tokens/` | Sim | Listar tokens AWS |
| POST | `/api/tokens/` | Sim | Cadastrar token AWS |
| PUT | `/api/tokens/{id}` | Sim | Atualizar token AWS |
| DELETE | `/api/tokens/{id}` | Sim | Remover token AWS |

### EC2

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/api/ec2/instances` | Sim | Listar instâncias |
| GET | `/api/ec2/images` | Sim | Listar AMIs recentes por sistema operacional |
| POST | `/api/ec2/instances` | Sim | Criar instância |
| POST | `/api/ec2/instances/start` | Sim | Iniciar instância |
| POST | `/api/ec2/instances/stop` | Sim | Parar instância |
| DELETE | `/api/ec2/instances` | Sim | Terminar instância (permanente) |

### S3

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/api/s3/buckets` | Sim | Listar buckets |
| POST | `/api/s3/buckets` | Sim | Criar bucket |
| DELETE | `/api/s3/buckets` | Sim | Remover bucket vazio |
| GET | `/api/s3/buckets/objects` | Sim | Listar objetos (com prefixo opcional) |
| PUT | `/api/s3/buckets/objects` | Sim | Criar ou substituir objeto (texto) |
| DELETE | `/api/s3/buckets/objects` | Sim | Remover objeto |

### RDS

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/api/rds/instances` | Sim | Listar instâncias |
| POST | `/api/rds/instances` | Sim | Criar instância |
| POST | `/api/rds/instances/start` | Sim | Iniciar instância parada |
| POST | `/api/rds/instances/stop` | Sim | Parar instância (Single-AZ) |
| DELETE | `/api/rds/instances` | Sim | Remover instância |
| GET | `/api/rds/snapshots` | Sim | Listar snapshots |
| POST | `/api/rds/snapshots` | Sim | Criar snapshot manual |

### VPC (somente leitura)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/api/vpc/vpcs` | Sim | Listar VPCs |
| GET | `/api/vpc/subnets` | Sim | Listar subnets (filtro por VPC) |
| GET | `/api/vpc/security-groups` | Sim | Listar security groups (filtro por VPC) |
| GET | `/api/vpc/internet-gateways` | Sim | Listar internet gateways (filtro por VPC) |
| GET | `/api/vpc/route-tables` | Sim | Listar route tables (filtro por VPC) |

### ALB / NLB

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/api/alb/load-balancers` | Sim | Listar load balancers |
| GET | `/api/alb/listeners` | Sim | Listar listeners de um LB |
| GET | `/api/alb/target-groups` | Sim | Listar target groups |
| GET | `/api/alb/target-health` | Sim | Saúde dos targets de um target group |
| POST | `/api/alb/targets/register` | Sim | Registrar target em um target group |
| DELETE | `/api/alb/targets/deregister` | Sim | Remover target de um target group |

### IAM

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/api/iam/whoami` | Sim | Identidade da credencial (via STS) |
| GET | `/api/iam/users` | Sim | Listar usuários IAM |
| GET | `/api/iam/roles` | Sim | Listar roles IAM |
| GET | `/api/iam/groups` | Sim | Listar grupos IAM |
| GET | `/api/iam/policies` | Sim | Listar políticas (Local ou AWS) |
| GET | `/api/iam/access-keys` | Sim | Listar access keys de um usuário |
| POST | `/api/iam/access-keys` | Sim | Criar access key (retorna secret — guardar agora) |
| DELETE | `/api/iam/access-keys` | Sim | Deletar access key |

### Sistema

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/health` | Não | Status da API |
