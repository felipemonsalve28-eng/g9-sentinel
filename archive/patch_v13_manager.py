import os
import re

def patch_position_manager():
    file_path = 'engine.py'
    print("🚀 Iniciando actualización a V13: Gestor de Posiciones Activas...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Inyectar la captura de posiciones abiertas justo después del ticker
    old_ticker_block = """            ticker = await client.futures.get_ticker()
            current_price = float(ticker.last_price)
            signals = await get_market_signals(client)"""
            
    new_ticker_block = """            ticker = await client.futures.get_ticker()
            current_price = float(ticker.last_price)
            signals = await get_market_signals(client)
            
            # --- NUEVO V13: GESTIÓN DE POSICIONES ABIERTAS ---
            try:
                positions_data = await client.futures.isolated.get_positions()
                # Filtramos las posiciones que no están cerradas
                active_positions = [p for p in positions_data if not hasattr(p, 'closed') or p.closed is False]
                in_position = len(active_positions) > 0
                current_position = active_positions[0] if in_position else None
            except Exception as e:
                print(f"⚠️ Aviso: No se pudieron validar las posiciones abiertas: {e}")
                in_position = False
                current_position = None
            # ------------------------------------------------"""

    if "get_positions" not in content:
        content = content.replace(old_ticker_block, new_ticker_block)

    # 2. Reemplazar el bloque del prompt estático por un sistema dual
    # Buscamos el bloque del prompt antiguo
    pattern_prompt = r'prompt\s*=\s*f\"\"\"[\s\S]*?\"\"\"'
    
    dual_prompt_logic = """
            if in_position:
                # MODO GESTIÓN: Evaluando una operación que ya está corriendo
                pos_side = current_position.side
                pos_price = current_position.price
                pos_margin = current_position.margin
                pos_pnl = current_position.pl if hasattr(current_position, 'pl') else "Desconocido"
                
                print(f"⚙️ GESTIÓN ACTIVA: Posición {pos_side.upper()} detectada. Entrada: ${pos_price} | PnL Actual: {pos_pnl} SATS")
                
                prompt = f\"\"\"
                SISTEMA DE GESTIÓN G9-SENTINEL V13
                -----------------------------------
                ESTADO DE LA POSICIÓN ACTIVA:
                - Dirección: {pos_side.upper()}
                - Precio de Entrada: ${pos_price}
                - Precio Actual BTC: ${current_price}
                - PnL Flotante: {pos_pnl} SATS
                
                SNAPSHOT TÉCNICO ACTUAL:
                - RSI: {signals['rsi']} ({signals['trend']})
                - Volatilidad: {signals['volatility']}
                
                TAREA: Tienes una posición abierta. Evalúa si la estructura del mercado ha cambiado. 
                Si el RSI se ha revertido en tu contra o el PnL es suficientemente bueno para asegurar comisiones, CIERRA la posición.
                Si la tendencia sigue a tu favor, MANTÉN la posición.
                
                Responde SOLO con JSON, sin markdown:
                {{
                    "action": "CLOSE_POSITION" o "HOLD_POSITION",
                    "confidence": numero del 1 al 100,
                    "logic": "Justifica por qué asegurar ganancias/cortar pérdidas o dejarla correr."
                }}
                \"\"\"
            else:
                # MODO FRANCOTIRADOR: Buscando entrada (El prompt de la V12.2)
                prompt = f\"\"\"
                SISTEMA DE TRADING G9-SENTINEL V13 (MODO FRANCOTIRADOR)
                -------------------------------------------------------
                SNAPSHOT TÉCNICO:
                - Precio BTC: ${current_price}
                - RSI: {signals['rsi']} ({signals['trend']})
                - Volatilidad: {signals['volatility']}
                
                ESTADO DE CUENTA:
                - Balance: {balance} SATS
                - Límite de Margen (35%): {int(balance * 0.35)} SATS

                {memoria}

                TAREA DE ANÁLISIS EVOLUTIVO:
                1. Las COMISIONES son tu mayor enemigo. Hacer HOLD para siempre NO es aceptable.
                2. Opera SOLO cuando el Alpha técnico sea EXTREMO (Ej: RSI < 35 o > 65).
                3. Exige un setup claro. Si no lo hay, responde HOLD.

                INSTRUCCIONES ESTRICTAS:
                Responde SOLO con JSON, sin markdown:
                {{
                    "action": "BUY" o "SELL" o "HOLD",
                    "margin": numero entero,
                    "leverage": numero entero,
                    "stop_loss": numero decimal,
                    "take_profit": numero decimal,
                    "confidence": numero del 1 al 100,
                    "logic": "Explica tu setup extremo"
                }}
                \"\"\"
"""
    if re.search(pattern_prompt, content):
        content = re.sub(pattern_prompt, dual_prompt_logic.strip(), content, count=1)

    # 3. Actualizar la lógica de ejecución para manejar el CLOSE_POSITION
    execution_logic_old = """if action != "HOLD":
                if margin > (balance * 0.35):"""
                
    execution_logic_new = """if action == "CLOSE_POSITION" and in_position:
                print("🚨 ORDEN DE CIERRE RECIBIDA. Asegurando posición...")
                try:
                    await client.futures.isolated.close_position(id=current_position.id)
                    print("✅ POSICIÓN CERRADA CON ÉXITO.")
                except Exception as api_err:
                    print(f"❌ Error al cerrar posición: {api_err}")
            
            elif action in ["BUY", "SELL"] and not in_position:
                if margin > (balance * 0.35):"""
    
    if "CLOSE_POSITION" not in content:
         content = content.replace(execution_logic_old, execution_logic_new)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("🏁 V13 instalada. El bot ahora auditará sus propias operaciones abiertas.")

if __name__ == "__main__":
    patch_position_manager()
