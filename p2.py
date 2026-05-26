# p2.py - Versão com debug visível e boas práticas
import os
import io
import base64
import json
import streamlit as st
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from azure.storage.blob import BlobServiceClient

# ==============================================================================
# CONFIGURAÇÕES GLOBAIS
# ==============================================================================

# Debug inicial no console (útil para logs do Render)
print("[DEBUG] Iniciando aplicação...")
print(f"[DEBUG] CWD: {os.getcwd()}")
print(f"[DEBUG] Arquivos no diretório: {os.listdir('.')}")

# Configuração de página DEVE ser a primeira chamada do Streamlit
st.set_page_config(page_title="Migração Multi-Cloud", layout="wide", initial_sidebar_state="collapsed")


# ==============================================================================
# CONFIGURAÇÃO DE CREDENCIAIS - Lógica Local vs Produção
# ==============================================================================
def configurar_caminhos_credenciais():
    """
    Define os caminhos corretos para credenciais baseado no ambiente.
    Prioriza arquivo local para desenvolvimento, variável de ambiente para produção.
    """
    # Caminho para Service Account JSON
    if os.path.exists("google_creds.json"):
        # Desenvolvimento local
        google_creds_path = "google_creds.json"
        st.session_state["env_mode"] = "local"
    else:
        # Produção (Render, etc) - usa variável de ambiente
        google_creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "/etc/secrets/google_creds.json")
        st.session_state["env_mode"] = "production"

    # Caminhos fixos para OAuth e Token
    credentials_path = "credentials.json"
    token_path = "token.json"

    return google_creds_path, credentials_path, token_path


GOOGLE_CREDS_PATH, CREDENTIALS_PATH, TOKEN_PATH = configurar_caminhos_credenciais()

# Configurações do projeto
PASTA_DRIVE_FIXA = "1yFnqtycFOdGsRpL3Z7wp4FPv2v4cbl25"
PASTA_DRIVE_LINK = "https://drive.google.com/drive/u/1/folders/1yFnqtycFOdGsRpL3Z7wp4FPv2v4cbl25"
NOME_ALUNO_FIXO = "ricardo"

# ⚠️ AVISO DE SEGURANÇA: Em produção, use variáveis de ambiente para a connection string!
AZURE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=https;"
    "AccountName=stodsm6p2;"
    "EndpointSuffix=core.windows.net;"
    "SharedAccessSignature=sv=2026-02-06&ss=b&srt=sco&sp=rwdlaciytfx"
    "&se=2026-06-08T20:41:40Z&st=2026-05-25T12:26:40Z&spr=https,http"
    "&sig=4ZaFti31frOhQfvDnNOlFPaad/gAjEeDiiGS8AlxJfU="
)

EXTENSOES_IMAGEM = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}


