FROM python:3.11-slim

# Instala o FFmpeg (obrigatório para fusão de vídeo/áudio e conversão MP3) e utilitários
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código principal
COPY app.py .

# Cria a estrutura de diretórios para volumes persistentes
RUN mkdir -p /app/media/audio/musicas /app/media/audio/albuns /app/media/video/mp4

EXPOSE 80

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]