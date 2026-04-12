import csv
import re
import unicodedata
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def _row_get(row: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return str(row[key])
    return None


def _parse_safra_years(safra_text: str | None) -> tuple[int | None, int | None]:
    if not safra_text:
        return None, None
    years = re.findall(r"\d{4}", safra_text)
    if not years:
        return None, None
    start_year = int(years[0])
    end_year = int(years[1]) if len(years) > 1 else start_year
    return start_year, end_year


@lru_cache(maxsize=1)
def _load_zarc_rows() -> list[dict[str, Any]]:
    backend_root = Path(__file__).resolve().parents[2]
    zarc_path = backend_root / "dataset" / "base_agricola.csv"
    if not zarc_path.exists():
        return []

    encodings = ["utf-8-sig", "latin-1"]
    for encoding in encodings:
        try:
            with zarc_path.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)
                rows = []
                for row in reader:
                    municipio = _row_get(row, ["Municipio", "Município", "MunicÃ­pio", "MunicÃƒÂ­pio"])
                    cultura = _row_get(row, ["Cultura", "Natura_Maior", "Natura Maior"])
                    safra = _row_get(row, ["Safra"])
                    uf = _row_get(row, ["UF"])
                    grupo = _row_get(row, ["Grupo"])
                    solo = _row_get(row, ["Solo"])
                    manejo = _row_get(row, ["Outros manejos", "Outros Manejos"])
                    safra_start, safra_end = _parse_safra_years(safra)
                    rows.append(
                        {
                            "uf_norm": _normalize_text(uf),
                            "municipio_norm": _normalize_text(municipio),
                            "cultura_norm": _normalize_text(cultura),
                            "safra_raw": (safra or "").strip(),
                            "safra_start": safra_start,
                            "safra_end": safra_end,
                            "cultura_label": (cultura or "").strip(),
                            "grupo": (grupo or "").strip(),
                            "solo": (solo or "").strip(),
                            "manejo": (manejo or "").strip(),
                        }
                    )
                return rows
        except Exception:
            continue
    return []


def _latest_safra(rows: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    best_start: int | None = None
    best_end: int | None = None
    for row in rows:
        start = row.get("safra_start")
        end = row.get("safra_end")
        if start is None:
            continue
        if best_start is None or (start, end or start) > (best_start, best_end or best_start):
            best_start = int(start)
            best_end = int(end) if end is not None else int(start)
    return best_start, best_end


def _filter_latest_safra(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safra_start, safra_end = _latest_safra(rows)
    if safra_start is None:
        return rows
    return [
        row
        for row in rows
        if row.get("safra_start") == safra_start and row.get("safra_end", row.get("safra_start")) == safra_end
    ]


def _parse_sowing_date(sowing_date: str) -> date | None:
    try:
        return date.fromisoformat(sowing_date)
    except ValueError:
        return None


def _culture_aliases(culture_norm: str) -> set[str]:
    aliases = {culture_norm}
    if "soja" in culture_norm:
        aliases.add("soja")
    if "milho" in culture_norm:
        aliases.update({"milho", "milho 1a safra", "milho 1 safra"})
    if "algod" in culture_norm:
        aliases.update({"algodao", "algodao herbaceo"})
    return aliases


def _culture_matches(culture_norm: str, row_culture_norm: str) -> bool:
    if not culture_norm or not row_culture_norm:
        return False
    aliases = _culture_aliases(culture_norm)
    if row_culture_norm in aliases:
        return True
    if culture_norm in row_culture_norm:
        return True
    for alias in aliases:
        if alias and alias in row_culture_norm:
            return True
    return False


def _build_dataset_partial_response(
    source: str,
    heuristic_zarc_flag: bool,
    culture: str,
    sowing_date: str,
    detail: str,
) -> dict[str, Any]:
    return {
        "source": source,
        "provider": "MAPA ZARC (base_agricola.csv)",
        "culture_match": False,
        "risk_plantio_perc": None,
        "zarc_class": 3,
        "zarc_label": "Moderado",
        "zarc_flag": heuristic_zarc_flag,
        "signals": [
            detail,
            f"Aplicado fallback heuristico para cultura {culture}.",
            f"Data de plantio informada: {sowing_date}.",
        ],
    }


def get_zarc_context(
    culture: str,
    municipio: str,
    sowing_date: str,
    heuristic_zarc_flag: bool,
    uf: str = "MT",
) -> dict[str, Any]:
    rows = _load_zarc_rows()
    uf_norm = _normalize_text(uf)
    municipio_norm = _normalize_text(municipio)
    culture_norm = _normalize_text(culture)
    sowing = _parse_sowing_date(sowing_date)

    uf_rows = [row for row in rows if row["uf_norm"] == uf_norm]
    municipio_rows = [row for row in uf_rows if row["municipio_norm"] == municipio_norm]
    culture_rows = [row for row in municipio_rows if _culture_matches(culture_norm, row["cultura_norm"])]

    if culture_rows:
        latest_rows = _filter_latest_safra(culture_rows)
        safra_start, safra_end = _latest_safra(latest_rows)
        sowing_within_safra = True
        if sowing and safra_start is not None and safra_end is not None:
            sowing_within_safra = safra_start <= sowing.year <= safra_end
        zarc_flag = bool(sowing_within_safra)
        zarc_class = 2 if zarc_flag else 4
        zarc_label = "Apto" if zarc_flag else "Fora da safra de referencia"
        group_values = sorted({row["grupo"] for row in latest_rows if row.get("grupo")})
        soil_values = sorted({row["solo"] for row in latest_rows if row.get("solo")})
        safra_label = latest_rows[0].get("safra_raw") if latest_rows else None
        return {
            "source": "dataset",
            "provider": "MAPA ZARC (base_agricola.csv)",
            "culture_match": True,
            "risk_plantio_perc": None,
            "zarc_class": zarc_class,
            "zarc_label": zarc_label,
            "zarc_flag": zarc_flag,
            "matched_rows": len(latest_rows),
            "safra_ref": safra_label,
            "groups": group_values,
            "soil_classes": soil_values,
            "signals": [
                f"Filtro ZARC aplicado por local/cultura na safra mais recente: {safra_label or 'nao identificada'}.",
                f"Municipio: {municipio}. Cultura: {culture}.",
                f"Data de plantio informada: {sowing_date}.",
            ],
        }

    if municipio_rows:
        return _build_dataset_partial_response(
            source="dataset_partial",
            heuristic_zarc_flag=heuristic_zarc_flag,
            culture=culture,
            sowing_date=sowing_date,
            detail="Dataset ZARC encontrado para o municipio, mas sem linha especifica para esta cultura.",
        )

    if uf_rows:
        return _build_dataset_partial_response(
            source="dataset_partial_uf",
            heuristic_zarc_flag=heuristic_zarc_flag,
            culture=culture,
            sowing_date=sowing_date,
            detail="Dataset ZARC encontrado na UF, mas sem linha para este municipio/cultura.",
        )

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
