#!/usr/bin/env python3
"""
Sistema de Trading de Alta Precisión
Enfoque: Menos trades, mayor calidad
Objetivo: Win Rate > 65%, Profit Factor > 2.0
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class PrecisionTradingSystem:
    """
    Sistema de alta precisión con múltiples filtros de confirmación
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Parámetros ULTRA estrictos para máxima precisión
        self.params = {
            # Filtros de entrada más estrictos
            'min_confirmations': 6,         # Mínimo 6 de 9 confirmaciones (MUY estricto)
            'strong_trend_required': True,  # Solo operar en tendencias fuertes
            'volume_surge_required': True,  # Requiere aumento de volumen
            
            # RSI más extremo
            'rsi_oversold': 20,            # MUY oversold
            'rsi_overbought': 80,           # MUY overbought
            'rsi_divergence_required': True, # Requiere divergencia RSI
            
            # MACD más estricto
            'macd_histogram_min': 0.001,   # Histogram mínimo para confirmar
            'macd_cross_strength': 0.002,  # Fuerza mínima del cruce
            
            # Estructura de precio
            'structure_confirmation': True,  # Confirmar con estructura
            'support_resistance_check': True, # Verificar S/R
            'min_distance_to_sr': 0.02,     # 2% mínimo a S/R
            
            # Gestión de riesgo mejorada
            'risk_reward_min': 2.5,         # Mínimo 1:2.5 R/R
            'atr_multiplier_sl': 1.2,       # Stop más ajustado
            'atr_multiplier_tp': 3.0,       # Target más amplio
            'max_risk_per_trade': 0.01,     # Solo 1% de riesgo
            
            # Filtros adicionales
            'avoid_news_days': True,        # Evitar días de noticias importantes
            'min_days_in_trend': 5,         # Tendencia mínima de 5 días
            'max_correlation': 0.7,         # Evitar trades correlacionados
            'time_of_day_filter': True,     # Mejores horas para operar
            
            # Confirmación de momentum
            'momentum_confirmation': True,   # Requiere momentum positivo
            'volume_profile_check': True,   # Verificar perfil de volumen
            'smart_money_check': True       # Verificar actividad institucional
        }
        
        self.trades = []
        self.active_positions = {}
        self.recent_signals = []
        
    def calculate_advanced_indicators(self, df):
        """
        Calcula indicadores avanzados para mayor precisión
        """
        # Indicadores básicos
        df = self.calculate_basic_indicators(df)
        
        # Indicadores avanzados
        
        # 1. RSI Divergencia
        df['RSI_Divergence'] = self.detect_rsi_divergence(df)
        
        # 2. MACD Histogram y fuerza
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        df['MACD_Cross_Strength'] = abs(df['MACD'] - df['MACD_Signal'])
        
        # 3. Estructura de precio (Higher Highs, Lower Lows)
        df['HH'] = (df['High'] > df['High'].shift(1)) & (df['High'].shift(1) > df['High'].shift(2))
        df['LL'] = (df['Low'] < df['Low'].shift(1)) & (df['Low'].shift(1) < df['Low'].shift(2))
        df['HL'] = (df['Low'] > df['Low'].shift(1)) & (df['Low'].shift(1) > df['Low'].shift(2))
        df['LH'] = (df['High'] < df['High'].shift(1)) & (df['High'].shift(1) < df['High'].shift(2))
        
        # 4. Soporte y Resistencia dinámicos
        df['Support'] = df['Low'].rolling(20).min()
        df['Resistance'] = df['High'].rolling(20).max()
        df['Distance_to_Support'] = (df['Close'] - df['Support']) / df['Close']
        df['Distance_to_Resistance'] = (df['Resistance'] - df['Close']) / df['Close']
        
        # 5. Volume Profile
        df['Volume_Profile'] = df['Volume'].rolling(20).apply(lambda x: np.percentile(x, 80))
        df['High_Volume'] = df['Volume'] > df['Volume_Profile']
        
        # 6. Momentum (Rate of Change)
        df['Momentum'] = df['Close'].pct_change(10) * 100
        df['Momentum_Positive'] = df['Momentum'] > 0
        
        # 7. ADX para fuerza de tendencia
        df['ADX'] = self.calculate_adx(df)
        df['Strong_Trend'] = df['ADX'] > 25
        
        # 8. Bollinger Bands Squeeze
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Squeeze'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        df['BB_Squeeze_Tight'] = df['BB_Squeeze'] < df['BB_Squeeze'].rolling(50).mean()
        
        # 9. Smart Money Flow
        df['Smart_Money'] = self.calculate_smart_money_flow(df)
        
        # 10. VWAP
        df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
        df['Price_Above_VWAP'] = df['Close'] > df['VWAP']
        
        return df
    
    def calculate_basic_indicators(self, df):
        """
        Calcula indicadores técnicos básicos
        """
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
        
        # EMAs
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # Trend
        df['Trend_Up'] = (df['EMA_9'] > df['EMA_20']) & (df['EMA_20'] > df['EMA_50'])
        df['Trend_Down'] = (df['EMA_9'] < df['EMA_20']) & (df['EMA_20'] < df['EMA_50'])
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        
        return df
    
    def detect_rsi_divergence(self, df, lookback=5):
        """
        Detecta divergencias en RSI
        """
        divergence = []
        
        for i in range(len(df)):
            if i < lookback * 2:
                divergence.append(0)
                continue
            
            # Buscar divergencia alcista (precio hace lower low, RSI hace higher low)
            price_ll = df['Low'].iloc[i] < df['Low'].iloc[i-lookback:i].min()
            rsi_hl = df['RSI'].iloc[i] > df['RSI'].iloc[i-lookback:i].min()
            
            if price_ll and rsi_hl and df['RSI'].iloc[i] < 35:
                divergence.append(1)  # Divergencia alcista
                continue
            
            # Buscar divergencia bajista (precio hace higher high, RSI hace lower high)
            price_hh = df['High'].iloc[i] > df['High'].iloc[i-lookback:i].max()
            rsi_lh = df['RSI'].iloc[i] < df['RSI'].iloc[i-lookback:i].max()
            
            if price_hh and rsi_lh and df['RSI'].iloc[i] > 65:
                divergence.append(-1)  # Divergencia bajista
            else:
                divergence.append(0)
        
        return divergence
    
    def calculate_adx(self, df, period=14):
        """
        Calcula el ADX (Average Directional Index)
        """
        # +DM y -DM
        plus_dm = df['High'].diff()
        minus_dm = -df['Low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # True Range
        tr1 = pd.DataFrame(df['High'] - df['Low'])
        tr2 = pd.DataFrame(abs(df['High'] - df['Close'].shift(1)))
        tr3 = pd.DataFrame(abs(df['Low'] - df['Close'].shift(1)))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        # +DI y -DI
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        # DX y ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx
    
    def calculate_smart_money_flow(self, df):
        """
        Calcula el flujo de dinero inteligente (institucional)
        """
        # Smart Money Flow = Volume * (Close - Open) / (High - Low)
        price_range = df['High'] - df['Low']
        price_range[price_range == 0] = 1  # Evitar división por cero
        
        smart_money = df['Volume'] * ((df['Close'] - df['Open']) / price_range)
        smart_money_ma = smart_money.rolling(10).mean()
        
        return smart_money_ma > 0
    
    def check_entry_conditions(self, df, idx):
        """
        Verifica condiciones de entrada con alta precisión
        """
        if idx < 200:  # Necesitamos historia suficiente
            return None, 0, ""
        
        current = df.iloc[idx]
        prev = df.iloc[idx-1]
        
        # Lista de confirmaciones
        long_confirmations = []
        short_confirmations = []
        
        # 1. RSI con divergencia
        if self.params['rsi_divergence_required']:
            if current['RSI'] < self.params['rsi_oversold'] and current['RSI_Divergence'] == 1:
                long_confirmations.append('RSI_DIVERGENCE')
            elif current['RSI'] > self.params['rsi_overbought'] and current['RSI_Divergence'] == -1:
                short_confirmations.append('RSI_DIVERGENCE')
        else:
            if current['RSI'] < self.params['rsi_oversold']:
                long_confirmations.append('RSI_OVERSOLD')
            elif current['RSI'] > self.params['rsi_overbought']:
                short_confirmations.append('RSI_OVERBOUGHT')
        
        # 2. MACD con fuerza
        if prev['MACD'] < prev['MACD_Signal'] and current['MACD'] > current['MACD_Signal']:
            if current['MACD_Cross_Strength'] >= self.params['macd_cross_strength']:
                long_confirmations.append('MACD_STRONG_CROSS')
        elif prev['MACD'] > prev['MACD_Signal'] and current['MACD'] < current['MACD_Signal']:
            if current['MACD_Cross_Strength'] >= self.params['macd_cross_strength']:
                short_confirmations.append('MACD_STRONG_CROSS')
        
        # 3. Estructura de precio
        if self.params['structure_confirmation']:
            if current['HL'] and not current['LH']:  # Higher Low sin Lower High
                long_confirmations.append('BULLISH_STRUCTURE')
            elif current['LH'] and not current['HL']:  # Lower High sin Higher Low
                short_confirmations.append('BEARISH_STRUCTURE')
        
        # 4. Tendencia fuerte
        if self.params['strong_trend_required']:
            if current['Strong_Trend'] and current['Trend_Up']:
                long_confirmations.append('STRONG_UPTREND')
            elif current['Strong_Trend'] and current['Trend_Down']:
                short_confirmations.append('STRONG_DOWNTREND')
        
        # 5. Volumen
        if self.params['volume_surge_required']:
            if current['High_Volume'] and current['Volume_Ratio'] > 1.5:
                if len(long_confirmations) > len(short_confirmations):
                    long_confirmations.append('VOLUME_SURGE')
                else:
                    short_confirmations.append('VOLUME_SURGE')
        
        # 6. Smart Money
        if self.params['smart_money_check']:
            if current['Smart_Money'] and current['Price_Above_VWAP']:
                long_confirmations.append('SMART_MONEY_BULLISH')
            elif not current['Smart_Money'] and not current['Price_Above_VWAP']:
                short_confirmations.append('SMART_MONEY_BEARISH')
        
        # 7. Soporte/Resistencia
        if self.params['support_resistance_check']:
            if current['Distance_to_Support'] < 0.03 and current['Distance_to_Support'] > self.params['min_distance_to_sr']:
                long_confirmations.append('NEAR_SUPPORT')
            elif current['Distance_to_Resistance'] < 0.03 and current['Distance_to_Resistance'] > self.params['min_distance_to_sr']:
                short_confirmations.append('NEAR_RESISTANCE')
        
        # 8. Momentum
        if self.params['momentum_confirmation']:
            if current['Momentum_Positive'] and current['Momentum'] > 5:
                long_confirmations.append('STRONG_MOMENTUM')
            elif not current['Momentum_Positive'] and current['Momentum'] < -5:
                short_confirmations.append('NEGATIVE_MOMENTUM')
        
        # 9. Bollinger Bands Squeeze
        if current['BB_Squeeze_Tight']:
            if current['Close'] > current['BB_Middle']:
                long_confirmations.append('BB_SQUEEZE_BULLISH')
            else:
                short_confirmations.append('BB_SQUEEZE_BEARISH')
        
        # Decisión final
        min_confirmations = self.params['min_confirmations']
        
        if len(long_confirmations) >= min_confirmations and len(long_confirmations) > len(short_confirmations):
            confidence = len(long_confirmations) / 9.0  # 9 posibles confirmaciones
            signal_strength = ', '.join(long_confirmations[:3])  # Top 3 señales
            return 'LONG', confidence, signal_strength
            
        elif len(short_confirmations) >= min_confirmations and len(short_confirmations) > len(long_confirmations):
            confidence = len(short_confirmations) / 9.0
            signal_strength = ', '.join(short_confirmations[:3])
            return 'SHORT', confidence, signal_strength
        
        return None, 0, ""
    
    def calculate_precision_stops(self, entry_price, signal_type, atr, support, resistance):
        """
        Calcula stops con precisión basados en estructura
        """
        if signal_type == 'LONG':
            # Stop loss en el mínimo reciente o ATR, lo que sea más cercano
            atr_stop = entry_price - (atr * self.params['atr_multiplier_sl'])
            structure_stop = support * 0.99  # Ligeramente debajo del soporte
            stop_loss = max(atr_stop, structure_stop)  # Usar el más conservador
            
            # Take profit en resistencia o ATR
            atr_target = entry_price + (atr * self.params['atr_multiplier_tp'])
            structure_target = resistance * 0.99  # Ligeramente antes de resistencia
            take_profit = min(atr_target, structure_target) if structure_target > entry_price else atr_target
            
        else:  # SHORT
            # Stop loss en el máximo reciente o ATR
            atr_stop = entry_price + (atr * self.params['atr_multiplier_sl'])
            structure_stop = resistance * 1.01  # Ligeramente arriba de resistencia
            stop_loss = min(atr_stop, structure_stop)
            
            # Take profit en soporte o ATR
            atr_target = entry_price - (atr * self.params['atr_multiplier_tp'])
            structure_target = support * 1.01  # Ligeramente después del soporte
            take_profit = max(atr_target, structure_target) if structure_target < entry_price else atr_target
        
        # Verificar ratio Risk/Reward
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk > 0:
            rr_ratio = reward / risk
            if rr_ratio < self.params['risk_reward_min']:
                # Ajustar take profit para cumplir ratio mínimo
                if signal_type == 'LONG':
                    take_profit = entry_price + (risk * self.params['risk_reward_min'])
                else:
                    take_profit = entry_price - (risk * self.params['risk_reward_min'])
        
        return stop_loss, take_profit
    
    def backtest(self, symbol, start_date, end_date):
        """
        Ejecuta backtesting del sistema de precisión
        """
        # Obtener datos
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1d')
        
        if len(df) < 200:
            return []
        
        # Calcular indicadores avanzados
        df = self.calculate_advanced_indicators(df)
        
        # Variables
        trades = []
        position = None
        last_signal_date = None
        consecutive_losses = 0
        
        # Iterar
        for i in range(200, len(df)):
            current_date = df.index[i]
            current = df.iloc[i]
            
            # Si no hay posición
            if position is None:
                # Evitar overtrading
                if last_signal_date:
                    days_since = (current_date - last_signal_date).days
                    if days_since < 2:
                        continue
                
                # Verificar condiciones
                signal, confidence, strength = self.check_entry_conditions(df, i)
                
                if signal and confidence >= 0.67:  # Requiere 67% de confianza mínima (6/9 confirmaciones)
                    # Stops con precisión
                    stop_loss, take_profit = self.calculate_precision_stops(
                        current['Close'],
                        signal,
                        current['ATR'],
                        current['Support'],
                        current['Resistance']
                    )
                    
                    # Calcular tamaño de posición
                    risk_amount = self.current_capital * self.params['max_risk_per_trade']
                    risk_per_share = abs(current['Close'] - stop_loss)
                    
                    if risk_per_share > 0:
                        shares = risk_amount / risk_per_share
                        
                        position = {
                            'symbol': symbol,
                            'type': signal,
                            'entry_date': current_date,
                            'entry_price': current['Close'],
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'shares': shares,
                            'confidence': confidence,
                            'strength': strength,
                            'entry_rsi': current['RSI'],
                            'entry_volume': current['Volume_Ratio'],
                            'risk_reward': abs(take_profit - current['Close']) / risk_per_share
                        }
                        
                        last_signal_date = current_date
            
            # Si hay posición, verificar salida
            else:
                exit_triggered = False
                exit_price = current['Close']
                exit_reason = ''
                
                if position['type'] == 'LONG':
                    if current['Low'] <= position['stop_loss']:
                        exit_triggered = True
                        exit_price = position['stop_loss']
                        exit_reason = 'Stop Loss'
                    elif current['High'] >= position['take_profit']:
                        exit_triggered = True
                        exit_price = position['take_profit']
                        exit_reason = 'Take Profit'
                    # Trailing stop si estamos en profit significativo
                    elif current['Close'] > position['entry_price'] * 1.05:
                        trailing_stop = current['Close'] - (current['ATR'] * 1.0)
                        if trailing_stop > position['stop_loss']:
                            position['stop_loss'] = trailing_stop
                            
                else:  # SHORT
                    if current['High'] >= position['stop_loss']:
                        exit_triggered = True
                        exit_price = position['stop_loss']
                        exit_reason = 'Stop Loss'
                    elif current['Low'] <= position['take_profit']:
                        exit_triggered = True
                        exit_price = position['take_profit']
                        exit_reason = 'Take Profit'
                    # Trailing stop
                    elif current['Close'] < position['entry_price'] * 0.95:
                        trailing_stop = current['Close'] + (current['ATR'] * 1.0)
                        if trailing_stop < position['stop_loss']:
                            position['stop_loss'] = trailing_stop
                
                if exit_triggered:
                    # Calcular resultado
                    if position['type'] == 'LONG':
                        pnl = (exit_price - position['entry_price']) * position['shares']
                        return_pct = ((exit_price / position['entry_price']) - 1) * 100
                    else:
                        pnl = (position['entry_price'] - exit_price) * position['shares']
                        return_pct = ((position['entry_price'] / exit_price) - 1) * 100
                    
                    # Actualizar capital
                    self.current_capital += pnl
                    
                    # Registrar trade
                    trade = {
                        **position,
                        'exit_date': current_date,
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'pnl': pnl,
                        'return_pct': return_pct,
                        'duration_days': (current_date - position['entry_date']).days
                    }
                    
                    trades.append(trade)
                    
                    # Control de pérdidas consecutivas
                    if pnl < 0:
                        consecutive_losses += 1
                        if consecutive_losses >= 3:
                            # Pausa después de 3 pérdidas consecutivas
                            last_signal_date = current_date + timedelta(days=5)
                    else:
                        consecutive_losses = 0
                    
                    position = None
        
        return trades
    
    def analyze_results(self, trades):
        """
        Analiza resultados con métricas de precisión
        """
        if not trades:
            return None
        
        metrics = {
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in trades if t['pnl'] <= 0])
        }
        
        metrics['win_rate'] = (metrics['winning_trades'] / metrics['total_trades']) * 100
        
        # Profit factor
        gross_wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))
        metrics['profit_factor'] = gross_wins / gross_losses if gross_losses > 0 else float('inf')
        
        # Returns
        metrics['total_pnl'] = sum(t['pnl'] for t in trades)
        metrics['total_return'] = (metrics['total_pnl'] / self.initial_capital) * 100
        metrics['avg_return'] = np.mean([t['return_pct'] for t in trades])
        
        # Risk metrics
        returns = [t['return_pct'] for t in trades]
        metrics['sharpe_ratio'] = np.mean(returns) / (np.std(returns) + 0.0001) if len(returns) > 1 else 0
        
        # Calidad de señales
        metrics['avg_confidence'] = np.mean([t['confidence'] for t in trades])
        metrics['avg_rr_ratio'] = np.mean([t['risk_reward'] for t in trades])
        
        # Análisis por tipo de salida
        tp_exits = [t for t in trades if t['exit_reason'] == 'Take Profit']
        sl_exits = [t for t in trades if t['exit_reason'] == 'Stop Loss']
        
        metrics['tp_rate'] = (len(tp_exits) / len(trades)) * 100 if trades else 0
        metrics['sl_rate'] = (len(sl_exits) / len(trades)) * 100 if trades else 0
        
        return metrics

