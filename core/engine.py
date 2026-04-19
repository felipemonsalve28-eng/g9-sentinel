import os
import re
import json
import asyncio
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from google import genai
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient
from core.brain import G9Brain
from core.notifier import G9Notifier

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
        """Extrae y procesa datos técnicos para un intervalo específico."""
        res = await client.futures.get_candles({"limit": limit})
        candles = getattr(res, 'data', res)
        df = pd.DataFrame([{'close': float(c.close), 'high': float(c.high), 'low': float(c.low)} for c in candles])
        df = df.iloc[::-1].reset_index(drop=True)
        
        # Cálculos Alpha
        df['rsi'] = ta.rsi(df['close'], length=14)
        bb = ta.bbands(df['close'], length=20, std=2)
        
        return {
            "price": df['close'].iloc[-1],
            "rsi": round(df['rsi'].iloc[-1], 2),
            "bb_u": round(bb.iloc[-1, 0], 2),
            "bb_l": round(bb.iloc[-1, 2], 2),
            "trend": "UP" if df['close'].iloc[-1] > df['close'].mean() else "DOWN"
        }

    async def get_full_market_snapshot(self, client):
        """Genera el paquete completo de datos multi-temporalidad."""
        return {
            "m1": await self.fetch_timeframe_data(client, 1),
            "m5": await self.fetch_timeframe_data(client, 5),
            "h1": await self.fetch_timeframe_data(client, 60),
            "h4": await self.fetch_timeframe_data(client, 240)
        }

    async def run_trading_cycle(self):
        print(f"🚀 G9-SENTINEL V25.5: FULL DATA MODE ACTIVE")
        async with LNMClient(self.config_lnm) as lnm:
            while True:
                try:
                    # 1. Datos de Cuenta y Mercado
                    acc = await lnm.account.get_account()
                    positions = await lnm.futures.isolated.get_running_trades()
                    market_data = await self.get_full_market_snapshot(lnm)
                    
                    # 2. Preparar el paquete para la IA
                    account_snapshot = {
                        "balance": acc.balance,
                        "open_positions": [p.__dict__ for p in positions],
                        "timestamp": datetime.now().isoformat()
                    }

                    # 3. Lógica de Auditoría o Estrategia (Actualizada)
                    ai_decision = None
                    if positions:
                        # Modo Defensa/Gestión
                        ai_decision = await self.execute_ai_action("audit", account_snapshot, market_data, lnm)
                        if ai_decision:
                            await self.process_audit_decision(ai_decision, positions[0], lnm)
                    else:
                        # Modo Ataque/Estrategia
                        ai_decision = await self.execute_ai_action("strategy", account_snapshot, market_data, lnm)
                        if ai_decision:
                            await self.process_strategy_decision(ai_decision, acc.balance, lnm)

                    # 4. Guardar en memoria (Para el Dashboard y el Contexto Histórico)
                    if ai_decision:
                        action = ai_decision.get("action", "HOLD")
                        logic = ai_decision.get("logic", "Sin lógica provista.")
                        conf = ai_decision.get("confidence", 0)
                        current_price = market_data['m1']['price']
                        
                        self.brain.save_decision(
                            market_price=current_price, 
                            action=action, 
                            confidence=conf, 
                            logic_applied=logic, 
                            indicators=market_data, 
                            balance=acc.balance
                        )
                        print(f"🧠 Memoria G9: Acción [{action}] guardada. Lógica: {logic}")

                    await asyncio.sleep(60) # Ciclo rápido de 1 min
                except Exception as e:
                    print(f"❌ Error en el ciclo de trading: {e}")
                    await asyncio.sleep(10)

    async def execute_ai_action(self, p_type, account, market, client):
        """Ejecuta una acción de IA asegurando un procesamiento 100% a prueba de fallos."""
        path = f'/home/felipemonsalve28/g9_production/config/prompts/{p_type}.txt'
        
        # Validar existencia del prompt
        try:
            with open(path, 'r') as f:
                template = f.read()
        except FileNotFoundError:
            print(f"❌ Error crítico: No se encontró el prompt '{p_type}' en {path}")
            return None

        # Inyección masiva de datos al prompt
        prompt = template.format(
            account=json.dumps(account, indent=2),
            market=json.dumps(market, indent=2),
            memoria=self.brain.get_context_for_gemini(limit=5)
        )

        try:
            # 1. Llamada a la IA
            resp = self.client_gemini.models.generate_content(model=self.model_name, contents=prompt)
            raw_text = resp.text

            # 2. Limpieza y Extracción (Busca solo lo que está entre llaves)
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if not match:
                raise ValueError("No se encontró ninguna estructura JSON en la respuesta de la IA.")
            
            clean_json_str = match.group(0)

            # 3. Parseo Seguro
            ai_decision = json.loads(clean_json_str)

            # 4. Validación Estructural Básica
            if not isinstance(ai_decision, dict):
                raise TypeError("El JSON decodificado no es un diccionario válido.")

            return ai_decision

        except json.JSONDecodeError as e:
            print(f"⚠️ Error de formato JSON: {e}")
            print(f"Texto crudo devuelto por IA: {raw_text}")
        except (ValueError, TypeError, KeyError) as e:
            print(f"⚠️ Error de validación estructural: {e}")
        except Exception as e:
            print(f"🚨 Error inesperado comunicándose con Gemini: {e}")
        
        # Fallo seguro: permite que el bot intente de nuevo en el próximo ciclo
        return None

    # --- NUEVAS FUNCIONES DE EJECUCIÓN ---

    async def process_audit_decision(self, decision, current_position, client):
        """Ejecuta las decisiones de protección de capital (audit.txt)"""
        action = decision.get("action")
        pos_id = getattr(current_position, 'id', None)

        if not pos_id:
            return

        if action == "UPDATE_SL":
            # Extraemos el nuevo SL (soporta variables llamadas new_stop_loss o stop_loss)
            new_sl = decision.get("new_stop_loss") or decision.get("stop_loss")
            if new_sl:
                print(f"🛡️ ACTUALIZANDO STOP LOSS DINÁMICO a: ${new_sl}")
                try:
                    await client.futures.isolated.update_position({"id": pos_id, "stoploss": float(new_sl)})
                    print("✅ TRAILING STOP ACTUALIZADO CON ÉXITO.")
                except Exception as e:
                    print(f"❌ Error al actualizar SL: {e}")
                    
        elif action == "CLOSE_POSITION":
            print("🚨 ORDEN DE CIERRE RECIBIDA. Asegurando posición...")
            try:
                await client.futures.isolated.close(id=pos_id)
                print("✅ POSICIÓN CERRADA CON ÉXITO.")
            except Exception as e:
                print(f"❌ Error al cerrar posición: {e}")
                
        else: # Asume HOLD_POSITION por defecto
            print(f"🛡️ AUDITORÍA [HOLD]: Manteniendo parámetros. Lógica: {decision.get('logic')}")

    async def process_strategy_decision(self, decision, balance, client):
        """Ejecuta las decisiones de entrada al mercado (strategy.txt)"""
        action = decision.get("action")
        
        if action in ["BUY", "SELL"]:
            margin = decision.get("margin", 0)
            leverage = decision.get("leverage", 10)
            sl = decision.get("stop_loss")
            tp = decision.get("take_profit")
            
            # Control de riesgo maestro (Máximo 35% del balance real)
            max_margin = int(balance * 0.35)
            if margin > max_margin:
                margin = max_margin
                
            print(f"🔨 EJECUTANDO {action} | Margen: {margin} Sats | Apalan: {leverage}x | SL: {sl} | TP: {tp}")
            try:
                # Construimos el diccionario base limpio
                params = {
                    "type": "market",
                    "side": "b" if action == "BUY" else "s",
                    "margin": int(margin),
                    "leverage": float(leverage)
                }
                
                # Solo inyectamos SL y TP si realmente existen
                if sl and float(sl) > 0:
                    params["stoploss"] = float(sl)
                if tp and float(tp) > 0:
                    params["takeprofit"] = float(tp)

                # Disparamos la orden
                await client.futures.isolated.new_trade(params)
                print("✅ ORDEN EJECUTADA CON ÉXITO")
            except Exception as e:
                print(f"❌ Error al ejecutar Orden: {e}")
        else:
            print(f"⏳ STRAT [HOLD]: Buscando setup. Lógica: {decision.get('logic')}")
