#!/usr/bin/env python3
"""
Sistema V2.5 para Render - Paper Trading 24/7
Backend que corre continuamente en Render
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import os
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import warnings
warnings.filterwarnings('ignore')

class RenderTradingBot:
    """
    Sistema V2.5 optimizado para Render deployment
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
            'check_interval_minutes': 15,  # Revisar cada 15 minutos
        }
        
        # Configuración
        self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
        self.active_positions = {}
        self.daily_trades = []
        self.trade_history = []
        
        # Setup logging
        self.setup_logging()
        
        # Estado del sistema
        self.last_check = None
        self.system_status = "STARTING"
        
    def setup_logging(self):
        """Configura logging para Render"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),  # Para Render logs
                logging.FileHandler('trading_bot.log') if os.path.exists('.') else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_market_data(self, symbol, days=30):
        """Obtiene datos de mercado con manejo de errores"""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(df) < 20:
                self.logger.warning(f"Datos insuficientes para {symbol}")
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
        
        # EMAs para tendencia
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
        """Genera señal V2.5 para el último dato"""
        if len(df) < 20:
            return None, 0, []
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0
        signals = []
        signal_type = None
        
        # Determinar tendencia
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
                # Solo LONG en uptrend
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
                # Solo SHORT en downtrend
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
        if score >= 2 and signal_type:  # Min score = 2
            confidence = min(score / 4, 0.9)
            if confidence >= self.params['min_confidence']:
                return signal_type, confidence, signals
        
        return None, 0, signals
    
    def create_paper_trade(self, symbol, signal_type, entry_price, confidence, atr, signals):
        """Crea un paper trade"""
        # Calcular stops V2.5
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
        """Verifica condiciones de salida para paper trade"""
        if trade['type'] == 'LONG':
            if current_price <= trade['stop_loss']:
                return True, current_price, "STOP_LOSS"
            elif current_price >= trade['take_profit']:
                return True, current_price, "TAKE_PROFIT"
        else:  # SHORT
            if current_price >= trade['stop_loss']:
                return True, current_price, "STOP_LOSS"
            elif current_price <= trade['take_profit']:
                return True, current_price, "TAKE_PROFIT"
        
        return False, None, None
    
    def close_trade(self, trade, exit_price, exit_reason):
        """Cierra un paper trade y calcula P&L"""
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
    
    def send_alert(self, message, trade_data=None):
        """Envía alertas (email, webhook, etc.)"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Log principal
        self.logger.info(f"ALERT: {message}")
        
        # Aquí puedes agregar:
        # - Email notifications
        # - Telegram bot
        # - Discord webhook
        # - Slack webhook
        
        try:
            # Ejemplo: Webhook simple (reemplaza con tu URL)
            webhook_url = os.getenv('WEBHOOK_URL')
            if webhook_url:
                payload = {
                    'timestamp': timestamp,
                    'message': message,
                    'trade_data': trade_data,
                    'system_status': self.system_status,
                    'current_capital': self.current_capital
                }
                requests.post(webhook_url, json=payload, timeout=10)
        except Exception as e:
            self.logger.error(f"Error enviando webhook: {e}")
    
    def get_system_stats(self):
        """Calcula estadísticas del sistema"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'roi': 0
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
            'current_capital': self.current_capital,
            'active_positions': len(self.active_positions)
        }
    
    def run_trading_cycle(self):
        """Ejecuta un ciclo completo de trading"""
        try:
            self.logger.info("🔄 Iniciando ciclo de trading...")
            self.system_status = "RUNNING"
            
            # 1. Revisar posiciones activas
            self.check_active_positions()
            
            # 2. Buscar nuevas señales
            self.scan_for_signals()
            
            # 3. Logging de estado
            stats = self.get_system_stats()
            self.logger.info(f"📊 Stats: {stats['total_trades']} trades, {stats['win_rate']:.1f}% WR, ${stats['total_pnl']:.2f} P&L")
            
            self.last_check = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error en ciclo de trading: {e}")
            self.system_status = "ERROR"
    
    def check_active_positions(self):
        """Revisa posiciones activas para cerrar"""
        positions_to_close = []
        
        for trade_id, trade in self.active_positions.items():
            try:
                # Obtener precio actual
                ticker = yf.Ticker(trade['symbol'])
                current_data = ticker.history(period="1d", interval="1m")
                
                if len(current_data) > 0:
                    current_price = current_data['Close'].iloc[-1]
                    
                    # Verificar condiciones de salida
                    should_exit, exit_price, exit_reason = self.check_exit_conditions(trade, current_price)
                    
                    if should_exit:
                        # Cerrar trade
                        closed_trade = self.close_trade(trade, exit_price, exit_reason)
                        positions_to_close.append(trade_id)
                        
                        # Enviar alerta
                        pnl_indicator = "✅" if closed_trade['pnl'] > 0 else "❌"
                        message = f"{pnl_indicator} {closed_trade['symbol']} {closed_trade['type']} CLOSED"
                        message += f" | {exit_reason} | P&L: ${closed_trade['pnl']:.2f}"
                        
                        self.send_alert(message, closed_trade)
                        
            except Exception as e:
                self.logger.error(f"Error revisando posición {trade_id}: {e}")
        
        # Remover posiciones cerradas
        for trade_id in positions_to_close:
            del self.active_positions[trade_id]
    
    def scan_for_signals(self):
        """Escanea símbolos buscando nuevas señales"""
        # Verificar límite diario
        today = datetime.now().date()
        today_trades = [t for t in self.trade_history if t['entry_time'].date() == today]
        
        if len(today_trades) >= self.params['max_daily_trades']:
            self.logger.info(f"Límite diario alcanzado: {len(today_trades)} trades")
            return
        
        for symbol in self.symbols:
            try:
                # Verificar si ya tenemos posición en este símbolo
                has_position = any(t['symbol'] == symbol for t in self.active_positions.values())
                if has_position:
                    continue
                
                # Obtener datos
                df = self.get_market_data(symbol, days=30)
                if df is None:
                    continue
                
                df = self.calculate_indicators(df)
                
                # Generar señal
                signal_type, confidence, signals = self.generate_signal(df)
                
                if signal_type and confidence >= self.params['min_confidence']:
                    current = df.iloc[-1]
                    
                    # Crear paper trade
                    trade = self.create_paper_trade(
                        symbol, signal_type, current['Close'], 
                        confidence, current['ATR'], signals
                    )
                    
                    # Agregar a posiciones activas
                    self.active_positions[trade['id']] = trade
                    
                    # Enviar alerta
                    message = f"🎯 NEW SIGNAL: {symbol} {signal_type}"
                    message += f" | Entry: ${current['Close']:.2f} | Conf: {confidence:.1%}"
                    message += f" | Signals: {', '.join(signals[:3])}"
                    
                    self.send_alert(message, trade)
                    
                    self.logger.info(f"📈 Nueva posición: {trade['id']}")
                    
            except Exception as e:
                self.logger.error(f"Error escaneando {symbol}: {e}")
    
    def run_forever(self):
        """Loop principal para Render"""
        self.logger.info("🚀 Trading Bot V2.5 iniciado en Render")
        self.send_alert("🚀 Trading Bot V2.5 STARTED", self.get_system_stats())
        
        while True:
            try:
                # Ejecutar ciclo de trading
                self.run_trading_cycle()
                
                # Esperar intervalo configurado
                wait_minutes = self.params['check_interval_minutes']
                self.logger.info(f"⏱️ Esperando {wait_minutes} minutos...")
                time.sleep(wait_minutes * 60)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Bot detenido por usuario")
                self.send_alert("🛑 Trading Bot STOPPED", self.get_system_stats())
                break
            except Exception as e:
                self.logger.error(f"Error crítico: {e}")
                self.system_status = "ERROR"
                time.sleep(60)  # Esperar 1 minuto antes de reintentar


def main():
    """Función principal para Render"""
    bot = RenderTradingBot()
    bot.run_forever()


if __name__ == "__main__":
    main()