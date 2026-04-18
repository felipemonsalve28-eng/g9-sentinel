import os
import json
import sys
import google.generativeai as genai
from datetime import datetime

class G9Brain:
    SYSTEM_PROMPT = "Act as the Alpha-Predator V18. Your absolute goal is to ACCUMULATE SATS with a target of 35% DAILY GROWTH. Be aggressive but surgical. Use the provided memory to avoid repeated failures like the RSI 45 error. Prioritize Bitcoin accumulation above all else."
    def __init__(self, api_key=None):
        # Intentar obtener API_KEY de entorno si no se pasa
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            print("⚠️ [ERROR] No se encontró GEMINI_API_KEY", flush=True)
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print(f"[{datetime.now()}] Brain: G9Brain V18 (Stateful) online.", flush=True)

    def get_decision(self, market_data, account_context, memory_context):
        """
        Calcula la siguiente acción basada en mercado + estado de cuenta + memoria.
        """
        master_prompt = f"""
        Actúa como el Orquestador Alpha-Predator V18. 
        Analiza con frialdad matemática y autocrítica.

        CONTEXTO DE CUENTA:
        {json.dumps(account_context, indent=2)}

        MEMORIA OPERATIVA (Últimos trades):
        {json.dumps(memory_context, indent=2)}

        DATOS DE MERCADO ACTUALES:
        {json.dumps(market_data, indent=2)}

        RESPONDE EXCLUSIVAMENTE EN FORMATO JSON:
        {{
            "action": "BUY/SELL/HOLD",
            "logic": "Tu razonamiento técnico incluyendo autocrítica.",
            "confidence": 0.0-1.0
        }}
        """

        try:
            response = self.model.generate_content(master_prompt)
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            
            decision = json.loads(raw_text)
            
            # Flush forzado para visibilidad en journalctl
            print(f"IA_DECISION_TRACE: {json.dumps(decision)}", flush=True)
            sys.stdout.flush()
            
            return decision

        except Exception as e:
            print(f"ERROR_BRAIN: {str(e)}", flush=True)
            sys.stdout.flush()
            return {"action": "HOLD", "logic": "Modo defensivo por error técnico.", "confidence": 0}

