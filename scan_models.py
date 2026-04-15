import inspect
import lnmarkets_sdk.v3.models.futures_isolated as models

print("🔍 Escaneando modelos de datos de Futures Isolated...")
for name, obj in inspect.getmembers(models, inspect.isclass):
    if issubclass(obj, BaseModel) or hasattr(obj, 'model_fields'):
        fields = obj.model_fields.keys() if hasattr(obj, 'model_fields') else obj.__fields__.keys()
        print(f"📦 Modelo: {name} | Parámetros: {list(fields)}")
