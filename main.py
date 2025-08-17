#!/usr/bin/env python3
"""
Trading Bot V2.5 - Optimizado para Replit
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
from flask import Flask, jsonify
warnings.filterwarnings('ignore')

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'Trading Bot V2.5 running on Replit',
        'timestamp': datetime.now().isoformat()
    })

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
    
    def send_signal_alert(self, trade_data):
        signal_emoji = "🟢" if trade_data['type'] == 'LONG' else "🔴"
        
        message = f"""
{signal_emoji} <b>NUEVA SEÑAL - REPLIT</b>

📊 <b>Símbolo:</b> {trade_data['symbol']}
📈 <b>Tipo:</b> {trade_data['type']}
💰 <b>Entry:</b> ${trade_data['entry_price']:,.2f}
🎯 <b>Confianza:</b> {trade_data['confidence']:.1%}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_message(message)
    
    def send_system_status(self, status):
        if status == "STARTED":
            message = f"""
🚀 <b>BOT INICIADO EN REPLIT</b>

✅ Sistema V2.5 funcionando
💰 Capital inicial: $206 USD
🎯 8 Símbolos: ADA, XRP, DOGE, AVAX, SOL, LINK, DOT, PEPE
☁️ Plataforma: Replit

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        else:
            message = f"ℹ️ <b>SISTEMA:</b> {status}"
        
        return self.send_message(message)


class TradingBotV25:
    def __init__(self):
        self.initial_capital = 206
        self.current_capital = self.initial_capital
        
        self.params = {
            'rsi_oversold': 30,  # Más estricto para oversold
            'rsi_overbought': 70,  # Más estricto para overbought
            'atr_stop_multiplier': 2.0,
            'atr_target_multiplier': 3.0,
            'counter_trend_forbidden': True,
            'min_confidence': 0.35,  # Más selectivo (era 0.25)
            'min_volume_ratio': 1.2,  # Volumen 20% sobre promedio
            'risk_per_trade': 0.005,
            'max_daily_trades': 3,
            'check_interval_minutes': 10,  # Reducido por más símbolos
        }
        
        # Símbolos optimizados para capital de $206
        # Incluye altcoins con buena liquidez y volatilidad
        self.symbols = [
            'ADA-USD',    # ~$0.35
            'XRP-USD',    # ~$0.60
            'DOGE-USD',   # ~$0.23
            'AVAX-USD',   # ~$25
            'SOL-USD',    # ~$150
            'LINK-USD',   # ~$15
            'DOT-USD',    # ~$5
            'PEPE-USD'    # ~$0.000008
        ]
        self.active_positions = {}
        self.trade_history = []
        
        self.setup_logging()
        self.setup_telegram()
        
        self.system_status = "STARTING"
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            self.telegram = TelegramNotifier(bot_token, chat_id)
            self.logger.info("✅ Telegram configurado")
        else:
            self.telegram = None
            self.logger.warning("⚠️ Revisa Secrets en Replit")
    
    def get_market_data(self, symbol, days=30):
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            # Usar intervalo de 1 hora para mejor precisión en crypto
            df = ticker.history(start=start_date, end=end_date, interval='1h')
            return df if len(df) >= 50 else None
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de {symbol}: {e}")
            return None
    
    def calculate_indicators(self, df):
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # EMAs
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # Tendencia
        df['Uptrend'] = df['EMA_20'] > df['EMA_50']
        df['Downtrend'] = df['EMA_20'] < df['EMA_50']
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        return df
    
    def generate_signal(self, df):
        if len(df) < 50:
            return None, 0, []
        
        current = df.iloc[-1]
        score = 0
        signals = []
        signal_type = None
        
        # Validar volumen
        avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
        current_volume = current['Volume']
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Si volumen bajo, no operar
        if volume_ratio < self.params['min_volume_ratio']:
            return None, 0, ['LOW_VOLUME']
        
        # Tendencia con confirmación múltiple
        if current['Uptrend'] and current['EMA_20'] > df['EMA_20'].iloc[-5]:
            trend = 'UP'
            signals.append('STRONG_UPTREND')
        elif current['Downtrend'] and current['EMA_20'] < df['EMA_20'].iloc[-5]:
            trend = 'DOWN'
            signals.append('STRONG_DOWNTREND')
        else:
            trend = 'NEUTRAL'
            return None, 0, ['NEUTRAL_TREND']
        
        # FILTRO ANTI-TENDENCIA
        if self.params['counter_trend_forbidden']:
            if trend == 'UP':
                if current['RSI'] < self.params['rsi_oversold']:
                    score += 2
                    signals.append('RSI_OVERSOLD')
                    signal_type = 'LONG'
                
                if current['MACD'] > current['MACD_Signal']:
                    score += 1
                    signals.append('MACD_BULLISH')
                    signal_type = 'LONG'
                    
            elif trend == 'DOWN':
                if current['RSI'] > self.params['rsi_overbought']:
                    score += 2
                    signals.append('RSI_OVERBOUGHT')
                    signal_type = 'SHORT'
                
                if current['MACD'] < current['MACD_Signal']:
                    score += 1
                    signals.append('MACD_BEARISH')
                    signal_type = 'SHORT'
        
        # Evaluar señal
        if score >= 2 and signal_type:
            confidence = min(score / 4, 0.9)
            if confidence >= self.params['min_confidence']:
                return signal_type, confidence, signals
        
        return None, 0, signals
    
    def create_paper_trade(self, symbol, signal_type, entry_price, confidence, atr, signals):
        if signal_type == 'LONG':
            stop_loss = entry_price - (atr * self.params['atr_stop_multiplier'])
            take_profit = entry_price + (atr * self.params['atr_target_multiplier'])
        else:
            stop_loss = entry_price + (atr * self.params['atr_stop_multiplier'])
            take_profit = entry_price - (atr * self.params['atr_target_multiplier'])
        
        trade = {
            'id': f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'symbol': symbol,
            'type': signal_type,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'signals': signals,
            'entry_time': datetime.now(),
            'status': 'OPEN'
        }
        
        return trade
    
    def scan_for_signals(self):
        today = datetime.now().date()
        today_trades = [t for t in self.trade_history if t.get('entry_time', datetime.now()).date() == today]
        
        if len(today_trades) >= self.params['max_daily_trades']:
            return
        
        for symbol in self.symbols:
            try:
                has_position = any(t['symbol'] == symbol for t in self.active_positions.values())
                if has_position:
                    continue
                
                df = self.get_market_data(symbol, days=30)
                if df is None:
                    continue
                
                df = self.calculate_indicators(df)
                signal_type, confidence, signals = self.generate_signal(df)
                
                if signal_type and confidence >= self.params['min_confidence']:
                    current = df.iloc[-1]
                    
                    trade = self.create_paper_trade(
                        symbol, signal_type, current['Close'], 
                        confidence, current['ATR'], signals
                    )
                    
                    self.active_positions[trade['id']] = trade
                    
                    self.logger.info(f"🎯 NEW SIGNAL: {symbol} {signal_type}")
                    
                    if self.telegram:
                        self.telegram.send_signal_alert(trade)
                    
            except Exception as e:
                self.logger.error(f"Error escaneando {symbol}: {e}")
    
    def run_trading_cycle(self):
        try:
            self.logger.info("🔄 Iniciando ciclo de trading...")
            self.system_status = "RUNNING"
            
            self.scan_for_signals()
            
            self.logger.info(f"📊 Posiciones activas: {len(self.active_positions)}")
            
        except Exception as e:
            self.logger.error(f"Error en ciclo: {e}")
            self.system_status = "ERROR"
    
    def run_forever(self):
        self.logger.info("🚀 Trading Bot V2.5 iniciado en Replit")
        
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
    
    print("🚀 INICIANDO TRADING BOT V2.5 EN REPLIT")
    
    # Servidor Flask para keepalive
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    print("🌐 Servidor Flask iniciado")
    
    # Bot de trading
    bot = TradingBotV25()
    bot.run_forever()


if __name__ == "__main__":
    main()