#!/usr/bin/env python3
"""
Análisis Detallado de Trades Perdedores
Investiga por qué ciertos trades generaron pérdidas
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

from daily_trading_system import DailyTradingSystem

class LossAnalyzer:
    """
    Analiza trades perdedores para identificar patrones y problemas
    """
    
    def __init__(self):
        self.system = DailyTradingSystem(initial_capital=10000)
        self.losing_trades = []
        self.winning_trades = []
        
    def run_detailed_backtest(self, symbols, start_date, end_date):
        """
        Ejecuta backtest detallado capturando información completa de cada trade
        """
        all_trades = []
        
        current_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        
        while current_date <= end_date:
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            for symbol in symbols:
                # Obtener indicadores
                indicators = self.system.calculate_multi_timeframe_indicators(symbol, current_date)
                
                if not indicators:
                    continue
                
                # Generar señales
                signal, confidence, signal_list, score = self.system.generate_daily_signals(symbol, indicators)
                
                if signal and confidence >= 0.3:
                    # Simular trade con más detalle
                    entry_price = indicators[list(indicators.keys())[0]]['close']
                    stop_loss, take_profit = self.system.calculate_dynamic_stops(
                        entry_price, signal, indicators
                    )
                    
                    # Obtener datos futuros para simular resultado real
                    ticker = yf.Ticker(symbol)
                    future_start = current_date + timedelta(days=1)
                    future_end = current_date + timedelta(days=10)
                    future_data = ticker.history(start=future_start, end=future_end, interval='1h')
                    
                    if len(future_data) > 0:
                        # Simular resultado basado en datos reales
                        trade_result = self.simulate_trade_outcome(
                            signal, entry_price, stop_loss, take_profit, future_data
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
                            'signals': signal_list,
                            'indicators': self.extract_key_indicators(indicators),
                            **trade_result
                        }
                        
                        all_trades.append(trade)
                        
                        if trade['pnl'] < 0:
                            self.losing_trades.append(trade)
                        else:
                            self.winning_trades.append(trade)
            
            current_date += timedelta(days=1)
        
        return all_trades
    
    def simulate_trade_outcome(self, signal_type, entry_price, stop_loss, take_profit, future_data):
        """
        Simula el resultado del trade basado en datos futuros reales
        """
        exit_price = None
        exit_reason = None
        exit_time = None
        
        for idx, row in future_data.iterrows():
            if signal_type == 'LONG':
                # Check stop loss
                if row['Low'] <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'Stop Loss Hit'
                    exit_time = idx
                    break
                # Check take profit
                elif row['High'] >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'Take Profit Hit'
                    exit_time = idx
                    break
            else:  # SHORT
                # Check stop loss
                if row['High'] >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'Stop Loss Hit'
                    exit_time = idx
                    break
                # Check take profit
                elif row['Low'] <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'Take Profit Hit'
                    exit_time = idx
                    break
        
        # Si no se alcanzó ningún stop, usar último precio
        if exit_price is None:
            exit_price = future_data['Close'].iloc[-1]
            exit_reason = 'Time Exit'
            exit_time = future_data.index[-1]
        
        # Calcular P&L
        if signal_type == 'LONG':
            pnl_pct = ((exit_price / entry_price) - 1) * 100
        else:
            pnl_pct = ((entry_price / exit_price) - 1) * 100
        
        pnl = 10000 * 0.01 * pnl_pct  # 1% position size
        
        return {
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'exit_time': exit_time,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'hours_in_trade': (exit_time - future_data.index[0]).total_seconds() / 3600 if exit_time else 0
        }
    
    def extract_key_indicators(self, indicators):
        """
        Extrae indicadores clave para análisis
        """
        key_indicators = {}
        
        for tf, data in indicators.items():
            key_indicators[f'{tf}_rsi'] = data.get('rsi', 0)
            key_indicators[f'{tf}_macd_histogram'] = data.get('macd_histogram', 0)
            key_indicators[f'{tf}_bb_position'] = data.get('bb_position', 0.5)
            key_indicators[f'{tf}_volume_ratio'] = data.get('volume_ratio', 1)
            key_indicators[f'{tf}_momentum'] = data.get('momentum', 0)
            key_indicators[f'{tf}_trend_up'] = data.get('trend_up', False)
            key_indicators[f'{tf}_trend_down'] = data.get('trend_down', False)
        
        return key_indicators
    
    def analyze_losing_patterns(self):
        """
        Analiza patrones comunes en trades perdedores
        """
        if not self.losing_trades:
            print("No hay trades perdedores para analizar")
            return
        
        print("\n" + "="*80)
        print("🔍 ANÁLISIS DE TRADES PERDEDORES")
        print("="*80)
        
        print(f"\n📊 ESTADÍSTICAS GENERALES:")
        print(f"  • Total trades perdedores: {len(self.losing_trades)}")
        print(f"  • Total trades ganadores: {len(self.winning_trades)}")
        win_rate = len(self.winning_trades) / (len(self.winning_trades) + len(self.losing_trades)) * 100
        print(f"  • Win Rate: {win_rate:.1f}%")
        
        # 1. Análisis por tipo de señal
        print("\n📈 ANÁLISIS POR TIPO DE SEÑAL:")
        long_losses = [t for t in self.losing_trades if t['type'] == 'LONG']
        short_losses = [t for t in self.losing_trades if t['type'] == 'SHORT']
        
        print(f"  • LONG perdedores: {len(long_losses)} ({len(long_losses)/len(self.losing_trades)*100:.1f}%)")
        print(f"  • SHORT perdedores: {len(short_losses)} ({len(short_losses)/len(self.losing_trades)*100:.1f}%)")
        
        # 2. Análisis por razón de salida
        print("\n🚪 RAZÓN DE SALIDA EN PÉRDIDAS:")
        exit_reasons = {}
        for trade in self.losing_trades:
            reason = trade.get('exit_reason', 'Unknown')
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(self.losing_trades) * 100
            print(f"  • {reason}: {count} trades ({pct:.1f}%)")
        
        # 3. Análisis por símbolo
        print("\n🪙 PÉRDIDAS POR SÍMBOLO:")
        symbol_losses = {}
        for trade in self.losing_trades:
            symbol = trade['symbol']
            if symbol not in symbol_losses:
                symbol_losses[symbol] = {'count': 0, 'total_loss': 0}
            symbol_losses[symbol]['count'] += 1
            symbol_losses[symbol]['total_loss'] += trade['pnl']
        
        for symbol, data in sorted(symbol_losses.items(), key=lambda x: x[1]['count'], reverse=True):
            avg_loss = data['total_loss'] / data['count']
            print(f"  • {symbol}: {data['count']} pérdidas, promedio ${avg_loss:.2f}")
        
        # 4. Análisis de señales falsas
        print("\n⚠️ SEÑALES MÁS COMUNES EN PÉRDIDAS:")
        signal_frequency = {}
        for trade in self.losing_trades:
            for signal in trade.get('signals', []):
                signal_frequency[signal] = signal_frequency.get(signal, 0) + 1
        
        top_signals = sorted(signal_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        for signal, count in top_signals:
            pct = count / len(self.losing_trades) * 100
            print(f"  • {signal}: {count} veces ({pct:.1f}%)")
        
        # 5. Análisis de confianza
        print("\n📊 ANÁLISIS DE CONFIANZA:")
        losing_confidences = [t['confidence'] for t in self.losing_trades]
        winning_confidences = [t['confidence'] for t in self.winning_trades] if self.winning_trades else [0]
        
        print(f"  • Confianza promedio en pérdidas: {np.mean(losing_confidences):.2%}")
        print(f"  • Confianza promedio en ganancias: {np.mean(winning_confidences):.2%}")
        
        # Distribución de confianza
        low_conf_losses = len([c for c in losing_confidences if c < 0.4])
        med_conf_losses = len([c for c in losing_confidences if 0.4 <= c < 0.6])
        high_conf_losses = len([c for c in losing_confidences if c >= 0.6])
        
        print(f"\n  Distribución de confianza en pérdidas:")
        print(f"  • Baja (<40%): {low_conf_losses} trades")
        print(f"  • Media (40-60%): {med_conf_losses} trades")
        print(f"  • Alta (>60%): {high_conf_losses} trades")
        
        # 6. Análisis de indicadores
        print("\n📉 INDICADORES PROMEDIO EN PÉRDIDAS vs GANANCIAS:")
        self.compare_indicator_averages()
        
        # 7. Análisis temporal
        print("\n⏰ DURACIÓN DE TRADES PERDEDORES:")
        durations = [t.get('hours_in_trade', 0) for t in self.losing_trades if t.get('hours_in_trade')]
        if durations:
            print(f"  • Duración promedio: {np.mean(durations):.1f} horas")
            print(f"  • Duración mínima: {min(durations):.1f} horas")
            print(f"  • Duración máxima: {max(durations):.1f} horas")
        
        # 8. Identificar problemas principales
        self.identify_main_problems()
    
    def compare_indicator_averages(self):
        """
        Compara promedios de indicadores entre trades ganadores y perdedores
        """
        if not self.winning_trades:
            print("  No hay trades ganadores para comparar")
            return
        
        # Extraer indicadores clave
        indicators_to_compare = ['15m_rsi', '1h_rsi', '15m_momentum', '1h_momentum', 
                                 '15m_volume_ratio', '1h_volume_ratio']
        
        for indicator in indicators_to_compare:
            losing_values = [t['indicators'].get(indicator, 0) for t in self.losing_trades 
                           if 'indicators' in t]
            winning_values = [t['indicators'].get(indicator, 0) for t in self.winning_trades 
                            if 'indicators' in t]
            
            if losing_values and winning_values:
                avg_losing = np.mean(losing_values)
                avg_winning = np.mean(winning_values)
                diff = ((avg_winning - avg_losing) / avg_losing * 100) if avg_losing != 0 else 0
                
                print(f"  • {indicator}:")
                print(f"    - En pérdidas: {avg_losing:.2f}")
                print(f"    - En ganancias: {avg_winning:.2f}")
                print(f"    - Diferencia: {diff:+.1f}%")
    
    def identify_main_problems(self):
        """
        Identifica los problemas principales del sistema
        """
        print("\n" + "="*80)
        print("🔴 PROBLEMAS PRINCIPALES IDENTIFICADOS:")
        print("="*80)
        
        problems = []
        
        # Problema 1: Señales en contra-tendencia
        counter_trend = 0
        for trade in self.losing_trades:
            indicators = trade.get('indicators', {})
            if trade['type'] == 'LONG' and indicators.get('1h_trend_down', False):
                counter_trend += 1
            elif trade['type'] == 'SHORT' and indicators.get('1h_trend_up', False):
                counter_trend += 1
        
        if counter_trend > len(self.losing_trades) * 0.3:
            pct = counter_trend / len(self.losing_trades) * 100
            problems.append(f"📌 {pct:.1f}% de pérdidas son trades contra-tendencia")
        
        # Problema 2: Baja confianza
        low_conf = len([t for t in self.losing_trades if t['confidence'] < 0.4])
        if low_conf > len(self.losing_trades) * 0.4:
            pct = low_conf / len(self.losing_trades) * 100
            problems.append(f"📌 {pct:.1f}% de pérdidas tienen confianza <40%")
        
        # Problema 3: Stop loss muy ajustado
        sl_hits = len([t for t in self.losing_trades if 'Stop Loss' in t.get('exit_reason', '')])
        if sl_hits > len(self.losing_trades) * 0.7:
            pct = sl_hits / len(self.losing_trades) * 100
            problems.append(f"📌 {pct:.1f}% de pérdidas por stop loss (posiblemente muy ajustado)")
        
        # Problema 4: Símbolos específicos problemáticos
        for symbol in ['ETH-USD', 'ADA-USD', 'BTC-USD']:
            symbol_losses = [t for t in self.losing_trades if t['symbol'] == symbol]
            symbol_wins = [t for t in self.winning_trades if t['symbol'] == symbol]
            if symbol_losses and len(symbol_losses) > len(symbol_wins) * 1.5:
                wr = len(symbol_wins) / (len(symbol_wins) + len(symbol_losses)) * 100
                problems.append(f"📌 {symbol} tiene win rate muy bajo: {wr:.1f}%")
        
        # Problema 5: Señales falsas recurrentes
        false_signals = ['VOLUME_SURGE_SHORT', 'RSI_OVERBOUGHT_15m', 'WEAK_MOMENTUM']
        for signal in false_signals:
            count = sum(1 for t in self.losing_trades if signal in t.get('signals', []))
            if count > len(self.losing_trades) * 0.3:
                pct = count / len(self.losing_trades) * 100
                problems.append(f"📌 Señal '{signal}' presente en {pct:.1f}% de pérdidas")
        
        # Imprimir problemas identificados
        for i, problem in enumerate(problems, 1):
            print(f"\n{i}. {problem}")
        
        # Recomendaciones
        print("\n" + "="*80)
        print("💡 RECOMENDACIONES PARA MEJORAR EL SISTEMA:")
        print("="*80)
        
        recommendations = [
            "1. 🎯 Aumentar el umbral mínimo de confianza de 30% a 40-45%",
            "2. 📊 Añadir filtro de tendencia: solo operar a favor de la tendencia dominante",
            "3. 🛡️ Ajustar multiplicadores ATR para stops menos ajustados (1.2 → 1.5)",
            "4. 🚫 Excluir o reducir peso de señales problemáticas identificadas",
            "5. 🪙 Considerar excluir símbolos con bajo rendimiento (ETH-USD)",
            "6. ⚖️ Implementar filtro de calidad: min_score de 4 → 5 o 6",
            "7. 📈 Añadir confirmación de volumen más estricta (1.5x en lugar de 1.3x)",
            "8. ⏰ Evitar primeras/últimas horas del día (mayor volatilidad errática)",
            "9. 🔄 Implementar trailing stop más agresivo para proteger ganancias",
            "10. 📉 Añadir filtro de volatilidad: evitar entradas en alta volatilidad"
        ]
        
        for rec in recommendations:
            print(f"\n{rec}")
        
        # Análisis de mejora potencial
        print("\n" + "="*80)
        print("📊 IMPACTO POTENCIAL DE MEJORAS:")
        print("="*80)
        
        # Simular mejoras
        filtered_losses = self.losing_trades.copy()
        
        # Filtrar por confianza > 40%
        before = len(filtered_losses)
        filtered_losses = [t for t in filtered_losses if t['confidence'] >= 0.4]
        after = len(filtered_losses)
        print(f"\n• Con confianza mínima 40%: -{before-after} trades perdedores")
        
        # Filtrar contra-tendencia
        before = len(filtered_losses)
        filtered_losses = [t for t in filtered_losses 
                          if not ((t['type'] == 'LONG' and t['indicators'].get('1h_trend_down', False)) or
                                 (t['type'] == 'SHORT' and t['indicators'].get('1h_trend_up', False)))]
        after = len(filtered_losses)
        print(f"• Eliminando contra-tendencia: -{before-after} trades perdedores adicionales")
        
        # Calcular nuevo win rate potencial
        new_losses = len(filtered_losses)
        new_total = new_losses + len(self.winning_trades)
        new_wr = len(self.winning_trades) / new_total * 100 if new_total > 0 else 0
        
        print(f"\n🎯 Win Rate potencial con mejoras: {new_wr:.1f}%")
        print(f"   (Actual: {win_rate:.1f}%)")


def main():
    """
    Ejecuta el análisis de trades perdedores
    """
    print("="*80)
    print("🔍 ANÁLISIS DETALLADO DE TRADES PERDEDORES")
    print("="*80)
    
    analyzer = LossAnalyzer()
    
    # Símbolos y período de análisis
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'MATIC-USD']
    end_date = datetime(2024, 11, 15)
    start_date = end_date - timedelta(days=30)
    
    print(f"\n📅 Período de análisis: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    print(f"🪙 Símbolos: {', '.join(symbols)}")
    print("\n⏳ Ejecutando backtest detallado...")
    
    # Ejecutar backtest
    trades = analyzer.run_detailed_backtest(symbols, start_date, end_date)
    
    print(f"\n✅ Backtest completado: {len(trades)} trades totales")
    print(f"   • Ganadores: {len(analyzer.winning_trades)}")
    print(f"   • Perdedores: {len(analyzer.losing_trades)}")
    
    # Analizar patrones de pérdidas
    analyzer.analyze_losing_patterns()
    
    return analyzer

if __name__ == "__main__":
    analyzer = main()