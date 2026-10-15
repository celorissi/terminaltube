#!/bin/bash
echo "🚀 A iniciar o TerminalTube..."

if [ ! -d "venv" ]; then
    echo "⚠️ Ambiente virtual não encontrado. A executar o instalador..."
    python3 install.py
fi

# Ativar ambiente virtual
source venv/bin/activate

echo "🌐 A abrir o servidor FastAPI em http://0.0.0.0:8200"
uvicorn app:app --host 0.0.0.0 --port 8200