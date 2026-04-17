import os
import asyncio
import time
from dotenv import load_dotenv
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient

# Forzamos la carga desde la raíz absoluta
load_dotenv('/home/felipemonsalve28/g9_production/.env')

async def run_diagnostics():
    print("===================================================")
    print("🔍 DIAGNÓSTICO DE CONECTIVIDAD: LNMARKETS NETWORK")
    print("===================================================")
    
    # 1. Validación de variables de entorno
    network_env = os.getenv('LNM_NETWORK', 'mainnet')
    key = os.getenv('LNM_KEY')
    
    if not key:
        print("❌ CRÍTICO: No se detectó LNM_KEY en el archivo .env.")
        return

    print(f"📡 Red configurada en .env: {network_env.upper()}")
    print(f"🔑 Longitud de API Key: {len(key)} caracteres")

    # 2. Configuración del cliente V3
    config = APIClientConfig(
        authentication=APIAuthContext(
            key=key,
            secret=os.getenv('LNM_SECRET'),
            passphrase=os.getenv('LNM_PASSPHRASE'),
        ),
        network=network_env,
        timeout=15.0 # Timeout estricto para medir latencia
    )

    try:
        start_time = time.time()
        print("\n⏳ Conectando con los servidores de LNMarkets...")
        
        async with LNMClient(config) as client:
            # 3. Prueba de lectura de cuenta
            account = await client.account.get_account()
            latency = round((time.time() - start_time) * 1000, 2)
            
            if account and hasattr(account, 'balance'):
                print(f"✅ CONEXIÓN EXITOSA (Latencia: {latency} ms)")
                print(f"💰 BALANCE CONFIRMADO: {account.balance} SATS")
                
                # Opcional: Validar si hay operaciones colgadas que no sabíamos
                trades = await client.futures.isolated.get_running_trades()
                print(f"📂 Posiciones aisladas activas en el broker: {len(trades)}")
            else:
                print(f"⚠️ Advertencia: Conexión lograda, pero el payload de la cuenta es inusual: {account}")

    except Exception as e:
        error_msg = str(e).lower()
        print("\n❌ FALLO EN LA CONEXIÓN")
        if "401" in error_msg or "unauthorized" in error_msg:
            print("👉 DIAGNÓSTICO: Error de Autenticación. Tus llaves LNM son inválidas, están expiradas o el passphrase es incorrecto.")
        elif "timeout" in error_msg:
            print("👉 DIAGNÓSTICO: Timeout. El servidor de LNMarkets tardó mucho en responder. Verifica si tu VM tiene salida a internet estable.")
        else:
            print(f"👉 DIAGNÓSTICO: Error técnico del SDK o Red: {e}")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())

