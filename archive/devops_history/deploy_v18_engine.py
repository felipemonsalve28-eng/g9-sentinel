import os
import shutil

BASE_DIR = "/home/felipemonsalve28/g9_production"
ENGINE_PATH = os.path.join(BASE_DIR, "core/engine.py")

# El código fuente completo y blindado de la V18 (Alpha Logic + Pro Guard)
engine_v18_code = """import os
import json
import asyncio
import warnings
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient
from lnmarkets_sdk.v3.models.futures_isolated import FuturesOrder
import lnmarkets_sdk.v3.models.futures_isolated as iso_models
import pandas as pd
import pandas_ta as ta

# Importaciones internas
from core.brain import G9Brain
from core.notifier import G9Notifier

warnings.filterwarnings('ignore')
load_dotenv('/home/felipemonsalve28/g9_production/.env')

class G9SentinelEngine:
    def __init__(self):
        self.brain = G9Brain()
        self.notifier = G9Notifier()
        self.model_name = "gemini-2.5-flash"
        self.client_gemini = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.config_lnm = APIClientConfig(
            authentication=APIAuthContext(
                key=os.getenv('LNM_KEY'),
                secret=os.getenv('LNM_SECRET'),
                passphrase=os.getenv('LNM_PASSPHRASE')
            ),
            network="mainnet",
            timeout=60.0
        )
        self.last_strategic_run = datetime.min
        self.fast_cycle_minutes = 5
        self.strategic_cycle_minutes = 15

    def round_to_tick(self, val):
        \"\"\"Ajusta el precio al tick de 0.5 de LNMarkets.\"\"\"
        try:
            return round(float(val) * 2) / 2
        except:
            return None

    async def get_market_signals(self, client):
        \"\"\"Cálculo de Alpha Técnico (V18).\"\"\"
        try:
            candles = await client.futures.get_candles(limit=50)
            df = pd.DataFrame([{
                'high': float(c.high), 'low': float(c.low), 'close': float(c.close)
            } for c in candles])
            
            df['rsi'] = ta.rsi(df['close'], length=14)
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
            atr_df = ta.atr(df['high'], df['low'], df['close'], length=14)
            bb_df = ta.bbands(df['close'], length=20, std=2)

            current_rsi = round(df['rsi'].iloc[-1], 2)
            current_adx = round(adx_df['ADX_14'].iloc[-1], 2) if adx_df is not None else 0
            current_atr = round(atr_df.iloc[-1], 2) if atr_df is not None else 0
            
            bb_width = 0
            if bb_df is not None:
                bb_width = round(bb_df['BBU_20_2.0'].iloc[-1] - bb_df['BBL_20_2.0'].iloc[-1], 2)

            return {
                "rsi": current_rsi,
                "adx": current_adx,
                "atr": current_atr,
                "bb_width": bb_width,
                "regimen": "TENDENCIA" if current_adx > 25 else "RANGO",
                "trend": "SOBRECOMPRA" if current_rsi > 70 else ("SOBREVENTA" if current_rsi < 30 else "NEUTRAL")
            }
        except Exception as e:
            print(f"⚠️ Error en señales: {e}")
            return {"rsi": 50, "adx": 0, "atr": 0, "bb_width": 0, "regimen": "DESCONOCIDO", "trend": "NEUTRAL"}

    async def audit_position(self, client, pos, signals, price):
        \"\"\"IA decidere sobre posiciones abiertas (Trailing Stop / Close).\"\"\"
        print(f"🧠 [IA AUDIT] Analizando {pos.side} ID: {pos.id[:8]}")
        prompt = f\"\"\"
        SISTEMA DE GESTIÓN G9 V18 (PRO-GUARD)
        Posición: {pos.side} | Entrada: ${pos.price} | PnL: {pos.pl} SATS
        Mercado: BTC ${price} | RSI: {signals['rsi']} ({signals['trend']})

        REGLA DE DEFENSA ESTRICTA: Si el PnL es mayor a 500 SATS, es OBLIGATORIO asegurar la operación dictando un "new_stop_loss" ligeramente a favor del precio de entrada (${pos.price}) para garantizar un Breakeven. ¡Cero tolerancia a devolver ganancias al mercado!
        
        Tarea: Decide si UPDATE_SL, CLOSE_POSITION o HOLD_POSITION.
        Responde SOLO JSON: {{"action": "...", "new_stop_loss": 0, "logic": "...", "confidence": 0}}
        \"\"\"
        try:
            resp = self.client_gemini.models.generate_content(model=self.model_name, contents=prompt)
            data = json.loads(resp.text.replace('```json', '').replace('```', '').strip())

            if data.get("action") == "UPDATE_SL" and data.get("new_stop_loss") > 0:
                n_sl = self.round_to_tick(data.get("new_stop_loss"))
                MClass = next(getattr(iso_models, n) for n in dir(iso_models) if 'Stoploss' in n and 'Response' not in n)
                await client.futures.isolated.update_stoploss(MClass(id=pos.id, value=n_sl))
                self.notifier.send_alert(f"🛡️ SL Dinámico: ${n_sl}")

            elif data.get("action") == "CLOSE_POSITION":
                MClass = next(getattr(iso_models, n) for n in dir(iso_models) if 'Close' in n and 'All' not in n and 'Response' not in n)
                await client.futures.isolated.close(MClass(id=pos.id))
                self.notifier.send_alert(f"🚨 IA cerró posición: {pos.pl} SATS")
        except Exception as e:
            print(f"❌ Fallo en auditoría IA: {e}")

    async def seek_entries(self, client, balance, signals, price):
        \"\"\"Modo Francotirador: Solo cada 15 minutos.\"\"\"
        if balance < 2000: return
        print("🔭 [IA STRAT] Buscando nuevas entradas...")
        memoria = self.brain.get_context_for_gemini(limit=5)

        prompt = f\"\"\"
        SISTEMA SNIPER G9 V18 (ALPHA SEEKER)
        Contexto: {memoria}
        Balance: {balance} | RSI: {signals['rsi']} | ADX: {signals['adx']} | ATR: {signals['atr']} | BB Width: {signals['bb_width']}
        
        REGLA DE RENTABILIDAD ESTRICTA: El ATR actual ({signals['atr']}) y la amplitud de bandas ({signals['bb_width']}) representan la volatilidad. Si la volatilidad es muy baja, los movimientos no cubrirán las comisiones del broker. Responde "HOLD" si el Alpha de volatilidad es pobre.
        
        ¿BUY/SELL/HOLD? JSON: {{"action": "...", "margin": 0, "leverage": 0, "stop_loss": 0, "take_profit": 0, "logic": "..."}}
        \"\"\"
        try:
            resp = self.client_gemini.models.generate_content(model=self.model_name, contents=prompt)
            data = json.loads(resp.text.replace('```json', '').replace('```', '').strip())

            if data.get("action") in ["BUY", "SELL"]:
                mrg = min(data.get("margin", 1000), int(balance * 0.15))
                lev = min(data.get("leverage", 5), 25)
                order = FuturesOrder(
                    type='market', side=data['action'].lower(), margin=mrg, leverage=lev,
                    stoploss=self.round_to_tick(data.get('stop_loss')),
                    takeprofit=self.round_to_tick(data.get('take_profit'))
                )
                await client.futures.isolated.new_trade(order)
                self.notifier.send_alert(f"🚀 Sniper {data['action']} ejecutado a ${price} | Lógica V18")
        except Exception as e:
            print(f"❌ Fallo en búsqueda de entradas: {e}")

    async def run_trading_cycle(self):
        print(f"⚡ G9-SENTINEL V18: MOTOR ALPHA ACTIVO")
        while True:
            try:
                async with LNMClient(self.config_lnm) as lnm:
                    account = await lnm.account.get_account()
                    ticker = await lnm.futures.get_ticker()
                    current_price = float(ticker.last_price)
                    signals = await self.get_market_signals(lnm)
                    trades = await lnm.futures.isolated.get_running_trades()

                    now = datetime.now()
                    is_strategic = (now - self.last_strategic_run) >= timedelta(minutes=self.strategic_cycle_minutes)

                    print(f"\\n[HEARTBEAT] {now.strftime('%H:%M:%S')} | BTC: ${current_price} | Abiertas: {len(trades)}")

                    # 1. Gestión de Riesgo (Fast: 5m o Emergencia)
                    for pos in trades:
                        if is_strategic or abs(pos.pl) > 3000:
                            await self.audit_position(lnm, pos, signals, current_price)

                    # 2. Entrada Estratégica (Strategic: 15m)
                    if is_strategic:
                        if len(trades) < 3:
                            await self.seek_entries(lnm, account.balance, signals, current_price)
                        self.last_strategic_run = now
                        print(f"💾 Ciclo estratégico concluido. Siguiente: {(now + timedelta(minutes=15)).strftime('%H:%M')}")

                await asyncio.sleep(self.fast_cycle_minutes * 60)
            except Exception as e:
                print(f"❌ Error en el orquestador: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    engine = G9SentinelEngine()
    asyncio.run(engine.run_trading_cycle())
"""

def deploy():
    print("🚀 Iniciando Despliegue Directo de Motor V18...")
    
    # Escribir el nuevo archivo de manera limpia
    with open(ENGINE_PATH, "w", encoding="utf-8") as f:
        f.write(engine_v18_code)
        
    print(f"✅ ¡Despliegue exitoso! El archivo {ENGINE_PATH} ha sido actualizado a la V18.")
    print("🛡️ Los nuevos filtros de Volatilidad (ATR/BB) y el Pro-Guard (Breakeven > 500 SATS) están instalados.")

if __name__ == "__main__":
    deploy()
