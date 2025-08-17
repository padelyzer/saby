#!/usr/bin/env python3
"""
Trading Bot V2.5 - Sistema principal para Render con Telegram
Integra todo: trading logic + notifications + logging
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import os
import logging
import requests
import warnings
warnings.filterwarnings('ignore')

class TelegramNotifier:
    """Notificador de Telegram integrado"""
    
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message, parse_mode="HTML"):
        """Envía mensaje a Telegram"""
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
        """Alerta de nueva señal"""
        signal_emoji = "🟢" if trade_data['type'] == 'LONG' else "🔴"
        
        message = f"""
{signal_emoji} <b>NUEVA SEÑAL</b>

📊 <b>Símbolo:</b> {trade_data['symbol']}
📈 <b>Tipo:</b> {trade_data['type']}
💰 <b>Entry:</b> ${trade_data['entry_price']:,.2f}
🎯 <b>Confianza:</b> {trade_data['confidence']:.1%}

🛡️ <b>Stop Loss:</b> ${trade_data['stop_loss']:,.2f}
🎊 <b>Take Profit:</b> ${trade_data['take_profit']:,.2f}

🔍 <b>Señales:</b> {', '.join(trade_data['signals'][:3])}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_message(message)
    
    def send_trade_close(self, trade_data):
        """Alerta de trade cerrado"""
        result_emoji = "✅" if trade_data['pnl'] > 0 else "❌"
        duration = (trade_data['exit_time'] - trade_data['entry_time']).total_seconds() / 3600
        
        message = f"""
{result_emoji} <b>TRADE CERRADO</b>

📊 <b>Símbolo:</b> {trade_data['symbol']}
📈 <b>Resultado:</b> {trade_data['exit_reason']}
💰 <b>P&L:</b> ${trade_data['pnl']:,.2f} ({trade_data['pnl_pct']:+.2f}%)
🕐 <b>Duración:</b> {duration:.1f}h

📍 <b>Entry → Exit:</b> ${trade_data['entry_price']:,.2f} → ${trade_data['exit_price']:,.2f}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_message(message)
    
    def send_system_status(self, status, stats=None):
        """Status del sistema"""
        if status == "STARTED":
            message = f"""
🚀 <b>BOT INICIADO</b>

✅ Sistema V2.5 funcionando
💰 Capital inicial: $10,000
🎯 Símbolos: BTC, ETH, SOL, BNB, ADA
📊 Parámetros validados (70% WR)

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        elif status == "DAILY_SUMMARY" and stats:
            status_emoji = "📈" if stats['total_pnl'] > 0 else "📉"
            message = f"""
{status_emoji} <b>RESUMEN DIARIO</b>

💰 <b>P&L Total:</b> ${stats['total_pnl']:,.2f}
📈 <b>ROI:</b> {stats['roi']:+.2f}%
🎯 <b>Win Rate:</b> {stats['win_rate']:.1f}%
📊 <b>Trades:</b> {stats['total_trades']}
⚡ <b>Profit Factor:</b> {stats['profit_factor']:.2f}
💼 <b>Capital:</b> ${stats['current_capital']:,.2f}

🤖 Trading Bot V2.5
            """.strip()
        else:
            message = f"ℹ️ <b>SISTEMA:</b> {status}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        return self.send_message(message)


