#!/usr/bin/env python3
"""
Backtesting Multi-Período - 90 días en diferentes épocas
Valida el desempeño del sistema en distintas condiciones de mercado
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# Importar todos los componentes del sistema
from sistema_adaptativo_completo import SistemaAdaptativoCompleto
from onchain_analysis import OnChainAnalyzer
from macro_correlations import MacroCorrelationAnalyzer
from entry_signals_optimizer import EntrySignalsOptimizer
from bollinger_squeeze_strategy import BollingerSqueezeStrategy
from trailing_stops_dynamic import DynamicTrailingStops
from volume_position_sizing import VolumeBasedPositionSizing
from fear_greed_index import FearGreedIndexAnalyzer

class MultiPeriodBacktester:
    """
    Backtester que prueba el sistema en múltiples períodos de 90 días
    para validar su efectividad en diferentes condiciones de mercado
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        
        # Períodos de prueba (90 días cada uno) - Ajustados para disponibilidad de datos
        self.test_periods = [
            {
                'name': 'BULL_MARKET_2024',
                'description': 'Mercado alcista - Rally Q1 2024',
                'start': '2024-01-01',
                'end': '2024-03-31',
                'expected_market': 'BULLISH'
            },
            {
                'name': 'BEAR_MARKET_2024',
                'description': 'Mercado correctivo - Consolidación Q2 2024',
                'start': '2024-04-01',
                'end': '2024-06-30',
                'expected_market': 'BEARISH'
            },
            {
                'name': 'RECOVERY_2024',
                'description': 'Mercado de recuperación - Q3 2024',
                'start': '2024-07-01',
                'end': '2024-09-30',
                'expected_market': 'RECOVERY'
            }
        ]
        
        # Símbolos a probar
        self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD']
        
        # Inicializar componentes del sistema
        self.sistema = SistemaAdaptativoCompleto()
        self.onchain = OnChainAnalyzer()
        self.macro = MacroCorrelationAnalyzer()
        self.optimizer = EntrySignalsOptimizer()
        self.bollinger = BollingerSqueezeStrategy()
        self.trailing = DynamicTrailingStops()
        self.sizing = VolumeBasedPositionSizing(self.initial_capital)
        self.fear_greed = FearGreedIndexAnalyzer()
        
        # Resultados de backtesting
        self.results = {}
        
    def run_all_backtests(self):
        """Ejecuta backtesting en todos los períodos"""
        
        print("🚀 BACKTESTING MULTI-PERÍODO - SISTEMA COMPLETO")
        print("="*80)
        print(f"💰 Capital inicial: ${self.initial_capital:,}")
        print(f"📊 Símbolos: {', '.join(self.symbols)}")
        print(f"📅 Períodos de prueba: {len(self.test_periods)} x 90 días")
        print("="*80)
        
        for period in self.test_periods:
            print(f"\n{'='*80}")
            print(f"📅 PERÍODO: {period['name']}")
            print(f"📝 {period['description']}")
            print(f"📆 {period['start']} → {period['end']}")
            print("="*80)
            
            period_results = self.run_period_backtest(period)
            self.results[period['name']] = period_results
            
            # Imprimir resumen del período
            self.print_period_summary(period['name'], period_results)
        
        # Análisis comparativo final
        self.print_comparative_analysis()
        
        return self.results
    
    def run_period_backtest(self, period):
        """Ejecuta backtesting para un período específico"""
        
        period_results = {
            'period_info': period,
            'trades': [],
            'metrics': {},
            'by_symbol': {}
        }
        
        # Backtesting por símbolo
        for symbol in self.symbols:
            print(f"\n🔍 Analizando {symbol}...")
            
            symbol_results = self.backtest_symbol(
                symbol, 
                period['start'], 
                period['end']
            )
            
            period_results['by_symbol'][symbol] = symbol_results
            period_results['trades'].extend(symbol_results['trades'])
        
        # Calcular métricas agregadas del período
        period_results['metrics'] = self.calculate_period_metrics(period_results)
        
        return period_results
    
    def backtest_symbol(self, symbol, start_date, end_date):
        """Ejecuta backtesting para un símbolo en un período"""
        
        try:
            # Obtener datos históricos
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(data) < 20:
                print(f"⚠️ Datos insuficientes para {symbol}")
                return {'trades': [], 'metrics': {}}
            
            # Preparar datos
            data = self.prepare_data(data)
            
            # Variables de tracking
            trades = []
            capital = self.initial_capital
            position = None
            trailing_stop = None
            
            # Iterar por cada período
            for i in range(20, len(data) - 1):
                current = data.iloc[i]
                prev = data.iloc[i-1]
                df_slice = data.iloc[max(0, i-100):i+1]
                
                # Si no hay posición abierta, buscar señal
                if position is None:
                    signal = self.generate_signal(df_slice, current, prev, symbol)
                    
                    if signal and signal['final_score'] >= 6.5:
                        # Determinar tamaño de posición
                        position_size = self.calculate_position_size(
                            symbol, signal, capital
                        )
                        
                        # Abrir posición
                        position = {
                            'symbol': symbol,
                            'type': signal['type'],
                            'entry_time': current.name,
                            'entry_price': float(current['Close']),
                            'quantity': position_size['quantity'],
                            'capital_used': position_size['capital'],
                            'signal_score': signal['final_score'],
                            'leverage': position_size['leverage']
                        }
                        
                        # Configurar trailing stop
                        trailing_stop = self.setup_trailing_stop(position)
                        
                        capital -= position['capital_used']
                
                # Si hay posición abierta, gestionar
                else:
                    # Actualizar trailing stop
                    if trailing_stop:
                        stop_update = self.update_trailing_stop(
                            trailing_stop, float(current['Close'])
                        )
                        
                        # Verificar si se activó el stop
                        if stop_update.get('triggered', False):
                            # Cerrar posición
                            exit_price = float(current['Close'])
                            position['exit_time'] = current.name
                            position['exit_price'] = exit_price
                            position['exit_reason'] = 'TRAILING_STOP'
                            
                            # Calcular P&L
                            pnl = self.calculate_pnl(position)
                            position['pnl'] = pnl['net_pnl']
                            position['pnl_pct'] = pnl['pnl_pct']
                            position['duration'] = (position['exit_time'] - position['entry_time']).total_seconds() / 3600
                            
                            # Actualizar capital
                            capital += position['capital_used'] + position['pnl']
                            
                            # Guardar trade
                            trades.append(position)
                            
                            # Reset
                            position = None
                            trailing_stop = None
                    
                    # Verificar take profit (15%)
                    if position and position['type'] == 'LONG':
                        if current['Close'] >= position['entry_price'] * 1.15:
                            # Take profit
                            position['exit_time'] = current.name
                            position['exit_price'] = float(current['Close'])
                            position['exit_reason'] = 'TAKE_PROFIT'
                            
                            pnl = self.calculate_pnl(position)
                            position['pnl'] = pnl['net_pnl']
                            position['pnl_pct'] = pnl['pnl_pct']
                            position['duration'] = (position['exit_time'] - position['entry_time']).total_seconds() / 3600
                            
                            capital += position['capital_used'] + position['pnl']
                            trades.append(position)
                            position = None
                            trailing_stop = None
            
            # Cerrar posición final si queda abierta
            if position:
                position['exit_time'] = data.iloc[-1].name
                position['exit_price'] = float(data.iloc[-1]['Close'])
                position['exit_reason'] = 'END_OF_PERIOD'
                
                pnl = self.calculate_pnl(position)
                position['pnl'] = pnl['net_pnl']
                position['pnl_pct'] = pnl['pnl_pct']
                position['duration'] = (position['exit_time'] - position['entry_time']).total_seconds() / 3600
                
                trades.append(position)
            
            # Calcular métricas
            metrics = self.calculate_symbol_metrics(trades, self.initial_capital)
            
            return {
                'trades': trades,
                'metrics': metrics,
                'final_capital': capital
            }
            
        except Exception as e:
            print(f"❌ Error en backtesting {symbol}: {e}")
            return {'trades': [], 'metrics': {}}
    
    def prepare_data(self, data):
        """Prepara los datos con indicadores técnicos"""
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = data['Close'].ewm(span=12).mean()
        exp2 = data['Close'].ewm(span=26).mean()
        data['MACD'] = exp1 - exp2
        data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        
        # ATR
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        data['ATR'] = true_range.rolling(14).mean()
        
        # Volume metrics
        data['Volume_MA'] = data['Volume'].rolling(20).mean()
        data['Volume_Ratio'] = data['Volume'] / data['Volume_MA'].replace(0, 1)
        
        # EMAs
        data['EMA_20'] = data['Close'].ewm(span=20).mean()
        data['EMA_50'] = data['Close'].ewm(span=50).mean()
        
        return data
    
    def generate_signal(self, df, current, prev, symbol):
        """Genera señal de trading usando el sistema completo"""
        
        try:
            # Señal base del sistema adaptativo
            signal_type, base_score, details = self.sistema.calculate_adaptive_score(
                df, current, prev, symbol.replace('-USD', ''), None
            )
            
            if signal_type is None:
                return None
            
            # Optimizar entrada
            optimized_type, optimized_score, opt_details = self.optimizer.optimize_entry_signal(
                df, current, prev, signal_type, base_score
            )
            
            if optimized_type == 'REJECTED':
                return None
            
            # Análisis on-chain (simulado)
            onchain_score, onchain_details = self.onchain.get_onchain_score(
                symbol.replace('-USD', '')
            )
            
            # Análisis macro
            macro_analysis = self.macro.get_macro_analysis(symbol)
            macro_score = macro_analysis['macro_score']
            
            # Fear & Greed
            fg_analysis = self.fear_greed.get_fear_greed_analysis(
                symbol.replace('-USD', '')
            )
            fg_adjustments = fg_analysis['trading_adjustments']
            
            # Bollinger Bands
            bb_score, bb_details = self.bollinger.analyze_bollinger_signal(
                df, current, signal_type
            )
            
            # Score final compuesto
            final_score = optimized_score
            final_score *= (1 + (onchain_score - 0.5) * 0.2)  # ±10% por on-chain
            final_score *= (1 + (macro_score - 0.5) * 0.2)    # ±10% por macro
            final_score *= fg_adjustments['entry_aggressiveness']  # Ajuste F&G
            final_score *= (1 + (bb_score - 0.5) * 0.1)       # ±5% por BB
            
            return {
                'type': signal_type,
                'base_score': base_score,
                'optimized_score': optimized_score,
                'final_score': final_score,
                'components': {
                    'onchain': onchain_score,
                    'macro': macro_score,
                    'fear_greed': fg_analysis['composite_index'],
                    'bollinger': bb_score
                },
                'timestamp': current.name
            }
            
        except Exception as e:
            return None
    
    def calculate_position_size(self, symbol, signal, available_capital):
        """Calcula el tamaño de posición óptimo"""
        
        # Usar sistema de volume-based sizing
        sizing_result = self.sizing.calculate_optimal_position_size(
            symbol, signal, available_capital
        )
        
        # Determinar leverage basado en score
        if signal['final_score'] >= 8.0:
            leverage = 5
        elif signal['final_score'] >= 7.0:
            leverage = 3
        else:
            leverage = 2
        
        # Ajustar por Fear & Greed
        fg_analysis = self.fear_greed.get_fear_greed_analysis(symbol.replace('-USD', ''))
        fg_adjustments = fg_analysis['trading_adjustments']
        leverage *= fg_adjustments['position_multiplier']
        
        # Calcular capital a usar
        position_pct = sizing_result['position_pct'] / 100
        position_capital = available_capital * position_pct * leverage
        
        # Limitar al 10% del capital disponible
        max_position = available_capital * 0.10
        position_capital = min(position_capital, max_position)
        
        return {
            'capital': position_capital,
            'quantity': position_capital / signal.get('entry_price', 1),
            'leverage': leverage,
            'position_pct': (position_capital / available_capital) * 100
        }
    
    def setup_trailing_stop(self, position):
        """Configura trailing stop inicial"""
        
        return {
            'symbol': position['symbol'],
            'type': position['type'],
            'entry_price': position['entry_price'],
            'current_stop': position['entry_price'] * 0.95 if position['type'] == 'LONG' else position['entry_price'] * 1.05,
            'best_price': position['entry_price'],
            'trail_pct': 5.0
        }
    
    def update_trailing_stop(self, trailing_stop, current_price):
        """Actualiza trailing stop"""
        
        # Actualizar mejor precio
        if trailing_stop['type'] == 'LONG':
            if current_price > trailing_stop['best_price']:
                trailing_stop['best_price'] = current_price
                # Mover stop up
                new_stop = current_price * (1 - trailing_stop['trail_pct'] / 100)
                if new_stop > trailing_stop['current_stop']:
                    trailing_stop['current_stop'] = new_stop
            
            # Verificar si se activó
            if current_price <= trailing_stop['current_stop']:
                return {'triggered': True, 'stop_price': trailing_stop['current_stop']}
        
        else:  # SHORT
            if current_price < trailing_stop['best_price']:
                trailing_stop['best_price'] = current_price
                # Mover stop down
                new_stop = current_price * (1 + trailing_stop['trail_pct'] / 100)
                if new_stop < trailing_stop['current_stop']:
                    trailing_stop['current_stop'] = new_stop
            
            # Verificar si se activó
            if current_price >= trailing_stop['current_stop']:
                return {'triggered': True, 'stop_price': trailing_stop['current_stop']}
        
        return {'triggered': False}
    
    def calculate_pnl(self, position):
        """Calcula P&L de una posición"""
        
        if position['type'] == 'LONG':
            gross_pnl = (position['exit_price'] - position['entry_price']) * position['quantity']
        else:
            gross_pnl = (position['entry_price'] - position['exit_price']) * position['quantity']
        
        # Comisiones (0.1% entrada + salida)
        commission = position['capital_used'] * 0.002
        net_pnl = gross_pnl - commission
        
        pnl_pct = (net_pnl / position['capital_used']) * 100
        
        return {
            'gross_pnl': gross_pnl,
            'commission': commission,
            'net_pnl': net_pnl,
            'pnl_pct': pnl_pct
        }
    
    def calculate_symbol_metrics(self, trades, initial_capital):
        """Calcula métricas para un símbolo"""
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        # Métricas básicas
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Profit factor
        total_wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        total_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Total return
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (total_pnl / initial_capital) * 100
        
        # Sharpe ratio (simplificado)
        if len(trades) > 1:
            returns = [t['pnl_pct'] for t in trades]
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in trades:
            cumulative_pnl += trade['pnl']
            peak = max(peak, cumulative_pnl)
            drawdown = (peak - cumulative_pnl) / initial_capital * 100 if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # Métricas adicionales
        avg_win = total_wins / winning_trades if winning_trades > 0 else 0
        avg_loss = total_losses / losing_trades if losing_trades > 0 else 0
        avg_duration = np.mean([t.get('duration', 0) for t in trades])
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_duration_hours': avg_duration
        }
    
    def calculate_period_metrics(self, period_results):
        """Calcula métricas agregadas del período"""
        
        all_trades = period_results['trades']
        
        if not all_trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_return': 0,
                'best_symbol': 'N/A',
                'worst_symbol': 'N/A'
            }
        
        # Métricas agregadas
        metrics = self.calculate_symbol_metrics(all_trades, self.initial_capital)
        
        # Mejor y peor símbolo
        symbol_returns = {}
        for symbol, data in period_results['by_symbol'].items():
            if data['metrics']:
                symbol_returns[symbol] = data['metrics'].get('total_return', 0)
        
        if symbol_returns:
            metrics['best_symbol'] = max(symbol_returns, key=symbol_returns.get)
            metrics['worst_symbol'] = min(symbol_returns, key=symbol_returns.get)
            metrics['best_return'] = symbol_returns[metrics['best_symbol']]
            metrics['worst_return'] = symbol_returns[metrics['worst_symbol']]
        
        return metrics
    
    def print_period_summary(self, period_name, results):
        """Imprime resumen de un período"""
        
        metrics = results['metrics']
        
        print(f"\n📊 RESUMEN - {period_name}")
        print("-"*60)
        
        if metrics.get('total_trades', 0) == 0:
            print("❌ Sin trades en este período")
            return
        
        # Métricas principales
        print(f"📈 Total Trades: {metrics['total_trades']}")
        print(f"✅ Win Rate: {metrics['win_rate']:.1f}%")
        print(f"💰 Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"📊 Total Return: {metrics['total_return']:+.2f}%")
        print(f"📉 Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"📐 Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        
        # Mejor y peor símbolo
        if 'best_symbol' in metrics:
            print(f"\n🏆 Mejor símbolo: {metrics['best_symbol']} ({metrics['best_return']:+.2f}%)")
            print(f"💔 Peor símbolo: {metrics['worst_symbol']} ({metrics['worst_return']:+.2f}%)")
        
        # Desglose por símbolo
        print(f"\n📊 Desglose por símbolo:")
        for symbol, data in results['by_symbol'].items():
            if data['metrics'] and data['metrics'].get('total_trades', 0) > 0:
                m = data['metrics']
                print(f"  • {symbol}: {m['total_trades']} trades, "
                      f"WR: {m['win_rate']:.1f}%, "
                      f"Return: {m['total_return']:+.2f}%")
    
    def print_comparative_analysis(self):
        """Imprime análisis comparativo de todos los períodos"""
        
        print("\n" + "="*80)
        print("📊 ANÁLISIS COMPARATIVO - TODOS LOS PERÍODOS")
        print("="*80)
        
        # Tabla comparativa
        print(f"\n{'Período':<20} {'Trades':<10} {'Win Rate':<12} {'Profit Factor':<15} {'Return':<12} {'Max DD':<10}")
        print("-"*85)
        
        for period_name, results in self.results.items():
            m = results['metrics']
            if m.get('total_trades', 0) > 0:
                print(f"{period_name:<20} {m['total_trades']:<10} "
                      f"{m['win_rate']:<11.1f}% {m['profit_factor']:<14.2f} "
                      f"{m['total_return']:+<11.2f}% {m['max_drawdown']:<9.2f}%")
        
        # Estadísticas globales
        all_trades = []
        for results in self.results.values():
            all_trades.extend(results['trades'])
        
        if all_trades:
            global_metrics = self.calculate_symbol_metrics(all_trades, self.initial_capital)
            
            print("\n" + "="*85)
            print("📈 MÉTRICAS GLOBALES (TODOS LOS PERÍODOS)")
            print("-"*85)
            print(f"• Total de Trades: {global_metrics['total_trades']}")
            print(f"• Win Rate Global: {global_metrics['win_rate']:.1f}%")
            print(f"• Profit Factor Global: {global_metrics['profit_factor']:.2f}")
            print(f"• Return Promedio: {global_metrics['total_return'] / len(self.test_periods):.2f}%")
            print(f"• Sharpe Ratio Promedio: {global_metrics['sharpe_ratio']:.2f}")
            
            # Análisis de robustez
            print("\n🎯 ANÁLISIS DE ROBUSTEZ:")
            win_rates = [r['metrics']['win_rate'] for r in self.results.values() 
                        if r['metrics'].get('total_trades', 0) > 0]
            
            if win_rates:
                wr_std = np.std(win_rates)
                wr_mean = np.mean(win_rates)
                
                print(f"• Win Rate promedio: {wr_mean:.1f}% ± {wr_std:.1f}%")
                
                if wr_mean >= 55 and wr_std <= 10:
                    print("✅ Sistema ROBUSTO - Win rate consistente")
                elif wr_mean >= 50:
                    print("⚠️ Sistema MODERADO - Win rate aceptable")
                else:
                    print("❌ Sistema DÉBIL - Win rate insuficiente")
            
            # Análisis por tipo de mercado
            print("\n📊 DESEMPEÑO POR TIPO DE MERCADO:")
            for period_name, results in self.results.items():
                period_info = results['period_info']
                metrics = results['metrics']
                if metrics.get('total_trades', 0) > 0:
                    print(f"• {period_info['expected_market']}: "
                          f"Return {metrics['total_return']:+.2f}%, "
                          f"WR {metrics['win_rate']:.1f}%")
        
        # Recomendaciones finales
        self.print_recommendations()
    
    def print_recommendations(self):
        """Imprime recomendaciones basadas en los resultados"""
        
        print("\n" + "="*80)
        print("💡 RECOMENDACIONES BASADAS EN BACKTESTING")
        print("="*80)
        
        # Analizar resultados por tipo de mercado
        bull_performance = None
        bear_performance = None
        sideways_performance = None
        
        for period_name, results in self.results.items():
            if 'BULL' in period_name:
                bull_performance = results['metrics'].get('total_return', 0)
            elif 'BEAR' in period_name:
                bear_performance = results['metrics'].get('total_return', 0)
            elif 'SIDEWAYS' in period_name:
                sideways_performance = results['metrics'].get('total_return', 0)
        
        print("\n📋 AJUSTES RECOMENDADOS:")
        
        # Recomendaciones por tipo de mercado
        if bull_performance is not None and bull_performance > 20:
            print("✅ BULL MARKET: Sistema funciona bien, mantener configuración")
        elif bull_performance is not None and bull_performance < 10:
            print("⚠️ BULL MARKET: Aumentar agresividad en tendencias alcistas")
        
        if bear_performance is not None and bear_performance > -5:
            print("✅ BEAR MARKET: Buena gestión de riesgo en caídas")
        elif bear_performance is not None and bear_performance < -15:
            print("⚠️ BEAR MARKET: Mejorar filtros para mercados bajistas")
        
        if sideways_performance is not None and abs(sideways_performance) < 5:
            print("✅ SIDEWAYS: Sistema maneja bien la lateralidad")
        elif sideways_performance is not None and sideways_performance < -10:
            print("⚠️ SIDEWAYS: Reducir frecuencia de trading en laterales")
        
        # Recomendaciones generales
        all_win_rates = [r['metrics']['win_rate'] for r in self.results.values() 
                         if r['metrics'].get('total_trades', 0) > 0]
        
        if all_win_rates:
            avg_wr = np.mean(all_win_rates)
            
            print("\n📊 AJUSTES DE SISTEMA:")
            
            if avg_wr < 50:
                print("• ⚠️ Aumentar threshold de entrada de 6.5 a 7.0")
                print("• ⚠️ Implementar más filtros de confirmación")
                print("• ⚠️ Reducir leverage máximo a 3x")
            elif avg_wr >= 50 and avg_wr < 60:
                print("• ✅ Mantener threshold actual de 6.5")
                print("• 📈 Considerar aumentar tamaño de posiciones")
                print("• 📊 Optimizar trailing stops para capturar más ganancias")
            else:
                print("• 🎯 Sistema optimizado, mantener configuración")
                print("• 💰 Considerar aumentar capital de trading")
                print("• 📈 Explorar más símbolos para diversificación")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. Implementar ajustes recomendados")
        print("2. Ejecutar paper trading por 30 días")
        print("3. Validar mejoras con backtesting adicional")
        print("4. Comenzar con capital real limitado ($1000-$5000)")
        print("5. Escalar gradualmente según resultados")

def main():
    """Función principal"""
    
    print("🚀 INICIANDO BACKTESTING MULTI-PERÍODO")
    print("="*80)
    
    # Crear backtester
    backtester = MultiPeriodBacktester(initial_capital=10000)
    
    # Ejecutar todos los backtests
    results = backtester.run_all_backtests()
    
    # Guardar resultados
    with open('backtesting_results_90days.json', 'w') as f:
        # Convertir a formato serializable
        serializable_results = {}
        for period_name, period_data in results.items():
            serializable_results[period_name] = {
                'period_info': period_data['period_info'],
                'metrics': period_data['metrics'],
                'trades_count': len(period_data['trades'])
            }
        json.dump(serializable_results, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print("✅ BACKTESTING COMPLETADO")
    print("📊 Resultados guardados en: backtesting_results_90days.json")
    print("="*80)
    
    return results

if __name__ == "__main__":
    main()