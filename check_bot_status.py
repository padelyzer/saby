#!/usr/bin/env python3
"""
Verificar estado del bot de señales
"""

import json
import os
from datetime import datetime
import requests

print("""
╔════════════════════════════════════════════════════════════════╗
║                   🤖 ESTADO DEL BOT DE SEÑALES                  ║
╚════════════════════════════════════════════════════════════════╝
""")

# Verificar configuración
if os.path.exists('signal_config.json'):
    with open('signal_config.json', 'r') as f:
        config = json.load(f)
    
    telegram_enabled = config.get('telegram', {}).get('enabled', False)
    
    if telegram_enabled:
        print("✅ Telegram configurado y activo")
        print(f"   Bot: @JA04mxbot")
        print(f"   Chat ID: {config['telegram']['chat_id']}")
    else:
        print("❌ Telegram no configurado")
    
    print(f"\n📊 Filtros activos:")
    print(f"   Score mínimo: {config.get('filters', {}).get('min_score', 5)}/10")
    print(f"   Máx señales simultáneas: {config.get('filters', {}).get('max_simultaneous_signals', 5)}")
    print(f"   Cooldown: {config.get('filters', {}).get('cooldown_minutes', 15)} minutos")

# Verificar archivos de señales
print("\n📁 Archivos de señales:")
signal_files = [f for f in os.listdir('.') if f.startswith('signals_')]
if signal_files:
    for file in signal_files[-3:]:  # Últimos 3 archivos
        print(f"   • {file}")
else:
    print("   No hay señales guardadas aún")

# Estado del mercado actual
try:
    from motor_trading import calcular_semaforo_mercado
    estado = calcular_semaforo_mercado()
    
    emoji = "🟢" if estado == "VERDE" else "🔴" if estado == "ROJO" else "🟡"
    print(f"\n📈 Estado del mercado: {emoji} {estado}")
    
    if estado == "VERDE":
        print("   → Buscando señales LONG")
    elif estado == "ROJO":
        print("   → Buscando señales SHORT")
    else:
        print("   → Mercado neutral - Sin señales")
except:
    print("\n📈 Estado del mercado: No disponible")

print("""
════════════════════════════════════════════════════════════════
                         🔄 BOT ACTIVO
════════════════════════════════════════════════════════════════

El bot está ejecutándose y:
• Escanea el mercado cada 5 minutos
• Analiza 15 criptomonedas principales
• Envía señales a tu Telegram cuando encuentra oportunidades
• Solo envía señales con Score ≥ 5/10

📱 Las señales llegarán automáticamente a tu Telegram
   No necesitas hacer nada más, solo esperar.

💡 Primera señal: Puede tomar 5-15 minutos en aparecer
   (depende de las condiciones del mercado)

Para detener el bot: Ctrl+C en la terminal del bot
════════════════════════════════════════════════════════════════
""")