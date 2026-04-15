import sqlite3
import os
import json
from datetime import datetime

class G9Brain:
    def __init__(self, db_path='/home/felipemonsalve28/g9_production/data/g9_market.db'):
        self.db_path = db_path
        self._initialize_neural_pathways()

    def _initialize_neural_pathways(self):
        """Asegura que la estructura de la base de datos exista y sea correcta."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla optimizada para el análisis de la IA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                market_price REAL,
                action TEXT, -- BUY, SELL, HOLD
                confidence INTEGER, -- 0 a 100
                logic_applied TEXT, -- El razonamiento de Gemini
                pnl_sats INTEGER DEFAULT 0,
                indicators_snapshot TEXT  -- Resultado de la operación (clave para aprender)
            )
        ''')
        conn.commit()
        conn.close()

    def get_context_for_gemini(self, limit=10):
        """Extrae la memoria y la formatea como un bloque de contexto para el prompt."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Usamos Row para poder acceder a las columnas por nombre
            conn.row_factory = sqlite3.Row 
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, market_price, action, confidence, logic_applied, pnl_sats 
                FROM ai_decisions 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return "[SISTEMA: No hay historial de trading previo. Esta es tu primera operación. Actúa con cautela y cíñete a tu estrategia base.]"

            # Construimos el bloque de memoria para inyectar en el prompt
            memory_block = "=== CONTEXTO HISTÓRICO: TUS ÚLTIMAS 10 DECISIONES ===\n"
            memory_block += "Analiza estos resultados antes de tomar tu nueva decisión. Evita repetir lógicas que resultaron en PnL negativo.\n\n"
            
            for i, row in enumerate(rows, 1):
                pnl_status = "GANANCIA" if row['pnl_sats'] > 0 else ("PÉRDIDA" if row['pnl_sats'] < 0 else "NEUTRAL")
                memory_block += f"Operación -{i}:\n"
                memory_block += f"  - Fecha/Hora: {row['timestamp']}\n"
                memory_block += f"  - Precio BTC: ${row['market_price']}\n"
                memory_block += f"  - Acción Tomada: {row['action']} (Confianza: {row['confidence']}%)\n"
                memory_block += f"  - Tu Razonamiento: {row['logic_applied']}\n"
                memory_block += f"  - Resultado: {row['pnl_sats']} SATS ({pnl_status})\n"
                memory_block += "-" * 40 + "\n"

            return memory_block

        except Exception as e:
            return f"[SISTEMA: Error crítico al recuperar memoria: {e}. Opera basándote únicamente en los datos técnicos actuales.]"

    def save_decision(self, market_price, action, confidence, logic_applied, indicators=None):
        """Guarda la decisión actual para que sirva de memoria en el futuro."""
        try:
            import json
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Inserción limpia y explícita
            cursor.execute('''
                INSERT INTO ai_decisions (market_price, action, confidence, logic_applied, indicators_snapshot)
                VALUES (?, ?, ?, ?, ?)
            ''', (market_price, action, confidence, logic_applied, json.dumps(indicators) if indicators else None))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error guardando memoria: {e}")
            return False


# --- Bloque de prueba ---
if __name__ == "__main__":
    brain = G9Brain()
    print("🧠 Memoria inicializada correctamente.")
    print("\nSimulando extracción de contexto para Gemini:")
    print(brain.get_context_for_gemini(limit=3))
