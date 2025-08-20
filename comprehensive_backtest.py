#!/usr/bin/env python3
"""
Backtesting completo de todos los pares con análisis detallado
"""

import json
import requests
import pandas as pd
from datetime import datetime
from tabulate import tabulate
import time

# Configuración de pares y sus estrategias
PAIRS_CONFIG = {
    'BNBUSDT': {'name': 'BNB', 'strategy': 'mean_reversion'},
    'SOLUSDT': {'name': 'SOL', 'strategy': 'mean_reversion'},  
    'XRPUSDT': {'name': 'XRP', 'strategy': 'mean_reversion'},
    'ADAUSDT': {'name': 'ADA', 'strategy': 'trend_following'},
    'AVAXUSDT': {'name': 'AVAX', 'strategy': 'avax_optimized'},
    'LINKUSDT': {'name': 'LINK', 'strategy': 'trend_following'},
    'DOTUSDT': {'name': 'DOT', 'strategy': 'mean_reversion'},
    'DOGEUSDT': {'name': 'DOGE', 'strategy': 'trend_following'}
}

def run_backtest(symbol, periods=[7, 15, 30, 90]):
    """Ejecuta backtest para un símbolo en múltiples períodos"""
    results = {}
    
    for period in periods:
        try:
            response = requests.post(
                f'http://localhost:8000/api/backtest/{symbol}',
                json={'period_days': period, 'risk_percent': 2.0},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Calcular métricas adicionales
                signals = data.get('signals', [])
                winners = sum(1 for s in signals if s.get('success', False))
                losers = len(signals) - winners
                
                # Calcular P&L promedio
                if signals:
                    avg_win = sum(s.get('profit_loss', 0) for s in signals if s.get('success', False)) / max(winners, 1)
                    avg_loss = sum(s.get('profit_loss', 0) for s in signals if not s.get('success', False)) / max(losers, 1)
                else:
                    avg_win = 0
                    avg_loss = 0
                
                results[period] = {
                    'total_signals': len(signals),
                    'winners': winners,
                    'losers': losers,
                    'win_rate': (winners / len(signals) * 100) if signals else 0,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'total_pnl': sum(s.get('profit_loss', 0) for s in signals),
                    'strategy': data.get('strategy_used', 'N/A')
                }
            else:
                results[period] = {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            results[period] = {'error': str(e)}
            
        time.sleep(0.5)  # Evitar sobrecarga
    
    return results

def analyze_performance(backtest_results):
    """Analiza el desempeño general de cada par"""
    analysis = {}
    
    for symbol, periods_data in backtest_results.items():
        total_signals = 0
        total_winners = 0
        total_pnl = 0
        periods_count = 0
        
        for period, data in periods_data.items():
            if 'error' not in data:
                total_signals += data['total_signals']
                total_winners += data['winners']
                total_pnl += data['total_pnl']
                periods_count += 1
        
        if total_signals > 0:
            overall_win_rate = (total_winners / total_signals) * 100
        else:
            overall_win_rate = 0
            
        analysis[symbol] = {
            'total_signals_all_periods': total_signals,
            'overall_win_rate': overall_win_rate,
            'total_pnl_all_periods': total_pnl,
            'avg_signals_per_period': total_signals / max(periods_count, 1),
            'strategy': PAIRS_CONFIG[symbol]['strategy'],
            'rating': get_performance_rating(overall_win_rate, total_signals)
        }
    
    return analysis

def get_performance_rating(win_rate, total_signals):
    """Califica el desempeño del par"""
    if total_signals == 0:
        return "⚪ SIN DATOS"
    elif win_rate >= 65:
        return "🟢 EXCELENTE"
    elif win_rate >= 55:
        return "🟡 BUENO"
    elif win_rate >= 45:
        return "🟠 REGULAR"
    else:
        return "🔴 DEFICIENTE"

def print_results(backtest_results, analysis):
    """Imprime resultados formateados"""
    
    print("\n" + "="*100)
    print(" BACKTESTING COMPLETO - TODOS LOS PARES ".center(100, "="))
    print("="*100)
    
    # Resultados por período
    for symbol in PAIRS_CONFIG.keys():
        print(f"\n📊 {PAIRS_CONFIG[symbol]['name']} ({symbol}) - Estrategia: {PAIRS_CONFIG[symbol]['strategy']}")
        print("-" * 60)
        
        table_data = []
        for period in [7, 15, 30, 90]:
            if period in backtest_results[symbol]:
                data = backtest_results[symbol][period]
                if 'error' not in data:
                    table_data.append([
                        f"{period} días",
                        data['total_signals'],
                        data['winners'],
                        data['losers'],
                        f"{data['win_rate']:.1f}%",
                        f"{data['avg_win']:.2f}%",
                        f"{data['avg_loss']:.2f}%",
                        f"{data['total_pnl']:.2f}%"
                    ])
                else:
                    table_data.append([f"{period} días", "ERROR", "-", "-", "-", "-", "-", "-"])
        
        headers = ["Período", "Señales", "Ganadoras", "Perdedoras", "Win Rate", "Avg Win", "Avg Loss", "P&L Total"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Resumen consolidado
    print("\n" + "="*100)
    print(" ANÁLISIS CONSOLIDADO ".center(100, "="))
    print("="*100)
    
    summary_data = []
    for symbol, data in analysis.items():
        summary_data.append([
            PAIRS_CONFIG[symbol]['name'],
            data['strategy'],
            data['total_signals_all_periods'],
            f"{data['overall_win_rate']:.1f}%",
            f"{data['total_pnl_all_periods']:.2f}%",
            f"{data['avg_signals_per_period']:.1f}",
            data['rating']
        ])
    
    # Ordenar por win rate
    summary_data.sort(key=lambda x: float(x[3].rstrip('%')), reverse=True)
    
    headers = ["Par", "Estrategia", "Total Señales", "Win Rate", "P&L Total", "Señales/Período", "Rating"]
    print(tabulate(summary_data, headers=headers, tablefmt="grid"))
    
    # Estadísticas generales
    print("\n📈 ESTADÍSTICAS GENERALES")
    print("-" * 50)
    
    total_signals = sum(data['total_signals_all_periods'] for data in analysis.values())
    avg_win_rate = sum(data['overall_win_rate'] for data in analysis.values()) / len(analysis)
    total_pnl = sum(data['total_pnl_all_periods'] for data in analysis.values())
    
    print(f"Total de señales generadas: {total_signals}")
    print(f"Win rate promedio del sistema: {avg_win_rate:.1f}%")
    print(f"P&L total acumulado: {total_pnl:.2f}%")
    
    # Mejores y peores
    sorted_pairs = sorted(analysis.items(), key=lambda x: x[1]['overall_win_rate'], reverse=True)
    
    print(f"\n🏆 Mejor desempeño: {PAIRS_CONFIG[sorted_pairs[0][0]]['name']} ({sorted_pairs[0][1]['overall_win_rate']:.1f}% WR)")
    print(f"⚠️  Peor desempeño: {PAIRS_CONFIG[sorted_pairs[-1][0]]['name']} ({sorted_pairs[-1][1]['overall_win_rate']:.1f}% WR)")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES")
    print("-" * 50)
    
    for symbol, data in analysis.items():
        if data['overall_win_rate'] < 50 and data['total_signals_all_periods'] > 0:
            print(f"⚠️ {PAIRS_CONFIG[symbol]['name']}: Requiere optimización (WR: {data['overall_win_rate']:.1f}%)")
        elif data['total_signals_all_periods'] == 0:
            print(f"🔍 {PAIRS_CONFIG[symbol]['name']}: Sin señales - revisar parámetros")
        elif data['overall_win_rate'] >= 65:
            print(f"✅ {PAIRS_CONFIG[symbol]['name']}: Excelente desempeño - mantener configuración")

def main():
    print("\n🚀 Iniciando backtesting completo...")
    print("⏰ Esto puede tomar unos minutos...\n")
    
    # Ejecutar backtests
    all_results = {}
    
    for symbol in PAIRS_CONFIG.keys():
        print(f"📊 Procesando {PAIRS_CONFIG[symbol]['name']} ({symbol})...")
        all_results[symbol] = run_backtest(symbol)
    
    # Analizar resultados
    analysis = analyze_performance(all_results)
    
    # Mostrar resultados
    print_results(all_results, analysis)
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'results': all_results,
            'analysis': analysis
        }, f, indent=2)
    
    print(f"\n💾 Resultados guardados en: {filename}")
    print("\n✅ Backtesting completado!")

if __name__ == "__main__":
    main()
