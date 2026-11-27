# ==========================================
# TerminalTube - Versão 2.5.3 (Seções Recolhíveis / Acordeão)
# ==========================================

from fastapi import FastAPI, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse, JSONResponse
import os
import glob
import subprocess
import zipfile
import io
import re
import shutil
from urllib.parse import quote

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.environ.get("TERMINALTUBE_MEDIA", os.path.join(BASE_DIR, 'media'))

DIRETORIO_MUSICAS = os.path.join(DIRETORIO_RAIZ, 'audio/musicas')
DIRETORIO_ALBUNS = os.path.join(DIRETORIO_RAIZ, 'audio/albuns')
DIRETORIO_VIDEOS = os.path.join(DIRETORIO_RAIZ, 'video/mp4')

BIN_YTDLP = 'yt-dlp' if os.path.exists('/app') else os.path.join(BASE_DIR, 'venv/bin/yt-dlp')

processo_atual = None
estado_download = {
    "ativo": False,
    "mensagem": "A aguardar...",
    "percentagem": "0%"
}


def _obter_formato_video(param_qualidade: str) -> str:
    if param_qualidade == "720p":
        return 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
    elif param_qualidade == "480p":
        return 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
    return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'


def _montar_comando(url: str, modo: str, param_qualidade: str):
    if modo == "album":
        pasta_destino = DIRETORIO_ALBUNS
        cmd = [
            BIN_YTDLP,
            '--no-playlist',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', param_qualidade,
            '--split-chapters',
            '-o', os.path.join(pasta_destino, '%(autonumber)02d. %(title)s.%(ext)s'),
            '--ignore-errors',
            url
        ]
    elif modo == "video":
        pasta_destino = DIRETORIO_VIDEOS
        formato_str = _obter_formato_video(param_qualidade)
        cmd = [
            BIN_YTDLP,
            '--no-playlist',
            '-f', formato_str,
            '--merge-output-format', 'mp4',
            '-o', os.path.join(pasta_destino, '%(title)s.%(ext)s'),
            '--ignore-errors',
            url
        ]
    elif modo == "video_playlist":
        pasta_destino = DIRETORIO_VIDEOS
        formato_str = _obter_formato_video(param_qualidade)
        cmd = [
            BIN_YTDLP,
            '--yes-playlist',
            '-f', formato_str,
            '--merge-output-format', 'mp4',
            '-o', os.path.join(pasta_destino, '%(playlist_index)s. %(title)s.%(ext)s'),
            '--ignore-errors',
            url
        ]
    elif modo == "musica_individual":
        pasta_destino = DIRETORIO_MUSICAS
        cmd = [
            BIN_YTDLP,
            '--no-playlist',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', param_qualidade,
            '-o', os.path.join(pasta_destino, '%(autonumber)02d. %(title)s.%(ext)s'),
            '--ignore-errors',
            url
        ]
    else:  # playlist_completa
        pasta_destino = DIRETORIO_MUSICAS
        cmd = [
            BIN_YTDLP,
            '--yes-playlist',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', param_qualidade,
            '-o', os.path.join(pasta_destino, '%(playlist_index)s. %(title)s.%(ext)s'),
            '--ignore-errors',
            url
        ]
    return pasta_destino, cmd