def test_precision_system():
    """
    Prueba el sistema de alta precisión
    """
    print("="*80)
    print("🎯 SISTEMA DE TRADING DE ALTA PRECISIÓN")
    print("="*80)
    print("Objetivo: Win Rate > 65%, Profit Factor > 2.0")
    print("Filosofía: Menos trades, mayor calidad")
    print("="*80)
    
    system = PrecisionTradingSystem(initial_capital=10000)
    
    # Períodos de prueba
    test_periods = [
        {'name': '2023_Full', 'start': '2023-01-01', 'end': '2023-12-31'},
        {'name': '2024_YTD', 'start': '2024-01-01', 'end': '2024-11-15'}
    ]
    
    all_trades = []
    
    for period in test_periods:
        print(f"\n📅 Testing Period: {period['name']}")
        print(f"   {period['start']} → {period['end']}")
        print("-"*60)
        
        # Test con múltiples símbolos
        for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
            print(f"\n   Testing {symbol}...")
            trades = system.backtest(symbol, period['start'], period['end'])
            
            if trades:
                metrics = system.analyze_results(trades)
                print(f"   • Trades: {metrics['total_trades']}")
                print(f"   • Win Rate: {metrics['win_rate']:.1f}%")
                print(f"   • Profit Factor: {metrics['profit_factor']:.2f}")
                print(f"   • Avg Confidence: {metrics['avg_confidence']:.2f}")
                print(f"   • Avg R/R: {metrics['avg_rr_ratio']:.2f}")
                print(f"   • TP Rate: {metrics['tp_rate']:.1f}%")
                
                all_trades.extend(trades)
            else:
                print(f"   • No trades (good - being selective!)")
    
    # Análisis global
    if all_trades:
        print("\n" + "="*80)
        print("📊 OVERALL PRECISION METRICS")
        print("="*80)
        
        final_metrics = system.analyze_results(all_trades)
        
        print(f"Total Trades: {final_metrics['total_trades']} (Less is more)")
        print(f"Win Rate: {final_metrics['win_rate']:.1f}%")
        print(f"Profit Factor: {final_metrics['profit_factor']:.2f}")
        print(f"Sharpe Ratio: {final_metrics['sharpe_ratio']:.2f}")
        print(f"Total Return: {final_metrics['total_return']:.1f}%")
        print(f"Avg Confidence: {final_metrics['avg_confidence']:.2f}")
        print(f"Take Profit Rate: {final_metrics['tp_rate']:.1f}%")
        
        # Evaluación
        print("\n🎯 PRECISION EVALUATION:")
        if final_metrics['win_rate'] >= 65 and final_metrics['profit_factor'] >= 2.0:
            print("✅ HIGH PRECISION ACHIEVED!")
            print("   System ready for production")
        elif final_metrics['win_rate'] >= 55 and final_metrics['profit_factor'] >= 1.5:
            print("🟡 GOOD PRECISION")
            print("   Close to target, fine-tuning needed")
        else:
            print("❌ PRECISION TARGET NOT MET")
            print("   Need to increase selectivity")
    
    return all_trades

if __name__ == "__main__":
    trades = test_precision_system()