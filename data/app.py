import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from dotenv import load_dotenv
from streamlit_folium import st_folium

load_dotenv()

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API_ZARC_URL = f"{API_BASE}/api/zarc"
API_ALERTA_URL = f"{API_BASE}/api/alerta"
API_MAPA_URL = f"{API_BASE}/api/mapa"
API_UFS_URL = f"{API_BASE}/api/filtros/ufs"
API_MUN_URL = f"{API_BASE}/api/filtros/municipios"
API_CULT_URL = f"{API_BASE}/api/filtros/culturas"

st.set_page_config(layout="wide", page_title="SafraViva BI")
st.title("🛰️🌱 SafraViva Platform")
st.caption("Dados + Sensoriamento Remoto")

# =========================
# Helpers
# =========================
@st.cache_data(ttl=300)
def fetch_json(url, params=None):
    r = requests.get(url, params=params or {}, timeout=240)
    if r.status_code != 200:
        raise Exception(r.text)
    return r.json()

@st.cache_data(ttl=3600)
def get_ufs():
    return fetch_json(API_UFS_URL)["dados"]

@st.cache_data(ttl=3600)
def get_municipios(uf=None):
    p = {"uf": uf} if uf and uf != "Todos" else {}
    return fetch_json(API_MUN_URL, p)["dados"]

@st.cache_data(ttl=3600)
def get_culturas():
    return fetch_json(API_CULT_URL)["dados"]

@st.cache_data(ttl=300)
def consultar_zarc(params):
    return fetch_json(API_ZARC_URL, params)

@st.cache_data(ttl=300)
def consultar_alerta(params):
    return fetch_json(API_ALERTA_URL, params)

@st.cache_data(ttl=300)
def consultar_mapa(params):
    return fetch_json(API_MAPA_URL, params)

# =========================
# Sidebar Global
# =========================
st.sidebar.header("⚙️ Configurações Globais")

safra = st.sidebar.number_input("Safra", min_value=2000, max_value=2050, value=2023)
decendio = st.sidebar.slider("Decêndio", 1, 36, 1)
cod_solo = st.sidebar.selectbox("Solo", [1, 2, 3], index=2)

# Produtos satélite (mais opções)
produto_sat = st.sidebar.selectbox(
    "Produto Satélite",
    [
        "NDVI",
        "EVI",
        "LST",
        "LANDSAT_TRUE",
        "LANDSAT_FALSE",
        "S2_TRUE",
        "S2_FALSE",
        "S2_NDVI"
    ],
    index=0
)

st.sidebar.markdown("### 🧪 Processamento (Kernels)")
kernel_op = st.sidebar.selectbox("Operação", ["NONE", "THRESHOLD", "SOBEL"], index=0)
threshold_value = st.sidebar.slider("Threshold", min_value=0.0, max_value=1.0, value=0.35, step=0.01)

# =========================
# Abas
# =========================
tab_dados, tab_sensor = st.tabs(["📊 Dados", "🛰️ Sensoriamento"])