# ==============================================================================
# CSS - ESTILIZAÇÃO
# ==============================================================================
def aplicar_estilo():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .stApp { background-color: #f4f4f0; color: #1a1a1a; }
    .main-header {
        background: #1a1a1a; color: #f4f4f0;
        padding: 28px 32px; margin: -1rem -1rem 2rem -1rem;
        font-family: 'IBM Plex Mono', monospace; letter-spacing: -0.5px;
    }
    .main-header h1 { font-size: 1.4rem; font-weight: 600; margin: 0; color: #f4f4f0; }
    .main-header p  { font-size: 0.75rem; color: #888; margin: 6px 0 0 0; font-family: 'IBM Plex Mono', monospace; }
    .flow-strip {
        display: flex; align-items: stretch; gap: 0;
        margin-bottom: 2rem; border: 1px solid #d8d8d4; background: #fff;
    }
    .flow-step {
        flex: 1; padding: 18px 20px; position: relative;
        border-right: 1px solid #e8e8e4;
    }
    .flow-step:last-child { border-right: none; }
    .flow-step.active { background: #1a1a1a; color: #f4f4f0; }
    .flow-step .step-num {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
        text-transform: uppercase; letter-spacing: 1px;
        color: #aaa; margin-bottom: 6px;
    }
    .flow-step.active .step-num { color: #666; }
    .flow-step .step-title {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem;
        font-weight: 600; color: #1a1a1a;
    }
    .flow-step.active .step-title { color: #f4f4f0; }
    .flow-step .step-desc {
        font-size: 0.75rem; color: #888; margin-top: 4px; line-height: 1.4;
    }
    .flow-step.active .step-desc { color: #aaa; }
    .flow-arrow {
        display: flex; align-items: center; padding: 0 4px;
        font-size: 1rem; color: #ccc; font-family: monospace;
        background: #fafaf8; border-right: 1px solid #e8e8e4;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: #e8e8e4; border-radius: 0; gap: 0;
        border-bottom: 2px solid #1a1a1a; padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0; padding: 12px 24px;
        font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
        font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase;
        color: #666; border: none; border-right: 1px solid #d0d0cc;
        transition: background 0.2s ease, color 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { background: #d4d4d0; color: #1a1a1a; }
    .stTabs [aria-selected="true"] { background: #1a1a1a !important; color: #f4f4f0 !important; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem; }
    .instrucao-box {
        background: #fffef0; border: 1px solid #e8e000;
        border-left: 4px solid #ccbb00;
        padding: 16px 20px; margin-bottom: 1.5rem;
        display: flex; align-items: flex-start; gap: 14px;
    }
    .instrucao-box .icon { font-size: 1.2rem; margin-top: 1px; }
    .instrucao-box .texto { font-size: 0.82rem; color: #555; line-height: 1.6; }
    .instrucao-box .texto strong { color: #1a1a1a; }
    .instrucao-box a {
        color: #1a1a1a; font-weight: 600;
        font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
    }
    .file-card {
        background: #ffffff; border: 1px solid #d8d8d4;
        padding: 12px 16px; margin-bottom: 6px;
        display: flex; align-items: center; justify-content: space-between;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .file-card:hover { border-color: #1a1a1a; box-shadow: 3px 3px 0px #1a1a1a; }
    .file-name { font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; color: #1a1a1a; font-weight: 500; }
    .file-size { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #999; }
    .file-icon { font-size: 1rem; margin-right: 12px; }
    .file-left { display: flex; align-items: center; }
    .img-section-title {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
        text-transform: uppercase; letter-spacing: 1px; color: #999;
        margin: 1.5rem 0 0.75rem 0;
    }
    .img-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 10px; margin-bottom: 1.5rem;
    }
    .img-card {
        background: #fff; border: 1px solid #d8d8d4;
        overflow: hidden; transition: border-color 0.2s, box-shadow 0.2s;
    }
    .img-card:hover { border-color: #1a1a1a; box-shadow: 3px 3px 0 #1a1a1a; }
    .img-card img { width: 100%; height: 180px; object-fit: cover; display: block; }
    .img-card .img-label {
        padding: 6px 10px; font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem; color: #888; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis; border-top: 1px solid #f0f0ec;
    }
    .badge { display: inline-block; padding: 3px 10px; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }
    .badge-ok   { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .badge-err  { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .badge-skip { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
    .info-block { background: #ffffff; border: 1px solid #d8d8d4; padding: 18px 22px; margin-bottom: 1.5rem; }
    .info-block .label { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #999; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
    .info-block .value { font-family: 'IBM Plex Mono', monospace; font-size: 0.88rem; color: #1a1a1a; font-weight: 500; }
    .counter-row { display: flex; gap: 12px; margin-bottom: 1.5rem; }
    .counter-box { background: #ffffff; border: 1px solid #d8d8d4; padding: 16px 22px; flex: 1; text-align: center; }
    .counter-box .num { font-family: 'IBM Plex Mono', monospace; font-size: 2rem; font-weight: 600; color: #1a1a1a; line-height: 1; }
    .counter-box .lbl { font-family: 'IBM Plex Sans', sans-serif; font-size: 0.72rem; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
    .stButton > button {
        border-radius: 0 !important; font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.78rem !important; font-weight: 500 !important;
        letter-spacing: 0.5px !important; text-transform: uppercase !important;
        border: 1.5px solid #1a1a1a !important; background: #ffffff !important;
        color: #1a1a1a !important; padding: 10px 20px !important;
        transition: background 0.2s ease, color 0.2s ease !important;
    }
    .stButton > button:hover { background: #1a1a1a !important; color: #f4f4f0 !important; }
    .stButton > button[kind="primary"] { background: #000000 !important; color: #ffffff !important; }
    .stButton > button[kind="primary"]:hover { background: #444444 !important; }
    .stCheckbox label { font-family: 'IBM Plex Sans', sans-serif; font-size: 0.85rem; color: #444; }
    .stProgress > div > div { background: #1a1a1a !important; border-radius: 0 !important; }
    .stProgress > div { border-radius: 0 !important; background: #d8d8d4 !important; height: 6px !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 0 !important; }
    hr { border: none; border-top: 1px solid #d8d8d4; margin: 1.5rem 0; }
    .log-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; margin-bottom: 6px; background: #fff; border: 1px solid #e0e0dc; }
    .log-row.success { border-left: 3px solid #28a745; }
    .log-row.error   { border-left: 3px solid #dc3545; }
    .log-row.skipped { border-left: 3px solid #ffc107; }
    .section-label {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
        text-transform: uppercase; letter-spacing: 1px; color: #999;
        border-bottom: 1px solid #e8e8e4; padding-bottom: 8px;
        margin-bottom: 1rem;
    }
    /* Debug box styling */
    .debug-box {
        background: #1a1a1a; color: #0f0;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem; padding: 12px;
        border-radius: 4px; margin: 1rem 0;
        white-space: pre-wrap; max-height: 200px; overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def formatar_tamanho(bytes_val):
    """Converte bytes para formato legível."""
    if bytes_val is None:
        return "—"
    try:
        b = int(bytes_val)
        if b < 1024:
            return f"{b} B"
        elif b < 1024 ** 2:
            return f"{b / 1024:.1f} KB"
        else:
            return f"{b / 1024 ** 2:.1f} MB"
    except:
        return "—"


def icone_arquivo(nome):
    """Retorna emoji baseado na extensão do arquivo."""
    ext = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    mapa = {
        "pdf": "📄", "xlsx": "📊", "xls": "📊", "csv": "📊",
        "docx": "📝", "doc": "📝", "txt": "📃", "json": "📋",
        "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️", "gif": "🖼️", "webp": "🖼️",
        "zip": "📦", "rar": "📦", "py": "🐍", "js": "⚙️",
    }
    return mapa.get(ext, "📁")


def eh_imagem(nome):
    """Verifica se o arquivo é uma imagem suportada."""
    ext = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    return ext in EXTENSOES_IMAGEM


def log_debug_ui(mensagem, nivel="info"):
    """
    Exibe mensagens de debug na UI (além do console).
    Níveis: info, warning, error, success
    """
    cores = {
        "info": "#888",
        "warning": "#ccbb00",
        "error": "#dc3545",
        "success": "#28a745"
    }
    cor = cores.get(nivel, "#888")
    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:{cor};border-left:3px solid {cor};padding:4px 12px;margin:4px 0;">
        [{nivel.upper()}] {mensagem}
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# CONEXÕES - GOOGLE DRIVE & AZURE
# ==============================================================================
def obter_servico_drive():
    """Obtém serviço do Google Drive — FORÇANDO OAuth para troca de conta."""
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    # === BLOCO DA SERVICE ACCOUNT — COMENTADO PARA FORÇAR OAUTH ===
    # if os.path.exists(GOOGLE_CREDS_PATH):
    #     try:
    #         creds = service_account.Credentials.from_service_account_file(
    #             GOOGLE_CREDS_PATH, scopes=SCOPES
    #         )
    #         return build("drive", "v3", credentials=creds)
    #     except Exception as e:
    #         log_debug_ui(f"⚠️ Falha na Service Account: {e}", "warning")
    # =================================================================

    # === FLUXO OAUTH 2.0 (AGORA SERÁ USADO SEMPRE) ===
    log_debug_ui("🔄 Usando fluxo OAuth 2.0...", "info")
    creds = None

    # Carrega token salvo se existir
    if os.path.exists(TOKEN_PATH) and os.path.getsize(TOKEN_PATH) > 0:
        try:
            with open(TOKEN_PATH, "r", encoding="utf-8") as _f:
                json.load(_f)  # Valida JSON
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            log_debug_ui(f"📄 Token carregado. Válido: {creds.valid}", "info")
        except Exception:
            os.remove(TOKEN_PATH)
            creds = None

    # Refresh ou novo login
    if not creds or not creds.valid:
        log_debug_ui("🔑 Credenciais inválidas. Iniciando login...", "warning")

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"'{CREDENTIALS_PATH}' não encontrado.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            # prompt="consent" força re-autenticação mesmo se já logado
            creds = flow.run_local_server(port=8080, prompt="consent")
            log_debug_ui("✅ Login OAuth concluído!", "success")

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
        log_debug_ui(f"💾 Token salvo em: {TOKEN_PATH}", "info")

    service = build("drive", "v3", credentials=creds)

    # Verificação final
    try:
        about = service.about().get(fields="user, storageQuota").execute()
        user_email = about.get('user', {}).get('emailAddress', 'Desconhecido')
        quota = about.get('storageQuota', {})
        usage_gb = int(quota.get('usage', 0)) / 1024 ** 3
        limit_gb = int(quota.get('limit', 0)) / 1024 ** 3 if quota.get('limit') else None
        free_gb = (limit_gb - usage_gb) if limit_gb else None

        msg = f"✅ Conectado como: {user_email}"
        if limit_gb:
            msg += f" | {usage_gb:.2f}GB / {limit_gb:.2f}GB"
        log_debug_ui(msg, "success")
    except Exception as e:
        log_debug_ui(f"⚠️ Não foi possível verificar conta: {e}", "warning")

    return service


def obter_container_client(nome_aluno):
    """Obtém cliente do Azure Blob Storage."""
    nome = f"aluno-{nome_aluno.strip().lower()}"
    client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    return client.get_container_client(nome), nome


# ==============================================================================
# FUNÇÕES - GOOGLE DRIVE
# ==============================================================================
def listar_dados_origem(folder_id):
    """Lista arquivos de uma pasta do Drive."""
    service = obter_servico_drive()
    log_debug_ui(f"📋 Listando arquivos da pasta: {folder_id[:10]}...", "info")

    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name, size, mimeType, createdTime, modifiedTime)"
    ).execute()

    arquivos = results.get("files", [])
    log_debug_ui(f"✅ Encontrados {len(arquivos)} arquivos", "success")

    # Remove duplicatas por ID
    vistos, unicos = set(), []
    for arq in arquivos:
        if arq["id"] not in vistos:
            vistos.add(arq["id"])
            unicos.append(arq)

    return unicos


def verificar_cota_drive(service):
    """
    Verifica cota de armazenamento do Drive.
    Retorna: (tem_espaco: bool, mensagem: str, detalhes: dict)
    """
    try:
        quota = service.about().get(fields="storageQuota").execute()
        sq = quota.get("storageQuota", {})

        # Converte para int com fallback seguro
        usage = int(sq.get("usage") or 0)
        limit = int(sq.get("limit") or 0)

        # Calcula valores em GB (sempre números, nunca None)
        usage_gb = usage / 1024 ** 3
        limit_gb = limit / 1024 ** 3 if limit > 0 else None
        free = limit - usage if limit > 0 else 0
        free_gb = free / 1024 ** 3

        # Determina se tem espaço (considera limite indefinido como "tem espaço")
        tem_espaco = (limit == 0) or (free > 0)

        # Formatação segura para mensagem
        if limit_gb is None:
            msg = f"✅ Espaço: {usage_gb:.2f}GB usados (limite indefinido)"
        elif tem_espaco:
            msg = f"✅ Espaço OK: {free_gb:.2f}GB livres de {limit_gb:.2f}GB"
        else:
            msg = f"❌ COTA ESGOTADA: {usage_gb:.2f}GB / {limit_gb:.2f}GB usados"

        return tem_espaco, msg, {
            "usage_gb": usage_gb,
            "limit_gb": limit_gb,
            "free_gb": free_gb,
            "usage_bytes": usage,
            "limit_bytes": limit
        }

    except Exception as e:
        # Retorna fallback seguro em caso de erro
        return True, f"⚠️ Não foi possível verificar cota: {type(e).__name__}", {}


def baixar_thumbnail(service, file_id):
    """Baixa os bytes de um arquivo do Drive para preview."""
    try:
        request = service.files().get_media(fileId=file_id)
        stream = io.BytesIO()
        downloader = MediaIoBaseDownload(stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        stream.seek(0)
        return stream.read()
    except Exception as e:
        log_debug_ui(f"❌ Erro ao baixar thumbnail {file_id}: {e}", "error")
        return None


# ==============================================================================
# FUNÇÕES - AZURE BLOB
# ==============================================================================
def listar_dados_destino(nome_aluno):
    """Lista blobs de um container Azure."""
    container_client, nome_container = obter_container_client(nome_aluno)
    criado = False

    if not container_client.exists():
        log_debug_ui(f"🆕 Criando container: {nome_container}", "info")
        container_client.create_container()
        criado = True

    blobs = [
        {"name": b.name, "size": b.size, "last_modified": b.last_modified}
        for b in container_client.list_blobs()
    ]
    log_debug_ui(f"✅ {len(blobs)} blobs no container '{nome_container}'", "success")
    return blobs, nome_container, criado


def migrar_arquivo(file_id, file_name, container_alvo, pular_existentes=False, blobs_existentes=None):
    """Migra arquivo do Drive para Azure Blob."""
    if pular_existentes and blobs_existentes and file_name in blobs_existentes:
        return "skip", "Arquivo já existe no destino."

    try:
        log_debug_ui(f"⬇️  Baixando do Drive: {file_name}", "info")
        service = obter_servico_drive()
        request = service.files().get_media(fileId=file_id)
        stream = io.BytesIO()
        downloader = MediaIoBaseDownload(stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        stream.seek(0)

        log_debug_ui(f"⬆️  Enviando para Azure: {file_name}", "info")
        blob_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING).get_blob_client(
            container=container_alvo, blob=file_name
        )
        blob_client.upload_blob(stream, overwrite=True)

        log_debug_ui(f"✅ Migrado: {file_name}", "success")
        return "ok", "Enviado com sucesso."
    except Exception as e:
        log_debug_ui(f"❌ Erro na migração {file_name}: {type(e).__name__}: {str(e)[:100]}", "error")
        return "error", f"{type(e).__name__}: {str(e)[:150]}"


def baixar_blob(container_nome, blob_nome):
    """Baixa blob do Azure para stream em memória."""
    try:
        blob_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING).get_blob_client(
            container=container_nome, blob=blob_nome
        )
        stream = io.BytesIO()
        stream.write(blob_client.download_blob().readall())
        stream.seek(0)
        return stream
    except Exception as e:
        log_debug_ui(f"❌ Erro ao baixar blob {blob_nome}: {e}", "error")
        return None


def migrar_para_drive(blob_nome, container_nome, folder_id):
    """Migra blob do Azure para Google Drive."""
    try:
        log_debug_ui(f"⬇️  Baixando do Azure: {blob_nome}", "info")
        stream = baixar_blob(container_nome, blob_nome)
        if not stream:
            return "error", "Falha ao baixar do Azure"

        service = obter_servico_drive()

        # Verifica cota antes de upload
        tem_espaco, msg_cota, _ = verificar_cota_drive(service)
        if not tem_espaco:
            log_debug_ui(f"❌ Upload abortado: {msg_cota}", "error")
            return "error", f"Cota excedida: {msg_cota}"

        file_metadata = {'name': blob_nome, 'parents': [folder_id]}
        media = MediaIoBaseUpload(stream, mimetype='application/octet-stream', resumable=True)

        # Verifica se já existe
        results = service.files().list(
            q=f"'{folder_id}' in parents and name='{blob_nome}' and trashed=false",
            fields="files(id)"
        ).execute()
        files = results.get('files', [])

        if files:
            log_debug_ui(f"🔄 Atualizando arquivo existente: {blob_nome}", "info")
            service.files().update(fileId=files[0]['id'], media_body=media).execute()
        else:
            log_debug_ui(f"🆕 Criando novo arquivo: {blob_nome}", "info")
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        log_debug_ui(f"✅ Migrado para Drive: {blob_nome}", "success")
        return "ok", "Migrado para o Drive com sucesso."
    except HttpError as e:
        if e.resp.status == 403 and 'storageQuotaExceeded' in str(e):
            log_debug_ui(f"❌ Cota do Drive excedida para: {blob_nome}", "error")
            return "error", "Cota de armazenamento do Drive excedida"
        log_debug_ui(f"❌ HttpError {e.resp.status}: {e.content.decode()[:100] if e.content else 'sem detalhes'}",
                     "error")
        return "error", f"HttpError {e.resp.status}: {str(e)[:100]}"
    except Exception as e:
        log_debug_ui(f"❌ Erro inesperado {blob_nome}: {type(e).__name__}: {str(e)[:100]}", "error")
        return "error", f"{type(e).__name__}: {str(e)[:150]}"


# ==============================================================================
# UI - MODAIS E VISUALIZAÇÃO
# ==============================================================================
@st.dialog("Visualização de Arquivo", width="large")
def modal_visualizar(nome_arquivo, dados_bytes):
    """Modal para preview de arquivos."""
    st.write(f"**Arquivo:** `{nome_arquivo}`")

    if eh_imagem(nome_arquivo):
        # ✅ CORREÇÃO: use_container_width → width="stretch"
        st.image(dados_bytes, caption=f"🖼️ {nome_arquivo}", width="stretch")
    elif nome_arquivo.lower().endswith(".pdf"):
        base64_pdf = base64.b64encode(dados_bytes).decode('utf-8')
        pdf_display = f'''<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'''
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        try:
            texto = dados_bytes.decode('utf-8')
            st.text_area("Conteúdo do Texto", texto, height=400)
        except UnicodeDecodeError:
            st.info("📦 Arquivo binário - use o download para visualizar.")
            st.download_button(label="⬇️ Fazer Download", data=dados_bytes, file_name=nome_arquivo)


# ==============================================================================
# RENDERIZADORES DE COMPONENTES
# ==============================================================================
def render_file_card(nome, tamanho=None, extra_html=""):
    """Renderiza card de arquivo na UI."""
    icone = icone_arquivo(nome)
    tam = formatar_tamanho(tamanho) if tamanho else ""
    st.markdown(f"""
    <div class="file-card">
        <div class="file-left">
            <span class="file-icon">{icone}</span>
            <span class="file-name">{nome}</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            {f'<span class="file-size">{tam}</span>' if tam else ""}
            {extra_html}
        </div>
    </div>""", unsafe_allow_html=True)


def render_counter_row(itens):
    """Renderiza linha de contadores."""
    cols_html = "".join([
        f'<div class="counter-box"><div class="num">{n}</div><div class="lbl">{l}</div></div>'
        for n, l in itens
    ])
    st.markdown(f'<div class="counter-row">{cols_html}</div>', unsafe_allow_html=True)


def render_info_block(label, value):
    """Renderiza bloco de informação."""
    st.markdown(f"""
    <div class="info-block">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
    </div>""", unsafe_allow_html=True)


def render_flow(aba_ativa):
    """Renderiza barra de progresso do fluxo."""
    steps = [
        ("01", "Google Drive", "Veja os arquivos\nna pasta monitorada"),
        ("02", "Azure Container", "Confirme o destino\nno Blob Storage"),
        ("03", "Migração", "Execute a transferência\nnuvem → nuvem"),
    ]
    html = '<div class="flow-strip">'
    for i, (num, titulo, desc) in enumerate(steps):
        ativo = "active" if i == aba_ativa else ""
        html += f'<div class="flow-step {ativo}"><div class="step-num">Passo {num}</div><div class="step-title">{titulo}</div><div class="step-desc">{desc}</div></div>'
        if i < len(steps) - 1:
            html += '<div class="flow-arrow">›</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_instrucao_manual():
    """Renderiza caixa de instruções."""
    st.markdown(f"""
    <div class="instrucao-box">
        <div class="icon">📂</div>
        <div class="texto">
            <strong>Para adicionar arquivos à origem:</strong> acesse a pasta do Google Drive manualmente,
            faça o upload dos arquivos lá, e clique em <strong>↻ Listar Arquivos</strong> para atualizar.<br>
            <a href="{PASTA_DRIVE_LINK}" target="_blank">→ Abrir pasta no Google Drive</a>
        </div>
    </div>""", unsafe_allow_html=True)


# ==============================================================================
# UI PRINCIPAL
# ==============================================================================
aplicar_estilo()

st.markdown("""
<div class="main-header">
    <h1>☁ MIGRAÇÃO DE ARQUIVOS — MULTI-CLOUD</h1>
    <p>Google Drive → Azure Blob Storage &nbsp;·&nbsp; Aluno: Ricardo</p>
</div>""", unsafe_allow_html=True)

# ==============================================================================
# PAINEL DE DEBUG (sempre visível para troubleshooting)
# ==============================================================================
with st.expander("🔧 Painel de Debug", expanded=False):
    col_dbg1, col_dbg2, col_dbg3 = st.columns(3)

    with col_dbg1:
        st.markdown("**📁 Ambiente**")
        st.code(f"Modo: {st.session_state.get('env_mode', '?')}\nCWD: {os.getcwd()}", language="text")

    with col_dbg2:
        st.markdown("**🔐 Credenciais**")
        creds_info = []
        if os.path.exists(GOOGLE_CREDS_PATH):
            creds_info.append(f"✅ SA: {os.path.basename(GOOGLE_CREDS_PATH)}")
        if os.path.exists(CREDENTIALS_PATH):
            creds_info.append(f"✅ OAuth: {CREDENTIALS_PATH}")
        if os.path.exists(TOKEN_PATH):
            creds_info.append(f"✅ Token: {TOKEN_PATH}")
        st.code("\n".join(creds_info) if creds_info else "❌ Nenhuma credencial encontrada", language="text")

    with col_dbg3:
        st.markdown("**💾 Cota Drive**")
        if st.button("🔄 Verificar agora", key="btn_check_quota_debug"):
            with st.spinner("Consultando Google..."):
                try:
                    service = obter_servico_drive()
                    tem_espaco, msg, detalhes = verificar_cota_drive(service)
                    st.success(msg) if tem_espaco else st.error(msg)
                    if detalhes:
                        st.metric("Livre", f"{detalhes['free_gb']:.2f} GB")
                except Exception as e:
                    st.error(f"Erro: {e}")

# ==============================================================================
# TABS PRINCIPAIS
# ==============================================================================
tab_drive, tab_container, tab_migracao = st.tabs(["① Google Drive", "② Azure Container", "③ Migração"])

# ──────────────────────────────────────────────────────────────────────────────
# ABA 1: GOOGLE DRIVE
# ──────────────────────────────────────────────────────────────────────────────
with tab_drive:
    render_flow(0)
    render_instrucao_manual()
    render_info_block("Pasta Monitorada — Google Drive ID", PASTA_DRIVE_FIXA)

    col_btn, col_esp = st.columns([1, 4])
    with col_btn:
        if st.button("↻ Listar Arquivos", key="btn_drive"):
            with st.spinner("🔌 Conectando ao Google Drive..."):
                try:
                    st.session_state["arquivos_drive"] = listar_dados_origem(PASTA_DRIVE_FIXA)
                    st.session_state.pop("imagens_cache", None)  # Limpa cache de imagens
                    log_debug_ui("✅ Lista atualizada com sucesso!", "success")
                except Exception as e:
                    log_debug_ui(f"❌ Erro: {type(e).__name__}: {str(e)[:100]}", "error")
                    st.error(f"Erro ao listar: {e}")

        # Upload direto para o Drive
        uploaded_files = st.file_uploader(
            "Selecionar arquivos para upload",
            accept_multiple_files=True,
            key="upload_files",
            help="Os arquivos serão enviados para a pasta do Drive configurada."
        )

        if uploaded_files:
            st.info(f"📎 {len(uploaded_files)} arquivo(s) selecionado(s): {[f.name for f in uploaded_files]}")

            if st.button("⬆️ Upload para Drive", key="btn_upload_drive", type="primary"):
                with st.spinner("🚀 Enviando para o Google Drive..."):
                    service = obter_servico_drive()

                    # Verifica cota uma vez antes do loop
                    tem_espaco, msg_cota, detalhes_cota = verificar_cota_drive(service)
                    if not tem_espaco:
                        st.error(f"🚫 {msg_cota}")
                        st.stop()

                    resultados_upload = []

                    for up_file in uploaded_files:
                        try:
                            mime = up_file.type or "application/octet-stream"
                            file_size = up_file.size if hasattr(up_file, "size") else len(up_file.getvalue())

                            # Verifica cota por arquivo
                            if detalhes_cota.get('free_gb', float('inf')) * 1024 ** 3 < file_size:
                                resultados_upload.append((up_file.name, "error", "Arquivo maior que espaço disponível"))
                                log_debug_ui(f"❌ {up_file.name}: muito grande para cota restante", "error")
                                continue

                            media = MediaIoBaseUpload(up_file, mimetype=mime, resumable=True)
                            file_metadata = {"name": up_file.name, "parents": [PASTA_DRIVE_FIXA]}

                            log_debug_ui(f"⬆️  Enviando: {up_file.name} ({formatar_tamanho(file_size)})", "info")
                            novo_arquivo = service.files().create(
                                body=file_metadata,
                                media_body=media,
                                fields="id, name, webViewLink"
                            ).execute()

                            resultados_upload.append((up_file.name, "ok", "Enviado"))
                            log_debug_ui(
                                f"✅ {up_file.name}: {novo_arquivo.get('webViewLink', 'ID:' + novo_arquivo['id'])}",
                                "success")

                        except HttpError as e:
                            if e.resp.status == 403 and 'storageQuotaExceeded' in str(e):
                                msg = "🚫 Cota do Drive esgotada!"
                                st.error(msg)
                                log_debug_ui(msg, "error")
                                resultados_upload.append((up_file.name, "error", "Cota excedida"))
                                break  # Para de tentar se acabou o espaço
                            else:
                                erro_detalhe = e.content.decode() if e.content else str(e)
                                msg = f"❗ Erro HTTP {e.resp.status}: {erro_detalhe[:100]}"
                                log_debug_ui(msg, "error")
                                resultados_upload.append((up_file.name, "error", msg))
                        except Exception as e:
                            msg = f"❌ {type(e).__name__}: {str(e)[:100]}"
                            log_debug_ui(msg, "error")
                            resultados_upload.append((up_file.name, "error", msg))

                    # Resumo final
                    sucessos = sum(1 for _, r, _ in resultados_upload if r == "ok")
                    erros = sum(1 for _, r, _ in resultados_upload if r == "error")

                    if sucessos > 0:
                        st.success(f"✅ {sucessos} arquivo(s) enviado(s) com sucesso!")
                    if erros > 0:
                        st.warning(f"⚠️ {erros} arquivo(s) falharam. Veja os logs acima.")

                    # Atualiza lista se houve sucesso
                    if sucessos > 0:
                        st.session_state["arquivos_drive"] = listar_dados_origem(PASTA_DRIVE_FIXA)

    # Lista de arquivos do Drive
    arquivos = st.session_state.get("arquivos_drive", [])

    if arquivos:
        total_size = sum(int(a.get("size", 0) or 0) for a in arquivos)
        imagens = [a for a in arquivos if eh_imagem(a["name"])]
        outros = [a for a in arquivos if not eh_imagem(a["name"])]

        render_counter_row([
            (len(arquivos), "Arquivos"),
            (len(imagens), "Imagens"),
            (formatar_tamanho(total_size), "Tamanho Total"),
        ])

        # Preview de imagens
        if imagens:
            st.markdown('<div class="img-section-title">🖼 Preview de Imagens</div>', unsafe_allow_html=True)

            if "imagens_cache" not in st.session_state:
                st.session_state["imagens_cache"] = {}

            service = obter_servico_drive()
            cols = st.columns(min(len(imagens), 4))

            for i, arq in enumerate(imagens):
                fid = arq["id"]
                if fid not in st.session_state["imagens_cache"]:
                    with st.spinner(f"📥 {arq['name']}..."):
                        dados = baixar_thumbnail(service, fid)
                        st.session_state["imagens_cache"][fid] = dados

                dados = st.session_state["imagens_cache"].get(fid)
                with cols[i % 4]:
                    if dados:
                        # ✅ CORREÇÃO: use_container_width → width="stretch"
                        st.image(dados, caption=arq["name"], width="stretch")
                    else:
                        st.markdown(f'''
                        <div style="background:#f0f0ec;height:120px;display:flex;align-items:center;justify-content:center;font-size:2rem;">🖼️</div>
                        <div style="font-size:0.7rem;color:#aaa;text-align:center;">{arq["name"]}</div>
                        ''', unsafe_allow_html=True)

        # Outros arquivos
        if outros:
            st.markdown('<div class="section-label">Outros Arquivos</div>', unsafe_allow_html=True)
            service = obter_servico_drive()  # Reutiliza conexão

            for arq in outros:
                c_card, c_btn = st.columns([9, 1], vertical_alignment="center")
                with c_card:
                    render_file_card(arq["name"], arq.get("size"))
                with c_btn:
                    if st.button("👁️", key=f"btn_view_drive_{arq['id']}"):
                        with st.spinner("📥 Baixando preview..."):
                            dados = baixar_thumbnail(service, arq["id"])
                            if dados:
                                modal_visualizar(arq["name"], dados)
                            else:
                                st.error("❌ Erro ao carregar preview.")

    elif "arquivos_drive" in st.session_state:
        st.info("📭 Nenhum arquivo encontrado na pasta. Adicione arquivos via o link acima e liste novamente.")
    else:
        st.markdown("""
        <div class="info-block" style="border-style:dashed;text-align:center;color:#aaa;padding:48px;">
            <div style="font-size:2rem;margin-bottom:8px;">📁</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.82rem;">
                Clique em ↻ Listar Arquivos para ver o conteúdo da pasta.
            </div>
        </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ABA 2: AZURE CONTAINER
# ──────────────────────────────────────────────────────────────────────────────
with tab_container:
    render_flow(1)
    render_info_block("Contêiner Azure Blob Storage", f"aluno-{NOME_ALUNO_FIXO}")

    st.markdown("""
    <div class="instrucao-box">
        <div class="icon">ℹ️</div>
        <div class="texto">
            Este contêiner é o <strong>destino final</strong> dos arquivos migrados.
            Clique em <strong>↻ Listar Blobs</strong> para verificar o que já foi enviado.
        </div>
    </div>""", unsafe_allow_html=True)

    col_btn2, _ = st.columns([1, 4])
    with col_btn2:
        if st.button("↻ Listar Blobs", key="btn_blob"):
            with st.spinner("🔌 Conectando ao Azure..."):
                try:
                    blobs, container_nome, criado = listar_dados_destino(NOME_ALUNO_FIXO)
                    st.session_state["blobs_destino"] = blobs
                    st.session_state["container_alvo"] = container_nome
                    if criado:
                        st.success(f"🆕 Contêiner '{container_nome}' criado automaticamente.")
                    log_debug_ui(f"✅ {len(blobs)} blobs listados", "success")
                except Exception as e:
                    log_debug_ui(f"❌ Erro Azure: {type(e).__name__}: {str(e)[:100]}", "error")
                    st.error(f"Erro ao acessar Azure: {e}")

    blobs = st.session_state.get("blobs_destino", [])

    if blobs:
        total_blob = sum(int(b.get("size", 0) or 0) for b in blobs)
        render_counter_row([(len(blobs), "Blobs"), (formatar_tamanho(total_blob), "Tamanho Total")])
        st.markdown('<div class="section-label">Arquivos no Contêiner</div>', unsafe_allow_html=True)

        selecionar_todos = st.checkbox("Selecionar Todos", key="chk_select_all_azure")
        arquivos_selecionados = []

        for b in blobs:
            mod = b["last_modified"].strftime("%d/%m/%Y %H:%M") if b.get("last_modified") else ""
            c_chk, c_card, c_btn = st.columns([0.5, 8.5, 1], vertical_alignment="center")

            with c_chk:
                if st.checkbox(" ", key=f"chk_{b['name']}", value=selecionar_todos):
                    arquivos_selecionados.append(b['name'])
            with c_card:
                render_file_card(b["name"], b.get("size"),
                                 extra_html=f'<span class="file-size">{mod}</span>' if mod else "")
            with c_btn:
                if st.button("👁️", key=f"btn_view_azure_{b['name']}"):
                    with st.spinner("📥 Baixando..."):
                        stream = baixar_blob(st.session_state["container_alvo"], b["name"])
                        if stream:
                            modal_visualizar(b["name"], stream.read())
                        else:
                            st.error("❌ Erro ao carregar preview.")

        if arquivos_selecionados:
            st.markdown("<hr>", unsafe_allow_html=True)
            if st.button("📤 Migrar Selecionados para Google Drive", type="primary", key="btn_migrar_drive"):
                st.markdown('<div class="section-label">Log de Migração (Azure → Drive)</div>', unsafe_allow_html=True)
                barra2 = st.progress(0)
                status_texto2 = st.empty()
                sucessos2, erros2 = 0, 0
                resultados2 = []

                for idx, arq_nome in enumerate(arquivos_selecionados):
                    status_texto2.markdown(
                        f'''<div class="info-block" style="padding:10px 16px;">
                        <div class="label">Enviando {idx + 1} de {len(arquivos_selecionados)}</div>
                        <div class="value">{arq_nome}</div></div>''',
                        unsafe_allow_html=True
                    )
                    res, msg = migrar_para_drive(arq_nome, st.session_state["container_alvo"], PASTA_DRIVE_FIXA)
                    resultados2.append((arq_nome, res, msg))
                    if res == "ok":
                        sucessos2 += 1
                    else:
                        erros2 += 1
                    barra2.progress((idx + 1) / len(arquivos_selecionados))

                status_texto2.empty()
                render_counter_row([(sucessos2, "✅ Enviados"), (erros2, "❌ Erros")])

                for nome, res, msg in resultados2:
                    if res == "ok":
                        st.success(f"{nome}: {msg}")
                    else:
                        st.error(f"{nome}: {msg}")

    elif "blobs_destino" in st.session_state:
        st.markdown('''<div class="info-block" style="border-style:dashed;text-align:center;color:#aaa;padding:40px;">
        <div style="font-size:1.5rem;">📭</div>
        <div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.82rem;margin-top:8px;">
        Contêiner vazio — pronto para receber arquivos.</div></div>''', unsafe_allow_html=True)
    else:
        st.markdown('''<div class="info-block" style="border-style:dashed;text-align:center;color:#aaa;padding:40px;">
        <div style="font-size:1.5rem;">☁</div>
        <div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.82rem;margin-top:8px;">
        Clique em ↻ Listar Blobs para verificar o contêiner.</div></div>''', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ABA 3: MIGRAÇÃO
# ──────────────────────────────────────────────────────────────────────────────
with tab_migracao:
    render_flow(2)

    st.markdown("""
    <div class="instrucao-box">
        <div class="icon">🚀</div>
        <div class="texto">
            <strong>Pré-requisitos antes de migrar:</strong><br>
            1. Liste os arquivos na aba <strong>① Google Drive</strong><br>
            2. Valide o contêiner na aba <strong>② Azure Container</strong><br>
            3. Volte aqui e clique em <strong>▶ Iniciar Migração</strong>
        </div>
    </div>""", unsafe_allow_html=True)

    pular_existentes = st.checkbox("Pular arquivos já presentes no contêiner (evita duplicatas)", value=True)

    col_src, col_dst = st.columns(2)
    n_src = len(st.session_state.get("arquivos_drive", []))
    container_alvo = st.session_state.get("container_alvo", f"aluno-{NOME_ALUNO_FIXO}")
    n_dst = len(st.session_state.get("blobs_destino", []))

    with col_src:
        status_src = f"✔ {n_src} arquivo(s) mapeado(s)" if n_src else "⚠ Não listado — vá à aba ①"
        render_info_block("Origem — Google Drive", status_src)
    with col_dst:
        status_dst = f"✔ {container_alvo} · {n_dst} blob(s)" if "container_alvo" in st.session_state else "⚠ Não validado — vá à aba ②"
        render_info_block("Destino — Azure Blob", status_dst)

    st.markdown("<hr>", unsafe_allow_html=True)

    pronto = n_src > 0 and "container_alvo" in st.session_state

    if st.button("▶ Iniciar Migração Drive → Azure", type="primary", key="btn_migrar", disabled=not pronto):
        arquivos = st.session_state.get("arquivos_drive")
        container_alvo = st.session_state.get("container_alvo")
        blobs_existentes = {b["name"] for b in st.session_state.get("blobs_destino", [])}

        st.markdown('<div class="section-label">Log de Transferência</div>', unsafe_allow_html=True)
        barra = st.progress(0)
        status_texto = st.empty()
        sucessos, erros, pulados = 0, 0, 0
        resultados = []

        for idx, arq in enumerate(arquivos):
            status_texto.markdown(
                f'''<div class="info-block" style="padding:10px 16px;">
                <div class="label">Transferindo {idx + 1} de {len(arquivos)}</div>
                <div class="value">{arq["name"]}</div></div>''',
                unsafe_allow_html=True
            )
            resultado, msg = migrar_arquivo(
                arq["id"], arq["name"], container_alvo,
                pular_existentes=pular_existentes,
                blobs_existentes=blobs_existentes
            )
            resultados.append((arq["name"], arq.get("size"), resultado, msg))
            if resultado == "ok":
                sucessos += 1
                blobs_existentes.add(arq["name"])
            elif resultado == "skip":
                pulados += 1
            else:
                erros += 1
            barra.progress((idx + 1) / len(arquivos))

        status_texto.empty()
        st.markdown("<hr>", unsafe_allow_html=True)
        render_counter_row([(sucessos, "✅ Enviados"), (pulados, "⏭ Pulados"), (erros, "❌ Erros")])

        st.markdown('<div class="section-label">Detalhes</div>', unsafe_allow_html=True)
        for nome, size, resultado, msg in resultados:
            icone = icone_arquivo(nome)
            if resultado == "ok":
                badge, classe = '<span class="badge badge-ok">Enviado</span>', "success"
            elif resultado == "skip":
                badge, classe = '<span class="badge badge-skip">Pulado</span>', "skipped"
            else:
                badge, classe = '<span class="badge badge-err">Erro</span>', "error"
            st.markdown(f"""
            <div class="log-row {classe}">
                <div class="file-left">
                    <span class="file-icon">{icone}</span>
                    <div>
                        <div class="file-name">{nome}</div>
                        <div class="file-size">{formatar_tamanho(size)}</div>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    {badge}
                    {"" if resultado != "error" else f'<span class="file-size" style="max-width:220px;overflow:hidden;text-overflow:ellipsis;">{msg[:70]}</span>'}
                </div>
            </div>""", unsafe_allow_html=True)

        # Atualiza lista do Azure
        try:
            blobs_atualizados, _, _ = listar_dados_destino(NOME_ALUNO_FIXO)
            st.session_state["blobs_destino"] = blobs_atualizados
            log_debug_ui("✅ Lista do Azure atualizada", "success")
        except Exception as e:
            log_debug_ui(f"⚠️ Não foi possível atualizar lista: {e}", "warning")

    if not pronto:
        avisos = []
        if not n_src:
            avisos.append("Liste os arquivos na aba **① Google Drive**")
        if "container_alvo" not in st.session_state:
            avisos.append("Valide o contêiner na aba **② Azure Container**")
        st.warning("Para habilitar a migração: " + " · ".join(avisos))