def executar_download(urls: list[str], modo: str, param_qualidade: str = "192"):
    global processo_atual, estado_download
    total_urls = len(urls)
    estado_download = {
        "ativo": True,
        "mensagem": f"A iniciar ligação (1/{total_urls})...",
        "percentagem": "0%"
    }

    try:
        for idx, url in enumerate(urls, start=1):
            if not estado_download["ativo"]:
                break

            pasta_destino, cmd = _montar_comando(url, modo, param_qualidade)
            os.makedirs(pasta_destino, exist_ok=True)
            prefixo = f"[{idx}/{total_urls}] " if total_urls > 1 else ""
            estado_download["mensagem"] = f"{prefixo}A preparar download..."

            processo_atual = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for linha in iter(processo_atual.stdout.readline, ''):
                linha_limpa = linha.strip()
                if linha_limpa:
                    estado_download["mensagem"] = f"{prefixo}{linha_limpa}"
                    match = re.search(r'(\d+\.\d+)%', linha_limpa)
                    if match:
                        pct_item = float(match.group(1))
                        pct_global = ((idx - 1) + (pct_item / 100.0)) / total_urls * 100.0
                        estado_download["percentagem"] = f"{pct_global:.1f}%"

            processo_atual.wait()
            if processo_atual.returncode == -9:
                estado_download = {
                    "ativo": False,
                    "mensagem": "Cancelado pelo utilizador",
                    "percentagem": "0%"
                }
                return

    except Exception as e:
        estado_download = {
            "ativo": False,
            "mensagem": f"Erro: {str(e)}",
            "percentagem": "0%"
        }
        return
    finally:
        processo_atual = None

    estado_download = {
        "ativo": False,
        "mensagem": "Concluído!",
        "percentagem": "100%"
    }


@app.get("/status")
def obter_status():
    return JSONResponse(estado_download)


