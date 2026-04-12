from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.pipeline import analyze_field
from src.schemas import AnalysisRequest, AnalysisResponse
from src.utils.time import to_iso_z


app = FastAPI(
    title="SafraViva Backend API",
    description="Copiloto climático do agro para cálculo de risco do MVP.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "safraviva-backend",
        "timestamp": to_iso_z(datetime.now(timezone.utc)),
    }


@app.post("/api/v1/analysis", response_model=AnalysisResponse)
def post_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    try:
        response = analyze_field(payload)
        return AnalysisResponse(**response)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Erro interno na análise: {error}") from error


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
def post_analyze_alias(payload: AnalysisRequest) -> AnalysisResponse:
    return post_analysis(payload)
