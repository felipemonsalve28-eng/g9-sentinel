# G9-Sentinel
**Versión:** 14.6 (Producción Consolidada)
**Entorno:** Google Cloud Platform (g9-trader-node)

## Descripción del Sistema
G9-Sentinel es un agente autónomo de trading algorítmico que combina análisis técnico cuantitativo con la capacidad de razonamiento de Gemini (gemini-2.5-flash).

## Arquitectura de Directorios
* `/core/`: Motor de trading, cerebro de IA y notificador.
* `/data/`: Base de datos persistente (g9_market.db).
* `/archive/`: Scripts obsoletos y auditorías previas.

## Lógica Operativa
1. **Percepción:** RSI, Bollinger, Volatilidad.
2. **Memoria:** Historial de las últimas 10 operaciones (PnL).
3. **Gestión:** Trailing Stop dinámico que solo se mueve a favor del profit.

## Ejecución
```bash
/home/felipemonsalve28/g9_production/venv/bin/python3 /home/felipemonsalve28/g9_production/main.py
``