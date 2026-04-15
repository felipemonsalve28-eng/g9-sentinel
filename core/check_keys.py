import os
from dotenv import load_dotenv

load_dotenv('/home/felipemonsalve28/g9_production/.env')

keys = ['LNM_KEY', 'LNM_SECRET', 'LNM_PASSPHRASE', 'TELEGRAM_TOKEN']
print("--- Verificando carga de .env ---")
for k in keys:
    val = os.getenv(k)
    if val:
        print(f"✅ {k}: Cargada correctamente (Largo: {len(val)})")
    else:
        print(f"❌ {k}: NO SE ENCONTRÓ EN EL ARCHIVO")
