import os

file_path = '/home/felipemonsalve28/g9_production/core/engine.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Definir la función de carga
load_func = """
    def _load_external_prompt(self, p_type):
        \"\"\"Carga prompts desde /config/prompts/ de forma segura.\"\"\"
        path = f'/home/felipemonsalve28/g9_production/config/prompts/{p_type}.txt'
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content: return content
        except: pass
        return None
"""

if "_load_external_prompt" not in code:
    code = code.replace("class G9SentinelEngine:", "class G9SentinelEngine:" + load_func)

# 2. Parchear con el nuevo límite del 30%
search_seek = 'prompt = f"""'
replace_seek = """        # --- SISTEMA DE PROMPTS DINÁMICOS V22 (RIESGO 30%) ---
        external_prompt = self._load_external_prompt("strategy")
        if external_prompt:
            prompt = external_prompt.format(
                recovery_status='🚨 RECOVERY' if recovery_active else '✅ ALPHA',
                num_positions=num_positions,
                progress_pct=progress_pct,
                price=price,
                rsi=signals.get('rsi'),
                margin_sats=int(balance * 0.30)
            )
        else:
            prompt = f\"\"\""""

if search_seek in code and "SISTEMA DE PROMPTS DINÁMICOS" not in code:
    code = code.replace(search_seek, replace_seek)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)
