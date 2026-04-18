from core.context_manager import get_full_context, save_trade_result
import os
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
        """Ajusta el precio al tick de 0.5 de LNMarkets."""
        try:
            return round(float(val) * 2) / 2
        except:
            return None

    async def get_market_signals(self, client):
        """Cálculo de Alpha Técnico (V18 - Final)."""
        try:
            # SDK V3 requiere un diccionario para los parámetros
            response = await client.futures.get_candles({"limit": 50})
            
            # Extraemos la lista de la respuesta paginada de Pydantic
            candles_list = getattr(response, 'data', response)
            
            df = pd.DataFrame([{
                'high': float(c.high), 'low': float(c.low), 'close': float(c.close)
            } for c in candles_list])
            
            # IMPORTANTE QUANT: LNMarkets devuelve la vela más reciente primero (descendente).
            # Pandas-TA necesita que la más antigua esté primero (ascendente) para el RSI/ATR.
            df = df.iloc[::-1].reset_index(drop=True)
            
            df['rsi'] = ta.rsi(df['close'], length=14)
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
            atr_df = ta.atr(df['high'], df['low'], df['close'], length=14)
            bb_df = ta.bbands(df['close'], length=20, std=2)

            current_rsi = round(df['rsi'].iloc[-1], 2)
            current_adx = round(adx_df['ADX_14'].iloc[-1], 2) if adx_df is not None else 0
            current_atr = round(atr_df.iloc[-1], 2) if atr_df is not None else 0
            
            bb_width = 0
            bb_upper = 0
            bb_lower = 0
            if bb_df is not None and not bb_df.empty:
                try:
                    # Extracción dinámica blindada contra cambios de versión de pandas_ta
                    upper_col = [c for c in bb_df.columns if 'BBU' in c][0]
                    lower_col = [c for c in bb_df.columns if 'BBL' in c][0]
                    bb_upper = round(bb_df[upper_col].iloc[-1], 2)
                    bb_lower = round(bb_df[lower_col].iloc[-1], 2)
                    bb_width = round(bb_upper - bb_lower, 2)
                except IndexError:
                    bb_width = 0

            return {
                "rsi": current_rsi,
                "adx": current_adx,
                "atr": current_atr,
                "bb_width": bb_width, "bb_upper": bb_upper, "bb_lower": bb_lower,
                "regimen": "TENDENCIA" if current_adx > 25 else "RANGO",
                "trend": "SOBRECOMPRA" if current_rsi > 70 else ("SOBREVENTA" if current_rsi < 30 else "NEUTRAL")
            }
        except Exception as e:
            print(f"⚠️ Error en señales: {e}")
            return {"rsi": 50, "adx": 0, "atr": 0, "bb_width": 0, "regimen": "DESCONOCIDO", "trend": "NEUTRAL"}

    async def audit_position(self, client, pos, signals, price):
        """IA decidere sobre posiciones abiertas (Trailing Stop / Close)."""
        print(f"🧠 [IA AUDIT] Analizando {pos.side} ID: {pos.id[:8]}")
        prompt = f"""
        SISTEMA DE GESTIÓN G9 V18 (PRO-GUARD)
        Posición: {pos.side} | Entrada: ${pos.price} | PnL: {pos.pl} SATS
        Mercado: BTC ${price} | RSI: {signals['rsi']} ({signals['trend']})

        REGLA DE DEFENSA ESTRICTA: Si el PnL es mayor a 500 SATS, es OBLIGATORIO asegurar la operación dictando un "new_stop_loss" ligeramente a favor del precio de entrada (${pos.price}) para garantizar un Breakeven. ¡Cero tolerancia a devolver ganancias al mercado!
        
        Tarea: Decide si UPDATE_SL, CLOSE_POSITION o HOLD_POSITION.
        Responde SOLO JSON: {{"action": "...", "new_stop_loss": 0, "logic": "...", "confidence": 0}}
        """
        try:
            # --- G9-V18 Context Injection ---
            # Obtenemos contexto (balance se pasa como argumento en seek_entries o se asume 0 en audit)
            ctx_data = get_full_context({'total_balance': 0})
            prompt = f"{prompt}\n\nCONTEXTO ACTUAL:\n{ctx_data}"
            print(f"[BRAIN] Inyectando memoria de estado en el prompt...", flush=True)
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
                save_trade_result('CLOSE', 0, 'Cierre ejecutado por auditoría de IA')
                print(f"[MEMORY] Resultado de cierre almacenado.", flush=True)
                self.notifier.send_alert(f"🚨 IA cerró posición: {pos.pl} SATS")
        except Exception as e:
            print(f"❌ Fallo en auditoría IA: {e}")

    async def seek_entries(self, client, balance, signals, price):
        """Modo Francotirador: Solo cada 15 minutos."""
        if balance < 2000: return

        # --- BLOQUE V17.2: ALPHA-PREDATOR & RECOVERY MODE ---
        if not hasattr(self, 'initial_balance_today'):
            self.initial_balance_today = balance
        
        profit_needed = self.initial_balance_today * 0.35
        current_profit = balance - self.initial_balance_today
        progress_pct = (current_profit / profit_needed) * 100 if profit_needed > 0 else 0
        
        drawdown = (self.initial_balance_today - balance) / self.initial_balance_today if self.initial_balance_today > 0 else 0
        recovery_active = drawdown > 0.15
        
        num_positions = len(getattr(self, 'positions', getattr(self, 'trades', getattr(self, 'active_trades', []))))
        at_limit = num_positions >= 20

        if recovery_active:
            print(f"⚠️ [CLOUD ALERT] RECOVERY MODE ACTIVO: Drawdown {drawdown*100:.2f}%")
        if at_limit:
            print(f"🚫 [CLOUD ALERT] LÍMITE ALCANZADO: {num_positions}/20 posiciones.")
        # ----------------------------------------------------

        print("🔭 [IA STRAT] Buscando nuevas entradas...")
        memoria = self.brain.get_context_for_gemini(limit=5)

        prompt = f"""
            SISTEMA G9-SENTINEL V17.2: ALPHA-PREDATOR
            -----------------------------------------------------------
            ESTADO: {'🚨 MODO RECUPERACIÓN (Alta Precisión)' if recovery_active else '✅ OPERACIÓN ALPHA'}
            POSICIONES ACTIVAS: {num_positions}/20
            PROGRESO DIARIO: {progress_pct:.2f}% (Meta: +35%)
            
            SNAPSHOT TÉCNICO:
            - Precio BTC: ${price}
            - RSI: {signals.get('rsi', 'N/A')}
            
            PROTOCOLO DE EJECUCIÓN:
            1. {'ESTRATEGIA RECOVERY: Detén pérdidas. Scalping seguro para recuperar drawdown.' if recovery_active else 'ESTRATEGIA ALPHA: Entra agresivo si RSI está en 45-55.'}
            2. Riesgo fijado al 60%. Error de stop-loss inaceptable.
            3. {'LÍMITE DE POSICIONES ALCANZADO. Tu única acción permitida es HOLD.' if at_limit else 'Capacidad operativa disponible.'}
            
            INSTRUCCIONES JSON:
            {{
                "action": "{'HOLD' if at_limit else 'BUY, SELL o HOLD'}",
                "margin": {int(balance * 0.60)},
                "leverage": 20,
                "stop_loss": float,
                "take_profit": float,
                "confidence": 1-100,
                "logic": "Análisis táctico justificado"
            }}
            """
        try:
            # --- G9-V18 Context Injection ---
            # Obtenemos contexto (balance se pasa como argumento en seek_entries o se asume 0 en audit)
            ctx_data = get_full_context({'total_balance': 0})
            prompt = f"{prompt}\n\nCONTEXTO ACTUAL:\n{ctx_data}"
            print(f"[BRAIN] Inyectando memoria de estado en el prompt...", flush=True)
            resp = self.client_gemini.models.generate_content(model=self.model_name, contents=prompt)
            data = json.loads(resp.text.replace('```json', '').replace('```', '').strip())

            confidence = data.get("confidence", 0)
            if data.get("action") in ["BUY", "SELL"] and confidence > 65:
                
                # --- FAIL-SAFE V17.2 ---
                if at_limit and data.get("action") in ["BUY", "SELL"]:
                    print("🛑 [ENGINE] Override automático: Límite 20 alcanzado. Forzando HOLD.")
                    data["action"] = "HOLD"
                # -----------------------
                mrg = min(data.get("margin", 1000), int(balance * 0.60))
                lev = min(data.get("leverage", 5), 25)
                order = FuturesOrder(
                    type='market', side=data['action'].lower(), margin=mrg, leverage=lev,
                    stoploss=self.round_to_tick(data.get('stop_loss')),
                    takeprofit=self.round_to_tick(data.get('take_profit'))
                )
                await client.futures.isolated.new_trade(order)
                self.notifier.send_alert(f"🚀 Sniper {data['action']} ejecutado a ${price} | Lógica V18")
                print(f"✅ Trade {data['action']} enviado a LNM.")
            elif data.get("action") in ["BUY", "SELL"]:
                print(f"🛡️ Filtro de Confianza: IA sugirió {data.get('action')} con {confidence}% (Requiere > 65). Abortando. Lógica: {data.get('logic', '')}")
            else:
                print(f"⏳ IA decidió HOLD. Lógica: {data.get('logic', 'Sin lógica provista')}")
        except Exception as e:
            print(f"❌ Fallo en búsqueda de entradas: {e}")

    async def run_trading_cycle(self):
        print(f"⚡ G9-SENTINEL V18: MOTOR ALPHA ACTIVO (DATOS SINCRONIZADOS)")
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

                    print(f"\n[HEARTBEAT] {now.strftime('%H:%M:%S')} | BTC: ${current_price} | RSI: {signals['rsi']} | ATR: {signals['atr']} | Abiertas: {len(trades)}")

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
