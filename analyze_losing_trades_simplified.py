#!/usr/bin/env python3
"""
Análisis Simplificado de Trades Perdedores
Usa datos diarios para evitar limitaciones de Yahoo Finance
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class SimplifiedLossAnalyzer:
    """
    Analiza patrones en trades perdedores usando datos históricos
    """
    
    def __init__(self):
        self.losing_trades = []
        self.winning_trades = []
        self.all_trades = []
        
    def calculate_indicators(self, df):
        """
        Calcula indicadores técnicos básicos
        """
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
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # EMAs
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # Trend
        df['Uptrend'] = (df['EMA_9'] > df['EMA_21']) & (df['EMA_21'] > df['EMA_50'])
        df['Downtrend'] = (df['EMA_9'] < df['EMA_21']) & (df['EMA_21'] < df['EMA_50'])
        
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
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # Momentum
        df['Momentum'] = df['Close'].pct_change(10) * 100
        
        return df
    
    def generate_signals(self, df, idx):
        """
        Genera señales de trading basadas en indicadores
        """
        if idx < 50:
            return None, 0, []
        
        current = df.iloc[idx]
        prev = df.iloc[idx-1]
        
        long_score = 0
        short_score = 0
        signals = []
        
        # RSI
        if current['RSI'] < 35:
            long_score += 2
            signals.append('RSI_OVERSOLD')
        elif current['RSI'] > 65:
            short_score += 2
            signals.append('RSI_OVERBOUGHT')
        
        # MACD Cross
        if prev['MACD'] < prev['MACD_Signal'] and current['MACD'] > current['MACD_Signal']:
            long_score += 2
            signals.append('MACD_BULLISH_CROSS')
        elif prev['MACD'] > prev['MACD_Signal'] and current['MACD'] < current['MACD_Signal']:
            short_score += 2
            signals.append('MACD_BEARISH_CROSS')
        
        # Trend
        if current['Uptrend']:
            long_score += 1
            signals.append('UPTREND')
        elif current['Downtrend']:
            short_score += 1
            signals.append('DOWNTREND')
        
        # Bollinger Bands
        if current['BB_Position'] < 0.2:
            long_score += 1
            signals.append('BB_OVERSOLD')
        elif current['BB_Position'] > 0.8:
            short_score += 1
            signals.append('BB_OVERBOUGHT')
        
        # Volume
        if current['Volume_Ratio'] > 1.5:
            if long_score > short_score:
                long_score += 1
                signals.append('VOLUME_SURGE_LONG')
            else:
                short_score += 1
                signals.append('VOLUME_SURGE_SHORT')
        
        # Momentum
        if current['Momentum'] > 5:
            long_score += 1
            signals.append('STRONG_MOMENTUM_UP')
        elif current['Momentum'] < -5:
            short_score += 1
            signals.append('STRONG_MOMENTUM_DOWN')
        
        # Decision
        if long_score >= 4 and long_score > short_score:
            confidence = long_score / 10
            return 'LONG', confidence, signals
        elif short_score >= 4 and short_score > long_score:
            confidence = short_score / 10
            return 'SHORT', confidence, signals
        
        return None, 0, []
    
    def simulate_trade(self, df, idx, signal_type, entry_price, atr):
        """
        Simula el resultado de un trade
        """
        # Calculate stops
        if signal_type == 'LONG':
            stop_loss = entry_price - (atr * 1.5)
            take_profit = entry_price + (atr * 2.5)
        else:
            stop_loss = entry_price + (atr * 1.5)
            take_profit = entry_price - (atr * 2.5)
        
        # Simulate outcome over next 10 days
        exit_price = None
        exit_reason = None
        exit_day = 0
        
        for i in range(1, min(11, len(df) - idx)):
            future = df.iloc[idx + i]
            
            if signal_type == 'LONG':
                if future['Low'] <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'Stop Loss'
                    exit_day = i
                    break
                elif future['High'] >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'Take Profit'
                    exit_day = i
                    break
            else:  # SHORT
                if future['High'] >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'Stop Loss'
                    exit_day = i
                    break
                elif future['Low'] <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'Take Profit'
                    exit_day = i
                    break
        
        # If no exit, use price after 10 days
        if exit_price is None:
            if idx + 10 < len(df):
                exit_price = df.iloc[idx + 10]['Close']
                exit_reason = 'Time Exit'
                exit_day = 10
            else:
                exit_price = df.iloc[-1]['Close']
                exit_reason = 'End of Data'
                exit_day = len(df) - idx - 1
        
        # Calculate P&L
        if signal_type == 'LONG':
            pnl_pct = ((exit_price / entry_price) - 1) * 100
        else:
            pnl_pct = ((entry_price / exit_price) - 1) * 100
        
        return {
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'exit_day': exit_day,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'pnl_pct': pnl_pct,
            'pnl': 100 * pnl_pct  # $100 per 1% move
        }
    
    def backtest_symbol(self, symbol, start_date, end_date):
        """
        Ejecuta backtest para un símbolo
        """
        # Get data
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1d')
        
        if len(df) < 50:
            return []
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        trades = []
        last_trade_idx = 0
        
        # Generate trades
        for i in range(50, len(df) - 10):
            # Skip if too close to last trade
            if i - last_trade_idx < 3:
                continue
            
            signal, confidence, signal_list = self.generate_signals(df, i)
            
            if signal and confidence >= 0.3:
                current = df.iloc[i]
                
                # Simulate trade
                trade_result = self.simulate_trade(
                    df, i, signal, current['Close'], current['ATR']
                )
                
                trade = {
                    'symbol': symbol,
                    'date': df.index[i],
                    'type': signal,
                    'entry_price': current['Close'],
                    'confidence': confidence,
                    'signals': signal_list,
                    'rsi': current['RSI'],
                    'macd_histogram': current['MACD_Histogram'],
                    'bb_position': current['BB_Position'],
                    'volume_ratio': current['Volume_Ratio'],
                    'momentum': current['Momentum'],
                    'uptrend': current['Uptrend'],
                    'downtrend': current['Downtrend'],
                    **trade_result
                }
                
                trades.append(trade)
                last_trade_idx = i
                
                # Categorize trade
                if trade['pnl'] < 0:
                    self.losing_trades.append(trade)
                else:
                    self.winning_trades.append(trade)
        
        return trades
    
    def analyze_losses(self):
        """
        Analiza los patrones en trades perdedores
        """
        if not self.losing_trades:
            print("No hay trades perdedores para analizar")
            return
        
        print("\n" + "="*80)
        print("🔍 ANÁLISIS DETALLADO DE TRADES PERDEDORES")
        print("="*80)
        
        total_trades = len(self.losing_trades) + len(self.winning_trades)
        win_rate = len(self.winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        print(f"\n📊 RESUMEN GENERAL:")
        print(f"  • Total trades: {total_trades}")
        print(f"  • Trades ganadores: {len(self.winning_trades)}")
        print(f"  • Trades perdedores: {len(self.losing_trades)}")
        print(f"  • Win Rate: {win_rate:.1f}%")
        
        # 1. Análisis por tipo de señal
        print("\n📈 PÉRDIDAS POR TIPO DE SEÑAL:")
        long_losses = [t for t in self.losing_trades if t['type'] == 'LONG']
        short_losses = [t for t in self.losing_trades if t['type'] == 'SHORT']
        
        print(f"  • LONG perdedores: {len(long_losses)} ({len(long_losses)/len(self.losing_trades)*100:.1f}%)")
        print(f"  • SHORT perdedores: {len(short_losses)} ({len(short_losses)/len(self.losing_trades)*100:.1f}%)")
        
        # 2. Análisis por razón de salida
        print("\n🚪 RAZÓN DE SALIDA EN PÉRDIDAS:")
        exit_reasons = {}
        for trade in self.losing_trades:
            reason = trade['exit_reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(self.losing_trades) * 100
            print(f"  • {reason}: {count} trades ({pct:.1f}%)")
        
        # 3. Análisis de indicadores en pérdidas
        print("\n📉 INDICADORES PROMEDIO EN PÉRDIDAS:")
        
        # RSI
        losing_rsi = [t['rsi'] for t in self.losing_trades]
        winning_rsi = [t['rsi'] for t in self.winning_trades] if self.winning_trades else [50]
        print(f"  • RSI promedio:")
        print(f"    - En pérdidas: {np.mean(losing_rsi):.1f}")
        print(f"    - En ganancias: {np.mean(winning_rsi):.1f}")
        
        # Momentum
        losing_mom = [t['momentum'] for t in self.losing_trades]
        winning_mom = [t['momentum'] for t in self.winning_trades] if self.winning_trades else [0]
        print(f"  • Momentum promedio:")
        print(f"    - En pérdidas: {np.mean(losing_mom):.2f}%")
        print(f"    - En ganancias: {np.mean(winning_mom):.2f}%")
        
        # Volume
        losing_vol = [t['volume_ratio'] for t in self.losing_trades]
        winning_vol = [t['volume_ratio'] for t in self.winning_trades] if self.winning_trades else [1]
        print(f"  • Volume ratio promedio:")
        print(f"    - En pérdidas: {np.mean(losing_vol):.2f}")
        print(f"    - En ganancias: {np.mean(winning_vol):.2f}")
        
        # 4. Señales más comunes en pérdidas
        print("\n⚠️ SEÑALES MÁS FRECUENTES EN PÉRDIDAS:")
        signal_freq = {}
        for trade in self.losing_trades:
            for signal in trade['signals']:
                signal_freq[signal] = signal_freq.get(signal, 0) + 1
        
        top_signals = sorted(signal_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        for signal, count in top_signals:
            pct = count / len(self.losing_trades) * 100
            print(f"  • {signal}: {count} veces ({pct:.1f}%)")
        
        # 5. Análisis de trades contra-tendencia
        print("\n🔄 ANÁLISIS DE TENDENCIA:")
        counter_trend_long = sum(1 for t in self.losing_trades 
                                if t['type'] == 'LONG' and t['downtrend'])
        counter_trend_short = sum(1 for t in self.losing_trades 
                                 if t['type'] == 'SHORT' and t['uptrend'])
        counter_trend_total = counter_trend_long + counter_trend_short
        
        if self.losing_trades:
            pct_counter = counter_trend_total / len(self.losing_trades) * 100
            print(f"  • Trades contra-tendencia: {counter_trend_total} ({pct_counter:.1f}%)")
            print(f"    - LONG en downtrend: {counter_trend_long}")
            print(f"    - SHORT en uptrend: {counter_trend_short}")
        
        # 6. Análisis por símbolo
        print("\n🪙 PÉRDIDAS POR SÍMBOLO:")
        symbol_stats = {}
        for trade in self.all_trades:
            symbol = trade['symbol']
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {'total': 0, 'wins': 0, 'losses': 0}
            symbol_stats[symbol]['total'] += 1
            if trade['pnl'] > 0:
                symbol_stats[symbol]['wins'] += 1
            else:
                symbol_stats[symbol]['losses'] += 1
        
        for symbol, stats in symbol_stats.items():
            wr = stats['wins'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  • {symbol}: {stats['total']} trades, WR: {wr:.1f}%, "
                  f"Losses: {stats['losses']}")
        
        # 7. Identificar problemas principales
        print("\n" + "="*80)
        print("🔴 PROBLEMAS PRINCIPALES IDENTIFICADOS:")
        print("="*80)
        
        problems = []
        
        # Problema 1: Alto porcentaje de stop losses
        sl_pct = exit_reasons.get('Stop Loss', 0) / len(self.losing_trades) * 100
        if sl_pct > 70:
            problems.append(f"1. 📌 {sl_pct:.1f}% de pérdidas por stop loss (muy ajustado o mala entrada)")
        
        # Problema 2: Trades contra-tendencia
        if pct_counter > 30:
            problems.append(f"2. 📌 {pct_counter:.1f}% de pérdidas son contra-tendencia")
        
        # Problema 3: Baja confianza promedio
        avg_conf_loss = np.mean([t['confidence'] for t in self.losing_trades])
        avg_conf_win = np.mean([t['confidence'] for t in self.winning_trades]) if self.winning_trades else 0
        if avg_conf_loss < 0.4:
            problems.append(f"3. 📌 Confianza promedio muy baja en pérdidas: {avg_conf_loss:.2%}")
        
        # Problema 4: Señales falsas específicas
        for signal, count in top_signals[:2]:
            if count > len(self.losing_trades) * 0.4:
                problems.append(f"4. 📌 Señal '{signal}' presente en {count/len(self.losing_trades)*100:.1f}% de pérdidas")
        
        for problem in problems:
            print(f"\n{problem}")
        
        # 8. Recomendaciones
        print("\n" + "="*80)
        print("💡 RECOMENDACIONES PARA MEJORAR:")
        print("="*80)
        
        recommendations = []
        
        if sl_pct > 70:
            recommendations.append("• Aumentar multiplicador ATR para stops (1.5 → 2.0)")
        
        if pct_counter > 30:
            recommendations.append("• Implementar filtro estricto de tendencia")
        
        if avg_conf_loss < 0.4:
            recommendations.append("• Aumentar umbral mínimo de confianza a 40-45%")
        
        if 'RSI_OVERBOUGHT' in [s[0] for s in top_signals[:3]]:
            recommendations.append("• Ajustar umbrales RSI (65/35 → 70/30)")
        
        if 'VOLUME_SURGE_SHORT' in [s[0] for s in top_signals[:3]]:
            recommendations.append("• Revisar lógica de volumen en shorts")
        
        # Símbolos problemáticos
        worst_symbols = []
        for symbol, stats in symbol_stats.items():
            wr = stats['wins'] / stats['total'] * 100 if stats['total'] > 0 else 0
            if wr < 40:
                worst_symbols.append(symbol)
        
        if worst_symbols:
            recommendations.append(f"• Considerar excluir símbolos con bajo WR: {', '.join(worst_symbols)}")
        
        recommendations.append("• Implementar trailing stop más agresivo")
        recommendations.append("• Añadir confirmación de precio (retests, breakouts)")
        recommendations.append("• Considerar timeframe superior para confirmación")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")
        
        # 9. Impacto potencial de mejoras
        print("\n" + "="*80)
        print("📊 IMPACTO POTENCIAL DE MEJORAS:")
        print("="*80)
        
        # Simular mejoras
        filtered_losses = self.losing_trades.copy()
        original_losses = len(filtered_losses)
        
        # Filtrar por confianza > 40%
        filtered_losses = [t for t in filtered_losses if t['confidence'] >= 0.4]
        conf_improvement = original_losses - len(filtered_losses)
        
        # Filtrar contra-tendencia
        filtered_losses = [t for t in filtered_losses 
                          if not ((t['type'] == 'LONG' and t['downtrend']) or
                                 (t['type'] == 'SHORT' and t['uptrend']))]
        trend_improvement = original_losses - conf_improvement - len(filtered_losses)
        
        print(f"\n• Filtro de confianza >40%: -{conf_improvement} trades perdedores")
        print(f"• Filtro de tendencia: -{trend_improvement} trades perdedores adicionales")
        
        new_total = len(self.winning_trades) + len(filtered_losses)
        new_wr = len(self.winning_trades) / new_total * 100 if new_total > 0 else 0
        
        print(f"\n🎯 Win Rate actual: {win_rate:.1f}%")
        print(f"🎯 Win Rate potencial con mejoras: {new_wr:.1f}%")
        print(f"📈 Mejora potencial: +{new_wr - win_rate:.1f}%")
        
        return problems, recommendations


def main():
    """
    Ejecuta el análisis principal
    """
    print("="*80)
    print("🔍 ANÁLISIS DE TRADES PERDEDORES - SISTEMA DAILY TRADING")
    print("="*80)
    
    analyzer = SimplifiedLossAnalyzer()
    
    # Configuración
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'MATIC-USD']
    end_date = datetime(2024, 11, 15)
    start_date = datetime(2024, 9, 1)  # 2.5 meses de datos
    
    print(f"\n📅 Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    print(f"🪙 Símbolos: {', '.join(symbols)}")
    print("\n⏳ Ejecutando backtest...")
    
    # Ejecutar backtest para cada símbolo
    for symbol in symbols:
        print(f"\n  Testing {symbol}...")
        trades = analyzer.backtest_symbol(symbol, start_date, end_date)
        analyzer.all_trades.extend(trades)
        print(f"    ✓ {len(trades)} trades generados")
    
    print(f"\n✅ Backtest completado:")
    print(f"  • Total trades: {len(analyzer.all_trades)}")
    print(f"  • Ganadores: {len(analyzer.winning_trades)}")
    print(f"  • Perdedores: {len(analyzer.losing_trades)}")
    
    # Analizar pérdidas
    problems, recommendations = analyzer.analyze_losses()
    
    return analyzer, problems, recommendations

if __name__ == "__main__":
    analyzer, problems, recommendations = main()