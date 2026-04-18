import os
import re

def patch_prompt_antidoto():
    file_path = 'engine.py'
    print("💉 Inyectando antídoto contra el HOLD infinito en V12.2...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_prompt_block = """prompt = f\"\"\"
            SISTEMA DE TRADING G9-SENTINEL V12.2 (MODO FRANCOTIRADOR)
            ---------------------------------------------------------
            SNAPSHOT TÉCNICO:
            - Precio BTC: ${current_price}
            - RSI: {signals['rsi']} ({signals['trend']})
            - Volatilidad: {signals['volatility']}
            
            ESTADO DE CUENTA:
            - Balance: {balance} SATS
            - Límite de Margen (35%): {int(balance * 0.35)} SATS

            {memoria}

            TAREA DE ANÁLISIS EVOLUTIVO:
            1. Revisa las operaciones anteriores. El problema principal han sido las COMISIONES del broker.
            2. SOLUCIÓN AL PROBLEMA: Hacer HOLD para siempre NO es aceptable. La orden es CRECER la cuenta. 
            3. Para vencer a las comisiones, debes operar SOLO cuando el Alpha técnico sea EXTREMO (Ej: RSI por debajo de 35 o por encima de 65, o tras un quiebre de volatilidad).
            4. Cuando entres, exige un TP que te garantice un ratio R:R de al menos 1:3 para que la operación cubra el spread matemático del broker.
            5. Si no hay setup, haz HOLD. Si el setup es claro, ataca con confianza > 80.

            INSTRUCCIONES ESTRICTAS:
            1. 'margin': SATS a arriesgar (Max 35% del balance).
            2. 'leverage': Apalancamiento (1-50x. Usa 5-15x por defecto para no liquidar por spread).
            3. 'stop_loss' y 'take_profit': Precios exactos obligatorios.
            
            Responde SOLO con JSON, sin markdown:
            {{
                "action": "BUY" o "SELL" o "HOLD",
                "margin": numero entero,
                "leverage": numero entero,
                "stop_loss": numero decimal,
                "take_profit": numero decimal,
                "confidence": numero del 1 al 100,
                "logic": "Explica cómo este trade específico superará la barrera de comisiones y justifica el setup"
            }}
            \"\"\""""

    pattern = r'prompt\s*=\s*f\"\"\"[\s\S]*?\"\"\"'
    
    if re.search(pattern, content):
        updated_content = re.sub(pattern, new_prompt_block, content, count=1)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("✅ engine.py actualizado. El centinela ahora entiende cómo operar rentable.")
    else:
        print("⚠️ Error encontrando el bloque de prompt.")

if __name__ == "__main__":
    patch_prompt_antidoto()
