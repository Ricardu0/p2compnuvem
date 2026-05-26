import os
import io
import base64
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from azure.storage.blob import BlobServiceClient

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
GOOGLE_CREDS_PATH = "google_creds.json"
PASTA_DRIVE_FIXA  = "1yFnqtycFOdGsRpL3Z7wp4FPv2v4cbl25"
PASTA_DRIVE_LINK  = "https://drive.google.com/drive/u/1/folders/1yFnqtycFOdGsRpL3Z7wp4FPv2v4cbl25"
NOME_ALUNO_FIXO   = "ricardo"
AZURE_CONNECTION_STRING = (
    "BlobEndpoint=https://stodsm6p2.blob.core.windows.net/;"
    "QueueEndpoint=https://stodsm6p2.queue.core.windows.net/;"
    "FileEndpoint=https://stodsm6p2.file.core.windows.net/;"
    "TableEndpoint=https://stodsm6p2.table.core.windows.net/;"
    "SharedAccessSignature=sv=2026-02-06&ss=b&srt=sco&sp=rwdlaciytfx"
    "&se=2026-06-08T20:41:40Z&st=2026-05-25T12:26:40Z&spr=https,http"
    "&sig=4ZaFti31frOhQfvDnNOlFPaad%2FgAjEeDiiGS8AlxJfU%3D"
)

EXTENSOES_IMAGEM = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}


