import os

FILE = '/home/felipemonsalve28/g9_production/core/engine.py'
with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Purgar el parche anterior fallido
cleaned_lines = []
skip = False
for line in lines:
    if "# --- GUARDRAIL MATEMÁTICO V15.1" in line: skip = True
    if skip and "# ----------------------------------" in line:
        skip = False
        continue
    if not skip: cleaned_lines.append(line)

# 2. Inyectar el Guardrail V15.2 sobreescribiendo el bloque exacto
final_lines = []
skip_count = 0
injected = False

for line in cleaned_lines:
    # Omitimos las 5 líneas originales del FuturesOrder viejo
    if skip_count > 0:
        skip_count -= 1
        continue

    # Localizamos el punto exacto de creación de orden
    if "order = FuturesOrder(" in line and not injected:
        skip_count = 5
        spaces = len(line) - len(line.lstrip())
        indent = " " * spaces
        
        new_block = f"""{indent}# --- GUARDRAIL MATEMÁTICO V15.2 ---
{indent}raw_action = entry_data.get("action", "HOLD").upper()
{indent}raw_sl = entry_data.get("stop_loss")
{indent}raw_tp = entry_data.get("take_profit")
{indent}
{indent}try:
{indent}    if raw_sl: raw_sl = float(raw_sl)
{indent}    if raw_tp: raw_tp = float(raw_tp)
{indent}except:
{indent}    raw_sl, raw_tp = None, None
{indent}
{indent}# Sanitización de lógica posicional estricta
{indent}if raw_action == "BUY":
{indent}    if raw_sl and raw_sl >= current_price: raw_sl = None
{indent}    if raw_tp and raw_tp <= current_price: raw_tp = None
{indent}elif raw_action == "SELL":
{indent}    if raw_sl and raw_sl <= current_price: raw_sl = None
{indent}    if raw_tp and raw_tp >= current_price: raw_tp = None
{indent}
{indent}order = FuturesOrder(
{indent}    type='market', side=raw_action.lower(),
{indent}    margin=mrg, leverage=entry_data.get("leverage", 1),
{indent}    stoploss=round_to_tick(raw_sl) if raw_sl else None,
{indent}    takeprofit=round_to_tick(raw_tp) if raw_tp else None
{indent})
{indent}# ----------------------------------\n"""
        final_lines.append(new_block)
        injected = True
        continue
        
    final_lines.append(line)

with open(FILE, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

if injected:
    print("✅ Guardrail V15.2 Inyectado: IA controlada matemáticamente.")
else:
    print("❌ Error: No se localizó la variable de orden.")
