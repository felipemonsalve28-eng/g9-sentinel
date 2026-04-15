import time
import os
import json
import asyncio
import warnings
import inspect
from dotenv import load_dotenv
from google import genai
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient
from lnmarkets_sdk.v3.models.futures_isolated import FuturesOrder
import lnmarkets_sdk.v3.models.futures_isolated as iso_models
import pandas as pd
import pandas_ta as ta
from core.brain import G9Brain
from core.notifier import G9Notifier

warnings.filterwarnings('ignore')
load_dotenv('/home/felipemonsalve28/g9_production/.env')
client_gemini = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def round_to_tick(val):
    return round(float(val) * 2) / 2 if val else None

async def get_market_signals(client):
    try:
        candles = await client.futures.get_candles(limit=50)
        df = pd.DataFrame([{
            'high': float(c.high), 'low': float(c.low), 'close': float(c.close)
        } for c in candles])
        
        df['rsi'] = ta.rsi(df['close'], length=14)
        bb = ta.bbands(df['close'], length=20, std=2)
        adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
        df['adx'] = adx_df['ADX_14'] if adx_df is not None else 0

        current_rsi = round(df['rsi'].iloc[-1], 2)
        current_adx = round(df['adx'].iloc[-1], 2)
        upper_band = bb['BBU_20_2.0'].iloc[-1]
        lower_band = bb['BBL_20_2.0'].iloc[-1]
        
        regimen = "TENDENCIA FUERTE" if current_adx > 25 else "RANGO/LATERAL"
        trend = "SOBRECOMPRA" if current_rsi > 70 else ("SOBREVENTA" if current_rsi < 30 else "NEUTRAL")

        return {
            "rsi": current_rsi,
            "trend": trend,
            "adx": current_adx,
            "regimen": regimen,
            "bb_upper": round(upper_band, 2),
            "bb_lower": round(lower_band, 2)
        }
    except Exception as e:
        return {"rsi": 50, "trend": "NEUTRAL", "adx": 0, "regimen": "DESCONOCIDO", "bb_upper": 0, "bb_lower": 0}

