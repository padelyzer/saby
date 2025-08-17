#!/usr/bin/env python3
"""
Sistema de Trading Robusto V2
Rediseño completo con enfoque en robustez y consistencia
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class RobustTradingSystemV2:
    """
    Sistema simplificado y robusto con validación cruzada
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Parámetros simplificados y robustos
        self.base_params = {
            'min_confirmations': 2,        # Mínimo de confirmaciones para entrada (reducido)
            'atr_multiplier_sl': 1.5,      # Stop loss = 1.5 * ATR
            'atr_multiplier_tp': 2.5,      # Take profit = 2.5 * ATR (más realista)
            'min_atr_threshold': 0.005,    # ATR mínimo para operar (0.5% volatilidad)
            'max_atr_threshold': 0.10,     # ATR máximo para operar (10% volatilidad)
            'trend_strength_min': 0.2,     # Fuerza de tendencia mínima
            'volume_threshold': 1.1,       # Volumen mínimo vs promedio (más flexible)
            'max_positions': 1,            # Máximo de posiciones simultáneas
            'risk_per_trade': 0.015,       # 1.5% de riesgo por trade
            'min_days_between_trades': 1   # Días mínimos entre trades (más flexible)
        }
        
        # Estado del sistema
        self.trades = []
        self.positions = []
        self.last_trade_date = None
        self.market_regime = 'NEUTRAL'
        
    def detect_market_regime(self, df):
        """
        Detecta el régimen actual del mercado
        """
        if len(df) < 50:
            return 'NEUTRAL'
        
        # Calcular tendencia con EMAs
        ema_20 = df['Close'].ewm(span=20).mean().iloc[-1]
        ema_50 = df['Close'].ewm(span=50).mean().iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        # Calcular volatilidad
        returns = df['Close'].pct_change()
        volatility = returns.std() * np.sqrt(252)
        
        # Calcular ADX para fuerza de tendencia
        adx = self.calculate_adx(df)
        
        # Determinar régimen
        if adx > 25:  # Tendencia fuerte
            if current_price > ema_20 > ema_50:
                regime = 'STRONG_UPTREND'
            elif current_price < ema_20 < ema_50:
                regime = 'STRONG_DOWNTREND'
            else:
                regime = 'TRANSITIONING'
        elif adx > 15:  # Tendencia débil
            if current_price > ema_50:
                regime = 'WEAK_UPTREND'
            else:
                regime = 'WEAK_DOWNTREND'
        else:  # Rango
            if volatility > 0.3:
                regime = 'VOLATILE_RANGE'
            else:
                regime = 'TIGHT_RANGE'
        
        return regime
    
    def calculate_adx(self, df, period=14):
        """
        Calcula el ADX (Average Directional Index)
        """
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # Calculate TR (True Range)
        tr1 = pd.DataFrame(high - low)
        tr2 = pd.DataFrame(abs(high - close.shift(1)))
        tr3 = pd.DataFrame(abs(low - close.shift(1)))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = tr.rolling(period).mean()
        
        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx.iloc[-1] if not adx.empty else 0
    
    def prepare_indicators(self, df):
        """
        Prepara indicadores técnicos simplificados
        """
        
        # Indicadores de tendencia
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 1)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # ATR para volatilidad
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        df['ATR_Percent'] = df['ATR'] / df['Close']
        
        # Volumen
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA'].replace(0, 1)
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Estructura de precio
        df['Higher_High'] = (df['High'] > df['High'].shift(1)) & (df['High'].shift(1) > df['High'].shift(2))
        df['Lower_Low'] = (df['Low'] < df['Low'].shift(1)) & (df['Low'].shift(1) < df['Low'].shift(2))
        
        return df
    
    def check_entry_conditions(self, df, current_idx):
        """
        Verifica condiciones de entrada con múltiples confirmaciones
        """
        if current_idx < 50:
            return None, 0
        
        current = df.iloc[current_idx]
        prev = df.iloc[current_idx - 1]
        
        # Detectar régimen de mercado
        market_regime = self.detect_market_regime(df.iloc[:current_idx+1])
        
        # No operar en mercados desfavorables
        if market_regime in ['TIGHT_RANGE', 'VOLATILE_RANGE', 'TRANSITIONING']:
            return None, 0
        
        # Verificar volatilidad está en rango aceptable
        if current['ATR_Percent'] < self.base_params['min_atr_threshold']:
            return None, 0  # Volatilidad muy baja
        if current['ATR_Percent'] > self.base_params['max_atr_threshold']:
            return None, 0  # Volatilidad muy alta
        
        # Contar confirmaciones para LONG
        long_confirmations = 0
        long_signals = []
        
        # 1. RSI oversold con reversión
        if prev['RSI'] < 30 and current['RSI'] > prev['RSI']:
            long_confirmations += 1
            long_signals.append('RSI_REVERSAL')
        
        # 2. MACD cruce alcista
        if prev['MACD'] < prev['MACD_Signal'] and current['MACD'] > current['MACD_Signal']:
            long_confirmations += 1
            long_signals.append('MACD_CROSS')
        
        # 3. Precio sobre EMA 20
        if current['Close'] > current['EMA_20'] and prev['Close'] <= prev['EMA_20']:
            long_confirmations += 1
            long_signals.append('EMA_BREAK')
        
        # 4. Volumen alto
        if current['Volume_Ratio'] > self.base_params['volume_threshold']:
            long_confirmations += 1
            long_signals.append('VOLUME_SURGE')
        
        # 5. Bounce en Bollinger Band inferior
        if prev['Low'] <= prev['BB_Lower'] and current['Close'] > current['BB_Lower']:
            long_confirmations += 1
            long_signals.append('BB_BOUNCE')
        
        # 6. Estructura alcista
        if current['Higher_High'] and not current['Lower_Low']:
            long_confirmations += 1
            long_signals.append('BULLISH_STRUCTURE')
        
        # Contar confirmaciones para SHORT
        short_confirmations = 0
        short_signals = []
        
        # 1. RSI overbought con reversión
        if prev['RSI'] > 70 and current['RSI'] < prev['RSI']:
            short_confirmations += 1
            short_signals.append('RSI_REVERSAL')
        
        # 2. MACD cruce bajista
        if prev['MACD'] > prev['MACD_Signal'] and current['MACD'] < current['MACD_Signal']:
            short_confirmations += 1
            short_signals.append('MACD_CROSS')
        
        # 3. Precio bajo EMA 20
        if current['Close'] < current['EMA_20'] and prev['Close'] >= prev['EMA_20']:
            short_confirmations += 1
            short_signals.append('EMA_BREAK')
        
        # 4. Volumen alto
        if current['Volume_Ratio'] > self.base_params['volume_threshold']:
            short_confirmations += 1
            short_signals.append('VOLUME_SURGE')
        
        # 5. Rechazo en Bollinger Band superior
        if prev['High'] >= prev['BB_Upper'] and current['Close'] < current['BB_Upper']:
            short_confirmations += 1
            short_signals.append('BB_REJECTION')
        
        # 6. Estructura bajista
        if current['Lower_Low'] and not current['Higher_High']:
            short_confirmations += 1
            short_signals.append('BEARISH_STRUCTURE')
        
        # Verificar mínimo de confirmaciones
        min_conf = self.base_params['min_confirmations']
        
        # Ajustar requerimientos según régimen
        if 'STRONG' in market_regime:
            min_conf = max(2, min_conf - 1)  # Menos estricto en tendencias fuertes
        
        # Decidir dirección
        if long_confirmations >= min_conf and long_confirmations > short_confirmations:
            # Verificar alineación con tendencia
            if 'UPTREND' in market_regime or (market_regime == 'NEUTRAL' and current['Close'] > current['EMA_50']):
                confidence_score = long_confirmations / 6.0
                return 'LONG', confidence_score
        
        elif short_confirmations >= min_conf and short_confirmations > long_confirmations:
            # Verificar alineación con tendencia
            if 'DOWNTREND' in market_regime or (market_regime == 'NEUTRAL' and current['Close'] < current['EMA_50']):
                confidence_score = short_confirmations / 6.0
                return 'SHORT', confidence_score
        
        return None, 0
    
    def calculate_position_size(self, capital, entry_price, stop_loss_price):
        """
        Calcula tamaño de posición basado en riesgo fijo
        """
        risk_amount = capital * self.base_params['risk_per_trade']
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk > 0:
            shares = risk_amount / price_risk
            position_value = shares * entry_price
            
            # Limitar posición al 20% del capital
            max_position = capital * 0.2
            if position_value > max_position:
                shares = max_position / entry_price
            
            return shares
        
        return 0
    
    def calculate_stops(self, entry_price, signal_type, atr):
        """
        Calcula stop loss y take profit basados en ATR
        """
        if signal_type == 'LONG':
            stop_loss = entry_price - (atr * self.base_params['atr_multiplier_sl'])
            take_profit = entry_price + (atr * self.base_params['atr_multiplier_tp'])
        else:  # SHORT
            stop_loss = entry_price + (atr * self.base_params['atr_multiplier_sl'])
            take_profit = entry_price - (atr * self.base_params['atr_multiplier_tp'])
        
        return stop_loss, take_profit
    
    def check_exit_conditions(self, position, current, atr):
        """
        Verifica condiciones de salida incluyendo trailing stop
        """
        exit_signal = False
        exit_price = current['Close']
        exit_reason = None
        
        # Check stop loss y take profit básicos
        if position['type'] == 'LONG':
            if current['Low'] <= position['stop_loss']:
                exit_signal = True
                exit_price = position['stop_loss']
                exit_reason = 'STOP_LOSS'
            elif current['High'] >= position['take_profit']:
                exit_signal = True
                exit_price = position['take_profit']
                exit_reason = 'TAKE_PROFIT'
            else:
                # Trailing stop si estamos en profit
                if current['Close'] > position['entry_price']:
                    trailing_stop = current['Close'] - (atr * self.base_params['atr_multiplier_sl'])
                    if trailing_stop > position['stop_loss']:
                        position['stop_loss'] = trailing_stop
                
                # Salida por señal contraria fuerte
                if current['RSI'] > 75 and current['MACD'] < current['MACD_Signal']:
                    exit_signal = True
                    exit_reason = 'REVERSAL_SIGNAL'
        
        else:  # SHORT
            if current['High'] >= position['stop_loss']:
                exit_signal = True
                exit_price = position['stop_loss']
                exit_reason = 'STOP_LOSS'
            elif current['Low'] <= position['take_profit']:
                exit_signal = True
                exit_price = position['take_profit']
                exit_reason = 'TAKE_PROFIT'
            else:
                # Trailing stop si estamos en profit
                if current['Close'] < position['entry_price']:
                    trailing_stop = current['Close'] + (atr * self.base_params['atr_multiplier_sl'])
                    if trailing_stop < position['stop_loss']:
                        position['stop_loss'] = trailing_stop
                
                # Salida por señal contraria fuerte
                if current['RSI'] < 25 and current['MACD'] > current['MACD_Signal']:
                    exit_signal = True
                    exit_reason = 'REVERSAL_SIGNAL'
        
        return exit_signal, exit_price, exit_reason
    
    def backtest(self, symbol, start_date, end_date):
        """
        Ejecuta backtest para un símbolo y período
        """
        # Obtener datos
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1d')
        
        if len(df) < 50:
            return []
        
        # Preparar indicadores
        df = self.prepare_indicators(df)
        
        # Reset estado
        self.trades = []
        self.current_capital = self.initial_capital
        position = None
        
        # Iterar por los datos
        for i in range(50, len(df)):
            current = df.iloc[i]
            
            # Si no hay posición, buscar entrada
            if position is None:
                # Verificar si ha pasado suficiente tiempo desde último trade
                if self.last_trade_date:
                    days_since_last = (current.name - self.last_trade_date).days
                    if days_since_last < self.base_params['min_days_between_trades']:
                        continue
                
                # Verificar condiciones de entrada
                signal_type, confidence = self.check_entry_conditions(df, i)
                
                if signal_type and confidence > 0.3:  # Requiere confianza mínima (reducida)
                    # Calcular stops
                    atr = current['ATR']
                    stop_loss, take_profit = self.calculate_stops(
                        current['Close'], signal_type, atr
                    )
                    
                    # Calcular tamaño de posición
                    shares = self.calculate_position_size(
                        self.current_capital, current['Close'], stop_loss
                    )
                    
                    if shares > 0:
                        # Abrir posición
                        position = {
                            'symbol': symbol,
                            'type': signal_type,
                            'entry_date': current.name,
                            'entry_price': current['Close'],
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'shares': shares,
                            'confidence': confidence,
                            'entry_atr': atr,
                            'market_regime': self.detect_market_regime(df.iloc[:i+1])
                        }
                        
                        self.last_trade_date = current.name
            
            # Si hay posición, verificar salida
            else:
                exit_signal, exit_price, exit_reason = self.check_exit_conditions(
                    position, current, current['ATR']
                )
                
                if exit_signal:
                    # Cerrar posición
                    position['exit_date'] = current.name
                    position['exit_price'] = exit_price
                    position['exit_reason'] = exit_reason
                    
                    # Calcular P&L
                    if position['type'] == 'LONG':
                        position['pnl'] = (exit_price - position['entry_price']) * position['shares']
                        position['return_pct'] = ((exit_price / position['entry_price']) - 1) * 100
                    else:
                        position['pnl'] = (position['entry_price'] - exit_price) * position['shares']
                        position['return_pct'] = ((position['entry_price'] / exit_price) - 1) * 100
                    
                    position['duration_days'] = (position['exit_date'] - position['entry_date']).days
                    
                    # Actualizar capital
                    self.current_capital += position['pnl']
                    
                    # Guardar trade
                    self.trades.append(position)
                    position = None
        
        # Cerrar posición final si queda abierta
        if position and len(df) > 0:
            last = df.iloc[-1]
            position['exit_date'] = last.name
            position['exit_price'] = last['Close']
            position['exit_reason'] = 'END_PERIOD'
            
            if position['type'] == 'LONG':
                position['pnl'] = (position['exit_price'] - position['entry_price']) * position['shares']
                position['return_pct'] = ((position['exit_price'] / position['entry_price']) - 1) * 100
            else:
                position['pnl'] = (position['entry_price'] - position['exit_price']) * position['shares']
                position['return_pct'] = ((position['entry_price'] / position['exit_price']) - 1) * 100
            
            position['duration_days'] = (position['exit_date'] - position['entry_date']).days
            self.trades.append(position)
        
        return self.trades
    
    def calculate_metrics(self, trades):
        """
        Calcula métricas de performance
        """
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'total_return': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'avg_duration': 0
            }
        
        # Métricas básicas
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        
        # Profit factor
        total_wins = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Returns
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (total_pnl / self.initial_capital) * 100
        
        # Average win/loss
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        # Duration
        avg_duration = np.mean([t['duration_days'] for t in trades])
        
        # Sharpe Ratio (simplified)
        returns = [t['return_pct'] for t in trades]
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / (np.std(returns) + 0.0001) * np.sqrt(252/avg_duration)
        else:
            sharpe_ratio = 0
        
        # Max Drawdown
        cumulative_pnl = []
        cum_sum = 0
        for t in sorted(trades, key=lambda x: x['entry_date']):
            cum_sum += t['pnl']
            cumulative_pnl.append(cum_sum)
        
        if cumulative_pnl:
            peak = cumulative_pnl[0]
            max_dd = 0
            for value in cumulative_pnl:
                peak = max(peak, value)
                dd = (peak - value) / (peak if peak > 0 else 1) * 100
                max_dd = max(max_dd, dd)
        else:
            max_dd = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_dd,
            'total_return': total_return,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_duration': avg_duration,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades)
        }

