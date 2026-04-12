# Status dos Dados — Dashboard SafraViva

> Atualizado em: 2026-04-12

## Legenda
- ✅ **Real** — dado calculado ou obtido de fonte externa verdadeira
- 🟡 **Parcial** — lógica real, mas dado de entrada ainda limitado
- 🔴 **Sintético** — gerado por algoritmo com seed lat/lon, sem fonte externa

---

## Painel esquerdo — Resumo do campo

| Elemento na tela | Status | Fonte |
|---|---|---|
| Nome da propriedade | ✅ Real | Digitado pelo usuário no formulário |
| Cultura e área (ha) | ✅ Real | Usuário + cálculo geométrico real sobre o polígono |
| Município e UF | 🟡 Parcial | GeoJSON real — **cobre apenas Mato Grosso** |
| Data de plantio | ✅ Real | Informada pelo usuário |
| Estágio da cultura | ✅ Real | Calculado da diferença entre `sowing_date` e hoje |
| Score de risco (0–100) | 🟡 Parcial | Algoritmo real, mas alimentado por clima e NDVI sintéticos |
| Nível de risco (baixo/moderado/alto/crítico) | 🟡 Parcial | Derivado do score acima |
| Alerta principal | 🟡 Parcial | Template real baseado nos flags abaixo |
| Ação recomendada | 🟡 Parcial | Template real baseado nos flags abaixo |

---

## Flags de risco

| Flag | Status | Fonte |
|---|---|---|
| Seca | 🔴 Sintético | Derivado da precipitação sintética vs threshold da cultura |
| Calor excessivo | 🔴 Sintético | Derivado da temperatura sintética vs threshold da cultura |
| Fora do ZARC | ✅ Real | Dataset local `zarc_mt_consolidado.csv` (municípios MT) |
| Estresse vegetativo | 🔴 Sintético | Derivado do NDVI sintético |

---

## Cards de métricas

| Métrica | Status | Fonte |
|---|---|---|
| Chuva 7 dias (mm) | 🔴 Sintético | GEE/GFS não autenticado → fórmula com seed lat/lon/data |
| Chuva 14 dias (mm) | 🔴 Sintético | Idem |
| Temperatura máxima 7d (°C) | 🔴 Sintético | Idem |
| Temperatura média 7d (°C) | 🔴 Sintético | Idem |
| Umidade média 7d (%) | 🔴 Sintético | Idem |
| Vento médio 7d (m/s) | 🔴 Sintético | Idem |

---

## Gráficos

| Gráfico | Status | Fonte |
|---|---|---|
| Previsão chuva + temperatura 14 dias | 🔴 Sintético | GEE/GFS não autenticado → todos os 14 pontos gerados sinteticamente |
| NDVI — Vegetação (série temporal) | 🔴 Sintético | GEE/MODIS não autenticado → hash por lat/lon |

---

## Mapa

| Elemento | Status | Fonte |
|---|---|---|
| Polígono do talhão | ✅ Real | Geometria desenhada pelo usuário |
| Cor do polígono (risco) | 🟡 Parcial | Cor derivada do score (lógica real, score parcial) |
| Tooltip de resumo | 🟡 Parcial | Texto gerado a partir dos dados acima |

---

## Fontes de dados (accordion)

| Fonte | Status | Observação |
|---|---|---|
| Clima — provider/modelo | 🔴 Sintético | Exibe "SafraViva Synthetic Climate" quando GEE está off |
| Clima — sinais | 🔴 Sintético | Gerados a partir dos valores sintéticos |
| Satélite — provider/data da imagem | 🔴 Sintético | Exibe "SafraViva Synthetic Territory" |
| Satélite — cobertura de nuvens | 🔴 Sintético | Hash determinístico |
| Satélite — sinais | 🔴 Sintético | Gerados a partir do NDVI/EVI sintéticos |
| ZARC — classe e label | ✅ Real | CSV local por município |
| ZARC — plantio dentro da janela | ✅ Real | Lógica real sobre `sowing_date` |
| ZARC — sinais | 🟡 Parcial | Mensagens reais, dados do CSV |
| Histórico — provider/período | 🔴 Sintético | Placeholder "IBGE/PAM (placeholder MVP)" |
| Histórico — sinais | 🔴 Sintético | Gerados via hash por município+cultura |

---

## Safrinia (chat e card de diagnóstico)

| Elemento | Status | Fonte |
|---|---|---|
| Card diagnóstico (resumo, por quê, ação) | 🟡 Parcial | Gerado pelo backend com templates + dados parciais |
| Chat — respostas da Safrinia | ✅ Real | **Gemini `gemini-3.1-flash-lite-preview` funcionando** |
| Chat — contexto enviado ao Gemini | 🟡 Parcial | Estrutura real, métricas de clima sintéticas |

---

## O que falta para virar 100% real

| Integração | Status | O que fazer |
|---|---|---|
| GEE — Clima (GFS/NOAA) | ❌ Pendente | Ativar API Earth Engine no GCP + registrar projeto `safraviva-493019` |
| GEE — Satélite (MODIS/Sentinel-2) | ❌ Pendente | Mesmas credenciais GEE acima |
| Municípios fora de MT | ❌ Pendente | Adicionar GeoJSONs dos demais estados em `backend/data/raw/` |
| Yield histórico real | ❌ Pendente | Integrar IBGE/PAM ou base própria |
