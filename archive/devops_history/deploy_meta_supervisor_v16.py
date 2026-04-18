import os
import json
import shutil
import re
from pathlib import Path

# --- CONFIGURACIÓN DE RUTAS ABSOLUTAS ---
BASE_DIR = Path("/home/felipemonsalve28/g9_production")
CORE_DIR = BASE_DIR / "core"
CONFIG_DIR = BASE_DIR / "config"
ARCHIVE_DIR = BASE_DIR / "archive" / "devops_history"
TOOLS_DIR = BASE_DIR / "tools"
ENGINE_PATH = CORE_DIR / "engine.py"
SUPERVISOR_PATH = BASE_DIR / "supervisor.py"
PARAMS_PATH = CONFIG_DIR / "dynamic_params.json"

def master_deploy():
    print("🚀 Iniciando Despliegue de Arquitectura G9-Meta-Supervisor...")

    # 1. LIMPIEZA Y ORDEN (Mover parches y herramientas)
    for folder in [ARCHIVE_DIR, TOOLS_DIR, CONFIG_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    files_to_archive = [f for f in os.listdir(BASE_DIR) if f.startswith(("patch_", "fix_", "build_", "deploy_")) and f.endswith(".py")]
    for f in files_to_archive:
        shutil.move(str(BASE_DIR / f), str(ARCHIVE_DIR / f))
        print(f"📦 Archivado: {f}")

    # 2. INICIALIZACIÓN DE PARÁMETROS (Contrato inicial)
    if not PARAMS_PATH.exists():
        initial_params = {
            "ADX_REGIME": "RANGING",
            "MAX_LEVERAGE": 10,
            "RSI_THRESHOLD_LOW": 30,
            "RSI_THRESHOLD_HIGH": 70,
            "FEE_COVERAGE_RATIO": 3.0,
            "RISK_PER_TRADE": 0.15,
            "LAST_STRATEGIC_UPDATE": "INITIAL_DEPLOY",
            "STRATEGIC_NOTE": "Despliegue inicial. Operando en modo conservador."
        }
        with open(PARAMS_PATH, "w") as f:
            json.dump(initial_params, f, indent=4)
        print("⚙️  dynamic_params.json inicializado.")

    # 3. CREACIÓN DEL SUPERVISOR (Gemini 1.5 Pro)
    supervisor_code = """import os
import json
import sqlite3
import pandas as pd
from google import genai
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = '/home/felipemonsalve28/g9_production'
load_dotenv(os.path.join(BASE_DIR, '.env'))

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
DB_PATH = os.path.join(BASE_DIR, 'data/g9_market.db')
CONFIG_PATH = os.path.join(BASE_DIR, 'config/dynamic_params.json')

def get_performance_report():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(\"\"\"
            SELECT action, pnl_sats, logic_applied 
            FROM ai_decisions 
            WHERE pnl_sats IS NOT NULL AND pnl_sats != 0
            ORDER BY timestamp DESC LIMIT 20
        \"\"\", conn)
        conn.close()
        winrate = (len(df[df['pnl_sats'] > 0]) / len(df)) * 100 if not df.empty else 0
        return df.to_json(orient='records'), winrate
    except Exception as e:
        print(f"❌ Error DB: {e}")
        return None, 0

async def run_audit():
    print(f"🕵️ Auditoría Pro en curso...")
    history, wr = get_performance_report()
    if history is None: return

    prompt = f\"\"\"
    Eres el QUANT STRATEGIST SENIOR de G9-Sentinel. 
    Analiza el desempeño reciente y ajusta los límites del bot Junior.
    
    DESEMPEÑO (Últimos 20 trades): {history}
    Winrate actual: {wr:.2f}%

    Responde SOLO JSON puro:
    {{
        "ADX_REGIME": "TRENDING/RANGING",
        "MAX_LEVERAGE": int,
        "RSI_THRESHOLD_LOW": int,
        "RSI_THRESHOLD_HIGH": int,
        "FEE_COVERAGE_RATIO": float,
        "RISK_PER_TRADE": float,
        "STRATEGIC_NOTE": "Explicación breve"
    }}
    \"\"\"
    try:
        resp = client.models.generate_content(model="gemini-1.5-pro", contents=prompt)
        clean_json = resp.text.strip().replace('```json', '').replace('```', '')
        new_config = json.loads(clean_json)
        new_config["LAST_STRATEGIC_UPDATE"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(CONFIG_PATH, 'w') as f:
            json.dump(new_config, f, indent=4)
        print(f"✅ Estrategia Pro actualizada.")
    except Exception as e:
        print(f"❌ Error Pro: {e}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(run_audit())
"""
    with open(SUPERVISOR_PATH, "w") as f:
        f.write(supervisor_code)
    print("🧠 supervisor.py creado exitosamente.")

    # 4. PARCHE DINÁMICO DE ENGINE.PY (Inyección de lógica de Supervisor)
    with open(ENGINE_PATH, "r") as f:
        engine_content = f.read()

    # Inyectar lectura de parámetros antes del prompt
    if "dynamic_params.json" not in engine_content:
        strat_loading_code = """
                # --- CAPA ESTRATÉGICA (SUPERVISOR PRO) ---
                try:
                    with open('/home/felipemonsalve28/g9_production/config/dynamic_params.json', 'r') as f:
                        strat = json.load(f)
                except:
                    strat = {"ADX_REGIME": "NORMAL", "MAX_LEVERAGE": 5, "RSI_THRESHOLD_LOW": 30, "RSI_THRESHOLD_HIGH": 70, "STRATEGIC_NOTE": "Modo Seguro"}
        """
        # Insertar justo antes de la definición de prompt_entry o prompt
        engine_content = re.sub(r'(prompt_entry|prompt)\s*=\s*f"""', strat_loading_code + r'\n                \1 = f"""', engine_content)

        # Inyectar las restricciones en el texto del prompt
        supervisor_rules = """
                [ORDENES ESTRATÉGICAS DEL SUPERVISOR]:
                - Régimen: {strat['ADX_REGIME']} | Max Leverage: {strat['MAX_LEVERAGE']}x
                - Umbrales RSI: {strat['RSI_THRESHOLD_LOW']} (Bajo) / {strat['RSI_THRESHOLD_HIGH']} (Alto)
                - Nota: {strat['STRATEGIC_NOTE']}
                - Regla Oro: Si no se cumplen estos umbrales, responde HOLD.
        """
        engine_content = engine_content.replace('SISTEMA DE TRADING G9-SENTINEL', 'SISTEMA DE TRADING G9-SENTINEL\n' + supervisor_rules)

    with open(ENGINE_PATH, "w") as f:
        f.write(engine_content)
    print("⚡ engine.py parcheado con el contrato de supervisión.")

    print("\n🏁 DESPLIEGUE FINALIZADO. Sistema operando en modo Meta-Supervisor.")

if __name__ == "__main__":
    master_deploy()
