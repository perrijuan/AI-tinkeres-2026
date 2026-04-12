# Arquitetura de Integrações Externas — SafraViva

> Documento criado a partir da análise do código atual em 2026-04-12.

## Objetivo

Este arquivo descreve como o SafraViva pega o que já existe internamente no projeto e integra com serviços externos, principalmente:

- Google Earth Engine
- Gemini

A ideia aqui não é só listar endpoints ou arquivos, mas mostrar a lógica de integração, o desenho arquitetural atual, os pontos fortes, os gargalos e o caminho natural de evolução.

---

## Leitura executiva

Hoje o SafraViva já possui uma arquitetura de integração bem definida para um MVP:

- o frontend coleta contexto do usuário e geometria da área
- o backend transforma isso em contexto espacial estruturado
- o pipeline tenta enriquecer a análise com serviços externos
- se a integração externa falha, o sistema cai para fallback controlado
- a resposta volta ao frontend em um contrato único
- esse mesmo contrato também alimenta a camada conversacional da Safrinia

Em termos práticos, a arquitetura já foi pensada para não quebrar quando uma dependência externa estiver indisponível. Esse é um ponto forte do projeto.

---

## Visão macro

```text
Usuário
  ↓
Frontend React/Vite
  ↓
POST /api/v1/analysis
  ↓
Backend FastAPI
  ↓
Pipeline de análise
  ├─ contexto espacial local
  ├─ integração com Google Earth Engine
  ├─ integração com datasets locais
  ├─ motor de risco e explicação
  └─ abertura de conversa com Gemini
  ↓
JSON unificado para o dashboard
  ↓
Frontend exibe mapa, métricas, score e chat
```

---

## O que o sistema já tem internamente

Antes de falar das integrações, vale separar o que já é domínio próprio do projeto.

### Núcleo interno

- contrato de entrada e saída via Pydantic
- cálculo geométrico da área
- derivação de centroide e bounding box
- lookup de município usando base local
- contexto agronômico por cultura
- leitura local de ZARC
- score de risco
- alertas e recomendação
- camada de resposta para o frontend
- criação da sessão de conversa da Safrinia

### Leitura arquitetural

Isso significa que as integrações externas não são o produto inteiro. Elas enriquecem o produto. O coração do fluxo decisório já está no código do próprio SafraViva.

Esse desenho é saudável porque:

- reduz acoplamento
- permite fallback
- facilita testes
- mantém uma fronteira clara entre domínio próprio e dependências externas

---

## Integração 1 — Google Earth Engine

## Papel do GEE no sistema

O Earth Engine entra como motor de dados geoespaciais e climáticos.

Hoje ele é usado em dois pontos:

1. clima
2. contexto territorial por satélite

---

## Fluxo de integração com GEE

### 1. Recebimento da geometria

O frontend envia um `Polygon` em GeoJSON no payload da análise.

### 2. Derivação espacial

O backend calcula:

- centroide
- bounding box
- área
- município aproximado

### 3. Conversão para geometria do Earth Engine

Em `backend/src/ingest/gee_client.py`, a geometria do usuário é convertida para `ee.Geometry.Polygon`.

### 4. Inicialização do cliente

O método `get_ee_client()` tenta inicializar o Earth Engine usando:

- service account
- chave JSON inline
- application default credentials
- default auth, se explicitamente habilitado

### 5. Uso em clima

Em `backend/src/ingest/climate_forecast.py`, o sistema consulta:

- `NOAA/GFS0P25`

Ele extrai:

- precipitação
- temperatura
- umidade
- vento

Depois agrega isso para:

- chuva em 7 dias
- chuva em 14 dias
- temperatura média em 7 dias
- temperatura máxima em 7 dias
- umidade média em 7 dias
- vento médio em 7 dias
- série temporal de 14 dias

### 6. Uso em satélite

Em `backend/src/ingest/territorial_context.py`, o sistema consulta:

- `MODIS/061/MOD13Q1`
- `MODIS/061/MOD11A2`
- `COPERNICUS/S2_SR_HARMONIZED`

