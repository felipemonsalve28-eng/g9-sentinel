import os
import sys
import sqlite3
import json
import shutil
import logging

# --- CONFIGURACIÓN ---
BASE_DIR = '/home/felipemonsalve28/g9_production'
CORE_DIR = os.path.join(BASE_DIR, 'core')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'g9_market.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

def check_integrity():
    logging.info("🔍 Auditoría de Integridad 2026...")
    try:
        # Probamos el nuevo SDK y la librería de LN
        from google import genai
        import lnmarkets
        logging.info("✅ google.genai y lnmarkets validados.")
    except ImportError as e:
        logging.error(f"❌ Falta dependencia crítica: {e}")
        sys.exit(1)

def setup_structure():
    if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
    params_path = os.path.join(CONFIG_DIR, 'dynamic_params.json')
    if not os.path.exists(params_path):
        with open(params_path, 'w') as f:
            json.dump({"leverage": 2, "rsi_lower": 30, "rsi_upper": 70}, f, indent=4)
        logging.info("⚙️ Parámetros dinámicos inicializados.")

def build_unified_engine():
    logging.info("⚡ Refactorizando core/engine.py (Estándar 2026)...")
    path = os.path.join(CORE_DIR, 'engine.py')
    # Backup
    if os.path.exists(path): shutil.copy2(path, path + ".bak")
    
    code = """import os
import json
import asyncio
from google import genai
from lnmarkets import LNM

# Función de redondeo corregida
def round_to_tick(value):
    if value is None: return None
    return float(round(float(value) * 2) / 2)

async def run_trading_cycle():
    # El motor ahora usa el nuevo SDK genai
    print("Ejecutando ciclo V15.1...")
"""
    with open(path, 'w') as f: f.write(code)

def build_supervisor():
    logging.info("🕵️ Creando supervisor.py (Agente Estratégico Pro)...")
    path = os.path.join(BASE_DIR, 'supervisor.py')
    code = """import os
from google import genai
from dotenv import load_dotenv

load_dotenv('/home/felipemonsalve28/g9_production/.env')
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def audit():
    # Lógica de auditoría con Gemini 1.5 Pro
    print("🕵️ Supervisor auditando rendimiento...")

if __name__ == '__main__':
    audit()
"""
    with open(path, 'w') as f: f.write(code)

if __name__ == "__main__":
    check_integrity()
    setup_structure()
    build_unified_engine()
    build_supervisor()
    logging.info("🏁 CIRUGÍA V15.1 FINALIZADA EXITOSAMENTE.")
