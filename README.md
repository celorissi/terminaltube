# TerminalTube 🚀

O **TerminalTube** é um painel web leve, moderno e autónomo desenvolvido em **FastAPI** para gerir e descarregar conteúdos multimédia do YouTube (Músicas, Playlists, Álbuns com Capítulos e Vídeos MP4) de forma totalmente organizada.

---

## 🌟 Funcionalidades
- 💾 **Monitor de Armazenamento em Tempo Real:** Acompanhe o espaço livre e ocupado no disco `/media`.
- 🎵 **Modos Flexíveis:** Suporte para músicas individuais (com opção de ignorar playlists), playlists completas, álbuns com divisão automática de capítulos e vídeos MP4 com seletor de resolução.
- ✏️ **Personalização e Gestão:** Defina nomes personalizados no download, renomeie, apague ou descarregue ficheiros em lote (arquivos `.zip`) diretamente pela interface web.
- 🐧 **Multi-arquitetura:** Pronto para correr via Docker (Linux x86_64, ARM, Raspberry Pi) ou de forma nativa em sistemas Linux.

---

## 🛠️ Guia de Instalação Prática

### Opção A: A forma mais rápida (Via Docker)
Recomendado para servidores, NAS ou Raspberry Pi.

1. Crie um ficheiro chamado `docker-compose.yml`:
   ```yaml
   version: '3.8'

   services:
     terminaltube:
       image: dockerrissi/terminaltube:latest
       container_name: terminaltube
       ports:
         - "8200:80"
       volumes:
         - ./media:/app/media
       restart: unless-stopped
   ```

2. Inicie o container em segundo plano:
   ```bash
   docker compose up -d
   ```

3. Aceda no seu navegador a: `http://IP-DO-SEU-SERVIDOR:8200`

---

### Opção B: Instalação Nativa no Linux (Debian / Ubuntu / Raspberry Pi)
Se preferir correr diretamente no sistema sem Docker:

1. **Instalar dependências de sistema (FFmpeg):**
   ```bash
   sudo apt update && sudo apt install -y ffmpeg python3-pip python3-venv
   ```

2. **Clonar ou descarregar o projeto e entrar na pasta:**
   ```bash
   git clone https://github.com/SEU_UTILIZADOR/terminaltube.git
   cd terminaltube
   ```

3. **Executar o script de arranque automático:**
   O script `start.sh` encarrega-se de criar o ambiente virtual, instalar as dependências necessárias e abrir o servidor web.
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

4. Aceda no seu navegador a: `http://localhost:8200`

---

## 📋 Como Utilizar
1. Cole o link do vídeo, playlist ou álbum do YouTube no campo indicado.
2. (Opcional) Insira um nome personalizado para o ficheiro final.
3. Selecione o modo pretendido (Áudio Individual, Playlist, Álbum ou Vídeo MP4) e clique em **Iniciar Download**.
4. Acompanhe o progresso e gira os seus ficheiros diretamente nas tabelas abaixo.

## 📄 Licença
Distribuído sob a licença **MIT**. Veja o ficheiro `LICENSE` para mais detalhes.