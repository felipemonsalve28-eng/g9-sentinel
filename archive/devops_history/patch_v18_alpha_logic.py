import os
import shutil
import re

BASE_DIR = "/home/felipemonsalve28/g9_production"
ENGINE_PATH = os.path.join(BASE_DIR, "core/engine.py")
BACKUP_PATH = os.path.join(BASE_DIR, "archive/devops_history/engine_v16.5.bak")

def apply_v18_patch():
    print("🛠️ Iniciando inyección de lógica Alpha V18...")

    if not os.path.exists(ENGINE_PATH):
        print(f"❌ CRÍTICO: No se encontró el motor en {ENGINE_PATH}")
        return

    # 1. Crear Backup
    os.makedirs(os.path.dirname(BACKUP_PATH), exist_ok=True)
    shutil.copy2(ENGINE_PATH, BACKUP_PATH)
    print(f"✅ Backup de seguridad creado en: {BACKUP_PATH}")

    with open(ENGINE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # --- INYECCIÓN 1: VOLATILIDAD ALFA EN SEÑALES ---
    old_signals = """            df['rsi'] = ta.rsi(df['close'], length=14)
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)

            current_rsi = round(df['rsi'].iloc[-1], 2)
            current_adx = round(adx_df['ADX_14'].iloc[-1], 2) if adx_df is not None else 0

            return {
                "rsi": current_rsi,
                "adx": current_adx,
                "regimen": "TENDENCIA" if current_adx > 25 else "RANGO",
                "trend": "SOBRECOMPRA" if current_rsi > 70 else ("SOBREVENTA" if current_rsi < 30 else "NEUTRAL")
            }"""

    new_signals = """            df['rsi'] = ta.rsi(df['close'], length=14)
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
            
            # --- NUEVO V18: CÁLCULO DE VOLATILIDAD (ATR Y BOLLINGER) ---
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
            }"""
            
    content = content.replace(old_signals, new_signals)

    # --- INYECCIÓN 2: BREAKEVEN AUTOMÁTICO EN AUDITORÍA ---
    old_audit_prompt = """        SISTEMA DE GESTIÓN G9 V16.5
        Posición: {pos.side} | Entrada: ${pos.price} | PnL: {pos.pl} SATS
        Mercado: BTC ${price} | RSI: {signals['rsi']} ({signals['trend']})

        Tarea: Decide si UPDATE_SL, CLOSE_POSITION o HOLD_POSITION.
        Responde SOLO JSON: {"action": "...", "new_stop_loss": 0, "logic": "...", "confidence": 0}"""

    new_audit_prompt = """        SISTEMA DE GESTIÓN G9 V18 (PRO-GUARD)
        Posición: {pos.side} | Entrada: ${pos.price} | PnL: {pos.pl} SATS
        Mercado: BTC ${price} | RSI: {signals['rsi']} ({signals['trend']})

        REGLA DE DEFENSA ESTRICTA: Si el PnL es mayor a 500 SATS, es OBLIGATORIO asegurar la operación dictando un "new_stop_loss" ligeramente a favor del precio de entrada (${pos.price}) para garantizar un Breakeven. ¡Cero tolerancia a devolver ganancias al mercado!
        
        Tarea: Decide si UPDATE_SL, CLOSE_POSITION o HOLD_POSITION.
        Responde SOLO JSON: {"action": "...", "new_stop_loss": 0, "logic": "...", "confidence": 0}"""
        
    content = content.replace(old_audit_prompt, new_audit_prompt)

    # --- INYECCIÓN 3: FILTRO DE SPREAD EN ENTRADAS ---
    old_sniper_prompt = """        SISTEMA SNIPER G9 V16.5
        Contexto: {memoria}
        Balance: {balance} | RSI: {signals['rsi']} | ADX: {signals['adx']}
        ¿BUY/SELL/HOLD? JSON: {"action": "...", "margin": 0, "leverage": 0, "stop_loss": 0, "take_profit": 0, "logic": "..."}"""

    new_sniper_prompt = """        SISTEMA SNIPER G9 V18 (ALPHA SEEKER)
        Contexto: {memoria}
        Balance: {balance} | RSI: {signals['rsi']} | ADX: {signals['adx']} | ATR: {signals['atr']} | BB Width: {signals['bb_width']}
        
        REGLA DE RENTABILIDAD ESTRICTA: El ATR actual ({signals['atr']}) y la amplitud de bandas ({signals['bb_width']}) representan la volatilidad. Si la volatilidad es muy baja, los movimientos no cubrirán las comisiones del broker. Responde "HOLD" si el Alpha de volatilidad es pobre.
        
        ¿BUY/SELL/HOLD? JSON: {"action": "...", "margin": 0, "leverage": 0, "stop_loss": 0, "take_profit": 0, "logic": "..."}"""
        
    content = content.replace(old_sniper_prompt, new_sniper_prompt)

    # Validar si se hicieron los cambios
    if "SISTEMA DE GESTIÓN G9 V18" in content and "SISTEMA SNIPER G9 V18" in content:
        with open(ENGINE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Motor V16.5 actualizado exitosamente a la lógica V18.")
    else:
        print("⚠️ No se pudieron realizar los reemplazos. Verifica que el archivo core/engine.py coincida con la V16.5 exacta.")

if __name__ == "__main__":
    apply_v18_patch()
