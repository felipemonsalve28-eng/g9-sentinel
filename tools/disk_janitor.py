import os
import shutil
import time
import psutil
import sqlite3
from collections import deque

# --- CONFIGURACIÓN ---
DISK_THRESHOLD = 75.0
RAM_THRESHOLD = 85.0
BASE_DIR = "/home/felipemonsalve28/g9_production"
LOGS_DIR = os.path.join(BASE_DIR, "logs")
# Archivos críticos para monitorear individualmente
CRITICAL_LOGS = [
    os.path.join(BASE_DIR, "bot_output.log"),
    os.path.join(BASE_DIR, "bot.log"),
    os.path.join(LOGS_DIR, "trading.log"),
    os.path.join(LOGS_DIR, "sys_out.log")
]
DB_PATH = os.path.join(BASE_DIR, "data/g9_market.db")

def check_resources():
    disk = shutil.disk_usage("/")
    disk_p = (disk.used / disk.total) * 100
    ram = psutil.virtual_memory().percent
    return disk_p, ram

def efficient_truncate(filepath, lines_to_keep=1000):
    """Mantiene solo las últimas N líneas para que el log no pese MBs."""
    try:
        if not os.path.exists(filepath): return
        with open(filepath, 'r') as f:
            last_lines = deque(f, maxlen=lines_to_keep)
        with open(filepath, 'w') as f:
            f.writelines(last_lines)
        print(f"✂️ [TRUNCATE] {os.path.basename(filepath)} reducido.")
    except Exception as e:
        print(f"⚠️ Error truncando {filepath}: {e}")

def vacuum_db():
    """Limpia registros viejos de la DB (> 15 días) y compacta el archivo."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Borrar registros de más de 15 días para mantener agilidad
        cursor.execute("DELETE FROM ai_decisions WHERE timestamp < datetime('now', '-15 days')")
        deleted = cursor.rowcount
        conn.execute("VACUUM") # Compacta el archivo en disco
        conn.commit()
        conn.close()
        print(f"🧠 [DB] Limpieza completada. {deleted} registros antiguos eliminados.")
    except Exception as e:
        print(f"⚠️ Error en DB Janitor: {e}")

def deep_clean():
    print("🧹 [JANITOR] Iniciando limpieza profunda...")

    # 1. Truncar logs críticos sin importar el tamaño total del disco
    for log in CRITICAL_LOGS:
        if os.path.exists(log) and os.path.getsize(log) > 5 * 1024 * 1024: # > 5MB
            efficient_truncate(log)

    # 2. Limpieza de logs antiguos en /logs
    if os.path.exists(LOGS_DIR):
        now = time.time()
        for filename in os.listdir(LOGS_DIR):
            path = os.path.join(LOGS_DIR, filename)
            if os.path.isfile(path) and (now - os.path.getmtime(path)) > (3 * 86400): # 3 días
                os.remove(path)
                print(f"🗑️ [DELETE] Log antiguo: {filename}")

    # 3. Mantenimiento de Base de Datos
    vacuum_db()

    # 4. Limpiar cache de Python
    for root, dirs, files in os.walk(BASE_DIR):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))

def run():
    disk_p, ram_p = check_resources()
    print(f"📊 [STATUS] Disco: {disk_p:.1f}% | RAM: {ram_p:.1f}%")

    # Ejecutar limpieza si el disco está alto O si simplemente toca mantenimiento
    if disk_p >= DISK_THRESHOLD:
        print("🚨 [CRITICAL] Espacio insuficiente. Activando deep_clean.")
        deep_clean()
    else:
        # Mantenimiento preventivo ligero de DB siempre
        vacuum_db()

if __name__ == "__main__":
    run()
