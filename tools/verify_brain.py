import json, os

def verificar_consciencia():
    ctx_path = '/home/felipemonsalve28/g9_production/bot_context_report.txt'
    mem_path = '/home/felipemonsalve28/g9_production/data/session_memory.json'
    
    print("🔍 [AUDITORÍA DE CONTEXTO G9]")
    print("-" * 40)
    
    # 1. Verificar qué lee Gemini sobre el mercado
    if os.path.exists(ctx_path):
        print("✅ ARCHIVO DE CONTEXTO ENCONTRADO.")
        with open(ctx_path, 'r') as f:
            contenido = f.read()
            print("\n--- LO QUE GEMINI VE AHORA MISMO ---")
            print(contenido)
            print("-" * 35)
    else:
        print("❌ ERROR: El archivo de contexto no existe. El bot no está alimentando a la IA.")

    # 2. Verificar qué recuerda Gemini (Memoria)
    if os.path.exists(mem_path):
        print("\n✅ MEMORIA DE SESIÓN ENCONTRADA.")
        with open(mem_path, 'r') as f:
            memoria = json.load(f)
            print(f"PnL Acumulado: {memoria.get('total_pnl', 'N/A')}")
            print(f"Última Decisión: {memoria.get('last_decision', 'Ninguna')}")
    else:
        print("❌ AVISO: No hay memoria de sesión todavía.")

if __name__ == "__main__":
    verificar_consciencia()
