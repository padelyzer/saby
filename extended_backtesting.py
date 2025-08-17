#!/usr/bin/env python3
"""
Backtesting Extendido con Configuración Óptima
Prueba el sistema en múltiples períodos y condiciones
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

from scoring_empirico_v2 import ScoringEmpiricoV2

class ExtendedBacktesting:
    """
    Backtesting completo con configuración optimizada
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.scoring_system = ScoringEmpiricoV2()
        
        # Cargar configuración óptima
        with open('quick_adaptive_config.json', 'r') as f:
            config_data = json.load(f)
            self.optimal_params = config_data['parameters']
        
        # Períodos de backtesting extendido
        self.test_periods = [
            # 2024 - Año completo hasta la fecha
            {
                'name': '2024_YTD',
                'description': 'Año 2024 completo',
                'start': '2024-01-01',
                'end': '2024-11-15',
                'expected_market': 'MIXED'
            },
            # Q4 2023 - Rally de fin de año
            {
                'name': 'Q4_2023_RALLY',
                'description': 'Rally Bitcoin ETF anticipation',
                'start': '2023-10-01',
                'end': '2023-12-31',
                'expected_market': 'BULL'
            },
            # Q3 2023 - Consolidación
            {
                'name': 'Q3_2023_CONSOLIDATION',
                'description': 'Consolidación de verano',
                'start': '2023-07-01',
                'end': '2023-09-30',
                'expected_market': 'SIDEWAYS'
            },
            # Q2 2023 - Recuperación
            {
                'name': 'Q2_2023_RECOVERY',
                'description': 'Recuperación post-banking crisis',
                'start': '2023-04-01',
                'end': '2023-06-30',
                'expected_market': 'RECOVERY'
            },
            # Q1 2023 - Inicio de recuperación
            {
                'name': 'Q1_2023_EARLY_RECOVERY',
                'description': 'Inicio de recuperación 2023',
                'start': '2023-01-01',
                'end': '2023-03-31',
                'expected_market': 'RECOVERY'
            }
        ]
        
        # Símbolos a testear
        self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
        
        self.all_trades = []
        self.period_results = {}
        
    def run_extended_backtesting(self):
        """Ejecuta backtesting extendido"""
        
        print("🚀 BACKTESTING EXTENDIDO CON CONFIGURACIÓN ÓPTIMA")
        print("="*80)
        print(f"💰 Capital inicial: ${self.initial_capital:,}")
        print(f"📊 Símbolos: {', '.join(self.symbols)}")
        print(f"📅 Períodos a testear: {len(self.test_periods)}")
        print(f"⏱️ Total días de trading: ~{sum([90 for _ in self.test_periods])} días")
        print("="*80)
        
        print("\n⚙️ CONFIGURACIÓN ÓPTIMA (Balanced):")
        print(f"  • Score Mínimo: {self.optimal_params['min_score']}")
        print(f"  • Stop Loss: {self.optimal_params['stop_loss_pct']*100:.1f}%")
        print(f"  • Take Profit: {self.optimal_params['take_profit_pct']*100:.1f}%")
        print(f"  • Position Size: {self.optimal_params['position_size_pct']*100:.1f}%")
        print(f"  • Leverage: {self.optimal_params['leverage_base']}x")
        print("="*80)
        
        # Ejecutar backtesting por período
        for period in self.test_periods:
            print(f"\n{'='*80}")
            print(f"📅 PERÍODO: {period['name']}")
            print(f"📝 {period['description']}")
            print(f"📆 {period['start']} → {period['end']}")
            print(f"🌍 Mercado esperado: {period['expected_market']}")
            print("="*80)
            
            period_trades = self.backtest_period(period)
            self.period_results[period['name']] = {
                'trades': period_trades,
                'metrics': self.calculate_metrics(period_trades)
            }
            
            # Mostrar resumen del período
            self.print_period_summary(period['name'], period_trades)
        
        # Análisis global
        self.print_global_analysis()
        
        # Análisis comparativo con calibración
        self.compare_with_calibration()
        
        return self.all_trades, self.period_results
    
    def backtest_period(self, period):
        """Ejecuta backtesting para un período específico"""
        
        period_trades = []
        
        for symbol in self.symbols:
            print(f"\n  🔍 Procesando {symbol}...")
            
            # Obtener datos
            data = self.get_historical_data(symbol, period['start'], period['end'])
            
            if data is None or len(data) < 20:
                print(f"    ⚠️ Datos insuficientes para {symbol}")
                continue
            
            # Ejecutar backtesting
            symbol_trades = self.backtest_symbol(
                symbol, 
                data, 
                period['expected_market']
            )
            
            period_trades.extend(symbol_trades)
            self.all_trades.extend(symbol_trades)
            
            if symbol_trades:
                wins = sum(1 for t in symbol_trades if t['return_pct'] > 0)
                print(f"    ✅ {len(symbol_trades)} trades ({wins} ganadores)")
            else:
                print(f"    ⚠️ No se generaron trades")
        
        return period_trades
    
    def get_historical_data(self, symbol, start_date, end_date):
        """Obtiene datos históricos"""
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(data) == 0:
                return None
            
            # Preparar indicadores
            data = self.prepare_indicators(data)
            
            return data
            
        except Exception as e:
            print(f"    ❌ Error obteniendo datos: {e}")
            return None
    
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
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # EMAs
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
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
    
    def backtest_symbol(self, symbol, data, market_type):
        """Ejecuta backtesting para un símbolo"""
        
        trades = []
        position = None
        
        # Ajustar parámetros según tipo de mercado
        adjusted_params = self.adjust_for_market(self.optimal_params, market_type)
        
        # Iterar por los datos
        for i in range(20, len(data)):
            current = data.iloc[i]
            prev = data.iloc[i-1]
            
            # Si no hay posición, buscar entrada
            if position is None:
                signal_type, score = self.generate_signal(
                    data.iloc[:i+1], current, prev, adjusted_params
                )
                
                if signal_type and score >= adjusted_params['min_score']:
                    # Abrir posición
                    position = {
                        'symbol': symbol,
                        'type': signal_type,
                        'entry_date': current.name,
                        'entry_price': float(current['Close']),
                        'score': score
                    }
                    
                    # Calcular stops
                    if signal_type == 'LONG':
                        position['stop_loss'] = position['entry_price'] * (1 - adjusted_params['stop_loss_pct'])
                        position['take_profit'] = position['entry_price'] * (1 + adjusted_params['take_profit_pct'])
                    else:
                        position['stop_loss'] = position['entry_price'] * (1 + adjusted_params['stop_loss_pct'])
                        position['take_profit'] = position['entry_price'] * (1 - adjusted_params['take_profit_pct'])
            
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
                    position['return_pct'] *= adjusted_params['leverage_base']
                    position['return_pct'] -= 0.2  # Comisiones
                    
                    position['duration_days'] = (position['exit_date'] - position['entry_date']).days
                    position['pnl'] = self.initial_capital * adjusted_params['position_size_pct'] * (position['return_pct'] / 100)
                    
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
            
            position['return_pct'] *= adjusted_params['leverage_base']
            position['return_pct'] -= 0.2
            position['duration_days'] = (position['exit_date'] - position['entry_date']).days
            position['pnl'] = self.initial_capital * adjusted_params['position_size_pct'] * (position['return_pct'] / 100)
            
            trades.append(position)
        
        return trades
    
    def adjust_for_market(self, params, market_type):
        """Ajusta parámetros según tipo de mercado"""
        
        adjusted = params.copy()
        
        if market_type == 'BULL':
            # Mercado alcista: más agresivo en longs
            adjusted['min_score'] = max(3.5, params['min_score'] - 0.3)
            adjusted['take_profit_pct'] = params['take_profit_pct'] * 1.1
            
        elif market_type in ['BEAR', 'SIDEWAYS']:
            # Mercado bajista o lateral: más conservador
            adjusted['min_score'] = min(5.0, params['min_score'] + 0.2)
            adjusted['stop_loss_pct'] = params['stop_loss_pct'] * 0.9
            
        elif market_type == 'RECOVERY':
            # Recuperación: balanceado
            # Mantener parámetros originales
            pass
            
        return adjusted
    
    def generate_signal(self, df, current, prev, params):
        """Genera señal de trading"""
        
        try:
            # Usar sistema de scoring
            signal_type, score = self.scoring_system.evaluar_entrada(df, current, prev)
            
            # Validaciones adicionales con indicadores
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            bb_position = current.get('BB_Position', 0.5)
            volume_ratio = current.get('Volume_Ratio', 1.0)
            
            # Condiciones de confirmación
            if rsi <= params['rsi_oversold'] and macd > macd_signal:
                if signal_type != 'SHORT':
                    signal_type = 'LONG'
                    score = max(score, params['min_score'] + 0.5)
                    
            elif rsi >= params['rsi_overbought'] and macd < macd_signal:
                if signal_type != 'LONG':
                    signal_type = 'SHORT'
                    score = max(score, params['min_score'] + 0.5)
            
            # Bonus por condiciones adicionales
            if signal_type == 'LONG' and bb_position < 0.2:
                score += 0.3
            elif signal_type == 'SHORT' and bb_position > 0.8:
                score += 0.3
            
            if volume_ratio > 1.5:
                score += 0.2
            
            return signal_type, score
            
        except:
            # Fallback simple
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            
            if rsi <= params['rsi_oversold'] and macd > macd_signal:
                return 'LONG', params['min_score'] + 0.5
            elif rsi >= params['rsi_overbought'] and macd < macd_signal:
                return 'SHORT', params['min_score'] + 0.5
            
            return None, 0
    
    def calculate_metrics(self, trades):
        """Calcula métricas de performance"""
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_return': 0,
                'avg_return': 0,
                'total_pnl': 0,
                'max_drawdown': 0
            }
        
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
        avg_return = total_return / total_trades
        
        # PnL
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        # Max drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for trade in sorted(trades, key=lambda x: x['entry_date']):
            cumulative += trade['return_pct']
            peak = max(peak, cumulative)
            dd = peak - cumulative
            max_dd = max(max_dd, dd)
        
        # Duración promedio
        avg_duration = np.mean([t.get('duration_days', 0) for t in trades])
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'avg_return': avg_return,
            'total_pnl': total_pnl,
            'max_drawdown': max_dd,
            'avg_duration': avg_duration
        }
    
    def print_period_summary(self, period_name, trades):
        """Imprime resumen del período"""
        
        print(f"\n📊 RESUMEN - {period_name}")
        print("-"*60)
        
        if not trades:
            print("  ❌ No se generaron trades en este período")
            return
        
        metrics = self.calculate_metrics(trades)
        
        print(f"  📈 Total Trades: {metrics['total_trades']}")
        print(f"  ✅ Ganadores: {metrics['winning_trades']} | ❌ Perdedores: {metrics['losing_trades']}")
        print(f"  📊 Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  💰 Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  📈 Return Total: {metrics['total_return']:.1f}%")
        print(f"  💵 P&L Total: ${metrics['total_pnl']:,.2f}")
        print(f"  ⏱️ Duración Promedio: {metrics['avg_duration']:.1f} días")
        
        # Análisis por símbolo
        symbol_performance = {}
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {'count': 0, 'return': 0}
            symbol_performance[symbol]['count'] += 1
            symbol_performance[symbol]['return'] += trade['return_pct']
        
        if symbol_performance:
            print("\n  📊 Por símbolo:")
            for symbol, perf in sorted(symbol_performance.items(), 
                                      key=lambda x: x[1]['return'], reverse=True):
                print(f"    • {symbol}: {perf['count']} trades, {perf['return']:.1f}% return")
    
    def print_global_analysis(self):
        """Imprime análisis global"""
        
        print("\n" + "="*80)
        print("📊 ANÁLISIS GLOBAL - BACKTESTING EXTENDIDO")
        print("="*80)
        
        if not self.all_trades:
            print("❌ No se generaron trades en ningún período")
            return
        
        # Métricas globales
        global_metrics = self.calculate_metrics(self.all_trades)
        
        print("\n📈 MÉTRICAS GLOBALES:")
        print(f"  • Total Trades: {global_metrics['total_trades']}")
        print(f"  • Win Rate: {global_metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {global_metrics['profit_factor']:.2f}")
        print(f"  • Return Total: {global_metrics['total_return']:.1f}%")
        print(f"  • Return Promedio por Trade: {global_metrics['avg_return']:.2f}%")
        print(f"  • P&L Total: ${global_metrics['total_pnl']:,.2f}")
        print(f"  • Max Drawdown: {global_metrics['max_drawdown']:.1f}%")
        
        # Calcular período total en días
        first_trade_date = min(t['entry_date'] for t in self.all_trades)
        last_trade_date = max(t['exit_date'] for t in self.all_trades)
        total_days = (last_trade_date - first_trade_date).days
        
        if total_days > 0:
            # Proyecciones
            monthly_return = global_metrics['total_return'] / (total_days / 30)
            annual_return = global_metrics['total_return'] / (total_days / 365)
            
            print(f"\n💰 PROYECCIONES:")
            print(f"  • Período testeado: {total_days} días")
            print(f"  • Return Mensual Promedio: {monthly_return:.1f}%")
            print(f"  • Return Anual Proyectado: {annual_return:.1f}%")
            print(f"  • Trades por Mes: {global_metrics['total_trades'] / (total_days / 30):.1f}")
        
        # Performance por período
        print(f"\n📅 PERFORMANCE POR PERÍODO:")
        for period_name, period_data in self.period_results.items():
            metrics = period_data['metrics']
            if metrics['total_trades'] > 0:
                print(f"  • {period_name}: {metrics['total_trades']} trades, "
                      f"WR={metrics['win_rate']:.1f}%, Return={metrics['total_return']:.1f}%")
        
        # Análisis por símbolo global
        symbol_performance = {}
        for trade in self.all_trades:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {
                    'trades': 0, 
                    'wins': 0,
                    'return': 0,
                    'pnl': 0
                }
            symbol_performance[symbol]['trades'] += 1
            if trade['return_pct'] > 0:
                symbol_performance[symbol]['wins'] += 1
            symbol_performance[symbol]['return'] += trade['return_pct']
            symbol_performance[symbol]['pnl'] += trade.get('pnl', 0)
        
        print(f"\n📊 PERFORMANCE POR SÍMBOLO:")
        for symbol, perf in sorted(symbol_performance.items(), 
                                  key=lambda x: x[1]['return'], reverse=True):
            wr = (perf['wins'] / perf['trades'] * 100) if perf['trades'] > 0 else 0
            print(f"  • {symbol}: {perf['trades']} trades, WR={wr:.1f}%, "
                  f"Return={perf['return']:.1f}%, P&L=${perf['pnl']:,.2f}")
        
        # Top trades
        if self.all_trades:
            best_trade = max(self.all_trades, key=lambda x: x['return_pct'])
            worst_trade = min(self.all_trades, key=lambda x: x['return_pct'])
            
            print(f"\n🏆 MEJORES Y PEORES TRADES:")
            print(f"  • Mejor: {best_trade['symbol']} +{best_trade['return_pct']:.1f}% "
                  f"({best_trade['entry_date'].strftime('%Y-%m-%d')})")
            print(f"  • Peor: {worst_trade['symbol']} {worst_trade['return_pct']:.1f}% "
                  f"({worst_trade['entry_date'].strftime('%Y-%m-%d')})")
        
        # Evaluación final
        self.print_final_evaluation(global_metrics)
    
    def compare_with_calibration(self):
        """Compara con resultados de calibración"""
        
        print("\n" + "="*80)
        print("📊 COMPARACIÓN CON CALIBRACIÓN")
        print("="*80)
        
        # Cargar métricas de calibración
        with open('quick_adaptive_config.json', 'r') as f:
            calibration_data = json.load(f)
            calibration_metrics = calibration_data['metrics']
        
        # Métricas actuales
        current_metrics = self.calculate_metrics(self.all_trades)
        
        print(f"\n{'Métrica':<20} {'Calibración':<15} {'Backtesting':<15} {'Diferencia':<15}")
        print("-"*65)
        
        # Win Rate
        cal_wr = calibration_metrics['win_rate']
        cur_wr = current_metrics['win_rate']
        diff_wr = cur_wr - cal_wr
        status_wr = "✅" if abs(diff_wr) <= 10 else "⚠️" if abs(diff_wr) <= 20 else "❌"
        print(f"{'Win Rate':<20} {cal_wr:<14.1f}% {cur_wr:<14.1f}% {diff_wr:+<14.1f}% {status_wr}")
        
        # Profit Factor
        cal_pf = calibration_metrics['profit_factor']
        cur_pf = current_metrics['profit_factor']
        diff_pf = cur_pf - cal_pf
        status_pf = "✅" if cur_pf >= cal_pf * 0.7 else "⚠️" if cur_pf >= cal_pf * 0.5 else "❌"
        print(f"{'Profit Factor':<20} {cal_pf:<14.2f} {cur_pf:<14.2f} {diff_pf:+<14.2f} {status_pf}")
        
        # Total Return (normalizado por período)
        cal_ret = calibration_metrics['total_return']
        cur_ret = current_metrics['total_return']
        # Normalizar por número de períodos
        cal_ret_norm = cal_ret / 3  # 3 períodos en calibración
        cur_ret_norm = cur_ret / len(self.test_periods)
        diff_ret = cur_ret_norm - cal_ret_norm
        status_ret = "✅" if cur_ret_norm >= cal_ret_norm * 0.7 else "⚠️" if cur_ret_norm >= cal_ret_norm * 0.5 else "❌"
        print(f"{'Return/Período':<20} {cal_ret_norm:<14.1f}% {cur_ret_norm:<14.1f}% {diff_ret:+<14.1f}% {status_ret}")
        
        print("\n📝 EVALUACIÓN DE CONSISTENCIA:")
        if cur_wr >= cal_wr * 0.8 and cur_pf >= cal_pf * 0.7:
            print("✅ SISTEMA CONSISTENTE - Performance dentro de rangos esperados")
            print("   • El sistema mantiene su efectividad en diferentes períodos")
            print("   • Configuración validada para producción")
        elif cur_wr >= cal_wr * 0.6 and cur_pf >= cal_pf * 0.5:
            print("⚠️ SISTEMA MODERADAMENTE CONSISTENTE")
            print("   • Performance ligeramente inferior a calibración")
            print("   • Recomendado monitoreo cercano en paper trading")
        else:
            print("❌ INCONSISTENCIA DETECTADA")
            print("   • Performance significativamente diferente a calibración")
            print("   • Considerar recalibración o ajustes")
    
    def print_final_evaluation(self, metrics):
        """Imprime evaluación final"""
        
        print("\n" + "="*80)
        print("🎯 EVALUACIÓN FINAL DEL SISTEMA")
        print("="*80)
        
        score = 0
        max_score = 100
        
        # Evaluar win rate (0-30 puntos)
        if metrics['win_rate'] >= 60:
            wr_score = 30
            wr_eval = "⭐ EXCELENTE"
        elif metrics['win_rate'] >= 50:
            wr_score = 20
            wr_eval = "✅ BUENO"
        elif metrics['win_rate'] >= 45:
            wr_score = 10
            wr_eval = "⚠️ ACEPTABLE"
        else:
            wr_score = 0
            wr_eval = "❌ INSUFICIENTE"
        score += wr_score
        print(f"  • Win Rate ({metrics['win_rate']:.1f}%): {wr_eval} ({wr_score}/30 pts)")
        
        # Evaluar profit factor (0-30 puntos)
        if metrics['profit_factor'] >= 2.0:
            pf_score = 30
            pf_eval = "⭐ EXCELENTE"
        elif metrics['profit_factor'] >= 1.5:
            pf_score = 20
            pf_eval = "✅ BUENO"
        elif metrics['profit_factor'] >= 1.2:
            pf_score = 10
            pf_eval = "⚠️ ACEPTABLE"
        else:
            pf_score = 0
            pf_eval = "❌ INSUFICIENTE"
        score += pf_score
        print(f"  • Profit Factor ({metrics['profit_factor']:.2f}): {pf_eval} ({pf_score}/30 pts)")
        
        # Evaluar número de trades (0-20 puntos)
        if metrics['total_trades'] >= 30:
            trades_score = 20
            trades_eval = "⭐ EXCELENTE"
        elif metrics['total_trades'] >= 20:
            trades_score = 15
            trades_eval = "✅ BUENO"
        elif metrics['total_trades'] >= 10:
            trades_score = 10
            trades_eval = "⚠️ ACEPTABLE"
        else:
            trades_score = 5
            trades_eval = "❌ INSUFICIENTE"
        score += trades_score
        print(f"  • Número de Trades ({metrics['total_trades']}): {trades_eval} ({trades_score}/20 pts)")
        
        # Evaluar drawdown (0-20 puntos)
        if metrics['max_drawdown'] <= 10:
            dd_score = 20
            dd_eval = "⭐ EXCELENTE"
        elif metrics['max_drawdown'] <= 15:
            dd_score = 15
            dd_eval = "✅ BUENO"
        elif metrics['max_drawdown'] <= 20:
            dd_score = 10
            dd_eval = "⚠️ ACEPTABLE"
        else:
            dd_score = 0
            dd_eval = "❌ ALTO RIESGO"
        score += dd_score
        print(f"  • Max Drawdown ({metrics['max_drawdown']:.1f}%): {dd_eval} ({dd_score}/20 pts)")
        
        # Puntuación final
        print(f"\n📊 PUNTUACIÓN TOTAL: {score}/{max_score} puntos")
        
        if score >= 80:
            print("\n⭐⭐⭐ SISTEMA EXCELENTE")
            print("✅ Altamente recomendado para producción")
            print("💡 Sugerencias:")
            print("   1. Iniciar paper trading inmediatamente")
            print("   2. Comenzar con capital real después de 30 días de paper trading exitoso")
            print("   3. Escalar posiciones gradualmente")
        elif score >= 60:
            print("\n⭐⭐ SISTEMA BUENO")
            print("✅ Apto para paper trading con monitoreo")
            print("💡 Sugerencias:")
            print("   1. Paper trading mínimo 60 días")
            print("   2. Monitorear métricas semanalmente")
            print("   3. Ajustar parámetros si es necesario")
        elif score >= 40:
            print("\n⭐ SISTEMA FUNCIONAL")
            print("⚠️ Requiere optimización antes de producción")
            print("💡 Sugerencias:")
            print("   1. Revisar y ajustar parámetros")
            print("   2. Extender período de backtesting")
            print("   3. Mejorar filtros de entrada")
        else:
            print("\n❌ SISTEMA NO APTO")
            print("❌ No recomendado para trading real")
            print("💡 Requiere rediseño significativo")

def main():
    """Función principal"""
    
    print("🚀 INICIANDO BACKTESTING EXTENDIDO")
    print("="*80)
    
    backtester = ExtendedBacktesting(initial_capital=10000)
    
    # Ejecutar backtesting
    all_trades, period_results = backtester.run_extended_backtesting()
    
    print("\n" + "="*80)
    print("✅ BACKTESTING COMPLETADO")
    print("="*80)
    
    print("\n📋 RESUMEN EJECUTIVO:")
    if all_trades:
        total_return = sum(t['return_pct'] for t in all_trades)
        total_pnl = sum(t.get('pnl', 0) for t in all_trades)
        print(f"  • {len(all_trades)} trades ejecutados")
        print(f"  • Return total: {total_return:.1f}%")
        print(f"  • P&L total: ${total_pnl:,.2f}")
        print(f"  • Capital final estimado: ${10000 + total_pnl:,.2f}")
    else:
        print("  • No se generaron trades")
    
    return all_trades, period_results

if __name__ == "__main__":
    main()