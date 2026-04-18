import os
import re

def patch_v13_final():
    file_path = 'engine.py'
    print("🛠️ Aplicando los métodos correctos del SDK de LNMarkets V3...")

    if not os.path.exists(file_path):
        print(f"❌ Error: No se encuentra {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Corregir la lectura de posiciones abiertas
    old_try_block = r"try:\s*positions_data = await client\.futures\.isolated\.get_positions\(\)[\s\S]*?current_position = active_positions\[0\] if in_position else None"
    
    new_try_block = """try:
                # SDK V3: Usamos get_running_trades para las operaciones activas
                active_positions = await client.futures.isolated.get_running_trades()
                in_position = len(active_positions) > 0
                current_position = active_positions[0] if in_position else None"""
    
    content = re.sub(old_try_block, new_try_block, content)

    # 2. Corregir el método de cierre de posición
    content = content.replace(
        "await client.futures.isolated.close_position(id=current_position.id)", 
        "await client.futures.isolated.close(id=current_position.id)"
    )

    # 3. Hacer robusta la lectura de atributos de la posición
    old_attributes = r"pos_side = current_position\.side[\s\S]*?pos_pnl = current_position\.pl if hasattr\(current_position, 'pl'\) else \"Desconocido\""
    
    new_attributes = """pos_side = getattr(current_position, 'side', 'N/A')
                pos_price = getattr(current_position, 'price', 0)
                pos_margin = getattr(current_position, 'margin', 0)
                pos_pnl = getattr(current_position, 'pl', 'Desconocido')"""
    
    content = re.sub(old_attributes, new_attributes, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("✅ engine.py actualizado. Los métodos 'get_running_trades' y 'close' están listos.")

if __name__ == "__main__":
    patch_v13_final()
