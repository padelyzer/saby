#!/usr/bin/env python3
"""
Trading Bot V4.0 ADAPTATIVO - Optimizado para Replit
Sistema inteligente que detecta régimen de mercado y ajusta estrategias
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import os
import logging
import requests
import warnings
import threading
import json
from flask import Flask, jsonify
warnings.filterwarnings('ignore')

# Import del sistema adaptativo
from trading_system_v4 import (
    MarketRegimeDetector,
    TrendStrategy,
    RangeStrategy,
    VolatileStrategy,
    AdaptiveTradingSystem,
    DCAStrategy
)

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'Trading Bot V4.0 ADAPTATIVO running on Replit',
        'version': '4.0',
        'features': ['Adaptive Regime Detection', 'Multi-Strategy', 'DCA', 'Risk Management'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/status')
def status():
    """Endpoint para ver el estado actual del bot"""
    global bot
    if bot:
        return jsonify({
            'status': 'running',
            'capital': bot.current_capital,
            'active_signals': len(bot.active_signals),
            'last_check': bot.last_check.isoformat() if bot.last_check else None,
            'regime': bot.current_regime
        })
    return jsonify({'status': 'not initialized'})


class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message, parse_mode="HTML"):
        if not self.bot_token or not self.chat_id:
            return False
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")
            return False
    
    def send_adaptive_signal(self, signal_data):
        """Envía señal adaptativa con información del régimen"""
        signal_emoji = "🟢" if signal_data['type'] == 'LONG' else "🔴"
        regime_emoji = {
            'TRENDING_UP': '📈',
            'TRENDING_DOWN': '📉',
            'RANGING': '↔️',
            'VOLATILE': '⚡'
        }.get(signal_data['regime'], '❓')
        
        message = f"""
{signal_emoji} <b>SEÑAL ADAPTATIVA V4.0</b>

{regime_emoji} <b>Régimen:</b> {signal_data['regime']}
🎯 <b>Estrategia:</b> {signal_data['strategy']}
📊 <b>Símbolo:</b> {signal_data['symbol']}
📈 <b>Tipo:</b> {signal_data['type']}
💰 <b>Entry:</b> ${signal_data['entry_price']:,.2f}
🛡️ <b>Stop Loss:</b> ${signal_data['stop_loss']:,.2f}
🎊 <b>Take Profit:</b> ${signal_data['take_profit']:,.2f}
🎯 <b>Confianza:</b> {signal_data['confidence']:.1%}
⚖️ <b>Riesgo:</b> {signal_data['risk']*100:.1f}% del capital

🔍 <b>Señales:</b> {', '.join(signal_data['signals'][:3])}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_message(message)
    
    def send_dca_opportunity(self, opportunities):
        """Envía oportunidades DCA"""
        if not opportunities:
            return
            
        message = "💰 <b>OPORTUNIDADES DCA DETECTADAS</b>\n\n"
        
        for opp in opportunities:
            emoji = "🔥" if opp['signal'] == 'STRONG_BUY' else "✅"
            message += f"{emoji} <b>{opp['symbol'].replace('-USD', '')}</b>\n"
            message += f"  📉 Caída: {opp['dip_from_high']:.1f}%\n"
            message += f"  💵 Precio: ${opp['current_price']:,.2f}\n"
            message += f"  💰 Comprar: ${opp['amount']:.2f}\n\n"
        
        message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        return self.send_message(message)
    
    def send_system_status(self, status, info=None):
        if status == "STARTED":
            message = f"""
🚀 <b>BOT V4.0 ADAPTATIVO INICIADO</b>

✅ Sistema inteligente funcionando
🧠 Detección automática de régimen
📊 Multi-estrategia adaptativa
💰 Capital inicial: $206 USD
🎯 Símbolos: ADA, XRP, DOGE, AVAX, SOL, LINK, DOT
☁️ Plataforma: Replit

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        elif status == "REGIME_CHANGE" and info:
            message = f"""