class TradingBotV25:
    """
    Sistema principal de trading V2.5 para Render
    """
    
    def __init__(self):
        self.initial_capital = 10000
        self.current_capital = self.initial_capital
        
        # Parámetros V2.5 validados
        self.params = {
            'rsi_oversold': 40,
            'rsi_overbought': 60,
            'atr_stop_multiplier': 2.0,
            'atr_target_multiplier': 3.0,
            'counter_trend_forbidden': True,
            'min_confidence': 0.20,
            'risk_per_trade': 0.01,
            'max_daily_trades': 5,
            'check_interval_minutes': 15,
        }
        
        # Configuración
        self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
        self.active_positions = {}
        self.trade_history = []
        
        # Setup logging
        self.setup_logging()
        
        # Setup Telegram
        self.setup_telegram()
        
        # Estado
        self.last_check = None
        self.system_status = "STARTING"
        self.last_daily_report = None
    
    def setup_logging(self):
        """Configura logging para Render"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        """Configura Telegram usando variables de entorno"""
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            self.telegram = TelegramNotifier(bot_token, chat_id)
            self.logger.info("✅ Telegram configurado correctamente")
        else:
            self.telegram = None
            self.logger.warning("⚠️ Telegram no configurado - faltan variables de entorno")
    
    def get_market_data(self, symbol, days=30):
        """Obtiene datos de mercado"""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(df) < 20:
                return None
            
            return df
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de {symbol}: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Calcula indicadores V2.5"""
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
        """Genera señal V2.5"""
        if len(df) < 20:
            return None, 0, []
        
        current = df.iloc[-1]
        
        score = 0
        signals = []
        signal_type = None
        
        # Tendencia
        if current['Uptrend']:
            trend = 'UP'
            signals.append('UPTREND')
        elif current['Downtrend']:
            trend = 'DOWN'
            signals.append('DOWNTREND')
        else:
            trend = 'NEUTRAL'
            signals.append('NEUTRAL')
        
        # FILTRO ANTI-TENDENCIA (CRÍTICO)
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
                
                if current['Close'] > current['EMA_20']:
                    score += 1
                    signals.append('ABOVE_EMA20')
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
                
                if current['Close'] < current['EMA_20']:
                    score += 1
                    signals.append('BELOW_EMA20')
                    signal_type = 'SHORT'
        
        # Evaluar señal
        if score >= 2 and signal_type:
            confidence = min(score / 4, 0.9)
            if confidence >= self.params['min_confidence']:
                return signal_type, confidence, signals
        
        return None, 0, signals
    
    def create_paper_trade(self, symbol, signal_type, entry_price, confidence, atr, signals):
        """Crea paper trade"""
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
            'status': 'OPEN',
            'exit_price': None,
            'exit_time': None,
            'exit_reason': None,
            'pnl': 0
        }
        
        return trade
    
    def check_exit_conditions(self, trade, current_price):
        """Verifica condiciones de salida"""
        if trade['type'] == 'LONG':
            if current_price <= trade['stop_loss']:
                return True, current_price, "STOP_LOSS"
            elif current_price >= trade['take_profit']:
                return True, current_price, "TAKE_PROFIT"
        else:
            if current_price >= trade['stop_loss']:
                return True, current_price, "STOP_LOSS"
            elif current_price <= trade['take_profit']:
                return True, current_price, "TAKE_PROFIT"
        
        return False, None, None
    
    def close_trade(self, trade, exit_price, exit_reason):
        """Cierra paper trade"""
        trade['exit_price'] = exit_price
        trade['exit_time'] = datetime.now()
        trade['exit_reason'] = exit_reason
        trade['status'] = 'CLOSED'
        
        # Calcular P&L
        if trade['type'] == 'LONG':
            pnl_pct = ((exit_price / trade['entry_price']) - 1) * 100
        else:
            pnl_pct = ((trade['entry_price'] / exit_price) - 1) * 100
        
        trade['pnl_pct'] = pnl_pct
        trade['pnl'] = self.current_capital * self.params['risk_per_trade'] * pnl_pct
        
        # Actualizar capital
        self.current_capital += trade['pnl']
        
        # Mover a historial
        self.trade_history.append(trade)
        
        return trade
    
    def get_system_stats(self):
        """Calcula estadísticas"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'roi': 0,
                'current_capital': self.current_capital
            }
        
        total_trades = len(self.trade_history)
        wins = sum(1 for t in self.trade_history if t['pnl'] > 0)
        win_rate = (wins / total_trades) * 100
        
        total_pnl = sum(t['pnl'] for t in self.trade_history)
        roi = ((self.current_capital / self.initial_capital) - 1) * 100
        
        gross_wins = sum(t['pnl'] for t in self.trade_history if t['pnl'] > 0)
        gross_losses = abs(sum(t['pnl'] for t in self.trade_history if t['pnl'] <= 0))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'roi': roi,
            'current_capital': self.current_capital
        }
    
    def check_active_positions(self):
        """Revisa posiciones activas"""
        positions_to_close = []
        
        for trade_id, trade in self.active_positions.items():
            try:
                ticker = yf.Ticker(trade['symbol'])
                current_data = ticker.history(period="1d", interval="5m")
                
                if len(current_data) > 0:
                    current_price = current_data['Close'].iloc[-1]
                    
                    should_exit, exit_price, exit_reason = self.check_exit_conditions(trade, current_price)
                    
                    if should_exit:
                        closed_trade = self.close_trade(trade, exit_price, exit_reason)
                        positions_to_close.append(trade_id)
                        
                        # Log y Telegram
                        pnl_indicator = "✅" if closed_trade['pnl'] > 0 else "❌"
                        self.logger.info(f"{pnl_indicator} {closed_trade['symbol']} {closed_trade['type']} CLOSED | {exit_reason} | P&L: ${closed_trade['pnl']:.2f}")
                        
                        if self.telegram:
                            self.telegram.send_trade_close(closed_trade)
                        
            except Exception as e:
                self.logger.error(f"Error revisando posición {trade_id}: {e}")
        
        for trade_id in positions_to_close:
            del self.active_positions[trade_id]
    
    def scan_for_signals(self):
        """Escanea símbolos"""
        today = datetime.now().date()
        today_trades = [t for t in self.trade_history if t['entry_time'].date() == today]
        
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
                    
                    # Log y Telegram
                    self.logger.info(f"🎯 NEW SIGNAL: {symbol} {signal_type} | Entry: ${current['Close']:.2f} | Conf: {confidence:.1%}")
                    
                    if self.telegram:
                        self.telegram.send_signal_alert(trade)
                    
            except Exception as e:
                self.logger.error(f"Error escaneando {symbol}: {e}")
    
    def send_daily_summary(self):
        """Envía resumen diario"""
        today = datetime.now().date()
        
        if self.last_daily_report == today:
            return
        
        stats = self.get_system_stats()
        
        if self.telegram:
            self.telegram.send_system_status("DAILY_SUMMARY", stats)
        
        self.last_daily_report = today
        self.logger.info(f"📊 Resumen diario enviado - P&L: ${stats['total_pnl']:.2f}")
    
    def run_trading_cycle(self):
        """Ciclo principal de trading"""
        try:
            self.logger.info("🔄 Iniciando ciclo de trading...")
            self.system_status = "RUNNING"
            
            # 1. Revisar posiciones
            self.check_active_positions()
            
            # 2. Buscar señales
            self.scan_for_signals()
            
            # 3. Stats
            stats = self.get_system_stats()
            self.logger.info(f"📊 Stats: {stats['total_trades']} trades, {stats['win_rate']:.1f}% WR, ${stats['total_pnl']:.2f} P&L")
            
            # 4. Resumen diario (una vez al día)
            if datetime.now().hour == 9 and datetime.now().minute <= 15:  # 9:00-9:15 AM
                self.send_daily_summary()
            
            self.last_check = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error en ciclo: {e}")
            self.system_status = "ERROR"
    
    def run_forever(self):
        """Loop principal para Render"""
        self.logger.info("🚀 Trading Bot V2.5 iniciado en Render")
        
        if self.telegram:
            self.telegram.send_system_status("STARTED")
        
        while True:
            try:
                self.run_trading_cycle()
                
                wait_minutes = self.params['check_interval_minutes']
                self.logger.info(f"⏱️ Esperando {wait_minutes} minutos...")
                time.sleep(wait_minutes * 60)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Bot detenido por usuario")
                break
            except Exception as e:
                self.logger.error(f"Error crítico: {e}")
                time.sleep(60)


def main():
    """Función principal para Render"""
    bot = TradingBotV25()
    bot.run_forever()


if __name__ == "__main__":
    main()