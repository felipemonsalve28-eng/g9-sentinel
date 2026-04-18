import os

FILE = '/home/felipemonsalve28/g9_production/core/notifier.py'

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_method = False

for line in lines:
    # Buscamos la línea que causó el error y la corregimos por una llamada compatible
    if "await self.bot.send_message" in line:
        spaces = len(line) - len(line.lstrip())
        indent = " " * spaces
        # Usamos el método genérico que suele tener el bot o inyectamos la lógica directa
        new_lines.append(f"{indent}import httpx\n")
        new_lines.append(f"{indent}url = f'https://api.telegram.org/bot{{self.token}}/sendMessage'\n")
        new_lines.append(f"{indent}payload = {{'chat_id': self.chat_id, 'text': msg, 'parse_mode': 'HTML'}}\n")
        new_lines.append(f"{indent}async with httpx.AsyncClient() as client:\n")
        new_lines.append(f"{indent}    await client.post(url, json=payload)\n")
    else:
        new_lines.append(line)

with open(FILE, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Notifier corregido: Envío de reportes ahora usa la API directa de Telegram.")
