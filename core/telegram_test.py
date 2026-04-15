import os
import requests
from dotenv import load_dotenv

# Cargamos el archivo unificado que acabas de preparar
load_dotenv('/home/felipemonsalve28/g9_production/.env')

token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

def send_test():
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": "🚀 G9-Sentinel: Sistema de notificaciones vinculado correctamente."
    }
    try:
        r = requests.post(url, json=payload)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    print("📡 Enviando señal a Telegram...")
    resultado = send_test()
    if resultado.get("ok"):
        print("✅ ¡Éxito! Revisa tu celular.")
    else:
        print(f"❌ Falló el envío: {resultado}")
