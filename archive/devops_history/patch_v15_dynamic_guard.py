import os

FILE = '/home/felipemonsalve28/g9_production/core/engine.py'

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
injected = False

for line in lines:
    # Detectamos la creación de la orden sin importar su espaciado
    if ("trade_params = FuturesOrder(" in line or "order = FuturesOrder(" in line) and not injected:
        spaces = len(line) - len(line.lstrip())
        indent = " " * spaces
        
        # Construimos el guardrail respetando la indentación original
        guardrail = f"{indent}# --- GUARDRAIL MATEMÁTICO V15.1 ---\n"
        guardrail += f"{indent}try:\n"
        guardrail += f"{indent}    if action == 'BUY':\n"
        guardrail += f"{indent}        if sl and float(sl) >= current_price: sl = None\n"
        guardrail += f"{indent}        if tp and float(tp) <= current_price: tp = None\n"
        guardrail += f"{indent}    elif action == 'SELL':\n"
        guardrail += f"{indent}        if sl and float(sl) <= current_price: sl = None\n"
        guardrail += f"{indent}        if tp and float(tp) >= current_price: tp = None\n"
        guardrail += f"{indent}except Exception as e:\n"
        # Escapamos la variable 'e' con dobles llaves para evitar el NameError
        guardrail += f"{indent}    print(f'⚠️ Guardrail mitigó un error de variables: {{e}}')\n"
        guardrail += f"{indent}    sl, tp = None, None\n"
        guardrail += f"{indent}# ----------------------------------\n"
        
        new_lines.append(guardrail)
        injected = True
        
    new_lines.append(line)

if injected:
    with open(FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("✅ Guardrail Matemático V15.1 inyectado con éxito mediante rastreo dinámico.")
else:
    print("❌ Error: No se pudo localizar la invocación de FuturesOrder.")
