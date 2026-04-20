import pandas as pd
import sqlite3
from datetime import datetime

# Configuración
DB_PATH = '/home/felipemonsalve28/g9_production/data/g9_market.db'

def generate_and_inject_report():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Cargar toda la data
    df = pd.read_sql_query("SELECT * FROM ai_decisions", conn)
    
    if df.empty:
        print("Base de datos vacía.")
        return

    # 2. Análisis con Pandas
    total_trades = len(df)
    # Filtramos solo donde hubo cierre o cambio de PnL real
    df_pnl = df[df['pnl_sats'] != 0]
    
    win_rate = (len(df_pnl[df_pnl['pnl_sats'] > 0]) / len(df_pnl) * 100) if not df_pnl.empty else 0
    total_pnl = df['pnl_sats'].sum()
    max_drawdown = df['pnl_sats'].min()
    profit_factor = abs(df_pnl[df_pnl['pnl_sats'] > 0]['pnl_sats'].sum() / 
                        df_pnl[df_pnl['pnl_sats'] < 0]['pnl_sats'].sum()) if len(df_pnl[df_pnl['pnl_sats'] < 0]) > 0 else float('inf')

    # 3. Formatear el Reporte para Gemini
    report_text = f"""
    [INYECCIÓN DE AUDITORÍA ESTRATÉGICA - {datetime.now().strftime('%Y-%m-%d %H:%M')}]
    Análisis de {total_trades} ciclos históricos:
    - Win Rate Real: {win_rate:.2f}%
    - Profit Factor: {profit_factor:.2f}
    - PnL Acumulado: {total_pnl} sats
    - Máxima Exposición (Drawdown): {max_drawdown} sats
    - Estado de Bóveda: {df['balance_sats'].iloc[-1]} sats
    
    CONSEJO PARA LA IA: Si el Profit Factor es < 1.5, aumenta la exigencia en la confianza (>90) para operar.
    """

    # 4. INYECTAR EN LA DB
    # Lo insertamos como una acción tipo 'SYSTEM_AUDIT'
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ai_decisions (market_price, action, confidence, logic_applied, balance_sats, pnl_sats)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        df['market_price'].iloc[-1], 
        'SYSTEM_AUDIT', 
        100, 
        report_text, 
        df['balance_sats'].iloc[-1],
        0
    ))
    
    conn.commit()
    conn.close()
    print("✅ Reporte de rentabilidad inyectado en la memoria de la IA.")

if __name__ == "__main__":
    generate_and_inject_report()
