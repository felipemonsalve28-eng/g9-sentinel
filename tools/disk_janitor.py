import os
import shutil
import time

# --- CONFIGURACIÓN DE UMBRALES ---
THRESHOLD = 80.0  # Porcentaje máximo permitido
BASE_DIR = "/home/felipemonsalve28/g9_production"
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ROOT_LOG = os.path.join(BASE_DIR, "bot.log")

def check_disk_usage():
    """Calcula el porcentaje de disco usado en la partición principal."""
    total, used, free = shutil.disk_usage("/")
    percent = (used / total) * 100
    return percent

def tactical_cleanup():
    """Ejecuta la limpieza sin romper los procesos vivos (Truncado)."""
    print(f"🧹 ALERTA: Iniciando Protocolo de Limpieza. Disco superó el {THRESHOLD}%")
    
    # 1. Truncar el log raíz (vaciar sin borrar)
    if os.path.exists(ROOT_LOG):
        with open(ROOT_LOG, 'w'): pass
        print(f"✅ Vaciado completo: {ROOT_LOG}")

    # 2. Limpieza inteligente del directorio /logs
    if os.path.exists(LOGS_DIR):
        current_time = time.time()
        for filename in os.listdir(LOGS_DIR):
            filepath = os.path.join(LOGS_DIR, filename)
            
            if os.path.isfile(filepath):
                # A. Borrar archivos que tengan más de 7 días de antigüedad (604800 segundos)
                if (current_time - os.path.getmtime(filepath)) > 604800 and filename != "trading.log":
                    os.remove(filepath)
                    print(f"🗑️ Eliminado log obsoleto: {filename}")
                
                # B. Truncado quirúrgico del log de trading vivo (dejamos solo lo más reciente)
                elif filename == "trading.log":
                    try:
                        with open(filepath, 'r') as f:
                            lines = f.readlines()
                        
                        # Si el log tiene más de 5000 líneas, conservamos solo las últimas 500
                        if len(lines) > 5000:
                            with open(filepath, 'w') as f:
                                f.writelines(lines[-500:])
                            print(f"✂️ Log truncado (500 líneas retenidas): {filename}")
                    except Exception as e:
                        print(f"⚠️ No se pudo truncar trading.log: {e}")

def run_diagnostics():
    print(f"--- G9-Janitor: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    usage = check_disk_usage()
    print(f"📊 Uso actual del disco: {usage:.2f}%")
    
    if usage >= THRESHOLD:
        tactical_cleanup()
        # Volver a medir después de limpiar
        new_usage = check_disk_usage()
        print(f"🏁 Limpieza finalizada. Nuevo uso de disco: {new_usage:.2f}%")
    else:
        print("🛡️ Espacio en niveles seguros. No se requiere acción.")

if __name__ == "__main__":
    run_diagnostics()
