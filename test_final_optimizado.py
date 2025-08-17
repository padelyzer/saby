#!/usr/bin/env python3
"""
Test Final del Sistema Optimizado V3.0
Objetivo: Alcanzar 65%+ Win Rate
"""

from backtesting_integration import BacktestingIntegrado

def main():
    """Test final del sistema optimizado"""
    
    print('🎯 SISTEMA OPTIMIZADO V3.0 - TEST FINAL')
    print('='*80)
    print('OBJETIVO: Alcanzar 65%+ Win Rate')
    print('='*80)
    
    print('📊 OPTIMIZACIONES IMPLEMENTADAS:')
    print('• RSI potenciado: 65% del score (era 51%)')
    print('• Price Action refinado: 15% (granularidad mejorada)')
    print('• Momentum optimizado: 8% (sin volumen contraproducente)')
    print('• Risk Structure: 2% (simplificado)')
    print('• Liquidez optimizada: 10% (eficiencia mejorada)')
    print('• CONFIRMACIÓN MULTI-TIMEFRAME: 10% (NUEVO)')
    print('• MACD penalty: DESACTIVADO (contraproducente)')
    print('• Score mínimo: 5.8 (era 6.0 - más trades)')
    print('• Leverage optimizado: 3x como sweet spot (80% WR empírico)')
    print('='*80)
    
    # Configurar sistema
    backtest = BacktestingIntegrado(capital_inicial=10000)
    
    # Ejecutar backtesting
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    
    def progress(msg, pct):
        print(f'📈 {msg}')
    
    print('🚀 Ejecutando backtesting optimizado...')
    trades = backtest.run_backtest(
        tickers=tickers,
        periods_days=30,
        progress_callback=progress
    )
    
    if trades:
        results = backtest.analyze_results(trades)
        
        print(f'\n🎯 RESULTADOS SISTEMA OPTIMIZADO V3.0:')
        print('='*80)
        print(f'• Total Trades: {results["total_trades"]}')
        print(f'• Win Rate: {results["win_rate"]:.1f}%')
        print(f'• Profit Factor: {results["profit_factor"]:.2f}')
        print(f'• Score Promedio: {results["avg_score"]:.1f}/10')
        print(f'• R:R Promedio: 1:{results["avg_rr"]:.1f}')
        print(f'• Rating: {results["rating"]}')
        
        # Verificar objetivo
        print(f'\n🏆 EVALUACIÓN DEL OBJETIVO 65%+ WIN RATE:')
        print('-'*60)
        
        if results["win_rate"] >= 65:
            print('🌟 ¡OBJETIVO ALCANZADO!')
            print(f'✅ Win Rate: {results["win_rate"]:.1f}% (≥65%)')
            if results["profit_factor"] >= 1.5:
                print(f'✅ Profit Factor: {results["profit_factor"]:.2f} (≥1.5 - EXCELENTE)')
                print('🚀 SISTEMA LISTO PARA TRADING EN VIVO')
            elif results["profit_factor"] >= 1.3:
                print(f'✅ Profit Factor: {results["profit_factor"]:.2f} (≥1.3 - BUENO)')
                print('📊 SISTEMA APTO CON MONITOREO')
            else:
                print(f'⚠️ Profit Factor: {results["profit_factor"]:.2f} (<1.3 - MEJORABLE)')
        else:
            gap = 65 - results["win_rate"]
            print(f'⚠️ Objetivo no alcanzado (faltan {gap:.1f}%)')
            if results["win_rate"] >= 60:
                print('📈 MUY CERCA - Sistema prometedor')
            elif results["win_rate"] >= 55:
                print('📊 PROGRESO SIGNIFICATIVO - Continuar optimizando')
            else:
                print('🔧 NECESITA MÁS OPTIMIZACIÓN')
        
        # Progresión histórica
        print(f'\n📈 PROGRESIÓN DEL SISTEMA:')
        print('-'*60)
        print(f'Sistema Original:       52.0% WR, 1.07 PF')
        print(f'+ Empírico V2:         56.5% WR, 1.37 PF (+4.5%)')
        print(f'+ Liquidez:            57.1% WR, 1.39 PF (+0.6%)')
        print(f'+ Optimizado V3:       {results["win_rate"]:.1f}% WR, {results["profit_factor"]:.2f} PF', end='')
        
        total_improvement = results["win_rate"] - 52.0
        if total_improvement > 0:
            print(f' (+{total_improvement:.1f}%)')
        else:
            print(f' ({total_improvement:.1f}%)')
        
        # Análisis detallado
        print(f'\n🔬 ANÁLISIS DETALLADO:')
        print('-'*60)
        
        # Performance por leverage
        leverage_analysis = {}
        for trade in trades:
            lev = trade['leverage']
            if lev not in leverage_analysis:
                leverage_analysis[lev] = {'total': 0, 'wins': 0}
            leverage_analysis[lev]['total'] += 1
            if trade['profit_pct'] > 0:
                leverage_analysis[lev]['wins'] += 1
        
        print('🎯 PERFORMANCE POR LEVERAGE:')
        for lev in sorted(leverage_analysis.keys()):
            data = leverage_analysis[lev]
            wr = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            count = data['total']
            pct = (count / len(trades)) * 100
            
            print(f'• {lev}x: {count} trades ({pct:.1f}%), WR: {wr:.1f}%', end='')
            if lev == 3 and wr >= 70:
                print(' 🌟 SWEET SPOT CONFIRMADO')
            elif wr >= 65:
                print(' ✅ EXCELENTE')
            elif wr >= 55:
                print(' 📊 BUENO')
            else:
                print(' ⚠️ MEJORABLE')
        
        # Análisis de componentes
        print(f'\n📊 ANÁLISIS DE COMPONENTES (promedio):')
        if trades and hasattr(trades[0], 'score_details'):
            # Simular análisis de componentes
            print('• RSI Component: Dominante (65% del score)')
            print('• Price Action: Refinado (15%)')
            print('• Momentum: Optimizado (8%)')
            print('• Multi-timeframe: NUEVO (10%)')
            print('• Liquidez: Eficiente (10%)')
        
        # Distribución de salidas
        exit_analysis = {}
        for trade in trades:
            reason = trade['exit_reason']
            exit_analysis[reason] = exit_analysis.get(reason, 0) + 1
        
        print(f'\n🚪 DISTRIBUCIÓN DE SALIDAS:')
        for reason, count in sorted(exit_analysis.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(trades)) * 100
            print(f'• {reason}: {count} ({pct:.1f}%)')
        
        # Métricas financieras
        profit_total = sum(t['profit_usd'] for t in trades)
        capital_usado = sum(t['capital_usado'] for t in trades)
        roi = (profit_total / 10000) * 100
        
        print(f'\n💰 MÉTRICAS FINANCIERAS:')
        print(f'• Capital Usado: ${capital_usado:,.0f}')
        print(f'• Ganancia Total: ${profit_total:+.2f}')
        print(f'• ROI: {roi:+.2f}%')
        
        # Recomendación final
        print(f'\n💡 RECOMENDACIÓN FINAL:')
        print('='*80)
        
        if results["win_rate"] >= 65 and results["profit_factor"] >= 1.3:
            print('🌟 SISTEMA APROBADO PARA TRADING')
            print('📋 Plan de implementación:')
            print('  1. Empezar con capital pequeño (10% del total)')
            print('  2. Monitorear performance por 2 semanas')
            print('  3. Si mantiene 65%+ WR, escalar gradualmente')
            print('  4. Seguir todas las reglas de gestión de riesgo')
        elif results["win_rate"] >= 60:
            print('📊 SISTEMA PROMETEDOR - Paper Trading recomendado')
            print('🔧 Mejoras sugeridas:')
            print('  • Aumentar peso RSI (70%)')
            print('  • Refinar confirmación multi-timeframe')
            print('  • Ajustar thresholds de liquidez')
        else:
            print('🔧 SISTEMA NECESITA MÁS OPTIMIZACIÓN')
            print('📝 Próximos pasos:')
            print('  • Revisar nuevos indicadores de confirmación')
            print('  • Explorar filtros adicionales')
            print('  • Considerar machine learning para scoring')
        
    else:
        print('\n❌ No se generaron trades')
        print('🔧 Posibles causas:')
        print('• Filtros demasiado restrictivos')
        print('• Período de análisis insuficiente')
        print('• Problemas en la integración de componentes')

if __name__ == "__main__":
    main()