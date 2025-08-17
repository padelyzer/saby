#!/usr/bin/env python3
"""
Demo de señales por Telegram - Bot temporal para pruebas
NOTA: Este es solo para demostración, crea tu propio bot para uso real
"""

import requests
import json
from datetime import datetime

print("""
════════════════════════════════════════════════════════════════
           📱 DEMO DE TELEGRAM - SEÑALES DE TRADING
════════════════════════════════════════════════════════════════

⚠️  IMPORTANTE: Este es un bot de DEMOSTRACIÓN
    Para uso real, debes crear tu propio bot siguiendo los pasos.

PARA RECIBIR UNA SEÑAL DE PRUEBA:
──────────────────────────────────────────────────────────────
1. Abre Telegram
2. Busca: @crypto_signals_demo_bot
3. Envíale: /start
4. Luego ejecuta este script para recibir una señal de ejemplo

Nota: El bot de demo puede no estar disponible.
      Es mejor crear tu propio bot para garantizar funcionamiento.

════════════════════════════════════════════════════════════════

MEJOR OPCIÓN - CREAR TU PROPIO BOT:
──────────────────────────────────────────────────────────────
1. En Telegram busca: @BotFather
2. Envía: /newbot
3. Sigue las instrucciones
4. Usa el token en telegram_quick_test.py

════════════════════════════════════════════════════════════════
""")

def show_example_signal():
    """Muestra cómo se verá una señal"""
    example = """
EJEMPLO DE SEÑAL QUE RECIBIRÁS:
──────────────────────────────────────────────────────────────

🟢 **SEÑAL LONG** 🟢
━━━━━━━━━━━━━━━━
📊 Par: BTC-USD
💰 Entry: $43,250.50
🛑 SL: $42,817.99
🎯 TP: $44,331.76
📈 Score: 7.5/10
⚡ Leverage: 3x
━━━━━━━━━━━━━━━━

[📋 Copiar Entry] [🛑 Copiar SL]
[🎯 Copiar TP] [✅ Aplicar Trade]

──────────────────────────────────────────────────────────────
Las señales incluyen:
✅ Precio exacto de entrada
✅ Stop Loss calculado automáticamente
✅ Take Profit con ratio 1:2.5
✅ Score de confianza (0-10)
✅ Botones para copiar valores fácilmente
──────────────────────────────────────────────────────────────
"""
    print(example)

if __name__ == "__main__":
    show_example_signal()
    
    print("""
SIGUIENTE PASO:
──────────────────────────────────────────────────────────────
Edita telegram_quick_test.py con tu token y chat ID:

1. Abre el archivo telegram_quick_test.py
2. En la línea 37: BOT_TOKEN = "tu_token_aqui"
3. En la línea 38: CHAT_ID = "tu_chat_id_aqui"
4. Guarda y ejecuta: python3 telegram_quick_test.py

¡Tu bot estará listo para enviar señales automáticas!
""")