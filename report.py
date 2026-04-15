import os
import asyncio
from dotenv import load_dotenv
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient
from notifier import G9Notifier

BASE_DIR = "/home/felipemonsalve28/g9_production"
load_dotenv(os.path.join(BASE_DIR, '.env'))

async def send_log_report():
    notifier = G9Notifier()
    
    config = APIClientConfig(
        authentication=APIAuthContext(
            key=os.getenv('LNM_KEY'),
            secret=os.getenv('LNM_SECRET'),
            passphrase=os.getenv('LNM_PASSPHRASE'),
        ),
        network="mainnet",
        timeout=30.0
    )

    try:
        async with LNMClient(config) as client:
            # 1. Obtener Balance Actual
            account = await client.account.get_account()
            balance = account.balance
            
            # 2. Leer las últimas líneas relevantes del log
            log_path = os.path.join(BASE_DIR, 'logs/trading.log')
            relevant_logs = ""
            
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    # Leemos las últimas 50 líneas para buscar actividad reciente
                    lines = f.readlines()[-50:]
                    for line in lines:
                        # Filtramos solo lo importante: órdenes, éxitos, errores y balance
                        if any(x in line for x in ["Ejecutando", "EXITO", "Error", "Balance:", "DECISIÓN"]):
                            relevant_logs += f"• {line.strip()}\n"

            if not relevant_logs:
                relevant_logs = "Sin actividad reciente de trading."

            # 3. Construir mensaje
            mensaje = (
                f"🏦 <b>ESTADO DE CUENTA (1H)</b>\n\n"
                f"💰 <b>Balance Actual:</b> {balance} SATS\n"
                f"--------------------------------\n"
                f"📜 <b>Actividad Reciente:</b>\n"
                f"<pre>{relevant_logs[-1500:]}</pre>\n\n" # Limite de caracteres para evitar error 400
                f"🤖 G9-Sentinel Online"
            )
            
            notifier.send_alert(mensaje)
            print("✅ Reporte de logs enviado.")

    except Exception as e:
        print(f"❌ Error en reporte: {e}")

if __name__ == "__main__":
    asyncio.run(send_log_report())
