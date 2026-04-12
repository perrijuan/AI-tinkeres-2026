# SafraViva Backend (MVP)

Backend do MVP focado em transformar entrada geoespacial + contexto agrícola em payload pronto para o frontend.

## Stack

- Python 3.11+
- FastAPI
- Uvicorn

## Rodando localmente

1. Instale dependências:

```bash
pip install -e .
```

2. Suba a API:

```bash
uvicorn src.main:app --reload --port 8000
```

3. Teste saúde:

```bash
curl http://localhost:8000/health
```

4. Teste análise:

```bash
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Content-Type: application/json" \
  -d @docs/example_request.json
```

## Testes

```bash
python -m unittest discover -s tests
```

## Endpoint principal

- `POST /api/v1/analysis`
- Alias: `POST /api/v1/analyze`

Retorna:
- `field_info`
- `summary`
- `metrics`
- `risk_flags`
- `forecast_timeseries`
- `map_layer`
- `copilot_response`

## Estrutura

```text
backend/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── docs/
├── notebooks/
├── output/
│   ├── climate/
│   ├── maps/
│   └── app/
├── src/
│   ├── ingest/
│   ├── features/
│   ├── scoring/
│   ├── utils/
│   ├── main.py
│   ├── pipeline.py
│   └── schemas.py
└── tests/
```

## Observações de MVP

- O forecast climático está em modo operacional simplificado/determinístico para demo.
- O módulo já foi estruturado para encaixar ingestão real de GFS/ZARC/PAM sem quebrar contrato.
- Lookup municipal usa pontos de municípios de MT em `data/raw/municipios_mt.geojson`.