🔄 <b>CAMBIO DE RÉGIMEN DETECTADO</b>

Anterior: {info.get('old_regime', 'UNKNOWN')}
Nuevo: {info.get('new_regime', 'UNKNOWN')}
Confianza: {info.get('confidence', 0):.1%}

El bot ajustará automáticamente las estrategias.

⏰ {datetime.now().strftime('%H:%M:%S')}
            """.strip()
        else:
            message = f"ℹ️ <b>SISTEMA:</b> {status}"
        
        return self.send_message(message)


class AdaptiveTradingBotV4:
    def __init__(self):
        self.initial_capital = 206
        self.current_capital = self.initial_capital
        
        # Parámetros del sistema adaptativo
        self.params = {
            'check_interval_minutes': 15,
            'dca_check_interval': 60,  # Revisar DCA cada hora
            'max_signals_per_day': 5,
            'min_regime_confidence': 0.4,
        }
        
        # Símbolos optimizados
        self.symbols = [
            'ADA-USD', 'XRP-USD', 'DOGE-USD',
            'AVAX-USD', 'SOL-USD', 'LINK-USD', 'DOT-USD'
        ]
        
        self.active_signals = {}
        self.signal_history = []
        self.current_regime = None
        self.last_regime = None
        
        # Sistemas adaptativos por símbolo
        self.adaptive_systems = {}
        for symbol in self.symbols:
            self.adaptive_systems[symbol] = AdaptiveTradingSystem(
                symbol, 
                capital=self.current_capital / len(self.symbols)
            )
        
        # Sistema DCA
        self.dca_system = DCAStrategy(self.symbols, capital=self.current_capital)
        
        self.setup_logging()
        self.setup_telegram()
        
        self.last_check = None
        self.last_dca_check = None
        self.system_status = "STARTING"
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            self.telegram = TelegramNotifier(bot_token, chat_id)
            self.logger.info("✅ Telegram configurado")
        else:
            self.telegram = None
            self.logger.warning("⚠️ Telegram no configurado")
    
    def detect_global_regime(self):
        """Detecta el régimen global del mercado"""
        regimes = []
        
        # Usar BTC y ETH como proxy del mercado general
        for symbol in ['BTC-USD', 'ETH-USD']:
            try:
                ticker = yf.Ticker(symbol)
                df_daily = ticker.history(period='30d', interval='1d')
                df_4h = ticker.history(period='7d', interval='1h')
                df_1h = df_4h  # Usar mismo data
                
                # Resample para 4H
                df_4h_resampled = df_4h.resample('4H').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
                
                if len(df_4h_resampled) > 10:
                    regime_info = MarketRegimeDetector.detect_regime(
                        df_1h, df_4h_resampled, df_daily
                    )
                    regimes.append(regime_info['regime'])
            except:
                pass
        
        # Determinar régimen dominante
        if regimes:
            from collections import Counter
            regime_count = Counter(regimes)
            self.current_regime = regime_count.most_common(1)[0][0]
        else:
            self.current_regime = 'UNKNOWN'
        
        # Detectar cambio de régimen
        if self.last_regime and self.last_regime != self.current_regime:
            self.logger.info(f"🔄 Cambio de régimen: {self.last_regime} → {self.current_regime}")
            if self.telegram:
                self.telegram.send_system_status("REGIME_CHANGE", {
                    'old_regime': self.last_regime,
                    'new_regime': self.current_regime,
                    'confidence': 0.8
                })
        
        self.last_regime = self.current_regime
        return self.current_regime
    
    def scan_for_adaptive_signals(self):
        """Escanea señales con el sistema adaptativo"""
        self.logger.info(f"🔍 Escaneando señales adaptativas...")
        
        # Detectar régimen global primero
        global_regime = self.detect_global_regime()
        self.logger.info(f"📊 Régimen global: {global_regime}")
        
        signals_found = 0
        today = datetime.now().date()
        today_signals = [s for s in self.signal_history if s.get('date', datetime.now()).date() == today]
        
        if len(today_signals) >= self.params['max_signals_per_day']:
            self.logger.info(f"⚠️ Límite diario alcanzado ({len(today_signals)}/{self.params['max_signals_per_day']})")
            return
        
        for symbol in self.symbols:
            if symbol in self.active_signals:
                continue  # Ya tiene señal activa
            
            try:
                system = self.adaptive_systems[symbol]
                
                # Obtener datos
                df_1h, df_4h, df_daily = system.get_multi_timeframe_data()
                
                if df_1h is None:
                    continue
                
                # Generar señal adaptativa
                signal = system.generate_adaptive_signal(df_1h, df_4h, df_daily)
                
                if signal and signal['confidence'] >= 0.5:
                    # Ejecutar señal
                    trade = system.execute_signal(signal)
                    
                    # Registrar
                    self.active_signals[symbol] = trade
                    self.signal_history.append({
                        'date': datetime.now(),
                        'symbol': symbol,
                        'trade': trade
                    })
                    
                    signals_found += 1
                    
                    self.logger.info(f"✅ {symbol}: {signal['type']} - {signal['strategy']} (conf: {signal['confidence']:.1%})")
                    
                    # Notificar
                    if self.telegram:
                        signal_data = {
                            'symbol': symbol,
                            'type': signal['type'],
                            'entry_price': trade['entry'],
                            'stop_loss': trade['stop_loss'],
                            'take_profit': trade['take_profit'],
                            'confidence': signal['confidence'],
                            'risk': signal['risk'],
                            'regime': signal['regime'],
                            'strategy': signal['strategy'],
                            'signals': signal['signals']
                        }
                        self.telegram.send_adaptive_signal(signal_data)
                    
            except Exception as e:
                self.logger.error(f"Error escaneando {symbol}: {e}")
        
        if signals_found == 0:
            self.logger.info("📊 No hay señales en este momento")
        else:
            self.logger.info(f"🎯 {signals_found} señales generadas")
    
    def check_dca_opportunities(self):
        """Revisa oportunidades DCA"""
        self.logger.info("💰 Revisando oportunidades DCA...")
        
        opportunities = self.dca_system.scan_opportunities()
        
        if opportunities and self.telegram:
            self.telegram.send_dca_opportunity(opportunities)
    
    def run_trading_cycle(self):
        """Ciclo principal adaptativo"""
        try:
            self.logger.info("🔄 Iniciando ciclo adaptativo...")
            self.system_status = "RUNNING"
            
            # Escanear señales adaptativas
            self.scan_for_adaptive_signals()
            
            # Revisar DCA cada hora
            now = datetime.now()
            if not self.last_dca_check or (now - self.last_dca_check).seconds >= self.params['dca_check_interval'] * 60:
                self.check_dca_opportunities()
                self.last_dca_check = now
            
            # Stats
            self.logger.info(f"📊 Señales activas: {len(self.active_signals)}")
            
            self.last_check = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error en ciclo: {e}")
            self.system_status = "ERROR"
    
    def run_forever(self):
        """Loop principal para Replit"""
        self.logger.info("🚀 Trading Bot V4.0 ADAPTATIVO iniciado")
        
        if self.telegram:
            self.telegram.send_system_status("STARTED")
        
        while True:
            try:
                self.run_trading_cycle()
                
                wait_minutes = self.params['check_interval_minutes']
                self.logger.info(f"⏱️ Esperando {wait_minutes} minutos...")
                time.sleep(wait_minutes * 60)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Bot detenido")
                break
            except Exception as e:
                self.logger.error(f"Error crítico: {e}")
                time.sleep(60)


def start_flask_server():
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)


def main():
    global bot
    
    print("🚀 INICIANDO TRADING BOT V4.0 ADAPTATIVO")
    
    # Servidor Flask para keepalive
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    print("🌐 Servidor Flask iniciado")
    
    # Bot de trading adaptativo
    bot = AdaptiveTradingBotV4()
    bot.run_forever()


if __name__ == "__main__":
    main()