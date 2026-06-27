# mcp-aws

API para gerenciar recursos AWS (EC2) via GPT Actions (Custom GPT do ChatGPT).  
Cada usuário cadastra seu próprio token AWS e usa o ChatGPT para controlar instâncias.

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
# edite o .env e troque SECRET_KEY por uma string aleatória longa
```

### 2. Subir o banco de dados

```bash
docker compose up -d
```

### 3. Instalar dependências e rodar a API

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
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
3. Em **Schema**, cole a URL do OpenAPI: `https://SUA-URL-NGROK/openapi.json`
4. Em **Authentication**, escolha **API Key** e configure como `Bearer` — o usuário cola o JWT obtido no login
5. Salve e teste pedindo ao GPT para listar instâncias EC2

---

## Estrutura do projeto

```
mcp-aws/
├── backend/
│   ├── app/
│   │   ├── main.py           # entrypoint FastAPI
│   │   ├── api/routes/       # auth, tokens, ec2
│   │   ├── core/             # config, database, jwt
│   │   ├── models/           # SQLAlchemy (user, aws_token)
│   │   ├── schemas/          # Pydantic
│   │   └── services/         # boto3 (aws_service)
│   └── requirements.txt
├── frontend/
│   ├── index.html            # login / cadastro
│   └── dashboard.html        # gerenciamento de tokens AWS
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /api/auth/register | Cadastrar usuário |
| POST | /api/auth/login | Login (retorna JWT) |
| GET | /api/auth/me | Dados do usuário autenticado |
| GET | /api/tokens/ | Listar tokens AWS |
| POST | /api/tokens/ | Cadastrar token AWS |
| PUT | /api/tokens/{id} | Atualizar token AWS |
| DELETE | /api/tokens/{id} | Remover token AWS |
| GET | /api/ec2/instances | Listar instâncias EC2 |
| POST | /api/ec2/instances | Criar instância EC2 |
| POST | /api/ec2/instances/start | Iniciar instância |
| POST | /api/ec2/instances/stop | Parar instância |
| DELETE | /api/ec2/instances | Terminar instância |
| GET | /health | Status da API |
