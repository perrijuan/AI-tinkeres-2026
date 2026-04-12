# Status dos Dados — SafraViva

> Atualizado com base no código atual do repositório em 2026-04-12.

## Como ler este documento

Este status foi consolidado pela análise do código, não por inspeção de execução em produção. Então o foco aqui é:

- o que já está implementado de forma real
- o que está parcialmente real
- o que ainda depende de fallback sintético ou heurístico

## Legenda

- `✅ Real`: lógica e fonte reais já conectadas no código
- `🟡 Parcial`: lógica real, mas com cobertura limitada, fallback ou dataset incompleto
- `🔴 Sintético/Heurístico`: saída gerada por fórmula, hash determinístico ou regra simplificada

---

## Resumo executivo

O produto já tem um pipeline funcional de análise territorial e climática, mas o realismo da resposta depende do estado das integrações externas.

Hoje, pelo código:

- a geometria do usuário é real
- área calculada é real
- lookup municipal é parcial e limitado a base local
- ZARC é parcialmente real via CSV local
- clima pode ser real via GEE, mas cai para sintético se o GEE falhar
- satélite pode ser real via GEE, mas cai para sintético se o GEE falhar
- histórico produtivo ainda é heurístico
- chat com Gemini está integrado, mas depende da chave de ambiente

---

## Fluxo do formulário até o algoritmo

Hoje o frontend envia um payload estruturado para `POST /api/v1/analysis`, então a integração front → backend é real e bem definida. Mas os campos têm pesos diferentes no sistema:

- alguns entram diretamente no algoritmo
- alguns são recalculados no backend
- alguns são usados só para identificação ou UX
- alguns hoje estão fixos no frontend

### Leitura geral

O fluxo está dinâmico no sentido de contrato e transporte de dados, mas ainda não está 100% dinâmico do ponto de vista de modelagem de entrada do usuário. O motor de risco hoje depende principalmente de:

- `culture`
- `sowing_date`
- `analysis_timestamp`
- `geometry`

Campos como nome, e-mail e empresa não afetam o score.

---

## Mapeamento do formulário para o backend

| Campo do frontend | Enviado ao backend | Usado no algoritmo | Status | Observação |
|---|---|---|---|---|
| Nome (`nome`) | 🟡 Indiretamente | ❌ Não | 🟡 Parcial | Entra na composição de `field_id` e pode virar `property_name` se `empresa` estiver vazia |
| Empresa (`empresa`) | ✅ Sim | ❌ Não | 🟡 Parcial | Vira `property_name`, usado para identificação no resultado |
| E-mail (`email`) | ❌ Não | ❌ Não | 🔴 Não integrado | É obrigatório no frontend, mas não vai para a API nem para o algoritmo |
| Cultura (`cultura`) | ✅ Sim | ✅ Sim | ✅ Real | Afeta perfil agronômico, thresholds e leitura de ZARC |
| Data de plantio (`sowingDate`) | ✅ Sim | ✅ Sim | ✅ Real | Afeta estágio da cultura e leitura da janela ZARC |
| Polígono desenhado (`points`) | ✅ Sim | ✅ Sim | ✅ Real | Base para área, centroide, município, clima, satélite e mapa |
| Área calculada no frontend (`areaHa`) | ❌ Não | ❌ Não | 🔴 Só UX local | O frontend calcula, mas não envia; o backend recalcula a área real |
| `field_id` | ✅ Sim | ❌ Não | 🟡 Parcial | Identificador dinâmico, mas não influencia a análise |
| `property_name` | ✅ Sim | ❌ Não | 🟡 Parcial | Identificação textual da análise, sem efeito no score |
| `crop_stage` | ✅ Sim (`null`) | 🟡 Indiretamente | 🟡 Parcial | O frontend não informa; o backend infere automaticamente |
| `irrigated` | ✅ Sim (`false`) | ✅ Sim | 🟡 Parcial | O algoritmo usa, mas o frontend hoje sempre manda `false` |
| `analysis_timestamp` | ✅ Sim | ✅ Sim | ✅ Real | Entra na janela temporal da análise e no fallback determinístico |

---

## O que está realmente dinâmico hoje

### Dinâmico e estrutural

- cultura selecionada
- data de plantio
- geometria desenhada
- timestamp da análise

Esses campos efetivamente alteram a análise.

### Dinâmico, mas só informacional

- `field_id`
- `property_name`

Esses campos mudam conforme o usuário preenche o formulário, mas hoje não mudam o comportamento do algoritmo.

### Ainda não dinâmico de verdade

- `email`, porque não é enviado ao backend
- `irrigated`, porque está fixo como `false`
- `crop_stage`, porque o frontend sempre manda `null`

---

## Entrada do usuário

