import os
from googlecloud import get_storage_client, get_bucket_name

def criar_bucket_se_nao_existir(bucket_name):
    """Cria um novo bucket no GCS se ele ainda não existir."""
    client = get_storage_client()
    if not client:
        print("Erro: Cliente GCS não inicializado.")
        return None

    try:
        bucket = client.get_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' já existe.")
    except Exception:
        print(f"Criando bucket '{bucket_name}'...")
        bucket = client.create_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' criado com sucesso.")
    
    return bucket

def upload_pasta_parquet(caminho_local, bucket_name):
    """Sobe uma pasta recursivamente para o bucket do GCS."""
    client = get_storage_client()
    if not client:
        return

    bucket = client.bucket(bucket_name)

    print(f"Iniciando upload de '{caminho_local}' para gs://{bucket_name}/")

    for root, dirs, files in os.walk(caminho_local):
        for file in files:
            # Caminho completo do arquivo local
            caminho_completo = os.path.join(root, file)
            
            # Caminho relativo para manter a estrutura de pastas (ex: UF=AC/part-...)
            # O blob_name deve ser relativo ao bucket
            blob_name = os.path.relpath(caminho_completo, start=os.path.dirname(caminho_local))
            
            blob = bucket.blob(blob_name)
            
            print(f"Subindo: {blob_name}...")
            blob.upload_from_filename(caminho_completo)

    print("Upload concluído com sucesso!")

if __name__ == "__main__":
    bucket_nome = get_bucket_name()
    if not bucket_nome:
        print("Erro: GCS_BUCKET_NAME não definido no arquivo .env")
    else:
        # 1. Garante que o bucket existe
        criar_bucket_se_nao_existir(bucket_nome)
        
        # 2. Faz o upload da pasta particionada
        caminho_pasta = "dados_zarc_particionado"
        if os.path.exists(caminho_pasta):
            upload_pasta_parquet(caminho_pasta, bucket_nome)
        else:
            print(f"Erro: Pasta '{caminho_pasta}' não encontrada localmente.")
