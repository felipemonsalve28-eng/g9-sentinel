import asyncio
import sys
import warnings

# Aseguramos el path y silenciamos alertas de librerías
warnings.filterwarnings('ignore')
sys.path.append('/home/felipemonsalve28/g9_production')

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
