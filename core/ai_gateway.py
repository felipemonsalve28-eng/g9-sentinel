import os
import sqlite3
import pandas as pd
from google import genai
from dotenv import load_dotenv

# Aseguramos que cargue las variables de entorno si se ejecuta de forma independiente
load_dotenv('/home/felipemonsalve28/g9_production/.env')

class G9Brain:
    def __init__(self):
        # ✅ Corrección: Leemos la llave de forma segura desde el entorno
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ ERROR: GEMINI_API_KEY no encontrada en el entorno.")
            
        # Cliente 2026: Directo y sin burocracia
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.5-flash"
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, 'data', 'g9_market.db')

    def get_market_context(self):
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT sum(cvd) as cvd, sum(msg_count) as trades FROM market_flow WHERE ts >= datetime('now', '-5 minutes')"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return {"cvd": df['cvd'].iloc[0] or 0, "trades": df['trades'].iloc[0] or 0}
        except Exception as e:
            print(f"Error de BD en market context: {e}")
            return {"cvd": 0, "trades": 0}

    def ask_recommendation(self):
        ctx = self.get_market_context()
        
        prompt = f"""
        Act as a BTC Whale Trader. Context (5m): CVD {ctx['cvd']:.2f}, Trades {ctx['trades']}.
        Goal: Maximize SAT profits.
        Respond ONLY with a JSON object:
        {{"decision": "BUY/SELL/WAIT", "confidence": 0-100, "reason": "10 word explanation"}}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text.strip().replace('```json', '').replace('```', '')
        except Exception as e:
            return f"❌ Error de IA: {e}"

if __name__ == "__main__":
    brain = G9Brain()
    print(f"🧠 Consultando al cerebro {brain.model_id}...")
    print(brain.ask_recommendation())
