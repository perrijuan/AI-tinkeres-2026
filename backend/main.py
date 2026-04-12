from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mock import get_mock_analysis

app = FastAPI(title="SafraViva API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CULTURAS = [
    {"id": "soja",        "label": "Soja"},
    {"id": "milho",       "label": "Milho"},
    {"id": "algodao",     "label": "Algodão"},
    {"id": "arroz",       "label": "Arroz"},
    {"id": "feijao",      "label": "Feijão"},
    {"id": "trigo",       "label": "Trigo"},
    {"id": "cana",        "label": "Cana-de-açúcar"},
    {"id": "girassol",    "label": "Girassol"},
    {"id": "sorgo",       "label": "Sorgo"},
    {"id": "amendoim",    "label": "Amendoim"},
]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/culturas")
def culturas():
    return CULTURAS


@app.post("/mock/analysis")
def mock_analysis(payload: dict):
    return get_mock_analysis(payload)
