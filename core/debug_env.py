import os
from dotenv import load_dotenv

# Usamos la ruta que confirmamos antes
load_dotenv('/home/felipemonsalve28/g9_production/.env')

def check_var(name):
    val = os.getenv(name)
    if val:
        print(f"✅ {name}: Detectada (Longitud: {len(val)})")
    else:
        print(f"❌ {name}: NO ENCONTRADA")

print("--- Revisión de Credenciales ---")
check_var('LNM_KEY')
check_var('LNM_SECRET')
check_var('LNM_PASSPHRASE')
check_var('LNM_NETWORK')
