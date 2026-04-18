import os
import sqlite3

def fix_critical_bugs():
    print("🛠️ Iniciando Reparación Crítica V13.1...")

    # 1. REPARACIÓN ABSOLUTA DE LA BASE DE DATOS
    db_path = '/home/felipemonsalve28/g9_production/g9_memory.db'
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("ALTER TABLE ai_decisions ADD COLUMN indicators_snapshot TEXT;")
        conn.commit()
        print("✅ Base de datos parcheada: Columna 'indicators_snapshot' añadida con éxito.")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✅ DB Check: La columna 'indicators_snapshot' ya estaba instalada.")
        else:
            print(f"⚠️ DB Info: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

    # 2. REPARACIÓN DEL ENRUTADOR DE EJECUCIÓN EN ENGINE.PY
    file_path = 'engine.py'
    if not os.path.exists(file_path):
        print(f"❌ Error: No se encuentra {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Puntos de anclaje exactos en tu código
    marker_logic = "print(f\"📝 Lógica: {decision.get('logic')}\")"
    marker_save = "brain.save_decision("

    if marker_logic in content and marker_save in content:
        # Partimos el archivo en tres piezas para inyectar el medio perfecto
        top_half = content.split(marker_logic)[0] + marker_logic + "\n"
        bottom_half = content.split(marker_save)[1]

        # Árbol de decisiones mutuamente excluyente
        perfect_router = """
            if action == "UPDATE_SL" and in_position:
                new_sl = decision.get("new_stop_loss")
                if new_sl:
                    new_sl = round_to_tick(new_sl)
                    print(f"🛡️ ACTUALIZANDO STOP LOSS DINÁMICO a: ${new_sl}")
                    try:
                        await client.futures.isolated.update_stoploss(id=current_position.id, stoploss=new_sl)
                        print("✅ TRAILING STOP ACTUALIZADO CON ÉXITO.")
                    except Exception as api_err:
                        print(f"❌ Error al actualizar SL: {api_err}")
                else:
                    print("⚠️ UPDATE_SL invocado pero sin nuevo precio. Manteniendo posición.")
                    
            elif action == "CLOSE_POSITION" and in_position:
                print("🚨 ORDEN DE CIERRE RECIBIDA. Asegurando posición...")
                try:
                    await client.futures.isolated.close(id=current_position.id)
                    print("✅ POSICIÓN CERRADA CON ÉXITO.")
                except Exception as api_err:
                    print(f"❌ Error al cerrar posición: {api_err}")

            elif action in ["BUY", "SELL"] and not in_position:
                if margin > (balance * 0.35):
                    margin = int(balance * 0.35)
                print(f"🔨 Ejecutando {action} | Margen: {margin} SATS | Apalan: {leverage}x")
                print(f"🛡️ SL Validado: {sl} | TP Validado: {tp}")
                try:
                    trade_params = FuturesOrder(
                        type="market",
                        side=action.lower(),
                        margin=margin,
                        leverage=leverage,
                        stoploss=sl,
                        takeprofit=tp
                    )
                    await client.futures.isolated.new_trade(trade_params)
                    print("✅ ¡ORDEN AISLADA EJECUTADA CON ÉXITO!")
                except Exception as api_err:
                    print(f"❌ Error de LN Markets al ejecutar: {api_err}")

            else:
                print("⏳ Manteniendo posición (HOLD) o buscando setup. Bóveda intacta.")

            """
        
        # Ensamblamos y guardamos
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(top_half + perfect_router + "            brain.save_decision(" + bottom_half)
        print("✅ engine.py: Enrutador de ejecución reparado. Ya no confundirá un Trailing Stop con una orden nueva.")
    else:
        print("⚠️ No se encontraron los marcadores en engine.py. El archivo puede estar mal formateado.")

if __name__ == "__main__":
    fix_critical_bugs()
