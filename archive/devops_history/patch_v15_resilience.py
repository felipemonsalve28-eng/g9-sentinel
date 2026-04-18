import os

FILE = '/home/felipemonsalve28/g9_production/core/engine.py'

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
injected = False

for line in lines:
    # Localizamos el punto exacto de envío de la orden
    if "await client.futures.isolated.new_trade(order)" in line and not injected:
        spaces = len(line) - len(line.lstrip())
        indent = " " * spaces
        
        # Inyectamos el bloque Try/Except anidado para ejecución resiliente
        block = f"{indent}try:\n"
        block += f"{indent}    await client.futures.isolated.new_trade(order)\n"
        block += f"{indent}    print('✅ ¡ORDEN EJECUTADA EXITOSAMENTE!')\n"
        block += f"{indent}except Exception as order_err:\n"
        block += f"{indent}    err_str = str(order_err)\n"
        block += f"{indent}    if 'Stoploss' in err_str or 'Takeprofit' in err_str or 'liquidation' in err_str:\n"
        block += f"{indent}        print(f'⚠️ Exchange rechazó márgenes SL/TP. Forzando entrada pura a mercado...')\n"
        block += f"{indent}        order_pure = FuturesOrder(type='market', side=order.side, margin=order.margin, leverage=order.leverage)\n"
        block += f"{indent}        await client.futures.isolated.new_trade(order_pure)\n"
        block += f"{indent}        print('✅ ¡ORDEN PURA EJECUTADA! La IA ajustará el Trailing Stop en el próximo ciclo.')\n"
        block += f"{indent}    else:\n"
        block += f"{indent}        raise order_err\n"
        
        new_lines.append(block)
        injected = True
    else:
        new_lines.append(line)

if injected:
    with open(FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("✅ Motor de Ejecución Blindado (V15.3). Resiliencia ante rechazos de API activa.")
else:
    print("❌ Error: No se encontró la instrucción de ejecución en engine.py.")
