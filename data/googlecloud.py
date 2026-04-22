import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

def get_storage_client():
    return storage.Client(project=GCP_PROJECT_ID)

def upload_pasta_parquet(caminho_local, bucket_nome):
    """Sobe uma pasta inteira (como a do Parquet) para o GCS."""
    client = get_storage_client()
    bucket = client.bucket(bucket_nome)
    
    print(f"Subindo {caminho_local} para gs://{bucket_nome}...")
    
    # Caminha por todos os arquivos da pasta gerada pelo Spark
    for root, dirs, files in os.walk(caminho_local):
        for file in files:
            # Caminho completo do arquivo local
            caminho_completo = os.path.join(root, file)
            
            # Define o caminho que o arquivo terá dentro do Bucket
            # (Mantendo a estrutura de pastas do particionamento)
            caminho_no_gcs = os.path.relpath(caminho_completo, os.path.dirname(caminho_local))
            
            blob = bucket.blob(caminho_no_gcs)
            blob.upload_from_filename(caminho_completo)
            
    print(f"Upload da pasta {caminho_local} concluído com sucesso!")