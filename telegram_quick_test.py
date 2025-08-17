#!/usr/bin/env python3
"""
Test rápido de Telegram Bot - Sin interacción
"""

import json
import requests
from datetime import datetime

# INSTRUCCIONES RÁPIDAS
print("""
════════════════════════════════════════════════════════════════
                📱 CONFIGURACIÓN RÁPIDA TELEGRAM BOT
════════════════════════════════════════════════════════════════

PASO 1: CREAR TU BOT EN TELEGRAM
─────────────────────────────────────────────────────────────
1. Abre Telegram
2. Busca: @BotFather
3. Envía: /newbot
4. Dale un nombre: "Mi Trading Bot"  
5. Dale un username: mi_trading_bot (debe terminar en 'bot')
6. Copia el TOKEN que te da

PASO 2: OBTENER TU CHAT ID
─────────────────────────────────────────────────────────────
1. Envía un mensaje a tu bot
2. Abre en navegador (reemplaza TU_TOKEN):
   https://api.telegram.org/botTU_TOKEN/getUpdates
3. Busca: "chat":{"id":NUMERO}
4. Ese NUMERO es tu Chat ID

════════════════════════════════════════════════════════════════
""")

# Configuración manual - EDITA ESTOS VALORES
BOT_TOKEN = "8433114763:AAExLQhROt2X66yUX6msH8pK5mLrwKVRhAs"  # Token configurado
CHAT_ID = "943397764"      # Chat ID configurado - @ja04mx

def test_connection():
    """Prueba la conexión con el bot"""
    if BOT_TOKEN == "TU_BOT_TOKEN_AQUI":
        print("❌ Por favor, edita este archivo y agrega tu BOT_TOKEN")
        print("   Línea 35: BOT_TOKEN = 'tu_token_real'")
        return False
    
    if CHAT_ID == "TU_CHAT_ID_AQUI":
        print("❌ Por favor, edita este archivo y agrega tu CHAT_ID")
        print("   Línea 36: CHAT_ID = 'tu_chat_id_real'")
        return False
    
    print("🔍 Probando conexión...")
    
    try:
        # Verificar que el bot existe
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url)
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Bot encontrado: @{bot_info['result']['username']}")
            return True
        else:
            print(f"❌ Token inválido o bot no encontrado")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def send_test_message():
    """Envía un mensaje de prueba"""
    print("\n📤 Enviando mensaje de prueba...")
    
    message = """
🎉 *¡BOT CONFIGURADO EXITOSAMENTE!*

Tu bot de señales está listo para recibir alertas de trading.

✅ Conexión establecida
✅ Mensajes funcionando
✅ Formato rico habilitado

_Mensaje de prueba - Signal Bot_
"""
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("✅ ¡Mensaje enviado! Revisa tu Telegram")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return False

def send_trading_signal():
    """Envía una señal de trading de ejemplo"""
    print("\n📊 Enviando señal de trading de ejemplo...")
    
    # Crear mensaje de señal
    signal_message = f"""
🟢 **SEÑAL LONG** 🟢
━━━━━━━━━━━━━━━━━━━
📊 **Par:** BTC-USD
⚡ **Acción:** COMPRAR
💰 **Precio:** $43,250.50
🛑 **Stop Loss:** $42,817.99
🎯 **Take Profit:** $44,331.76
📈 **Score:** 7.5/10
⚙️ **Leverage:** 3x
📏 **Tamaño:** 5% del capital
⏰ **Hora:** {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━

_Señal generada automáticamente_
"""
    
    # Agregar botones inline
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📋 Entry: $43,250", "callback_data": "copy_entry"},
                {"text": "🛑 SL: $42,817", "callback_data": "copy_sl"}
            ],
            [
                {"text": "🎯 TP: $44,331", "callback_data": "copy_tp"},
                {"text": "✅ Aplicar", "callback_data": "apply_trade"}
            ]
        ]
    }
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': signal_message,
        'parse_mode': 'Markdown',
        'reply_markup': json.dumps(keyboard)
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("✅ ¡Señal de trading enviada!")
            print("📱 Revisa tu Telegram - verás botones interactivos")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def save_config():
    """Guarda la configuración en el archivo"""
    print("\n💾 Guardando configuración...")
    
    config = {
        "telegram": {
            "enabled": True,
            "bot_token": BOT_TOKEN,
            "chat_id": CHAT_ID
        },
        "discord": {
            "enabled": False,
            "webhook_url": ""
        },
        "email": {
            "enabled": False
        },
        "webhook": {
            "enabled": False
        },
        "filters": {
            "min_score": 5,
            "max_simultaneous_signals": 5,
            "cooldown_minutes": 15
        }
    }
    
    with open('signal_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuración guardada en signal_config.json")
    return True

def main():
    """Función principal"""
    print("\n🚀 PROBANDO BOT DE TELEGRAM")
    print("════════════════════════════════════════════\n")
    
    # Paso 1: Probar conexión
    if not test_connection():
        return
    
    # Paso 2: Enviar mensaje de prueba
    if not send_test_message():
        return
    
    # Paso 3: Enviar señal de trading
    if not send_trading_signal():
        return
    
    # Paso 4: Guardar configuración
    save_config()
    
    print("""
════════════════════════════════════════════════════════════════
                    ✅ CONFIGURACIÓN COMPLETA
════════════════════════════════════════════════════════════════

Tu bot está listo para usar. Comandos disponibles:

🤖 Iniciar bot automático (escanea cada 5 min):
   python3 signal_bot.py

📊 Abrir dashboard web:
   python3 -m streamlit run signal_dashboard.py

📡 Probar señales manualmente:
   python3 signal_manager.py

💡 Los mensajes llegarán automáticamente a tu Telegram
   cuando el bot encuentre oportunidades de trading.

════════════════════════════════════════════════════════════════
""")

if __name__ == "__main__":
    main()