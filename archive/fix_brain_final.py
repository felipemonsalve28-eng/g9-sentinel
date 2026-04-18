import re

def fix_brain():
    print("🔧 Reparando la base de datos (Eliminando error de sintaxis)...")
    with open('brain.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Reescribimos la función completa para asegurar cero errores de sintaxis
    correct_func = """
    def save_decision(self, market_price, action, confidence, logic_applied, indicators=None):
        \"\"\"Guarda la decisión actual para que sirva de memoria en el futuro.\"\"\"
        try:
            import json
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Inserción limpia y explícita
            cursor.execute('''
                INSERT INTO ai_decisions (market_price, action, confidence, logic_applied, indicators_snapshot)
                VALUES (?, ?, ?, ?, ?)
            ''', (market_price, action, confidence, logic_applied, json.dumps(indicators) if indicators else None))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error guardando memoria: {e}")
            return False
    """
    
    # Reemplaza desde la def save_decision hasta el final del archivo/clase
    content = re.sub(r'def save_decision\(self.*?return False(\n|$)', correct_func.strip() + '\n\n', content, flags=re.DOTALL)
    
    with open('brain.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ brain.py reparado: SQL Syntax solucionado de forma definitiva.")

if __name__ == "__main__":
    fix_brain()