# ==============================================================================
# CSS
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

    /* Fluxo steps */
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

    /* Tabs */
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

    /* Instrução manual */
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

    /* File cards */
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

    /* Image preview grid */
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
    .img-card img { width: 100%; height: 140px; object-fit: cover; display: block; }
    .img-card .img-label {
        padding: 6px 10px; font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem; color: #888; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis; border-top: 1px solid #f0f0ec;
    }

    /* Badges */
    .badge { display: inline-block; padding: 3px 10px; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }
    .badge-ok   { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .badge-err  { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .badge-skip { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }

    /* Info block */
    .info-block { background: #ffffff; border: 1px solid #d8d8d4; padding: 18px 22px; margin-bottom: 1.5rem; }
    .info-block .label { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #999; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
    .info-block .value { font-family: 'IBM Plex Mono', monospace; font-size: 0.88rem; color: #1a1a1a; font-weight: 500; }

    /* Counter */
    .counter-row { display: flex; gap: 12px; margin-bottom: 1.5rem; }
    .counter-box { background: #ffffff; border: 1px solid #d8d8d4; padding: 16px 22px; flex: 1; text-align: center; }
    .counter-box .num { font-family: 'IBM Plex Mono', monospace; font-size: 2rem; font-weight: 600; color: #1a1a1a; line-height: 1; }
    .counter-box .lbl { font-family: 'IBM Plex Sans', sans-serif; font-size: 0.72rem; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }

    /* Buttons */
    .stButton > button {
        border-radius: 0 !important; font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.78rem !important; font-weight: 500 !important;
        letter-spacing: 0.5px !important; text-transform: uppercase !important;
        border: 1.5px solid #1a1a1a !important; background: #ffffff !important;
        color: #1a1a1a !important; padding: 10px 20px !important;
        transition: background 0.2s ease, color 0.2s ease !important;
    }
    .stButton > button:hover { background: #1a1a1a !important; color: #f4f4f0 !important; }
    .stButton > button[kind="primary"] { background: #1a1a1a !important; color: #f4f4f0 !important; }
    .stButton > button[kind="primary"]:hover { background: #444 !important; }

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
    </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def formatar_tamanho(bytes_val):
    if bytes_val is None: return "—"
    try:
        b = int(bytes_val)
        if b < 1024:        return f"{b} B"
        elif b < 1024**2:   return f"{b/1024:.1f} KB"
        else:               return f"{b/1024**2:.1f} MB"
    except: return "—"


def icone_arquivo(nome):
    ext = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    mapa = {
        "pdf":"📄","xlsx":"📊","xls":"📊","csv":"📊",
        "docx":"📝","doc":"📝","txt":"📃","json":"📋",
        "png":"🖼️","jpg":"🖼️","jpeg":"🖼️","gif":"🖼️","webp":"🖼️",
        "zip":"📦","rar":"📦","py":"🐍","js":"⚙️",
    }
    return mapa.get(ext, "📁")


def eh_imagem(nome):
    ext = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    return ext in EXTENSOES_IMAGEM


# ==============================================================================
# CONEXÕES
# ==============================================================================
def obter_servico_drive():
    if not os.path.exists(GOOGLE_CREDS_PATH):
        raise FileNotFoundError(f"'{GOOGLE_CREDS_PATH}' não encontrado.")
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDS_PATH,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)


def obter_container_client(nome_aluno):
    nome = f"aluno-{nome_aluno.strip().lower()}"
    client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    return client.get_container_client(nome), nome


# ==============================================================================
# DRIVE
# ==============================================================================
def listar_dados_origem(folder_id):
    service = obter_servico_drive()
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name, size, mimeType)"
    ).execute()
    arquivos = results.get("files", [])
    vistos, unicos = set(), []
    for arq in arquivos:
        if arq["id"] not in vistos:
            vistos.add(arq["id"])
            unicos.append(arq)
    return unicos


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
    except:
        return None


# ==============================================================================
# AZURE
# ==============================================================================
def listar_dados_destino(nome_aluno):
    container_client, nome_container = obter_container_client(nome_aluno)
    criado = False
    if not container_client.exists():
        container_client.create_container()
        criado = True
    blobs = [
        {"name": b.name, "size": b.size, "last_modified": b.last_modified}
        for b in container_client.list_blobs()
    ]
    return blobs, nome_container, criado


def migrar_arquivo(file_id, file_name, container_alvo, pular_existentes=False, blobs_existentes=None):
    if pular_existentes and blobs_existentes and file_name in blobs_existentes:
        return "skip", "Arquivo já existe no destino."
    try:
        service = obter_servico_drive()
        request = service.files().get_media(fileId=file_id)
        stream = io.BytesIO()
        downloader = MediaIoBaseDownload(stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        stream.seek(0)
        blob_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING).get_blob_client(
            container=container_alvo, blob=file_name
        )
        blob_client.upload_blob(stream, overwrite=True)
        return "ok", "Enviado com sucesso."
    except Exception as e:
        return "error", str(e)


# ==============================================================================
# RENDERIZADORES
# ==============================================================================
def render_file_card(nome, tamanho=None, extra_html=""):
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
    cols_html = "".join([
        f'<div class="counter-box"><div class="num">{n}</div><div class="lbl">{l}</div></div>'
        for n, l in itens
    ])
    st.markdown(f'<div class="counter-row">{cols_html}</div>', unsafe_allow_html=True)


def render_info_block(label, value):
    st.markdown(f"""
    <div class="info-block">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
    </div>""", unsafe_allow_html=True)


def render_flow(aba_ativa):
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
    st.markdown(f"""
    <div class="instrucao-box">
        <div class="icon">📂</div>
        <div class="texto">
            <strong>Para adicionar arquivos à origem:</strong> acesse a pasta do Google Drive manualmente,
            faça o upload dos arquivos lá, e clique em <strong>↻ Listar Arquivos</strong> para atualizar.(EU TENTEI FAZER DE TUDO PRA PODER ENVIAR POR FORA, MAS N CONSEGUI).<br>
            <a href="{PASTA_DRIVE_LINK}" target="_blank">→ Abrir pasta no Google Drive</a>
        </div>
    </div>""", unsafe_allow_html=True)


# ==============================================================================
# INTERFACE PRINCIPAL
# ==============================================================================
st.set_page_config(page_title="Migração Multi-Cloud", layout="wide", initial_sidebar_state="collapsed")
aplicar_estilo()

st.markdown("""
<div class="main-header">
    <h1>☁ MIGRAÇÃO DE ARQUIVOS — MULTI-CLOUD</h1>
    <p>Google Drive → Azure Blob Storage &nbsp;·&nbsp; Aluno: Ricardo</p>
</div>""", unsafe_allow_html=True)

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
            with st.spinner("Acessando Google Drive..."):
                try:
                    st.session_state["arquivos_drive"] = listar_dados_origem(PASTA_DRIVE_FIXA)
                    st.session_state.pop("imagens_cache", None)
                except Exception as e:
                    st.error(f"Erro: {e}")

    arquivos = st.session_state.get("arquivos_drive", [])

    if arquivos:
        total_size = sum(int(a.get("size", 0) or 0) for a in arquivos)
        imagens = [a for a in arquivos if eh_imagem(a["name"])]
        outros  = [a for a in arquivos if not eh_imagem(a["name"])]

        render_counter_row([
            (len(arquivos), "Arquivos"),
            (len(imagens), "Imagens"),
            (formatar_tamanho(total_size), "Tamanho Total"),
        ])

        # Preview de imagens
        if imagens:
            st.markdown('<div class="img-section-title">🖼 Preview de Imagens</div>', unsafe_allow_html=True)

            # Cache de imagens na sessão
            if "imagens_cache" not in st.session_state:
                st.session_state["imagens_cache"] = {}

            service = obter_servico_drive()
            cols = st.columns(min(len(imagens), 4))
            for i, arq in enumerate(imagens):
                fid = arq["id"]
                if fid not in st.session_state["imagens_cache"]:
                    with st.spinner(f"Carregando {arq['name']}..."):
                        dados = baixar_thumbnail(service, fid)
                        st.session_state["imagens_cache"][fid] = dados
                dados = st.session_state["imagens_cache"].get(fid)
                with cols[i % 4]:
                    if dados:
                        st.image(dados, caption=arq["name"], use_container_width=True)
                    else:
                        st.markdown(f'<div style="background:#f0f0ec;height:120px;display:flex;align-items:center;justify-content:center;font-size:2rem;">🖼️</div><div style="font-size:0.7rem;color:#aaa;">{arq["name"]}</div>', unsafe_allow_html=True)

        # Outros arquivos
        if outros:
            st.markdown('<div class="section-label">Outros Arquivos</div>', unsafe_allow_html=True)
            for arq in outros:
                render_file_card(arq["name"], arq.get("size"))

    elif "arquivos_drive" in st.session_state:
        st.info("Nenhum arquivo encontrado na pasta. Adicione arquivos via o link acima e liste novamente.")
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
            Clique em <strong>↻ Listar Blobs</strong> para verificar o que já foi enviado
            e confirmar que o contêiner está acessível antes de migrar.
        </div>
    </div>""", unsafe_allow_html=True)

    col_btn2, _ = st.columns([1, 4])
    with col_btn2:
        if st.button("↻ Listar Blobs", key="btn_blob"):
            with st.spinner("Conectando ao Azure..."):
                try:
                    blobs, container_nome, criado = listar_dados_destino(NOME_ALUNO_FIXO)
                    st.session_state["blobs_destino"] = blobs
                    st.session_state["container_alvo"] = container_nome
                    if criado:
                        st.success(f"Contêiner '{container_nome}' criado automaticamente.")
                except Exception as e:
                    st.error(f"Erro ao acessar Azure: {e}")

    blobs = st.session_state.get("blobs_destino", [])

    if blobs:
        total_blob = sum(int(b.get("size", 0) or 0) for b in blobs)
        render_counter_row([(len(blobs), "Blobs"), (formatar_tamanho(total_blob), "Tamanho Total")])
        st.markdown('<div class="section-label">Arquivos no Contêiner</div>', unsafe_allow_html=True)
        for b in blobs:
            mod = b["last_modified"].strftime("%d/%m/%Y %H:%M") if b.get("last_modified") else ""
            render_file_card(b["name"], b.get("size"),
                             extra_html=f'<span class="file-size">{mod}</span>' if mod else "")
    elif "blobs_destino" in st.session_state:
        st.markdown('<div class="info-block" style="border-style:dashed;text-align:center;color:#aaa;padding:40px;"><div style="font-size:1.5rem;">📭</div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.82rem;margin-top:8px;">Contêiner vazio — pronto para receber arquivos.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-block" style="border-style:dashed;text-align:center;color:#aaa;padding:40px;"><div style="font-size:1.5rem;">☁</div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.82rem;margin-top:8px;">Clique em ↻ Listar Blobs para verificar o contêiner.</div></div>', unsafe_allow_html=True)

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

    if st.button("▶ Iniciar Migração", type="primary", key="btn_migrar", disabled=not pronto):
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
                f'<div class="info-block" style="padding:10px 16px;">'
                f'<div class="label">Transferindo {idx+1} de {len(arquivos)}</div>'
                f'<div class="value">{arq["name"]}</div></div>',
                unsafe_allow_html=True
            )
            resultado, msg = migrar_arquivo(
                arq["id"], arq["name"], container_alvo,
                pular_existentes=pular_existentes,
                blobs_existentes=blobs_existentes
            )
            resultados.append((arq["name"], arq.get("size"), resultado, msg))
            if resultado == "ok":    sucessos += 1; blobs_existentes.add(arq["name"])
            elif resultado == "skip": pulados += 1
            else:                    erros += 1
            barra.progress((idx+1) / len(arquivos))

        status_texto.empty()
        st.markdown("<hr>", unsafe_allow_html=True)
        render_counter_row([(sucessos, "Enviados"), (pulados, "Pulados"), (erros, "Erros")])

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

        try:
            blobs_atualizados, _, _ = listar_dados_destino(NOME_ALUNO_FIXO)
            st.session_state["blobs_destino"] = blobs_atualizados
        except: pass

    if not pronto:
        avisos = []
        if not n_src: avisos.append("Liste os arquivos na aba **① Google Drive**")
        if "container_alvo" not in st.session_state: avisos.append("Valide o contêiner na aba **② Azure Container**")
        st.warning("Para habilitar a migração: " + " · ".join(avisos))