| Elemento | Status | Observação |
|---|---|---|
| Nome da propriedade | 🟡 Parcial | Recebido do formulário e enviado ao backend, mas sem efeito no cálculo |
| Cultura | ✅ Real | Selecionada no frontend e enviada ao backend |
| Data de plantio | ✅ Real | Informada pelo usuário |
| Geometria do talhão | ✅ Real | Polígono desenhado pelo usuário |
| Área em hectares | ✅ Real | Recalculada no backend a partir do polígono |
| `analysis_timestamp` | ✅ Real | Gerado no momento da análise |
| E-mail do usuário | 🔴 Não integrado | Existe no formulário, mas não é enviado para a API |
| Irrigação | 🔴 Não capturado pelo usuário | O backend aceita o campo, mas o frontend fixa `false` |
| Estágio da cultura informado pelo usuário | 🔴 Não capturado pelo usuário | O backend aceita o campo, mas o frontend manda `null` |

---

## Contexto espacial

| Elemento | Status | Observação |
|---|---|---|
| Centroide do polígono | ✅ Real | Derivado da geometria |
| Bounding box | ✅ Real | Derivada da geometria |
| Área do polígono | ✅ Real | Calculada no backend |
| Município e UF | 🟡 Parcial | Resolvidos por proximidade usando GeoJSON local |

### Observação importante

O lookup municipal usa `backend/data/raw/municipios_mt.geojson` ou `data/municipios_mt.geojson`. A base atual é focada em MT e a estratégia é por proximidade de centroides, não por interseção poligonal robusta.

---

## Clima

| Elemento | Status | Observação |
|---|---|---|
| Fonte climática primária | 🟡 Parcial | GEE com `NOAA/GFS0P25`, se inicializar corretamente |
| Precipitação 7d | 🟡 Parcial | Real com GEE, sintética no fallback |
| Precipitação 14d | 🟡 Parcial | Real com GEE, sintética no fallback |
| Temperatura média 7d | 🟡 Parcial | Real com GEE, sintética no fallback |
| Temperatura máxima 7d | 🟡 Parcial | Real com GEE, sintética no fallback |
| Umidade média 7d | 🟡 Parcial | Real com GEE, sintética no fallback |
| Vento médio 7d | 🟡 Parcial | Real com GEE, sintética no fallback |
| Série de previsão 14 dias | 🟡 Parcial | Real com GEE, sintética no fallback |

### Quando o dado climático é real

- `USE_GEE_CLIMATE=true`
- credenciais do Earth Engine válidas
- coleção `NOAA/GFS0P25` acessível
- bandas esperadas disponíveis

### Quando vira fallback

Se qualquer uma dessas condições falhar, o backend usa um gerador determinístico baseado em:

- latitude
- longitude
- timestamp de análise

Isso preserva consistência visual para demo, mas não representa observação operacional real.

---

## Satélite e território

| Elemento | Status | Observação |
|---|---|---|
| NDVI | 🟡 Parcial | Real via MODIS quando GEE funciona |
| EVI | 🟡 Parcial | Real via MODIS quando GEE funciona |
| LST | 🟡 Parcial | Real via MODIS quando GEE funciona |
| Cobertura de nuvens | 🟡 Parcial | Real via Sentinel-2 quando GEE funciona |
| Série temporal de NDVI | 🟡 Parcial | Real quando MODIS responde; sintética no fallback |
| Índice de estresse vegetativo | 🟡 Parcial | Cálculo real sobre entrada real ou sintética |
| Índice de buffer hídrico do solo | 🟡 Parcial | Cálculo real sobre entrada real ou sintética |
| Índice de vulnerabilidade | 🟡 Parcial | Cálculo real sobre entrada real ou sintética |
| `alphaearth_cluster` | 🔴 Heurístico | Cluster sintético derivado de hash |

### Fontes usadas quando o GEE está ativo

- `MODIS/061/MOD13Q1`
- `MODIS/061/MOD11A2`
- `COPERNICUS/S2_SR_HARMONIZED`

### Fallback atual

Se o GEE não responder, o sistema cria:

- NDVI sintético
- EVI sintético
- LST sintético
- nuvem sintética
- timeseries sintética de NDVI

---

## Contexto agro e ZARC

| Elemento | Status | Observação |
|---|---|---|
| Estágio da cultura | ✅ Real | Inferido da diferença entre plantio e data da análise |
| Perfil agronômico de soja | ✅ Real | Threshold explícito |
| Perfil agronômico de milho | ✅ Real | Threshold explícito |
| Perfil agronômico de algodão | ✅ Real | Threshold explícito |
| Demais culturas | 🟡 Parcial | Usam perfil padrão |
| ZARC por município/cultura | 🟡 Parcial | CSV local em `backend/dataset/zarc_mt_consolidado.csv` |
| Janela heurística de plantio | 🟡 Parcial | Usada quando o dataset não cobre o caso |
| Classe ZARC | 🟡 Parcial | Real quando o CSV encontra cultura e município |
| Flag de plantio dentro da janela | 🟡 Parcial | Real ou heurística, conforme cobertura |

### Importante

