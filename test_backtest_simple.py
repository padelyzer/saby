#!/usr/bin/env python3
"""
Test simplificado del sistema de backtesting
"""

from backtesting_avanzado import BacktestEngine
from datetime import datetime, timedelta

print("""
╔════════════════════════════════════════════════════════════════╗
║          EJECUTANDO BACKTESTING AVANZADO                        ║
╚════════════════════════════════════════════════════════════════╝
""")

# Configuración simplificada
tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD']  # Solo 3 tickers
strategies = ['Momentum', 'Mean Reversion']  # Solo 2 estrategias
capital_inicial = 10000

# Período más corto para prueba rápida
end_date = datetime.now()
start_date = end_date - timedelta(days=30)  # Solo 30 días

print(f"📊 Configuración:")
print(f"• Capital: ${capital_inicial:,}")
print(f"• Tickers: {tickers}")
print(f"• Estrategias: {strategies}")
print(f"• Período: {start_date.date()} a {end_date.date()}")
print("="*60)

# Ejecutar backtest
engine = BacktestEngine(initial_capital=capital_inicial)

try:
    results = engine.run_backtest(
        tickers=tickers,
        strategies=strategies,
        start_date=start_date,
        end_date=end_date,
        position_size=0.15,  # 15% por trade (más agresivo)
        max_positions=4      # Máximo 4 posiciones
    )
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("📊 RESULTADOS DEL BACKTESTING")
    print("="*60)
    
    # Métricas principales
    final_capital = results['equity_curve'][-1]['capital'] if results['equity_curve'] else capital_inicial
    
    print(f"\n💰 CAPITAL:")
    print(f"• Inicial: ${capital_inicial:,.2f}")
    print(f"• Final: ${final_capital:,.2f}")
    print(f"• Retorno: {results['total_return']:+.2f}%")
    
    print(f"\n📈 MÉTRICAS:")
    print(f"• Total Trades: {results['total_trades']}")
    print(f"• Win Rate: {results['win_rate']:.1f}%")
    print(f"• Profit Factor: {results['profit_factor']:.2f}")
    print(f"• Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"• Max Drawdown: -{results['max_drawdown']:.2f}%")
    
    print(f"\n🎯 TRADES:")
    print(f"• Promedio Ganancia: {results['avg_win']:+.2f}%")
    print(f"• Promedio Pérdida: {results['avg_loss']:+.2f}%")
    print(f"• Mejor Trade: {results['best_trade']:+.2f}%")
    print(f"• Peor Trade: {results['worst_trade']:+.2f}%")
    
    # Performance por estrategia
    if results['trades_by_strategy']:
        print(f"\n🎯 PERFORMANCE POR ESTRATEGIA:")
        for strategy, stats in results['trades_by_strategy'].items():
            print(f"\n{strategy}:")
            print(f"  • Trades: {stats['total']}")
            print(f"  • Win Rate: {stats['win_rate']:.1f}%")
            print(f"  • PnL: ${stats['total_pnl']:+,.2f}")
    
    # Performance por ticker
    if results['performance_by_ticker']:
        print(f"\n📊 PERFORMANCE POR TICKER:")
        sorted_tickers = sorted(results['performance_by_ticker'].items(), 
                              key=lambda x: x[1]['total_pnl'], 
                              reverse=True)
        
        for ticker, stats in sorted_tickers:
            win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{ticker}: ${stats['total_pnl']:+,.2f} ({stats['total']} trades, {win_rate:.0f}% WR)")
    
    # Análisis de calidad
    print(f"\n✨ ANÁLISIS DE CALIDAD:")
    
    if results['total_return'] > 20:
        print("🌟 EXCELENTE: Retorno superior al 20%")
    elif results['total_return'] > 10:
        print("✅ BUENO: Retorno entre 10-20%")
    elif results['total_return'] > 5:
        print("⚠️ REGULAR: Retorno entre 5-10%")
    else:
        print("❌ BAJO: Retorno menor al 5%")
    
    if results['win_rate'] > 60:
        print("🌟 EXCELENTE: Win Rate superior al 60%")
    elif results['win_rate'] > 50:
        print("✅ BUENO: Win Rate entre 50-60%")
    else:
        print("⚠️ MEJORABLE: Win Rate menor al 50%")
    
    if results['profit_factor'] > 2:
        print("🌟 EXCELENTE: Profit Factor superior a 2")
    elif results['profit_factor'] > 1.5:
        print("✅ BUENO: Profit Factor entre 1.5-2")
    else:
        print("⚠️ MEJORABLE: Profit Factor menor a 1.5")
    
    if results['max_drawdown'] < 10:
        print("🌟 EXCELENTE: Drawdown menor al 10%")
    elif results['max_drawdown'] < 20:
        print("✅ BUENO: Drawdown entre 10-20%")
    else:
        print("⚠️ RIESGOSO: Drawdown mayor al 20%")
    
    print("\n" + "="*60)
    print("✅ BACKTESTING COMPLETADO EXITOSAMENTE")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Error en backtesting: {e}")
    import traceback
    traceback.print_exc()