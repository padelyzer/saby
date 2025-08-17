#!/usr/bin/env python3
"""
Test de Integración: Sistema Empírico + Validación de Liquidez
"""

from backtesting_integration import BacktestingIntegrado

def main():
    """Test del sistema con validación de liquidez"""
    
    print('💧 SISTEMA EMPÍRICO V2.0 + VALIDACIÓN DE LIQUIDEZ')
    print('='*80)
    
    # Configurar sistema
    backtest = BacktestingIntegrado(capital_inicial=10000)
    
    print('📊 COMPONENTES DEL SISTEMA:')
    print('• RSI Score: 51% (empíricamente confiable)')
    print('• Price Action: 17% (patrones de velas)')
    print('• Momentum: 12% (sin volumen alto contraproducente)')
    print('• Risk Structure: 5% (volatilidad controlada)')
    print('• LIQUIDEZ VALIDATION: 15% (NUEVO)')
    print('  - Patrones de volumen (30%)')
    print('  - Impacto de precio (25%)')
    print('  - Coherencia direccional (30%)')
    print('  - Consistencia temporal (15%)')
    print('='*80)
    
    # Ejecutar backtesting
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    
    def progress(msg, pct):
        print(f'📈 {msg}')
    
    print('🔍 Ejecutando backtesting con validación de liquidez...')
    trades = backtest.run_backtest(
        tickers=tickers,
        periods_days=30,
        progress_callback=progress
    )
    
    if trades:
        results = backtest.analyze_results(trades)
        
        print(f'\n📊 RESULTADOS CON VALIDACIÓN DE LIQUIDEZ:')
        print('='*80)
        print(f'• Total Trades: {results["total_trades"]}')
        print(f'• Win Rate: {results["win_rate"]:.1f}%')
        print(f'• Profit Factor: {results["profit_factor"]:.2f}')
        print(f'• Score Promedio: {results["avg_score"]:.1f}/10')
        print(f'• R:R Promedio: 1:{results["avg_rr"]:.1f}')
        print(f'• Rating: {results["rating"]}')
        
        # Comparar con versiones anteriores
        print(f'\n📈 COMPARACIÓN CON VERSIONES ANTERIORES:')
        print('-'*50)
        
        # Sistema original (diagnóstico)
        print(f'Sistema Original:     52.0% WR, 1.07 PF')
        print(f'Sistema Empírico:     56.5% WR, 1.37 PF')
        print(f'+ Validación Liquidez: {results["win_rate"]:.1f}% WR, {results["profit_factor"]:.2f} PF')
        
        if results["win_rate"] > 56.5:
            improvement = results["win_rate"] - 56.5
            print(f'✅ MEJORA LIQUIDEZ: +{improvement:.1f}% win rate')
        else:
            decline = 56.5 - results["win_rate"]
            print(f'⚠️ IMPACTO NEGATIVO: -{decline:.1f}% win rate')
        
        if results["profit_factor"] > 1.37:
            pf_improvement = results["profit_factor"] - 1.37
            print(f'✅ MEJORA PF: +{pf_improvement:.2f}')
        else:
            pf_decline = 1.37 - results["profit_factor"]
            print(f'⚠️ DECLINE PF: -{pf_decline:.2f}')
        
        # Análisis detallado de trades
        print(f'\n🔬 ANÁLISIS DETALLADO DE LIQUIDEZ:')
        print('-'*50)
        
        # Simular análisis de componentes de liquidez
        from scoring_empirico_v2 import ScoringEmpiricoV2
        scoring_system = ScoringEmpiricoV2()
        
        high_score_trades = [t for t in trades if t['score'] >= 7.5]
        low_score_trades = [t for t in trades if t['score'] < 6.5]
        
        if high_score_trades:
            high_score_winners = [t for t in high_score_trades if t['profit_pct'] > 0]
            high_score_wr = len(high_score_winners) / len(high_score_trades) * 100
            print(f'Trades Score Alto (≥7.5): {len(high_score_trades)}, WR: {high_score_wr:.1f}%')
        
        if low_score_trades:
            low_score_winners = [t for t in low_score_trades if t['profit_pct'] > 0]
            low_score_wr = len(low_score_winners) / len(low_score_trades) * 100
            print(f'Trades Score Bajo (<6.5): {len(low_score_trades)}, WR: {low_score_wr:.1f}%')
        
        # Distribución de leverage
        leverage_dist = {}
        leverage_wr = {}
        
        for trade in trades:
            lev = trade['leverage']
            leverage_dist[lev] = leverage_dist.get(lev, 0) + 1
            
            if lev not in leverage_wr:
                leverage_wr[lev] = {'total': 0, 'wins': 0}
            leverage_wr[lev]['total'] += 1
            if trade['profit_pct'] > 0:
                leverage_wr[lev]['wins'] += 1
        
        print(f'\n🎯 PERFORMANCE POR LEVERAGE:')
        for lev in sorted(leverage_dist.keys()):
            count = leverage_dist[lev]
            wr = (leverage_wr[lev]['wins'] / leverage_wr[lev]['total'] * 100) if leverage_wr[lev]['total'] > 0 else 0
            pct = (count / len(trades)) * 100
            print(f'• {lev}x: {count} trades ({pct:.1f}%), WR: {wr:.1f}%')
        
        # Métricas financieras
        profit_total = sum(t['profit_usd'] for t in trades)
        capital_usado = sum(t['capital_usado'] for t in trades)
        roi = (profit_total / 10000) * 100
        
        print(f'\n💰 MÉTRICAS FINANCIERAS:')
        print(f'• Capital Usado: ${capital_usado:,.0f}')
        print(f'• Ganancia Total: ${profit_total:+.2f}')
        print(f'• ROI: {roi:+.2f}%')
        
        # Análisis de salidas
        exit_reasons = {}
        for trade in trades:
            reason = trade['exit_reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        print(f'\n🚪 DISTRIBUCIÓN DE SALIDAS:')
        for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(trades)) * 100
            print(f'• {reason}: {count} ({pct:.1f}%)')
        
        # Evaluación del objetivo 65%+
        print(f'\n🎯 EVALUACIÓN DEL OBJETIVO 65%+ WIN RATE:')
        print('-'*50)
        
        if results["win_rate"] >= 65:
            print('🌟 ¡OBJETIVO ALCANZADO! Sistema listo para trading')
            print(f'✅ Win Rate: {results["win_rate"]:.1f}% (≥65%)')
            print(f'✅ Profit Factor: {results["profit_factor"]:.2f}')
        elif results["win_rate"] >= 60:
            gap = 65 - results["win_rate"]
            print(f'📊 MUY CERCA del objetivo (faltan {gap:.1f}%)')
            print('💡 Sugerencias para alcanzar 65%:')
            print('  • Ajustar threshold de liquidez')
            print('  • Refinar validación de coherencia')
            print('  • Aumentar peso de RSI (más confiable)')
        else:
            gap = 65 - results["win_rate"]
            print(f'⚠️ Aún faltan {gap:.1f}% para el objetivo')
            print('🔧 Acciones requeridas:')
            print('  • Revisar componentes de liquidez')
            print('  • Ajustar filtros de coherencia')
            print('  • Considerar nuevos indicadores')
        
        # Recomendación final
        print(f'\n💡 EVALUACIÓN FINAL:')
        if results["win_rate"] >= 60 and results["profit_factor"] >= 1.3:
            print('✅ Sistema con LIQUIDEZ es superior')
            print('📊 Recomendación: Usar en trading real con monitoreo')
        elif results["win_rate"] > 56.5:
            print('📈 Validación de liquidez MEJORA el sistema')
            print('🔧 Recomendación: Continuar optimizando')
        else:
            print('❌ Validación de liquidez no mejora suficientemente')
            print('🔍 Recomendación: Revisar implementación o parámetros')
        
    else:
        print('\n❌ No se generaron trades con validación de liquidez')
        print('⚠️ Posibles causas:')
        print('• Filtros de liquidez demasiado estrictos')
        print('• Score mínimo muy alto combinado con liquidez')
        print('• Período de análisis insuficiente')

if __name__ == "__main__":
    main()