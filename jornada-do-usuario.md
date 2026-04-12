# Jornada do Usuário — SafraViva

> Atualizado com base no código atual do repositório em 2026-04-12.

## Visão geral

Hoje, a jornada implementada no produto é uma experiência de demonstração guiada:

1. o usuário entra pela landing page
2. inicia uma nova análise em `/demo`
3. preenche dados básicos em 3 etapas
4. desenha o polígono da área no mapa
5. envia a análise para o backend
6. recebe um dashboard com score, métricas, mapa, explicação e chat com a Safrinia

O fluxo atual é voltado a demonstração de valor do produto, não a operação corporativa multiusuário. Por isso, ainda não existem login, carteira de propriedades, relatórios exportáveis, histórico persistido ou gestão de alertas por conta.

---

## Persona principal do MVP

### João, produtor ou técnico de campo

- Quer entender rapidamente se a área está entrando em risco climático.
- Não quer interpretar dado bruto de clima, satélite e ZARC separadamente.
- Precisa de uma resposta objetiva: qual o risco, por que isso está acontecendo e o que fazer agora.

### Persona secundária

### Ana, analista técnica ou de risco

- Usa a plataforma para leitura rápida de uma área específica.
- Quer uma síntese visual e explicável.
- Se beneficia do copiloto para explorar dúvidas sobre a análise gerada.

---

## Jornada real implementada

## Etapa 1 — Entrada na plataforma

O usuário acessa a landing page e segue para uma nova análise.

### O que existe no código

- Frontend com rotas principais:
- `/` para apresentação do produto
- `/demo` para captura dos dados
- `/resultado` para exibição da análise

### Objetivo da etapa

Levar o usuário rapidamente para a análise, sem barreira de autenticação.

---

## Etapa 2 — Preenchimento dos dados básicos

Na tela `/demo`, o usuário passa por um fluxo em 3 passos.

### Passo 1 — Seus dados

O usuário informa:

- nome
- empresa ou propriedade
- e-mail
- data de plantio

### Leitura de produto

- Nome e e-mail são usados para compor a experiência.
- `property_name` é enviado ao backend.
- Não há persistência de cadastro.

---

## Etapa 3 — Seleção da cultura

No segundo passo, o frontend busca a lista de culturas em `GET /culturas`.

### Culturas expostas hoje

- soja
- milho
- algodão
- arroz
- feijão
- trigo
- cana-de-açúcar
- girassol
- sorgo
- amendoim

### Observação importante

Nem todas as culturas têm o mesmo nível de profundidade agronômica no backend. Os perfis explícitos de risco estão mais maduros para:

- soja
- milho
- algodão

As demais culturas usam fallback de perfil padrão.

---

## Etapa 4 — Delimitação da área

No terceiro passo, o usuário desenha manualmente um polígono no mapa.

### O que o sistema faz

- registra os vértices clicados no mapa
- fecha o polígono automaticamente
- calcula a área em hectares no frontend
- envia a geometria em GeoJSON para o backend

### Valor percebido pelo usuário

Ele sente que a análise é territorial e localizada, não uma previsão genérica por município.

---

## Etapa 5 — Envio da análise

Ao confirmar, o frontend envia um `POST /api/v1/analysis` com:

- `field_id`
- `property_name`
- `culture`
- `sowing_date`
- `crop_stage` como `null`
- `irrigated`
- `analysis_timestamp`
- `geometry`

### O que acontece no backend

O pipeline executa, em sequência:

1. derivação espacial
2. clima
3. contexto territorial
4. contexto agro
5. score de risco
6. alertas e recomendação
7. camada de mapa
8. montagem da resposta para o frontend
9. criação opcional de uma sessão de conversa para a Safrinia

---

## Etapa 6 — Dashboard de resultado

Depois da análise, o usuário é levado para `/resultado`.

### O que ele vê hoje

- score de risco de 0 a 100
- nível de risco
- alerta principal
- ação recomendada
- dados da propriedade
- métricas climáticas de 7 e 14 dias
- flags de risco
- gráfico de previsão
- gráfico de NDVI, quando disponível
- bloco explicativo da Safrinia
- fontes de dados
- polígono da área no mapa

### Leitura de experiência

Essa é a parte mais forte do produto hoje. A proposta de valor fica clara porque o sistema não entrega só métrica: ele entrega interpretação.

---

## Etapa 7 — Conversa com a Safrinia

Se a análise conseguir abrir uma sessão de conversa, o usuário pode clicar em "Fale com a Safrinia".

### Como funciona

- o backend cria um `conversation_id`
- esse id é retornado junto da análise
- o chat usa `POST /chat`
- o contexto inicial da análise vira um `system prompt`
- as respostas são geradas pelo Gemini

### Valor para o usuário

- explorar dúvidas específicas da área
- transformar o dashboard em conversa
- pedir explicações adicionais sem navegar em múltiplos painéis

### Limitação atual

- o histórico fica em memória
- se o servidor reiniciar, a conversa é perdida
- ainda não existe persistência em banco ou Redis

---

## Jornada resumida em uma linha

O usuário informa cultura e área, o backend cruza contexto espacial, clima, satélite e ZARC, calcula risco e devolve uma análise explicada, com possibilidade de aprofundamento via chat.

---

## O que a jornada atual faz bem

- reduz atrito de entrada
- demonstra valor em poucos passos
- conecta mapa, score e explicação em uma narrativa única
- cria percepção de inteligência aplicada, e não só visualização

## O que ainda não existe na jornada

- autenticação
- múltiplas propriedades por usuário
- histórico de análises
- comparação entre análises
- exportação de relatório
- gestão de alertas persistidos
- carteira institucional

---

## Próxima evolução recomendada

### Jornada v2

1. cadastro ou identificação simples do usuário
2. salvamento das áreas analisadas
3. histórico por propriedade
4. reanálise automática por janela de tempo
5. alertas proativos
6. relatório compartilhável
7. camada institucional para cooperativa, seguradora ou assistência técnica

---

## Conclusão

A jornada implementada hoje é enxuta, coerente com um MVP e bem alinhada ao discurso do produto. O que o código entrega de verdade é uma demo funcional orientada a análise pontual de uma área, com forte componente visual e uma camada conversacional apoiada por IA.
