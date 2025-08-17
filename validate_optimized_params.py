#!/usr/bin/env python3
"""
Validación de Parámetros Optimizados
Ejecuta backtest completo con la configuración óptima encontrada
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

from scoring_empirico_v2 import ScoringEmpiricoV2

class OptimizedBacktester:
    """
    Backtester con parámetros optimizados
    """
    
    def __init__(self):
        # Cargar configuración óptima
        with open('optimal_config.json', 'r') as f:
            self.config = json.load(f)
        
        self.params = self.config['parameters']
        self.initial_capital = 10000
        self.scoring_system = ScoringEmpiricoV2()
        
        # Períodos de validación (los mismos 3 períodos)
        self.test_periods = [
            {
                'name': 'Q1_2024_BULL',
                'description': 'Mercado alcista - Rally Q1 2024',
                'start': '2024-01-01',
                'end': '2024-03-31'
            },
            {
                'name': 'Q2_2024_CORRECTION', 
                'description': 'Corrección - Q2 2024',
                'start': '2024-04-01',
                'end': '2024-06-30'
            },
            {
                'name': 'Q3_2024_RECOVERY',
                'description': 'Recuperación - Q3 2024',
                'start': '2024-07-01',
                'end': '2024-09-30'
            }
        ]
        
        self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
        
    def run_validation(self):
        """Ejecuta validación completa"""
        
        print("🎯 VALIDACIÓN DE PARÁMETROS OPTIMIZADOS")
        print("="*80)
        print(f"💰 Capital inicial: ${self.initial_capital:,}")
        print(f"📊 Símbolos: {', '.join(self.symbols)}")
        
        print("\n⚙️ PARÁMETROS OPTIMIZADOS:")
        print(f"  • Score Mínimo: {self.params['min_score']}")
        print(f"  • Stop Loss: {self.params['stop_loss_pct']*100:.0f}%")
        print(f"  • Take Profit: {self.params['take_profit_pct']*100:.0f}%")
        print(f"  • Position Size: {self.params['position_size_pct']*100:.0f}%")
        print(f"  • Leverage Base: {self.params['leverage_base']}x")
        print(f"  • RSI Oversold: {self.params['rsi_oversold']}")
        print(f"  • RSI Overbought: {self.params['rsi_overbought']}")
        
        print("\n📊 MÉTRICAS ESPERADAS (de calibración):")
        expected_metrics = self.config['metrics']
        print(f"  • Win Rate: {expected_metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {expected_metrics['profit_factor']:.2f}")
        print(f"  • Total Return: {expected_metrics['total_return']:.1f}%")
        
        print("="*80)
        
        all_trades = []
        period_results = {}
        
        for period in self.test_periods:
            print(f"\n📅 PERÍODO: {period['name']}")
            print(f"📝 {period['description']}")
            print(f"📆 {period['start']} → {period['end']}")
            print("-"*60)
            
            period_trades = []
            
            for symbol in self.symbols:
                symbol_trades = self.backtest_symbol(
                    symbol, 
                    period['start'], 
                    period['end']
                )
                
                if symbol_trades:
                    period_trades.extend(symbol_trades)
                    print(f"  • {symbol}: {len(symbol_trades)} trades")
            
            all_trades.extend(period_trades)
            period_results[period['name']] = period_trades
            
            # Resumen del período
            if period_trades:
                period_metrics = self.calculate_metrics(period_trades)
                self.print_period_summary(period['name'], period_metrics)
        
        # Análisis global
        print("\n" + "="*80)
        print("📊 ANÁLISIS GLOBAL - VALIDACIÓN COMPLETA")
        print("="*80)
        
        if all_trades:
            global_metrics = self.calculate_metrics(all_trades)
            self.print_global_results(global_metrics, all_trades)
            
            # Comparar con expectativas
            self.compare_with_expectations(global_metrics, expected_metrics)
        else:
            print("❌ No se generaron trades")
        
        return all_trades, period_results
    
    def backtest_symbol(self, symbol, start_date, end_date):
        """Ejecuta backtest para un símbolo"""
        
        try:
            # Obtener datos
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(data) < 20:
                return []
            
            # Preparar indicadores
            data = self.prepare_indicators(data)
            
            # Variables de trading
            trades = []
            position = None
            capital = self.initial_capital
            
            # Iterar por los datos
            for i in range(20, len(data)):
                current = data.iloc[i]
                prev = data.iloc[i-1]
                
                # Si no hay posición, buscar entrada
                if position is None:
                    signal_type, score = self.generate_signal(
                        data.iloc[:i+1], current, prev
                    )
                    
                    if signal_type and score >= self.params['min_score']:
                        # Abrir posición
                        position = {
                            'symbol': symbol,
                            'type': signal_type,
                            'entry_date': current.name,
                            'entry_price': float(current['Close']),
                            'score': score
                        }
                        
                        # Calcular stops con parámetros optimizados
                        if signal_type == 'LONG':
                            position['stop_loss'] = position['entry_price'] * (1 - self.params['stop_loss_pct'])
                            position['take_profit'] = position['entry_price'] * (1 + self.params['take_profit_pct'])
                        else:
                            position['stop_loss'] = position['entry_price'] * (1 + self.params['stop_loss_pct'])
                            position['take_profit'] = position['entry_price'] * (1 - self.params['take_profit_pct'])
                
                # Si hay posición, verificar salida
                elif position:
                    exit_signal = False
                    exit_price = float(current['Close'])
                    exit_reason = None
                    
                    # Verificar stops
                    if position['type'] == 'LONG':
                        if current['Low'] <= position['stop_loss']:
                            exit_signal = True
                            exit_price = position['stop_loss']
                            exit_reason = 'STOP_LOSS'
                        elif current['High'] >= position['take_profit']:
                            exit_signal = True
                            exit_price = position['take_profit']
                            exit_reason = 'TAKE_PROFIT'
                    else:  # SHORT
                        if current['High'] >= position['stop_loss']:
                            exit_signal = True
                            exit_price = position['stop_loss']
                            exit_reason = 'STOP_LOSS'
                        elif current['Low'] <= position['take_profit']:
                            exit_signal = True
                            exit_price = position['take_profit']
                            exit_reason = 'TAKE_PROFIT'
                    
                    if exit_signal:
                        # Cerrar posición
                        position['exit_date'] = current.name
                        position['exit_price'] = exit_price
                        position['exit_reason'] = exit_reason
                        
                        # Calcular return
                        if position['type'] == 'LONG':
                            position['return_pct'] = ((exit_price / position['entry_price']) - 1) * 100
                        else:
                            position['return_pct'] = ((position['entry_price'] / exit_price) - 1) * 100
                        
                        # Aplicar leverage y comisiones
                        position['return_pct'] *= self.params['leverage_base']
                        position['return_pct'] -= 0.2  # Comisiones
                        
                        position['pnl'] = capital * self.params['position_size_pct'] * (position['return_pct'] / 100)
                        position['duration_days'] = (position['exit_date'] - position['entry_date']).days
                        
                        trades.append(position)
                        position = None
            
            # Cerrar posición final si queda abierta
            if position:
                position['exit_date'] = data.iloc[-1].name
                position['exit_price'] = float(data.iloc[-1]['Close'])
                position['exit_reason'] = 'END_PERIOD'
                
                if position['type'] == 'LONG':
                    position['return_pct'] = ((position['exit_price'] / position['entry_price']) - 1) * 100
                else:
                    position['return_pct'] = ((position['entry_price'] / position['exit_price']) - 1) * 100
                
                position['return_pct'] *= self.params['leverage_base']
                position['return_pct'] -= 0.2
                
                position['pnl'] = capital * self.params['position_size_pct'] * (position['return_pct'] / 100)
                position['duration_days'] = (position['exit_date'] - position['entry_date']).days
                
                trades.append(position)
            
            return trades
            
        except Exception as e:
            return []
    
    def prepare_indicators(self, df):
        """Prepara indicadores técnicos"""
        
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
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA'].replace(0, 1)
        df['Volume_Ratio'] = df['Volume_Ratio'].fillna(1.0).clip(lower=0.1)
        
        return df
    
    def generate_signal(self, df, current, prev):
        """Genera señal con parámetros optimizados"""
        
        try:
            # Usar sistema de scoring
            signal_type, score = self.scoring_system.evaluar_entrada(df, current, prev)
            
            # Aplicar overrides con parámetros optimizados
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            
            # Condiciones con parámetros optimizados
            if rsi <= self.params['rsi_oversold'] and macd > macd_signal:
                if signal_type != 'SHORT':
                    return 'LONG', max(score, self.params['min_score'] + 0.5)
            elif rsi >= self.params['rsi_overbought'] and macd < macd_signal:
                if signal_type != 'LONG':
                    return 'SHORT', max(score, self.params['min_score'] + 0.5)
            
            return signal_type, score
            
        except:
            # Fallback simple
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            
            if rsi <= self.params['rsi_oversold'] and macd > macd_signal:
                return 'LONG', self.params['min_score'] + 0.5
            elif rsi >= self.params['rsi_overbought'] and macd < macd_signal:
                return 'SHORT', self.params['min_score'] + 0.5
            
            return None, 0
    
    def calculate_metrics(self, trades):
        """Calcula métricas de performance"""
        
        if not trades:
            return {}
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['return_pct'] > 0)
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100)
        
        # Profit factor
        wins = sum(t['return_pct'] for t in trades if t['return_pct'] > 0)
        losses = abs(sum(t['return_pct'] for t in trades if t['return_pct'] < 0))
        profit_factor = wins / losses if losses > 0 else float('inf') if wins > 0 else 0
        
        # Returns
        total_return = sum(t['return_pct'] for t in trades)
        avg_return = total_return / total_trades if total_trades > 0 else 0
        
        # PnL en dólares
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        # Duración promedio
        avg_duration = np.mean([t.get('duration_days', 0) for t in trades])
        
        # Por tipo de salida
        exit_reasons = {}
        for trade in trades:
            reason = trade.get('exit_reason', 'UNKNOWN')
            if reason not in exit_reasons:
                exit_reasons[reason] = {'count': 0, 'return': 0}
            exit_reasons[reason]['count'] += 1
            exit_reasons[reason]['return'] += trade['return_pct']
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'avg_return': avg_return,
            'total_pnl': total_pnl,
            'avg_duration': avg_duration,
            'exit_reasons': exit_reasons
        }
    
    def print_period_summary(self, period_name, metrics):
        """Imprime resumen del período"""
        
        print(f"\n📊 Métricas {period_name}:")
        print(f"  • Trades: {metrics['total_trades']}")
        print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  • Return: {metrics['total_return']:.1f}%")
    
    def print_global_results(self, metrics, all_trades):
        """Imprime resultados globales"""
        
        print(f"\n📈 MÉTRICAS GLOBALES:")
        print(f"  • Total Trades: {metrics['total_trades']}")
        print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  • Total Return: {metrics['total_return']:.1f}%")
        print(f"  • Avg Return per Trade: {metrics['avg_return']:.2f}%")
        print(f"  • Total P&L: ${metrics['total_pnl']:,.2f}")
        print(f"  • Avg Duration: {metrics['avg_duration']:.1f} días")
        
        # Análisis por tipo de salida
        print(f"\n📊 ANÁLISIS DE SALIDAS:")
        for reason, data in metrics['exit_reasons'].items():
            pct = (data['count'] / metrics['total_trades']) * 100
            print(f"  • {reason}: {data['count']} trades ({pct:.1f}%), Return: {data['return']:.1f}%")
        
        # Análisis por símbolo
        symbol_performance = {}
        for trade in all_trades:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {'count': 0, 'return': 0}
            symbol_performance[symbol]['count'] += 1
            symbol_performance[symbol]['return'] += trade['return_pct']
        
        print(f"\n📊 PERFORMANCE POR SÍMBOLO:")
        for symbol, perf in sorted(symbol_performance.items(), key=lambda x: x[1]['return'], reverse=True):
            if perf['count'] > 0:
                print(f"  • {symbol}: {perf['count']} trades, Return: {perf['return']:.1f}%")
        
        # Mejor y peor trade
        if all_trades:
            best_trade = max(all_trades, key=lambda x: x['return_pct'])
            worst_trade = min(all_trades, key=lambda x: x['return_pct'])
            
            print(f"\n🏆 MEJORES Y PEORES:")
            print(f"  • Mejor Trade: {best_trade['symbol']} +{best_trade['return_pct']:.1f}% ({best_trade['entry_date'].strftime('%Y-%m-%d')})")
            print(f"  • Peor Trade: {worst_trade['symbol']} {worst_trade['return_pct']:.1f}% ({worst_trade['entry_date'].strftime('%Y-%m-%d')})")
    
    def compare_with_expectations(self, actual_metrics, expected_metrics):
        """Compara resultados con expectativas"""
        
        print(f"\n" + "="*80)
        print("📊 COMPARACIÓN CON EXPECTATIVAS")
        print("-"*60)
        
        print(f"\n{'Métrica':<20} {'Esperado':<15} {'Real':<15} {'Diferencia':<15}")
        print("-"*65)
        
        # Win Rate
        expected_wr = expected_metrics['win_rate']
        actual_wr = actual_metrics['win_rate']
        diff_wr = actual_wr - expected_wr
        status_wr = "✅" if diff_wr >= -5 else "⚠️" if diff_wr >= -10 else "❌"
        print(f"{'Win Rate':<20} {expected_wr:<14.1f}% {actual_wr:<14.1f}% {diff_wr:+<14.1f}% {status_wr}")
        
        # Profit Factor
        expected_pf = expected_metrics['profit_factor']
        actual_pf = actual_metrics['profit_factor']
        diff_pf = actual_pf - expected_pf
        status_pf = "✅" if diff_pf >= -0.5 else "⚠️" if diff_pf >= -1 else "❌"
        print(f"{'Profit Factor':<20} {expected_pf:<14.2f} {actual_pf:<14.2f} {diff_pf:+<14.2f} {status_pf}")
        
        # Total Return
        expected_ret = expected_metrics['total_return']
        actual_ret = actual_metrics['total_return']
        diff_ret = actual_ret - expected_ret
        status_ret = "✅" if diff_ret >= -5 else "⚠️" if diff_ret >= -10 else "❌"
        print(f"{'Total Return':<20} {expected_ret:<14.1f}% {actual_ret:<14.1f}% {diff_ret:+<14.1f}% {status_ret}")
        
        # Evaluación general
        print(f"\n🎯 EVALUACIÓN:")
        
        if actual_wr >= expected_wr - 5 and actual_pf >= expected_pf - 0.5:
            print("✅ VALIDACIÓN EXITOSA - Sistema funcionando según expectativas")
            print("   • Los parámetros optimizados son confiables")
            print("   • Listo para paper trading")
        elif actual_wr >= expected_wr - 10 and actual_pf >= expected_pf - 1:
            print("⚠️ VALIDACIÓN PARCIAL - Desempeño ligeramente inferior")
            print("   • Considerar ajustes menores")
            print("   • Monitorear en paper trading")
        else:
            print("❌ VALIDACIÓN FALLIDA - Desempeño significativamente inferior")
            print("   • Requiere recalibración")
            print("   • No usar en producción")

def main():
    """Función principal"""
    
    print("🚀 INICIANDO VALIDACIÓN DE PARÁMETROS OPTIMIZADOS")
    print("="*80)
    
    validator = OptimizedBacktester()
    trades, period_results = validator.run_validation()
    
    print("\n" + "="*80)
    print("✅ VALIDACIÓN COMPLETADA")
    print("="*80)
    
    # Recomendaciones finales
    print("\n💡 PRÓXIMOS PASOS RECOMENDADOS:")
    
    if trades and len(trades) >= 10:
        metrics = validator.calculate_metrics(trades)
        
        if metrics['win_rate'] >= 50 and metrics['profit_factor'] >= 1.5:
            print("1. ✅ Iniciar paper trading inmediatamente")
            print("2. 📊 Monitorear por 30 días")
            print("3. 💰 Si mantiene métricas, comenzar con $1,000 real")
            print("4. 📈 Escalar gradualmente según resultados")
        else:
            print("1. ⚠️ Ajustar parámetros basado en resultados")
            print("2. 🔄 Ejecutar nueva calibración")
            print("3. 📊 Validar nuevamente antes de paper trading")
    else:
        print("1. ❌ Sistema genera muy pocos trades")
        print("2. 🔧 Revisar lógica de generación de señales")
        print("3. 📊 Considerar reducir threshold mínimo")
    
    return trades, period_results

if __name__ == "__main__":
    main()