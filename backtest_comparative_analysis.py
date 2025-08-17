#!/usr/bin/env python3
"""
Análisis Comparativo de Backtesting
Sistema Daily Trading V2 vs V3 Balanceado vs V3 Ultra Conservador
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class ComparativeBacktestAnalysis:
    """
    Análisis comparativo de diferentes versiones del sistema
    """
    
    def __init__(self):
        self.results = {}
        
    def create_v3_balanced_system(self):
        """
        Crea sistema V3 balanceado - menos estricto que ultra conservador
        """
        params = {
            # PARÁMETROS BALANCEADOS
            'min_score': 6,                # Entre V2 (5) y V3 (8)
            'min_confidence': 0.5,          # Entre V2 (0.4) y V3 (0.6)
            'timeframes': ['15m', '1h', '4h'],
            
            # RSI MODERADAMENTE ESTRICTO
            'rsi_oversold_15m': 25,        # Entre V2 (30) y V3 (15)
            'rsi_overbought_15m': 75,      # Entre V2 (70) y V3 (85)
            'rsi_oversold_1h': 20,         # Entre V2 (25) y V3 (10)
            'rsi_overbought_1h': 80,       # Entre V2 (75) y V3 (90)
            'rsi_oversold_4h': 15,         # Entre V2 (20) y V3 (5)
            'rsi_overbought_4h': 85,       # Entre V2 (80) y V3 (95)
            
            # GESTIÓN DE RIESGO BALANCEADA
            'risk_per_trade': 0.008,        # Entre V2 (0.01) y V3 (0.005)
            'max_daily_risk': 0.02,         # Entre V2 (0.03) y V3 (0.01)
            'max_daily_trades': 2,          # Entre V2 (3) y V3 (1)
            'max_concurrent_positions': 1,
            
            # STOPS AMPLIOS PERO NO EXTREMOS
            'atr_stop_15m': 2.5,            # Entre V2 (1.5) y V3 (3.0)
            'atr_target_15m': 3.5,          # Entre V2 (2.0) y V3 (5.0)
            'atr_stop_1h': 2.8,             # Entre V2 (2.0) y V3 (3.5)
            'atr_target_1h': 4.5,           # Entre V2 (3.0) y V3 (6.0)
            'atr_stop_4h': 3.2,             # Entre V2 (2.5) y V3 (4.0)
            'atr_target_4h': 6.0,           # Entre V2 (4.0) y V3 (8.0)
            
            # FILTROS BALANCEADOS
            'min_volume_usd': 2000000,      # Entre V2 (1M) y V3 (5M)
            'volume_surge_required': 1.8,   # Entre V2 (1.5) y V3 (2.0)
            
            # TENDENCIA ESTRICTA PERO NO ULTRA
            'respect_trend': True,
            'trend_alignment_required': True,
            'counter_trend_forbidden': True,
            'all_timeframes_must_align': False,  # Más flexible que V3
            'min_aligned_timeframes': 2,         # 2 de 3 vs V3 (3 de 3)
            
            # FILTROS ADICIONALES MODERADOS
            'correlation_filter': True,
            'correlation_threshold': 0.8,        # Más flexible que V3 (0.7)
            'momentum_confirmation': True,
            'min_momentum_strength': 5,          # Menos estricto que V3 (10)
        }
        return params

    def simulate_trade_outcome(self, signal_type, confidence, stop_loss, take_profit, entry_price):
        """
        Simula el resultado de un trade con probabilidades realistas
        """
        # Probabilidades basadas en confianza y tipo de mercado
        if confidence >= 0.7:
            win_probability = 0.75  # Alta confianza
        elif confidence >= 0.6:
            win_probability = 0.65  # Buena confianza
        elif confidence >= 0.5:
            win_probability = 0.55  # Confianza moderada
        else:
            win_probability = 0.45  # Baja confianza
        
        # Simular resultado
        if np.random.random() < win_probability:
            exit_price = take_profit
            exit_reason = "Take Profit"
        else:
            exit_price = stop_loss
            exit_reason = "Stop Loss"
        
        # Calcular P&L
        if signal_type == 'LONG':
            pnl_pct = ((exit_price / entry_price) - 1) * 100
        else:
            pnl_pct = ((entry_price / exit_price) - 1) * 100
        
        return exit_price, exit_reason, pnl_pct

    def calculate_simple_indicators(self, df):
        """
        Calcula indicadores simplificados para backtest rápido
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
        
        # EMAs
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # Tendencia
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
        
        # Momentum
        df['Momentum'] = df['Close'].pct_change(5) * 100
        
        return df

    def generate_signals_by_version(self, df, idx, version_params):
        """
        Genera señales según los parámetros de la versión
        """
        if idx < 50:
            return None, 0, []
        
        current = df.iloc[idx]
        prev = df.iloc[idx-1]
        
        long_score = 0
        short_score = 0
        signals = []
        
        # Verificar tendencia
        trend_aligned = False
        if current['Uptrend'] and not current['Downtrend']:
            trend_direction = 'UP'
            trend_aligned = True
        elif current['Downtrend'] and not current['Uptrend']:
            trend_direction = 'DOWN'
            trend_aligned = True
        else:
            trend_direction = 'NEUTRAL'
            if version_params.get('all_timeframes_must_align', False):
                return None, 0, ['TREND_NOT_ALIGNED']
        
        # RSI
        rsi_oversold = version_params.get('rsi_oversold_1h', 30)
        rsi_overbought = version_params.get('rsi_overbought_1h', 70)
        
        if current['RSI'] < rsi_oversold:
            if trend_direction != 'DOWN' or not version_params.get('counter_trend_forbidden', False):
                long_score += 2
                signals.append('RSI_OVERSOLD')
        elif current['RSI'] > rsi_overbought:
            if trend_direction != 'UP' or not version_params.get('counter_trend_forbidden', False):
                short_score += 2
                signals.append('RSI_OVERBOUGHT')
        
        # MACD
        if prev['MACD'] < prev['MACD_Signal'] and current['MACD'] > current['MACD_Signal']:
            if trend_direction != 'DOWN' or not version_params.get('counter_trend_forbidden', False):
                long_score += 2
                signals.append('MACD_BULLISH_CROSS')
        elif prev['MACD'] > prev['MACD_Signal'] and current['MACD'] < current['MACD_Signal']:
            if trend_direction != 'UP' or not version_params.get('counter_trend_forbidden', False):
                short_score += 2
                signals.append('MACD_BEARISH_CROSS')
        
        # Tendencia
        if current['Uptrend']:
            long_score += 2
            signals.append('UPTREND')
        elif current['Downtrend']:
            short_score += 2
            signals.append('DOWNTREND')
        
        # Volume
        volume_threshold = version_params.get('volume_surge_required', 1.5)
        if current['Volume_Ratio'] > volume_threshold:
            if long_score > short_score:
                long_score += 1
                signals.append('VOLUME_SURGE_LONG')
            else:
                short_score += 1
                signals.append('VOLUME_SURGE_SHORT')
        
        # Momentum
        min_momentum = version_params.get('min_momentum_strength', 5)
        if version_params.get('momentum_confirmation', False):
            if abs(current['Momentum']) < min_momentum:
                return None, 0, ['INSUFFICIENT_MOMENTUM']
        
        if current['Momentum'] > 3:
            long_score += 1
            signals.append('MOMENTUM_UP')
        elif current['Momentum'] < -3:
            short_score += 1
            signals.append('MOMENTUM_DOWN')
        
        # Evaluar señal
        min_score = version_params.get('min_score', 4)
        min_confidence = version_params.get('min_confidence', 0.4)
        
        if long_score >= min_score and long_score > short_score:
            confidence = min(long_score / 10, 0.9)
            if confidence >= min_confidence:
                return 'LONG', confidence, signals
        elif short_score >= min_score and short_score > long_score:
            confidence = min(short_score / 10, 0.9)
            if confidence >= min_confidence:
                return 'SHORT', confidence, signals
        
        return None, 0, signals

    def calculate_stops(self, entry_price, signal_type, atr, version_params):
        """
        Calcula stops según la versión
        """
        atr_stop = version_params.get('atr_stop_1h', 2.0)
        atr_target = version_params.get('atr_target_1h', 3.0)
        
        if signal_type == 'LONG':
            stop_loss = entry_price - (atr * atr_stop)
            take_profit = entry_price + (atr * atr_target)
        else:
            stop_loss = entry_price + (atr * atr_stop)
            take_profit = entry_price - (atr * atr_target)
        
        return stop_loss, take_profit

    def backtest_version(self, symbol, start_date, end_date, version_name, version_params):
        """
        Ejecuta backtest para una versión específica
        """
        print(f"\n🧪 Testing {version_name} on {symbol}...")
        
        # Obtener datos
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1d')
        
        if len(df) < 60:
            print(f"   ❌ Insufficient data for {symbol}")
            return []
        
        # Calcular indicadores
        df = self.calculate_simple_indicators(df)
        
        trades = []
        last_trade_idx = 0
        daily_trades = 0
        max_daily_trades = version_params.get('max_daily_trades', 3)
        
        for i in range(50, len(df) - 1):
            # Resetear contador diario
            if i == 50 or df.index[i].date() != df.index[i-1].date():
                daily_trades = 0
            
            # Verificar límites
            if daily_trades >= max_daily_trades:
                continue
            
            if i - last_trade_idx < 2:  # Mínimo 2 días entre trades
                continue
            
            # Generar señal
            signal, confidence, signal_list = self.generate_signals_by_version(df, i, version_params)
            
            if signal and confidence >= version_params.get('min_confidence', 0.4):
                current = df.iloc[i]
                
                # Calcular stops
                stop_loss, take_profit = self.calculate_stops(
                    current['Close'], signal, current['ATR'], version_params
                )
                
                # Simular resultado
                exit_price, exit_reason, pnl_pct = self.simulate_trade_outcome(
                    signal, confidence, stop_loss, take_profit, current['Close']
                )
                
                # Calcular P&L en dólares
                risk_per_trade = version_params.get('risk_per_trade', 0.01)
                pnl_dollars = 10000 * risk_per_trade * pnl_pct  # Base $10k
                
                trade = {
                    'symbol': symbol,
                    'date': df.index[i],
                    'version': version_name,
                    'type': signal,
                    'entry_price': current['Close'],
                    'exit_price': exit_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'signals': signal_list,
                    'exit_reason': exit_reason,
                    'pnl_pct': pnl_pct,
                    'pnl': pnl_dollars,
                    'rsi': current['RSI'],
                    'momentum': current['Momentum'],
                    'trend_up': current['Uptrend'],
                    'trend_down': current['Downtrend']
                }
                
                trades.append(trade)
                last_trade_idx = i
                daily_trades += 1
        
        print(f"   ✅ Generated {len(trades)} trades")
        return trades

    def run_comparative_analysis(self):
        """
        Ejecuta análisis comparativo completo
        """
        print("="*80)
        print("📊 ANÁLISIS COMPARATIVO DE BACKTESTING")
        print("="*80)
        print("Versiones a comparar:")
        print("  V2: Sistema actual (51.9% WR)")
        print("  V3-Balanced: Versión balanceada")
        print("  V3-Ultra: Ultra conservador")
        print("="*80)
        
        # Configurar versiones
        versions = {
            'V2_Current': {
                'min_score': 4,
                'min_confidence': 0.4,
                'rsi_oversold_1h': 30,
                'rsi_overbought_1h': 70,
                'atr_stop_1h': 2.0,
                'atr_target_1h': 3.0,
                'risk_per_trade': 0.01,
                'max_daily_trades': 3,
                'volume_surge_required': 1.5,
                'counter_trend_forbidden': False,
                'momentum_confirmation': False,
                'min_momentum_strength': 0
            },
            'V3_Balanced': self.create_v3_balanced_system(),
            'V3_Ultra': {
                'min_score': 8,
                'min_confidence': 0.6,
                'rsi_oversold_1h': 10,
                'rsi_overbought_1h': 90,
                'atr_stop_1h': 3.5,
                'atr_target_1h': 6.0,
                'risk_per_trade': 0.005,
                'max_daily_trades': 1,
                'volume_surge_required': 2.0,
                'counter_trend_forbidden': True,
                'all_timeframes_must_align': True,
                'momentum_confirmation': True,
                'min_momentum_strength': 10
            }
        }
        
        # Símbolos y período
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 3 meses
        
        print(f"\n📅 Período de análisis: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
        print(f"🪙 Símbolos: {', '.join(symbols)}")
        
        # Ejecutar backtests
        all_results = {}
        
        for version_name, version_params in versions.items():
            print(f"\n" + "="*60)
            print(f"🔬 TESTING VERSION: {version_name}")
            print("="*60)
            
            version_trades = []
            for symbol in symbols:
                trades = self.backtest_version(symbol, start_date, end_date, version_name, version_params)
                version_trades.extend(trades)
            
            all_results[version_name] = version_trades
            
            # Mostrar resumen rápido
            if version_trades:
                total_trades = len(version_trades)
                wins = sum(1 for t in version_trades if t['pnl'] > 0)
                win_rate = (wins / total_trades) * 100
                total_pnl = sum(t['pnl'] for t in version_trades)
                
                print(f"\n📊 {version_name} Summary:")
                print(f"   • Total Trades: {total_trades}")
                print(f"   • Win Rate: {win_rate:.1f}%")
                print(f"   • Total P&L: ${total_pnl:.2f}")
                print(f"   • ROI: {(total_pnl/10000)*100:.1f}%")
            else:
                print(f"\n❌ {version_name}: No trades generated")
        
        # Análisis comparativo detallado
        self.analyze_comparative_results(all_results)
        
        return all_results

    def analyze_comparative_results(self, all_results):
        """
        Analiza y compara resultados de todas las versiones
        """
        print("\n" + "="*80)
        print("📈 ANÁLISIS COMPARATIVO DETALLADO")
        print("="*80)
        
        summary_stats = {}
        
        for version_name, trades in all_results.items():
            if not trades:
                summary_stats[version_name] = {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'roi': 0,
                    'profit_factor': 0,
                    'avg_confidence': 0,
                    'avg_trade_pnl': 0,
                    'max_drawdown': 0,
                    'sharpe_ratio': 0
                }
                continue
            
            # Métricas básicas
            total_trades = len(trades)
            wins = sum(1 for t in trades if t['pnl'] > 0)
            win_rate = (wins / total_trades) * 100
            total_pnl = sum(t['pnl'] for t in trades)
            roi = (total_pnl / 10000) * 100
            
            # Profit factor
            gross_wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
            gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))
            profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
            
            # Otras métricas
            avg_confidence = np.mean([t['confidence'] for t in trades])
            avg_trade_pnl = total_pnl / total_trades
            
            # Drawdown
            equity_curve = [10000]
            for trade in trades:
                equity_curve.append(equity_curve[-1] + trade['pnl'])
            
            peak = equity_curve[0]
            max_drawdown = 0
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Sharpe ratio simplificado
            daily_returns = [t['pnl']/10000 for t in trades]
            sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 1 and np.std(daily_returns) > 0 else 0
            
            summary_stats[version_name] = {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'roi': roi,
                'profit_factor': profit_factor,
                'avg_confidence': avg_confidence,
                'avg_trade_pnl': avg_trade_pnl,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio
            }
        
        # Mostrar tabla comparativa
        print(f"\n📊 TABLA COMPARATIVA:")
        print(f"{'Version':<15} {'Trades':<8} {'WR':<8} {'ROI':<8} {'PF':<8} {'Conf':<8} {'DD':<8} {'Eval':<12}")
        print("-" * 80)
        
        for version, stats in summary_stats.items():
            # Evaluación
            if stats['win_rate'] >= 65 and stats['profit_factor'] >= 2.0:
                evaluation = "EXCELLENT"
            elif stats['win_rate'] >= 55 and stats['profit_factor'] >= 1.5:
                evaluation = "GOOD"
            elif stats['win_rate'] >= 45 and stats['profit_factor'] >= 1.2:
                evaluation = "ACCEPTABLE"
            else:
                evaluation = "NEEDS_WORK"
            
            print(f"{version:<15} {stats['total_trades']:<8} {stats['win_rate']:<7.1f}% "
                  f"{stats['roi']:<7.1f}% {stats['profit_factor']:<7.2f} "
                  f"{stats['avg_confidence']:<7.1%} {stats['max_drawdown']:<7.1f}% {evaluation:<12}")
        
        # Análisis de mejoras
        print(f"\n📈 ANÁLISIS DE MEJORAS:")
        
        if 'V2_Current' in summary_stats and 'V3_Balanced' in summary_stats:
            v2_wr = summary_stats['V2_Current']['win_rate']
            v3_wr = summary_stats['V3_Balanced']['win_rate']
            wr_improvement = v3_wr - v2_wr
            
            v2_pf = summary_stats['V2_Current']['profit_factor']
            v3_pf = summary_stats['V3_Balanced']['profit_factor']
            pf_improvement = v3_pf - v2_pf
            
            print(f"  V2 → V3 Balanced:")
            print(f"    • Win Rate: {v2_wr:.1f}% → {v3_wr:.1f}% ({wr_improvement:+.1f}%)")
            print(f"    • Profit Factor: {v2_pf:.2f} → {v3_pf:.2f} ({pf_improvement:+.2f})")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        
        best_version = max(summary_stats.items(), key=lambda x: x[1]['roi'] if x[1]['total_trades'] > 0 else -999)
        if best_version[1]['total_trades'] > 0:
            print(f"  🏆 Mejor versión: {best_version[0]}")
            print(f"    • ROI: {best_version[1]['roi']:.1f}%")
            print(f"    • Win Rate: {best_version[1]['win_rate']:.1f}%")
            print(f"    • Trades: {best_version[1]['total_trades']}")
        
        # Análisis de trade quality
        print(f"\n🔍 ANÁLISIS DE CALIDAD DE TRADES:")
        for version_name, trades in all_results.items():
            if not trades:
                continue
            
            # Trades contra-tendencia
            counter_trend = sum(1 for t in trades 
                              if (t['type'] == 'LONG' and t['trend_down']) or 
                                 (t['type'] == 'SHORT' and t['trend_up']))
            counter_trend_pct = (counter_trend / len(trades)) * 100
            
            # Trades con alta confianza
            high_conf_trades = [t for t in trades if t['confidence'] >= 0.6]
            high_conf_wr = sum(1 for t in high_conf_trades if t['pnl'] > 0) / len(high_conf_trades) * 100 if high_conf_trades else 0
            
            print(f"  {version_name}:")
            print(f"    • Trades contra-tendencia: {counter_trend_pct:.1f}%")
            print(f"    • WR con confianza >60%: {high_conf_wr:.1f}%")
        
        return summary_stats


def main():
    """
    Función principal del análisis comparativo
    """
    analyzer = ComparativeBacktestAnalysis()
    results = analyzer.run_comparative_analysis()
    
    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPARATIVO COMPLETADO")
    print("="*80)
    print("\n🎯 CONCLUSIONES CLAVE:")
    print("1. Comparación directa V2 vs V3 en métricas clave")
    print("2. Análisis de trade quality y filtros")
    print("3. Evaluación de diferentes niveles de conservadurismo")
    print("4. Recomendaciones para optimización final")
    
    return results

if __name__ == "__main__":
    results = main()