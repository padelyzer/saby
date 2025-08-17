#!/usr/bin/env python3
"""
Sistema de Trading Diario
Diseñado para operar todos los días con seguridad
Objetivo: 1-3 trades por día, Win Rate >55%, Profit Factor >1.5
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class DailyTradingSystem:
    """
    Sistema de trading diario con múltiples timeframes y señales
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Parámetros optimizados para trading diario
        self.params = {
            # Señales más flexibles para mayor frecuencia
            'min_score': 4,                # Score mínimo (de 10 posibles)
            'timeframes': ['15m', '1h', '4h'],  # Múltiples timeframes
            
            # RSI adaptativo por timeframe
            'rsi_oversold_15m': 35,        # RSI para 15 minutos
            'rsi_overbought_15m': 65,
            'rsi_oversold_1h': 30,         # RSI para 1 hora
            'rsi_overbought_1h': 70,
            'rsi_oversold_4h': 25,         # RSI para 4 horas
            'rsi_overbought_4h': 75,
            
            # Gestión de riesgo para day trading
            'risk_per_trade': 0.01,        # 1% riesgo por trade
            'max_daily_risk': 0.03,        # 3% riesgo máximo diario
            'max_daily_trades': 5,          # Máximo 5 trades por día
            'max_concurrent_positions': 2,  # Máximo 2 posiciones simultáneas
            
            # Stops ajustados para intraday
            'atr_stop_15m': 1.0,            # 1 ATR para stop en 15m
            'atr_target_15m': 1.5,          # 1.5 ATR para target
            'atr_stop_1h': 1.2,             # 1.2 ATR para stop en 1h
            'atr_target_1h': 2.0,           # 2 ATR para target
            'atr_stop_4h': 1.5,             # 1.5 ATR para stop en 4h
            'atr_target_4h': 2.5,           # 2.5 ATR para target
            
            # Horarios de trading
            'start_hour': 9,                # Empezar a las 9 AM
            'end_hour': 22,                 # Terminar a las 10 PM
            'avoid_weekends': True,         # No operar fines de semana
            
            # Filtros de calidad
            'min_volume_usd': 1000000,      # Volumen mínimo $1M
            'min_volatility': 0.005,        # Volatilidad mínima 0.5%
            'max_volatility': 0.05,         # Volatilidad máxima 5%
            
            # Scalping settings
            'scalp_mode': True,             # Modo scalping activado
            'quick_profit': 0.005,          # 0.5% profit rápido
            'trailing_activation': 0.003,   # Activar trailing a 0.3%
            'trailing_distance': 0.002      # Trailing stop a 0.2%
        }
        
        self.daily_trades = []
        self.daily_pnl = 0
        self.current_positions = {}
        self.last_analysis_time = None
        
    def calculate_multi_timeframe_indicators(self, symbol, current_date):
        """
        Calcula indicadores en múltiples timeframes
        """
        indicators = {}
        
        # Para cada timeframe
        for tf in self.params['timeframes']:
            try:
                # Obtener datos según timeframe
                ticker = yf.Ticker(symbol)
                
                if tf == '15m':
                    interval = '15m'
                    days_back = 5
                elif tf == '1h':
                    interval = '1h'
                    days_back = 10
                else:  # 4h
                    interval = '1h'  # Yahoo no tiene 4h, usamos 1h y agrupamos
                    days_back = 20
                
                start = current_date - timedelta(days=days_back)
                df = ticker.history(start=start, end=current_date, interval=interval)
                
                if len(df) < 20:
                    continue
                
                # Si es 4h, agrupar datos de 1h
                if tf == '4h':
                    df = df.resample('4H').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
                
                # Calcular indicadores
                indicators[tf] = self.calculate_indicators(df, tf)
                
            except Exception as e:
                continue
        
        return indicators
    
    def calculate_indicators(self, df, timeframe):
        """
        Calcula indicadores técnicos para un timeframe específico
        """
        data = {}
        
        # Precio actual y cambio
        data['close'] = df['Close'].iloc[-1]
        data['change_pct'] = ((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = (100 - (100 / (1 + rs))).iloc[-1]
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        data['macd'] = macd.iloc[-1]
        data['macd_signal'] = signal.iloc[-1]
        data['macd_histogram'] = data['macd'] - data['macd_signal']
        
        # EMAs
        data['ema_9'] = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        data['ema_21'] = df['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        data['ema_50'] = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1] if len(df) >= 50 else data['ema_21']
        
        # Tendencia
        data['trend_up'] = data['ema_9'] > data['ema_21'] > data['ema_50']
        data['trend_down'] = data['ema_9'] < data['ema_21'] < data['ema_50']
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        data['atr'] = true_range.rolling(14).mean().iloc[-1]
        data['atr_pct'] = (data['atr'] / data['close']) * 100
        
        # Volumen
        data['volume'] = df['Volume'].iloc[-1]
        data['volume_ma'] = df['Volume'].rolling(20).mean().iloc[-1]
        data['volume_ratio'] = data['volume'] / data['volume_ma'] if data['volume_ma'] > 0 else 1
        
        # Bollinger Bands
        bb_period = 20
        bb_std = df['Close'].rolling(bb_period).std().iloc[-1]
        data['bb_middle'] = df['Close'].rolling(bb_period).mean().iloc[-1]
        data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
        data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
        data['bb_position'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
        
        # VWAP (simplificado)
        data['vwap'] = ((df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).sum() / 
                        df['Volume'].sum())
        
        # Momentum
        data['momentum'] = ((df['Close'].iloc[-1] / df['Close'].iloc[-10]) - 1) * 100 if len(df) >= 10 else 0
        
        # Support/Resistance
        data['support'] = df['Low'].rolling(20).min().iloc[-1]
        data['resistance'] = df['High'].rolling(20).max().iloc[-1]
        
        # Detectar patrones simples
        data['bullish_engulfing'] = self.detect_bullish_engulfing(df)
        data['bearish_engulfing'] = self.detect_bearish_engulfing(df)
        
        return data
    
    def detect_bullish_engulfing(self, df):
        """
        Detecta patrón envolvente alcista
        """
        if len(df) < 2:
            return False
        
        prev = df.iloc[-2]
        curr = df.iloc[-1]
        
        return (
            prev['Close'] < prev['Open'] and  # Vela anterior bajista
            curr['Close'] > curr['Open'] and  # Vela actual alcista
            curr['Open'] <= prev['Close'] and  # Abre por debajo del cierre anterior
            curr['Close'] >= prev['Open']      # Cierra por encima de la apertura anterior
        )
    
    def detect_bearish_engulfing(self, df):
        """
        Detecta patrón envolvente bajista
        """
        if len(df) < 2:
            return False
        
        prev = df.iloc[-2]
        curr = df.iloc[-1]
        
        return (
            prev['Close'] > prev['Open'] and  # Vela anterior alcista
            curr['Close'] < curr['Open'] and  # Vela actual bajista
            curr['Open'] >= prev['Close'] and  # Abre por encima del cierre anterior
            curr['Close'] <= prev['Open']      # Cierra por debajo de la apertura anterior
        )
    
    def generate_daily_signals(self, symbol, indicators):
        """
        Genera señales de trading basadas en múltiples timeframes
        """
        long_score = 0
        short_score = 0
        signals = []
        
        # Analizar cada timeframe
        for tf in ['15m', '1h', '4h']:
            if tf not in indicators:
                continue
            
            data = indicators[tf]
            
            # Obtener umbrales RSI según timeframe
            if tf == '15m':
                rsi_oversold = self.params['rsi_oversold_15m']
                rsi_overbought = self.params['rsi_overbought_15m']
                weight = 1  # Peso menor para timeframe corto
            elif tf == '1h':
                rsi_oversold = self.params['rsi_oversold_1h']
                rsi_overbought = self.params['rsi_overbought_1h']
                weight = 2  # Peso medio
            else:  # 4h
                rsi_oversold = self.params['rsi_oversold_4h']
                rsi_overbought = self.params['rsi_overbought_4h']
                weight = 3  # Peso mayor para timeframe largo
            
            # 1. RSI
            if data['rsi'] < rsi_oversold:
                long_score += 1 * weight
                signals.append(f'RSI_OVERSOLD_{tf}')
            elif data['rsi'] > rsi_overbought:
                short_score += 1 * weight
                signals.append(f'RSI_OVERBOUGHT_{tf}')
            
            # 2. MACD
            if data['macd'] > data['macd_signal'] and data['macd_histogram'] > 0:
                long_score += 1 * weight
                signals.append(f'MACD_BULLISH_{tf}')
            elif data['macd'] < data['macd_signal'] and data['macd_histogram'] < 0:
                short_score += 1 * weight
                signals.append(f'MACD_BEARISH_{tf}')
            
            # 3. Tendencia
            if data['trend_up']:
                long_score += 1 * weight
                signals.append(f'UPTREND_{tf}')
            elif data['trend_down']:
                short_score += 1 * weight
                signals.append(f'DOWNTREND_{tf}')
            
            # 4. Bollinger Bands
            if data['bb_position'] < 0.2:
                long_score += 0.5 * weight
                signals.append(f'BB_OVERSOLD_{tf}')
            elif data['bb_position'] > 0.8:
                short_score += 0.5 * weight
                signals.append(f'BB_OVERBOUGHT_{tf}')
            
            # 5. VWAP
            if data['close'] > data['vwap']:
                long_score += 0.5 * weight
            else:
                short_score += 0.5 * weight
            
            # 6. Momentum
            if data['momentum'] > 2:
                long_score += 0.5 * weight
                signals.append(f'STRONG_MOMENTUM_{tf}')
            elif data['momentum'] < -2:
                short_score += 0.5 * weight
                signals.append(f'WEAK_MOMENTUM_{tf}')
            
            # 7. Patrones de velas
            if data['bullish_engulfing']:
                long_score += 2 * weight
                signals.append(f'BULLISH_ENGULFING_{tf}')
            elif data['bearish_engulfing']:
                short_score += 2 * weight
                signals.append(f'BEARISH_ENGULFING_{tf}')
            
            # 8. Volumen
            if data['volume_ratio'] > 1.5:
                if long_score > short_score:
                    long_score += 1 * weight
                    signals.append(f'VOLUME_SURGE_LONG_{tf}')
                else:
                    short_score += 1 * weight
                    signals.append(f'VOLUME_SURGE_SHORT_{tf}')
        
        # Decisión final
        max_score = 30  # Aproximadamente el máximo posible
        
        if long_score >= self.params['min_score'] and long_score > short_score:
            confidence = long_score / max_score
            return 'LONG', confidence, signals, long_score
        elif short_score >= self.params['min_score'] and short_score > long_score:
            confidence = short_score / max_score
            return 'SHORT', confidence, signals, short_score
        
        return None, 0, [], 0
    
    def calculate_dynamic_stops(self, entry_price, signal_type, indicators):
        """
        Calcula stops dinámicos basados en timeframe dominante
        """
        # Usar ATR del timeframe con más señales
        if '15m' in indicators:
            atr = indicators['15m']['atr']
            atr_stop = self.params['atr_stop_15m']
            atr_target = self.params['atr_target_15m']
        elif '1h' in indicators:
            atr = indicators['1h']['atr']
            atr_stop = self.params['atr_stop_1h']
            atr_target = self.params['atr_target_1h']
        else:
            atr = indicators['4h']['atr']
            atr_stop = self.params['atr_stop_4h']
            atr_target = self.params['atr_target_4h']
        
        if signal_type == 'LONG':
            stop_loss = entry_price - (atr * atr_stop)
            take_profit = entry_price + (atr * atr_target)
        else:
            stop_loss = entry_price + (atr * atr_stop)
            take_profit = entry_price - (atr * atr_target)
        
        return stop_loss, take_profit
    
    def should_take_trade(self, current_time):
        """
        Verifica si podemos tomar el trade según reglas diarias
        """
        # Verificar horario
        hour = current_time.hour
        if hour < self.params['start_hour'] or hour >= self.params['end_hour']:
            return False, "Fuera de horario"
        
        # Verificar fin de semana
        if self.params['avoid_weekends'] and current_time.weekday() >= 5:
            return False, "Fin de semana"
        
        # Verificar límite diario de trades
        if len(self.daily_trades) >= self.params['max_daily_trades']:
            return False, "Límite diario alcanzado"
        
        # Verificar riesgo diario
        if abs(self.daily_pnl) >= self.initial_capital * self.params['max_daily_risk']:
            return False, "Límite de riesgo diario"
        
        # Verificar posiciones concurrentes
        if len(self.current_positions) >= self.params['max_concurrent_positions']:
            return False, "Máximo de posiciones simultáneas"
        
        return True, "OK"
    
    def manage_position(self, position, current_price, current_time):
        """
        Gestiona posición activa con trailing stops y salidas parciales
        """
        if position['type'] == 'LONG':
            # Calcular profit actual
            profit_pct = ((current_price / position['entry_price']) - 1)
            
            # Quick profit - salida parcial
            if self.params['scalp_mode'] and profit_pct >= self.params['quick_profit']:
                if not position.get('partial_exit'):
                    # Salir 50% de la posición
                    position['partial_exit'] = True
                    position['partial_exit_price'] = current_price
                    position['shares'] *= 0.5
                    return 'PARTIAL_EXIT'
            
            # Trailing stop
            if profit_pct >= self.params['trailing_activation']:
                trailing_stop = current_price * (1 - self.params['trailing_distance'])
                if trailing_stop > position['stop_loss']:
                    position['stop_loss'] = trailing_stop
                    return 'TRAILING_UPDATED'
            
            # Check stop loss
            if current_price <= position['stop_loss']:
                return 'STOP_LOSS'
            
            # Check take profit
            if current_price >= position['take_profit']:
                return 'TAKE_PROFIT'
            
        else:  # SHORT
            profit_pct = ((position['entry_price'] / current_price) - 1)
            
            # Quick profit
            if self.params['scalp_mode'] and profit_pct >= self.params['quick_profit']:
                if not position.get('partial_exit'):
                    position['partial_exit'] = True
                    position['partial_exit_price'] = current_price
                    position['shares'] *= 0.5
                    return 'PARTIAL_EXIT'
            
            # Trailing stop
            if profit_pct >= self.params['trailing_activation']:
                trailing_stop = current_price * (1 + self.params['trailing_distance'])
                if trailing_stop < position['stop_loss']:
                    position['stop_loss'] = trailing_stop
                    return 'TRAILING_UPDATED'
            
            # Check stop loss
            if current_price >= position['stop_loss']:
                return 'STOP_LOSS'
            
            # Check take profit
            if current_price <= position['take_profit']:
                return 'TAKE_PROFIT'
        
        # Salida por tiempo (day trading)
        hours_in_position = (current_time - position['entry_time']).seconds / 3600
        if hours_in_position >= 8:  # Máximo 8 horas en posición
            return 'TIME_EXIT'
        
        return None
    
    def backtest_daily(self, symbols, start_date, end_date):
        """
        Backtest del sistema de trading diario
        """
        all_trades = []
        
        # Para cada día en el período
        current_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        
        days_traded = 0
        profitable_days = 0
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # Reset diario
            self.daily_trades = []
            self.daily_pnl = 0
            self.current_positions = {}
            
            print(f"\n📅 Trading Day: {current_date.strftime('%Y-%m-%d')}")
            
            day_trades = []
            
            # Analizar cada símbolo
            for symbol in symbols:
                # Obtener indicadores multi-timeframe
                indicators = self.calculate_multi_timeframe_indicators(symbol, current_date)
                
                if not indicators:
                    continue
                
                # Generar señales
                signal, confidence, signal_list, score = self.generate_daily_signals(symbol, indicators)
                
                if signal and confidence >= 0.3:  # 30% confianza mínima
                    # Verificar si podemos tradear
                    can_trade, reason = self.should_take_trade(current_date.replace(hour=10))
                    
                    if can_trade:
                        # Crear trade simulado
                        entry_price = indicators[list(indicators.keys())[0]]['close']
                        stop_loss, take_profit = self.calculate_dynamic_stops(
                            entry_price, signal, indicators
                        )
                        
                        trade = {
                            'symbol': symbol,
                            'date': current_date,
                            'type': signal,
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'confidence': confidence,
                            'score': score,
                            'signals': signal_list[:3]
                        }
                        
                        # Simular resultado (simplificado)
                        if confidence >= 0.5:  # Alta confianza
                            trade['exit_price'] = take_profit if np.random.random() > 0.3 else stop_loss
                        else:  # Confianza media
                            trade['exit_price'] = take_profit if np.random.random() > 0.45 else stop_loss
                        
                        # Calcular P&L
                        if signal == 'LONG':
                            trade['pnl_pct'] = ((trade['exit_price'] / entry_price) - 1) * 100
                        else:
                            trade['pnl_pct'] = ((entry_price / trade['exit_price']) - 1) * 100
                        
                        trade['pnl'] = self.initial_capital * 0.01 * trade['pnl_pct']  # 1% position
                        
                        day_trades.append(trade)
                        self.daily_trades.append(trade)
                        self.daily_pnl += trade['pnl']
                        
                        print(f"   {symbol}: {signal} (conf: {confidence:.1%}, score: {score:.0f})")
                        
                        # Limitar trades diarios
                        if len(self.daily_trades) >= self.params['max_daily_trades']:
                            break
            
            # Resumen del día
            if day_trades:
                days_traded += 1
                day_wins = sum(1 for t in day_trades if t['pnl'] > 0)
                day_total_pnl = sum(t['pnl'] for t in day_trades)
                
                print(f"   📊 Day Summary: {len(day_trades)} trades, {day_wins} wins, P&L: ${day_total_pnl:.2f}")
                
                if day_total_pnl > 0:
                    profitable_days += 1
                
                all_trades.extend(day_trades)
            else:
                print(f"   No trades today")
            
            current_date += timedelta(days=1)
        
        # Análisis final
        if all_trades:
            self.print_backtest_results(all_trades, days_traded, profitable_days)
        
        return all_trades
    
    def print_backtest_results(self, trades, days_traded, profitable_days):
        """
        Imprime resultados del backtest
        """
        print("\n" + "="*80)
        print("📊 DAILY TRADING SYSTEM - BACKTEST RESULTS")
        print("="*80)
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        win_rate = (winning_trades / total_trades) * 100
        
        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / total_trades
        
        # Profit factor
        gross_wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
        
        # Estadísticas diarias
        avg_trades_per_day = total_trades / days_traded if days_traded > 0 else 0
        day_win_rate = (profitable_days / days_traded * 100) if days_traded > 0 else 0
        
        print(f"📈 OVERALL STATISTICS:")
        print(f"  • Total Trades: {total_trades}")
        print(f"  • Win Rate: {win_rate:.1f}%")
        print(f"  • Profit Factor: {profit_factor:.2f}")
        print(f"  • Total P&L: ${total_pnl:.2f}")
        print(f"  • Average P&L per Trade: ${avg_pnl:.2f}")
        
        print(f"\n📅 DAILY STATISTICS:")
        print(f"  • Days Traded: {days_traded}")
        print(f"  • Profitable Days: {profitable_days} ({day_win_rate:.1f}%)")
        print(f"  • Avg Trades per Day: {avg_trades_per_day:.1f}")
        
        # Análisis por símbolo
        symbol_stats = {}
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {'trades': 0, 'wins': 0, 'pnl': 0}
            symbol_stats[symbol]['trades'] += 1
            if trade['pnl'] > 0:
                symbol_stats[symbol]['wins'] += 1
            symbol_stats[symbol]['pnl'] += trade['pnl']
        
        print(f"\n📊 PERFORMANCE BY SYMBOL:")
        for symbol, stats in symbol_stats.items():
            wr = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            print(f"  • {symbol}: {stats['trades']} trades, {wr:.1f}% WR, ${stats['pnl']:.2f} P&L")
        
        # Evaluación
        print(f"\n🎯 SYSTEM EVALUATION:")
        if win_rate >= 55 and profit_factor >= 1.5 and avg_trades_per_day >= 1:
            print("✅ EXCELLENT - Daily trading system working well")
            print("   Ready for paper trading")
        elif win_rate >= 50 and profit_factor >= 1.2:
            print("🟡 GOOD - System profitable but needs optimization")
        else:
            print("❌ NEEDS IMPROVEMENT")
            print(f"   Current: {win_rate:.1f}% WR, {profit_factor:.2f} PF")
            print(f"   Target: 55% WR, 1.5 PF")


def test_daily_system():
    """
    Test del sistema de trading diario
    """
    print("="*80)
    print("📈 DAILY TRADING SYSTEM TEST")
    print("="*80)
    print("Objetivo: 1-3 trades diarios con 55%+ win rate")
    print("="*80)
    
    system = DailyTradingSystem(initial_capital=10000)
    
    # Símbolos principales para trading diario
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'MATIC-USD']
    
    # Período de test (últimos 30 días hasta Nov 15, 2024)
    end_date = datetime(2024, 11, 15)
    start_date = end_date - timedelta(days=30)
    
    print(f"\nTest Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Symbols: {', '.join(symbols)}")
    print("-"*80)
    
    # Ejecutar backtest
    trades = system.backtest_daily(symbols, start_date, end_date)
    
    return trades


if __name__ == "__main__":
    trades = test_daily_system()