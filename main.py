import asyncio
import sys
import warnings

# Aseguramos el path y silenciamos alertas de librerías
warnings.filterwarnings('ignore')
sys.path.append('/home/felipemonsalve28/g9_production')


# --- MÓDULO DE SEGURIDAD V17.2 (GOOGLE SECRET MANAGER) ---
def load_secure_credentials():
    import io
    from dotenv import load_dotenv
    try:
        from google.cloud import secretmanager
        import urllib.request
        
        # 1. Obtener Project ID desde el Metadata Server de la Máquina Virtual
        url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
        req = urllib.request.Request(url, headers={"Metadata-Flavor": "Google"})
        project_id = urllib.request.urlopen(req, timeout=2).read().decode()
        
        # 2. Extraer claves de la Bóveda
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/g9-sentinel-vault/versions/latest"
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        
        # 3. Cargar en memoria de forma segura (sin escribir en disco)
        load_dotenv(stream=io.StringIO(payload))
        print("🔐 [SECURITY] Credenciales cargadas exitosamente desde Google Secret Manager.")
    except Exception as e:
        print(f"⚠️ [SECURITY FALLBACK] No se pudo acceder a la bóveda ({e}). Leyendo .env local...")
        load_dotenv()

load_secure_credentials()
# ---------------------------------------------------------

from core.engine import G9SentinelEngine

if __name__ == "__main__":
    print("===================================================")
    print("🟢 G9-SENTINEL CORE ORCHESTRATOR INICIADO")
    print("🔗 Arquitectura: Motor Dual (5m/15m) V18")
    print("===================================================")
    
    try:
        # Instanciamos el motor
        engine = G9SentinelEngine()
        # Ejecutamos el método de la clase
        asyncio.run(engine.run_trading_cycle())
    except KeyboardInterrupt:
        print("\n🛑 Apagado manual detectado.")
    except Exception as e:
        print(f"\n❌ Error crítico en el orquestador: {e}")
