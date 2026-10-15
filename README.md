# TerminalTube 🚀

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

## 🛠️ Guia de Instalação Prática

### Opção A: A forma mais rápida (Via Docker)
Recomendado para servidores, NAS ou Raspberry Pi.

1. Crie um ficheiro chamado `docker-compose.yml`:
   ```yaml
   services:
     terminaltube:
       image: dockerrissi/terminaltube:latest
       container_name: terminaltube
       ports:
         - "8200:80"
       volumes:
         - ./media:/app/media
       restart: unless-stopped