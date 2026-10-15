FROM python:3.11-slim

# Instalar dependências do sistema (FFmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

EXPOSE 8200

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8200"]