O ZARC local tem valor real, mas a cobertura ainda não é universal. Quando município ou cultura não são encontrados, o sistema cai para regra heurística.

---

## Histórico produtivo

| Elemento | Status | Observação |
|---|---|---|
| `yield_mean_index` | 🔴 Heurístico | Derivado de hash por município e cultura |
| `yield_volatility` | 🔴 Heurístico | Derivado de hash por município e cultura |
| `yield_trend` | 🔴 Heurístico | Derivado de hash por município e cultura |
| Fonte exibida no frontend | 🔴 Placeholder | `"IBGE/PAM (placeholder MVP)"` |

### Situação real

Ainda não há integração com uma base histórica operacional de produtividade. Existe apenas uma camada sintética usada para compor score e narrativa.

---

## Score, flags e explicação

| Elemento | Status | Observação |
|---|---|---|
| Score de risco | 🟡 Parcial | Algoritmo real, alimentado por cultura, data, geometria e fontes reais ou fallback |
| Nível de risco | ✅ Real | Derivado do score |
| Flags de seca, calor, ZARC e vegetação | 🟡 Parcial | Regras reais, dependentes da qualidade dos insumos |
| Alerta principal | ✅ Real | Gerado por lógica do backend |
| Ação recomendada | ✅ Real | Gerada por lógica do backend |
| Copilot response | ✅ Real | Gerado por templates e regras do backend |

### Leitura correta

O motor de decisão já existe e é real. O que ainda oscila é a fidelidade das entradas.

---

## Chat da Safrinia

| Elemento | Status | Observação |
|---|---|---|
| Sessão de conversa | ✅ Real | Criada após a análise |
| Contextualização do prompt | ✅ Real | Montada a partir do payload da análise |
| Resposta via Gemini | 🟡 Parcial | Real quando `GEMINI_API_KEY` estiver válida |
| Persistência do histórico | 🔴 Limitada | Em memória apenas |

### Situação prática

- sem `GEMINI_API_KEY`, o endpoint `/chat` não funciona
- com chave válida, o chat funciona
- o histórico não persiste entre reinícios do backend

---

## Frontend e visualização

| Elemento | Status | Observação |
|---|---|---|
| Polígono desenhado | ✅ Real | Vem diretamente da geometria enviada pelo usuário |
| Cor do polígono | ✅ Real | Derivada do nível de risco |
| Tooltip do mapa | ✅ Real | Montado pelo backend |
| Cards de métricas | 🟡 Parcial | Reais ou sintéticos conforme origem dos dados |
| Gráfico de previsão | 🟡 Parcial | Real ou sintético conforme clima |
| Gráfico de NDVI | 🟡 Parcial | Real ou sintético conforme satélite |
| Bloco de fontes de dados | ✅ Real | Exibe a origem realmente entregue pelo backend |
| Nome da propriedade no dashboard | 🟡 Parcial | Dinâmico, mas apenas informacional |
| Cultura no dashboard | ✅ Real | Dinâmica e também usada no algoritmo |
| Área exibida no dashboard | ✅ Real | Vem do cálculo do backend, não do cálculo visual do frontend |
| Estágio exibido no dashboard | ✅ Real | Inferido pelo backend a partir da data de plantio |

---

## Conclusão específica sobre a estrutura dos dados do front

O front hoje entrega um payload válido, consistente e suficiente para acionar o pipeline real. Então a resposta curta é: sim, a estrutura está boa para o MVP e a integração com o backend funciona de forma organizada.

Mas há três pontos importantes:

1. nem tudo que o usuário preenche influencia a análise
2. parte do que aparece dinâmico na interface é só informacional
3. ainda faltam entradas relevantes de negócio, como irrigação e estágio manual, para dizer que o formulário está totalmente conectado ao algoritmo

Em resumo, o fluxo está bem estruturado tecnicamente, mas ainda parcialmente aproveitado pelo motor de decisão.

---

## O que já está bom para MVP

- fluxo ponta a ponta funcionando
- análise territorial por polígono
- motor de score com critérios explícitos
- resposta legível e visual
- chat contextual integrado
- fallback suficiente para demonstração mesmo sem todas as APIs operando

---

## O que falta para elevar a maturidade dos dados

1. estabilizar o Earth Engine em ambiente real
2. ampliar base municipal além do recorte atual
3. trocar o lookup por proximidade por interseção espacial robusta
4. ampliar cobertura do ZARC local
5. integrar histórico de produtividade real
6. persistir histórico de análises e conversas
7. adicionar observabilidade sobre quando cada resposta veio de dado real ou fallback

---

## Conclusão

Hoje o SafraViva já tem uma espinha dorsal técnica real. A principal diferença entre uma demo convincente e uma operação mais confiável está na consolidação das fontes externas. O sistema não está preso em mock estático; ele já está preparado para consumir clima, satélite e IA de forma integrada, mas ainda convive com fallbacks importantes em clima, território e histórico produtivo.
