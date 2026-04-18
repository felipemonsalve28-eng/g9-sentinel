import sqlite3
import time
import os
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from datetime import datetime

console = Console()
DB_PATH = '/home/felipemonsalve28/g9_production/data/g9_market.db'

def get_latest_data():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_decisions ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row
    except:
        return None

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", size=10),
        Layout(name="footer", size=10)
    )
    return layout

def generate_ui():
    data = get_latest_data()
    layout = make_layout()
    
    layout["header"].update(Panel(
        Text(f"🛰️ G9-SENTINEL V25.3 | {datetime.now().strftime('%H:%M:%S')}", justify="center", style="bold white on blue")
    ))

    if data:
        action = data['action']
        action_style = "bold green" if action == "BUY" else "bold red" if action == "SELL" else "bold yellow"
        
        info_table = Table.grid(expand=True)
        info_table.add_column(style="bold cyan", width=20)
        info_table.add_column()
        
        # Corrección de acceso a Row de SQLite
        try:
            bal = data['balance_sats']
        except:
            bal = 0
            
        info_table.add_row("BÓVEDA ACTUAL:", f"[bold white]{bal:,} Sats[/bold white]")
        info_table.add_row("ÚLTIMA ACCIÓN:", Text(action, style=action_style))
        info_table.add_row("PRECIO BTC:", f"${data['market_price']}")
        
        # RSI con extracción segura
        rsi_val = "N/A"
        if data['indicators_snapshot']:
            try:
                indicators = json.loads(data['indicators_snapshot'])
                rsi_val = indicators.get('rsi', 'N/A')
            except:
                pass
        
        info_table.add_row("RSI ACTUAL:", f"{rsi_val}")
        info_table.add_row("CONFIANZA IA:", f"{data['confidence']}%")
        
        layout["main"].update(Panel(info_table, title="[bold]Telemetría Táctica[/bold]", border_style="bright_blue"))
        layout["footer"].update(Panel(Text(data['logic_applied'], style="italic white"), title="[bold]Neural Feed (Pensamiento Crítico)[/bold]", border_style="magenta"))
    else:
        layout["main"].update(Panel("Sincronizando con el Motor...", title="Status"))
        layout["footer"].update(Panel("Esperando primera decisión de Gemini...", title="Neural Feed"))

    return layout

if __name__ == "__main__":
    with Live(generate_ui(), refresh_per_second=1, screen=True) as live:
        while True:
            time.sleep(1)
            live.update(generate_ui())
