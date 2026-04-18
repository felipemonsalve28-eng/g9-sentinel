import os
import re
import shutil

def patch_prompt():
    file_path = 'engine.py'
    
    print("🛠️ Iniciando parche de Prompt Evolutivo (V12.1)...")
    
    # 1. Crear Backup
    if os.path.exists(file_path):
        shutil.copy(file_path, file_path + ".prompt_bak")
        print(f"✅ Backup creado: {file_path}.prompt_bak")
    else:
        print("❌ Error: No se encuentra engine.py")
        return

    # 2. Leer archivo original
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. Definir el nuevo bloque del prompt completo (Lógica + JSON)
    new_prompt_block = """prompt = f\"\"\"
            SISTEMA DE TRADING G9-SENTINEL V12.1
            ------------------------------------
            SNAPSHOT TÉCNICO:
            - Precio BTC: ${current_price}
            - RSI: {signals['rsi']} ({signals['trend']})
            - Volatilidad: {signals['volatility']}
            
            ESTADO DE CUENTA:
            - Balance: {balance} SATS
            - Límite de Margen (35%): {int(balance * 0.35)} SATS

            {memoria}

            TAREA DE ANÁLISIS EVOLUTIVO:
            1. Revisa las 'Operaciones -1 a -10'. Si ves 'NEUTRAL' o 'PÉRDIDA' recurrentes, NO intentes compensar subiendo el apalancamiento.
            2. Analiza si el RSI estaba en sobrecompra/sobreventa en tus fallos anteriores.
            3. Si tu 'confidence' es menor a 80, el 'leverage' NO puede superar 10x.
            4. Si el mercado está en Volatilidad ALTA, prioriza HOLD o reduce el margen a la mitad.

            Tus decisiones afectan directamente la acumulación de Sats. Sé un gestor de riesgo, no un jugador.

            INSTRUCCIONES ESTRICTAS:
            1. 'margin': SATS a arriesgar (Max 35% del balance).
            2. 'leverage': Apalancamiento (1-50x).
            3. 'stop_loss' y 'take_profit': Precios exactos. Recuerda: Si es BUY, TP debe ser MAYOR al precio actual y SL MENOR. Si es SELL, TP debe ser MENOR al precio actual y SL MAYOR.
            
            Responde SOLO con JSON, sin markdown:
            {{
                "action": "BUY" o "SELL" o "HOLD",
                "margin": numero entero,
                "leverage": numero entero,
                "stop_loss": numero decimal,
                "take_profit": numero decimal,
                "confidence": numero del 1 al 100,
                "logic": "Análisis del PnL pasado y justificación técnica actual"
            }}
            \"\"\""""

    # 4. Expresión regular para encontrar y reemplazar el bloque prompt antiguo
    # Busca 'prompt = f"""' (o variaciones de espacios) hasta el siguiente '"""'
    pattern = r'prompt\s*=\s*f\"\"\"[\s\S]*?\"\"\"'
    
    # Verificar si encontramos el patrón
    if re.search(pattern, content):
        updated_content = re.sub(pattern, new_prompt_block, content, count=1)
        
        # 5. Escribir los cambios
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("✅ engine.py actualizado con el nuevo prompt evolutivo.")
    else:
        print("⚠️ No se pudo encontrar el bloque 'prompt = f\"\"\"' en el archivo. Verifica el formato.")

if __name__ == "__main__":
    patch_prompt()
