import time, os, requests, json, subprocess
from dotenv import load_dotenv

load_dotenv('/home/felipemonsalve28/g9_production/.env')
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = f"https://api.telegram.org/bot{TOKEN}/"

def get_updates(offset=None):
    try:
        r = requests.get(URL + "getUpdates", params={"offset": offset, "timeout": 30})
        return r.json()
    except:
        return None

def handle_status():
    print("Comando /status detectado. Generando reporte...")
    # Llamamos al script que ya creamos antes
    subprocess.run(["/home/felipemonsalve28/g9_production/venv/bin/python3", "/home/felipemonsalve28/g9_production/tools/telegram_4h_report.py"])

def start_listening():
    print("📡 Listener de comandos activado. Esperando /status...")
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if updates and "result" in updates:
            for update in updates["result"]:
                last_update_id = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                from_id = str(msg.get("chat", {}).get("id", ""))

                if text == "/status" and from_id == CHAT_ID:
                    handle_status()
        time.sleep(2)

if __name__ == "__main__":
    start_listening()