async def run_trading_cycle():
    print("⚡ G9-SENTINEL V14.6: MOTOR DE PORTAFOLIO ACTIVO")
    brain = G9Brain()
    notifier = G9Notifier()
    last_heartbeat = 0
    MODEL_NAME = "gemini-2.5-flash" 
    
    config = APIClientConfig(
        authentication=APIAuthContext(
            key=os.getenv('LNM_KEY'), 
            secret=os.getenv('LNM_SECRET'), 
            passphrase=os.getenv('LNM_PASSPHRASE')
        ),
        network="mainnet", timeout=60.0
    )

    while True:
        try:
            async with LNMClient(config) as client:
                # 1. Datos de Mercado y Cuenta
                account = await client.account.get_account()
                balance = account.balance  
                ticker = await client.futures.get_ticker()
                current_price = float(ticker.last_price)
                signals = await get_market_signals(client)
                trades = await client.futures.isolated.get_running_trades()
                memoria = brain.get_context_for_gemini(limit=10)
                
                print(f"\n📊 Balance: {balance} SATS | BTC: ${current_price} | Abiertas: {len(trades)}")

                # --- HEARTBEAT HORARIO ---
                current_time = time.time()
                if (current_time - last_heartbeat) >= 3600:
                    hb_msg = f"🛰️ <b>Reporte G9</b>\nBalance: {balance} SATS\nPosiciones: {len(trades)}\nBTC: ${current_price}"
                    asyncio.create_task(asyncio.to_thread(notifier.send_alert, hb_msg))
                    last_heartbeat = current_time

                # --- A. GESTIÓN DE CADA POSICIÓN ABIERTA ---
                for pos in trades:
                    print(f"🔍 Analizando {pos.side} (ID: {pos.id[:8]})...")
                    p_prompt = f"""
                    GESTIÓN DE POSICIÓN {pos.id}
                    Dirección: {pos.side} | Entrada: ${pos.price} | Actual: ${current_price} | PnL: {pos.pl} SATS
                    RSI: {signals['rsi']} ({signals['trend']}) | ADX: {signals['adx']} ({signals['regimen']}) | BB: U {signals['bb_upper']} / L {signals['bb_lower']}
                    {memoria}
                    Decide: UPDATE_SL (para asegurar profit), CLOSE_POSITION (si el riesgo es alto) o HOLD_POSITION.
                    Responde SOLO JSON: {{"action": "...", "new_stop_loss": 0, "logic": "...", "confidence": 0}}
                    """
                    
                    resp = client_gemini.models.generate_content(model=MODEL_NAME, contents=p_prompt)
                    data = json.loads(resp.text.replace('```json', '').replace('```', '').strip())
                    
                    if data.get("action") == "UPDATE_SL":
                        n_sl = round_to_tick(data.get("new_stop_loss"))
                        # Filtro $15
                        if pos.side.upper() == 'SELL': n_sl = max(n_sl, current_price + 15)
                        else: n_sl = min(n_sl, current_price - 15)
                        
                        MClass = next(getattr(iso_models, n) for n in dir(iso_models) if 'Stoploss' in n and 'Response' not in n)
                        await client.futures.isolated.update_stoploss(MClass(id=pos.id, value=n_sl))
                        print(f"✅ SL Actualizado ID: {pos.id[:8]}")
                        asyncio.create_task(asyncio.to_thread(notifier.send_alert, f"🛡️ <b>SL Dinámico</b>\nID: {pos.id[:8]}\nNuevo SL: ${n_sl}"))
                    
                    elif data.get("action") == "CLOSE_POSITION":
                        MClass = next(getattr(iso_models, n) for n in dir(iso_models) if 'Close' in n and 'All' not in n and 'Response' not in n)
                        await client.futures.isolated.close(MClass(id=pos.id))
                        print(f"🚨 Posición {pos.id[:8]} cerrada.")
                        asyncio.create_task(asyncio.to_thread(notifier.send_alert, f"🚨 <b>Cierre</b>\nID: {pos.id[:8]}\nPnL: {pos.pl} SATS"))

                # --- B. BÚSQUEDA DE REBALANCEO ---
                print("🧠 Buscando nuevas oportunidades...")
                resumen_pos = [f"{t.side} @ ${t.price}" for t in trades]
                prompt_entry = f"""
                REBALANCEO DE CARTERA
                Balance: {balance} SATS | Actuales: {resumen_pos} | RSI: {signals['rsi']} ({signals['trend']}) | ADX: {signals['adx']} ({signals['regimen']}) | BB: U {signals['bb_upper']} / L {signals['bb_lower']}
                {memoria}
                ¿Abrir nueva posición? Considera diversificar o cubrir (hedge).
                Responde JSON: {{"action": "BUY/SELL/HOLD", "margin": int, "leverage": int, "stop_loss": float, "take_profit": float, "logic": "..."}}
                """
                
                resp_entry = client_gemini.models.generate_content(model=MODEL_NAME, contents=prompt_entry)
                entry_data = json.loads(resp_entry.text.replace('```json', '').replace('```', '').strip())
                
                if entry_data.get("action") in ["BUY", "SELL"] and balance > 2000:
                    mrg = min(entry_data.get("margin", 1000), int(balance * 0.20))
                    order = FuturesOrder(
                        type='market', side=entry_data.get("action").lower(), 
                        margin=mrg, leverage=entry_data.get("leverage", 1),
                        stoploss=round_to_tick(entry_data.get("stop_loss")),
                        takeprofit=round_to_tick(entry_data.get("take_profit"))
                    )
                    await client.futures.isolated.new_trade(order)
                    print(f"🔥 Rebalanceo: {entry_data.get('action')} de {mrg} SATS.")
                    asyncio.create_task(asyncio.to_thread(notifier.send_alert, f"🚀 <b>Rebalanceo</b>\nAcción: {entry_data.get('action')}\nSATS: {mrg}"))

                print("💾 Ciclo completado. Esperando 15 min...")
                await asyncio.sleep(900)

        except Exception as e:
            print(f"❌ Error: {e}. Reintentando en 60s...")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_trading_cycle())
