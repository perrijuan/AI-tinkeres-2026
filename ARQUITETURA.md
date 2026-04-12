# Arquitetura — SafraViva

> Atualizado em: 2026-04-12

## Visão geral

```
Usuário (browser)
      │
      ▼
┌─────────────────────────────┐
│   Frontend  (React + Vite)  │  porta 5173
│   /frontend                 │
└─────────────┬───────────────┘
              │ HTTP/REST
              ▼
┌─────────────────────────────┐
│   Backend  (FastAPI)        │  porta 8000
│   /backend                  │
└──┬──────────┬───────────────┘
   │          │
   ▼          ▼
Google     CSV/GeoJSON
Earth      local
Engine     (ZARC, municípios)
```

---

## Frontend

### Stack
| Tecnologia | Versão | Uso |
|---|---|---|
| React | 18 | UI |
| TypeScript | 5 | Tipagem |
| Vite | 5 | Build e dev server |
| Tailwind CSS | 3 | Estilização |
| shadcn/ui | — | Componentes (Card, Badge, Button…) |
| React Router | 6 | Navegação entre páginas |
| Recharts | 2 | Gráficos (previsão 14d, NDVI) |
| React Leaflet | 4 | Mapa interativo (Leaflet.js) |
| react-markdown | 10 | Renderiza markdown nas respostas da Safrinia |

### Páginas
| Arquivo | Rota | O que faz |
|---|---|---|
| `src/pages/DemoPage.tsx` | `/demo` | Formulário (3 steps) + mapa para desenhar o polígono |
| `src/pages/ResultsPage.tsx` | `/resultado` | Dashboard completo da análise + chat Safrinia |

### Configuração de ambiente
| Arquivo | Conteúdo |
|---|---|
| `frontend/.env` | `VITE_API_BASE_URL` — URL base do backend |
| `frontend/src/config.ts` | Centraliza todos os endpoints (`API_ENDPOINTS`) |

### Fluxo do usuário
```
/ (landing)
  → /demo   Step 1: nome, empresa, email, cultura, data de plantio
            Step 2: seleção da cultura no mapa de culturas
            Step 3: desenho do polígono no mapa (cliques)
              ↓ POST /api/v1/analysis
  → /resultado  Dashboard com todos os dados da análise
```

---

## Backend

### Stack
| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.12 | Runtime |
| FastAPI | 0.115+ | Framework HTTP |
| Uvicorn | 0.29+ | ASGI server |
| Pydantic v2 | 2+ | Validação de schemas |
| google-generativeai | 0.8+ | Chat Gemini (Safrinia) — *deprecação prevista* |
| earthengine-api | 1.7+ | Dados de clima e satélite via GEE |
| python-dotenv | 1.0+ | Leitura do `.env` |

### Endpoints

| Método | Rota | Arquivo | O que faz |
|---|---|---|---|
| `POST` | `/api/v1/analysis` | `main.py` | Análise completa — contrato v1 |
| `POST` | `/api/v1/analyze` | `main.py` | Alias do endpoint acima |
| `POST` | `/mock/analysis` | `routers/analysis.py` | Análise via Gemini (legado) com fallback para mock fixo |
| `POST` | `/chat` | `routers/chat.py` | Mensagem para a Safrinia |
| `GET` | `/culturas` | `routers/culturas.py` | Lista de culturas disponíveis |
| `GET` | `/health` | `routers/health.py` | Health check |

### Estrutura de pastas

```
backend/
├── main.py                    ← entrypoint FastAPI, registra routers e endpoint v1
├── run.sh                     ← inicia uvicorn com --reload otimizado
│
├── routers/                   ← endpoints HTTP legados
│   ├── analysis.py            /mock/analysis (Gemini ou mock fixo)
│   ├── chat.py                /chat
│   ├── culturas.py            /culturas
│   └── health.py              /health
│
├── src/                       ← motor de análise (pipeline v1)
│   ├── pipeline.py            orquestra todas as etapas
│   ├── schemas.py             modelos Pydantic (AnalysisRequest, AnalysisResponse)
│   │
│   ├── ingest/                busca dados externos
│   │   ├── gee_client.py      autenticação GEE (service account)
│   │   ├── climate_forecast.py  previsão GFS/NOAA via GEE + fallback sintético
│   │   ├── territorial_context.py  NDVI/EVI/LST via MODIS+Sentinel + fallback
│   │   ├── spatial_context.py  centroide, bbox, área, município
│   │   └── municipality_lookup.py  lookup por GeoJSON (atualmente só MT)
│   │
│   ├── features/              transforma dados em features
│   │   ├── agro_context.py    estágio da cultura, ZARC, perfis agronômicos
│   │   ├── zarc_lookup.py     consulta dataset ZARC local
│   │   ├── response_builder.py  monta o JSON final para o frontend
│   │   └── map_layer.py       geometria + cor de risco para o mapa
│   │
│   └── scoring/               calcula risco e alertas
│       ├── risk.py            score 0–100, flags (seca, calor, ZARC, vegetação)
│       └── alerts.py          textos de alerta, recomendação e copilot
│
├── chat_session.py            sessões de conversa da Safrinia (Gemini, in-memory)
├── mock.py                    mock estático completo (fallback do /mock/analysis)
├── ai_mock.py                 geração via Gemini do /mock/analysis
│
└── data/
    ├── raw/municipios_mt.geojson  lookup de municípios MT
    └── zarc_mt_consolidado.csv    dataset ZARC por município/cultura
```

