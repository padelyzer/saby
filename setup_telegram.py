#!/usr/bin/env python3
"""
Script de configuración y prueba para Telegram Bot
Guía paso a paso interactiva
"""

import json
import requests
import os
import time

def create_bot_instructions():
    """Muestra instrucciones para crear el bot"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                 📱 CONFIGURACIÓN BOT DE TELEGRAM                ║
╚════════════════════════════════════════════════════════════════╝

PASO 1: CREAR TU BOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Abre Telegram en tu teléfono o computadora
2. Busca el usuario: @BotFather
3. Envíale el comando: /newbot
4. Te pedirá un nombre para tu bot (ej: "Mi Trading Bot")
5. Te pedirá un username (debe terminar en 'bot'): mi_trading_bot
6. BotFather te dará un TOKEN que se ve así:
   
   5678901234:ABCdefGHIjklMNOpqrsTUVwxyz123456789
   
7. GUARDA ESE TOKEN - lo necesitarás en el siguiente paso

Presiona ENTER cuando tengas tu TOKEN...
""")
    input()
    return True

def get_chat_id(bot_token):
    """Obtiene el chat_id del usuario"""
    print("""
PASO 2: OBTENER TU CHAT ID
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Ve a Telegram y busca tu bot por su username
2. Envíale cualquier mensaje (ej: "Hola")
3. Presiona ENTER aquí después de enviar el mensaje...
""")
    input()
    
    print("🔍 Buscando tu Chat ID...")
    
    try:
        # Obtener actualizaciones del bot
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url)
        data = response.json()
        
        if data['ok'] and data['result']:
            # Obtener el chat_id del último mensaje
            chat_id = data['result'][-1]['message']['chat']['id']
            print(f"✅ Chat ID encontrado: {chat_id}")
            return str(chat_id)
        else:
            print("❌ No se encontraron mensajes. Asegúrate de haber enviado un mensaje a tu bot.")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_bot(bot_token, chat_id):
    """Envía un mensaje de prueba"""
    print("\nPASO 3: PRUEBA DEL BOT")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📤 Enviando mensaje de prueba...")
    
    try:
        # Mensaje de prueba con formato
        message = """
🎉 *¡CONFIGURACIÓN EXITOSA!*

Tu bot de señales de trading está listo para usar.

✅ *Bot Token:* Configurado
✅ *Chat ID:* Configurado
✅ *Conexión:* Funcionando

Ahora recibirás señales como esta:

📊 *BTC-USD*
🟢 *LONG* - Score: 7.5/10
💰 Entry: $43,250.50
🛑 Stop Loss: $42,817.99
🎯 Take Profit: $44,331.76
⚡ Leverage: 3x

_Mensaje de prueba enviado desde Signal Bot_
"""
        
        # Crear teclado inline de prueba
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Funciona", "callback_data": "test_ok"},
                    {"text": "📊 Ver Dashboard", "callback_data": "dashboard"}
                ]
            ]
        }
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'reply_markup': json.dumps(keyboard)
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("✅ ¡Mensaje enviado! Revisa tu Telegram")
            return True
        else:
            print(f"❌ Error enviando mensaje: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def save_config(bot_token, chat_id):
    """Guarda la configuración en el archivo"""
    print("\nPASO 4: GUARDAR CONFIGURACIÓN")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Cargar configuración existente o crear nueva
    config_file = 'signal_config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "filters": {
                "min_score": 5,
                "max_simultaneous_signals": 5,
                "cooldown_minutes": 15
            }
        }
    
    # Actualizar con configuración de Telegram
    config['telegram'] = {
        'enabled': True,
        'bot_token': bot_token,
        'chat_id': chat_id
    }
    
    # Asegurar que otros canales están deshabilitados por defecto
    if 'discord' not in config:
        config['discord'] = {'enabled': False, 'webhook_url': ''}
    if 'email' not in config:
        config['email'] = {'enabled': False}
    if 'webhook' not in config:
        config['webhook'] = {'enabled': False}
    
    # Guardar configuración
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuración guardada en {config_file}")
    return True

def send_test_signal():
    """Envía una señal de trading de prueba"""
    print("\nPASO 5: ENVIAR SEÑAL DE TRADING DE PRUEBA")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Importar el sistema de señales
    try:
        from signal_manager import SignalManager, TradingSignal
        from datetime import datetime
        
        # Crear gestor con la configuración guardada
        manager = SignalManager()
        
        # Crear una señal de prueba
        test_signal = TradingSignal(
            timestamp=datetime.now().isoformat(),
            ticker="BTC-USD",
            action="BUY_LONG",
            price=43250.50,
            stop_loss=42817.99,
            take_profit=44331.76,
            score=7.5,
            direccion="LONG",
            timeframe="1H",
            leverage=3,
            position_size_pct=5.0,
            risk_reward_ratio=2.5,
            confidence="HIGH"
        )
        
        print("📤 Enviando señal de trading de prueba...")
        
        # Enviar la señal
        results = manager.broadcast_signal(test_signal)
        
        if results.get('TelegramNotifier', False):
            print("✅ ¡Señal de trading enviada a Telegram!")
            print("\n📱 Revisa tu Telegram - Deberías ver:")
            print("   - Información detallada del trade")
            print("   - Botones para copiar valores")
            print("   - Formato profesional con emojis")
            return True
        else:
            print("❌ Error enviando la señal")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de tener el archivo signal_manager.py")
        return False

def main():
    """Función principal de configuración"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║              🚀 CONFIGURADOR DE TELEGRAM BOT                    ║
║                  Para Señales de Trading                        ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Paso 1: Instrucciones para crear bot
    create_bot_instructions()
    
    # Obtener token del usuario
    print("📝 Ingresa tu Bot Token:")
    bot_token = input("Token: ").strip()
    
    if not bot_token or len(bot_token) < 40:
        print("❌ Token inválido")
        return
    
    # Paso 2: Obtener Chat ID
    chat_id = get_chat_id(bot_token)
    
    if not chat_id:
        print("\n🔄 Intentando método alternativo...")
        print(f"""
Método alternativo:
1. Abre este link en tu navegador:
   https://api.telegram.org/bot{bot_token}/getUpdates
   
2. Busca "chat":{{"id": NUMERO}}
3. Ese NUMERO es tu Chat ID

Ingresa tu Chat ID manualmente:
""")
        chat_id = input("Chat ID: ").strip()
    
    # Paso 3: Probar bot
    if test_bot(bot_token, chat_id):
        # Paso 4: Guardar configuración
        if save_config(bot_token, chat_id):
            # Paso 5: Enviar señal de prueba
            print("\n¿Quieres enviar una señal de trading de prueba? (s/n)")
            if input().lower() == 's':
                send_test_signal()
            
            print("""
╔════════════════════════════════════════════════════════════════╗
║                    ✅ CONFIGURACIÓN COMPLETA                    ║
╚════════════════════════════════════════════════════════════════╝

Tu bot de Telegram está listo para:
• Recibir señales automáticas cada 5 minutos
• Alertas instantáneas de oportunidades de trading
• Botones interactivos para copiar valores

🚀 Para iniciar el bot automático:
   python3 signal_bot.py

📊 Para abrir el dashboard:
   python3 -m streamlit run signal_dashboard.py

💡 Consejo: Puedes anclar el chat del bot en Telegram
          para no perderte ninguna señal

¡Feliz Trading! 📈
""")
    else:
        print("❌ No se pudo completar la configuración")

if __name__ == "__main__":
    main()