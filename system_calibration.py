#!/usr/bin/env python3
"""
Sistema de Calibración Automática
Optimiza parámetros del sistema usando los 3 períodos de 90 días
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

class SystemCalibrator:
    """
    Calibrador automático que encuentra los mejores parámetros
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
                'weight': 0.33
            },
            {
                'name': 'Q2_2024_CORRECTION',
                'start': '2024-04-01',
                'end': '2024-06-30',
                'weight': 0.33
            },
            {
                'name': 'Q3_2024_RECOVERY',
                'start': '2024-07-01',
                'end': '2024-09-30',
                'weight': 0.34
            }
        ]
        
        # Rangos de parámetros a probar
        self.param_ranges = {
            'min_score': [4.5, 5.0, 5.5, 6.0, 6.5],
            'stop_loss_pct': [0.02, 0.03, 0.04, 0.05],
            'take_profit_pct': [0.10, 0.15, 0.20, 0.25],
            'position_size_pct': [0.02, 0.03, 0.04],
            'leverage_base': [2, 3],
            'rsi_oversold': [25, 30, 35],
            'rsi_overbought': [65, 70, 75]
        }
        
        # Métricas objetivo
        self.target_metrics = {
            'min_win_rate': 50,      # Mínimo 50% win rate
            'min_profit_factor': 1.2, # Mínimo 1.2 profit factor
            'min_trades': 10,         # Mínimo 10 trades en 270 días
            'min_return': 10          # Mínimo 10% return
        }
        
        self.best_params = None
        self.best_score = -float('inf')
        self.results_history = []
        
    def run_calibration(self):
        """Ejecuta calibración completa"""
        
        print("🔧 SISTEMA DE CALIBRACIÓN AUTOMÁTICA")
        print("="*80)
        print(f"💰 Capital: ${self.initial_capital:,}")
        print(f"📅 Períodos: 3 x 90 días (270 días total)")
        print(f"🔍 Combinaciones a probar: {self.count_combinations()}")
        print("="*80)
        
        # Obtener datos históricos primero
        print("\n📊 Cargando datos históricos...")
        market_data = self.load_all_data()
        
        if not market_data:
            print("❌ Error cargando datos")
            return None
        
        print("✅ Datos cargados exitosamente")
        
        # Probar combinaciones de parámetros
        print("\n🔍 Iniciando calibración...")
        print("-"*60)
        
        tested_combinations = 0
        best_combinations = []
        
        # Generar todas las combinaciones
        param_combinations = self.generate_param_combinations()
        total_combinations = len(param_combinations)
        
        for i, params in enumerate(param_combinations):
            tested_combinations += 1
            
            # Mostrar progreso cada 10%
            if tested_combinations % max(1, total_combinations // 10) == 0:
                progress = (tested_combinations / total_combinations) * 100
                print(f"📈 Progreso: {progress:.0f}% ({tested_combinations}/{total_combinations})")
            
            # Probar configuración
            results = self.test_configuration(params, market_data)
            
            # Evaluar resultados
            score = self.evaluate_results(results)
            
            # Guardar si es buena configuración
            if self.meets_targets(results):
                best_combinations.append({
                    'params': params,
                    'results': results,
                    'score': score
                })
            
            # Actualizar mejor configuración
            if score > self.best_score:
                self.best_score = score
                self.best_params = params
                self.best_results = results
        
        # Ordenar mejores configuraciones
        best_combinations.sort(key=lambda x: x['score'], reverse=True)
        
        # Mostrar resultados
        self.print_calibration_results(best_combinations[:10])
        
        # Guardar configuración óptima
        if self.best_params:
            self.save_optimal_configuration()
        
        return self.best_params, self.best_results
    
    def count_combinations(self):
        """Cuenta total de combinaciones"""
        total = 1
        for param_values in self.param_ranges.values():
            total *= len(param_values)
        return total
    
    def generate_param_combinations(self):
        """Genera todas las combinaciones de parámetros"""
        
        # Crear lista de todas las combinaciones
        param_names = list(self.param_ranges.keys())
        param_values = [self.param_ranges[name] for name in param_names]
        
        combinations = []
        for values in product(*param_values):
            param_dict = dict(zip(param_names, values))
            combinations.append(param_dict)
        
        return combinations
    
    def load_all_data(self):
        """Carga todos los datos necesarios"""
        
        market_data = {}
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        
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
                        # Preparar indicadores
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
    
    def test_configuration(self, params, market_data):
        """Prueba una configuración específica"""
        
        all_trades = []
        
        for symbol, symbol_data in market_data.items():
            for period_name, data in symbol_data.items():
                trades = self.backtest_with_params(symbol, data, params)
                all_trades.extend(trades)
        
        # Calcular métricas
        if all_trades:
            metrics = self.calculate_metrics(all_trades)
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
            'metrics': metrics
        }
    
    def backtest_with_params(self, symbol, data, params):
        """Ejecuta backtest con parámetros específicos"""
        
        trades = []
        position = None
        
        # Usar parámetros personalizados
        min_score = params['min_score']
        stop_loss = params['stop_loss_pct']
        take_profit = params['take_profit_pct']
        position_size = params['position_size_pct']
        leverage = params['leverage_base']
        rsi_oversold = params['rsi_oversold']
        rsi_overbought = params['rsi_overbought']
        
        # Iterar por los datos
        for i in range(20, len(data)):
            current = data.iloc[i]
            prev = data.iloc[i-1]
            
            # Si no hay posición, buscar entrada
            if position is None:
                # Generar señal con parámetros ajustados
                signal_type, score = self.generate_signal_with_params(
                    data.iloc[:i+1], current, prev, 
                    rsi_oversold, rsi_overbought
                )
                
                if signal_type and score >= min_score:
                    # Abrir posición
                    position = {
                        'symbol': symbol,
                        'type': signal_type,
                        'entry_date': current.name,
                        'entry_price': float(current['Close']),
                        'score': score,
                        'params': params
                    }
                    
                    # Calcular stops
                    if signal_type == 'LONG':
                        position['stop_loss'] = position['entry_price'] * (1 - stop_loss)
                        position['take_profit'] = position['entry_price'] * (1 + take_profit)
                    else:
                        position['stop_loss'] = position['entry_price'] * (1 + stop_loss)
                        position['take_profit'] = position['entry_price'] * (1 - take_profit)
            
            # Si hay posición, verificar salida
            elif position:
                exit_signal = False
                exit_price = float(current['Close'])
                
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
                    
                    # Calcular P&L
                    if position['type'] == 'LONG':
                        position['return_pct'] = ((exit_price / position['entry_price']) - 1) * 100
                    else:
                        position['return_pct'] = ((position['entry_price'] / exit_price) - 1) * 100
                    
                    position['return_pct'] *= leverage  # Aplicar leverage
                    position['return_pct'] -= 0.2  # Comisiones
                    
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
            
            position['return_pct'] *= leverage
            position['return_pct'] -= 0.2
            
            trades.append(position)
        
        return trades
    
    def generate_signal_with_params(self, df, current, prev, rsi_oversold, rsi_overbought):
        """Genera señal con parámetros personalizados"""
        
        try:
            # Usar sistema de scoring con ajustes
            signal_type, score = self.scoring_system.evaluar_entrada(df, current, prev)
            
            # Ajustar por parámetros personalizados
            rsi = current.get('RSI', 50)
            
            # Override con parámetros personalizados
            if rsi <= rsi_oversold:
                if signal_type != 'SHORT':
                    signal_type = 'LONG'
                    score = max(score, 6.0)
            elif rsi >= rsi_overbought:
                if signal_type != 'LONG':
                    signal_type = 'SHORT'
                    score = max(score, 6.0)
            
            return signal_type, score
            
        except:
            # Fallback simple
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            
            if rsi <= rsi_oversold and macd > macd_signal:
                return 'LONG', 6.0
            elif rsi >= rsi_overbought and macd < macd_signal:
                return 'SHORT', 6.0
            
            return None, 0
    
    def calculate_metrics(self, trades):
        """Calcula métricas de performance"""
        
        if not trades:
            return {}
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['return_pct'] > 0)
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Profit factor
        wins = sum(t['return_pct'] for t in trades if t['return_pct'] > 0)
        losses = abs(sum(t['return_pct'] for t in trades if t['return_pct'] < 0))
        profit_factor = wins / losses if losses > 0 else float('inf') if wins > 0 else 0
        
        # Total return
        total_return = sum(t['return_pct'] for t in trades)
        avg_return = total_return / total_trades if total_trades > 0 else 0
        
        # Max drawdown (simplificado)
        cumulative_return = 0
        peak = 0
        max_drawdown = 0
        
        for trade in sorted(trades, key=lambda x: x['entry_date']):
            cumulative_return += trade['return_pct']
            peak = max(peak, cumulative_return)
            drawdown = peak - cumulative_return
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'avg_trade_return': avg_return,
            'max_drawdown': max_drawdown
        }
    
    def evaluate_results(self, results):
        """Evalúa qué tan buenos son los resultados"""
        
        metrics = results['metrics']
        
        # Sistema de puntuación
        score = 0
        
        # Win rate (0-40 puntos)
        win_rate = metrics.get('win_rate', 0)
        score += min(40, win_rate * 0.8)
        
        # Profit factor (0-30 puntos)
        pf = metrics.get('profit_factor', 0)
        score += min(30, pf * 10)
        
        # Total return (0-20 puntos)
        total_return = metrics.get('total_return', 0)
        score += min(20, total_return)
        
        # Número de trades (0-10 puntos)
        trades = metrics.get('total_trades', 0)
        score += min(10, trades / 3)
        
        # Penalización por max drawdown
        max_dd = metrics.get('max_drawdown', 0)
        if max_dd > 20:
            score -= (max_dd - 20)
        
        return score
    
    def meets_targets(self, results):
        """Verifica si cumple objetivos mínimos"""
        
        metrics = results['metrics']
        
        return (
            metrics.get('win_rate', 0) >= self.target_metrics['min_win_rate'] and
            metrics.get('profit_factor', 0) >= self.target_metrics['min_profit_factor'] and
            metrics.get('total_trades', 0) >= self.target_metrics['min_trades'] and
            metrics.get('total_return', 0) >= self.target_metrics['min_return']
        )
    
    def print_calibration_results(self, best_combinations):
        """Imprime resultados de calibración"""
        
        print("\n" + "="*80)
        print("📊 RESULTADOS DE CALIBRACIÓN")
        print("="*80)
        
        if not best_combinations:
            print("❌ No se encontraron configuraciones que cumplan los objetivos")
            print("\nConsiderar:")
            print("• Relajar objetivos mínimos")
            print("• Ampliar rangos de parámetros")
            print("• Revisar lógica de señales")
            return
        
        print(f"\n✅ Se encontraron {len(best_combinations)} configuraciones óptimas")
        
        # Mostrar top 3
        for i, combo in enumerate(best_combinations[:3], 1):
            print(f"\n{'🥇' if i==1 else '🥈' if i==2 else '🥉'} CONFIGURACIÓN #{i}")
            print("-"*60)
            
            params = combo['params']
            metrics = combo['results']['metrics']
            
            print("📊 MÉTRICAS:")
            print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
            print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"  • Total Return: {metrics['total_return']:.1f}%")
            print(f"  • Total Trades: {metrics['total_trades']}")
            print(f"  • Max Drawdown: {metrics['max_drawdown']:.1f}%")
            
            print("\n⚙️ PARÁMETROS:")
            print(f"  • Score Mínimo: {params['min_score']}")
            print(f"  • Stop Loss: {params['stop_loss_pct']*100:.0f}%")
            print(f"  • Take Profit: {params['take_profit_pct']*100:.0f}%")
            print(f"  • Position Size: {params['position_size_pct']*100:.0f}%")
            print(f"  • RSI Oversold: {params['rsi_oversold']}")
            print(f"  • RSI Overbought: {params['rsi_overbought']}")
        
        # Análisis de patrones
        self.analyze_patterns(best_combinations[:10])
    
    def analyze_patterns(self, combinations):
        """Analiza patrones en las mejores configuraciones"""
        
        print("\n" + "="*80)
        print("🔍 ANÁLISIS DE PATRONES")
        print("-"*60)
        
        if not combinations:
            return
        
        # Extraer todos los parámetros
        all_params = {}
        for combo in combinations:
            for param, value in combo['params'].items():
                if param not in all_params:
                    all_params[param] = []
                all_params[param].append(value)
        
        # Calcular promedios y modas
        print("\n📊 VALORES ÓPTIMOS PROMEDIO:")
        for param, values in all_params.items():
            avg_value = np.mean(values)
            most_common = max(set(values), key=values.count)
            
            if param in ['stop_loss_pct', 'take_profit_pct', 'position_size_pct']:
                print(f"  • {param}: {avg_value*100:.1f}% (más común: {most_common*100:.0f}%)")
            else:
                print(f"  • {param}: {avg_value:.1f} (más común: {most_common})")
        
        print("\n💡 RECOMENDACIONES:")
        
        # Analizar tendencias
        avg_min_score = np.mean(all_params['min_score'])
        if avg_min_score < 5.5:
            print("• ✅ Sistema funciona mejor con threshold bajo (5.0-5.5)")
        else:
            print("• ⚠️ Sistema requiere señales de alta calidad (6.0+)")
        
        avg_stop_loss = np.mean(all_params['stop_loss_pct'])
        if avg_stop_loss <= 0.03:
            print("• ✅ Stop loss ajustado (2-3%) mejora win rate")
        else:
            print("• ⚠️ Stop loss amplio necesario para volatilidad")
        
        avg_take_profit = np.mean(all_params['take_profit_pct'])
        if avg_take_profit >= 0.20:
            print("• ✅ Take profit amplio (20%+) maximiza ganancias")
        else:
            print("• ⚠️ Take profit conservador limita potencial")
    
    def save_optimal_configuration(self):
        """Guarda la configuración óptima"""
        
        if not self.best_params:
            return
        
        config = {
            'calibration_date': datetime.now().isoformat(),
            'parameters': self.best_params,
            'metrics': self.best_results['metrics'] if hasattr(self, 'best_results') else {},
            'periods_used': [p['name'] for p in self.calibration_periods]
        }
        
        with open('optimal_config.json', 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print("\n💾 Configuración óptima guardada en 'optimal_config.json'")

def main():
    """Función principal"""
    
    print("🚀 INICIANDO CALIBRACIÓN DEL SISTEMA")
    print("="*80)
    
    calibrator = SystemCalibrator(initial_capital=10000)
    
    # Ejecutar calibración
    best_params, best_results = calibrator.run_calibration()
    
    if best_params:
        print("\n" + "="*80)
        print("✅ CALIBRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*80)
        
        print("\n🎯 CONFIGURACIÓN ÓPTIMA ENCONTRADA:")
        print(json.dumps(best_params, indent=2))
        
        print("\n📊 MÉTRICAS ESPERADAS:")
        if best_results:
            metrics = best_results['metrics']
            print(f"• Win Rate: {metrics['win_rate']:.1f}%")
            print(f"• Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"• Return Esperado: {metrics['total_return']:.1f}%")
            
            # Proyección anual
            annual_return = metrics['total_return'] * (365 / 270)
            print(f"• Return Anualizado: {annual_return:.1f}%")
    else:
        print("\n❌ No se encontró configuración óptima")
        print("Considerar ajustar rangos de parámetros o criterios de éxito")
    
    return best_params, best_results

if __name__ == "__main__":
    main()