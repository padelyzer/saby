#!/usr/bin/env python3
"""
Walk-Forward Analysis para Validación Robusta
Entrena en un período, valida en el siguiente, repite el proceso
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from robust_trading_system_v2 import RobustTradingSystemV2
import warnings
warnings.filterwarnings('ignore')

class WalkForwardAnalysis:
    """
    Implementa walk-forward analysis para validación robusta
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        
        # Parámetros a optimizar con rangos conservadores
        self.param_ranges = {
            'min_confirmations': [2, 3],
            'atr_multiplier_sl': [1.0, 1.5, 2.0],
            'atr_multiplier_tp': [2.0, 2.5, 3.0],
            'risk_per_trade': [0.01, 0.015, 0.02],
            'volume_threshold': [1.0, 1.1, 1.2]
        }
        
        # Períodos para walk-forward (6 meses train, 3 meses test)
        self.walk_forward_periods = [
            {
                'train_start': '2023-01-01',
                'train_end': '2023-06-30',
                'test_start': '2023-07-01',
                'test_end': '2023-09-30',
                'name': 'WF_Period_1'
            },
            {
                'train_start': '2023-04-01',
                'train_end': '2023-09-30',
                'test_start': '2023-10-01',
                'test_end': '2023-12-31',
                'name': 'WF_Period_2'
            },
            {
                'train_start': '2023-07-01',
                'train_end': '2023-12-31',
                'test_start': '2024-01-01',
                'test_end': '2024-03-31',
                'name': 'WF_Period_3'
            },
            {
                'train_start': '2023-10-01',
                'train_end': '2024-03-31',
                'test_start': '2024-04-01',
                'test_end': '2024-06-30',
                'name': 'WF_Period_4'
            },
            {
                'train_start': '2024-01-01',
                'train_end': '2024-06-30',
                'test_start': '2024-07-01',
                'test_end': '2024-09-30',
                'name': 'WF_Period_5'
            }
        ]
        
        self.results = []
        self.best_params_history = []
        
    def generate_param_combinations(self):
        """
        Genera combinaciones de parámetros para probar
        """
        from itertools import product
        
        keys = list(self.param_ranges.keys())
        values = [self.param_ranges[k] for k in keys]
        
        combinations = []
        for combo in product(*values):
            param_dict = dict(zip(keys, combo))
            combinations.append(param_dict)
        
        return combinations
    
    def optimize_parameters(self, train_start, train_end, symbol='BTC-USD'):
        """
        Optimiza parámetros en período de entrenamiento
        """
        param_combinations = self.generate_param_combinations()
        best_score = -float('inf')
        best_params = None
        best_metrics = None
        
        print(f"  Testing {len(param_combinations)} parameter combinations...")
        
        for params in param_combinations:
            # Crear sistema con parámetros específicos
            system = RobustTradingSystemV2(self.initial_capital)
            
            # Actualizar parámetros
            for key, value in params.items():
                if key in system.base_params:
                    system.base_params[key] = value
            
            # Ejecutar backtest
            trades = system.backtest(symbol, train_start, train_end)
            
            if trades:
                metrics = system.calculate_metrics(trades)
                
                # Calcular score compuesto (priorizar consistencia)
                score = self.calculate_optimization_score(metrics)
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_metrics = metrics
        
        return best_params, best_metrics, best_score
    
    def calculate_optimization_score(self, metrics):
        """
        Calcula score para optimización priorizando robustez
        """
        if metrics['total_trades'] < 5:
            return -1000  # Penalizar fuertemente si hay muy pocos trades
        
        # Score basado en múltiples factores
        score = 0
        
        # Win rate (importante pero no lo único)
        score += metrics['win_rate'] * 0.3
        
        # Profit factor (muy importante)
        score += min(metrics['profit_factor'] * 20, 40)
        
        # Sharpe ratio (consistencia)
        score += min(metrics['sharpe_ratio'] * 10, 20)
        
        # Penalizar drawdown excesivo
        if metrics['max_drawdown'] > 20:
            score -= (metrics['max_drawdown'] - 20) * 0.5
        
        # Bonus por número razonable de trades
        if 10 <= metrics['total_trades'] <= 30:
            score += 10
        elif metrics['total_trades'] > 30:
            score += 5
        
        # Penalizar si el sistema es demasiado activo
        if metrics['total_trades'] > 50:
            score -= 10
        
        return score
    
    def validate_parameters(self, params, test_start, test_end, symbol='BTC-USD'):
        """
        Valida parámetros en período de prueba
        """
        system = RobustTradingSystemV2(self.initial_capital)
        
        # Actualizar parámetros
        for key, value in params.items():
            if key in system.base_params:
                system.base_params[key] = value
        
        # Ejecutar backtest
        trades = system.backtest(symbol, test_start, test_end)
        
        if trades:
            metrics = system.calculate_metrics(trades)
            return trades, metrics
        
        return [], None
    
    def run_walk_forward(self, symbol='BTC-USD'):
        """
        Ejecuta walk-forward analysis completo
        """
        print("🚀 WALK-FORWARD ANALYSIS")
        print("="*80)
        print(f"Symbol: {symbol}")
        print(f"Periods: {len(self.walk_forward_periods)}")
        print(f"Parameter combinations: {len(self.generate_param_combinations())}")
        print("="*80)
        
        all_test_trades = []
        
        for i, period in enumerate(self.walk_forward_periods, 1):
            print(f"\n📊 WALK-FORWARD PERIOD {i}/{len(self.walk_forward_periods)}")
            print(f"Train: {period['train_start']} → {period['train_end']}")
            print(f"Test:  {period['test_start']} → {period['test_end']}")
            print("-"*60)
            
            # Fase de optimización (entrenamiento)
            print("\n🔧 Optimization Phase:")
            best_params, train_metrics, train_score = self.optimize_parameters(
                period['train_start'], 
                period['train_end'],
                symbol
            )
            
            if best_params:
                print(f"  Best params found:")
                for key, value in best_params.items():
                    print(f"    • {key}: {value}")
                
                if train_metrics:
                    print(f"\n  Training metrics:")
                    print(f"    • Win Rate: {train_metrics['win_rate']:.1f}%")
                    print(f"    • Profit Factor: {train_metrics['profit_factor']:.2f}")
                    print(f"    • Sharpe Ratio: {train_metrics['sharpe_ratio']:.2f}")
                    print(f"    • Score: {train_score:.1f}")
                
                # Fase de validación (test)
                print("\n📈 Validation Phase:")
                test_trades, test_metrics = self.validate_parameters(
                    best_params,
                    period['test_start'],
                    period['test_end'],
                    symbol
                )
                
                if test_metrics:
                    print(f"  Test metrics:")
                    print(f"    • Trades: {test_metrics['total_trades']}")
                    print(f"    • Win Rate: {test_metrics['win_rate']:.1f}%")
                    print(f"    • Profit Factor: {test_metrics['profit_factor']:.2f}")
                    print(f"    • Return: {test_metrics['total_return']:.1f}%")
                    print(f"    • Sharpe Ratio: {test_metrics['sharpe_ratio']:.2f}")
                    
                    # Guardar resultados
                    self.results.append({
                        'period': period['name'],
                        'train_metrics': train_metrics,
                        'test_metrics': test_metrics,
                        'params': best_params,
                        'trades': test_trades
                    })
                    
                    all_test_trades.extend(test_trades)
                    self.best_params_history.append(best_params)
                else:
                    print("  ❌ No trades generated in test period")
            else:
                print("  ❌ No valid parameters found in training")
        
        # Análisis global
        self.print_global_analysis(all_test_trades)
        
        # Encontrar parámetros más consistentes
        self.find_robust_parameters()
        
        return self.results
    
    def print_global_analysis(self, all_trades):
        """
        Imprime análisis global de todos los períodos de test
        """
        print("\n" + "="*80)
        print("📊 GLOBAL WALK-FORWARD RESULTS")
        print("="*80)
        
        if not all_trades:
            print("❌ No trades generated across all test periods")
            return
        
        # Calcular métricas globales
        system = RobustTradingSystemV2(self.initial_capital)
        global_metrics = system.calculate_metrics(all_trades)
        
        print(f"\n📈 Overall Test Performance:")
        print(f"  • Total Test Trades: {global_metrics['total_trades']}")
        print(f"  • Win Rate: {global_metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {global_metrics['profit_factor']:.2f}")
        print(f"  • Sharpe Ratio: {global_metrics['sharpe_ratio']:.2f}")
        print(f"  • Total Return: {global_metrics['total_return']:.1f}%")
        print(f"  • Max Drawdown: {global_metrics['max_drawdown']:.1f}%")
        
        # Análisis de consistencia
        print(f"\n📊 Consistency Analysis:")
        
        profitable_periods = sum(1 for r in self.results 
                               if r['test_metrics'] and r['test_metrics']['total_return'] > 0)
        total_periods = len([r for r in self.results if r['test_metrics']])
        
        if total_periods > 0:
            consistency_rate = (profitable_periods / total_periods) * 100
            print(f"  • Profitable Periods: {profitable_periods}/{total_periods} ({consistency_rate:.1f}%)")
        
        # Calcular desviación estándar de returns
        test_returns = [r['test_metrics']['total_return'] 
                       for r in self.results if r['test_metrics']]
        if test_returns:
            avg_return = np.mean(test_returns)
            std_return = np.std(test_returns)
            print(f"  • Average Period Return: {avg_return:.1f}%")
            print(f"  • Return Std Dev: {std_return:.1f}%")
        
        # Evaluación final
        print(f"\n🎯 SYSTEM EVALUATION:")
        
        if global_metrics['win_rate'] >= 45 and global_metrics['profit_factor'] >= 1.3:
            if consistency_rate >= 60:
                print("✅ ROBUST SYSTEM - High consistency across periods")
                print("   Ready for production with careful monitoring")
            else:
                print("⚠️ MODERATELY ROBUST - Acceptable but variable performance")
                print("   Requires extended paper trading")
        else:
            print("❌ INSUFFICIENT ROBUSTNESS - Poor out-of-sample performance")
            print("   System needs fundamental redesign")
    
    def find_robust_parameters(self):
        """
        Encuentra los parámetros más robustos (que aparecen con más frecuencia)
        """
        if not self.best_params_history:
            return None
        
        print("\n" + "="*80)
        print("🔍 ROBUST PARAMETER ANALYSIS")
        print("="*80)
        
        # Contar frecuencia de cada valor de parámetro
        param_frequencies = {}
        
        for params in self.best_params_history:
            for key, value in params.items():
                if key not in param_frequencies:
                    param_frequencies[key] = {}
                if value not in param_frequencies[key]:
                    param_frequencies[key][value] = 0
                param_frequencies[key][value] += 1
        
        # Encontrar valores más comunes
        robust_params = {}
        
        print("\nMost frequent parameter values:")
        for param_name, value_counts in param_frequencies.items():
            sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
            most_common_value = sorted_values[0][0]
            frequency = sorted_values[0][1]
            total = len(self.best_params_history)
            
            robust_params[param_name] = most_common_value
            
            print(f"\n{param_name}:")
            for value, count in sorted_values:
                pct = (count / total) * 100
                marker = "⭐" if value == most_common_value else "  "
                print(f"  {marker} {value}: {count}/{total} ({pct:.0f}%)")
        
        # Guardar parámetros robustos
        self.save_robust_parameters(robust_params)
        
        return robust_params
    
    def save_robust_parameters(self, params):
        """
        Guarda los parámetros robustos encontrados
        """
        config = {
            'analysis_date': datetime.now().isoformat(),
            'method': 'walk_forward_analysis',
            'robust_parameters': params,
            'periods_tested': len(self.walk_forward_periods),
            'total_test_trades': sum(len(r['trades']) for r in self.results if 'trades' in r),
            'consistency_metrics': {
                'profitable_periods': sum(1 for r in self.results 
                                        if r['test_metrics'] and r['test_metrics']['total_return'] > 0),
                'total_periods': len([r for r in self.results if r['test_metrics']])
            }
        }
        
        with open('robust_parameters.json', 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print("\n💾 Robust parameters saved to 'robust_parameters.json'")

def main():
    """
    Función principal
    """
    print("🚀 STARTING WALK-FORWARD VALIDATION")
    print("="*80)
    
    analyzer = WalkForwardAnalysis(initial_capital=10000)
    
    # Ejecutar con múltiples símbolos para más robustez
    symbols = ['BTC-USD']  # Empezar con BTC, luego expandir
    
    for symbol in symbols:
        print(f"\n🪙 Analyzing {symbol}")
        results = analyzer.run_walk_forward(symbol)
    
    print("\n" + "="*80)
    print("✅ WALK-FORWARD ANALYSIS COMPLETE")
    print("="*80)
    
    return results

if __name__ == "__main__":
    results = main()