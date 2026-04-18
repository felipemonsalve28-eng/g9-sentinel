import sys, os, json, subprocess
sys.path.append('/home/felipemonsalve28/g9_production')
from dotenv import load_dotenv
load_dotenv('/home/felipemonsalve28/g9_production/.env')
from core.notifier import G9Notifier

def enviar_reporte():
    notifier = G9Notifier()
    
    # 1. Extraer los Sats Acumulados de la Memoria
    try:
        with open('/home/felipemonsalve28/g9_production/data/session_memory.json', 'r') as f:
            mem = json.load(f)
        pnl = mem.get("total_pnl", 0)
    except:
        pnl = "N/A"

    # 2. Extraer el último razonamiento de los logs
    try:
        # Tomamos las últimas 25 líneas y filtramos la actividad del Cerebro
        comando = "tail -n 25 /home/felipemonsalve28/g9_production/bot_output.log | grep -iE 'audit|brain|decision|heartbeat|logic'"
        logs = subprocess.check_output(comando, shell=True).decode('utf-8').strip()
        if not logs:
            logs = "Modo acecho (Sin decisiones recientes)."
    except Exception as e:
        logs = f"Error leyendo logs: {e}"

    # 3. Ensamblar el Reporte
    msg = f"🧠 REPORTE TÁCTICO V18 (4H)\n\n"
    msg += f"💰 Sats Acumulados: {pnl}\n"
    msg += f"🎯 Meta: 35% Diario (Predator Mode)\n\n"
    msg += f"🔍 Último análisis de Gemini:\n"
    msg += f"{logs[-600:]}" # Limitamos a 600 caracteres para no saturar Telegram

    print("Enviando reporte...")
    notifier.send_alert(msg)

if __name__ == "__main__":
    enviar_reporte()
