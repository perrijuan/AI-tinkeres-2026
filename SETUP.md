# Setup do Projeto — SafraViva

> Atualizado com base no código atual do repositório em 2026-04-12.

## Visão rápida

O projeto está dividido em dois apps principais:

- `backend/` com FastAPI e pipeline de análise
- `frontend/` com React + Vite

Para rodar o MVP localmente, você precisa subir os dois.

---

## Pré-requisitos

- Python 3.10 ou superior
- Node.js 18 ou superior
- `npm`

### Integrações opcionais

- chave do Gemini para o chat da Safrinia
- credenciais do Google Earth Engine para clima e satélite reais

Sem essas integrações, parte da aplicação continua funcionando com fallback, principalmente no lado climático e territorial.

---

## Estrutura relevante

```text
backend/
frontend/
backend/.env
backend/requirements.txt
frontend/package.json
```

---

## Backend

### 1. Criar ambiente virtual

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

No Windows:

```bash
.venv\Scripts\activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

Dependências principais:

- `fastapi`
- `uvicorn`
- `pydantic`
- `google-generativeai`
- `earthengine-api`
- `python-dotenv`

### 3. Configurar variáveis de ambiente

Crie ou edite o arquivo `backend/.env`.

Variáveis identificadas no projeto:

```env
GEMINI_API_KEY=
GEE_PROJECT_ID=
GEE_SERVICE_ACCOUNT=
GEE_PRIVATE_KEY_PATH=
USE_GEE_CLIMATE=true
USE_GEE_TERRITORY=true
```

### 4. Rodar o backend

Opção direta:

```bash
uvicorn main:app --reload
```

Opção recomendada no repositório:

```bash
./run.sh
```

O script `backend/run.sh` já sobe o Uvicorn com `reload` e ignora diretórios pesados como `.venv`, `data` e `dataset`.

### 5. Endereço local

```text
http://localhost:8000
```

Endpoints principais:

- `POST /api/v1/analysis`
- `POST /api/v1/analyze`
- `POST /mock/analysis`
- `POST /chat`
- `GET /culturas`
- `GET /health`

---

## Frontend

### 1. Instalar dependências

```bash
cd frontend
npm install
```

### 2. Configurar ambiente

Se quiser apontar para outro backend, crie `frontend/.env` com:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Se esse arquivo não existir, o frontend já usa `http://localhost:8000` como padrão.

### 3. Rodar o frontend

```bash
npm run dev
```

### 4. Endereço local

```text
http://localhost:5173
```

---

## Configuração das integrações

## Gemini

O chat da Safrinia depende de:

```env
GEMINI_API_KEY=...
```

### O que funciona com Gemini

- criação de sessão contextual após a análise
- respostas do endpoint `/chat`
- geração do mock enriquecido em `/mock/analysis`, quando a chave estiver presente

### O que acontece sem Gemini

- a análise principal continua funcionando
- o chat retorna indisponível
- o endpoint de mock cai para um mock fixo local

---

## Google Earth Engine

O backend tenta usar GEE para:

- previsão climática via `NOAA/GFS0P25`
- contexto territorial via `MODIS` e `Sentinel-2`

### Variáveis esperadas

```env
GEE_PROJECT_ID=...
GEE_SERVICE_ACCOUNT=...
GEE_PRIVATE_KEY_PATH=/caminho/para/service-account.json
USE_GEE_CLIMATE=true
USE_GEE_TERRITORY=true
```

### Comportamento do código

- se as credenciais estiverem válidas, o backend tenta inicializar o Earth Engine
- se falhar, o sistema usa fallback sintético
- o fallback mantém o dashboard funcional para demo

### Alternativas previstas no código

O cliente também considera:

- `GEE_PRIVATE_KEY_JSON`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `ENABLE_GEE_DEFAULT_AUTH`
- `DISABLE_GEE`

Mesmo que essas variáveis não estejam hoje no `.env`, elas já são suportadas pelo código em `backend/src/ingest/gee_client.py`.

---

## Como validar que tudo subiu

### Backend

Abra no navegador ou use `curl`:

```bash
curl http://localhost:8000/health
```

### Frontend

Abra:

```text
http://localhost:5173
```

### Fluxo mínimo de teste

1. abrir a landing
2. entrar em `/demo`
3. preencher nome, e-mail, cultura e data
4. desenhar um polígono
5. confirmar a análise
6. verificar se `/resultado` abre com score, métricas e mapa

---

## Limitações observadas no setup atual

- o repositório raiz tem um `env.example`, mas ele está vazio
- não há `frontend/.env.example`
- a documentação antiga sugeria copiar `.env.example`, mas isso não reflete o estado atual do projeto
- parte dos dados reais depende de credenciais externas que não podem ser validadas só pela leitura do repositório

---

## Setup recomendado para demo

Se a prioridade for demonstrar o produto rapidamente:

1. configure `GEMINI_API_KEY`
2. rode backend e frontend
3. deixe GEE habilitado apenas se as credenciais estiverem corretas
4. se GEE falhar, o sistema ainda entrega a experiência de ponta a ponta com fallback

---

## Resumo

O setup do projeto é simples para o núcleo do MVP. O backend e o frontend sobem localmente sem grande atrito. O que muda o nível de realismo dos dados não é a capacidade de rodar o sistema, e sim a presença ou ausência das integrações externas, especialmente GEE e Gemini.
