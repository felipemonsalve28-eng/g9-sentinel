import os
import json
import asyncio
import warnings
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
from google.genai import types
from lnmarkets_sdk.v3.http.client import APIAuthContext, APIClientConfig, LNMClient
from lnmarkets_sdk.v3.models.futures_isolated import FuturesOrder
import lnmarkets_sdk.v3.models.futures_isolated as iso_models
import pandas as pd
import pandas_ta as ta

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
            network='mainnet',
            timeout=60.0
        )
        self.last_strategic_run = datetime.min
        self.fast_cycle_minutes = 1
        self.strategic_cycle_minutes = 5
        self.safe_config = types.GenerateContentConfig(
            safety_settings=[
                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
            ]
        )

    def _load_external_prompt(self, p_type):
        path = f'/home/felipemonsalve28/g9_production/config/prompts/{p_type}.txt'
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    c = f.read().strip()
                    if c: return c
        except: pass
        return None

    def _extract_json(self, text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: return json.loads(match.group(0))
        except: pass
        return None

    def round_to_tick(self, val):
        try: return round(float(val) * 2) / 2
        except: return None

    async def get_market_signals(self, client):
        try:
            response = await client.futures.get_candles({'limit': 100})
            c = getattr(response, 'data', response)
            df = pd.DataFrame([{'close': float(i.close), 'high': float(i.high), 'low': float(i.low)} for i in c])
            df = df.iloc[::-1].reset_index(drop=True)

            df['rsi'] = ta.rsi(df['close'], length=14)
            df['ema_20'] = ta.ema(df['close'], length=20)
            df['ema_50'] = ta.ema(df['close'], length=50)
            bbands = ta.bbands(df['close'], length=20, std=2)
            df = pd.concat([df, bbands], axis=1)

            def get_col(patterns, default_val=0):
                for p in patterns:
                    cols = [c for c in df.columns if p.upper() in c.upper()]
                    if cols:
                        val = df[cols[0]].iloc[-1]
                        return round(float(val), 2) if pd.notnull(val) else default_val
                return default_val

            return {
                'rsi': get_col(['RSI'], 50),
                'ema_20': get_col(['EMA_20', 'EMA20']),
                'ema_50': get_col(['EMA_50', 'EMA50']),
                'bb_u': get_col(['BBU']),
                'bb_l': get_col(['BBL']),
                'candles': df.tail(5)[['close', 'high', 'low']].fillna(0).to_dict('records')
            }
        except Exception as e:
            print(f"❌ Error Crítico Señales: {e}")
            return {'rsi': 50, 'ema_20': 0, 'ema_50': 0, 'bb_u': 0, 'bb_l': 0, 'candles': []}

    async def audit_position(self, client, pos, signals, price, balance):
        print(f"🧠 [IA AUDIT] Analizando {pos.side} ID: {pos.id[:8]}")
        template = self._load_external_prompt('audit')
        if not template: return

        try:
            prompt_data = {
                'side': pos.side, 'entry': pos.price, 'pnl': pos.pl, 'price': price,
                'rsi': signals['rsi'], 'ema20': signals['ema_20'], 'ema50': signals['ema_50'],
                'bb_u': signals['bb_u'], 'bb_l': signals['bb_l'],
                'candles': json.dumps(signals['candles'])
            }
            prompt = template.format(**prompt_data)
            
            resp = self.client_gemini.models.generate_content(model=self.model_name, contents=prompt, config=self.safe_config)
            data = self._extract_json(resp.text)
            
            if data:
                # Guardamos incluyendo el balance actual
                self.brain.save_decision(price, data.get('action'), data.get('confidence', 0), data.get('logic', ''), indicators=signals, balance=int(balance))

                if data.get('action') == 'UPDATE_SL' and data.get('new_stop_loss', 0) > 0:
                    n_sl = self.round_to_tick(data.get('new_stop_loss'))
                    MClass = next(getattr(iso_models, n) for n in dir(iso_models) if 'Stoploss' in n and 'Response' not in n)
                    await client.futures.isolated.update_stoploss(MClass(id=pos.id, value=n_sl))
                    self.notifier.send_alert(f"🛡️ Trailing SL: ${n_sl}")
                elif data.get('action') == 'CLOSE_POSITION':
                    MClass = next(getattr(iso_models, n) for n in dir(iso_models) if 'Close' in n and 'All' not in n and 'Response' not in n)
                    await client.futures.isolated.close(MClass(id=pos.id))
                    self.notifier.send_alert(f"🚨 IA cerró: {pos.pl} SATS")
        except Exception as e:
            print(f"❌ Error Formato Audit: {e}")

    async def seek_entries(self, client, balance, signals, price):
        trades = await client.futures.isolated.get_running_trades()
        if len(trades) >= 3 or balance < 2000: return

        print("🔭 [IA STRAT] Buscando confluencias...")
        template = self._load_external_prompt('strategy')
        if not template: return

        context = self.brain.get_context_for_gemini(limit=5)
        try:
            prompt_data = {
                'context': context, 'recovery_status': 'ALPHA', 'num_positions': len(trades),
                'price': price, 'rsi': signals['rsi'], 'ema20': signals['ema_20'],
                'ema50': signals['ema_50'], 'bb_u': signals['bb_u'], 'bb_l': signals['bb_l'],
                'candles': json.dumps(signals['candles']), 'margin_sats': int(balance * 0.30)
            }
            prompt = template.format(**prompt_data)

            resp = self.client_gemini.models.generate_content(model=self.model_name, contents=prompt, config=self.safe_config)
            data = self._extract_json(resp.text)
            
            if data:
                # Guardamos incluyendo el balance actual
                self.brain.save_decision(price, data.get('action'), data.get('confidence', 0), data.get('logic', ''), indicators=signals, balance=int(balance))
                if data.get('action') in ['BUY', 'SELL']:
                    order = FuturesOrder(
                        type='market', side=data['action'].lower(), margin=int(balance * 0.30),
                        leverage=20, stoploss=self.round_to_tick(data.get('stop_loss')),
                        takeprofit=self.round_to_tick(data.get('take_profit'))
                    )
                    await client.futures.isolated.new_trade(order)
                    self.notifier.send_alert(f"🚀 Sniper {data['action']} | RSI: {signals['rsi']}")
                else:
                    print(f"IA decidió: {data.get('action') if data else 'HOLD'}")
        except Exception as e:
            print(f"❌ Error Formato Strat: {e}")

    async def run_trading_cycle(self):
        print(f"⚡ G9-SENTINEL V25.4: ALPHA SNIPER + CONCIENCIA DE CAPITAL")
        while True:
            try:
                async with LNMClient(self.config_lnm) as lnm:
                    acc = await lnm.account.get_account()
                    # Capturamos el balance real de la cuenta
                    current_balance = int(acc.balance) if hasattr(acc, 'balance') else 0
                    
                    tick = await lnm.futures.get_ticker()
                    price = float(tick.last_price)
                    sigs = await self.get_market_signals(lnm)
                    trades = await lnm.futures.isolated.get_running_trades()

                    print(f"[HEARTBEAT] {datetime.now().strftime('%H:%M:%S')} | BTC: ${price} | Bal: {current_balance} | Abiertas: {len(trades)}")

                    for p in trades:
                        await self.audit_position(lnm, p, sigs, price, current_balance)

                    if (datetime.now() - self.last_strategic_run) >= timedelta(minutes=self.strategic_cycle_minutes):
                        await self.seek_entries(lnm, current_balance, sigs, price)
                        self.last_strategic_run = datetime.now()

                await asyncio.sleep(self.fast_cycle_minutes * 60)
            except Exception as e:
                print(f"❌ Error ciclo: {e}")
                await asyncio.sleep(60)

if __name__ == '__main__':
    engine = G9SentinelEngine()
    asyncio.run(engine.run_trading_cycle())
