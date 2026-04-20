import sqlite3
import json
import os
import time
import psutil
import shutil
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns

DB_PATH = '/home/felipemonsalve28/g9_production/data/g9_market.db'
PROJECT_PATH = '/home/felipemonsalve28/g9_production'
console = Console()

def get_system_metrics():
    # RAM
    ram = psutil.virtual_memory()
    # DISCO (Partición del proyecto)
    total, used, free = shutil.disk_usage(PROJECT_PATH)
    # Tamaño de la carpeta del proyecto (estimado rápido)
    folder_size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                      for dirpath, dirnames, filenames in os.walk(PROJECT_PATH) 
                      for filename in filenames) / (1024 * 1024) # MB
    
    return {
        "ram_p": ram.percent,
        "disk_free_gb": free / (1024**3),
        "folder_mb": folder_size,
        "cpu_p": psutil.cpu_percent()
    }

def get_db_analytics():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM ai_decisions", conn)
        conn.close()
        
        if df.empty:
            return None

        # Análisis con Pandas
        total_trades = len(df)
        wins = len(df[df['pnl_sats'] > 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        net_pnl = df['pnl_sats'].sum()
        avg_pnl = df['pnl_sats'].mean()
        max_drawdown = df['pnl_sats'].min()
        
        return {
            "df": df.tail(5), # Últimas 5 para la tabla
            "stats": {
                "total": total_trades,
                "win_rate": win_rate,
                "net_pnl": net_pnl,
                "avg_pnl": avg_pnl,
                "max_loss": max_drawdown
            },
            "last_row": df.iloc[-1]
        }
    except Exception as e:
        return None

def generate_enhanced_dashboard():
    sys = get_system_metrics()
    ana = get_db_analytics()
    
    if not ana:
        return Panel("Cargando datos...", title="G9-SENTINEL")

    last = ana['last_row']
    stats = ana['stats']

    # --- PANEL 1: HARDWARE & PROYECTO ---
    sys_text = Text()
    sys_text.append(f"💻 CPU: {sys['cpu_p']}% | RAM: {sys['ram_p']}%\n", style="bold magenta")
    sys_text.append(f"💽 DISCO LIBRE: {sys['disk_free_gb']:.2f} GB\n", style="bold blue")
    sys_text.append(f"📂 TAMAÑO PROYECTO: {sys['folder_mb']:.2f} MB", style="dim cyan")
    
    sys_panel = Panel(sys_text, title="[bold white]ESTADO DEL NODO")

    # --- PANEL 2: ANALÍTICA DE TRADING (PANDAS) ---
    trade_text = Text()
    trade_text.append(f"📈 TOTAL CICLOS: {stats['total']}\n", style="bold")
    trade_text.append(f"🎯 WIN RATE: {stats['win_rate']:.1f}%\n", style="bold green" if stats['win_rate'] > 50 else "bold red")
    trade_text.append(f"💰 PnL NETO: {stats['net_pnl']:,} SATS\n", style="bold yellow")
    trade_text.append(f"📊 AVG PnL: {stats['avg_pnl']:.2f}", style="dim")

    ana_panel = Panel(trade_text, title="[bold white]RESUMEN ESTRATÉGICO")

    # --- PANEL 3: LÓGICA GEMINI (SE MANTIENE) ---
    logic_panel = Panel(
        last['logic_applied'],
        title="[bold green]🧠 ÚLTIMO RAZONAMIENTO",
        border_style="green"
    )

    # --- TABLA DE HISTORIAL (SE MANTIENE) ---
    table = Table(expand=True, border_style="dim")
    table.add_column("Fecha", style="dim")
    table.add_column("Acción")
    table.add_column("Precio", justify="right")
    table.add_column("PnL", justify="right")
    table.add_column("Balance", justify="right", style="bold cyan")
    
    for _, row in ana['df'].iterrows():
        pnl_color = "green" if row['pnl_sats'] > 0 else "red" if row['pnl_sats'] < 0 else "white"
        table.add_row(
            str(row['timestamp']),
            str(row['action']),
            f"${row['market_price']:,.2f}",
            Text(str(row['pnl_sats']), style=pnl_color),
            f"{row['balance_sats']:,}"
        )

    # --- LAYOUT DE PANTALLA COMPLETA ---
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=6),
        Layout(name="middle", size=8),
        Layout(name="footer")
    )
    
    layout["header"].split_row(sys_panel, ana_panel)
    layout["middle"].update(logic_panel)
    layout["footer"].update(table)
    
    return layout

if __name__ == "__main__":
    os.system('clear')
    with Live(generate_enhanced_dashboard(), refresh_per_second=0.5, screen=True) as live:
        while True:
            time.sleep(2)
            live.update(generate_enhanced_dashboard())
