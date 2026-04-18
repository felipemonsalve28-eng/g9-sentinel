import os
import re

BASE_DIR = '/home/felipemonsalve28/g9_production'

def patch_brain():
    file_path = os.path.join(BASE_DIR, 'core/brain.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Añadir inyección de performance al contexto (Buscamos la función get_context_for_gemini)
    # Suponiendo que devuelve una cadena o un diccionario, agregaremos un bloque de lectura rápida.
    # Dado que las firmas varían, haremos un parche dinámico al inicio del archivo para crear un helper
    if "def get_global_performance" not in content:
        helper = """\n
    def get_global_performance(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT winrate, delta_pnl FROM performance_logs ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row: return {"winrate": row[0], "delta": row[1]}
        except: pass
        return {"winrate": 50.0, "delta": 0.0}
"""
        # Insertamos el helper dentro de la clase G9Brain
        content = content.replace("class G9Brain:", f"class G9Brain:{helper}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Cerebro evolucionado: Nueva red neuronal para rendimiento macro.")

def patch_engine():
    file_path = os.path.join(BASE_DIR, 'core/engine.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Inyectar lectura de performance en el ciclo
    if "perf = brain.get_global_performance()" not in content:
        old_brain_call = "context = brain.get_context"
        new_brain_call = "perf = brain.get_global_performance()\n        context = brain.get_context"
        content = content.replace(old_brain_call, new_brain_call)

        # Inyectar reglas del Conservative Mode
        old_rules = "TAREA DE ANÁLISIS EVOLUTIVO Y DATA SCIENCE:"
        new_rules = """TAREA DE ANÁLISIS EVOLUTIVO Y DATA SCIENCE:
                [MACRO PERFORMANCE]: Winrate actual {perf['winrate']}%. Delta reciente: {perf['delta']} SATS.
                1. REGIMEN DE MERCADO: Si es RANGO, compra suelo/vende techo de Bollinger. Si es TENDENCIA, súbete.
                2. CONSERVATIVE MODE: Si el Winrate es < 45 o el Delta es negativo, DEBES reducir el tamaño del Take Profit, exigir un 'confidence' > 90 para entrar, y priorizar HOLD si hay duda.
                3. GESTIÓN DE RIESGO: Usa SL estricto siempre."""
        
        content = content.replace(old_rules, new_rules)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Prompt V16 inyectado: IA sensible al dolor financiero.")

patch_brain()
patch_engine()
