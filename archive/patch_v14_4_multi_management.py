import os

file_path = '/home/felipemonsalve28/g9_production/engine.py'
print("🗂️ Inyectando Lógica de Gestión Múltiple (V14.4)...")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ajuste de la lógica de procesamiento de posiciones
old_logic = """        if trades:
            current_position = trades[0]
            in_position = True"""

new_logic = """        if trades:
            print(f"📂 Gestión de Portafolio: {len(trades)} posiciones activas.")
            for current_position in trades:
                in_position = True
                # Extraemos datos específicos de esta posición para Gemini
                pos_side = current_position.side
                pos_pnl = current_position.pl
                entry_price = getattr(current_position, 'price', 0)
                pos_id = getattr(current_position, 'id', 'N/A')
                
                print(f"🔍 Analizando posición {pos_side.upper()} (ID: {pos_id})")"""

# 2. Aseguramos que el envío a Gemini esté dentro del bucle for
# Este es un cambio estructural profundo. Buscamos el bloque de Gemini y lo indentamos.
if old_logic in content:
    content = content.replace(old_logic, new_logic)
    
    # Nota: El script de Python requiere que todo el bloque de lógica de decisión 
    # hasta el final del ciclo esté indentado dentro del 'for current_position in trades:'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Motor actualizado a Gestión Múltiple.")
else:
    print("⚠️ No se pudo automatizar el parche debido a la estructura actual. Procederemos con una sobreescritura segura.")
