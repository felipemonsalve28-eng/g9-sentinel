import os
import shutil

def apply_patch():
    files = ['brain.py', 'engine.py']
    print("🛠️ Iniciando cirugía técnica G9-Sentinel V12...")

    # 1. Crear Backups
    for f in files:
        if os.path.exists(f):
            shutil.copy(f, f + ".bak")
            print(f"✅ Backup creado: {f}.bak")

    # --- MODIFICACIÓN DE BRAIN.PY ---
    print("🧠 Actualizando brain.py...")
    with open('brain.py', 'r') as f:
        brain_code = f.read()

    # Actualizar SQL de creación
    old_sql = "pnl_sats INTEGER DEFAULT 0"
    new_sql = "pnl_sats INTEGER DEFAULT 0,\n                indicators_snapshot TEXT -- Snapshot de RSI, BB, CVD"
    if "indicators_snapshot" not in brain_code:
        brain_code = brain_code.replace(old_sql, new_sql)

    # Actualizar firma de save_decision y su INSERT
    old_sig = "def save_decision(self, market_price, action, confidence, logic_applied):"
    new_sig = "def save_decision(self, market_price, action, confidence, logic_applied, indicators=None):"
    brain_code = brain_code.replace(old_sig, new_sig)
    
    old_insert = "VALUES (?, ?, ?, ?)"
    new_insert = "VALUES (?, ?, ?, ?, ?)"
    brain_code = brain_code.replace(old_insert, new_insert)
    
    old_params = "(market_price, action, confidence, logic_applied)"
    new_params = "(market_price, action, confidence, logic_applied, json.dumps(indicators) if indicators else None)"
    brain_code = brain_code.replace(old_params, new_params)

    with open('brain.py', 'w') as f:
        f.write(brain_code)

    # --- MODIFICACIÓN DE ENGINE.PY ---
    print("🚀 Actualizando engine.py...")
    with open('engine.py', 'r') as f:
        engine_code = f.read()

    # Añadir Imports
    if "import pandas" not in engine_code:
        imports = "import pandas as pd\nimport pandas_ta as ta\nfrom brain import G9Brain"
        engine_code = engine_code.replace("from brain import G9Brain", imports)

    # Inyectar función get_market_signals antes de run_trading_cycle
    signals_func = """
async def get_market_signals(client):
    try:
        candles = await client.futures.get_candles(limit=50)
        df = pd.DataFrame([{
            'open': float(c.open), 'high': float(c.high),
            'low': float(c.low), 'close': float(c.close), 'volume': float(c.volume)
        } for c in candles])
        df['rsi'] = ta.rsi(df['close'], length=14)
        bb = ta.bbands(df['close'], length=20, std=2)
        current_rsi = round(df['rsi'].iloc[-1], 2)
        upper_band = bb['BBU_20_2.0'].iloc[-1]
        lower_band = bb['BBL_20_2.0'].iloc[-1]
        last_close = df['close'].iloc[-1]
        vol = "ALTA" if (upper_band - lower_band) > (last_close * 0.01) else "NORMAL"
        return {
            "rsi": current_rsi, "bb_upper": round(upper_band, 2),
            "bb_lower": round(lower_band, 2), "volatility": vol,
            "trend": "SOBRECOMPRA" if current_rsi > 70 else ("SOBREVENTA" if current_rsi < 30 else "NEUTRAL")
        }
    except Exception as e:
        return {"rsi": 50, "bb_upper": 0, "bb_lower": 0, "volatility": "NORMAL", "trend": "NEUTRAL"}

"""
    if "async def get_market_signals" not in engine_code:
        engine_code = engine_code.replace("async def run_trading_cycle():", signals_func + "async def run_trading_cycle():")

    # Inyectar llamada a señales dentro del ciclo
    old_memoria = "memoria = brain.get_context_for_gemini(limit=10)"
    new_memoria = "signals = await get_market_signals(client)\n            memoria = brain.get_context_for_gemini(limit=10)"
    engine_code = engine_code.replace(old_memoria, new_memoria)

    # Actualizar el Prompt
    old_prompt_start = "SNAPSHOT DE CUENTA:"
    new_prompt_start = """SNAPSHOT DE MERCADO:
            - Precio BTC: ${current_price}
            - RSI: {signals['rsi']} ({signals['trend']})
            - Volatilidad: {signals['volatility']}
            - Bollinger: U {signals['bb_upper']} | L {signals['bb_lower']}
            
            SNAPSHOT DE CUENTA:"""
    engine_code = engine_code.replace(old_prompt_start, new_prompt_start)

    # Actualizar el guardado de decisión para incluir señales
    old_save = "brain.save_decision(current_price, action, decision.get('confidence'), decision.get('logic'))"
    new_save = "brain.save_decision(current_price, action, decision.get('confidence'), decision.get('logic'), indicators=signals)"
    engine_code = engine_code.replace(old_save, new_save)

    with open('engine.py', 'w') as f:
        f.write(engine_code)

    print("🏁 Cirugía completada. V12 lista para test.")

if __name__ == "__main__":
    apply_patch()
