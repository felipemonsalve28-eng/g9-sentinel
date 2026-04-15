import os
import requests
from dotenv import load_dotenv
from pathlib import Path

env_path = '/home/felipemonsalve28/g9_production/.env'
load_dotenv(dotenv_path=env_path, override=True)

class G9Notifier:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
    def send_alert(self, message):
        # Diagnóstico impreso en consola
        print(f" debug -> Token detectado: {self.token[:10]}...")
        print(f" debug -> ID detectado: {self.chat_id}")
        
        if not self.token or not self.chat_id:
            print("⚠️ ERROR: No se leyeron las variables del .env")
            return False
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}
        
        try:
            r = requests.post(url, json=payload, timeout=10)
            print(f" debug -> Status: {r.status_code}")
            print(f" debug -> Respuesta API: {r.text}")
            return r.status_code == 200
        except Exception as e:
            print(f"❌ Error de red: {e}")
            return False
