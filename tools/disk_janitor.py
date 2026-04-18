import os
import shutil
import time
import psutil
from collections import deque

# --- CONFIGURACIÓN DE UMBRALES ---
DISK_THRESHOLD = 75.0  # Bajamos a 75% para ser más preventivos
RAM_THRESHOLD = 85.0   # Alerta si la RAM es crítica
BASE_DIR = "/home/felipemonsalve28/g9_production"
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ROOT_LOG = os.path.join(BASE_DIR, "bot.log")

def check_resources():
    """Monitorea Salud de Hardware."""
    disk = shutil.disk_usage("/")
    disk_p = (disk.used / disk.total) * 100
    
    ram = psutil.virtual_memory()
    ram_p = ram.percent
    
    return disk_p, ram_p

def efficient_truncate(filepath, lines_to_keep=500):
    """Vacia el archivo conservando solo las últimas N líneas de forma eficiente."""
    try:
        with open(filepath, 'r') as f:
            last_lines = deque(f, maxlen=lines_to_keep)
        
        with open(filepath, 'w') as f:
            f.writelines(last_lines)
        print(f"✂️ [TRUNCATE] {os.path.basename(filepath)} reducido a {lines_to_keep} líneas.")
    except Exception as e:
        print(f"⚠️ [ERROR] No se pudo truncar {filepath}: {e}")

def deep_clean():
    """Limpieza profunda de residuos de ejecución."""
    print("🧹 [JANITOR] Iniciando Protocolo de Limpieza Profunda...")

    # 1. Truncar Log Raíz
    if os.path.exists(ROOT_LOG):
        with open(ROOT_LOG, 'w'): pass
        print(f"✅ [CLEAN] Vaciado: {ROOT_LOG}")

    # 2. Rotación de Directorio /logs
    if os.path.exists(LOGS_DIR):
        now = time.time()
        for filename in os.listdir(LOGS_DIR):
            path = os.path.join(LOGS_DIR, filename)
            
            # Borrar archivos de más de 5 días (excepto el activo)
            if os.path.isfile(path):
                if (now - os.path.getmtime(path)) > (5 * 86400) and filename != "trading.log":
                    os.remove(path)
                    print(f"🗑️ [DELETE] Log antiguo: {filename}")
                
                # Truncar el log vivo de trading si es muy grande
                elif filename == "trading.log" and os.path.getsize(path) > 10 * 1024 * 1024: # > 10MB
                    efficient_truncate(path)

    # 3. Limpiar __pycache__ (Libera inodos y espacio)
    for root, dirs, files in os.walk(BASE_DIR):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            shutil.rmtree(pycache_path)
            print(f"🧹 [CLEAN] Eliminado cache: {pycache_path}")

def run():
    disk_p, ram_p = check_resources()
    print(f"📊 [STATUS] Disco: {disk_p:.1f}% | RAM: {ram_p:.1f}%")

    if disk_p >= DISK_THRESHOLD:
        print("🚨 [CRITICAL] Umbral de DISCO superado.")
        deep_clean()
    
    if ram_p >= RAM_THRESHOLD:
        print("🚨 [CRITICAL] RAM saturada. Reportando para reinicio de servicio si persiste.")
        # Aquí podrías añadir un: os.system("systemctl restart g9-sentinel") si es muy crítico

if __name__ == "__main__":
    run()
