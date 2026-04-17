import asyncio
import os
from dotenv import load_dotenv
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient

load_dotenv('/home/felipemonsalve28/g9_production/.env')

async def scan_candles():
    print("🔍 INICIANDO ESCÁNER DE VELAS SDK V3")
    config = APIClientConfig(
        authentication=APIAuthContext(
            key=os.getenv('LNM_KEY'), 
            secret=os.getenv('LNM_SECRET'), 
            passphrase=os.getenv('LNM_PASSPHRASE')
        ), network="mainnet", timeout=10.0
    )
    try:
        async with LNMClient(config) as client:
            print("⏳ Pidiendo 2 velas al servidor...")
            res = await client.futures.get_candles({"limit": 2})
            
            print(f"\n📦 TIPO DE RESPUESTA RAÍZ: {type(res)}")
            
            if isinstance(res, list):
                print("✅ La respuesta es una lista directa.")
                print(f"🕯️ ESTRUCTURA DEL ITEM 0: {type(res[0])}")
                print(f"📊 VALORES: {res[0]}")
            else:
                print("⚠️ La respuesta es un Objeto Wrapper (Típico de Pydantic/SDKs nuevos).")
                print(f"🛠️ ATRIBUTOS DEL OBJETO: {[a for a in dir(res) if not a.startswith('_')]}")
                if hasattr(res, '__dict__'):
                    print(f"📊 DICCIONARIO INTERNO: {res.__dict__}")
                else:
                    print(f"📊 VALOR BRUTO: {res}")
                    
    except Exception as e:
        print(f"❌ Error en la petición: {e}")

if __name__ == "__main__":
    asyncio.run(scan_candles())
