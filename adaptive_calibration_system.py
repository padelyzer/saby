#!/usr/bin/env python3
"""
Sistema de Calibración Adaptativa Iterativa
Encuentra parámetros óptimos mediante iteraciones hasta alcanzar objetivos
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
from itertools import product
import warnings
warnings.filterwarnings('ignore')

from scoring_empirico_v2 import ScoringEmpiricoV2

class AdaptiveCalibrationSystem:
    """
    Sistema que itera la calibración hasta encontrar parámetros aceptables
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.scoring_system = ScoringEmpiricoV2()
        
        # Períodos de calibración
        self.calibration_periods = [
            {
                'name': 'Q1_2024_BULL',
                'start': '2024-01-01',
                'end': '2024-03-31',
                'weight': 0.33,
                'type': 'BULL'
            },
            {
                'name': 'Q2_2024_CORRECTION',
                'start': '2024-04-01',
                'end': '2024-06-30',
                'weight': 0.33,
                'type': 'BEAR'
            },
            {
                'name': 'Q3_2024_RECOVERY',
                'start': '2024-07-01',
                'end': '2024-09-30',
                'weight': 0.34,
                'type': 'RECOVERY'
            }
        ]
        
        # Iteración 1: Rangos iniciales amplios
        self.iteration_configs = [
            {
                'iteration': 1,
                'description': 'Búsqueda amplia inicial',
                'param_ranges': {
                    'min_score': [3.5, 4.0, 4.5, 5.0, 5.5],
                    'stop_loss_pct': [0.02, 0.03, 0.04, 0.05, 0.06],
                    'take_profit_pct': [0.08, 0.10, 0.12, 0.15, 0.20],
                    'position_size_pct': [0.01, 0.02, 0.03],
                    'leverage_base': [1, 2, 3],
                    'rsi_oversold': [25, 30, 35],
                    'rsi_overbought': [65, 70, 75]
                },
                'target_metrics': {
                    'min_win_rate': 45,
                    'min_profit_factor': 1.2,
                    'min_trades': 5,
                    'min_return': 5
                }
            },
            {
                'iteration': 2,
                'description': 'Refinamiento basado en mejores resultados',
                'param_ranges': {},  # Se actualizará dinámicamente
                'target_metrics': {
                    'min_win_rate': 50,
                    'min_profit_factor': 1.5,
                    'min_trades': 8,
                    'min_return': 10
                }
            },
            {
                'iteration': 3,
                'description': 'Optimización final',
                'param_ranges': {},  # Se actualizará dinámicamente
                'target_metrics': {
                    'min_win_rate': 55,
                    'min_profit_factor': 1.8,
                    'min_trades': 10,
                    'min_return': 15
                }
            }
        ]
        
        self.market_data = None
        self.best_configs_history = []
        self.iteration_results = []
        
    def run_adaptive_calibration(self):
        """Ejecuta calibración adaptativa iterativa"""
        
        print("🚀 SISTEMA DE CALIBRACIÓN ADAPTATIVA ITERATIVA")
        print("="*80)
        print(f"💰 Capital: ${self.initial_capital:,}")
        print(f"📅 Períodos: 3 x 90 días")
        print(f"🔄 Iteraciones planificadas: {len(self.iteration_configs)}")
        print("="*80)
        
        # Cargar datos una sola vez
        print("\n📊 Cargando datos de mercado...")
        self.market_data = self.load_market_data()
        
        if not self.market_data:
            print("❌ Error cargando datos")
            return None
        
        print("✅ Datos cargados exitosamente")
        
        # Variables para tracking
        best_global_config = None
        best_global_score = -float('inf')
        
        # Ejecutar iteraciones
        for iteration_num, iteration_config in enumerate(self.iteration_configs, 1):
            print(f"\n{'='*80}")
            print(f"🔄 ITERACIÓN {iteration_num}/{len(self.iteration_configs)}")
            print(f"📝 {iteration_config['description']}")
            print("="*80)
            
            # Actualizar rangos basado en iteración anterior si es necesario
            if iteration_num > 1:
                iteration_config['param_ranges'] = self.generate_refined_ranges(
                    self.best_configs_history[-1]
                )
            
            # Mostrar configuración de iteración
            self.print_iteration_config(iteration_config)
            
            # Ejecutar calibración para esta iteración
            best_configs = self.run_iteration(iteration_config)
            
            # Guardar resultados
            self.iteration_results.append({
                'iteration': iteration_num,
                'config': iteration_config,
                'best_configs': best_configs,
                'configs_found': len(best_configs)
            })
            
            # Actualizar mejor configuración global
            if best_configs:
                top_config = best_configs[0]
                if top_config['score'] > best_global_score:
                    best_global_score = top_config['score']
                    best_global_config = top_config
                
                self.best_configs_history.append(best_configs[:3])
                
                # Verificar si cumplimos objetivos
                if self.meets_all_objectives(top_config, iteration_config['target_metrics']):
                    print(f"\n✅ OBJETIVOS ALCANZADOS EN ITERACIÓN {iteration_num}")
                    break
            else:
                print(f"⚠️ No se encontraron configuraciones válidas en iteración {iteration_num}")
        
        # Mostrar resumen final
        self.print_final_summary(best_global_config)
        
        # Guardar mejor configuración
        if best_global_config:
            self.save_best_configuration(best_global_config)
        
        return best_global_config
    
    def load_market_data(self):
        """Carga datos de mercado una sola vez"""
        
        market_data = {}
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
        
        for symbol in symbols:
            print(f"  • Cargando {symbol}...")
            symbol_data = {}
            
            for period in self.calibration_periods:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(
                        start=period['start'],
                        end=period['end'],
                        interval='1d'
                    )
                    
                    if len(data) > 0:
                        data = self.prepare_indicators(data)
                        symbol_data[period['name']] = data
                        
                except Exception as e:
                    print(f"    ⚠️ Error: {e}")
            
            if symbol_data:
                market_data[symbol] = symbol_data
        
        return market_data
    
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
        df['ATR_Ratio'] = df['ATR'] / df['Close']
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA'].replace(0, 1)
        df['Volume_Ratio'] = df['Volume_Ratio'].fillna(1.0).clip(lower=0.1)
        
        # Price Action
        df['Higher_High'] = df['High'] > df['High'].shift(1)
        df['Higher_Low'] = df['Low'] > df['Low'].shift(1)
        df['Lower_High'] = df['High'] < df['High'].shift(1)
        df['Lower_Low'] = df['Low'] < df['Low'].shift(1)
        
        return df
    
    def run_iteration(self, iteration_config):
        """Ejecuta una iteración de calibración"""
        
        param_ranges = iteration_config['param_ranges']
        target_metrics = iteration_config['target_metrics']
        
        # Generar combinaciones
        param_combinations = self.generate_param_combinations(param_ranges)
        total_combinations = len(param_combinations)
        
        print(f"📊 Combinaciones a probar: {total_combinations}")
        
        best_configs = []
        tested = 0
        
        for params in param_combinations:
            tested += 1
            
            # Mostrar progreso
            if tested % max(1, total_combinations // 10) == 0:
                progress = (tested / total_combinations) * 100
                print(f"  • Progreso: {progress:.0f}% ({tested}/{total_combinations})")
            
            # Probar configuración
            results = self.test_configuration(params)
            
            # Evaluar si cumple objetivos
            if self.meets_objectives(results, target_metrics):
                score = self.calculate_score(results)
                best_configs.append({
                    'params': params,
                    'metrics': results['metrics'],
                    'score': score,
                    'trades': results.get('trades', [])
                })
        
        # Ordenar por score
        best_configs.sort(key=lambda x: x['score'], reverse=True)
        
        # Mostrar resultados de iteración
        self.print_iteration_results(iteration_config['iteration'], best_configs[:5])
        
        return best_configs
    
    def generate_param_combinations(self, param_ranges):
        """Genera combinaciones de parámetros"""
        
        param_names = list(param_ranges.keys())
        param_values = [param_ranges[name] for name in param_names]
        
        combinations = []
        for values in product(*param_values):
            param_dict = dict(zip(param_names, values))
            combinations.append(param_dict)
        
        return combinations
    
    def generate_refined_ranges(self, previous_best_configs):
        """Genera rangos refinados basados en mejores configuraciones anteriores"""
        
        if not previous_best_configs:
            # Si no hay configuraciones previas, usar rangos por defecto
            return self.iteration_configs[0]['param_ranges']
        
        refined_ranges = {}
        
        # Analizar mejores configuraciones
        for param_name in previous_best_configs[0]['params'].keys():
            values = [config['params'][param_name] for config in previous_best_configs[:3]]
            
            # Calcular rango refinado alrededor de los mejores valores
            if isinstance(values[0], float):
                center = np.mean(values)
                spread = max(0.01, np.std(values))
                
                if 'pct' in param_name:
                    # Para porcentajes
                    refined_ranges[param_name] = [
                        round(max(0.01, center - spread), 2),
                        round(center, 2),
                        round(min(0.5, center + spread), 2)
                    ]
                elif param_name == 'min_score':
                    # Para score mínimo
                    refined_ranges[param_name] = [
                        round(max(3.0, center - 0.5), 1),
                        round(center, 1),
                        round(min(6.0, center + 0.5), 1)
                    ]
                else:
                    # Para otros float
                    refined_ranges[param_name] = [
                        round(center - spread, 1),
                        round(center, 1),
                        round(center + spread, 1)
                    ]
            else:
                # Para enteros
                center = int(np.median(values))
                refined_ranges[param_name] = [
                    max(1, center - 5),
                    center,
                    min(100, center + 5)
                ]
        
        # Eliminar duplicados
        for param_name in refined_ranges:
            refined_ranges[param_name] = sorted(list(set(refined_ranges[param_name])))
        
        return refined_ranges
    
    def test_configuration(self, params):
        """Prueba una configuración específica"""
        
        all_trades = []
        period_performance = {}
        
        for symbol, symbol_data in self.market_data.items():
            for period_name, data in symbol_data.items():
                trades = self.backtest_with_params(symbol, data, params, period_name)
                all_trades.extend(trades)
                
                if period_name not in period_performance:
                    period_performance[period_name] = []
                period_performance[period_name].extend(trades)
        
        # Calcular métricas
        if all_trades:
            metrics = self.calculate_metrics(all_trades)
            
            # Añadir métricas por tipo de mercado
            for period in self.calibration_periods:
                period_trades = period_performance.get(period['name'], [])
                if period_trades:
                    period_metrics = self.calculate_metrics(period_trades)
                    metrics[f"{period['type']}_win_rate"] = period_metrics['win_rate']
                    metrics[f"{period['type']}_return"] = period_metrics['total_return']
        else:
            metrics = {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_return': 0,
                'avg_trade_return': 0,
                'max_drawdown': 0
            }
        
        return {
            'params': params,
            'trades': all_trades,
            'metrics': metrics,
            'period_performance': period_performance
        }
    
    def backtest_with_params(self, symbol, data, params, period_name):
        """Ejecuta backtest con parámetros específicos"""
        
        trades = []
        position = None
        
        # Obtener tipo de mercado del período
        period_type = next((p['type'] for p in self.calibration_periods 
                           if p['name'] == period_name), 'NEUTRAL')
        
        # Ajustar parámetros según tipo de mercado
        adjusted_params = self.adjust_params_for_market(params, period_type)
        
        # Iterar por los datos
        for i in range(20, len(data)):
            current = data.iloc[i]
            prev = data.iloc[i-1]
            
            # Si no hay posición, buscar entrada
            if position is None:
                signal_type, score = self.generate_adaptive_signal(
                    data.iloc[:i+1], current, prev, adjusted_params, period_type
                )
                
                if signal_type and score >= adjusted_params['min_score']:
                    # Abrir posición
                    position = {
                        'symbol': symbol,
                        'type': signal_type,
                        'entry_date': current.name,
                        'entry_price': float(current['Close']),
                        'score': score,
                        'period': period_name,
                        'market_type': period_type
                    }
                    
                    # Calcular stops adaptativos
                    if signal_type == 'LONG':
                        position['stop_loss'] = position['entry_price'] * (1 - adjusted_params['stop_loss_pct'])
                        position['take_profit'] = position['entry_price'] * (1 + adjusted_params['take_profit_pct'])
                    else:
                        position['stop_loss'] = position['entry_price'] * (1 + adjusted_params['stop_loss_pct'])
                        position['take_profit'] = position['entry_price'] * (1 - adjusted_params['take_profit_pct'])
            
            # Si hay posición, verificar salida
            elif position:
                exit_signal, exit_price, exit_reason = self.check_exit_conditions(
                    position, current, adjusted_params
                )
                
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
            
            trades.append(position)
        
        return trades
    
    def adjust_params_for_market(self, params, market_type):
        """Ajusta parámetros según tipo de mercado"""
        
        adjusted = params.copy()
        
        if market_type == 'BULL':
            # Mercado alcista: más agresivo en longs
            adjusted['min_score'] = max(3.0, params['min_score'] - 0.5)
            adjusted['take_profit_pct'] = params['take_profit_pct'] * 1.2
            adjusted['rsi_oversold'] = min(35, params['rsi_oversold'] + 5)
            
        elif market_type == 'BEAR':
            # Mercado bajista: más conservador
            adjusted['min_score'] = min(6.0, params['min_score'] + 0.5)
            adjusted['stop_loss_pct'] = params['stop_loss_pct'] * 0.8
            adjusted['leverage_base'] = max(1, params['leverage_base'] - 1)
            
        elif market_type == 'RECOVERY':
            # Recuperación: balanceado pero optimista
            adjusted['take_profit_pct'] = params['take_profit_pct'] * 1.1
            adjusted['rsi_overbought'] = min(75, params['rsi_overbought'] + 5)
        
        return adjusted
    
    def generate_adaptive_signal(self, df, current, prev, params, market_type):
        """Genera señal adaptativa según condiciones de mercado"""
        
        try:
            # Indicadores
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            bb_position = current.get('BB_Position', 0.5)
            volume_ratio = current.get('Volume_Ratio', 1.0)
            atr_ratio = current.get('ATR_Ratio', 0.02)
            
            # Score base
            score = 0
            signal_type = None
            
            # Condiciones LONG
            long_conditions = 0
            if rsi <= params['rsi_oversold']:
                long_conditions += 2
            if macd > macd_signal:
                long_conditions += 1
            if bb_position <= 0.2:  # Cerca de banda inferior
                long_conditions += 1
            if volume_ratio > 1.2:  # Alto volumen
                long_conditions += 1
            if current['Close'] > current.get('EMA_20', current['Close']):
                long_conditions += 1
            
            # Condiciones SHORT
            short_conditions = 0
            if rsi >= params['rsi_overbought']:
                short_conditions += 2
            if macd < macd_signal:
                short_conditions += 1
            if bb_position >= 0.8:  # Cerca de banda superior
                short_conditions += 1
            if volume_ratio > 1.2:
                short_conditions += 1
            if current['Close'] < current.get('EMA_20', current['Close']):
                short_conditions += 1
            
            # Determinar señal y score
            if long_conditions >= 3:
                signal_type = 'LONG'
                score = params['min_score'] + (long_conditions - 3) * 0.5
                
                # Bonus por tipo de mercado
                if market_type == 'BULL':
                    score += 0.5
                elif market_type == 'RECOVERY':
                    score += 0.3
                
            elif short_conditions >= 3:
                signal_type = 'SHORT'
                score = params['min_score'] + (short_conditions - 3) * 0.5
                
                # Bonus por tipo de mercado
                if market_type == 'BEAR':
                    score += 0.5
            
            # Ajuste por volatilidad
            if atr_ratio > 0.03:  # Alta volatilidad
                score -= 0.3
            elif atr_ratio < 0.015:  # Baja volatilidad
                score += 0.2
            
            return signal_type, score
            
        except Exception as e:
            return None, 0
    
    def check_exit_conditions(self, position, current, params):
        """Verifica condiciones de salida adaptativas"""
        
        exit_signal = False
        exit_price = float(current['Close'])
        exit_reason = None
        
        # Verificar stops básicos
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
        
        # Salidas adaptativas adicionales
        if not exit_signal and position.get('duration_days', 0) > 10:
            # Si llevamos más de 10 días, ser más agresivo con profits
            current_return = ((exit_price / position['entry_price']) - 1) * 100
            if position['type'] == 'SHORT':
                current_return = ((position['entry_price'] / exit_price) - 1) * 100
            
            if current_return > params['take_profit_pct'] * 100 * 0.7:
                exit_signal = True
                exit_reason = 'PARTIAL_PROFIT'
        
        return exit_signal, exit_price, exit_reason
    
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
            'avg_trade_return': avg_return,
            'max_drawdown': max_dd,
            'avg_duration': avg_duration
        }
    
    def calculate_score(self, results):
        """Calcula score compuesto para una configuración"""
        
        metrics = results['metrics']
        
        score = 0
        
        # Win rate (0-40 puntos)
        score += min(40, metrics.get('win_rate', 0) * 0.6)
        
        # Profit factor (0-30 puntos)
        score += min(30, metrics.get('profit_factor', 0) * 10)
        
        # Total return (0-20 puntos)
        score += min(20, metrics.get('total_return', 0) * 0.5)
        
        # Número de trades (0-10 puntos)
        score += min(10, metrics.get('total_trades', 0) * 0.5)
        
        # Penalización por drawdown
        max_dd = metrics.get('max_drawdown', 0)
        if max_dd > 20:
            score -= (max_dd - 20) * 0.5
        
        # Bonus por consistencia en diferentes mercados
        if 'BULL_win_rate' in metrics and 'BEAR_win_rate' in metrics:
            consistency = 100 - abs(metrics['BULL_win_rate'] - metrics['BEAR_win_rate'])
            score += consistency * 0.1
        
        return max(0, score)
    
    def meets_objectives(self, results, target_metrics):
        """Verifica si cumple objetivos"""
        
        metrics = results['metrics']
        
        return (
            metrics.get('win_rate', 0) >= target_metrics['min_win_rate'] and
            metrics.get('profit_factor', 0) >= target_metrics['min_profit_factor'] and
            metrics.get('total_trades', 0) >= target_metrics['min_trades'] and
            metrics.get('total_return', 0) >= target_metrics['min_return']
        )
    
    def meets_all_objectives(self, config, target_metrics):
        """Verifica si cumple todos los objetivos incluyendo consistencia"""
        
        metrics = config['metrics']
        
        # Objetivos básicos
        basic_met = (
            metrics.get('win_rate', 0) >= target_metrics['min_win_rate'] and
            metrics.get('profit_factor', 0) >= target_metrics['min_profit_factor'] and
            metrics.get('total_trades', 0) >= target_metrics['min_trades'] and
            metrics.get('total_return', 0) >= target_metrics['min_return']
        )
        
        # Consistencia en diferentes mercados
        consistency_met = True
        if 'BULL_win_rate' in metrics and 'BEAR_win_rate' in metrics:
            # Todos los tipos de mercado deben tener win rate > 40%
            consistency_met = (
                metrics.get('BULL_win_rate', 0) >= 40 and
                metrics.get('BEAR_win_rate', 0) >= 40 and
                metrics.get('RECOVERY_win_rate', 0) >= 40
            )
        
        return basic_met and consistency_met
    
    def print_iteration_config(self, config):
        """Imprime configuración de iteración"""
        
        print("\n📊 Configuración de iteración:")
        print(f"  • Objetivos:")
        for metric, value in config['target_metrics'].items():
            print(f"    - {metric}: {value}")
        
        if config['param_ranges']:
            print(f"  • Rangos de parámetros:")
            for param, values in config['param_ranges'].items():
                if len(values) <= 5:
                    print(f"    - {param}: {values}")
                else:
                    print(f"    - {param}: {values[0]} ... {values[-1]} ({len(values)} valores)")
    
    def print_iteration_results(self, iteration_num, best_configs):
        """Imprime resultados de una iteración"""
        
        print(f"\n📊 Resultados Iteración {iteration_num}:")
        
        if not best_configs:
            print("  ❌ No se encontraron configuraciones válidas")
            return
        
        print(f"  ✅ {len(best_configs)} configuraciones válidas encontradas")
        
        # Mostrar top 3
        for i, config in enumerate(best_configs[:3], 1):
            metrics = config['metrics']
            print(f"\n  #{i} Score: {config['score']:.1f}")
            print(f"     • Win Rate: {metrics['win_rate']:.1f}%")
            print(f"     • Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"     • Total Return: {metrics['total_return']:.1f}%")
            print(f"     • Trades: {metrics['total_trades']}")
            
            # Parámetros clave
            params = config['params']
            print(f"     • Params: Score≥{params['min_score']}, "
                  f"SL={params['stop_loss_pct']*100:.0f}%, "
                  f"TP={params['take_profit_pct']*100:.0f}%")
    
    def print_final_summary(self, best_config):
        """Imprime resumen final"""
        
        print("\n" + "="*80)
        print("📊 RESUMEN FINAL DE CALIBRACIÓN ADAPTATIVA")
        print("="*80)
        
        if not best_config:
            print("❌ No se encontró configuración óptima")
            print("\nRecomendaciones:")
            print("• Ampliar rangos de parámetros")
            print("• Reducir objetivos mínimos")
            print("• Revisar lógica de generación de señales")
            return
        
        print("\n✅ CONFIGURACIÓN ÓPTIMA ENCONTRADA")
        
        metrics = best_config['metrics']
        params = best_config['params']
        
        print("\n📈 MÉTRICAS ALCANZADAS:")
        print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  • Total Return: {metrics['total_return']:.1f}%")
        print(f"  • Total Trades: {metrics['total_trades']}")
        print(f"  • Avg Trade Return: {metrics['avg_trade_return']:.2f}%")
        print(f"  • Max Drawdown: {metrics['max_drawdown']:.1f}%")
        
        # Performance por tipo de mercado
        print("\n📊 PERFORMANCE POR TIPO DE MERCADO:")
        for market_type in ['BULL', 'BEAR', 'RECOVERY']:
            wr_key = f"{market_type}_win_rate"
            ret_key = f"{market_type}_return"
            if wr_key in metrics:
                print(f"  • {market_type}: WR={metrics[wr_key]:.1f}%, Return={metrics[ret_key]:.1f}%")
        
        print("\n⚙️ PARÁMETROS ÓPTIMOS:")
        print(f"  • Score Mínimo: {params['min_score']}")
        print(f"  • Stop Loss: {params['stop_loss_pct']*100:.1f}%")
        print(f"  • Take Profit: {params['take_profit_pct']*100:.1f}%")
        print(f"  • Position Size: {params['position_size_pct']*100:.1f}%")
        print(f"  • Leverage: {params['leverage_base']}x")
        print(f"  • RSI Oversold: {params['rsi_oversold']}")
        print(f"  • RSI Overbought: {params['rsi_overbought']}")
        
        # Proyecciones
        annual_return = metrics['total_return'] * (365 / 270)
        monthly_return = metrics['total_return'] / 9
        
        print("\n💰 PROYECCIONES:")
        print(f"  • Return Mensual Esperado: {monthly_return:.1f}%")
        print(f"  • Return Anual Esperado: {annual_return:.1f}%")
        print(f"  • Trades por Mes: {metrics['total_trades'] / 9:.1f}")
        
        print("\n🎯 EVALUACIÓN FINAL:")
        if metrics['win_rate'] >= 55 and metrics['profit_factor'] >= 2.0:
            print("  ⭐ EXCELENTE - Sistema altamente confiable")
            print("  ✅ Listo para paper trading inmediato")
        elif metrics['win_rate'] >= 50 and metrics['profit_factor'] >= 1.5:
            print("  ✅ BUENO - Sistema confiable")
            print("  ✅ Recomendado para paper trading")
        elif metrics['win_rate'] >= 45 and metrics['profit_factor'] >= 1.2:
            print("  ⚠️ ACEPTABLE - Sistema funcional")
            print("  ⚠️ Paper trading con monitoreo cercano")
        else:
            print("  ❌ INSUFICIENTE - Requiere más optimización")
    
    def save_best_configuration(self, best_config):
        """Guarda la mejor configuración"""
        
        config_to_save = {
            'calibration_date': datetime.now().isoformat(),
            'parameters': best_config['params'],
            'metrics': best_config['metrics'],
            'score': best_config['score'],
            'periods_used': [p['name'] for p in self.calibration_periods],
            'system_type': 'ADAPTIVE',
            'iterations_performed': len(self.iteration_results)
        }
        
        with open('adaptive_optimal_config.json', 'w') as f:
            json.dump(config_to_save, f, indent=2, default=str)
        
        print("\n💾 Configuración guardada en 'adaptive_optimal_config.json'")

def main():
    """Función principal"""
    
    print("🚀 INICIANDO CALIBRACIÓN ADAPTATIVA ITERATIVA")
    print("="*80)
    
    calibrator = AdaptiveCalibrationSystem(initial_capital=10000)
    
    # Ejecutar calibración adaptativa
    best_config = calibrator.run_adaptive_calibration()
    
    if best_config:
        print("\n" + "="*80)
        print("✅ CALIBRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*80)
        
        print("\n🎯 SISTEMA ADAPTATIVO LISTO")
        print("Configuración óptima encontrada y guardada")
        print("\nPróximos pasos:")
        print("1. Validar con backtesting extendido")
        print("2. Iniciar paper trading")
        print("3. Monitorear y ajustar según resultados")
    else:
        print("\n❌ Calibración no encontró configuración óptima")
        print("Considerar revisar estrategia base")
    
    return best_config

if __name__ == "__main__":
    main()