import os

BASE_DIR = "/home/felipemonsalve28/g9_production"
ENGINE_PATH = os.path.join(BASE_DIR, "core/engine.py")

def apply_bb_hotfix():
    print("🔧 Aplicando Extractor Dinámico de Bollinger...")

    with open(ENGINE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    old_bb_logic = """            bb_width = 0
            if bb_df is not None:
                bb_width = round(bb_df['BBU_20_2.0'].iloc[-1] - bb_df['BBL_20_2.0'].iloc[-1], 2)"""

    new_bb_logic = """            bb_width = 0
            if bb_df is not None and not bb_df.empty:
                try:
                    # Extracción dinámica blindada contra cambios de versión de pandas_ta
                    upper_col = [c for c in bb_df.columns if 'BBU' in c][0]
                    lower_col = [c for c in bb_df.columns if 'BBL' in c][0]
                    bb_width = round(bb_df[upper_col].iloc[-1] - bb_df[lower_col].iloc[-1], 2)
                except IndexError:
                    bb_width = 0"""

    if "bb_width = 0" in content:
        content = content.replace(old_bb_logic, new_bb_logic)
        with open(ENGINE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Hotfix aplicado: core/engine.py ahora extrae las bandas dinámicamente.")
    else:
        print("⚠️ No se encontró el bloque exacto. Revisa el archivo engine.py.")

if __name__ == "__main__":
    apply_bb_hotfix()