E extrai:

- NDVI
- EVI
- LST
- cobertura média de nuvens
- data da última imagem
- série temporal curta de NDVI

### 7. Saída normalizada

Tanto no clima quanto no satélite, o backend transforma o retorno do GEE em um dicionário padronizado, que depois é consumido pelo restante do pipeline.

Essa padronização é importante porque o motor de risco não precisa saber se o dado veio do GEE ou do fallback. Ele consome um contrato interno consistente.

---

## Estratégia de fallback do GEE

Esse é um dos melhores pontos do desenho atual.

Se o Earth Engine falhar por qualquer motivo:

- credencial ausente
- projeto não habilitado
- coleção sem dados
- banda diferente do esperado
- erro de inicialização

o sistema não quebra. Em vez disso:

- o clima vira sintético determinístico
- o território vira sintético determinístico

### Por que isso é bom

- garante demo ponta a ponta
- evita tela vazia
- preserva contrato com o frontend
- reduz dependência operacional durante desenvolvimento

### Limite dessa abordagem

O fallback ajuda na experiência, mas pode mascarar a diferença entre dado real e dado sintético se o time não monitorar isso com clareza no produto.

---

## Integração 2 — Gemini

## Papel do Gemini no sistema

O Gemini entra em duas frentes diferentes:

1. chat contextual da Safrinia
2. enriquecimento do endpoint de mock legado

O uso mais importante hoje é o chat.

---

## Fluxo da Safrinia com Gemini

### 1. Análise concluída

Depois que o pipeline termina, o backend chama `start_conversation(analysis_payload)`.

### 2. Geração do contexto base

O arquivo `backend/chat_session.py` monta um `system prompt` com:

- propriedade
- cultura
- área
- município
- estágio da cultura
- irrigação
- score de risco
- alerta principal
- recomendação
- métricas climáticas
- fatores de risco ativos

### 3. Criação da conversa

Uma sessão é criada em memória com:

- `conversation_id`
- `system`
- `history`
- `created_at`

### 4. Uso pelo frontend

O frontend recebe o `conversation_id` na análise e, quando o usuário abre o painel da Safrinia, envia mensagens para `POST /chat`.

### 5. Chamada ao Gemini

O backend:

- valida `GEMINI_API_KEY`
- instancia `google.generativeai`
- abre um chat com `system_instruction`
- envia a mensagem do usuário
- salva o histórico em memória
- retorna a resposta já pronta para o frontend

---

## Pontos fortes da integração com Gemini

- usa o contexto real da análise, não um prompt genérico
- transforma o dashboard em experiência conversacional
- não exige remontar toda a análise a cada pergunta
- mantém um `conversation_id` simples e direto

## Limitações atuais

- histórico em memória apenas
- dependência de uma biblioteca já marcada no código como sujeita a deprecação futura
- sem controle de custo, tokens, retries ou observabilidade fina
- sem persistência por usuário

---

## Integração 3 — Datasets locais como ponte entre interno e externo

Além de APIs externas, o projeto também usa bases locais que funcionam como uma camada intermediária importante.

### Bases locais já plugadas

- `backend/dataset/zarc_mt_consolidado.csv`
- `backend/data/raw/municipios_mt.geojson`

### Papel dessas bases

- completar o contexto agrícola nacional
- reduzir dependência externa em partes críticas
- permitir resposta útil mesmo sem internet ou sem GEE funcional

### Leitura arquitetural

Esses datasets são uma espécie de "camada de soberania" do produto. Mesmo em um MVP, isso é valioso porque evita colocar todo o valor do sistema na mão de terceiros.

---

## Como tudo se encaixa no pipeline

## Sequência real

1. frontend envia cultura, data e polígono
2. backend deriva contexto espacial
3. backend tenta buscar clima no GEE
4. backend tenta buscar satélite no GEE
5. backend combina isso com ZARC e contexto agronômico local
6. backend calcula score e flags
7. backend monta textos de alerta e resposta do copiloto
8. backend devolve um JSON único para o frontend
9. backend abre uma sessão contextual para a Safrinia
10. frontend usa esse mesmo contexto para conversa via Gemini

