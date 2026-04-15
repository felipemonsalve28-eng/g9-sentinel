import os
from dotenv import load_dotenv
from lnmarkets import rest

# Cargamos el .env desde la raíz
load_dotenv('/home/felipemonsalve28/g9_production/.env')

def test_lnm():
    options = {
        'key': os.getenv('LNM_KEY'),
        'secret': os.getenv('LNM_SECRET'),
        'passphrase': os.getenv('LNM_PASSPHRASE'),
        'network': os.getenv('LNM_NETWORK', 'mainnet')
    }
    
    lnm = rest.LNMarketsRest(**options)
    
    try:
        user = lnm.get_user()
        if isinstance(user, dict):
            return f"✅ Conexión exitosa. Balance: {user.get('balance')} SATS"
        else:
            return f"❌ Error de respuesta (posiblemente llaves incorrectas): {user}"
    except Exception as e:
        return f"❌ Error de conexión: {str(e)}"

if __name__ == "__main__":
    print("🔌 Conectando con LN Markets...")
    print(test_lnm())
