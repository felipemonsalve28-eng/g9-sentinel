import os
import sqlite3

BASE_DIR = '/home/felipemonsalve28/g9_production'
DB_PATH = os.path.join(BASE_DIR, 'data/g9_market.db')
NOTIFIER_PATH = os.path.join(BASE_DIR, 'core/notifier.py')
REPORT_ENGINE_PATH = os.path.join(BASE_DIR, 'report_engine.py')

def migrate_database():
    print("🗄️ 1. Migrando Base de Datos (performance_logs)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_pnl REAL,
            roi REAL,
            winrate REAL,
            delta_pnl REAL,
            drawdown INTEGER
        )
    """)
    # Insertar snapshot base (cero) si la tabla es nueva para que el Delta no falle
    cursor.execute("SELECT COUNT(*) FROM performance_logs")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO performance_logs (total_pnl, roi, winrate, delta_pnl, drawdown) VALUES (0,0,0,0,0)")
    conn.commit()
    conn.close()
    print("✅ DB: Migración completada.")

def create_report_engine():
    print("📊 2. Generando report_engine.py...")
    script = """import asyncio
import sqlite3
import os
import logging
from core.notifier import G9Notifier

DB_PATH = '/home/felipemonsalve28/g9_production/data/g9_market.db'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_metrics():
    # Modo Read-Only
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        conn = sqlite3.connect(DB_PATH) # Fallback si uri falla
    
    cursor = conn.cursor()
    
    # Ignorar OPEN trades. Asumimos que los cerrados tienen pnl_sats != 0 o action en ('BUY', 'SELL') sin open flag
    # Si su schema difiere, ajustamos la query. Asumiremos pnl_sats IS NOT NULL para este cálculo.
    cursor.execute("SELECT pnl_sats, margin FROM ai_decisions WHERE pnl_sats IS NOT NULL AND pnl_sats != 0")
    trades = cursor.fetchall()
    
    if not trades:
        return None
        
    total_pnl = sum(t[0] for t in trades)
    total_margin = sum(t[1] for t in trades if t[1] is not None)
    
    wins = len([t for t in trades if t[0] > 0])
    winrate = (wins / len(trades)) * 100 if trades else 0
    roi = (total_pnl / total_margin) * 100 if total_margin > 0 else 0
    
    # Calcular Drawdown (racha de pérdidas)
    max_dd = 0
    current_dd = 0
    for t in trades:
        if t[0] < 0:
            current_dd += 1
            max_dd = max(max_dd, current_dd)
        else:
            current_dd = 0

    # Obtener reporte anterior para Delta
    cursor.execute("SELECT total_pnl FROM performance_logs ORDER BY id DESC LIMIT 1")
    last_pnl_row = cursor.fetchone()
    last_pnl = last_pnl_row[0] if last_pnl_row else 0
    
    delta_pnl = total_pnl - last_pnl
    conn.close()
    
    return {
        "total_pnl": round(total_pnl, 2),
        "roi": round(roi, 2),
        "winrate": round(winrate, 2),
        "delta_pnl": round(delta_pnl, 2),
        "drawdown": max_dd
    }

async def run_report():
    print("Iniciando Reporte Financiero G9-Sentinel...")
    metrics = calculate_metrics()
    if not metrics:
        print("Sin datos suficientes para reporte.")
        return

    # Escribir nuevo Snapshot
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO performance_logs (total_pnl, roi, winrate, delta_pnl, drawdown) 
                      VALUES (?, ?, ?, ?, ?)''', 
                   (metrics['total_pnl'], metrics['roi'], metrics['winrate'], metrics['delta_pnl'], metrics['drawdown']))
    conn.commit()
    conn.close()

    notifier = G9Notifier()
    await notifier.send_financial_report(metrics)
    print("✅ Reporte generado y enviado exitosamente.")

if __name__ == "__main__":
    asyncio.run(run_report())
"""
    with open(REPORT_ENGINE_PATH, 'w', encoding='utf-8') as f:
        f.write(script)
    print("✅ Motor de reportes creado.")

def patch_notifier():
    print("📡 3. Inyectando UI de Reportes en Notifier...")
    with open(NOTIFIER_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "def send_financial_report" not in content:
        new_method = """
    async def send_financial_report(self, stats):
        try:
            trend_emoji = "📈" if stats['delta_pnl'] >= 0 else "📉"
            status = "🟢 AGRESIVO" if stats['winrate'] >= 45 and stats['delta_pnl'] >= 0 else "🛡️ CONSERVADOR"
            
            msg = f"🏦 <b>REPORTE FINANCIERO V16</b>\\n"
            msg += f"Estado IA: {status}\\n\\n"
            msg += f"<pre>"
            msg += f"Total PnL : {stats['total_pnl']} SATS\\n"
            msg += f"Delta 4H  : {stats['delta_pnl']} SATS {trend_emoji}\\n"
            msg += f"Winrate   : {stats['winrate']}%\\n"
            msg += f"ROI Global: {stats['roi']}%\\n"
            msg += f"Drawdown  : {stats['drawdown']} rachas"
            msg += f"</pre>"
            await self.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='HTML')
        except Exception as e:
            print(f"Error enviando reporte TG: {e}")
"""
        with open(NOTIFIER_PATH, 'a', encoding='utf-8') as f:
            f.write(new_method)
        print("✅ UI de Telegram actualizada (Dashboard Mode).")
    else:
        print("✅ Notifier ya contiene el método de reporte.")

if __name__ == "__main__":
    migrate_database()
    create_report_engine()
    patch_notifier()
    print("🚀 FASE 1 COMPLETADA.")
