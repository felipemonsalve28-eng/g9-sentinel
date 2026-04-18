import os
import re

FILE = '/home/felipemonsalve28/g9_production/core/engine.py'
with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Capturamos la firma exacta de ejecución en engine.py
old_block = r"trade_params = FuturesOrder\(\s*type=\"market\",\s*side=action\.lower\(\),\s*margin=margin,\s*leverage=leverage,\s*stoploss=sl,\s*takeprofit=tp\s*\)"

# Inyectamos el filtro de lógica posicional estricta
new_block = """# --- GUARDRAIL MATEMÁTICO V15.1 ---
                    try:
                        if action == "BUY":
                            if sl and float(sl) >= current_price: sl = None
                            if tp and float(tp) <= current_price: tp = None
                        elif action == "SELL":
                            if sl and float(sl) <= current_price: sl = None
                            if tp and float(tp) >= current_price: tp = None
                    except:
                        sl, tp = None, None
                    # ----------------------------------
                    
                    trade_params = FuturesOrder(
                        type="market",
                        side=action.lower(),
                        margin=margin,
                        leverage=leverage,
                        stoploss=sl,
                        takeprofit=tp
                    )"""

if re.search(old_block, content):
    content = re.sub(old_block, new_block, content)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Guardrail Matemático V15.1 inyectado con éxito. Error 400 neutralizado.")
else:
    print("❌ Falla estructural: No se encontró la firma de FuturesOrder. Se requiere inspección manual.")
