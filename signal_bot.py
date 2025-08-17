#!/usr/bin/env python3
"""
Bot de Monitoreo Continuo de Señales
Ejecuta análisis cada 5 minutos y envía alertas automáticamente
"""

import time
import schedule
import json
import os
from datetime import datetime
from signal_manager import SignalManager
import threading
import queue

class SignalBot:
    """Bot autónomo de señales de trading"""
    
    def __init__(self, interval_minutes=5):
        self.manager = SignalManager()
        self.interval = interval_minutes
        self.running = False
        self.signal_queue = queue.Queue()
        
        # Cargar lista de tickers
        self.tickers = self.load_tickers()
        
        # Estadísticas
        self.stats = {
            'scans_performed': 0,
            'signals_generated': 0,
            'last_scan': None,
            'start_time': datetime.now()
        }
    
    def load_tickers(self):
        """Carga la lista de tickers a monitorear"""
        # Top 15 criptos por defecto
        default_tickers = [
            'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'SOL-USD',
            'ADA-USD', 'DOGE-USD', 'MATIC-USD', 'DOT-USD', 'AVAX-USD',
            'LINK-USD', 'LTC-USD', 'UNI-USD', 'ATOM-USD', 'FIL-USD'
        ]
        
        # Intentar cargar desde archivo
        if os.path.exists('watchlist.json'):
            try:
                with open('watchlist.json', 'r') as f:
                    custom_tickers = json.load(f)
                    return custom_tickers.get('tickers', default_tickers)
            except:
                pass
        
        return default_tickers
    
    def scan_and_notify(self):
        """Escanea el mercado y envía notificaciones"""
        try:
            print(f"\n{'='*60}")
            print(f"🔄 Iniciando escaneo - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Incrementar contador
            self.stats['scans_performed'] += 1
            self.stats['last_scan'] = datetime.now().isoformat()
            
            # Escanear mercado
            signals = self.manager.scan_market(self.tickers)
            
            if signals:
                print(f"\n🎯 {len(signals)} señales encontradas!")
                self.stats['signals_generated'] += len(signals)
                
                # Procesar cada señal
                for signal in signals:
                    # Mostrar en consola
                    print(f"\n{'='*50}")
                    print(signal.format_message())
                    
                    # Enviar a todos los canales
                    results = self.manager.broadcast_signal(signal)
                    
                    # Mostrar resultados
                    success_count = sum(1 for v in results.values() if v)
                    print(f"📤 Señal enviada a {success_count}/{len(results)} canales")
                    
                    # Agregar a la cola para procesamiento adicional
                    self.signal_queue.put(signal)
            else:
                print("❌ No se encontraron señales en este escaneo")
            
            # Mostrar estadísticas
            self.show_stats()
            
        except Exception as e:
            print(f"❌ Error en escaneo: {e}")
    
    def show_stats(self):
        """Muestra estadísticas del bot"""
        runtime = datetime.now() - self.stats['start_time']
        hours = runtime.total_seconds() / 3600
        
        print(f"\n📊 ESTADÍSTICAS DEL BOT")
        print(f"├─ Tiempo ejecutando: {hours:.1f} horas")
        print(f"├─ Escaneos realizados: {self.stats['scans_performed']}")
        print(f"├─ Señales generadas: {self.stats['signals_generated']}")
        print(f"└─ Último escaneo: {self.stats['last_scan']}")
    
    def start(self):
        """Inicia el bot de monitoreo"""
        self.running = True
        
        print(f"""
╔════════════════════════════════════════════════════╗
║           🤖 BOT DE SEÑALES DE TRADING            ║
╠════════════════════════════════════════════════════╣
║ Intervalo: Cada {self.interval} minutos                      ║
║ Activos monitoreados: {len(self.tickers)}                       ║
║ Canales activos: {len(self.manager.channels)}                           ║
╚════════════════════════════════════════════════════╝
        """)
        
        # Hacer primer escaneo inmediato
        print("\n🚀 Realizando escaneo inicial...")
        self.scan_and_notify()
        
        # Programar escaneos periódicos
        schedule.every(self.interval).minutes.do(self.scan_and_notify)
        
        print(f"\n⏰ Próximo escaneo en {self.interval} minutos...")
        print("🛑 Presiona Ctrl+C para detener el bot\n")
        
        # Loop principal
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Detiene el bot"""
        self.running = False
        print("\n\n🛑 Bot detenido")
        self.show_stats()
        print("\n👋 Hasta luego!")

class SignalAPI:
    """API REST para consultar señales (opcional)"""
    
    def __init__(self, manager: SignalManager, port=8080):
        from flask import Flask, jsonify, request
        
        self.app = Flask(__name__)
        self.manager = manager
        self.port = port
        
        # Definir endpoints
        self.setup_routes()
    
    def setup_routes(self):
        """Configura los endpoints de la API"""
        
        @self.app.route('/signals/active', methods=['GET'])
        def get_active_signals():
            """Retorna señales activas"""
            signals = self.manager.get_active_signals()
            return jsonify([s.to_dict() for s in signals])
        
        @self.app.route('/signals/history', methods=['GET'])
        def get_signal_history():
            """Retorna historial de señales"""
            limit = request.args.get('limit', 50, type=int)
            signals = self.manager.signal_history[-limit:]
            return jsonify([s.to_dict() for s in signals])
        
        @self.app.route('/signals/scan', methods=['POST'])
        def trigger_scan():
            """Ejecuta un escaneo manual"""
            data = request.json or {}
            tickers = data.get('tickers', [])
            
            if not tickers:
                tickers = ['BTC-USD', 'ETH-USD', 'BNB-USD']
            
            signals = self.manager.scan_market(tickers)
            return jsonify({
                'found': len(signals),
                'signals': [s.to_dict() for s in signals]
            })
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check del servicio"""
            return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
    
    def run(self):
        """Inicia el servidor API"""
        print(f"🌐 API iniciada en http://localhost:{self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

def create_telegram_bot():
    """Crea un bot de Telegram (instrucciones)"""
    instructions = """
📱 CONFIGURACIÓN BOT DE TELEGRAM:

1. Abrir Telegram y buscar @BotFather
2. Enviar comando: /newbot
3. Elegir nombre para tu bot (ej: Mi Trading Bot)
4. Elegir username (debe terminar en 'bot'): mi_trading_bot
5. BotFather te dará un TOKEN - guárdalo

6. Para obtener tu CHAT_ID:
   - Envía un mensaje a tu bot
   - Visita: https://api.telegram.org/bot<TOKEN>/getUpdates
   - Busca "chat":{"id": <CHAT_ID>}

7. Edita signal_config.json:
   {
     "telegram": {
       "enabled": true,
       "bot_token": "TU_TOKEN_AQUI",
       "chat_id": "TU_CHAT_ID_AQUI"
     }
   }

✅ Listo! Las señales llegarán a tu Telegram
"""
    print(instructions)

def create_discord_webhook():
    """Crea un webhook de Discord (instrucciones)"""
    instructions = """
💬 CONFIGURACIÓN WEBHOOK DISCORD:

1. Ir a tu servidor de Discord
2. Click derecho en el canal → Editar canal
3. Integraciones → Webhooks → Crear Webhook
4. Darle un nombre (ej: Trading Signals)
5. Copiar URL del webhook

6. Edita signal_config.json:
   {
     "discord": {
       "enabled": true,
       "webhook_url": "TU_WEBHOOK_URL_AQUI"
     }
   }

✅ Listo! Las señales llegarán a tu Discord
"""
    print(instructions)

def main():
    """Función principal"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'setup-telegram':
            create_telegram_bot()
        elif command == 'setup-discord':
            create_discord_webhook()
        elif command == 'api':
            # Iniciar API
            manager = SignalManager()
            api = SignalAPI(manager)
            api.run()
        else:
            print(f"Comando desconocido: {command}")
            print("Comandos disponibles: setup-telegram, setup-discord, api")
    else:
        # Iniciar bot por defecto
        bot = SignalBot(interval_minutes=5)
        bot.start()

if __name__ == "__main__":
    main()