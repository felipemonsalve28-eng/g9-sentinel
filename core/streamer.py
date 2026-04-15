import websocket, json, sqlite3, threading, time, os
from datetime import datetime

class G9Streamer:
    def __init__(self):
        # Detecta la raíz del proyecto (un nivel arriba de /core)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(self.base_dir, 'config', 'settings.json')
        self.db_path = os.path.join(self.base_dir, 'data', 'g9_market.db')
        
        if not os.path.exists(config_path):
            print(f"❌ ERROR: No se encuentra el config en {config_path}")
            return

        with open(config_path) as f: self.config = json.load(f)
        self._setup_db()

    def _setup_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS market_flow (ts TIMESTAMP PRIMARY KEY, cvd REAL, msg_count INTEGER)")
        conn.commit()
        conn.close()

    def _update_db(self, value):
        try:
            conn = sqlite3.connect(self.db_path)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:00')
            conn.execute("INSERT INTO market_flow(ts, cvd, msg_count) VALUES(?, ?, 1) "
                         "ON CONFLICT(ts) DO UPDATE SET cvd=cvd+?, msg_count=msg_count+1", (now, value, value))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")

    def on_message(self, ws, msg):
        data = json.loads(msg)
        if data.get('type') == 'match':
            sz = float(data['size'])
            side = 1 if data['side'] == 'buy' else -1
            self._update_db(sz * side)

    def run(self):
        print(f"🔌 Conectando a Coinbase... (DB: {self.db_path})")
        ws = websocket.WebSocketApp("wss://ws-feed.exchange.coinbase.com",
            on_open=lambda ws: ws.send(json.dumps({"type": "subscribe", "channels": [{"name": "matches", "product_ids": ["BTC-USD"]}]})),
            on_message=self.on_message)
        ws.run_forever()

if __name__ == "__main__":
    G9Streamer().run()
