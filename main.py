import asyncio
import sys
import warnings

# Supresión de advertencias no críticas y aseguramiento del path
warnings.filterwarnings('ignore')
sys.path.append('/home/felipemonsalve28/g9_production')

from core.engine import run_trading_cycle

if __name__ == "__main__":
    print("===================================================")
    print("🟢 G9-SENTINEL CORE ORCHESTRATOR INICIADO")
    print("🔗 Arquitectura: Producción Consolidada (V14.6)")
    print("===================================================")
    try:
        asyncio.run(run_trading_cycle())
    except KeyboardInterrupt:
        print("\n🛑 Apagado manual del sistema detectado.")
    except Exception as e:
        print(f"\n❌ Error crítico en el orquestador: {e}")
