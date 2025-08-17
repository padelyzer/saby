#!/usr/bin/env python3
"""
Demo del impacto del score mínimo 6.5+
"""

from backtesting_integration import BacktestingIntegrado

def main():
    print('🚀 BACKTESTING CON SCORE MÍNIMO 6.5+')
    print('='*60)
    
    # Configurar sistema
    backtest = BacktestingIntegrado(capital_inicial=10000)
    print(f'📊 Score mínimo configurado: {backtest.config["min_score"]}')
    print('⚡ Solo acepta trades con leverage 2x o superior')
    print('='*60)
    
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
        
        print('\n📊 RESULTADOS CON SCORE 6.5+:')
        print('='*60)
        print(f'• Total Trades: {results["total_trades"]}')
        print(f'• Win Rate: {results["win_rate"]:.1f}%')
        print(f'• Profit Factor: {results["profit_factor"]:.2f}')
        print(f'• Score Promedio: {results["avg_score"]:.1f}/10')
        print(f'• R:R Promedio: 1:{results["avg_rr"]:.1f}')
        print(f'• Rating: {results["rating"]}')
        
        # Métricas financieras
        profit_total = sum(t['profit_usd'] for t in trades)
        capital_usado = sum(t['capital_usado'] for t in trades)
        roi = (profit_total / 10000) * 100
        
        print(f'\n💰 MÉTRICAS FINANCIERAS:')
        print(f'• Capital Usado: ${capital_usado:,.0f}')
        print(f'• Ganancia Total: ${profit_total:+.2f}')
        print(f'• ROI Total: {roi:+.2f}%')
        
        # Distribución de leverage
        leverage_dist = {}
        for trade in trades:
            lev = trade['leverage']
            leverage_dist[lev] = leverage_dist.get(lev, 0) + 1
        
        print(f'\n🎯 DISTRIBUCIÓN DE LEVERAGE:')
        for lev in sorted(leverage_dist.keys()):
            count = leverage_dist[lev]
            pct = (count / len(trades)) * 100
            print(f'• {lev}x: {count} trades ({pct:.1f}%)')
        
        # Mejores trades
        trades_sorted = sorted(trades, key=lambda x: x['profit_usd'], reverse=True)
        print(f'\n🏆 TOP 3 TRADES:')
        for i, trade in enumerate(trades_sorted[:3]):
            print(f'{i+1}. {trade["ticker"]} {trade["type"]}: ${trade["profit_usd"]:+.2f} '
                  f'(Score: {trade["score"]:.1f}, {trade["leverage"]}x)')
        
        print(f'\n💡 ANÁLISIS DEL FILTRO 6.5+:')
        trades_2x_plus = [t for t in trades if t['leverage'] >= 2]
        pct_qualified = (len(trades_2x_plus) / len(trades)) * 100 if trades else 0
        
        print(f'• {len(trades_2x_plus)}/{len(trades)} trades califican para 2x+ ({pct_qualified:.0f}%)')
        print(f'• Score promedio asegura calidad superior')
        print(f'• Menor cantidad pero mayor confianza en cada trade')
        
    else:
        print('\n❌ NO SE GENERARON TRADES con score 6.5+')
        print('💡 Esto indica que:')
        print('• El filtro es muy estricto para el período')
        print('• Se necesita ajustar el score mínimo a 6.0 o 5.5')
        print('• O ampliar el período de análisis')
        
        print('\n🔧 RECOMENDACIÓN:')
        print('• Probar con score mínimo 6.0 primero')
        print('• Luego 5.5 si es necesario')
        print('• Mantener calidad pero permitir más trades')

if __name__ == "__main__":
    main()