# =====================================================
# ABA 1: DADOS
# =====================================================
with tab_dados:
    st.subheader("Consulta Analítica (BigQuery)")

    c1, c2, c3, c4 = st.columns(4)

    ufs = ["Todos"] + get_ufs()
    uf_sel = c1.selectbox("UF", ufs, index=0, key="dados_uf")

    municipios = ["Todos"] + get_municipios(None if uf_sel == "Todos" else uf_sel)
    municipio_sel = c2.selectbox("Município", municipios, index=0, key="dados_mun")

    culturas = ["Todos"] + get_culturas()
    cultura_sel = c3.selectbox("Cultura", culturas, index=0, key="dados_cult")

    geocodigo_dados = c4.text_input("Geocódigo", key="dados_geo")

    limite = st.slider("Limite de linhas", 100, 5000, 1200, 100, key="dados_limite")
    run_dados = st.button("Consultar Dados", key="btn_dados")

    if run_dados:
        params = {"limite": int(limite), "safra_ini": int(safra), "cod_solo": int(cod_solo)}

        if uf_sel != "Todos":
            params["uf"] = uf_sel
        if municipio_sel != "Todos":
            params["municipio"] = municipio_sel
        if cultura_sel != "Todos":
            params["cultura"] = cultura_sel
        if geocodigo_dados:
            params["geocodigo"] = geocodigo_dados.strip()

        if not any([params.get("uf"), params.get("municipio"), params.get("cultura"), params.get("geocodigo")]):
            st.error("Informe pelo menos UF, município, cultura ou geocódigo.")
            st.stop()

        with st.spinner("Consultando BigQuery..."):
            data = consultar_zarc(params)

        df = pd.DataFrame(data.get("dados", []))
        if df.empty:
            st.warning("Sem dados.")
            st.stop()

        df["SafraIni"] = pd.to_numeric(df["SafraIni"], errors="coerce")
        df["valor_frequencia"] = pd.to_numeric(df["valor_frequencia"], errors="coerce")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Registros", len(df))
        k2.metric("Municípios", df["municipio"].nunique())
        k3.metric("Culturas", df["Nome_cultura"].nunique())
        k4.metric("Freq média", round(df["valor_frequencia"].mean(), 2))

        g1, g2 = st.columns([2, 1])
        with g1:
            agg = df["Nome_cultura"].value_counts().reset_index()
            agg.columns = ["Cultura", "Qtd"]
            st.plotly_chart(px.bar(agg, x="Cultura", y="Qtd"), width="stretch")
        with g2:
            solo = df.groupby("Cod_Solo", dropna=False)["valor_frequencia"].mean().reset_index()
            st.plotly_chart(px.pie(solo, names="Cod_Solo", values="valor_frequencia"), width="stretch")

        st.plotly_chart(
            px.line(
                df.sort_values("SafraIni"),
                x="SafraIni",
                y="valor_frequencia",
                color="Nome_cultura",
                markers=True
            ),
            width="stretch"
        )

        st.dataframe(df, width="stretch")

# =====================================================
# ABA 2: SENSORIAMENTO
# =====================================================
with tab_sensor:
    st.subheader("Painel de Sensoriamento Remoto (Mapa Principal)")

    # fluxo: listar todos e depois gerar mapa
    c1, c2, c3 = st.columns([1, 2, 1])

    ufs_s = ["Todos"] + get_ufs()
    uf_sel_s = c1.selectbox("UF", ufs_s, index=0, key="sens_uf")

    municipios_s = ["Todos"] + get_municipios(None if uf_sel_s == "Todos" else uf_sel_s)
    municipio_sel_s = c2.selectbox("Município (lista completa)", municipios_s, index=0, key="sens_mun")

    geocodigo_s = c3.text_input("Geocódigo (opcional)", key="sens_geo")

    st.caption("Se não informar geocódigo, use município + UF e preencha o geocódigo correspondente.")

    run_map = st.button("Gerar Mapa Satelital", key="btn_map")

    if run_map:
        if not geocodigo_s:
            st.error("Informe o geocódigo para gerar o mapa satelital.")
            st.stop()

        mapa_params = {
            "geocodigo": geocodigo_s.strip(),
            "ano": int(safra),
            "decendio": int(decendio),
            "produto": produto_sat,
            "kernel": kernel_op,             # precisa suporte no backend
            "threshold": float(threshold_value)  # precisa suporte no backend
        }

        alerta_params = {
            "geocodigo": geocodigo_s.strip(),
            "ano": int(safra),
            "decendio": int(decendio),
            "solo": int(cod_solo)
        }

        col_map, col_info = st.columns([4, 1])

        with col_map:
            with st.spinner("Processando imagem satelital..."):
                mapa = consultar_mapa(mapa_params)

            lat = mapa["center"]["lat"]
            lon = mapa["center"]["lon"]
            tile_url = mapa["tile_url"]

            m = folium.Map(location=[lat, lon], zoom_start=10, tiles="CartoDB positron")
            folium.TileLayer(
                tiles=tile_url,
                attr="Google Earth Engine",
                name=f"GEE {produto_sat}"
            ).add_to(m)
            folium.LayerControl().add_to(m)

            # MAPA MAIOR (pedido)
            st_folium(m, height=780, returned_objects=[])

            st.caption(
                f'Produto: {produto_sat} | Kernel: {kernel_op} | '
                f'Período: {mapa["periodo"]["inicio"]} até {mapa["periodo"]["fim"]}'
            )

        with col_info:
            with st.spinner("Calculando indicadores..."):
                alerta = consultar_alerta(alerta_params)

            st.metric("ZARC (%)", alerta.get("zarc_frequencia", "-"))
            st.metric("NDVI", alerta.get("ndvi_medio", "-"))
            st.metric("Divergência", alerta.get("divergencia", "-"))
            st.metric("Status", alerta.get("status", "-"))

            st.json(alerta)