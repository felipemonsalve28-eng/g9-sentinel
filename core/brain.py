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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                market_price REAL,
                action TEXT,
                confidence INTEGER,
                logic_applied TEXT,
                pnl_sats INTEGER DEFAULT 0,
                indicators_snapshot TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def get_context_for_gemini(self, limit=10):
        """Extrae la memoria para que Gemini no cometa los mismos errores."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, market_price, action, confidence, logic_applied, pnl_sats 
                FROM ai_decisions 
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return "[SISTEMA: Primera operación. Sin historial previo.]"

            memory_block = "=== MEMORIA DE OPERACIONES RECIENTES ===\n"
            for row in rows:
                status = "GANANCIA" if row['pnl_sats'] > 0 else "PÉRDIDA"
                memory_block += f"- {row['timestamp']} | {row['action']} | {status} ({row['pnl_sats']} sats) | Logic: {row['logic_applied'][:50]}...\n"
            return memory_block
        except Exception as e:
            return f"Error de memoria: {e}"

    def save_decision(self, market_price, action, confidence, logic_applied, indicators=None):
        """Guarda la decisión actual."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_decisions (market_price, action, confidence, logic_applied, indicators_snapshot)
                VALUES (?, ?, ?, ?, ?)
            ''', (market_price, action, confidence, logic_applied, json.dumps(indicators) if indicators else None))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error guardando memoria: {e}")
            return False
