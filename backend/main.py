from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers import analysis, chat, culturas, health
from src.pipeline import analyze_field
from src.schemas import AnalysisRequest, AnalysisResponse

load_dotenv()

app = FastAPI(title="SafraViva API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(culturas.router)
app.include_router(analysis.router)
app.include_router(chat.router)


@app.post("/api/v1/analysis", response_model=AnalysisResponse)
def api_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    try:
        analysis_payload = analyze_field(payload)
        return AnalysisResponse(**analysis_payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Erro interno na analise: {error}") from error


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
def api_analyze_alias(payload: AnalysisRequest) -> AnalysisResponse:
    return api_analysis(payload)

