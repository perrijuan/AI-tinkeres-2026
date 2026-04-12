# Status dos Dados — SafraViva MVP

> Última atualização: 2026-04-12

## Legenda
- ✅ **Real** — dado calculado ou obtido de fonte externa verdadeira
- 🟡 **Parcial** — lógica real, mas dados de entrada ainda limitados
- 🔴 **Sintético** — gerado por algoritmo determinístico (seed lat/lon), sem fonte externa

---

## Backend — `/api/v1/analysis`

### Entrada do usuário
| Campo | Status | Observação |
|---|---|---|
| Geometria do polígono | ✅ Real | Desenhada pelo usuário no mapa |
| Cultura | ✅ Real | Selecionada pelo usuário |
| Data de plantio | ✅ Real | Informada pelo usuário |
| Nome / propriedade | ✅ Real | Informado pelo usuário |

### Contexto espacial
| Dado | Status | Observação |
|---|---|---|
| Centroide, área, bbox | ✅ Real | Cálculo geométrico real sobre o polígono |
| Município e UF | 🟡 Parcial | Lookup real via GeoJSON — **só cobre MT** |

### Clima e previsão do tempo
| Dado | Status | Observação |
|---|---|---|
| Precipitação 7d / 14d | 🔴 Sintético | GEE/GFS não autenticado → fórmula matemática com seed |
| Temperatura máx / média 7d | 🔴 Sintético | Idem |
| Umidade média 7d | 🔴 Sintético | Idem |
| Vento médio 7d | 🔴 Sintético | Idem |
| Série temporal 14 dias (gráfico) | 🔴 Sintético | Todos os pontos gerados sinteticamente |
| **Quando GEE ativado** | ✅ Real | Fonte: `NOAA/GFS0P25` via Google Earth Engine |

### Satélite / vegetação
| Dado | Status | Observação |
|---|---|---|
| NDVI (série temporal) | 🔴 Sintético | GEE não autenticado → hash determinístico por lat/lon |
| EVI | 🔴 Sintético | Idem |
| LST (temperatura superfície) | 🔴 Sintético | Idem |
| Cobertura de nuvens | 🔴 Sintético | Idem |
| **Quando GEE ativado** | ✅ Real | Fontes: `MOD13Q1`, `MOD11A2`, `COPERNICUS/S2_SR_HARMONIZED` |

### Contexto agroclimático
| Dado | Status | Observação |
|---|---|---|
| Estágio da cultura (crop_stage) | ✅ Real | Calculado da diferença entre `sowing_date` e hoje |
| Perfis por cultura (thresholds) | ✅ Real | Parâmetros agronômicos baseados em literatura (soja, milho, algodão) |
| Janela ZARC | ✅ Real | Dataset local `zarc_mt_consolidado.csv` — municípios de MT |
| Flag "fora do ZARC" | 🟡 Parcial | Lógica real, dataset cobre só MT e culturas disponíveis no CSV |
| Yield histórico (volatilidade, tendência) | 🔴 Sintético | Hash por município+cultura, sem dados reais do IBGE/PAM |
| Índices territoriais (vegetation_stress, soil_buffer) | 🔴 Sintético | Derivados do NDVI/EVI sintéticos |

### Score e alertas
| Dado | Status | Observação |
|---|---|---|
| Score de risco (0–100) | 🟡 Parcial | Algoritmo real, mas alimentado por dados climáticos e de vegetação sintéticos |
| Flags (seca, calor, ZARC, vegetação) | 🟡 Parcial | Lógica real, inputs sintéticos |
| Textos de alerta e recomendação | 🟡 Parcial | Templates reais, derivados dos flags acima |

### Chat — Safrinia
| Dado | Status | Observação |
|---|---|---|
| Respostas do chat | ✅ Real | Gemini (`gemini-flash`) com contexto da análise — `GEMINI_API_KEY` configurada |
| Contexto enviado ao Gemini | 🟡 Parcial | Real na estrutura, mas métricas de base são sintéticas |

---

## O que ativa os dados reais

| Integração | O que falta |
|---|---|
| **GEE — Clima (GFS)** | Instalar `earthengine-api` + preencher `GEE_PROJECT_ID`, `GEE_SERVICE_ACCOUNT`, `GEE_PRIVATE_KEY_JSON` no `.env` |
| **GEE — Satélite (MODIS/Sentinel)** | Mesmas credenciais acima |
| **Municípios fora de MT** | Adicionar GeoJSONs de outros estados em `data/raw/` |
| **Yield histórico real** | Integrar IBGE/PAM ou base própria em `src/features/historical.py` |

---

## Fluxo atual resumido

```
Usuário desenha polígono
        ↓
Geometria real → centroide/área/município (real, só MT)
        ↓
Clima → GEE tenta → falha (sem credenciais) → SINTÉTICO
        ↓
Satélite → GEE tenta → falha (sem credenciais) → SINTÉTICO
        ↓
ZARC → CSV local → REAL (só MT)
        ↓
Score → algoritmo real sobre dados sintéticos → PARCIAL
        ↓
Chat Safrinia → Gemini → REAL
```
