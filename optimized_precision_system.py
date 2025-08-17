#!/usr/bin/env python3
"""
Sistema Optimizado de Precisión
Balance entre alta precisión y frecuencia razonable de trades
Objetivo: Win Rate > 60%, Profit Factor > 1.8, 20-40 trades/año
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class OptimizedPrecisionSystem:
    """
    Sistema balanceado: Alta precisión con frecuencia práctica
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Parámetros optimizados para balance precisión/frecuencia
        self.params = {
            # Confirmaciones requeridas (3-4 de 5 señales principales)
            'min_strong_signals': 3,       # Señales fuertes mínimas
            'min_total_score': 5,          # Score total mínimo
            
            # RSI optimizado
            'rsi_oversold': 30,            # Oversold estándar
            'rsi_overbought': 70,           # Overbought estándar
            'rsi_extreme_oversold': 25,    # Para señal extra fuerte
            'rsi_extreme_overbought': 75,  # Para señal extra fuerte
            
            # MACD
            'macd_signal_strength': 0.5,   # Fuerza de señal MACD
            
            # Tendencia y estructura
            'trend_alignment': True,       # Debe alinearse con tendencia
            'volume_confirmation': 1.3,    # 30% más volumen que promedio
            
            # Gestión de riesgo
            'risk_per_trade': 0.015,       # 1.5% riesgo por trade
            'min_risk_reward': 2.0,        # Mínimo 1:2 R/R
            'atr_stop_mult': 1.5,          # 1.5 ATR para stop
            'atr_target_mult': 2.5,        # 2.5 ATR para target
            
            # Control de calidad
            'max_trades_per_week': 2,      # Máximo 2 trades por semana
            'pause_after_loss': 2,         # Días de pausa después de pérdida
            'require_momentum': True        # Requiere momentum positivo
        }
        
        self.trades = []
        self.last_trade_date = None
        self.consecutive_losses = 0
        
    def calculate_indicators(self, df):
        """
        Calcula indicadores técnicos necesarios
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
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # EMAs para tendencia
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # Determinar tendencia
        df['Uptrend'] = (df['EMA_9'] > df['EMA_21']) & (df['EMA_21'] > df['EMA_50'])
        df['Downtrend'] = (df['EMA_9'] < df['EMA_21']) & (df['EMA_21'] < df['EMA_50'])
        
        # ATR para volatilidad
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        df['ATR_Percent'] = df['ATR'] / df['Close'] * 100
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # Momentum (ROC)
        df['Momentum'] = df['Close'].pct_change(10) * 100
        
        # Support/Resistance levels
        df['Support'] = df['Low'].rolling(20).min()
        df['Resistance'] = df['High'].rolling(20).max()
        
        # Price action patterns
        df['Hammer'] = self.detect_hammer(df)
        df['Shooting_Star'] = self.detect_shooting_star(df)
        
        return df
    
    def detect_hammer(self, df):
        """
        Detecta patrón de vela martillo (bullish reversal)
        """
        hammer = []
        for i in range(len(df)):
            if i < 1:
                hammer.append(False)
                continue
            
            body = abs(df['Close'].iloc[i] - df['Open'].iloc[i])
            lower_shadow = min(df['Open'].iloc[i], df['Close'].iloc[i]) - df['Low'].iloc[i]
            upper_shadow = df['High'].iloc[i] - max(df['Open'].iloc[i], df['Close'].iloc[i])
            
            # Condiciones de martillo
            is_hammer = (
                lower_shadow > body * 2 and  # Sombra inferior larga
                upper_shadow < body * 0.5 and  # Sombra superior corta
                df['Close'].iloc[i] > df['Open'].iloc[i]  # Vela alcista
            )
            
            hammer.append(is_hammer)
        
        return hammer
    
    def detect_shooting_star(self, df):
        """
        Detecta patrón estrella fugaz (bearish reversal)
        """
        shooting_star = []
        for i in range(len(df)):
            if i < 1:
                shooting_star.append(False)
                continue
            
            body = abs(df['Close'].iloc[i] - df['Open'].iloc[i])
            upper_shadow = df['High'].iloc[i] - max(df['Open'].iloc[i], df['Close'].iloc[i])
            lower_shadow = min(df['Open'].iloc[i], df['Close'].iloc[i]) - df['Low'].iloc[i]
            
            # Condiciones de estrella fugaz
            is_shooting_star = (
                upper_shadow > body * 2 and  # Sombra superior larga
                lower_shadow < body * 0.5 and  # Sombra inferior corta
                df['Close'].iloc[i] < df['Open'].iloc[i]  # Vela bajista
            )
            
            shooting_star.append(is_shooting_star)
        
        return shooting_star
    
    def evaluate_entry_signals(self, df, idx):
        """
        Evalúa señales de entrada con sistema de puntuación
        """
        if idx < 50:
            return None, 0, []
        
        current = df.iloc[idx]
        prev = df.iloc[idx-1]
        
        long_score = 0
        short_score = 0
        long_signals = []
        short_signals = []
        
        # 1. RSI (0-2 puntos)
        if current['RSI'] < self.params['rsi_extreme_oversold']:
            long_score += 2
            long_signals.append('RSI_EXTREME_OVERSOLD')
        elif current['RSI'] < self.params['rsi_oversold']:
            long_score += 1
            long_signals.append('RSI_OVERSOLD')
        elif current['RSI'] > self.params['rsi_extreme_overbought']:
            short_score += 2
            short_signals.append('RSI_EXTREME_OVERBOUGHT')
        elif current['RSI'] > self.params['rsi_overbought']:
            short_score += 1
            short_signals.append('RSI_OVERBOUGHT')
        
        # 2. MACD Cross (0-2 puntos)
        if prev['MACD'] < prev['MACD_Signal'] and current['MACD'] > current['MACD_Signal']:
            strength = abs(current['MACD_Histogram'])
            if strength > self.params['macd_signal_strength']:
                long_score += 2
                long_signals.append('MACD_STRONG_CROSS')
            else:
                long_score += 1
                long_signals.append('MACD_CROSS')
        elif prev['MACD'] > prev['MACD_Signal'] and current['MACD'] < current['MACD_Signal']:
            strength = abs(current['MACD_Histogram'])
            if strength > self.params['macd_signal_strength']:
                short_score += 2
                short_signals.append('MACD_STRONG_CROSS')
            else:
                short_score += 1
                short_signals.append('MACD_CROSS')
        
        # 3. Tendencia (0-2 puntos)
        if self.params['trend_alignment']:
            if current['Uptrend']:
                long_score += 2
                long_signals.append('UPTREND')
            elif current['Downtrend']:
                short_score += 2
                short_signals.append('DOWNTREND')
        
        # 4. Volumen (0-1 punto)
        if current['Volume_Ratio'] > self.params['volume_confirmation']:
            if long_score > short_score:
                long_score += 1
                long_signals.append('VOLUME_SURGE')
            elif short_score > long_score:
                short_score += 1
                short_signals.append('VOLUME_SURGE')
        
        # 5. Bollinger Bands (0-1 punto)
        if current['BB_Position'] < 0.2:  # Cerca de banda inferior
            long_score += 1
            long_signals.append('BB_OVERSOLD')
        elif current['BB_Position'] > 0.8:  # Cerca de banda superior
            short_score += 1
            short_signals.append('BB_OVERBOUGHT')
        
        # 6. Patrones de velas (0-2 puntos)
        if current['Hammer']:
            long_score += 2
            long_signals.append('HAMMER_PATTERN')
        elif current['Shooting_Star']:
            short_score += 2
            short_signals.append('SHOOTING_STAR')
        
        # 7. Momentum (0-1 punto)
        if self.params['require_momentum']:
            if current['Momentum'] > 0 and long_score > short_score:
                long_score += 1
                long_signals.append('POSITIVE_MOMENTUM')
            elif current['Momentum'] < 0 and short_score > long_score:
                short_score += 1
                short_signals.append('NEGATIVE_MOMENTUM')
        
        # 8. Soporte/Resistencia (0-1 punto)
        price_to_support = (current['Close'] - current['Support']) / current['Close']
        price_to_resistance = (current['Resistance'] - current['Close']) / current['Close']
        
        if price_to_support < 0.02:  # Cerca del soporte (2%)
            long_score += 1
            long_signals.append('NEAR_SUPPORT')
        elif price_to_resistance < 0.02:  # Cerca de resistencia
            short_score += 1
            short_signals.append('NEAR_RESISTANCE')
        
        # Decisión final
        strong_long_signals = len([s for s in long_signals if 'STRONG' in s or 'EXTREME' in s])
        strong_short_signals = len([s for s in short_signals if 'STRONG' in s or 'EXTREME' in s])
        
        if long_score >= self.params['min_total_score'] and strong_long_signals >= 1:
            confidence = long_score / 12.0  # Máximo 12 puntos posibles
            return 'LONG', confidence, long_signals[:3]
        elif short_score >= self.params['min_total_score'] and strong_short_signals >= 1:
            confidence = short_score / 12.0
            return 'SHORT', confidence, short_signals[:3]
        
        return None, 0, []
    
    def calculate_optimal_stops(self, entry_price, signal_type, atr, support, resistance):
        """
        Calcula stops óptimos basados en estructura y ATR
        """
        if signal_type == 'LONG':
            # Stop loss
            atr_stop = entry_price - (atr * self.params['atr_stop_mult'])
            structure_stop = support * 0.98  # 2% debajo del soporte
            stop_loss = max(atr_stop, structure_stop)
            
            # Take profit
            atr_target = entry_price + (atr * self.params['atr_target_mult'])
            structure_target = resistance * 0.98  # 2% antes de resistencia
            
            # Usar el que esté más cerca si es válido
            if structure_target > entry_price * 1.01:  # Al menos 1% de profit
                take_profit = min(atr_target, structure_target)
            else:
                take_profit = atr_target
                
        else:  # SHORT
            # Stop loss
            atr_stop = entry_price + (atr * self.params['atr_stop_mult'])
            structure_stop = resistance * 1.02  # 2% arriba de resistencia
            stop_loss = min(atr_stop, structure_stop)
            
            # Take profit
            atr_target = entry_price - (atr * self.params['atr_target_mult'])
            structure_target = support * 1.02  # 2% después del soporte
            
            if structure_target < entry_price * 0.99:  # Al menos 1% de profit
                take_profit = max(atr_target, structure_target)
            else:
                take_profit = atr_target
        
        # Verificar ratio risk/reward
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk > 0:
            rr_ratio = reward / risk
            if rr_ratio < self.params['min_risk_reward']:
                # Ajustar take profit
                if signal_type == 'LONG':
                    take_profit = entry_price + (risk * self.params['min_risk_reward'])
                else:
                    take_profit = entry_price - (risk * self.params['min_risk_reward'])
        
        return stop_loss, take_profit
    
    def should_take_trade(self, current_date):
        """
        Verifica si debemos tomar el trade basado en gestión de riesgo
        """
        # Verificar pausa después de pérdida
        if self.consecutive_losses > 0 and self.last_trade_date:
            days_since = (current_date - self.last_trade_date).days
            if days_since < self.params['pause_after_loss'] * self.consecutive_losses:
                return False
        
        # Verificar límite semanal
        if self.last_trade_date:
            days_since = (current_date - self.last_trade_date).days
            if days_since < 3:  # Mínimo 3 días entre trades
                return False
        
        return True
    
    def backtest(self, symbol, start_date, end_date):
        """
        Ejecuta backtesting del sistema optimizado
        """
        # Obtener datos
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1d')
        
        if len(df) < 50:
            return []
        
        # Calcular indicadores
        df = self.calculate_indicators(df)
        
        # Variables
        trades = []
        position = None
        weekly_trades = 0
        week_start = df.index[0]
        
        # Iterar
        for i in range(50, len(df)):
            current_date = df.index[i]
            current = df.iloc[i]
            
            # Reset contador semanal
            if (current_date - week_start).days >= 7:
                weekly_trades = 0
                week_start = current_date
            
            # Si no hay posición
            if position is None:
                # Verificar si podemos tradear
                if not self.should_take_trade(current_date):
                    continue
                
                if weekly_trades >= self.params['max_trades_per_week']:
                    continue
                
                # Evaluar señales
                signal, confidence, signals = self.evaluate_entry_signals(df, i)
                
                if signal and confidence >= 0.5:  # 50% confianza mínima (6/12 puntos)
                    # Calcular stops
                    stop_loss, take_profit = self.calculate_optimal_stops(
                        current['Close'],
                        signal,
                        current['ATR'],
                        current['Support'],
                        current['Resistance']
                    )
                    
                    # Calcular tamaño
                    risk_amount = self.current_capital * self.params['risk_per_trade']
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
                            'signals': signals,
                            'atr_percent': current['ATR_Percent']
                        }
                        
                        self.last_trade_date = current_date
                        weekly_trades += 1
            
            # Si hay posición, verificar salida
            else:
                exit_triggered = False
                exit_price = current['Close']
                exit_reason = ''
                
                if position['type'] == 'LONG':
                    # Check stops
                    if current['Low'] <= position['stop_loss']:
                        exit_triggered = True
                        exit_price = position['stop_loss']
                        exit_reason = 'Stop Loss'
                    elif current['High'] >= position['take_profit']:
                        exit_triggered = True
                        exit_price = position['take_profit']
                        exit_reason = 'Take Profit'
                    
                    # Trailing stop si hay profit significativo
                    elif current['Close'] > position['entry_price'] * 1.03:
                        new_stop = current['Close'] - (current['ATR'] * 1.2)
                        if new_stop > position['stop_loss']:
                            position['stop_loss'] = new_stop
                            
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
                    elif current['Close'] < position['entry_price'] * 0.97:
                        new_stop = current['Close'] + (current['ATR'] * 1.2)
                        if new_stop < position['stop_loss']:
                            position['stop_loss'] = new_stop
                
                if exit_triggered:
                    # Calcular P&L
                    if position['type'] == 'LONG':
                        pnl = (exit_price - position['entry_price']) * position['shares']
                        return_pct = ((exit_price / position['entry_price']) - 1) * 100
                    else:
                        pnl = (position['entry_price'] - exit_price) * position['shares']
                        return_pct = ((position['entry_price'] / exit_price) - 1) * 100
                    
                    # Actualizar capital
                    self.current_capital += pnl
                    
                    # Gestionar pérdidas consecutivas
                    if pnl < 0:
                        self.consecutive_losses += 1
                    else:
                        self.consecutive_losses = 0
                    
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
                    position = None
        
        return trades


def comprehensive_test():
    """
    Test comprehensivo del sistema optimizado
    """
    print("="*80)
    print("🎯 SISTEMA OPTIMIZADO DE PRECISIÓN")
    print("="*80)
    print("Balance: Alta precisión + Frecuencia práctica")
    print("Objetivo: Win Rate >60%, PF >1.8, 20-40 trades/año")
    print("="*80)
    
    system = OptimizedPrecisionSystem(initial_capital=10000)
    
    # Períodos de test
    test_periods = [
        {'name': '2022', 'start': '2022-01-01', 'end': '2022-12-31'},
        {'name': '2023', 'start': '2023-01-01', 'end': '2023-12-31'},
        {'name': '2024_YTD', 'start': '2024-01-01', 'end': '2024-11-15'}
    ]
    
    # Símbolos a testear
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD']
    
    all_trades = []
    period_summary = []
    
    for period in test_periods:
        print(f"\n📅 PERÍODO: {period['name']}")
        print(f"   {period['start']} → {period['end']}")
        print("-"*60)
        
        period_trades = []
        
        for symbol in symbols:
            trades = system.backtest(symbol, period['start'], period['end'])
            
            if trades:
                period_trades.extend(trades)
                wins = len([t for t in trades if t['pnl'] > 0])
                print(f"   {symbol}: {len(trades)} trades ({wins} wins)")
        
        if period_trades:
            # Métricas del período
            total = len(period_trades)
            wins = len([t for t in period_trades if t['pnl'] > 0])
            win_rate = (wins / total) * 100
            
            total_pnl = sum(t['pnl'] for t in period_trades)
            total_return = (total_pnl / 10000) * 100
            
            print(f"\n   📊 Resumen del período:")
            print(f"   • Total: {total} trades")
            print(f"   • Win Rate: {win_rate:.1f}%")
            print(f"   • Return: {total_return:.1f}%")
            
            all_trades.extend(period_trades)
            period_summary.append({
                'period': period['name'],
                'trades': total,
                'win_rate': win_rate,
                'return': total_return
            })
        else:
            print("   ❌ No trades generated")
    
    # Análisis final
    if all_trades:
        print("\n" + "="*80)
        print("📊 ANÁLISIS FINAL - SISTEMA OPTIMIZADO")
        print("="*80)
        
        total = len(all_trades)
        wins = len([t for t in all_trades if t['pnl'] > 0])
        losses = total - wins
        win_rate = (wins / total) * 100
        
        # Profit factor
        gross_wins = sum(t['pnl'] for t in all_trades if t['pnl'] > 0)
        gross_losses = abs(sum(t['pnl'] for t in all_trades if t['pnl'] <= 0))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
        
        # Returns
        total_pnl = sum(t['pnl'] for t in all_trades)
        total_return = (total_pnl / 10000) * 100
        
        # Duración
        avg_duration = np.mean([t['duration_days'] for t in all_trades])
        
        # Confianza promedio
        avg_confidence = np.mean([t['confidence'] for t in all_trades])
        
        print(f"Total Trades: {total} ({total/2.8:.1f} por año)")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Profit Factor: {profit_factor:.2f}")
        print(f"Total Return: {total_return:.1f}%")
        print(f"Avg Duration: {avg_duration:.1f} días")
        print(f"Avg Confidence: {avg_confidence:.2%}")
        
        # Evaluación
        print("\n🎯 EVALUACIÓN FINAL:")
        
        if win_rate >= 60 and profit_factor >= 1.8:
            print("✅ OBJETIVO ALCANZADO - Sistema de alta precisión")
            print("   Listo para paper trading")
        elif win_rate >= 55 and profit_factor >= 1.5:
            print("🟡 CERCA DEL OBJETIVO - Buen sistema")
            print("   Refinamiento menor requerido")
        else:
            print("❌ OBJETIVO NO ALCANZADO")
            print(f"   Win Rate: {win_rate:.1f}% (objetivo 60%)")
            print(f"   Profit Factor: {profit_factor:.2f} (objetivo 1.8)")
    
    return all_trades

if __name__ == "__main__":
    trades = comprehensive_test()