def test_robust_system():
    """
    Prueba el sistema robusto con múltiples períodos
    """
    print("🚀 TESTING ROBUST TRADING SYSTEM V2")
    print("="*80)
    
    system = RobustTradingSystemV2(initial_capital=10000)
    
    # Períodos de prueba diversos
    test_periods = [
        {'name': '2024_YTD', 'start': '2024-01-01', 'end': '2024-11-15'},
        {'name': 'Q4_2023', 'start': '2023-10-01', 'end': '2023-12-31'},
        {'name': 'Q3_2023', 'start': '2023-07-01', 'end': '2023-09-30'},
    ]
    
    all_trades = []
    
    for period in test_periods:
        print(f"\n📅 Testing Period: {period['name']}")
        print(f"   {period['start']} → {period['end']}")
        
        # Test con BTC
        trades = system.backtest('BTC-USD', period['start'], period['end'])
        all_trades.extend(trades)
        
        if trades:
            metrics = system.calculate_metrics(trades)
            print(f"\n   📊 Results:")
            print(f"   • Trades: {metrics['total_trades']}")
            print(f"   • Win Rate: {metrics['win_rate']:.1f}%")
            print(f"   • Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"   • Total Return: {metrics['total_return']:.1f}%")
            print(f"   • Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"   • Max Drawdown: {metrics['max_drawdown']:.1f}%")
        else:
            print("   ❌ No trades generated")
    
    # Métricas globales
    if all_trades:
        print("\n" + "="*80)
        print("📊 OVERALL PERFORMANCE")
        print("="*80)
        
        global_metrics = system.calculate_metrics(all_trades)
        
        print(f"Total Trades: {global_metrics['total_trades']}")
        print(f"Win Rate: {global_metrics['win_rate']:.1f}%")
        print(f"Profit Factor: {global_metrics['profit_factor']:.2f}")
        print(f"Sharpe Ratio: {global_metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {global_metrics['max_drawdown']:.1f}%")
        print(f"Total Return: {global_metrics['total_return']:.1f}%")
        print(f"Average Win: ${global_metrics['avg_win']:.2f}")
        print(f"Average Loss: ${global_metrics['avg_loss']:.2f}")
        print(f"Avg Duration: {global_metrics['avg_duration']:.1f} days")
        
        # Evaluación
        print("\n🎯 SYSTEM EVALUATION:")
        if global_metrics['win_rate'] >= 45 and global_metrics['profit_factor'] >= 1.3:
            print("✅ System shows promise - Continue with optimization")
        elif global_metrics['win_rate'] >= 40 and global_metrics['profit_factor'] >= 1.0:
            print("⚠️ System needs refinement - Adjust parameters")
        else:
            print("❌ System underperforming - Major changes needed")
    
    return all_trades

if __name__ == "__main__":
    trades = test_robust_system()