### Pipeline v1 — passo a passo

```
POST /api/v1/analysis  (AnalysisRequest)
        │
        ▼
1. derive_spatial_context
   └── centroide, bbox, área ha, município (GeoJSON MT)
        │
        ▼
2. get_climate_forecast
   ├── tenta: GEE → NOAA/GFS0P25 (14 dias de precip/temp/umidade/vento)
   └── fallback: gerador determinístico com seed lat/lon/data
        │
        ▼
3. get_territorial_context
   ├── tenta: GEE → MOD13Q1 (NDVI/EVI) + MOD11A2 (LST) + Sentinel-2 (nuvens)
   └── fallback: hash determinístico por lat/lon
        │
        ▼
4. get_agro_context
   ├── perfil da cultura (thresholds agronômicos)
   ├── zarc_lookup (CSV local)
   ├── crop_stage (calculado da sowing_date)
   └── índices territoriais (do passo 3)
        │
        ▼
5. calculate_risk_score
   └── score 0–100 + flags de risco
        │
        ▼
6. generate_alerts_and_recommendations
   └── textos de alerta + copilot_response
        │
        ▼
7. build_map_layer
   └── cor do polígono baseada no risk_level
        │
        ▼
8. build_frontend_response
   └── monta AnalysisResponse completo
        │
        ▼
9. start_conversation (Gemini)
   └── cria sessão de chat com contexto da análise
        │
        ▼
AnalysisResponse (JSON)  →  Frontend
```

### Score de risco — componentes

| Componente | Peso máximo | Condição |
|---|---|---|
| Base | 12 pts | Sempre |
| Seca | 42 pts | Precipitação abaixo do ideal da cultura |
| Calor | 26 pts | Temperatura acima do threshold da cultura |
| Umidade baixa | 8 pts | Umidade < 58% |
| Vento alto | 7 pts | Vento > 4.8 m/s |
| Fora do ZARC | 14 pts | Data de plantio fora da janela recomendada |
| Estresse vegetativo | 22 pts | NDVI abaixo da faixa saudável |
| Volatilidade histórica | 9 pts | Baseado no histórico de produtividade |

### Variáveis de ambiente

| Variável | Obrigatória | Uso |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Sim (chat) | Chat da Safrinia via Gemini |
| `GEE_PROJECT_ID` | Para GEE | ID do projeto GCP |
| `GEE_SERVICE_ACCOUNT` | Para GEE | Email da service account |
| `GEE_PRIVATE_KEY_PATH` | Para GEE | Caminho para o JSON da chave |
| `GEE_PRIVATE_KEY_JSON` | Alternativa | JSON da chave inline |
| `USE_GEE_CLIMATE` | Não | `true/false` — ativa/desativa GEE para clima |
| `USE_GEE_TERRITORY` | Não | `true/false` — ativa/desativa GEE para satélite |

---

## Integrações externas

| Serviço | Status | Uso |
|---|---|---|
| **Google Earth Engine** | ❌ Pendente (permissão GCP) | Clima (GFS) + Satélite (MODIS/Sentinel-2) |
| **Gemini API** | ✅ Funcionando | Chat Safrinia — `gemini-3.1-flash-lite-preview` |
| **CARTO (TileLayer)** | ✅ Funcionando | Tiles do mapa base no frontend |

---

## Como rodar localmente

```bash
# Backend
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # preencher as chaves
./run.sh               # inicia com hot-reload otimizado

# Frontend
cd frontend
npm install
cp .env.example .env   # ajustar VITE_API_BASE_URL se necessário
npm run dev
```
