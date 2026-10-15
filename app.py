# ==========================================
# TerminalTube - Versão 2.4 (Systemd)
# Data: Outubro 2026
# Descrição: Dashboard multimédia com monitor
#            de espaço, seletores, nome personalizado,
#            ignorar playlist e renomeação direta.
# ==========================================

from fastapi import FastAPI, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse
import os
import glob
import subprocess
import zipfile
import io
import re
import shutil

app = FastAPI()

DIRETORIO_RAIZ = '/home/marcelo/laboratorios/yt-dlp/media'
DIRETORIO_MUSICAS = os.path.join(DIRETORIO_RAIZ, 'audio/musicas')
DIRETORIO_ALBUNS = os.path.join(DIRETORIO_RAIZ, 'audio/albuns')
DIRETORIO_VIDEOS = os.path.join(DIRETORIO_RAIZ, 'video/mp4')
BIN_YTDLP = '/home/marcelo/laboratorios/yt-dlp/venv/bin/yt-dlp'



processo_atual = None
estado_download = {
    "ativo": False,
    "mensagem": "A aguardar...",
    "percentagem": "0%"
}

def executar_download(url: str, modo: str, param_qualidade: str = "192"):
    global processo_atual, estado_download
    estado_download = {"ativo": True, "mensagem": "A iniciar ligação ao YouTube...", "percentagem": "0%"}
    
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
        
        if param_qualidade == "720p":
            formato_str = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif param_qualidade == "480p":
            formato_str = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
        else: # "max"
            formato_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        cmd = [
            BIN_YTDLP,
            '--no-playlist',
            '-f', formato_str,
            '--merge-output-format', 'mp4',
            '-o', os.path.join(pasta_destino, '%(title)s.%(ext)s'),
            '--ignore-errors',
            url
        ]
    elif modo == "musica_individual":
        pasta_destino = DIRETORIO_MUSICAS
        cmd = [
            BIN_YTDLP,
            '--no-playlist',  # Força ignorar a playlist mesmo se o link contiver &list=
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', param_qualidade,
            '-o', os.path.join(pasta_destino, '%(autonumber)02d. %(title)s.%(ext)s'),
            '--ignore-errors',
            url
        ]
    else: # playlist_completa
        pasta_destino = DIRETORIO_MUSICAS
        cmd = [
            BIN_YTDLP,
            '--yes-playlist',  # Permite baixar a playlist completa
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', param_qualidade,
            '-o', os.path.join(pasta_destino, '%(playlist_index)s. %(title)s.%(ext)s'),
            '--ignore-errors',
            url
        ]

    os.makedirs(pasta_destino, exist_ok=True)
    try:
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
                estado_download["mensagem"] = linha_limpa
                match = re.search(r'(\d+\.\d+)%', linha_limpa)
                if match:
                    estado_download["percentagem"] = f"{match.group(1)}%"
                    
        processo_atual.wait()
    except Exception as e:
        estado_download["mensagem"] = f"Erro: {str(e)}"
    finally:
        processo_atual = None
        estado_download = {"ativo": False, "mensagem": "Concluído!", "percentagem": "100%"}

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

    meta_refresh = '<meta http-equiv="refresh" content="2">' if a_baixar else ''

    def gerar_tabela(lista, nome_grupo):
        if not lista:
            return "<tr><td colspan='5' style='text-align: center; color: #777;'>Pasta vazia.</td></tr>"
        
        html = ""
        for i, f in enumerate(sorted(lista), start=1):
            nome = os.path.basename(f)
            tamanho = os.path.getsize(f) / (1024 * 1024)
            html += f"""
                <tr>
                    <td style="width: 30px; text-align: center;"><input type="checkbox" name="selecionados" value="{f}" form="form-{nome_grupo}" style="cursor: pointer;"></td>
                    <td style="width: 30px; color: #1db954; font-weight: bold;">{i}.</td>
                    <td>{nome}</td>
                    <td style="color: #888; text-align: right; width: 70px;">{tamanho:.1f} MB</td>
                    <td style="text-align: right; width: 140px;">
                        <a href="/download?caminho={f}" style="color: #1db954; text-decoration: none; font-weight: bold; margin-right: 10px;">[Baixar]</a>
                        <a href="/apagar?caminho={f}" style="color: #ff5555; text-decoration: none; font-weight: bold;">[Apagar]</a>
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
            <div style="background: #1a2c1a; border: 1px solid #1db954; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: #1db954; font-weight: bold;">⬇️ A processar conteúdo do YouTube...</span>
                    <span style="color: #fff; font-weight: bold; font-family: monospace;">{pct_str}</span>
                </div>
                <div style="background: #333; border-radius: 6px; height: 12px; width: 100%; overflow: hidden; margin-bottom: 12px;">
                    <div style="background: #1db954; height: 100%; width: {pct_num}%; transition: width 0.5s ease;"></div>
                </div>
                <div style="background: #111; border-radius: 4px; padding: 8px; margin-bottom: 15px; font-family: monospace; font-size: 12px; color: #aaa; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {estado_download['mensagem']}
                </div>
                <form action="/parar" method="post" style="margin:0; text-align: center;">
                    <button type="submit" class="danger-btn" style="width: auto; padding: 8px 20px;">Parar / Cancelar Download</button>
                </form>
            </div>
        """
    else:
        painel_download = """
            <form action="/baixar" method="post">
                <input type="text" name="url" placeholder="Cole o link do YouTube..." required autocomplete="off">
                <div style="display: flex; gap: 10px;">
                    <select name="modo" id="modo-select" onchange="atualizarParametros()" style="flex: 2;">
                        <option value="musica_individual">🎵 Áudio MP3: Música Individual (Ignora Playlist)</option>
                        <option value="playlist_completa">🎶 Áudio MP3: Playlist Completa</option>
                        <option value="album">💿 Áudio MP3: Álbum Completo (Com Capítulos)</option>
                        <option value="video">🎬 Vídeo MP4: Vídeo Único e Individual</option>
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
                    
                    if (modo === 'video') {
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
            </script>
        """

    return f"""
    <html>
        <head>
            <title>TerminalTube [v2.4]</title>
            <meta charset="utf-8">
            <!-- Favicon Vetorial Incorporado (Terminal >_) -->
            <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%23121212%22/><text x=%2250%%22 y=%2262%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22monospace%22 font-weight=%22bold%22 font-size=%2250%22 fill=%22%231db954%22>%3E_</text></svg>">
            {meta_refresh}
            <style>
                body {{ font-family: Arial, sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; margin: 0; padding: 30px; box-sizing: border-box; }}
                .container {{ width: 950px; display: flex; flex-direction: column; gap: 20px; }}
                .card {{ background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }}
                h2, h3 {{ margin-top: 0; color: #1db954; text-align: center; }}
                h3 {{ text-align: left; font-size: 16px; color: #fff; }}
                input[type="text"], select {{ width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #444; background: #2b2b2b; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 14px; }}
                select {{ cursor: pointer; }}
                button {{ background: #1db954; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; font-size: 16px; transition: background 0.3s; margin-top: 10px; }}
                button:hover {{ background: #1aa34a; }}
                .secondary-btn {{ background: #333; font-size: 13px; padding: 6px 12px; width: auto; margin: 0; }}
                .secondary-btn:hover {{ background: #444; }}
                .danger-btn {{ background: #d9534f !important; }}
                .danger-btn:hover {{ background: #c9302c !important; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
                th, td {{ padding: 8px; border-bottom: 1px solid #333; text-align: left; }}
                .file-list {{ max-height: 200px; overflow-y: auto; display: block; }}
                table {{ display: table; width: 100%; }}
                .section-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 8px; }}
                .actions-bar {{ display: flex; gap: 10px; align-items: center; }}
                .storage-bar {{ background: #252525; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 13px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h2>TerminalTube 🚀</h2>
                    
                    <!-- Indicador de Espaço em Disco -->
                    <div class="storage-bar">
                        <span>💾 <b>Armazenamento (/media):</b> {usado_gb:.1f} GB usados / {total_gb:.1f} GB totais (<span style="color: #1db954;">{livre_gb:.1f} GB livres</span>)</span>
                        <div style="background: #333; width: 150px; height: 8px; border-radius: 4px; overflow: hidden; display: inline-block; vertical-align: middle; margin-left: 10px;">
                            <div style="background: {'#d9534f' if pct_usado > 90 else '#1db954'}; height: 100%; width: {pct_usado:.1f}%;"></div>
                        </div>
                    </div>

                    {painel_download}
                </div>

                <!-- Pasta Músicas / Playlists -->
                <div class="card">
                    <div class="section-header">
                        <h3 style="margin:0;">🎵 Músicas / Playlists ({len(lista_musicas)})</h3>
                        <div class="actions-bar">
                            <form id="form-musicas" action="/download-lote" method="post" style="margin:0;">
                                <button type="submit" class="secondary-btn">Baixar Selecionados (.zip)</button>
                            </form>
                            {f'<form action="/limpar-pasta" method="post" style="margin:0;"><input type="hidden" name="pasta" value="musicas"><button type="submit" class="danger-btn" style="padding: 6px 12px; font-size: 13px; width: auto;">Limpar Tudo</button></form>' if lista_musicas else ''}
                        </div>
                    </div>
                    <div class="file-list">
                        <table>{tabela_musicas}</table>
                    </div>
                </div>

                <!-- Pasta Álbuns -->
                <div class="card">
                    <div class="section-header">
                        <h3 style="margin:0;">💿 Álbuns com Capítulos ({len(lista_albuns)})</h3>
                        <div class="actions-bar">
                            <form id="form-albuns" action="/download-lote" method="post" style="margin:0;">
                                <button type="submit" class="secondary-btn">Baixar Selecionados (.zip)</button>
                            </form>
                            {f'<form action="/limpar-pasta" method="post" style="margin:0;"><input type="hidden" name="pasta" value="albuns"><button type="submit" class="danger-btn" style="padding: 6px 12px; font-size: 13px; width: auto;">Limpar Tudo</button></form>' if lista_albuns else ''}
                        </div>
                    </div>
                    <div class="file-list">
                        <table>{tabela_albuns}</table>
                    </div>
                </div>

                <!-- Pasta Vídeos MP4 -->
                <div class="card">
                    <div class="section-header">
                        <h3 style="margin:0;">🎬 Vídeos MP4 ({len(lista_videos)})</h3>
                        <div class="actions-bar">
                            <form id="form-videos" action="/download-lote" method="post" style="margin:0;">
                                <button type="submit" class="secondary-btn">Baixar Selecionados (.zip)</button>
                            </form>
                            {f'<form action="/limpar-pasta" method="post" style="margin:0;"><input type="hidden" name="pasta" value="videos"><button type="submit" class="danger-btn" style="padding: 6px 12px; font-size: 13px; width: auto;">Limpar Tudo</button></form>' if lista_videos else ''}
                        </div>
                    </div>
                    <div class="file-list">
                        <table>{tabela_videos}</table>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """

@app.post("/baixar", response_class=HTMLResponse)
def iniciar_download(background_tasks: BackgroundTasks, url: str = Form(...), modo: str = Form(...), qualidade: str = Form("192")):
    background_tasks.add_task(executar_download, url, modo, qualidade)
    return RedirectResponse(url="/", status_code=303)

@app.post("/parar")
def parar_download():
    global processo_atual, estado_download
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

@app.post("/download-lote")
def descarregar_lote(selecionados: list[str] = Form(...)):
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