import json
import os
from datetime import datetime

MEMORY_PATH = 'data/session_memory.json'

def get_full_context(account_data):
    """Combina datos en tiempo real con memoria histórica."""
    memory = {
        "performance_summary": {"total_pnl": 0, "win_rate": 0},
        "recent_history": []
    }
    
    if os.path.exists(MEMORY_PATH):
        try:
            with open(MEMORY_PATH, 'r') as f:
                memory = json.load(f)
        except Exception as e:
            print(f"WARN: No se pudo leer la memoria: {e}", flush=True)

    context = {
        "equity": account_data.get('total_balance', 0),
        "margin_pct": account_data.get('margin_usage_pct', 0),
        "open_trades_count": len(account_data.get('positions', [])),
        "memory": memory
    }
    return context

def save_trade_result(action, pnl, logic_critique):
    """Registra el resultado de la operación."""
    if not os.path.exists(MEMORY_PATH): return
    
    try:
        with open(MEMORY_PATH, 'r+') as f:
            data = json.load(f)
            new_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "pnl": pnl,
                "logic_critique": logic_critique
            }
            data['recent_history'].append(new_entry)
            data['recent_history'] = data['recent_history'][-5:]
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            print(f"INFO: Memoria actualizada: {action} PnL: {pnl}", flush=True)
    except Exception as e:
        print(f"ERROR: No se pudo guardar memoria: {e}", flush=True)
