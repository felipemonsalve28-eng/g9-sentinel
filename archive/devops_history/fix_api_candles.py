import os

BASE_DIR = "/home/felipemonsalve28/g9_production"
ENGINE_PATH = os.path.join(BASE_DIR, "core/engine.py")
MAIN_PATH = os.path.join(BASE_DIR, "main.py")

def apply_hotfix():
    print("🔧 Aplicando Hotfix de API y Parseo Seguro...")

    # 1. Reparar engine.py
    with open(ENGINE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    old_block = """        try:
            candles = await client.futures.get_candles(limit=50)
            df = pd.DataFrame([{
                'high': float(c.high), 'low': float(c.low), 'close': float(c.close)
            } for c in candles])"""

    new_block = """        try:
            # SDK V3 requiere un diccionario para los parámetros
            candles = await client.futures.get_candles({"limit": 50})
            
            # Parseo blindado: soporta objetos, diccionarios y listas nativas
            parsed_data = []
            for c in candles:
                try:
                    high = float(getattr(c, 'high', c.get('high') if isinstance(c, dict) else c[2]))
                    low = float(getattr(c, 'low', c.get('low') if isinstance(c, dict) else c[3]))
                    close = float(getattr(c, 'close', c.get('close') if isinstance(c, dict) else c[4]))
                    parsed_data.append({'high': high, 'low': low, 'close': close})
                except:
                    continue
                    
            df = pd.DataFrame(parsed_data)"""

    if "limit=50" in content:
        content = content.replace(old_block, new_block)
        with open(ENGINE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ engine.py: Extracción de velas blindada para SDK V3.")
    else:
        print("⚠️ No se encontró el bloque a reemplazar en engine.py.")

    # 2. Actualizar el banner en main.py
    if os.path.exists(MAIN_PATH):
        with open(MAIN_PATH, "r", encoding="utf-8") as f:
            main_content = f.read()
        
        if "V16.5" in main_content:
            main_content = main_content.replace("V16.5", "V18")
            with open(MAIN_PATH, "w", encoding="utf-8") as f:
                f.write(main_content)
            print("✅ main.py: Banner actualizado a V18.")

if __name__ == "__main__":
    apply_hotfix()
