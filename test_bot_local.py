#!/usr/bin/env python3
"""
Script para probar el bot localmente antes de deploy
"""

import os
import sys
from datetime import datetime

def test_telegram_config():
    """Prueba configuración de Telegram"""
    print("🧪 TESTING TELEGRAM SETUP...")
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN no encontrado")
        print("💡 Ejecuta: export TELEGRAM_BOT_TOKEN='tu_token_aquí'")
        return False
    
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID no encontrado")
        print("💡 Ejecuta: export TELEGRAM_CHAT_ID='tu_chat_id_aquí'")
        return False
    
    print(f"✅ TELEGRAM_BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ TELEGRAM_CHAT_ID: {chat_id}")
    
    # Probar envío de mensaje
    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"🧪 Test desde bot local\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Mensaje de prueba enviado a Telegram")
            return True
        else:
            print(f"❌ Error enviando mensaje: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando Telegram: {e}")
        return False

def test_yfinance():
    """Prueba yfinance"""
    print("\n🧪 TESTING YFINANCE...")
    
    try:
        import yfinance as yf
        
        ticker = yf.Ticker("BTC-USD")
        data = ticker.history(period="5d")
        
        if len(data) > 0:
            last_price = data['Close'].iloc[-1]
            print(f"✅ yfinance funcionando - BTC: ${last_price:,.2f}")
            return True
        else:
            print("❌ yfinance no retorna datos")
            return False
            
    except Exception as e:
        print(f"❌ Error con yfinance: {e}")
        return False

def test_dependencies():
    """Prueba dependencias"""
    print("\n🧪 TESTING DEPENDENCIES...")
    
    dependencies = ['pandas', 'numpy', 'yfinance', 'requests']
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - ejecuta: pip install {dep}")
            return False
    
    return True

def test_trading_logic():
    """Prueba lógica de trading básica"""
    print("\n🧪 TESTING TRADING LOGIC...")
    
    try:
        # Importar nuestro bot
        from main_trading_bot import TradingBotV25
        
        # Crear instancia
        bot = TradingBotV25()
        
        # Probar obtener datos
        df = bot.get_market_data("BTC-USD", days=30)
        
        if df is None:
            print("❌ No se pudieron obtener datos de mercado")
            return False
        
        print(f"✅ Datos obtenidos: {len(df)} días de BTC")
        
        # Probar indicadores
        df = bot.calculate_indicators(df)
        
        if 'RSI' not in df.columns:
            print("❌ Error calculando indicadores")
            return False
        
        print(f"✅ Indicadores calculados - RSI actual: {df['RSI'].iloc[-1]:.1f}")
        
        # Probar señal
        signal_type, confidence, signals = bot.generate_signal(df)
        
        print(f"✅ Señal generada: {signal_type or 'NONE'} (conf: {confidence:.1%})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en lógica de trading: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 TESTING TRADING BOT V2.5 LOCAL")
    print("="*50)
    
    tests = [
        test_dependencies,
        test_yfinance,
        test_telegram_config,
        test_trading_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("="*50)
    print(f"📊 RESULTADOS: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("✅ TODO LISTO PARA DEPLOY EN RENDER!")
        print("\n🚀 Próximos pasos:")
        print("1. git add . && git commit -m 'Trading bot ready'")
        print("2. git push origin main")
        print("3. Conectar a Render siguiendo SETUP_GUIDE.md")
    else:
        print("❌ Arreglar errores antes de deploy")
        print("\n🔧 Revisar:")
        print("1. Variables de entorno de Telegram")
        print("2. Instalación de dependencias")
        print("3. Conectividad a internet")

if __name__ == "__main__":
    main()