import asyncio
import os
from dotenv import load_dotenv
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient

# Cargamos el .env desde la ruta absoluta
load_dotenv('/home/felipemonsalve28/g9_production/.env')

async def main():
    # Configuramos la autenticación v3
    config = APIClientConfig(
        authentication=APIAuthContext(
            key=os.getenv('LNM_KEY'),
            secret=os.getenv('LNM_SECRET'),
            passphrase=os.getenv('LNM_PASSPHRASE'),
        ),
        network="mainnet",
        timeout=60.0
    )

    print("🔌 Intentando conexión con SDK v3...")
    
    try:
        async with LNMClient(config) as client:
            account = await client.account.get_account()
            
            if account and 'balance' in account:
                print(f"✅ ¡ÉXITO TOTAL! Conectado a LN Markets.")
                print(f"💰 Balance actual: {account['balance']} SATS")
            else:
                print(f"❌ Respuesta inesperada de la API: {account}")
                
    except Exception as e:
        print(f"❌ Error de autenticación o red: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
