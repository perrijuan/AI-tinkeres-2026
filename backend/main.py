<<<<<<< Updated upstream
=======
﻿import os
from typing import Any

>>>>>>> Stashed changes
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

<<<<<<< Updated upstream
from routers import health, culturas, analysis, chat
=======
from chat import send_message, start_conversation
from copilot import generate_copilot_response
from mock import get_mock_analysis
from src.pipeline import analyze_field
from src.schemas import AnalysisRequest, AnalysisResponse
>>>>>>> Stashed changes

load_dotenv()

app = FastAPI(title="SafraViva API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< Updated upstream
app.include_router(health.router)
app.include_router(culturas.router)
app.include_router(analysis.router)
app.include_router(chat.router)
=======

class ChatRequest(BaseModel):
    conversation_id: str
    message: str


CULTURAS = [
    {"id": "soja", "label": "Soja", "emoji": "🌱"},
    {"id": "milho", "label": "Milho", "emoji": "🌽"},
    {"id": "algodao", "label": "Algodão", "emoji": "🌿"},
    {"id": "arroz", "label": "Arroz", "emoji": "🌾"},
    {"id": "feijao", "label": "Feijão", "emoji": "🫘"},
    {"id": "trigo", "label": "Trigo", "emoji": "🌾"},
    {"id": "cana", "label": "Cana-de-açúcar", "emoji": "🎋"},
    {"id": "girassol", "label": "Girassol", "emoji": "🌻"},
    {"id": "sorgo", "label": "Sorgo", "emoji": "🌾"},
    {"id": "amendoim", "label": "Amendoim", "emoji": "🥜"},
]


def _is_new_contract_payload(payload: dict[str, Any]) -> bool:
    required_fields = {"geometry", "culture", "sowing_date", "analysis_timestamp"}
    return required_fields.issubset(payload.keys())


def _enrich_with_copilot_and_chat(analysis: dict[str, Any]) -> dict[str, Any]:
    if os.environ.get("GEMINI_API_KEY"):
        try:
            analysis["copilot_response"] = generate_copilot_response(analysis)
        except Exception as error:
            print(f"[copilot] Gemini failed, keeping default response: {error}")

    try:
        analysis["conversation_id"] = start_conversation(analysis)
    except Exception as error:
        print(f"[chat] Failed to create conversation: {error}")

    return analysis


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/culturas")
def culturas() -> list[dict[str, str]]:
    return CULTURAS


@app.post("/mock/analysis")
def mock_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    if _is_new_contract_payload(payload):
        analysis = analyze_field(payload)
    else:
        analysis = get_mock_analysis(payload)
    return _enrich_with_copilot_and_chat(analysis)


@app.post("/api/v1/analysis", response_model=AnalysisResponse)
def api_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    try:
        analysis = analyze_field(payload)
        return AnalysisResponse(**analysis)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Erro interno na análise: {error}") from error


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
def api_analyze_alias(payload: AnalysisRequest) -> AnalysisResponse:
    return api_analysis(payload)


@app.post("/chat")
def chat(req: ChatRequest) -> dict[str, Any]:
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY não configurada.")
    try:
        return send_message(req.conversation_id, req.message)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
>>>>>>> Stashed changes