@app.get("/", response_class=HTMLResponse)
def home():
    os.makedirs(DIRETORIO_MUSICAS, exist_ok=True)
    os.makedirs(DIRETORIO_ALBUNS, exist_ok=True)
    os.makedirs(DIRETORIO_VIDEOS, exist_ok=True)

    lista_musicas = glob.glob(os.path.join(DIRETORIO_MUSICAS, "*.mp3"))
    lista_albuns = glob.glob(os.path.join(DIRETORIO_ALBUNS, "*.mp3"))
    lista_videos = glob.glob(os.path.join(DIRETORIO_VIDEOS, "*.mp4"))

    try:
        total, usado, livre = shutil.disk_usage(DIRETORIO_RAIZ if os.path.exists(DIRETORIO_RAIZ) else "/")
        total_gb = total / (2**30)
        livre_gb = livre / (2**30)
        usado_gb = usado / (2**30)
        pct_usado = (usado / total) * 100
    except Exception:
        total_gb, livre_gb, usado_gb, pct_usado = 0, 0, 0, 0

    global processo_atual, estado_download
    a_baixar = estado_download["ativo"]

    def gerar_tabela(lista, nome_grupo):
        if not lista:
            return "<tr><td colspan='5' style='text-align: center; color: #777; padding: 18px;'>Pasta vazia.</td></tr>"

        html = ""
        for i, f in enumerate(sorted(lista), start=1):
            nome = os.path.basename(f)
            tamanho = os.path.getsize(f) / (1024 * 1024)
            caminho_encoded = quote(f, safe="")
            html += f"""
                <tr class="file-row" data-name="{nome.lower()}">
                    <td style="width: 32px; text-align: center;"><input type="checkbox" name="selecionados" data-grupo="{nome_grupo}" value="{caminho_encoded}" style="cursor: pointer;"></td>
                    <td style="width: 34px; color: #1db954; font-weight: bold;">{i}.</td>
                    <td>
                        <span id="nome-txt-{i}-{nome_grupo}" style="word-break: break-word;">{nome}</span>
                        <form action="/renomear" method="post" id="form-renomear-{i}-{nome_grupo}" style="display:none; margin-top: 6px;">
                            <input type="hidden" name="caminho_antigo" value="{f}">
                            <input type="text" name="novo_nome" value="{nome}" style="padding: 5px 8px; font-size: 12px; width: 68%; display: inline-block; margin: 0;">
                            <button type="submit" style="padding: 5px 10px; font-size: 11px; width: auto; margin: 0;">Guardar</button>
                            <button type="button" onclick="cancelarEdicao({i}, '{nome_grupo}')" class="danger-btn" style="padding: 5px 10px; font-size: 11px; width: auto; margin: 0;">X</button>
                        </form>
                    </td>
                    <td style="color: #999; text-align: right; width: 78px; font-family: monospace;">{tamanho:.1f} MB</td>
                    <td style="text-align: right; width: 205px; white-space: nowrap;">
                        <button type="button" onclick="ativarEdicao({i}, '{nome_grupo}')" class="secondary-btn" style="padding: 4px 8px; font-size: 11px;">[Renomear]</button>
                        <a href="/download?caminho={caminho_encoded}" class="action-link download-link">[Baixar]</a>
                        <a href="/apagar?caminho={caminho_encoded}" class="action-link delete-link">[Apagar]</a>
                    </td>
                </tr>
            """
        return html

    tabela_musicas = gerar_tabela(lista_musicas, "musicas")
    tabela_albuns = gerar_tabela(lista_albuns, "albuns")
    tabela_videos = gerar_tabela(lista_videos, "videos")

    if a_baixar:
        pct_str = estado_download["percentagem"]
        pct_val = pct_str.replace('%', '')
        try:
            pct_num = float(pct_val)
        except ValueError:
            pct_num = 0

        painel_download = f"""
            <div class="progress-panel">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: #1db954; font-weight: bold;">⬇️ A processar conteúdo...</span>
                    <span id="status-pct" style="color: #fff; font-weight: bold; font-family: monospace;">{pct_str}</span>
                </div>
                <div style="background: #333; border-radius: 6px; height: 12px; width: 100%; overflow: hidden; margin-bottom: 12px;">
                    <div id="status-bar" style="background: #1db954; height: 100%; width: {pct_num}%; transition: width 0.4s ease;"></div>
                </div>
                <div id="status-msg" class="log-box">
                    {estado_download['mensagem']}
                </div>
                <form action="/parar" method="post" style="margin:0; text-align: center;">
                    <button type="submit" class="danger-btn" style="width: auto; padding: 8px 20px;">Parar / Cancelar Download</button>
                </form>
            </div>
            <script>
                (function pollStatus() {{
                    fetch('/status')
                        .then(r => r.json())
                        .then(data => {{
                            const pctEl = document.getElementById('status-pct');
                            const barEl = document.getElementById('status-bar');
                            const msgEl = document.getElementById('status-msg');
                            if (pctEl) pctEl.textContent = data.percentagem || '0%';
                            if (msgEl) msgEl.textContent = data.mensagem || '';
                            if (barEl) {{
                                const num = parseFloat((data.percentagem || '0').replace('%', '')) || 0;
                                barEl.style.width = Math.min(Math.max(num, 0), 100) + '%';
                            }}
                            if (data.ativo) {{
                                setTimeout(pollStatus, 1200);
                            }} else {{
                                window.location.reload();
                            }}
                        }})
                        .catch(() => setTimeout(pollStatus, 2500));
                }})();
            </script>
        """
    else:
        painel_download = """
            <form id="form-download" action="/baixar" method="post" onsubmit="return validarFormularioDownload()">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; gap: 8px;">
                        <button type="button" id="tab-single" class="mode-pill active" onclick="alternarEntrada('single')">Link Único</button>
                        <button type="button" id="tab-multi" class="mode-pill" onclick="alternarEntrada('multi')">Vários Links (1 por linha)</button>
                    </div>
                    <div style="display: flex; gap: 6px;">
                        <button type="button" class="mini-btn" onclick="colarUrl()">📋 Colar</button>
                        <button type="button" class="mini-btn" onclick="limparUrl()">× Limpar</button>
                    </div>
                </div>

                <input type="text" id="url-single" name="url" placeholder="Cole o link do vídeo ou playlist..." autocomplete="off">
                <textarea id="url-multi" name="urls_lote" rows="4" placeholder="Cole vários links, um por linha (ex.: vários vídeos do OK.ru ou YouTube)..." style="display: none;"></textarea>

                <div class="controls-row">
                    <select name="modo" id="modo-select" onchange="atualizarParametros()" style="flex: 2;">
                        <option value="musica_individual">🎵 Áudio MP3: Música Individual (Ignora Playlist)</option>
                        <option value="playlist_completa">🎶 Áudio MP3: Playlist Completa</option>
                        <option value="album">💿 Áudio MP3: Álbum Completo (Com Capítulos)</option>
                        <option value="video">🎬 Vídeo MP4: Vídeo Único e Individual</option>
                        <option value="video_playlist">🎞️ Vídeo MP4: Playlist Completa</option>
                    </select>

                    <select name="qualidade" id="audio-qualidade" style="flex: 1;">
                        <option value="192">Áudio Padrão (192 kbps)</option>
                        <option value="320">Alta Fidelidade (320 kbps)</option>
                    </select>

                    <select name="qualidade" id="video-qualidade" style="flex: 1; display: none;">
                        <option value="max">Resolução Máxima (HD/4K)</option>
                        <option value="720p">Equilibrado (720p HD)</option>
                        <option value="480p">Económico (480p)</option>
                    </select>
                </div>
                <button type="submit">Iniciar Download</button>
            </form>
            <script>
                function atualizarParametros() {
                    const modo = document.getElementById('modo-select').value;
                    const audioSelect = document.getElementById('audio-qualidade');
                    const videoSelect = document.getElementById('video-qualidade');

                    if (modo === 'video' || modo === 'video_playlist') {
                        audioSelect.style.display = 'none';
                        audioSelect.name = 'ignorar';
                        videoSelect.style.display = 'block';
                        videoSelect.name = 'qualidade';
                    } else {
                        videoSelect.style.display = 'none';
                        videoSelect.name = 'ignorar';
                        audioSelect.style.display = 'block';
                        audioSelect.name = 'qualidade';
                    }
                }

                function alternarEntrada(tipo) {
                    const singleEl = document.getElementById('url-single');
                    const multiEl = document.getElementById('url-multi');
                    const tabSingle = document.getElementById('tab-single');
                    const tabMulti = document.getElementById('tab-multi');

                    if (tipo === 'multi') {
                        singleEl.style.display = 'none';
                        multiEl.style.display = 'block';
                        tabMulti.classList.add('active');
                        tabSingle.classList.remove('active');
                        multiEl.focus();
                    } else {
                        multiEl.style.display = 'none';
                        singleEl.style.display = 'block';
                        tabSingle.classList.add('active');
                        tabMulti.classList.remove('active');
                        singleEl.focus();
                    }
                }

                function validarFormularioDownload() {
                    const isMulti = document.getElementById('url-multi').style.display !== 'none';
                    const valor = isMulti
                        ? document.getElementById('url-multi').value.trim()
                        : document.getElementById('url-single').value.trim();
                    if (!valor) {
                        alert('Cole pelo menos um link antes de iniciar o download.');
                        return false;
                    }
                    return true;
                }

                async function colarUrl() {
                    try {
                        const texto = await navigator.clipboard.readText();
                        if (!texto) return;
                        const isMulti = document.getElementById('url-multi').style.display !== 'none';
                        if (isMulti) {
                            const el = document.getElementById('url-multi');
                            el.value = el.value ? el.value.trimEnd() + '\\n' + texto.trim() : texto.trim();
                        } else {
                            document.getElementById('url-single').value = texto.trim();
                        }
                    } catch (err) {
                        console.warn('Clipboard indisponível:', err);
                    }
                }

                function limparUrl() {
                    document.getElementById('url-single').value = '';
                    document.getElementById('url-multi').value = '';
                }
            </script>
        """

    cor_barra = '#d9534f' if pct_usado > 90 else '#1db954'
    limpar_musicas = f'<form action="/limpar-pasta" method="post" style="margin:0;"><input type="hidden" name="pasta" value="musicas"><button type="submit" class="danger-btn" style="padding: 6px 12px; font-size: 13px; width: auto;">Limpar Tudo</button></form>' if lista_musicas else ''
    limpar_albuns = f'<form action="/limpar-pasta" method="post" style="margin:0;"><input type="hidden" name="pasta" value="albuns"><button type="submit" class="danger-btn" style="padding: 6px 12px; font-size: 13px; width: auto;">Limpar Tudo</button></form>' if lista_albuns else ''
    limpar_videos = f'<form action="/limpar-pasta" method="post" style="margin:0;"><input type="hidden" name="pasta" value="videos"><button type="submit" class="danger-btn" style="padding: 6px 12px; font-size: 13px; width: auto;">Limpar Tudo</button></form>' if lista_videos else ''

    disabled_attr_musicas = "" if lista_musicas else "disabled"
    disabled_attr_albuns = "" if lista_albuns else "disabled"
    disabled_attr_videos = "" if lista_videos else "disabled"

    return f"""
    <html>
        <head>
            <title>TerminalTube [v2.5]</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%23121212%22/><text x=%2250%%22 y=%2262%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22monospace%22 font-weight=%22bold%22 font-size=%2250%22 fill=%22%231db954%22>%3E_</text></svg>">
            <style>
                body {{ font-family: Arial, sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; margin: 0; padding: 24px; box-sizing: border-box; }}
                .container {{ max-width: 950px; width: 100%; display: flex; flex-direction: column; gap: 18px; }}
                .card {{ background: #1e1e1e; padding: 22px 24px; border-radius: 12px; border: 1px solid #2a2a2a; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }}
                h2, h3 {{ margin-top: 0; color: #1db954; text-align: center; }}
                h3 {{ text-align: left; font-size: 16px; color: #fff; }}
                input[type="text"], textarea, select {{ width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #3d3d3d; background: #292929; color: #fff; border-radius: 8px; box-sizing: border-box; font-size: 14px; transition: border-color 0.2s; }}
                input[type="text"]:focus, textarea:focus, select:focus {{ outline: none; border-color: #1db954; }}
                textarea {{ resize: vertical; font-family: monospace; font-size: 12.5px; }}
                select {{ cursor: pointer; }}
                button {{ background: #1db954; color: #fff; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; font-size: 16px; transition: background 0.2s, opacity 0.2s; margin-top: 10px; }}
                button:hover:not(:disabled) {{ background: #1aa34a; }}
                button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
                .secondary-btn {{ background: #303030; font-size: 12.5px; padding: 6px 12px; width: auto; margin: 0; border: 1px solid #3e3e3e; }}
                .secondary-btn:hover:not(:disabled) {{ background: #3d3d3d; }}
                .toggle-btn {{ background: #242424; color: #1db954; border: 1px solid #383838; font-size: 12px; padding: 6px 11px; width: auto; margin: 0; }}
                .toggle-btn:hover {{ background: #2c2c2c; }}
                .zip-btn {{ background: #1db954; color: #fff; border: none; }}
                .danger-btn {{ background: #d9534f !important; border: none !important; }}
                .danger-btn:hover:not(:disabled) {{ background: #c9302c !important; }}
                .mode-pill {{ background: #282828; color: #bbb; border: 1px solid #3a3a3a; padding: 5px 12px; font-size: 12px; width: auto; margin: 0; border-radius: 999px; }}
                .mode-pill.active {{ background: #1a2e22; color: #1db954; border-color: #1db954; }}
                .mini-btn {{ background: #282828; color: #ccc; border: 1px solid #3a3a3a; padding: 5px 10px; font-size: 11.5px; width: auto; margin: 0; border-radius: 6px; }}
                .mini-btn:hover {{ background: #363636; color: #fff; }}
                .controls-row {{ display: flex; gap: 10px; }}
                .progress-panel {{ background: #18261d; border: 1px solid #1db954; padding: 20px; border-radius: 10px; }}
                .log-box {{ background: #111; border: 1px solid #282828; border-radius: 6px; padding: 9px 12px; margin-bottom: 14px; font-family: monospace; font-size: 12px; color: #bbb; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
                .filter-input {{ padding: 7px 10px !important; margin: 0 0 10px 0 !important; font-size: 12.5px !important; background: #232323 !important; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 13px; }}
                th, td {{ padding: 8px; border-bottom: 1px solid #2d2d2d; text-align: left; }}
                .file-row:hover {{ background: #252525; }}
                .file-list {{ max-height: 220px; overflow-y: auto; }}
                .section-header {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }}
                .section-title-group {{ display: flex; align-items: center; gap: 10px; cursor: pointer; }}
                .section-body {{ display: none; margin-top: 12px; padding-top: 12px; border-top: 1px solid #2e2e2e; }}
                .section-body.open {{ display: block; }}
                .actions-bar {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
                .storage-bar {{ background: #242424; padding: 11px 15px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; display: flex; justify-content: space-between; align-items: center; gap: 12px; border: 1px solid #313131; }}
                .action-link {{ text-decoration: none; font-weight: bold; font-size: 12px; }}
                .download-link {{ color: #1db954; margin-left: 8px; margin-right: 8px; }}
                .delete-link {{ color: #ff5555; }}
                @media (max-width: 640px) {{
                    body {{ padding: 12px; }}
                    .controls-row {{ flex-direction: column; gap: 4px; }}
                    .storage-bar {{ flex-direction: column; align-items: flex-start; }}
                }}
            </style>
            <script>
                function alternarSecao(grupo) {{
                    const bodyEl = document.getElementById('corpo-' + grupo);
                    const btnEl = document.getElementById('btn-toggle-' + grupo);
                    if (!bodyEl || !btnEl) return;
                    const vaiAbrir = !bodyEl.classList.contains('open');
                    bodyEl.classList.toggle('open', vaiAbrir);
                    btnEl.textContent = vaiAbrir ? '▾ [Recolher]' : '▸ [Expandir]';
                }}
                function ativarEdicao(i, grupo) {{
                    document.getElementById('nome-txt-' + i + '-' + grupo).style.display = 'none';
                    document.getElementById('form-renomear-' + i + '-' + grupo).style.display = 'block';
                }}
                function cancelarEdicao(i, grupo) {{
                    document.getElementById('form-renomear-' + i + '-' + grupo).style.display = 'none';
                    document.getElementById('nome-txt-' + i + '-' + grupo).style.display = 'inline';
                }}
                function selecionarTodos(grupo, marcar) {{
                    const checkboxes = document.querySelectorAll('input[name="selecionados"][data-grupo="' + grupo + '"]');
                    checkboxes.forEach(cb => {{
                        const row = cb.closest('tr');
                        if (!row || row.style.display !== 'none') {{
                            cb.checked = marcar;
                        }}
                    }});
                }}
                function baixarSelecionadosSequencial(grupo) {{
                    const checkboxes = Array.from(document.querySelectorAll('input[name="selecionados"][data-grupo="' + grupo + '"]:checked'));
                    if (checkboxes.length === 0) {{
                        alert('Selecione pelo menos um arquivo para baixar.');
                        return;
                    }}
                    checkboxes.forEach((cb, idx) => {{
                        setTimeout(() => {{
                            const link = document.createElement('a');
                            link.href = '/download?caminho=' + cb.value;
                            link.style.display = 'none';
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                        }}, idx * 350);
                    }});
                }}
                function filtrarTabela(grupo, termo) {{
                    const q = (termo || '').trim().toLowerCase();
                    const rows = document.querySelectorAll('#tabela-' + grupo + ' tr.file-row');
                    rows.forEach(row => {{
                        const nome = row.getAttribute('data-name') || '';
                        row.style.display = nome.includes(q) ? '' : 'none';
                    }});
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h2>TerminalTube 🚀</h2>

                    <div class="storage-bar">
                        <span>💾 <b>Armazenamento (/media):</b> {usado_gb:.1f} GB usados / {total_gb:.1f} GB totais (<span style="color: #1db954;">{livre_gb:.1f} GB livres</span>)</span>
                        <div style="background: #333; width: 150px; height: 8px; border-radius: 4px; overflow: hidden; flex-shrink: 0;">
                            <div style="background: {cor_barra}; height: 100%; width: {pct_usado:.1f}%;"></div>
                        </div>
                    </div>

                    {painel_download}
                </div>

                <div class="card">
                    <div class="section-header">
                        <div class="section-title-group" onclick="alternarSecao('musicas')">
                            <button type="button" id="btn-toggle-musicas" class="toggle-btn" onclick="event.stopPropagation(); alternarSecao('musicas')">▸ [Expandir]</button>
                            <h3 style="margin:0;">🎵 Músicas / Playlists ({len(lista_musicas)})</h3>
                        </div>
                        <div class="actions-bar">
                            <button type="button" class="secondary-btn" onclick="selecionarTodos('musicas', false)" {disabled_attr_musicas}>[Nenhum]</button>
                            <button type="button" class="secondary-btn" onclick="selecionarTodos('musicas', true)" {disabled_attr_musicas}>[Todos]</button>
                            <button type="button" class="secondary-btn zip-btn" onclick="baixarSelecionadosSequencial('musicas')" {disabled_attr_musicas}>Baixar Selecionados</button>
                            {limpar_musicas}
                        </div>
                    </div>
                    <div id="corpo-musicas" class="section-body">
                        <input type="text" class="filter-input" placeholder="Filtrar músicas nesta pasta..." oninput="filtrarTabela('musicas', this.value)">
                        <div class="file-list">
                            <table id="tabela-musicas">{tabela_musicas}</table>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="section-header">
                        <div class="section-title-group" onclick="alternarSecao('albuns')">
                            <button type="button" id="btn-toggle-albuns" class="toggle-btn" onclick="event.stopPropagation(); alternarSecao('albuns')">▸ [Expandir]</button>
                            <h3 style="margin:0;">💿 Álbuns com Capítulos ({len(lista_albuns)})</h3>
                        </div>
                        <div class="actions-bar">
                            <button type="button" class="secondary-btn" onclick="selecionarTodos('albuns', false)" {disabled_attr_albuns}>[Nenhum]</button>
                            <button type="button" class="secondary-btn" onclick="selecionarTodos('albuns', true)" {disabled_attr_albuns}>[Todos]</button>
                            <button type="button" class="secondary-btn zip-btn" onclick="baixarSelecionadosSequencial('albuns')" {disabled_attr_albuns}>Baixar Selecionados</button>
                            {limpar_albuns}
                        </div>
                    </div>
                    <div id="corpo-albuns" class="section-body">
                        <input type="text" class="filter-input" placeholder="Filtrar álbuns nesta pasta..." oninput="filtrarTabela('albuns', this.value)">
                        <div class="file-list">
                            <table id="tabela-albuns">{tabela_albuns}</table>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="section-header">
                        <div class="section-title-group" onclick="alternarSecao('videos')">
                            <button type="button" id="btn-toggle-videos" class="toggle-btn" onclick="event.stopPropagation(); alternarSecao('videos')">▸ [Expandir]</button>
                            <h3 style="margin:0;">🎬 Vídeos MP4 ({len(lista_videos)})</h3>
                        </div>
                        <div class="actions-bar">
                            <button type="button" class="secondary-btn" onclick="selecionarTodos('videos', false)" {disabled_attr_videos}>[Nenhum]</button>
                            <button type="button" class="secondary-btn" onclick="selecionarTodos('videos', true)" {disabled_attr_videos}>[Todos]</button>
                            <button type="button" class="secondary-btn zip-btn" onclick="baixarSelecionadosSequencial('videos')" {disabled_attr_videos}>Baixar Selecionados</button>
                            {limpar_videos}
                        </div>
                    </div>
                    <div id="corpo-videos" class="section-body">
                        <input type="text" class="filter-input" placeholder="Filtrar vídeos nesta pasta..." oninput="filtrarTabela('videos', this.value)">
                        <div class="file-list">
                            <table id="tabela-videos">{tabela_videos}</table>
                        </div>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """


