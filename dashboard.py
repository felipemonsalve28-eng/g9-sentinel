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
        Layout(name="account", size=8),
        Layout(name="market", size=10),
        Layout(name="footer", size=10)
    )
    return layout

def generate_ui():
    data = get_latest_data()
    layout = make_layout()
    
    # 1. HEADER
    layout["header"].update(Panel(
        Text(f"🛰️ G9-SENTINEL V25.5 | {datetime.now().strftime('%H:%M:%S')}", justify="center", style="bold white on blue")
    ))

    if data:
        # 🛠️ CORRECCIÓN: Convertimos el objeto sqlite3.Row a un diccionario de Python
        data = dict(data)

        # --- 2. PANEL DE CUENTA Y ACCIÓN ---
        action = data.get('action', 'WAIT')
        action_style = "bold green" if action == "BUY" else "bold red" if action == "SELL" else "bold yellow"
        
        acc_table = Table.grid(expand=True)
        acc_table.add_column(style="bold cyan", width=20)
        acc_table.add_column()
        
        try:
            bal = data.get('balance_sats', 0)
        except:
            bal = 0
            
        acc_table.add_row("BÓVEDA ACTUAL:", f"[bold white]{bal:,} Sats[/bold white]")
        acc_table.add_row("ÚLTIMA ACCIÓN:", Text(action, style=action_style))
        acc_table.add_row("PRECIO BTC:", f"[bold yellow]${data.get('market_price', 'N/A')}[/bold yellow]")
        acc_table.add_row("CONFIANZA IA:", f"[bold magenta]{data.get('confidence', '0')}%[/bold magenta]")
        
        layout["account"].update(Panel(acc_table, title="[bold]Estado de Bóveda y Mando[/bold]", border_style="bright_blue"))

        # --- 3. PANEL DE TELEMETRÍA MULTI-TEMPORALIDAD ---
        tf_table = Table(expand=True)
        tf_table.add_column("Timeframe", justify="center", style="bold white")
        tf_table.add_column("Tendencia", justify="center")
        tf_table.add_column("RSI (14)", justify="center")
        tf_table.add_column("BB Alta", justify="center", style="cyan")
        tf_table.add_column("BB Baja", justify="center", style="cyan")

        if data.get('indicators_snapshot'):
            try:
                market_data = json.loads(data['indicators_snapshot'])
                
                # Iteramos sobre los timeframes configurados en el engine
                for tf in ['m1', 'm5', 'h1', 'h4']:
                    if tf in market_data:
                        info = market_data[tf]
                        
                        # Estilos para tendencia
                        trend = info.get('trend', 'N/A')
                        if trend == "UP":
                            trend_styled = "[bold green]▲ UP[/bold green]"
                        elif trend == "DOWN":
                            trend_styled = "[bold red]▼ DOWN[/bold red]"
                        else:
                            trend_styled = trend
                            
                        # Estilos para RSI
                        rsi = info.get('rsi', 'N/A')
                        if isinstance(rsi, (int, float)):
                            if rsi < 30:
                                rsi_styled = f"[bold green]{rsi}[/bold green]" # Sobrevendido (Oportunidad)
                            elif rsi > 70:
                                rsi_styled = f"[bold red]{rsi}[/bold red]"   # Sobrecomprado (Peligro)
                            else:
                                rsi_styled = str(rsi)
                        else:
                            rsi_styled = str(rsi)

                        tf_table.add_row(
                            tf.upper(),
                            trend_styled,
                            rsi_styled,
                            str(info.get('bb_u', 'N/A')),
                            str(info.get('bb_l', 'N/A'))
                        )
            except Exception as e:
                tf_table.add_row("ERROR", f"Fallo al parsear datos: {e}", "", "", "")
        else:
             tf_table.add_row("N/A", "Sin datos de mercado", "N/A", "N/A", "N/A")

        layout["market"].update(Panel(tf_table, title="[bold]Radar de Mercado (Multi-Timeframe)[/bold]", border_style="green"))

        # --- 4. PANEL DE LÓGICA / PENSAMIENTO ---
        layout["footer"].update(Panel(Text(data.get('logic_applied', 'Sin registro de pensamiento.'), style="italic white"), title="[bold]Neural Feed (Pensamiento Crítico de Gemini)[/bold]", border_style="magenta"))
    
    else:
        layout["account"].update(Panel("Sincronizando...", title="Estado de Bóveda"))
        layout["market"].update(Panel("Esperando datos de temporalidad...", title="Radar de Mercado"))
        layout["footer"].update(Panel("Esperando primera decisión de Gemini...", title="Neural Feed"))

    return layout

if __name__ == "__main__":
    # Limpiamos la consola antes de iniciar para evitar parpadeos sucios
    os.system('cls' if os.name == 'nt' else 'clear')
    with Live(generate_ui(), refresh_per_second=1, screen=True) as live:
        while True:
            time.sleep(1)
            live.update(generate_ui())
