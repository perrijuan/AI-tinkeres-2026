import os

from fastapi import APIRouter

from ai_mock import generate_ai_analysis
from mock import get_mock_analysis
from chat_session import start_conversation

router = APIRouter()


@router.post("/mock/analysis")
def mock_analysis(payload: dict):
    # Tenta gerar dados realistas via Gemini; cai no mock fixo se falhar
    if os.environ.get("GEMINI_API_KEY"):
        try:
            analysis = generate_ai_analysis(payload)
        except Exception as e:
            print(f"[ai_mock] Gemini falhou, usando mock fixo: {e}")
            analysis = get_mock_analysis(payload)
    else:
        analysis = get_mock_analysis(payload)

    try:
        analysis["conversation_id"] = start_conversation(analysis)
    except Exception as e:
        print(f"[chat] Falha ao criar sessão: {e}")

    return analysis
