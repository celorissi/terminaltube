import os
import sys
import subprocess
import platform

print("🚀 [TerminalTube] A iniciar instalador de dependências locais...")

if not os.path.exists("venv"):
    print("📦 A criar ambiente virtual Python (venv)...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

if platform.system() == "Windows":
    pip_path = os.path.join("venv", "Scripts", "pip")
else:
    pip_path = os.path.join("venv", "bin", "pip")

print("📥 A instalar dependências do requirements.txt...")
subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)

def verificar_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

if verificar_ffmpeg():
    print("✅ FFmpeg detetado com sucesso no sistema!")
else:
    print("⚠️ FFmpeg não encontrado no PATH do sistema. Recomenda-se instalar com: sudo apt install ffmpeg")

print("\n✨ Instalação concluída com sucesso! Pode iniciar com ./start.sh")
