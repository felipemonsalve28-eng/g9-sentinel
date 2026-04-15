import os
from dotenv import load_dotenv
from lnmarkets import rest

# Cargamos las llaves desde el archivo .env
load_dotenv()

class LNMConnector:
    def __init__(self):
        self.key = os.getenv('LNM_KEY')
        self.secret = os.getenv('LNM_SECRET')
        self.passphrase = os.getenv('LNM_PASSPHRASE')
        self.network = os.getenv('LNM_NETWORK', 'mainnet')
        
        options = {
            'key': self.key,
            'secret': self.secret,
            'passphrase': self.passphrase,
            'network': self.network
        }
        
        # Iniciamos el cliente REST de la librería oficial
        self.lnm = rest.LNMarketsRest(**options)

    def get_balance(self):
        """Obtiene el balance del usuario en SATS."""
        try:
            user = self.lnm.get_user()
            return user.get('balance', 0)
        except Exception as e:
            return f"❌ Error de balance: {e}"

    def execute_trade(self, side, margin, leverage=25):
        """
        Ejecuta una operación.
        side: 'b' (buy/long), 's' (sell/short)
        """
        params = {
            'type': 'm', # Market order
            'side': side,
            'margin': int(margin),
            'leverage': float(leverage)
        }
        try:
            return self.lnm.futures_new_trade(params)
        except Exception as e:
            return f"❌ Error en trade: {e}"

if __name__ == "__main__":
    # Prueba de conexión rápida
    connector = LNMConnector()
    print(f"💰 Balance actual: {connector.get_balance()} SATS")
