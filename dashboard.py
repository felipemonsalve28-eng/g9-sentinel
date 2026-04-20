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

console = Console()
DB_PATH = '/home/felipemonsalve28/g9_production/data/g9_market.db'

class G9Dashboard:
    def __init__(self, path):
        self.db_path = path

    def get_telemetry(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Apuntamos directamente a la tabla reina
            table = "ai_decisions"
            
            # Obtenemos los nombres de las columnas para no fallar en el mapeo
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [c[1] for c in cursor.fetchall()]
            
            # Traemos la última fila
            cursor.execute(f"SELECT * FROM {table} ORDER BY ROWID DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()

            if not row:
                return "⚠️ Tabla 'ai_decisions' encontrada pero está vacía."

            # Creamos un diccionario con los datos reales
            data = dict(zip(cols, row))
            
            # Procesar el JSON de indicadores (que suele venir en la columna 'indicators')
            indicators = {}
            raw_inds = data.get('indicators')
            if raw_inds:
                try:
                    indicators = json.loads(raw_inds)
                except:
                    pass

            return {
                "ts": data.get('timestamp') or data.get('created_at', 'N/A'),
                "action": data.get('action', 'HOLD'),
                "balance": data.get('balance', 0),
                "price": data.get('market_price', 0),
                "logic": data.get('logic_applied', 'N/A'),
                "conf": data.get('confidence', 0),
                "inds": indicators
            }
        except Exception as e:
            return f"🚨 Error de conexión: {str(e)}"

    def update(self):
        res = self.get_telemetry()
        if isinstance(res, str):
            return Panel(Text(res, style="bold red"), title="Status", border_style="red")

        # --- HEADER ---
        header = Panel(
            Text(f"🛡️ G9-SENTINEL V25.6 | 🧠 TABLA: ai_decisions | 🕒 {datetime.now().strftime('%H:%M:%S')}", 
                 justify="center", style="bold white on blue"), 
            style="blue"
        )
        
        # --- STATS PANEL ---
        stats = Table(show_header=False, box=box.SIMPLE, expand=True)
        # Limpiar timestamp para que no sea tan largo
        clean_ts = str(res['ts']).split('.')[0].replace('T', ' ')
        stats.add_row("📅 Registro", clean_ts)
        stats.add_row("🎯 Acción", f"[bold yellow]{res['action']}[/]")
        stats.add_row("🧠 Confianza", f"{res['conf']}%")
        stats.add_row("💰 Balance", f"{res['balance']:,} Sats")
        stats.add_row("📊 Precio BTC", f"${res['price']:,}")
        stats_p = Panel(stats, title="[cyan]Estado General[/]", border_style="cyan")

        # --- MARKET PANEL (RSI & TREND) ---
        m_table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True)
        m_table.add_column("TF", justify="center")
        m_table.add_column("RSI", justify="center")
        m_table.add_column("Tendencia", justify="center")
        m_table.add_column("Bandas BB", justify="center")
        
        for tf in ['m1', 'm5', 'h1', 'h4']:
            tf_d = res['inds'].get(tf, {})
            rsi = tf_d.get('rsi', 0)
            # Color dinámico para RSI
            rsi_s = "bold red" if rsi > 70 else ("bold green" if rsi < 30 else "white")
            
            # Formatear BB
            bb_info = "N/A"
            if 'bb_l' in tf_d and 'bb_u' in tf_d:
                bb_info = f"{int(tf_d['bb_l'])} | {int(tf_d['bb_u'])}"

            m_table.add_row(
                tf.upper(), 
                Text(str(rsi), style=rsi_s), 
                Text(str(tf_d.get('trend', 'N/A')), style="green" if tf_d.get('trend') == "UP" else "red"),
                bb_info
            )
        
        market_p = Panel(m_table, title="[magenta]Telemetría Multi-Temporal[/]", border_style="magenta")

        # --- LAYOUT FINAL ---
        layout = Layout()
        layout.split_column(
            Layout(name="h", size=3), 
            Layout(name="m", ratio=1), 
            Layout(name="f", size=6)
        )
        layout["m"].split_row(Layout(stats_p), Layout(market_p))
        
        # Footer con la lógica de Gemini
        footer_text = Text(res['logic'], style="italic dim", justify="left")
        layout["f"].update(Panel(footer_text, title="🧠 Razonamiento de la IA", border_style="green"))
        layout["h"].update(header)
        
        return layout

# Ejecución
dash = G9Dashboard(DB_PATH)
with Live(dash.update(), refresh_per_second=1, screen=True) as live:
    while True:
        live.update(dash.update())
        time.sleep(1)
