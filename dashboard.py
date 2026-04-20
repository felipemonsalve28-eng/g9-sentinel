import sqlite3
import json
import time
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich import box

# --- CONFIGURACIÓN BASADA EN TU BRAIN.PY ---
DB_PATH = '/home/felipemonsalve28/g9_production/data/g9_market.db'
console = Console()

class G9Dashboard:
    def __init__(self, path):
        self.db_path = path

    def get_telemetry(self):
        """Obtiene datos de la DB respetando el esquema de G9Brain."""
        if not os.path.exists(self.db_path):
            return f"❌ No se encuentra la DB en: {self.db_path}"

        conn = None
        try:
            # Abrimos en modo lectura (mode=ro) para no bloquear al motor
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Consultamos las columnas exactas de tu brain.py
            cursor.execute("""
                SELECT timestamp, market_price, action, confidence, 
                       logic_applied, balance_sats, indicators_snapshot 
                FROM ai_decisions 
                ORDER BY id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return "⏳ La tabla está lista, esperando primera decisión..."

            data = dict(row)
            
            # Parseo de indicadores (columna indicators_snapshot)
            inds = {}
            if data.get('indicators_snapshot'):
                try:
                    inds = json.loads(data['indicators_snapshot'])
                except:
                    inds = {}

            return {
                "ts": data['timestamp'],
                "action": str(data['action']).upper(),
                "price": data['market_price'],
                "conf": data['confidence'],
                "logic": data['logic_applied'],
                "balance": data['balance_sats'],
                "inds": inds
            }
        except Exception as e:
            return f"🚨 Error de lectura: {str(e)}"
        finally:
            if conn:
                conn.close()

    def generate_layout(self) -> Layout:
        res = self.get_telemetry()
        
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=10)
        )

        if isinstance(res, str):
            layout["main"].update(Panel(Text(res, justify="center", style="bold yellow"), title="G9-SENTINEL"))
            return layout

        # --- HEADER ---
        header_text = Text.assemble(
            ("🛡️ G9-SENTINEL ", "bold white"),
            ("V25.6 ", "cyan"),
            ("| ", "white"),
            (f"BTC: ${res['price']:,} ", "bold yellow"),
            ("| ", "white"),
            (f"ACTUALIZADO: {datetime.now().strftime('%H:%M:%S')}", "dim white")
        )
        layout["header"].update(Panel(header_text, style="blue", box=box.ROUNDED))

        # --- PANEL IZQUIERDO ---
        act_color = {"BUY": "bold green", "SELL": "bold red", "UPDATE_SL": "bold cyan", "CLOSE_POSITION": "bold orange3"}
        stats = Table(show_header=False, expand=True, box=box.SIMPLE)
        stats.add_row("🎯 ACCIÓN", Text(res['action'], style=act_color.get(res['action'], "white")))
        stats.add_row("🧠 CONF", f"{res['conf']}%")
        stats.add_row("💰 BALANCE", f"[green]{res['balance']:,} sats[/]")
        stats.add_row("🕒 REGISTRO", res['ts'].split('.')[0])
        
        # --- PANEL DERECHO ---
        m_table = Table(box=box.MINIMAL, expand=True)
        m_table.add_column("TF", justify="center", style="bold magenta")
        m_table.add_column("RSI", justify="center")
        m_table.add_column("TREND", justify="center")
        m_table.add_column("BOLLINGER", justify="center")

        for tf in ['m1', 'm5', 'h1', 'h4']:
            tf_d = res['inds'].get(tf, {})
            rsi = tf_d.get('rsi', 0)
            rsi_style = "bold red" if rsi > 70 else ("bold green" if rsi < 30 else "white")
            trend = str(tf_d.get('trend', 'N/A'))
            bb = f"{int(tf_d.get('bb_l',0))} | {int(tf_d.get('bb_u',0))}"
            m_table.add_row(tf.upper(), Text(str(rsi), style=rsi_style), Text(trend, style="green" if trend == "UP" else "red"), bb)

        layout["main"].split_row(
            Layout(Panel(stats, title="[cyan]Telemetría[/]", border_style="cyan"), ratio=1),
            Layout(Panel(m_table, title="[magenta]Matriz Fractal[/]", border_style="magenta"), ratio=2)
        )

        # --- FOOTER ---
        layout["footer"].update(Panel(Text(res['logic'], style="italic gray70"), title="🧠 Razonamiento Gemini", border_style="green"))

        return layout

if __name__ == "__main__":
    dash = G9Dashboard(DB_PATH)
    with Live(dash.generate_layout(), refresh_per_second=2, screen=True) as live:
        while True:
            live.update(dash.generate_layout())
            time.sleep(0.5)
