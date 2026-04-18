import os

def fix_model_version():
    file_path = 'engine.py'
    
    print("🔧 Restaurando versión del modelo a gemini-2.5-flash...")
    
    if not os.path.exists(file_path):
        print("❌ Error: No se encuentra engine.py")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Reemplazamos la cadena del modelo incorrecto por el correcto
    if "gemini-2.5-flash" in content:
        content = content.replace("gemini-2.5-flash", "gemini-2.5-flash")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ engine.py actualizado. Modelo restaurado a gemini-2.5-flash.")
    else:
        print("⚠️ No se encontró la referencia a gemini-2.0-flash en el archivo.")

if __name__ == "__main__":
    fix_model_version()
