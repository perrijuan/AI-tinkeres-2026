import os

# 1. FORÇA A ALOCAÇÃO DE MEMÓRIA NO WSL ANTES DO PYSPARK INICIAR A JVM
# Ajuste o "8g" para mais ou para menos dependendo de quanto você liberou no .wslconfig
os.environ["PYSPARK_SUBMIT_ARGS"] = "--driver-memory 8g --executor-memory 8g pyspark-shell"

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from functools import reduce
from operator import or_
from pyspark.sql.functions import expr


from database import salvar_no_postgres


# 2. Inicialização da sessão do Spark com configurações otimizadas para OOM
spark = (
    SparkSession.builder
    .appName("zarc")
    .config("spark.driver.maxResultSize", "2g")
    .config("spark.sql.shuffle.partitions", "50")
    .config("spark.jars", "jars/postgresql-42.7.10.jar") 
    .getOrCreate()
)

# 3. Carregar dados de um arquivo CSV
caminho_arquivo = "safra_ordenada.csv"
dados_safra = spark.read.csv(caminho_arquivo, header=True, inferSchema=True, sep=";")

# Comentei este show() para não engasgar a memória logo na largada. 
# Deixe o Spark carregar tudo preguiçosamente (lazy).
# dados_safra.show() 

# 4. Definir listas de colunas
cols_base = [
    "Nome_cultura", "SafraIni", "SafraFin", 
    "Cod_Solo", "geocodigo", "UF", "municipio"
]
cols_dec = [f"dec{i}" for i in range(1, 36)]
cols_totais = cols_base + cols_dec

# 5. Construir a condição de forma funcional (Lazy)
condicao_decendios = reduce(or_, [F.col(c) > 0 for c in cols_dec])

# 6. Encadeamento Lazy de Transformações
dados_processados = (
    dados_safra
    .select(cols_totais) 
    .fillna(0, subset=cols_dec)
    .filter(condicao_decendios)
    #  CORREÇÃO 1: Incluir SafraFin e Cod_Solo para NÃO deletar os solos e anos finais!
    .dropDuplicates(["geocodigo", "SafraIni", "SafraFin", "Cod_Solo", "Nome_cultura"]) 
)

# 7. Ação (Action)
dados_processados = dados_processados.cache()  # evita o reprocessamento 

print(f"Total de registros originais: {dados_processados.count()}")

#  CORREÇÃO 2: Normalizando os índices dos decêndios para serem apenas NÚMEROS (1 a 36)
stack_expr = "stack(35, " + ",".join([f"{i}, dec{i}" for i in range(1, 36)]) + ") as (decendio_idx, valor_frequencia)"

#  CORREÇÃO 3: Incluindo SafraFin e Cod_Solo no select final para ir pro banco
df_long = dados_processados.select(
    "UF", "municipio", "Nome_cultura", "SafraIni", "SafraFin", "Cod_Solo", "geocodigo",
    expr(stack_expr)
)

# Mantém APENAS as labels/decêndios que tenham valores válidos de plantio
df_long = df_long.filter(F.col("valor_frequencia") > 0)


# 8. Escrita particionada no Data Lake (Parquet)
df_long.write \
    .mode("overwrite") \
    .partitionBy("UF") \
    .parquet("dados_zarc_particionado")

print("Parquet salvo localmente!")




# --- INTEGRAÇÃO GOOGLE CLOUD ---
# --- INTEGRAÇÃO GOOGLE CLOUD ---
try:
    # Importando direto do seu arquivo de configuração
    from googlecloud import upload_pasta_parquet, GCS_BUCKET_NAME
    
    if GCS_BUCKET_NAME:
        # Chama a função que criamos acima
        upload_pasta_parquet("dados_zarc_particionado", GCS_BUCKET_NAME)
    else:
        print("Aviso: GCS_BUCKET_NAME não configurado.")
except Exception as e:
    print(f"Erro no upload para o GCS: {e}")

print("Iniciando gravação otimizada no Postgres...")





#
# uso do banco de dados -> alternativa extra 
#

# 9. Gravação Otimizada no Banco (Sem o loop For)
df_base = spark.read.parquet("dados_zarc_particionado")

# Cria as partições para paralelizar a gravação
df_to_db = df_base.repartition(10)

try:
    # Chama a função de salvar do database.py uma única vez!
    salvar_no_postgres(df_to_db, "dados_safra_front")
except Exception as e:
    print(f"Erro geral na gravação: {e}")

print("DEPOIS DE SALVAR")
spark.stop()