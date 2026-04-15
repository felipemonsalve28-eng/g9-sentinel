#!/bin/bash

echo "=== INICIANDO AUDITORÍA DEL BOT DE TRADING ==="
OUTPUT_FILE="bot_context_report.txt"

# 1. Información del Sistema y Entorno
echo "--- ENTORNO Y LIBRERÍAS ---" > $OUTPUT_FILE
echo "Python Version:" >> $OUTPUT_FILE
python3 --version >> $OUTPUT_FILE 2>&1
echo -e "\nLibrerías instaladas (pip freeze):" >> $OUTPUT_FILE
pip freeze >> $OUTPUT_FILE

# 2. Estructura de Archivos
echo -e "\n--- ESTRUCTURA DE DIRECTORIOS ---" >> $OUTPUT_FILE
ls -R | grep ":$" | sed -e 's/:$//' -e 's/[^-][^\/]*\//--/g' -e 's/^/   /' >> $OUTPUT_FILE

# 3. Lectura de Archivos Python (.py) y JSON (.json)
echo -e "\n--- CONTENIDO DE ARCHIVOS CLAVE ---" >> $OUTPUT_FILE
for file in $(find . -maxdepth 2 -name "*.py" -o -name "*.json" -o -name ".env.example"); do
    echo -e "\n>> ARCHIVO: $file" >> $OUTPUT_FILE
    echo "--------------------------------------" >> $OUTPUT_FILE
    cat "$file" >> $OUTPUT_FILE
    echo -e "\n--------------------------------------" >> $OUTPUT_FILE
done

echo "=== AUDITORÍA FINALIZADA ==="
echo "El archivo '$OUTPUT_FILE' ha sido generado. Puedes copiar su contenido aquí."
