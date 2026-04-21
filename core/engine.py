import os
import re
import json
import asyncio
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta, timezone
from google import genai
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient
from core.brain import G9Brain
from core.notifier import G9Notifier

# Modelos del SDK
from lnmarkets_sdk.v3.models.futures_data import GetCandlesParams
from lnmarkets_sdk.v3.models.futures_isolated import UpdateStoplossParams

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
            network="mainnet"
        )

    async def fetch_timeframe_data(self, client, interval_mins, limit=50):
        """Extrae datos técnicos cumpliendo con el requisito 'from_' del SDK v3."""
        range_map = {1: "1m", 5: "5m", 60: "1h", 240: "4h"}
        tf_range = range_map.get(interval_mins, "1m")
        start_time = (datetime.now(timezone.utc) - timedelta(minutes=interval_mins * limit * 2))
        from_timestamp = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        try:
            params = GetCandlesParams(limit=limit, range=tf_range, from_=from_timestamp)
            res = await client.futures.get_candles(params)
            candles = getattr(res, 'data', res)
            
            if not candles or len(candles) < 14:
                return None

            df = pd.DataFrame([{'close': float(c.close), 'high': float(c.high), 'low': float(c.low)} for c in candles])
            df = df.iloc[::-1].reset_index(drop=True)
            
            df['rsi'] = ta.rsi(df['close'], length=14)
            bb = ta.bbands(df['close'], length=20, std=2)
            bbl_col = [c for c in bb.columns if 'BBL' in c][0]
            bbu_col = [c for c in bb.columns if 'BBU' in c][0]
            
            return {
                "price": float(df['close'].iloc[-1]),
                "rsi": round(float(df['rsi'].iloc[-1]), 2),
                "bb_u": round(float(bb[bbu_col].iloc[-1]), 2),
                "bb_l": round(float(bb[bbl_col].iloc[-1]), 2),
                "trend": "UP" if df['close'].iloc[-1] > df['close'].rolling(20).mean().iloc[-1] else "DOWN"
            }
        except Exception as e:
            print(f"⚠️ Error en velas {tf_range}: {e}")
            return None

    async def get_full_market_snapshot(self, client):
        return {
            "m1": await self.fetch_timeframe_data(client, 1),
            "m5": await self.fetch_timeframe_data(client, 5),
            "h1": await self.fetch_timeframe_data(client, 60),
            "h4": await self.fetch_timeframe_data(client, 240)
        }

    async def run_trading_cycle(self):
        print(f"🚀 G9-SENTINEL V25.5: FULL ASYNC MODE ACTIVE")
        async with LNMClient(self.config_lnm) as lnm:
            while True:
                try:
                    acc = await lnm.account.get_account()
                    raw_positions = await lnm.futures.isolated.get_running_trades()
                    market_data = await self.get_full_market_snapshot(lnm)
                    
                    formatted_positions = []
                    for p in raw_positions:
                        formatted_positions.append({
                            "id": str(p.id),
                            "side": p.side,
                            "entry_price": float(p.price), 
                            "pnl": float(p.pl),            
                            "stoploss": float(p.stoploss) if p.stoploss else None,
                            "margin": int(p.margin),
                            "leverage": int(p.leverage)
                        })

                    account_snapshot = {
                        "balance": int(acc.balance),
                        "open_positions": formatted_positions,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    # 1. HILO DEL AUDITOR: Gestiona posiciones activas
                    if formatted_positions:
                        for pos in formatted_positions:
                            # Pasamos solo la posición que se está evaluando para mayor precisión
                            audit_snapshot = account_snapshot.copy()
                            audit_snapshot["open_positions"] = [pos]
                            
                            audit_decision = await self.execute_ai_action("audit", audit_snapshot, market_data, lnm)
                            if audit_decision:
                                await self.process_audit_decision(audit_decision, pos['id'], lnm)
                                
                                # Guardar memoria del Auditor
                                self.brain.save_decision(
                                    market_price=market_data['m1']['price'],
                                    action=audit_decision.get("action", "HOLD"),
                                    confidence=audit_decision.get("confidence", 0),
                                    logic_applied=audit_decision.get("logic", "N/A"),
                                    indicators=market_data,
                                    balance=acc.balance,
                                    pnl=pos['pnl'],
                                    margin=pos['margin']
                                )
                                print(f"🧠 Memoria G9 (Audit): Registro guardado (PnL: {pos['pnl']} sats).")

                    # 2. HILO DEL ESTRATEGA: Busca nuevas entradas (Máximo 3 simultáneas)
                    if len(formatted_positions) < 3:
                        strategy_decision = await self.execute_ai_action("strategy", account_snapshot, market_data, lnm)
                        if strategy_decision and strategy_decision.get("action") in ["BUY", "SELL"]:
                            await self.process_strategy_decision(strategy_decision, acc.balance, lnm)
                            
                            # Guardar memoria del Estratega
                            self.brain.save_decision(
                                market_price=market_data['m1']['price'],
                                action=strategy_decision.get("action", "HOLD"),
                                confidence=strategy_decision.get("confidence", 0),
                                logic_applied=strategy_decision.get("logic", "N/A"),
                                indicators=market_data,
                                balance=acc.balance,
                                pnl=0,
                                margin=strategy_decision.get("margin", 0)
                            )
                            print(f"🧠 Memoria G9 (Strategy): Nueva entrada registrada en DB.")

                    await asyncio.sleep(60)
                except Exception as e:
                    print(f"❌ Error en el ciclo: {e}")
                    await asyncio.sleep(10)

    async def execute_ai_action(self, p_type, account, market, client):
        path = f'/home/felipemonsalve28/g9_production/config/prompts/{p_type}.txt'
        try:
            with open(path, 'r') as f:
                template = f.read()
            prompt = template.format(
                account=json.dumps(account, indent=2),
                market=json.dumps(market, indent=2),
                memoria=self.brain.get_context_for_gemini(limit=5)
            )
            print(f"\n[DEBUG] EJECUTANDO PROMPT: {p_type.upper()}")
            resp = self.client_gemini.models.generate_content(model=self.model_name, contents=prompt)
            match = re.search(r'\{.*\}', resp.text, re.DOTALL)
            return json.loads(match.group(0)) if match else None
        except Exception as e:
            print(f"🚨 Error IA ({p_type}): {e}")
            return None

    async def process_audit_decision(self, decision, pos_id, client):
        action = decision.get("action")
        if action == "UPDATE_SL":
            val = decision.get("new_stop_loss") or decision.get("stop_loss")
            if val:
                try:
                    clean_val = int(float(val))
                    params = UpdateStoplossParams(id=pos_id, value=clean_val)
                    await client.futures.isolated.update_stoploss(params)
                    print(f"✅ SL ACTUALIZADO a {clean_val}")
                except Exception as e:
                    print(f"❌ Error al actualizar SL: {e}")
        elif action == "CLOSE_POSITION":
            try:
                await client.futures.isolated.close(id=pos_id)
                print(f"✅ POSICIÓN CERRADA.")
            except Exception as e:
                print(f"❌ Error al cerrar: {e}")

    async def process_strategy_decision(self, decision, balance, client):
        action = decision.get("action")
        if action in ["BUY", "SELL"]:
            try:
                margin = int(float(decision.get("margin", 1000)))
                leverage = int(float(decision.get("leverage", 10)))
                max_margin = int(balance * 0.35)
                if margin > max_margin: margin = max_margin
                
                params = {
                    "type": "market",
                    "side": "buy" if action == "BUY" else "sell",
                    "margin": margin,
                    "leverage": leverage
                }
                if decision.get("stop_loss"): params["stoploss"] = int(float(decision["stop_loss"]))
                if decision.get("take_profit"): params["takeprofit"] = int(float(decision["take_profit"]))
                
                print(f"🔨 DISPARANDO {action}...")
                await client.futures.isolated.new_trade(params)
                print(f"✅ ORDEN EJECUTADA.")
            except Exception as e:
                print(f"❌ Error en orden: {e}")
