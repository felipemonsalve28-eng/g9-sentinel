import os
import re

def patch_trailing_stop():
    file_path = 'engine.py'
    print("🛡️ Inyectando módulo de Trailing Stop Dinámico (V13.1)...")

    if not os.path.exists(file_path):
        print(f"❌ Error: No se encuentra {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Añadir la extracción del SL actual
    old_attributes = """pos_side = getattr(current_position, 'side', 'N/A')
                pos_price = getattr(current_position, 'price', 0)
                pos_margin = getattr(current_position, 'margin', 0)
                pos_pnl = getattr(current_position, 'pl', 'Desconocido')"""
    
    new_attributes = """pos_side = getattr(current_position, 'side', 'N/A')
                pos_price = getattr(current_position, 'price', 0)
                pos_margin = getattr(current_position, 'margin', 0)
                pos_pnl = getattr(current_position, 'pl', 'Desconocido')
                pos_sl = getattr(current_position, 'stoploss', 'N/A')"""
    
    content = content.replace(old_attributes, new_attributes)

    # 2. Actualizar el prompt de Gestión Activa (in_position)
    old_in_position_prompt_regex = r'prompt\s*=\s*f\"\"\"\s*SISTEMA DE GESTIÓN G9-SENTINEL V13[\s\S]*?\"\"\"'
    
    new_in_position_prompt = """prompt = f\"\"\"
                SISTEMA DE GESTIÓN G9-SENTINEL V13.1 (TRAILING STOP)
                ----------------------------------------------------
                ESTADO DE LA POSICIÓN ACTIVA:
                - Dirección: {pos_side.upper()}
                - Precio de Entrada: ${pos_price}
                - Precio Actual BTC: ${current_price}
                - Stop Loss Actual: ${pos_sl}
                - PnL Flotante: {pos_pnl} SATS
                
                SNAPSHOT TÉCNICO ACTUAL:
                - RSI: {signals['rsi']} ({signals['trend']})
                - Volatilidad: {signals['volatility']}
                
                TAREA DE GESTIÓN:
                1. Si el PnL es negativo, decide si debes hacer CLOSE_POSITION o HOLD_POSITION. ¡NUNCA alejes el Stop Loss!
                2. Si el PnL es positivo, tu misión es ASEGURAR GANANCIAS. Usa UPDATE_SL para mover el Stop Loss cerca del precio actual.
                3. REGLA MATEMÁTICA OBLIGATORIA: Si la posición es BUY, el nuevo SL debe ser MAYOR al SL actual. Si es SELL, el nuevo SL debe ser MENOR al SL actual.
                
                Responde SOLO con JSON, sin markdown:
                {{
                    "action": "CLOSE_POSITION" o "HOLD_POSITION" o "UPDATE_SL",
                    "new_stop_loss": numero decimal (solo si la acción es UPDATE_SL, de lo contrario envía 0),
                    "confidence": numero del 1 al 100,
                    "logic": "Justifica detalladamente tu movimiento defensivo u ofensivo."
                }}
                \"\"\""""
    
    content = re.sub(old_in_position_prompt_regex, new_in_position_prompt, content)

    # 3. Inyectar la lógica de ejecución del UPDATE_SL en el ciclo
    old_execution = """if action == "CLOSE_POSITION" and in_position:"""
    
    new_execution = """if action == "UPDATE_SL" and in_position:
                new_sl = decision.get("new_stop_loss")
                if new_sl:
                    new_sl = round_to_tick(new_sl)
                    print(f"🛡️ ACTUALIZANDO STOP LOSS DINÁMICO a: ${new_sl}")
                    try:
                        await client.futures.isolated.update_stoploss(id=current_position.id, stoploss=new_sl)
                        print("✅ TRAILING STOP ACTUALIZADO CON ÉXITO.")
                    except Exception as api_err:
                        print(f"❌ Error al actualizar SL: {api_err}")
                else:
                    print("⚠️ UPDATE_SL invocado pero sin nuevo precio. Manteniendo posición.")
                    
            elif action == "CLOSE_POSITION" and in_position:"""
    
    content = content.replace(old_execution, new_execution)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("🏁 V13.1 instalada. Gemini ahora tiene permisos para arrastrar el Stop Loss y blindar ganancias.")

if __name__ == "__main__":
    patch_trailing_stop()