### Consequência positiva

O projeto já evita um problema comum em MVPs com IA: o chat não é uma ilha. Ele nasce da mesma análise que alimenta o dashboard.

---

## Qual é a lógica de integração de verdade

Se resumirmos o desenho atual em uma frase:

> o SafraViva usa serviços externos para enriquecer sinais, mas mantém internamente a responsabilidade por interpretar esses sinais e transformá-los em decisão.

Isso é uma escolha muito boa.

O GEE não decide o risco.

O Gemini não decide o risco.

Quem decide é o núcleo do SafraViva, com:

- regras agronômicas
- score
- alertas
- explicação estruturada

Os serviços externos entram como provedores de insumo e interface conversacional.

---

## Riscos arquiteturais atuais

## 1. Dependência silenciosa de fallback

O sistema pode parecer funcional mesmo quando o GEE falha, porque o fallback mantém tudo de pé. Isso é ótimo para demo, mas perigoso para validação de qualidade se o time não souber claramente qual análise foi real e qual foi sintética.

## 2. Persistência fraca no chat

O uso em memória é suficiente para MVP, mas inviável para continuidade real de conversa, auditoria, analytics e multiusuário.

## 3. Lookup municipal simplificado

Hoje o município é estimado por ponto mais próximo. Isso pode funcionar bem em muitos casos, mas não é a forma espacialmente mais robusta para produção.

## 4. Histórico produtivo ainda artificial

O score já usa histórico, mas essa parte ainda não representa uma fonte agrícola operacional real. Isso reduz a confiança analítica do sistema quando o produto for cobrado por explicabilidade mais forte.

## 5. Biblioteca do Gemini

O projeto usa `google-generativeai`, enquanto o próprio código já sinaliza risco de deprecação futura. Isso sugere a necessidade de uma camada de abstração maior para o LLM provider.

---

## Evolução arquitetural recomendada

## Curto prazo

1. explicitar no payload quando cada bloco veio de `real`, `synthetic` ou `heuristic`
2. persistir conversas em Redis ou banco
3. registrar status de inicialização do GEE no healthcheck
4. separar melhor mock legado e pipeline v1

## Médio prazo

1. criar um `integration layer` mais explícito para provedores externos
2. desacoplar Gemini por meio de um adapter de LLM
3. trocar o lookup municipal por interseção geoespacial
4. adicionar fonte histórica real de produtividade

## Longo prazo

1. versionar fontes e modelos usados em cada análise
2. armazenar trilha completa de auditoria
3. suportar reprocessamento de uma análise com novas fontes
4. evoluir para arquitetura orientada a jobs assíncronos

---

## Proposta de arquitetura-alvo

```text
Frontend
  ↓
API Gateway / FastAPI
  ↓
Orchestrator de análise
  ├─ Spatial Service
  ├─ Climate Provider Adapter
  ├─ Satellite Provider Adapter
  ├─ Agro Rules Engine
  ├─ Historical Data Service
  ├─ Risk Engine
  └─ Copilot Context Builder
        ↓
     Chat Service / LLM Adapter
        ↓
Persistência
  ├─ análises
  ├─ conversas
  └─ metadados de fontes
```

### Vantagem desse desenho

Ele preserva o que já está bom no projeto atual, mas deixa mais clara a fronteira entre:

- dados
- regras de negócio
- IA generativa
- persistência

---

## Conclusão

O SafraViva já tem uma arquitetura inteligente para integrar serviços externos sem perder o controle do produto. O projeto não terceiriza sua lógica principal para GEE ou Gemini; ele usa esses serviços como extensões do motor interno.

Isso é exatamente o que um bom MVP técnico deveria fazer:

- usar provedores fortes onde faz sentido
- manter o domínio de negócio dentro de casa
- degradar com elegância quando uma dependência falha

O próximo salto de maturidade não é reinventar a base. É consolidar observabilidade, persistência e clareza sobre a proveniência dos dados.
