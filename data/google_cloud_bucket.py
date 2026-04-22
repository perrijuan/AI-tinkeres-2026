import os
from google.cloud import storage
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

# Nome da pasta gerada pelo Spark
PASTA_LOCAL = "dados_zarc_particionado"

def upload_pasta_parquet(caminho_local, bucket_nome):
    """Sobe uma pasta inteira e mantém a estrutura original."""
    try:
        # Usa automaticamente o login do terminal (ADC)
        client = storage.Client(project=GCP_PROJECT_ID)
        bucket = client.bucket(bucket_nome)
        
        print(f" Conectado ao projeto: {GCP_PROJECT_ID}")
        print(f" Iniciando upload de '{caminho_local}' para gs://{bucket_nome}...\n")
        
        contador = 0
        # Percorre todos os arquivos dentro da pasta local
        for root, dirs, files in os.walk(caminho_local):
            for file in files:
                caminho_completo = os.path.join(root, file)
                
                # Cria o caminho no Bucket mantendo as partições (ex: UF=MT/arquivo.parquet)
                caminho_no_gcs = os.path.relpath(caminho_completo, os.path.dirname(caminho_local))
                
                blob = bucket.blob(caminho_no_gcs)
                blob.upload_from_filename(caminho_completo)
                
                contador += 1
                print(f"   Enviado: {caminho_no_gcs}")
                
        print(f"\n Upload concluído! {contador} arquivos enviados para o GCS.")
        
    except Exception as e:
        print(f"\n Erro durante o upload: {e}")

if __name__ == "__main__":
    # Verificações de segurança antes de tentar subir
    if not GCS_BUCKET_NAME:
        print(" Erro: Variável 'GCS_BUCKET_NAME' não encontrada no arquivo .env")
    elif not os.path.exists(PASTA_LOCAL):
        print(f"Erro: A pasta '{PASTA_LOCAL}' não foi encontrada neste diretório.")
        print("   Execute o etl.py primeiro para gerar os dados.")
    else:
        upload_pasta_parquet(PASTA_LOCAL, GCS_BUCKET_NAME)