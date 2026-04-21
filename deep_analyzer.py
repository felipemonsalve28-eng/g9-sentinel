import os
import sqlite3
import pandas as pd
import json
from datetime import datetime

class G9DeepAnalyzer:
    def __init__(self, db_path='/home/felipemonsalve28/g9_production/data/g9_market.db'):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            print(f"❌ ERROR: Base de datos no encontrada en {self.db_path}")
            exit(1)

    def load_data(self):
        """Extrae la memoria neuronal y la convierte en un DataFrame estructurado."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM ai_decisions"
            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                print("⚠️ La base de datos está vacía. G9 aún no ha operado.")
                return None

            # Procesar la columna JSON para extraer métricas clave
            df['m1_rsi'] = df['indicators_snapshot'].apply(self._extract_metric, args=('m1', 'rsi'))
            df['m5_rsi'] = df['indicators_snapshot'].apply(self._extract_metric, args=('m5', 'rsi'))
            df['h1_trend'] = df['indicators_snapshot'].apply(self._extract_metric, args=('h1', 'trend'))
            
            # Clasificar resultados
            df['resultado'] = df['pnl_sats'].apply(lambda x: 'WIN' if x > 0 else ('LOSS' if x < 0 else 'EV/HOLD'))
            
            return df
        except Exception as e:
            print(f"❌ Error al cargar datos: {e}")
            return None

    def _extract_metric(self, json_str, timeframe, metric):
        """Extrae de forma segura datos del snapshot JSON."""
        if not json_str:
            return None
        try:
            data = json.loads(json_str)
            if data and timeframe in data and data[timeframe]:
                return data[timeframe].get(metric)
            return None
        except:
            return None

    def generate_report(self):
        """Genera el reporte de inteligencia de enjambre."""
        print("\n" + "="*50)
        print("🚀 G9-SENTINEL V25 - DEEP ANALYZER REPORT")
        print("="*50)

        df = self.load_data()
        if df is None: return

        # 1. KPIs Generales
        total_trades = len(df[df['action'].isin(['BUY', 'SELL'])])
        wins = len(df[df['resultado'] == 'WIN'])
        losses = len(df[df['resultado'] == 'LOSS'])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        total_pnl = df['pnl_sats'].sum()
        
        print("\n📊 1. EFICIENCIA OPERATIVA")
        print(f"   ▶ Total Ejecuciones: {total_trades}")
        print(f"   ▶ Win Rate:          {win_rate:.2f}% ({wins} W / {losses} L)")
        print(f"   ▶ PnL Acumulado:     {total_pnl} sats")
        print(f"   ▶ Margen Promedio:   {df[df['action'].isin(['BUY', 'SELL'])]['margin'].mean():.2f}")

        # 2. Análisis de Confianza de la IA
        print("\n🧠 2. PRECISIÓN DE IA (CONFIDENCE SCORE)")
        if not df['confidence'].isnull().all():
            high_conf = df[df['confidence'] >= 90]
            hc_wins = len(high_conf[high_conf['resultado'] == 'WIN'])
            hc_total = len(high_conf[high_conf['action'].isin(['BUY', 'SELL'])])
            hc_wr = (hc_wins / hc_total * 100) if hc_total > 0 else 0
            
            print(f"   ▶ Win Rate (Confianza > 90%): {hc_wr:.2f}%")
            print(f"   ▶ PnL con Alta Confianza:     {high_conf['pnl_sats'].sum()} sats")

        # 3. Sweet Spots Técnicos (RSI M1)
        print("\n🎯 3. ZONAS DE ALTA RENTABILIDAD (SWEET SPOTS)")
        ganadoras = df[df['resultado'] == 'WIN']
        
        if not ganadoras.empty and not ganadoras['m1_rsi'].isnull().all():
            longs_ganadores = ganadoras[ganadoras['action'] == 'BUY']
            shorts_ganadores = ganadoras[ganadoras['action'] == 'SELL']
            
            avg_rsi_long = longs_ganadores['m1_rsi'].mean() if not longs_ganadores.empty else "N/A"
            avg_rsi_short = shorts_ganadores['m1_rsi'].mean() if not shorts_ganadores.empty else "N/A"
            
            print(f"   ▶ Promedio RSI (M1) en LONGs ganadores:  {avg_rsi_long}")
            print(f"   ▶ Promedio RSI (M1) en SHORTs ganadores: {avg_rsi_short}")
        else:
            print("   ▶ Datos insuficientes para RSI Sweet Spots.")

        # 4. Tendencia H1 (Alineación Fractal)
        print("\n📈 4. ALINEACIÓN FRACTAL (H1)")
        alineados = df[((df['action'] == 'BUY') & (df['h1_trend'] == 'UP')) | 
                       ((df['action'] == 'SELL') & (df['h1_trend'] == 'DOWN'))]
        contra_tend = df[((df['action'] == 'BUY') & (df['h1_trend'] == 'DOWN')) | 
                         ((df['action'] == 'SELL') & (df['h1_trend'] == 'UP'))]
        
        al_pnl = alineados['pnl_sats'].sum()
        ct_pnl = contra_tend['pnl_sats'].sum()
        
        print(f"   ▶ PnL Operando A FAVOR de H1: {al_pnl} sats")
        print(f"   ▶ PnL Operando CONTRA H1:     {ct_pnl} sats")

        print("\n" + "="*50)
        print(f"📅 Reporte generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50 + "\n")

if __name__ == "__main__":
    analyzer = G9DeepAnalyzer()
    analyzer.generate_report()
