#!/usr/bin/env python3
"""
Test del Sistema de Scoring Empírico V2.0
"""

from backtesting_integration import BacktestingIntegrado

def main():
    """Test del nuevo sistema empírico"""
    
    print('🚀 TESTING SISTEMA EMPÍRICO V2.0')
    print('='*70)
    
    # Configurar sistema con scoring empírico
    backtest = BacktestingIntegrado(capital_inicial=10000)
    
    print(f'📊 Configuración:')
    print(f'• Score mínimo: {backtest.config["min_score"]} (empírico)')
    print(f'• Sistema: Scoring basado en evidencia empírica')
    print(f'• RSI: 60% del score')
    print(f'• Price Action: 20%')
    print(f'• Momentum: 15%')
    print(f'• Risk Structure: 5%')
    print(f'• Penalizaciones por volumen alto y MACD contraproducente')
    print('='*70)
    
    # Ejecutar backtesting
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    
    def progress(msg, pct):
        print(f'📈 {msg}')
    
    trades = backtest.run_backtest(
        tickers=tickers,
        periods_days=30,
        progress_callback=progress
    )
    
    if trades:
        results = backtest.analyze_results(trades)
        
        print(f'\n📊 RESULTADOS SISTEMA EMPÍRICO V2.0:')
        print('='*70)
        print(f'• Total Trades: {results["total_trades"]}')
        print(f'• Win Rate: {results["win_rate"]:.1f}%')
        print(f'• Profit Factor: {results["profit_factor"]:.2f}')
        print(f'• Score Promedio: {results["avg_score"]:.1f}/10')
        print(f'• R:R Promedio: 1:{results["avg_rr"]:.1f}')
        print(f'• Rating: {results["rating"]}')
        
        # Comparar con versión anterior
        if results["win_rate"] > 52.0:
            improvement = results["win_rate"] - 52.0
            print(f'\n✅ MEJORA: +{improvement:.1f}% win rate vs sistema anterior')
        else:
            decline = 52.0 - results["win_rate"]
            print(f'\n⚠️ DECLINE: -{decline:.1f}% win rate vs sistema anterior')
        
        if results["profit_factor"] > 1.07:
            pf_improvement = results["profit_factor"] - 1.07
            print(f'✅ MEJORA: +{pf_improvement:.2f} profit factor vs sistema anterior')
        else:
            pf_decline = 1.07 - results["profit_factor"]
            print(f'⚠️ DECLINE: -{pf_decline:.2f} profit factor vs sistema anterior')
        
        # Análisis de leverage
        leverage_dist = {}
        for trade in trades:
            lev = trade['leverage']
            leverage_dist[lev] = leverage_dist.get(lev, 0) + 1
        
        print(f'\n🎯 DISTRIBUCIÓN DE LEVERAGE EMPÍRICO:')
        for lev in sorted(leverage_dist.keys()):
            count = leverage_dist[lev]
            pct = (count / len(trades)) * 100
            print(f'• {lev}x: {count} trades ({pct:.1f}%)')
        
        # Métricas financieras
        profit_total = sum(t['profit_usd'] for t in trades)
        capital_usado = sum(t['capital_usado'] for t in trades)
        roi = (profit_total / 10000) * 100
        
        print(f'\n💰 MÉTRICAS FINANCIERAS:')
        print(f'• Capital Usado: ${capital_usado:,.0f}')
        print(f'• Ganancia Total: ${profit_total:+.2f}')
        print(f'• ROI: {roi:+.2f}%')
        
        # Análisis por exit reason
        exit_reasons = {}
        for trade in trades:
            reason = trade['exit_reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        print(f'\n🚪 SALIDAS:')
        for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(trades)) * 100
            print(f'• {reason}: {count} ({pct:.1f}%)')
        
        # Evaluación final
        print(f'\n💡 EVALUACIÓN SISTEMA EMPÍRICO V2.0:')
        if results["win_rate"] >= 60 and results["profit_factor"] >= 1.3:
            print('🌟 EXCELENTE: Sistema empírico funciona bien')
        elif results["win_rate"] >= 55 and results["profit_factor"] >= 1.2:
            print('✅ BUENO: Sistema empírico es prometedor')
        elif results["win_rate"] >= 50:
            print('📊 MODERADO: Sistema empírico mejora algo')
        else:
            print('⚠️ INSUFICIENTE: Sistema empírico necesita ajustes')
        
    else:
        print('\n❌ No se generaron trades con el sistema empírico')
        print('💡 Puede indicar que el score mínimo 6.0 es demasiado estricto')

if __name__ == "__main__":
    main()