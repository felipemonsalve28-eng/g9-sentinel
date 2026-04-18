import os
import sqlite3
import re
import shutil

BASE_DIR = '/home/felipemonsalve28/g9_production'
# Rutas ajustadas a Arquitectura Fase 1
DB_PATH = os.path.join(BASE_DIR, 'data/g9_market.db')
ENGINE_PATH = os.path.join(BASE_DIR, 'core/engine.py')

def patch_database():
    print("🗄️ 1. Actualizando Base de Datos (Memoria Evolutiva)...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE ai_decisions ADD COLUMN error_category TEXT DEFAULT 'NINGUNO';")
        conn.commit()
        print("✅ DB: Columna 'error_category' añadida con éxito.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✅ DB: La columna 'error_category' ya existe.")
        else:
            print(f"❌ Error SQL: {e}")
    finally:
        conn.close()

def patch_market_signals():
    print("📊 2. Inyectando ADX y Detección de Regimen de Mercado...")
    with open(ENGINE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    shutil.copy(ENGINE_PATH, ENGINE_PATH + ".v14_bak")

    # Regex optimizada para capturar la función get_market_signals completa
    old_signals_func = r"async def get_market_signals\(client\):[\s\S]*?return \{\"rsi\": 50\}"
    
    new_signals_func = """async def get_market_signals(client):
    try:
        candles = await client.futures.get_candles(limit=50)
        df = pd.DataFrame([{
            'high': float(c.high), 'low': float(c.low), 'close': float(c.close)
        } for c in candles])
        
        df['rsi'] = ta.rsi(df['close'], length=14)
        bb = ta.bbands(df['close'], length=20, std=2)
        adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
        df['adx'] = adx_df['ADX_14'] if adx_df is not None else 0

        current_rsi = round(df['rsi'].iloc[-1], 2)
        current_adx = round(df['adx'].iloc[-1], 2)
        upper_band = bb['BBU_20_2.0'].iloc[-1]
        lower_band = bb['BBL_20_2.0'].iloc[-1]
        
        regimen = "TENDENCIA FUERTE" if current_adx > 25 else "RANGO/LATERAL"
        trend = "SOBRECOMPRA" if current_rsi > 70 else ("SOBREVENTA" if current_rsi < 30 else "NEUTRAL")

        return {
            "rsi": current_rsi,
            "trend": trend,
            "adx": current_adx,
            "regimen": regimen,
            "bb_upper": round(upper_band, 2),
            "bb_lower": round(lower_band, 2)
        }
    except Exception as e:
        return {"rsi": 50, "trend": "NEUTRAL", "adx": 0, "regimen": "DESCONOCIDO", "bb_upper": 0, "bb_lower": 0}"""

    content = re.sub(old_signals_func, new_signals_func, content)
    
    with open(ENGINE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Motor de Señales actualizado con ADX.")

def patch_prompts():
    print("🧠 3. Optimizando el Cerebro (Chain of Thought & Gestión de Riesgo)...")
    with open(ENGINE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Inyección de ADX y Bollinger en el Snapshot del Prompt
    content = content.replace(
        "RSI: {signals['rsi']}",
        "RSI: {signals['rsi']} ({signals['trend']}) | ADX: {signals['adx']} ({signals['regimen']}) | BB: U {signals['bb_upper']} / L {signals['bb_lower']}"
    )

    # Inyección de Lógica Evolutiva y CoT
    old_rules = "TAREA DE ANÁLISIS EVOLUTIVO:"
    new_rules = """TAREA DE ANÁLISIS EVOLUTIVO Y DATA SCIENCE:
                1. REGIMEN DE MERCADO: Si el Regimen es 'RANGO/LATERAL' (ADX < 25), compra cerca del Suelo de Bollinger y vende en el Techo. Si es 'TENDENCIA FUERTE' (ADX > 25), ignora el RSI sobrecomprado y móntate en la tendencia.
                2. GESTIÓN DE RIESGO ASIMÉTRICA: Si tu 'confidence' es mayor a 85 y el ADX apoya el movimiento, usa un margen mayor.
                3. AUTO-CRÍTICA: Genera un 'chain_of_thought' (paso a paso lógico) antes de tu decisión final.
                4. CATEGORIZACIÓN: Si vienes de pérdidas, asigna un 'error_category' (Ej: 'FALSO_QUIEBRE', 'FOMO_RSI') a trades pasados."""

    content = content.replace(old_rules, new_rules)

    # Actualización de estructura JSON esperada
    old_json_struct = """Responde SOLO con JSON, sin markdown:
                {
                    "action": "BUY" o "SELL" o "HOLD","""
    
    new_json_struct = """Responde SOLO con JSON, sin markdown:
                {
                    "chain_of_thought": "Análisis técnico paso a paso detalladamente",
                    "error_category": "Clasifica el error de tu último trade perdido o 'NINGUNO'",
                    "action": "BUY" o "SELL" o "HOLD","""
    
    content = content.replace(old_json_struct, new_json_struct)

    with open(ENGINE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Prompts actualizados.")

if __name__ == "__main__":
    patch_database()
    patch_market_signals()
    patch_prompts()
    print("🏁 SISTEMA V15 INSTALADO.")
