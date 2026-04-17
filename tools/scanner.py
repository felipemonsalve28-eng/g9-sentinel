import os
import asyncio
import inspect
from dotenv import load_dotenv
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient

load_dotenv('/home/felipemonsalve28/g9_production/.env')

async def main():
    config = APIClientConfig(
        authentication=APIAuthContext(
            key=os.getenv('LNM_KEY'), secret=os.getenv('LNM_SECRET'), passphrase=os.getenv('LNM_PASSPHRASE')
        ), network="mainnet", timeout=10.0
    )
    try:
        async with LNMClient(config) as client:
            print("🔍 Analizando la firma de 'new_trade'...")
            
            # Usamos inspect para ver qué argumentos pide exactamente la función
            firma = inspect.signature(client.futures.isolated.new_trade)
            print(f"\n📋 Firma exacta de la función:\nnew_trade{firma}\n")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
