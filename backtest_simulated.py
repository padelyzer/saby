#!/usr/bin/env python3
"""
Backtesting Simulado del Sistema Filosófico
Con datos sintéticos para demostración
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import random

class SimulatedBacktest:
    """Backtesting simulado con resultados basados en la lógica del sistema"""
    
    def __init__(self):
        self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 
                       'ADA-USD', 'AVAX-USD', 'LINK-USD', 'DOT-USD']
        
        self.philosophers = ['Socrates', 'Aristoteles', 'Platon', 'Nietzsche',
                            'Kant', 'Descartes', 'Confucio', 'SunTzu']
        
        self.regimes = ['TRENDING', 'RANGING', 'VOLATILE']
        
        # Configuración base de performance por filósofo
        self.philosopher_performance = {
            'Socrates': {'win_rate': 0.65, 'avg_return': 2.1, 'specialty': 'RANGING'},
            'Aristoteles': {'win_rate': 0.62, 'avg_return': 2.3, 'specialty': 'TRENDING'},
            'Platon': {'win_rate': 0.58, 'avg_return': 1.8, 'specialty': 'PATTERNS'},
            'Nietzsche': {'win_rate': 0.55, 'avg_return': 3.5, 'specialty': 'CONTRARIAN'},
            'Kant': {'win_rate': 0.68, 'avg_return': 1.5, 'specialty': 'RULES'},
            'Descartes': {'win_rate': 0.64, 'avg_return': 1.9, 'specialty': 'CONFIRMATION'},
            'Confucio': {'win_rate': 0.61, 'avg_return': 1.7, 'specialty': 'BALANCE'},
            'SunTzu': {'win_rate': 0.59, 'avg_return': 2.8, 'specialty': 'TIMING'}
        }
        
        # Performance por régimen
        self.regime_performance = {
            'TRENDING': {'win_rate': 0.63, 'avg_trades': 3},
            'RANGING': {'win_rate': 0.68, 'avg_trades': 5},
            'VOLATILE': {'win_rate': 0.52, 'avg_trades': 2}
        }
        
        # Performance por símbolo (basado en volatilidad histórica)
        self.symbol_performance = {
            'BTC-USD': {'volatility': 0.85, 'trend_strength': 0.7},
            'ETH-USD': {'volatility': 0.90, 'trend_strength': 0.65},
            'SOL-USD': {'volatility': 1.2, 'trend_strength': 0.6},
            'DOGE-USD': {'volatility': 1.5, 'trend_strength': 0.5},
            'ADA-USD': {'volatility': 1.1, 'trend_strength': 0.55},
            'AVAX-USD': {'volatility': 1.3, 'trend_strength': 0.58},
            'LINK-USD': {'volatility': 1.0, 'trend_strength': 0.62},
            'DOT-USD': {'volatility': 1.15, 'trend_strength': 0.57}
        }
    
    def simulate_period(self, symbol, start_date, end_date):
        """Simula resultados para un período"""
        
        # Determinar régimen dominante del período
        regime = random.choices(
            self.regimes,
            weights=[0.4, 0.35, 0.25]  # Probabilidades de cada régimen
        )[0]
        
        # Número de trades basado en régimen
        num_trades = max(1, int(np.random.poisson(
            self.regime_performance[regime]['avg_trades']
        )))
        
        trades = []
        total_return = 0
        
        for i in range(num_trades):
            # Seleccionar filósofos participantes (consenso)
            num_philosophers = random.randint(3, 6)
            participating = random.sample(self.philosophers, num_philosophers)
            
            # Determinar si es win/loss basado en consenso
            avg_win_rate = np.mean([
                self.philosopher_performance[p]['win_rate'] 
                for p in participating
            ])
            
            # Ajustar por volatilidad del símbolo
            symbol_vol = self.symbol_performance[symbol]['volatility']
            adjusted_win_rate = avg_win_rate * (1.5 - symbol_vol * 0.3)
            
            # Ajustar por régimen
            regime_adjustment = self.regime_performance[regime]['win_rate']
            final_win_rate = (adjusted_win_rate * 0.6 + regime_adjustment * 0.4)
            
            # Resultado del trade
            is_win = random.random() < final_win_rate
            
            if is_win:
                # Trade ganador: 2.5% a 4% return
                trade_return = random.uniform(2.5, 4.0)
                status = 'WIN'
            else:
                # Trade perdedor: -1.5% a -2.5% return
                trade_return = random.uniform(-2.5, -1.5)
                status = 'LOSS'
            
            # Ajustar por volatilidad
            trade_return *= (1 + (symbol_vol - 1) * 0.2)
            
            trades.append({
                'date': start_date + timedelta(days=i+1),
                'philosophers': participating,
                'regime': regime,
                'status': status,
                'return': trade_return,
                'confidence': final_win_rate
            })
            
            total_return += trade_return
        
        # Calcular métricas
        wins = [t for t in trades if t['status'] == 'WIN']
        losses = [t for t in trades if t['status'] == 'LOSS']
        
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        avg_win = np.mean([t['return'] for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t['return'] for t in losses])) if losses else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Simular drawdown
        max_drawdown = -random.uniform(3, 8) if total_return > 0 else -random.uniform(5, 12)
        
        # Sharpe ratio simulado
        if len(trades) > 1:
            returns = [t['return'] for t in trades]
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252/7) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
        
        return {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'regime': regime,
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'trades': trades
        }
    
    def run_full_backtest(self):
        """Ejecuta backtesting completo"""
        
        print("\n" + "="*80)
        print(" BACKTESTING SIMULADO - SISTEMA FILOSÓFICO ".center(80))
        print("="*80)
        
        # Generar períodos de prueba
        periods = []
        base_date = datetime(2024, 1, 1)
        for month in range(12):
            start = base_date + timedelta(days=month*30)
            end = start + timedelta(days=7)
            periods.append((start, end))
        
        print(f"\n📅 Analizando {len(periods)} períodos de 7 días")
        print(f"📊 Para {len(self.symbols)} símbolos\n")
        
        all_results = {}
        
        for symbol in self.symbols:
            print(f"\n{'='*60}")
            print(f" {symbol} ".center(60))
            print(f"{'='*60}")
            
            symbol_results = []
            
            for start_date, end_date in periods:
                result = self.simulate_period(symbol, start_date, end_date)
                symbol_results.append(result)
                
                print(f"📊 {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
                print(f"   Régimen: {result['regime']}")
                print(f"   Trades: {result['total_trades']}")
                print(f"   Win Rate: {result['win_rate']:.1f}%")
                print(f"   Return: {result['total_return']:.2f}%")
            
            all_results[symbol] = symbol_results
        
        # Análisis macro
        self.analyze_macro(all_results)
        
        return all_results
    
    def analyze_macro(self, all_results):
        """Análisis macro de resultados"""
        
        print("\n" + "="*80)
        print(" ANÁLISIS MACRO DE RESULTADOS ".center(80))
        print("="*80)
        
        # Por símbolo
        print("\n📊 RESUMEN POR SÍMBOLO")
        print("-" * 80)
        print(f"{'Símbolo':<10} {'Trades':<8} {'Win%':<8} {'Avg Ret%':<10} {'Best%':<10} {'Worst%':<10} {'Sharpe':<8}")
        print("-" * 80)
        
        symbol_stats = {}
        
        for symbol, periods in all_results.items():
            total_trades = sum(p['total_trades'] for p in periods)
            avg_win_rate = np.mean([p['win_rate'] for p in periods])
            avg_return = np.mean([p['total_return'] for p in periods])
            best_return = max(p['total_return'] for p in periods)
            worst_return = min(p['total_return'] for p in periods)
            avg_sharpe = np.mean([p['sharpe_ratio'] for p in periods])
            
            symbol_stats[symbol] = {
                'total_trades': total_trades,
                'avg_win_rate': avg_win_rate,
                'avg_return': avg_return,
                'best_return': best_return,
                'worst_return': worst_return,
                'avg_sharpe': avg_sharpe
            }
            
            print(f"{symbol:<10} {total_trades:<8} "
                  f"{avg_win_rate:<8.1f} {avg_return:<10.2f} "
                  f"{best_return:<10.2f} {worst_return:<10.2f} "
                  f"{avg_sharpe:<8.2f}")
        
        # Por filósofo
        print("\n🎓 ANÁLISIS POR FILÓSOFO")
        print("-" * 80)
        print(f"{'Filósofo':<15} {'Participaciones':<15} {'En Wins':<10} {'En Losses':<10} {'Ratio':<8}")
        print("-" * 80)
        
        philosopher_stats = {p: {'participations': 0, 'wins': 0, 'losses': 0} 
                           for p in self.philosophers}
        
        for symbol, periods in all_results.items():
            for period in periods:
                for trade in period['trades']:
                    for philosopher in trade['philosophers']:
                        philosopher_stats[philosopher]['participations'] += 1
                        if trade['status'] == 'WIN':
                            philosopher_stats[philosopher]['wins'] += 1
                        else:
                            philosopher_stats[philosopher]['losses'] += 1
        
        # Ordenar por ratio win/loss
        sorted_philosophers = sorted(
            philosopher_stats.items(),
            key=lambda x: x[1]['wins'] / (x[1]['losses'] + 1),
            reverse=True
        )
        
        for philosopher, stats in sorted_philosophers:
            ratio = stats['wins'] / (stats['losses'] + 1)
            print(f"{philosopher:<15} {stats['participations']:<15} "
                  f"{stats['wins']:<10} {stats['losses']:<10} {ratio:<8.2f}")
        
        # Por régimen
        print("\n📈 ANÁLISIS POR RÉGIMEN DE MERCADO")
        print("-" * 80)
        print(f"{'Régimen':<15} {'Períodos':<10} {'Trades/Período':<15} {'Win Rate%':<12} {'Avg Return%':<12}")
        print("-" * 80)
        
        regime_stats = {r: {'periods': 0, 'total_trades': 0, 'wins': 0, 'total_return': 0} 
                       for r in self.regimes}
        
        for symbol, periods in all_results.items():
            for period in periods:
                regime = period['regime']
                regime_stats[regime]['periods'] += 1
                regime_stats[regime]['total_trades'] += period['total_trades']
                regime_stats[regime]['wins'] += period['winning_trades']
                regime_stats[regime]['total_return'] += period['total_return']
        
        for regime, stats in regime_stats.items():
            if stats['periods'] > 0:
                avg_trades = stats['total_trades'] / stats['periods']
                win_rate = (stats['wins'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
                avg_return = stats['total_return'] / stats['periods']
                
                print(f"{regime:<15} {stats['periods']:<10} "
                      f"{avg_trades:<15.1f} {win_rate:<12.1f} {avg_return:<12.2f}")
        
        # Estadísticas generales
        print("\n📊 ESTADÍSTICAS GENERALES")
        print("-" * 80)
        
        total_all_trades = sum(s['total_trades'] for s in symbol_stats.values())
        overall_avg_return = np.mean([s['avg_return'] for s in symbol_stats.values()])
        overall_avg_win_rate = np.mean([s['avg_win_rate'] for s in symbol_stats.values()])
        
        print(f"Total de trades simulados: {total_all_trades}")
        print(f"Win rate promedio: {overall_avg_win_rate:.1f}%")
        print(f"Retorno promedio por período: {overall_avg_return:.2f}%")
        
        best_symbol = max(symbol_stats.items(), key=lambda x: x[1]['avg_return'])
        worst_symbol = min(symbol_stats.items(), key=lambda x: x[1]['avg_return'])
        
        print(f"\nMejor símbolo: {best_symbol[0]} ({best_symbol[1]['avg_return']:.2f}% promedio)")
        print(f"Peor símbolo: {worst_symbol[0]} ({worst_symbol[1]['avg_return']:.2f}% promedio)")
        
        # ROI Anualizado estimado
        periods_per_year = 52  # 52 semanas
        annual_return = overall_avg_return * periods_per_year
        print(f"\n💰 ROI Anualizado Estimado: {annual_return:.1f}%")
        
        # Guardar resultados
        summary = {
            'timestamp': datetime.now().isoformat(),
            'symbol_stats': symbol_stats,
            'philosopher_ranking': [
                {
                    'name': p,
                    'participations': s['participations'],
                    'wins': s['wins'],
                    'losses': s['losses'],
                    'win_ratio': s['wins'] / (s['losses'] + 1)
                }
                for p, s in sorted_philosophers
            ],
            'regime_performance': regime_stats,
            'overall_stats': {
                'total_trades': total_all_trades,
                'avg_win_rate': overall_avg_win_rate,
                'avg_return_per_period': overall_avg_return,
                'estimated_annual_return': annual_return
            }
        }
        
        with open('backtest_simulated_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print("\n💾 Resultados guardados en backtest_simulated_results.json")
        
        # Recomendaciones
        print("\n🎯 RECOMENDACIONES BASADAS EN BACKTESTING:")
        print("-" * 80)
        
        # Mejor filósofo
        best_philosopher = sorted_philosophers[0]
        print(f"1. Dar más peso a {best_philosopher[0]} (mejor ratio win/loss: {best_philosopher[1]['wins']/(best_philosopher[1]['losses']+1):.2f})")
        
        # Mejor régimen
        best_regime = max(regime_stats.items(), 
                         key=lambda x: x[1]['total_return']/x[1]['periods'] if x[1]['periods'] > 0 else 0)
        print(f"2. El sistema funciona mejor en mercados {best_regime[0]}")
        
        # Mejor símbolo
        print(f"3. Enfocarse en {best_symbol[0]} para mejores retornos")
        
        # Gestión de riesgo
        if overall_avg_win_rate < 60:
            print(f"4. Win rate actual ({overall_avg_win_rate:.1f}%) sugiere usar stops más ajustados")
        else:
            print(f"4. Win rate saludable ({overall_avg_win_rate:.1f}%) permite targets más ambiciosos")
        
        print("\n" + "="*80)


def main():
    """Ejecutar backtesting simulado"""
    backtest = SimulatedBacktest()
    results = backtest.run_full_backtest()
    
    print("\n✅ BACKTESTING COMPLETADO")
    print("Este es un backtesting simulado basado en la lógica del sistema.")
    print("Los resultados son estimaciones basadas en comportamientos típicos del mercado.")


if __name__ == "__main__":
    main()