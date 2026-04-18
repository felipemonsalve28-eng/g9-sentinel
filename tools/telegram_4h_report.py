import sys, os, json, subprocess, re
sys.path.append('/home/felipemonsalve28/g9_production')
from dotenv import load_dotenv
load_dotenv('/home/felipemonsalve28/g9_production/.env')
from core.notifier import G9Notifier

def extraer_datos():
    log_path = '/home/felipemonsalve28/g9_production/bot_output.log'
    d = {"btc": "0", "rsi": 0, "pos": "0", "logic": "IA en espera...", "bal": "Sincronizando..."}
    try:
        content = subprocess.getoutput(f"tail -n 150 {log_path}")
        
        # 1. Balance Sniper (Busca etiqueta o números de 6+ cifras)
        bal_match = re.findall(r'TELEMETRY_BALANCE: ([0-9.]+)', content)
        if bal_match:
            d["bal"] = "{:,}".format(int(float(bal_match[-1])))
        else:
            # Plan B: Buscar números grandes que no sean el precio de BTC
            potential_bal = re.findall(r'(?<!\$)\b\d{6,10}\b', content)
            if potential_bal: d["bal"] = "{:,}".format(int(potential_bal[-1]))

        # 2. Heartbeat (BTC, RSI, Posiciones)
        hb = [l for l in content.split('\n') if '[HEARTBEAT]' in l]
        if hb:
            last_hb = hb[-1]
            d["btc"] = re.search(r'BTC: \$([0-9.]+)', last_hb).group(1)
            d["rsi"] = float(re.search(r'RSI: ([0-9.]+)', last_hb).group(1))
            d["pos"] = re.search(r'Abiertas: ([0-9]+)', last_hb).group(1)

        # 3. Lógica de Gemini (Captura mejorada)
        logic_match = re.findall(r'Lógica: (.*)', content)
        if logic_match: d["logic"] = logic_match[-1]
        elif "HOLD" in content: d["logic"] = "IA decidió mantener posiciones (RSI en rango)."
    except: pass
    return d

def generar_reporte():
    notifier = G9Notifier()
    data = extraer_datos()
    
    rsi_val = data["rsi"]
    emoji_rsi = "🔴" if rsi_val > 70 else ("🟢" if rsi_val < 30 else "🟡")
    
    msg = f"🛡️ <b>G9-SENTINEL: STATUS PRO V21.1</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"🏦 <b>BÓVEDA TÁCTICA</b>\n"
    msg += f"• Balance: <code>{data['bal']} Sats</code>\n"
    msg += f"• Precio BTC: <code>${data['btc']}</code>\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"🎯 <b>ESTADO DE OPERACIÓN</b>\n"
    msg += f"• Posiciones: <code>{data['pos']}</code>\n"
    msg += f"• RSI: {emoji_rsi} <code>{rsi_val}</code>\n"
    msg += f"━━━━━━━━━━━━━━━━━━\n"
    msg += f"🧠 <b>RAZONAMIENTO GEMINI</b>\n"
    msg += f"<i>\"{data['logic'][:250]}\"</i>\n\n"
    msg += f"🚀 <b>Objetivo: +35% Sats/Día</b>"

    notifier.send_alert(msg)

if __name__ == "__main__":
    generar_reporte()
