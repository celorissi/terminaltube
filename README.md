# TerminalTube 🚀
<p align="center">
  <img src="assets/terminaltube.png" alt="TerminalTube Dashboard" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.110.0-005571?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/docker/image-size/dockerrissi/terminaltube/latest?style=flat-square" alt="Docker Image Size">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License MIT">
</p>

O **TerminalTube** é um painel web leve, moderno e autónomo desenvolvido em **FastAPI** para gerir e descarregar conteúdos multimédia do YouTube (Músicas, Playlists, Álbuns com Capítulos e Vídeos MP4) de forma totalmente organizada. Focado principalmente em ambientes **Linux e Raspberry Pi**.

---

## 🌟 Funcionalidades
- 💾 **Monitor de Armazenamento em Tempo Real:** Acompanhe o espaço livre e ocupado no disco `/media`.
- 🎵 **Modos Flexíveis:** Suporte para músicas individuais (com opção de ignorar playlists), playlists completas, álbuns com divisão automática de capítulos e vídeos MP4 com seletor de resolução.
- ✏️ **Personalização e Gestão:** Defina nomes personalizados no download, renomeie, apague ou descarregue ficheiros em lote (arquivos `.zip`) diretamente pela interface web.
- 🐧 **Multi-arquitetura:** Pronto para correr via Docker (x86_64, ARM, Raspberry Pi) ou de forma nativa em sistemas Linux.

---

## 🚀 Instalação e Execução

### Opção A: A forma mais rápida (Via Imagem Oficial)
Ideal para quem quer apenas correr o container rapidamente sem clonar o código-fonte:

1. Crie um ficheiro chamado `docker-compose.yml`:
   ```yaml
   services:
     terminaltube:
       image: dockerrissi/terminaltube:latest
       container_name: terminaltube
       ports:
         - "8200:8200"
       volumes:
         - ./media:/app/media
       restart: unless-stopped
   ```
2. Inicie o container:
   ```bash
   docker compose up -d
   ```

### Opção B: Clonar e Executar (Desenvolvimento / Build Local)
Ideal para ambientes como o Raspberry Pi onde deseja compilar localmente a partir do código:

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/celorissi/terminaltube.git
   cd terminaltube
   ```

2. **Iniciar com o Docker Compose:**
   ```bash
   docker compose up --build -d
   ```

3. **Aceder à aplicação:**
   Abra o seu browser e aceda a:
   👉 **`http://localhost:8200`**

Para verificar se o container está a ser executado corretamente, pode consultar os logs com:
```bash
docker logs -f terminaltube
```

---

## 📂 Estrutura do Projeto

Ao clonar o repositório, encontrará a seguinte organização de ficheiros:

| Ficheiro / Pasta | Descrição |
| :--- | :--- |
| **`app.py`** | Código principal da aplicação em **FastAPI** (gere a interface web, rotas, lógica de download com `yt-dlp` e monitor de armazenamento). |
| **`requirements.txt`** | Lista de dependências Python necessárias (`fastapi`, `uvicorn`, `yt-dlp`, `python-multipart`). |
| **`install.py`** | Script auxiliar em Python que automatiza a criação do ambiente virtual (`venv`) e a instalação das dependências em Linux. |
| **`start.sh`** | Script de arranque rápido para sistemas Linux e Raspberry Pi (`./start.sh`) que ativa o ambiente e inicia o servidor web. |
| **`Dockerfile`** | Configuração oficial para empacotar a aplicação num container Docker otimizado (Python 3.11 slim + FFmpeg). |
| **`docker-compose.yml`** | Ficheiro de orquestração para subir o serviço rapidamente via Docker (`docker compose up -d`). |
| **`.github/workflows/`** | Automação (CI/CD) do GitHub Actions para compilar e publicar automaticamente imagens multi-arquitetura no Docker Hub. |
| **`.gitignore`** | Define ficheiros e pastas ignoradas pelo Git (ex: ambiente virtual `venv/`, pasta local `media/` e caches). |
| **`.dockerignore`** | Otimiza o build do Docker ignorando ficheiros desnecessários para a imagem. |
| **`LICENSE`** | Ficheiro de licenciamento do projeto sob os termos da licença **MIT**. |

---

## 🧹 Desinstalação e Limpeza Completa (Do Zero)

Se precisar de remover completamente a aplicação, apagar todos os volumes de dados e limpar as imagens Docker associadas para reiniciar num estado totalmente limpo, execute os seguintes comandos na raiz do projeto:

1. **Parar e remover os containers e volumes:**
   ```bash
   docker compose down -v --remove-orphans
   ```
   *(O terminal deve confirmar a remoção do container e da rede associada).*

2. **Remover a imagem Docker local:**
   ```bash
   docker rmi terminaltube-terminaltube dockerrissi/terminaltube:latest --force 2>/dev/null
   ```
   *(O terminal confirmará a eliminação das camadas de imagem armazenadas).*

3. **Limpar diretoria de multimédia (opcional):**
   Caso queira apagar também todos os ficheiros descarregados guardados no volume local:
   ```bash
   rm -rf media/
   ```
   *(Execute `ls -la` para garantir que a pasta foi removida com sucesso).*