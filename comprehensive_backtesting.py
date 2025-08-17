#!/usr/bin/env python3
"""
Backtesting Comprehensivo del Sistema Final
Prueba exhaustiva con múltiples períodos, símbolos y métricas detalladas
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

from final_robust_system import FinalRobustSystem

class ComprehensiveBacktesting:
    """
    Backtesting completo y detallado del sistema final
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.system = FinalRobustSystem(initial_capital)
        
        # Períodos de backtesting extendidos
        self.test_periods = [
            # 2022 - Año completo (Bear Market)
            {
                'name': '2022_BEAR_MARKET',
                'description': 'Mercado bajista extremo - Colapso crypto',
                'start': '2022-01-01',
                'end': '2022-12-31',
                'market_type': 'EXTREME_BEAR'
            },
            # 2023 Q1-Q2 - Recuperación temprana
            {
                'name': '2023_H1_RECOVERY',
                'description': 'Recuperación post-FTX',
                'start': '2023-01-01',
                'end': '2023-06-30',
                'market_type': 'EARLY_RECOVERY'
            },
            # 2023 Q3-Q4 - Consolidación y rally
            {
                'name': '2023_H2_RALLY',
                'description': 'Anticipación ETF Bitcoin',
                'start': '2023-07-01',
                'end': '2023-12-31',
                'market_type': 'BULL_RALLY'
            },
            # 2024 Q1 - Post ETF
            {
                'name': '2024_Q1_POST_ETF',
                'description': 'Rally post aprobación ETF',
                'start': '2024-01-01',
                'end': '2024-03-31',
                'market_type': 'STRONG_BULL'
            },
            # 2024 Q2 - Corrección
            {
                'name': '2024_Q2_CORRECTION',
                'description': 'Corrección y consolidación',
                'start': '2024-04-01',
                'end': '2024-06-30',
                'market_type': 'CORRECTION'
            },
            # 2024 Q3 - Verano
            {
                'name': '2024_Q3_SUMMER',
                'description': 'Período de verano volátil',
                'start': '2024-07-01',
                'end': '2024-09-30',
                'market_type': 'VOLATILE'
            },
            # 2024 Q4 hasta ahora
            {
                'name': '2024_Q4_CURRENT',
                'description': 'Período actual',
                'start': '2024-10-01',
                'end': '2024-11-15',
                'market_type': 'CURRENT'
            }
        ]
        
        # Símbolos a testear
        self.symbols = {
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum',
            'SOL-USD': 'Solana',
            'BNB-USD': 'Binance Coin',
            'ADA-USD': 'Cardano'
        }
        
        self.all_results = []
        
    def run_comprehensive_backtest(self):
        """
        Ejecuta backtesting comprehensivo
        """
        print("="*80)
        print("🚀 BACKTESTING COMPREHENSIVO - SISTEMA FINAL")
        print("="*80)
        print(f"💰 Capital Inicial: ${self.initial_capital:,}")
        print(f"📊 Símbolos: {len(self.symbols)}")
        print(f"📅 Períodos: {len(self.test_periods)}")
        print(f"⏱️ Rango Total: 2022-01-01 a 2024-11-15 (casi 3 años)")
        print("="*80)
        
        # Resultados por período
        period_results = []
        
        for period in self.test_periods:
            print(f"\n{'='*80}")
            print(f"📅 PERÍODO: {period['name']}")
            print(f"📝 {period['description']}")
            print(f"📆 {period['start']} → {period['end']}")
            print(f"🌍 Tipo de Mercado: {period['market_type']}")
            print("="*80)
            
            period_trades = []
            symbol_results = {}
            
            for symbol, name in self.symbols.items():
                print(f"\n  🪙 Testing {name} ({symbol})...")
                
                # Ejecutar backtest
                trades = self.system.backtest(symbol, period['start'], period['end'])
                
                if trades:
                    metrics = self.system.analyze_performance(trades)
                    symbol_results[symbol] = {
                        'trades': trades,
                        'metrics': metrics
                    }
                    period_trades.extend(trades)
                    
                    # Mostrar resultados del símbolo
                    print(f"    ✅ {metrics['total_trades']} trades")
                    print(f"    • Win Rate: {metrics['win_rate']:.1f}%")
                    print(f"    • Profit Factor: {metrics['profit_factor']:.2f}")
                    print(f"    • Return: {metrics['total_return']:.1f}%")
                else:
                    print(f"    ❌ No trades generated")
            
            # Análisis del período
            if period_trades:
                period_metrics = self.system.analyze_performance(period_trades)
                period_result = {
                    'period': period,
                    'trades': period_trades,
                    'metrics': period_metrics,
                    'symbol_results': symbol_results
                }
                period_results.append(period_result)
                
                self.print_period_summary(period['name'], period_metrics, len(period_trades))
            else:
                print(f"\n  ⚠️ No trades in this period")
        
        # Análisis global
        self.print_global_analysis(period_results)
        
        # Análisis por símbolo
        self.analyze_by_symbol(period_results)
        
        # Análisis por tipo de mercado
        self.analyze_by_market_type(period_results)
        
        # Evaluación final
        self.final_evaluation(period_results)
        
        return period_results
    
    def print_period_summary(self, period_name, metrics, trade_count):
        """
        Imprime resumen del período
        """
        print(f"\n  📊 RESUMEN DEL PERÍODO {period_name}:")
        print(f"  {'='*60}")
        print(f"  • Total Trades: {trade_count}")
        print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  • Total Return: {metrics['total_return']:.1f}%")
        print(f"  • Avg Win: ${metrics['avg_win']:.2f}")
        print(f"  • Avg Loss: ${metrics['avg_loss']:.2f}")
        print(f"  • Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  • Max Drawdown: {metrics['max_drawdown']:.1f}%")
        
        # Evaluación rápida
        if metrics['profit_factor'] >= 1.5 and metrics['win_rate'] >= 45:
            print(f"  🟢 Período EXITOSO")
        elif metrics['profit_factor'] >= 1.0:
            print(f"  🟡 Período NEUTRAL")
        else:
            print(f"  🔴 Período NEGATIVO")
    
    def print_global_analysis(self, period_results):
        """
        Imprime análisis global de todos los períodos
        """
        print("\n" + "="*80)
        print("📊 ANÁLISIS GLOBAL - TODOS LOS PERÍODOS")
        print("="*80)
        
        # Combinar todos los trades
        all_trades = []
        for result in period_results:
            all_trades.extend(result['trades'])
        
        if not all_trades:
            print("❌ No se generaron trades en ningún período")
            return
        
        # Métricas globales
        global_metrics = self.system.analyze_performance(all_trades)
        
        print("\n📈 MÉTRICAS GLOBALES:")
        print(f"  • Total Trades: {global_metrics['total_trades']}")
        print(f"  • Win Rate: {global_metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {global_metrics['profit_factor']:.2f}")
        print(f"  • Total Return: {global_metrics['total_return']:.1f}%")
        print(f"  • Average Return per Trade: {global_metrics['avg_return']:.2f}%")
        print(f"  • Sharpe Ratio: {global_metrics['sharpe_ratio']:.2f}")
        print(f"  • Max Drawdown: {global_metrics['max_drawdown']:.1f}%")
        print(f"  • Total P&L: ${global_metrics['total_pnl']:,.2f}")
        
        # Estadísticas adicionales
        print("\n📊 ESTADÍSTICAS ADICIONALES:")
        
        # Calcular duración promedio
        avg_duration = np.mean([t['duration_days'] for t in all_trades])
        print(f"  • Duración Promedio: {avg_duration:.1f} días")
        
        # Ratio ganancia/pérdida
        if global_metrics['avg_loss'] > 0:
            reward_risk = global_metrics['avg_win'] / global_metrics['avg_loss']
            print(f"  • Reward/Risk Ratio: {reward_risk:.2f}")
        
        # Trades por mes
        first_date = min(t['entry_date'] for t in all_trades)
        last_date = max(t['exit_date'] for t in all_trades)
        months = (last_date - first_date).days / 30
        trades_per_month = global_metrics['total_trades'] / months if months > 0 else 0
        print(f"  • Trades por Mes: {trades_per_month:.1f}")
        
        # Períodos rentables
        profitable_periods = sum(1 for r in period_results if r['metrics']['total_return'] > 0)
        total_periods = len(period_results)
        consistency = (profitable_periods / total_periods * 100) if total_periods > 0 else 0
        print(f"  • Períodos Rentables: {profitable_periods}/{total_periods} ({consistency:.1f}%)")
    
    def analyze_by_symbol(self, period_results):
        """
        Analiza performance por símbolo
        """
        print("\n" + "="*80)
        print("📊 ANÁLISIS POR SÍMBOLO")
        print("="*80)
        
        symbol_aggregated = {}
        
        # Agregar trades por símbolo
        for result in period_results:
            for symbol, data in result.get('symbol_results', {}).items():
                if symbol not in symbol_aggregated:
                    symbol_aggregated[symbol] = []
                symbol_aggregated[symbol].extend(data['trades'])
        
        # Analizar cada símbolo
        symbol_metrics = {}
        for symbol, trades in symbol_aggregated.items():
            if trades:
                metrics = self.system.analyze_performance(trades)
                symbol_metrics[symbol] = metrics
                
                print(f"\n🪙 {self.symbols.get(symbol, symbol)}:")
                print(f"  • Trades: {metrics['total_trades']}")
                print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
                print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
                print(f"  • Total Return: {metrics['total_return']:.1f}%")
                print(f"  • Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
                
                # Calificación
                if metrics['profit_factor'] >= 1.3 and metrics['win_rate'] >= 45:
                    print(f"  ⭐ EXCELENTE")
                elif metrics['profit_factor'] >= 1.0:
                    print(f"  ✅ RENTABLE")
                else:
                    print(f"  ❌ NO RENTABLE")
        
        # Mejor y peor símbolo
        if symbol_metrics:
            best_symbol = max(symbol_metrics.items(), key=lambda x: x[1]['total_return'])
            worst_symbol = min(symbol_metrics.items(), key=lambda x: x[1]['total_return'])
            
            print(f"\n🏆 Mejor Símbolo: {self.symbols.get(best_symbol[0], best_symbol[0])} "
                  f"({best_symbol[1]['total_return']:.1f}% return)")
            print(f"💔 Peor Símbolo: {self.symbols.get(worst_symbol[0], worst_symbol[0])} "
                  f"({worst_symbol[1]['total_return']:.1f}% return)")
    
    def analyze_by_market_type(self, period_results):
        """
        Analiza performance por tipo de mercado
        """
        print("\n" + "="*80)
        print("📊 ANÁLISIS POR TIPO DE MERCADO")
        print("="*80)
        
        market_types = {}
        
        # Agrupar por tipo de mercado
        for result in period_results:
            market_type = result['period']['market_type']
            if market_type not in market_types:
                market_types[market_type] = []
            market_types[market_type].extend(result['trades'])
        
        # Analizar cada tipo
        for market_type, trades in market_types.items():
            if trades:
                metrics = self.system.analyze_performance(trades)
                
                print(f"\n🌍 {market_type}:")
                print(f"  • Trades: {metrics['total_trades']}")
                print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
                print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
                print(f"  • Return: {metrics['total_return']:.1f}%")
                
                # Recomendación
                if metrics['profit_factor'] >= 1.2:
                    print(f"  ✅ Sistema funciona bien en {market_type}")
                else:
                    print(f"  ⚠️ Sistema necesita ajustes para {market_type}")
    
    def final_evaluation(self, period_results):
        """
        Evaluación final del sistema
        """
        print("\n" + "="*80)
        print("🎯 EVALUACIÓN FINAL DEL SISTEMA")
        print("="*80)
        
        # Combinar todos los trades
        all_trades = []
        for result in period_results:
            all_trades.extend(result['trades'])
        
        if not all_trades:
            print("❌ Sistema no generó trades - NO APTO")
            return
        
        # Métricas finales
        final_metrics = self.system.analyze_performance(all_trades)
        
        # Sistema de puntuación
        score = 0
        max_score = 10
        
        print("\n📋 CRITERIOS DE EVALUACIÓN:")
        print("-"*60)
        
        # 1. Win Rate (0-2 puntos)
        if final_metrics['win_rate'] >= 50:
            score += 2
            print("✅ Win Rate ≥50%: 2/2 puntos")
        elif final_metrics['win_rate'] >= 45:
            score += 1.5
            print("🟡 Win Rate ≥45%: 1.5/2 puntos")
        elif final_metrics['win_rate'] >= 40:
            score += 1
            print("🟡 Win Rate ≥40%: 1/2 puntos")
        else:
            print("❌ Win Rate <40%: 0/2 puntos")
        
        # 2. Profit Factor (0-2 puntos)
        if final_metrics['profit_factor'] >= 1.5:
            score += 2
            print("✅ Profit Factor ≥1.5: 2/2 puntos")
        elif final_metrics['profit_factor'] >= 1.2:
            score += 1.5
            print("🟡 Profit Factor ≥1.2: 1.5/2 puntos")
        elif final_metrics['profit_factor'] >= 1.0:
            score += 1
            print("🟡 Profit Factor ≥1.0: 1/2 puntos")
        else:
            print("❌ Profit Factor <1.0: 0/2 puntos")
        
        # 3. Sharpe Ratio (0-2 puntos)
        if final_metrics['sharpe_ratio'] >= 1.0:
            score += 2
            print("✅ Sharpe Ratio ≥1.0: 2/2 puntos")
        elif final_metrics['sharpe_ratio'] >= 0.5:
            score += 1.5
            print("🟡 Sharpe Ratio ≥0.5: 1.5/2 puntos")
        elif final_metrics['sharpe_ratio'] >= 0:
            score += 1
            print("🟡 Sharpe Ratio ≥0: 1/2 puntos")
        else:
            print("❌ Sharpe Ratio <0: 0/2 puntos")
        
        # 4. Max Drawdown (0-2 puntos)
        if final_metrics['max_drawdown'] <= 15:
            score += 2
            print("✅ Max Drawdown ≤15%: 2/2 puntos")
        elif final_metrics['max_drawdown'] <= 25:
            score += 1.5
            print("🟡 Max Drawdown ≤25%: 1.5/2 puntos")
        elif final_metrics['max_drawdown'] <= 35:
            score += 1
            print("🟡 Max Drawdown ≤35%: 1/2 puntos")
        else:
            print("❌ Max Drawdown >35%: 0/2 puntos")
        
        # 5. Consistencia (0-2 puntos)
        profitable_periods = sum(1 for r in period_results if r['metrics']['total_return'] > 0)
        total_periods = len(period_results)
        consistency = (profitable_periods / total_periods) if total_periods > 0 else 0
        
        if consistency >= 0.7:
            score += 2
            print(f"✅ Consistencia ≥70%: 2/2 puntos")
        elif consistency >= 0.5:
            score += 1.5
            print(f"🟡 Consistencia ≥50%: 1.5/2 puntos")
        elif consistency >= 0.3:
            score += 1
            print(f"🟡 Consistencia ≥30%: 1/2 puntos")
        else:
            print(f"❌ Consistencia <30%: 0/2 puntos")
        
        # Puntuación final
        print("-"*60)
        print(f"\n🏆 PUNTUACIÓN FINAL: {score:.1f}/{max_score}")
        percentage = (score / max_score) * 100
        print(f"📊 Porcentaje: {percentage:.1f}%")
        
        # Veredicto
        print("\n📝 VEREDICTO:")
        if score >= 8:
            print("⭐⭐⭐ SISTEMA EXCELENTE")
            print("✅ Listo para producción con capital real")
            print("\nRecomendaciones:")
            print("• Comenzar con paper trading 30 días")
            print("• Iniciar con 5% del capital disponible")
            print("• Escalar gradualmente según resultados")
        elif score >= 6:
            print("⭐⭐ SISTEMA BUENO")
            print("✅ Apto para paper trading extendido")
            print("\nRecomendaciones:")
            print("• Paper trading mínimo 60 días")
            print("• Monitorear métricas semanalmente")
            print("• Ajustar parámetros según performance")
        elif score >= 4:
            print("⭐ SISTEMA BÁSICO")
            print("⚠️ Necesita optimización")
            print("\nRecomendaciones:")
            print("• Revisar filtros de entrada")
            print("• Mejorar gestión de riesgo")
            print("• Considerar diferentes timeframes")
        else:
            print("❌ SISTEMA NO APTO")
            print("Requiere rediseño fundamental")
            print("\nProblemas principales:")
            if final_metrics['win_rate'] < 40:
                print("• Win rate muy bajo")
            if final_metrics['profit_factor'] < 1.0:
                print("• Sistema no rentable")
            if final_metrics['max_drawdown'] > 35:
                print("• Riesgo excesivo")
        
        # Guardar resultados
        self.save_results(period_results, final_metrics, score)
    
    def save_results(self, period_results, final_metrics, score):
        """
        Guarda los resultados del backtesting
        """
        results = {
            'date': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'periods_tested': len(self.test_periods),
            'symbols_tested': list(self.symbols.keys()),
            'final_metrics': {
                'total_trades': final_metrics['total_trades'],
                'win_rate': final_metrics['win_rate'],
                'profit_factor': final_metrics['profit_factor'],
                'sharpe_ratio': final_metrics['sharpe_ratio'],
                'max_drawdown': final_metrics['max_drawdown'],
                'total_return': final_metrics['total_return'],
                'total_pnl': final_metrics['total_pnl']
            },
            'evaluation_score': score,
            'periods_detail': [
                {
                    'name': r['period']['name'],
                    'trades': r['metrics']['total_trades'],
                    'return': r['metrics']['total_return']
                }
                for r in period_results
            ]
        }
        
        with open('backtesting_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("\n💾 Resultados guardados en 'backtesting_results.json'")

def main():
    """
    Función principal
    """
    print("🚀 INICIANDO BACKTESTING COMPREHENSIVO")
    print("="*80)
    
    backtester = ComprehensiveBacktesting(initial_capital=10000)
    results = backtester.run_comprehensive_backtest()
    
    print("\n" + "="*80)
    print("✅ BACKTESTING COMPLETADO")
    print("="*80)
    
    return results

if __name__ == "__main__":
    results = main()