@app.post("/baixar", response_class=HTMLResponse)
def iniciar_download(
    background_tasks: BackgroundTasks,
    url: str = Form(""),
    urls_lote: str = Form(""),
    modo: str = Form(...),
    qualidade: str = Form("192")
):
    lista_urls = []
    if urls_lote and urls_lote.strip():
        lista_urls = [linha.strip() for linha in urls_lote.splitlines() if linha.strip()]
    elif url and url.strip():
        lista_urls = [url.strip()]

    if lista_urls:
        background_tasks.add_task(executar_download, lista_urls, modo, qualidade)
    return RedirectResponse(url="/", status_code=303)


@app.post("/parar")
def parar_download():
    global processo_atual, estado_download
    estado_download["ativo"] = False
    if processo_atual and processo_atual.poll() is None:
        try:
            processo_atual.kill()
        except Exception:
            pass
    processo_atual = None
    estado_download = {"ativo": False, "mensagem": "Cancelado pelo utilizador", "percentagem": "0%"}
    return RedirectResponse(url="/", status_code=303)


@app.get("/download")
def descarregar_ficheiro(caminho: str):
    if caminho.startswith(DIRETORIO_RAIZ) and os.path.exists(caminho):
        media_type = 'video/mp4' if caminho.endswith('.mp4') else 'audio/mpeg'
        return FileResponse(caminho, media_type=media_type, filename=os.path.basename(caminho))
    return RedirectResponse(url="/", status_code=303)


