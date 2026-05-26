import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

GOOGLE_CREDS_PATH = "google_creds.json"

# 1. Autentica o robô com permissão total de escrita no Drive dele
scopes = ['https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=scopes)
service = build('drive', 'v3', credentials=creds)

# 2. Configura os metadados para criar uma PASTA chamada 'p2cloud'
folder_metadata = {
    'name': 'p2cloud',
    'mimeType': 'application/vnd.google-apps.folder'
}

print("🔄 Solicitando ao Google Cloud a criação da pasta dentro da Service Account...")

try:
    # Cria a pasta dentro do armazenamento do robô
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    novo_id = folder.get('id')

    print("\n🎉 SUCESSO! Pasta criada dentro do robô.")
    print(f"🆔 O ID DA NOVA PASTA É: {novo_id}")
    print("\n👉 COPIE ESSE ID ACIMA E COLOQUE NA VARIÁVEL 'PASTA_DRIVE_FIXA' DO SEU p2.py")

except Exception as e:
    print(f"\n❌ ERRO ao criar a pasta: {e}")