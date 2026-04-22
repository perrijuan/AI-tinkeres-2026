import ee
import geemap
import os 
from datetime import datetime, timedelta
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

class SafraVivaGEE:
    def __init__(self):
        # Inicializa o Earth Engine
        try:
            ee.Initialize(project=GCP_PROJECT_ID)
        except Exception:
            ee.Authenticate()
            ee.Initialize()

        # Malha Municipal do IBGE (Asset público ou oficial)
        self.municipios = ee.FeatureCollection("projects/ee-ibge/assets/malha_municipal_2022")

    def get_municipio_geometry(self, geocodigo):
        """Retorna o polígono e o centroide do município via geocódigo IBGE."""
        municipio = self.municipios.filter(ee.Filter.eq('CD_MUN', str(geocodigo)))
        return municipio.geometry()

    def get_landsat9_image(self, geocodigo, data_inicio, data_fim, bandas=['SR_B4', 'SR_B3', 'SR_B2']):
        """
        Coleta imagem Landsat 9 (30m) com máscara de nuvens.
        Bandas comuns: ['SR_B4', 'SR_B3', 'SR_B2'] para Cor Verdadeira
                       ['SR_B5', 'SR_B4', 'SR_B3'] para Falsa Cor (Vegetação)
        """
        geom = self.get_municipio_geometry(geocodigo)
        
        # Coleção Landsat 9 Nível 2 (Surface Reflectance)
        collection = (ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                      .filterBounds(geom)
                      .filterDate(data_inicio, data_fim)
                      .map(self._mask_landsat_sr)) # Remove nuvens e sombras

        # Retorna a mediana do período (mosaico limpo) clipada no município
        return collection.median().select(bandas).clip(geom)

    def get_modis_data(self, geocodigo, data_inicio, data_fim, produto='NDVI'):
        """
        Coleta dados MODIS (250m/500m).
        Produtos: 'NDVI' (Saúde), 'EVI' (Biomassa), 'LST' (Temperatura da Superfície)
        """
        geom = self.get_municipio_geometry(geocodigo)
        
        if produto == 'NDVI':
            coll = ee.ImageCollection("MODIS/061/MOD13Q1").select('NDVI')
        elif produto == 'LST':
            coll = ee.ImageCollection("MODIS/061/MOD11A1").select('LST_Day_1km')
        
        image = coll.filterBounds(geom).filterDate(data_inicio, data_fim).median()
        return image.clip(geom)

    def _mask_landsat_sr(self, image):
        """Função interna para remover nuvens e sombras do Landsat 9."""
        qa = image.select('QA_PIXEL')
        # Bits para nuvens e sombras
        dilated_cloud = 1 << 1
        cirrus = 1 << 2
        cloud = 1 << 3
        cloud_shadow = 1 << 4
        mask = qa.bitwiseAnd(dilated_cloud).eq(0) \
            .and(qa.bitwiseAnd(cirrus).eq(0)) \
            .and(qa.bitwiseAnd(cloud).eq(0)) \
            .and(qa.bitwiseAnd(cloud_shadow).eq(0))
        return image.updateMask(mask)

    def decendio_to_dates(self, ano, decendio):
        """Converte seu decendio_idx em intervalo de datas para o GEE."""
        mes = (decendio - 1) // 3 + 1
        dia_inicio = ((decendio - 1) % 3) * 10 + 1
        # Simplificação: cada decêndio tem 10 dias
        start_date = datetime(ano, mes, dia_inicio)
        end_date = start_date + timedelta(days=10)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    

    from google.cloud import bigquery
import ee

class SafraAnalysis:
    def __init__(self, project_id="safra-viva", dataset_id="safravivaorig"):
        self.bq_client = bigquery.Client(project=project_id)
        self.table_id = f"{project_id}.{dataset_id}.zarc-04-26"
        self.gee_helper = SafraVivaGEE() # Usando a classe que criamos antes

    def get_zarc_data(self, geocodigo, decendio, safra, solo=3):
        """Busca o valor_frequencia do ZARC no BigQuery."""
        query = f"""
            SELECT valor_frequencia, Nome_cultura
            FROM `{self.table_id}`
            WHERE geocodigo = @geo AND decendio_idx = @dec 
              AND SafraIni = @safra AND Cod_Solo = @solo
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("geo", "INT64", geocodigo),
                bigquery.ScalarQueryParameter("dec", "INT64", decendio),
                bigquery.ScalarQueryParameter("safra", "INT64", safra),
                bigquery.ScalarQueryParameter("solo", "INT64", solo),
            ]
        )
        df = self.bq_client.query(query, job_config=job_config).to_dataframe()
        return df.iloc[0] if not df.empty else None

    def calculate_early_alert(self, geocodigo, ano, decendio, cultura="SOJA"):
        # 1. Obter Datas e Geometria
        start_date, end_date = self.gee_helper.decendio_to_dates(ano, decendio)
        geom = self.gee_helper.get_municipio_geometry(geocodigo)

        # 2. Obter Risco ZARC (Esperado)
        zarc_row = self.get_zarc_data(geocodigo, decendio, ano)
        if zarc_row is None: return "Dados ZARC não encontrados"
        
        frequencia_zarc = zarc_row['valor_frequencia'] # Ex: 80% (Risco Baixo)

        # 3. Obter NDVI Médio (Realidade via MODIS)
        # MODIS NDVI (MOD13Q1) escala é 0.0001. Valor 8000 = 0.8
        img_ndvi = self.gee_helper.get_modis_data(geocodigo, start_date, end_date, 'NDVI')
        
        stats = img_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geom,
            scale=250,
            maxPixels=1e9
        ).getInfo()
        
        ndvi_real = (stats.get('NDVI', 0) or 0) / 10000.0

        # 4. Lógica de Alerta (Anomalia)
        # Normalizamos a frequência ZARC para 0-1
        zarc_prob = frequencia_zarc / 100.0
        
        # Cálculo de Divergência: Se ZARC é alto mas NDVI é baixo = Alerta
        # Usamos uma métrica de correlação simples ou Delta
        divergencia = zarc_prob - ndvi_real

        status = "Normal"
        if zarc_prob > 0.7 and ndvi_real < 0.4:
            status = "ALERTA CRÍTICO: Seca Detectada (ZARC favorável, mas satélite indica estresse)"
        elif zarc_prob < 0.4 and ndvi_real > 0.7:
            status = "ANOMALIA POSITIVA: Resiliência (Risco alto, mas vegetação saudável)"

        return {
            "municipio_cod": geocodigo,
            "cultura": zarc_row['Nome_cultura'],
            "periodo": f"D{decendio}/{ano}",
            "zarc_frequencia": frequencia_zarc,
            "ndvi_medio": round(ndvi_real, 3),
            "status": status,
            "divergencia": round(divergencia, 3)
        }