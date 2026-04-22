from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from google.cloud import bigquery
from dotenv import load_dotenv
import pandas as pd
import os
import ee
import requests
from datetime import datetime, timedelta

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET")
BQ_TABLE = os.getenv("BQ_TABLE")

if not all([GCP_PROJECT_ID, BQ_DATASET, BQ_TABLE]):
    raise RuntimeError("Configure GCP_PROJECT_ID, BQ_DATASET e BQ_TABLE no .env")

TABLE_ID = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

# ==============================
# FASTAPI
# ==============================
app = FastAPI(title="SafraViva API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# CLIENTS
# ==============================
def get_client():
    return bigquery.Client(project=GCP_PROJECT_ID)

def init_ee():
    try:
        ee.Initialize(project=GCP_PROJECT_ID)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=GCP_PROJECT_ID)

# ==============================
# HELPERS BQ
# ==============================
def normalize(df: pd.DataFrame):
    if df.empty:
        return df

    df["UF"] = df["UF"].astype(str).str.upper().str.strip()
    df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()
    df["Nome_cultura"] = df["Nome_cultura"].astype(str).str.upper().str.strip()
    df["geocodigo"] = df["geocodigo"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(7)
    return df

def build_query(filters: dict, limite: int):
    query = f"""
        SELECT
            UF,
            municipio,
            geocodigo,
            Nome_cultura,
            Cod_Solo,
            SafraIni,
            valor_frequencia
        FROM `{TABLE_ID}`
        WHERE 1=1
    """
    params = []

    def add(cond, name, dtype, value):
        nonlocal query
        query += f" AND {cond}"
        params.append(bigquery.ScalarQueryParameter(name, dtype, value))

    if filters.get("uf"):
        add("UPPER(UF) = @uf", "uf", "STRING", filters["uf"])

    if filters.get("municipio"):
        add("UPPER(municipio) = @municipio", "municipio", "STRING", filters["municipio"])

    if filters.get("cultura"):
        add("UPPER(Nome_cultura) = @cultura", "cultura", "STRING", filters["cultura"])

    if filters.get("cod_solo") is not None:
        add("Cod_Solo = @cod_solo", "cod_solo", "INT64", filters["cod_solo"])

    if filters.get("geocodigo"):
        add("CAST(geocodigo AS STRING) = @geocodigo", "geocodigo", "STRING", str(filters["geocodigo"]))

    if filters.get("safra_ini") is not None:
        add("SafraIni = @safra_ini", "safra_ini", "INT64", filters["safra_ini"])

    query += " LIMIT @limite"
    params.append(bigquery.ScalarQueryParameter("limite", "INT64", int(limite)))

    job_config = bigquery.QueryJobConfig(
        query_parameters=params,
        maximum_bytes_billed=10**9
    )
    return query, job_config

# ==============================
# GEE
# ==============================
class SafraVivaGEE:
    def __init__(self):
        init_ee()

    def decendio_to_dates(self, ano, decendio):
        mes = (decendio - 1) // 3 + 1
        dia_inicio = ((decendio - 1) % 3) * 10 + 1
        start_date = datetime(ano, mes, dia_inicio)
        end_date = start_date + timedelta(days=10)
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def get_municipio_geometry(self, geocodigo: str):
        cod = str(geocodigo).strip()
        if len(cod) != 7 or not cod.isdigit():
            raise ValueError("geocodigo deve ter 7 dígitos.")

        url = f"https://servicodados.ibge.gov.br/api/v3/malhas/municipios/{cod}?formato=application/vnd.geo+json"
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            raise ValueError(f"IBGE malha indisponível para {cod}")

        gj = r.json()
        if gj.get("type") == "FeatureCollection":
            feats = gj.get("features", [])
            if not feats:
                raise ValueError("GeoJSON vazio no IBGE.")
            geom = feats[0].get("geometry")
        elif gj.get("type") == "Feature":
            geom = gj.get("geometry")
        else:
            geom = gj if gj.get("type") in ("Polygon", "MultiPolygon") else None

        if not geom:
            raise ValueError("Geometria inválida do IBGE.")

        return ee.Geometry(geom)

    def prep_landsat_l2(self, image):
        qa = image.select("QA_PIXEL")
        cloud = qa.bitwiseAnd(1 << 3).eq(0)
        shadow = qa.bitwiseAnd(1 << 4).eq(0)
        cirrus = qa.bitwiseAnd(1 << 2).eq(0)
        mask = cloud.And(shadow).And(cirrus)

        optical = (
            image.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"])
            .multiply(0.0000275)
            .add(-0.2)
        )

        ndvi = optical.normalizedDifference(["SR_B5", "SR_B4"]).rename("qscore")

        return image.addBands(optical, overwrite=True).addBands(ndvi).updateMask(mask)

class SafraAnalysis:
    def __init__(self, table_id):
        self.table_id = table_id
        self.bq_client = get_client()
        self.gee = SafraVivaGEE()

    def get_zarc_data(self, geocodigo, safra, solo=3):
        query = f"""
            SELECT valor_frequencia, Nome_cultura
            FROM `{self.table_id}`
            WHERE CAST(geocodigo AS STRING) = @geo
              AND SafraIni = @safra
              AND Cod_Solo = @solo
            LIMIT 1
        """
        cfg = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("geo", "STRING", str(geocodigo)),
                bigquery.ScalarQueryParameter("safra", "INT64", int(safra)),
                bigquery.ScalarQueryParameter("solo", "INT64", int(solo)),
            ]
        )
        df = self.bq_client.query(query, job_config=cfg).result().to_dataframe()
        return df.iloc[0] if not df.empty else None

