import os

file_path = 'core/engine.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '    async def process_strategy_decision(self, decision, balance, client):'

if target in content:
    top_half = content.split(target)[0]
    new_func = """    async def process_strategy_decision(self, decision, balance, client):
        \"\"\"Ejecuta las decisiones de entrada al mercado (strategy.txt)\"\"\"
        action = decision.get("action")
        
        if action in ["BUY", "SELL"]:
            margin = decision.get("margin", 0)
            leverage = decision.get("leverage", 10)
            sl = decision.get("stop_loss")
            tp = decision.get("take_profit")
            
            # Control de riesgo maestro (Máximo 35% del balance real)
            max_margin = int(balance * 0.35)
            if margin > max_margin:
                margin = max_margin
                
            print(f"🔨 EJECUTANDO {action} | Margen: {margin} Sats | Apalan: {leverage}x | SL: {sl} | TP: {tp}")
            try:
                # Construimos el diccionario base limpio
                params = {
                    "type": "market",
                    "side": "b" if action == "BUY" else "s",
                    "margin": int(margin),
                    "leverage": float(leverage)
                }
                
                # Solo inyectamos SL y TP si realmente existen
                if sl and float(sl) > 0:
                    params["stoploss"] = float(sl)
                if tp and float(tp) > 0:
                    params["takeprofit"] = float(tp)

                # Disparamos la orden
                await client.futures.isolated.new_trade(params)
                print("✅ ORDEN EJECUTADA CON ÉXITO")
            except Exception as e:
                print(f"❌ Error al ejecutar Orden: {e}")
        else:
            print(f"⏳ STRAT [HOLD]: Buscando setup. Lógica: {decision.get('logic')}")
"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(top_half + new_func)
    print("✅ ¡Cirugía completada! engine.py actualizado perfectamente.")
else:
    print("❌ No se encontró la función en el archivo.")