@app.post("/renomear")
def renomear_ficheiro(caminho_antigo: str = Form(...), novo_nome: str = Form(...)):
    if caminho_antigo.startswith(DIRETORIO_RAIZ) and os.path.exists(caminho_antigo):
        diretorio = os.path.dirname(caminho_antigo)
        novo_nome_limpo = os.path.basename(novo_nome)
        caminho_novo = os.path.join(diretorio, novo_nome_limpo)
        if not os.path.exists(caminho_novo):
            os.rename(caminho_antigo, caminho_novo)
    return RedirectResponse(url="/", status_code=303)


@app.post("/download-lote")
def descarregar_lote(selecionados: list[str] = Form(default=[])):
    if not selecionados:
        return RedirectResponse(url="/", status_code=303)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for caminho in selecionados:
            if caminho.startswith(DIRETORIO_RAIZ) and os.path.exists(caminho):
                zip_file.write(caminho, arcname=os.path.basename(caminho))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=terminaltube-selecionada.zip"}
    )


@app.get("/apagar")
def apagar_ficheiro(caminho: str):
    if caminho.startswith(DIRETORIO_RAIZ) and os.path.exists(caminho):
        os.remove(caminho)
    return RedirectResponse(url="/", status_code=303)


@app.post("/limpar-pasta")
def limpar_pasta(pasta: str = Form(...)):
    if pasta == "musicas":
        dir_alvo = DIRETORIO_MUSICAS
        ext = "*.mp3"
    elif pasta == "albuns":
        dir_alvo = DIRETORIO_ALBUNS
        ext = "*.mp3"
    else:
        dir_alvo = DIRETORIO_VIDEOS
        ext = "*.mp4"

    for f in glob.glob(os.path.join(dir_alvo, ext)):
        os.remove(f)
    return RedirectResponse(url="/", status_code=303)