# ==============================
# KERNELS
# ==============================
def apply_kernel(image: ee.Image, kernel: str = "NONE", threshold: float = 0.35):
    k = (kernel or "NONE").upper()

    if k == "NONE":
        return image

    if k == "THRESHOLD":
        b = image.bandNames().get(0)
        th = ee.Number(threshold).multiply(10000)
        return image.select([b]).gt(th).selfMask().rename("threshold_mask")

    if k == "SOBEL":
        b = image.bandNames().get(0)
        return image.select([b]).convolve(ee.Kernel.sobel()).rename("sobel")

    return image

# ==============================
# ENDPOINTS
# ==============================
@app.get("/api/health")
def health():
    return {"status": "ok", "table": TABLE_ID}

@app.get("/api/zarc")
def zarc(
    uf: Optional[str] = None,
    municipio: Optional[str] = None,
    cultura: Optional[str] = None,
    cod_solo: Optional[int] = None,
    geocodigo: Optional[str] = None,
    safra_ini: Optional[int] = None,
    limite: int = 500
):
    if not any([uf, municipio, cultura, geocodigo]):
        raise HTTPException(status_code=400, detail="Informe ao menos um filtro")

    filters = {
        "uf": uf.upper() if uf else None,
        "municipio": municipio.upper() if municipio else None,
        "cultura": cultura.upper() if cultura else None,
        "cod_solo": cod_solo,
        "geocodigo": geocodigo.strip() if geocodigo else None,
        "safra_ini": safra_ini
    }

    try:
        query, cfg = build_query(filters, limite)
        df = get_client().query(query, job_config=cfg).result().to_dataframe()
        df = normalize(df)
        return {"total": len(df), "dados": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtros/ufs")
def listar_ufs():
    try:
        query = f"""
            SELECT DISTINCT UPPER(TRIM(UF)) AS UF
            FROM `{TABLE_ID}`
            WHERE UF IS NOT NULL AND TRIM(UF) <> ''
            ORDER BY UF
        """
        rows = get_client().query(query).result()
        return {"total": rows.total_rows, "dados": [r["UF"] for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtros/municipios")
def listar_municipios(uf: Optional[str] = None):
    try:
        query = f"""
            SELECT DISTINCT UPPER(TRIM(municipio)) AS municipio
            FROM `{TABLE_ID}`
            WHERE municipio IS NOT NULL AND TRIM(municipio) <> ''
        """
        params = []
        if uf:
            query += " AND UPPER(TRIM(UF)) = @uf"
            params.append(bigquery.ScalarQueryParameter("uf", "STRING", uf.upper().strip()))
        query += " ORDER BY municipio"

        cfg = bigquery.QueryJobConfig(query_parameters=params)
        rows = get_client().query(query, job_config=cfg).result()
        return {"total": rows.total_rows, "dados": [r["municipio"] for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtros/culturas")
def listar_culturas():
    try:
        query = f"""
            SELECT DISTINCT UPPER(TRIM(Nome_cultura)) AS cultura
            FROM `{TABLE_ID}`
            WHERE Nome_cultura IS NOT NULL AND TRIM(Nome_cultura) <> ''
            ORDER BY cultura
        """
        rows = get_client().query(query).result()
        return {"total": rows.total_rows, "dados": [r["cultura"] for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filtros/codigos")
def listar_codigos(
    uf: Optional[str] = None,
    municipio: Optional[str] = None,
    limite: int = 300
):
    try:
        query = f"""
            SELECT DISTINCT
                UPPER(TRIM(UF)) AS UF,
                UPPER(TRIM(municipio)) AS municipio,
                CAST(geocodigo AS STRING) AS geocodigo
            FROM `{TABLE_ID}`
            WHERE UF IS NOT NULL
              AND municipio IS NOT NULL
              AND geocodigo IS NOT NULL
        """
        params = []
        if uf and uf != "Todos":
            query += " AND UPPER(TRIM(UF)) = @uf"
            params.append(bigquery.ScalarQueryParameter("uf", "STRING", uf.upper().strip()))
        if municipio and municipio != "Todos":
            query += " AND UPPER(TRIM(municipio)) = @municipio"
            params.append(bigquery.ScalarQueryParameter("municipio", "STRING", municipio.upper().strip()))

        query += " ORDER BY UF, municipio LIMIT @limite"
        params.append(bigquery.ScalarQueryParameter("limite", "INT64", int(limite)))

        cfg = bigquery.QueryJobConfig(query_parameters=params)
        rows = get_client().query(query, job_config=cfg).result()

        dados = []
        for r in rows:
            dados.append({
                "UF": r["UF"],
                "municipio": r["municipio"],
                "geocodigo": str(r["geocodigo"]).zfill(7)
            })

        return {"total": len(dados), "dados": dados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerta")
def alerta(
    geocodigo: str = Query(...),
    ano: int = Query(..., ge=2000, le=2050),
    decendio: int = Query(..., ge=1, le=36),
    solo: int = Query(3, ge=1, le=3)
):
    try:
        analysis = SafraAnalysis(TABLE_ID)
        gee = analysis.gee

        start_date, end_date = gee.decendio_to_dates(ano, decendio)
        geom = gee.get_municipio_geometry(geocodigo)

        zarc_row = analysis.get_zarc_data(geocodigo, ano, solo)
        if zarc_row is None:
            return {"status": "Dados ZARC não encontrados"}

        frequencia_zarc = float(zarc_row["valor_frequencia"])

        img_ndvi = (
            ee.ImageCollection("MODIS/061/MOD13Q1")
            .filterBounds(geom)
            .filterDate(start_date, end_date)
            .median()
            .select("NDVI")
            .clip(geom)
        )

        stats = img_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geom,
            scale=250,
            maxPixels=1e9
        ).getInfo()

        ndvi_real = (stats.get("NDVI", 0) or 0) / 10000.0
        zarc_prob = frequencia_zarc / 100.0
        divergencia = zarc_prob - ndvi_real

        status = "Normal"
        if zarc_prob > 0.7 and ndvi_real < 0.4:
            status = "ALERTA CRÍTICO: Seca detectada"
        elif zarc_prob < 0.4 and ndvi_real > 0.7:
            status = "ANOMALIA POSITIVA: Vegetação acima do esperado"

        return {
            "municipio_cod": str(geocodigo),
            "cultura": str(zarc_row["Nome_cultura"]),
            "periodo": f"D{decendio}/{ano}",
            "zarc_frequencia": frequencia_zarc,
            "ndvi_medio": round(ndvi_real, 3),
            "divergencia": round(divergencia, 3),
            "status": status,
            "data_inicio": start_date,
            "data_fim": end_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mapa")
def mapa_gee(
    geocodigo: str = Query(...),
    ano: int = Query(..., ge=2000, le=2050),
    decendio: int = Query(..., ge=1, le=36),
    produto: str = Query("NDVI"),
    kernel: str = Query("NONE"),
    threshold: float = Query(0.35, ge=0.0, le=1.0)
):
    try:
        gee = SafraVivaGEE()
        start_date, end_date = gee.decendio_to_dates(ano, decendio)
        geom = gee.get_municipio_geometry(geocodigo)
        produto = produto.upper().strip()
        kernel = kernel.upper().strip()

        def safe_median(collection, fallback_days=60):
            size = collection.size().getInfo()
            if size and size > 0:
                return collection.median(), False

            sd = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=fallback_days)
            ed = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=fallback_days)
            c2 = collection.filterDate(sd.strftime("%Y-%m-%d"), ed.strftime("%Y-%m-%d"))
            size2 = c2.size().getInfo()
            if size2 and size2 > 0:
                return c2.median(), True

            return None, True

        img = None
        vis = None
        fallback_used = False

        if produto == "NDVI":
            coll = ee.ImageCollection("MODIS/061/MOD13Q1").filterBounds(geom).filterDate(start_date, end_date).select("NDVI")
            med, fallback_used = safe_median(coll)
            if med is None:
                raise HTTPException(status_code=404, detail="Sem imagens NDVI no período/área (mesmo com fallback).")
            img = med.clip(geom)
            vis = {"min": 0, "max": 9000, "palette": ["#8b0000", "#ffcc00", "#1a9850"]}

        elif produto == "EVI":
            coll = ee.ImageCollection("MODIS/061/MOD13Q1").filterBounds(geom).filterDate(start_date, end_date).select("EVI")
            med, fallback_used = safe_median(coll)
            if med is None:
                raise HTTPException(status_code=404, detail="Sem imagens EVI no período/área (mesmo com fallback).")
            img = med.clip(geom)
            vis = {"min": 0, "max": 9000, "palette": ["#542788", "#f7f7f7", "#1b7837"]}

        elif produto == "LST":
            coll = ee.ImageCollection("MODIS/061/MOD11A1").filterBounds(geom).filterDate(start_date, end_date).select("LST_Day_1km")
            med, fallback_used = safe_median(coll)
            if med is None:
                raise HTTPException(status_code=404, detail="Sem imagens LST no período/área (mesmo com fallback).")
            img = med.clip(geom)
            vis = {"min": 13000, "max": 16500, "palette": ["#313695", "#74add1", "#fdae61", "#a50026"]}

        elif produto in ["LANDSAT_TRUE", "LANDSAT_FALSE"]:
            base = (
                ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                .filterBounds(geom)
                .filterDate(start_date, end_date)
                .map(gee.prep_landsat_l2)
            )

            size = base.size().getInfo()
            if not size or size == 0:
                sd = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
                ed = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=90)).strftime("%Y-%m-%d")
                base = (
                    ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                    .filterBounds(geom)
                    .filterDate(sd, ed)
                    .map(gee.prep_landsat_l2)
                )
                fallback_used = True

            if (base.size().getInfo() or 0) == 0:
                raise HTTPException(status_code=404, detail="Sem cenas Landsat disponíveis.")

            med = base.qualityMosaic("qscore").clip(geom)

            if produto == "LANDSAT_TRUE":
                img = med.select(["SR_B4", "SR_B3", "SR_B2"])
            else:
                img = med.select(["SR_B5", "SR_B4", "SR_B3"])

            vis = {"min": 0.02, "max": 0.35, "gamma": 1.15}

        elif produto in ["S2_TRUE", "S2_FALSE", "S2_NDVI"]:
            coll = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(geom)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
            )
            med, fallback_used = safe_median(coll)
            if med is None:
                raise HTTPException(status_code=404, detail="Sem imagens Sentinel-2 no período/área (mesmo com fallback).")

            if produto == "S2_TRUE":
                img = med.select(["B4", "B3", "B2"]).clip(geom)
                vis = {"min": 0, "max": 3000, "gamma": 1.2}
            elif produto == "S2_FALSE":
                img = med.select(["B8", "B4", "B3"]).clip(geom)
                vis = {"min": 0, "max": 3000, "gamma": 1.2}
            else:
                img = med.normalizedDifference(["B8", "B4"]).rename("S2_NDVI").clip(geom)
                vis = {"min": 0, "max": 1, "palette": ["#8b0000", "#ffcc00", "#1a9850"]}

        else:
            raise HTTPException(status_code=400, detail="Produto inválido")

        if kernel in ["THRESHOLD", "SOBEL"]:
            img = apply_kernel(img, kernel=kernel, threshold=threshold)
            if kernel == "THRESHOLD":
                vis = {"min": 0, "max": 1, "palette": ["#000000", "#00ff00"]}
            else:
                vis = {"min": -2000, "max": 2000, "palette": ["#0000ff", "#ffffff", "#ff0000"]}

        map_id = ee.Image(img).getMapId(vis)
        tile_url = map_id["tile_fetcher"].url_format
        centroid = geom.centroid(1).coordinates().getInfo()

        return {
            "produto": produto,
            "kernel": kernel,
            "threshold": threshold,
            "fallback_used": fallback_used,
            "periodo": {"inicio": start_date, "fim": end_date},
            "tile_url": tile_url,
            "center": {"lon": centroid[0], "lat": centroid[1]}
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))