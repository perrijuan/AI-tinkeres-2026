import csv
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


@lru_cache(maxsize=1)
def _load_zarc_rows() -> list[dict[str, Any]]:
    backend_root = Path(__file__).resolve().parents[2]
    zarc_path = backend_root / "dataset" / "zarc_mt_consolidado.csv"
    if not zarc_path.exists():
        return []

    encodings = ["utf-8-sig", "latin-1"]
    for encoding in encodings:
        try:
            with zarc_path.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)
                rows = []
                for row in reader:
                    municipio = row.get("Município") or row.get("MunicÃ­pio") or row.get("Municipio")
                    cultura = row.get("Natura_Maior")
                    risco = row.get("Risco_Plantio_Perc")
                    rows.append(
                        {
                            "municipio_norm": _normalize_text(municipio),
                            "cultura_norm": _normalize_text(cultura),
                            "cultura_label": (cultura or "").strip(),
                            "risco_plantio_perc": float(risco) if risco not in (None, "") else None,
                        }
                    )
                return rows
        except Exception:
            continue
    return []


def _zarc_class_from_risk(risk_percent: float) -> tuple[int, str]:
    if risk_percent <= 20:
        return 1, "Baixo"
    if risk_percent <= 30:
        return 2, "Moderado"
    if risk_percent <= 40:
        return 3, "Alto"
    if risk_percent <= 50:
        return 4, "Muito Alto"
    return 5, "Critico"


def get_zarc_context(culture: str, municipio: str, sowing_date: str, heuristic_zarc_flag: bool) -> dict[str, Any]:
    rows = _load_zarc_rows()
    municipio_norm = _normalize_text(municipio)
    culture_norm = _normalize_text(culture)
    municipio_rows = [row for row in rows if row["municipio_norm"] == municipio_norm]
    culture_rows = [row for row in municipio_rows if row["cultura_norm"] == culture_norm]

    if culture_rows:
        risks = [row["risco_plantio_perc"] for row in culture_rows if row["risco_plantio_perc"] is not None]
        if risks:
            risk_percent = sum(risks) / len(risks)
            zarc_class, zarc_label = _zarc_class_from_risk(risk_percent)
            zarc_flag = risk_percent <= 30
            return {
                "source": "dataset",
                "provider": "MAPA ZARC (dataset local)",
                "culture_match": True,
                "risk_plantio_perc": round(risk_percent, 2),
                "zarc_class": zarc_class,
                "zarc_label": zarc_label,
                "zarc_flag": zarc_flag,
                "signals": [
                    f"Risco medio de plantio no ZARC local: {round(risk_percent, 1)}%.",
                    f"Classificacao ZARC local: {zarc_label}.",
                    f"Data de plantio informada: {sowing_date}.",
                ],
            }

    if municipio_rows:
        return {
            "source": "dataset_partial",
            "provider": "MAPA ZARC (dataset local)",
            "culture_match": False,
            "risk_plantio_perc": None,
            "zarc_class": 3,
            "zarc_label": "Moderado",
            "zarc_flag": heuristic_zarc_flag,
            "signals": [
                "Dataset ZARC encontrado para o municipio, mas sem linha especifica para esta cultura.",
                f"Aplicado fallback heuristico para cultura {culture}.",
                f"Data de plantio informada: {sowing_date}.",
            ],
        }

    return {
        "source": "heuristic",
        "provider": "SafraViva Heuristic ZARC",
        "culture_match": False,
        "risk_plantio_perc": None,
        "zarc_class": 3 if heuristic_zarc_flag else 4,
        "zarc_label": "Moderado" if heuristic_zarc_flag else "Alto",
        "zarc_flag": heuristic_zarc_flag,
        "signals": [
            "Nao foi encontrado registro no dataset ZARC local para o municipio/cultura.",
            "Aplicado fallback heuristico de janela de plantio.",
            f"Data de plantio informada: {sowing_date}.",
        ],
    }

