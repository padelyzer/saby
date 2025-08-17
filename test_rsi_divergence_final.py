#!/usr/bin/env python3
"""
Test Final del Sistema con RSI Divergence Optimizado
"""

from backtesting_integration import BacktestingIntegrado

def main():
    """Test del sistema con RSI Divergence integrado"""
    
    print('📊 SISTEMA FINAL: RSI DIVERGENCE OPTIMIZADO')
    print('='*80)
    print('CONFIGURACIÓN:')
    print('• RSI Score: 45% (base confiable)')
    print('• Price Action: 20% (aumentado)')
    print('• Momentum: 10% (reducido)')
    print('• Risk Structure: 5% (mantenido)')
    print('• RSI DIVERGENCE: 20% (NUEVO - optimizado)')
    print('• Liquidez: DESHABILITADA (era contraproducente)')
    print('='*80)
    
    # Configurar sistema
    backtest = BacktestingIntegrado(capital_inicial=10000)
    
    # Ejecutar backtesting
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    
    def progress(msg, pct):
        print(f'📈 {msg}')
    
    print('🚀 Ejecutando backtesting con RSI Divergence...')
    trades = backtest.run_backtest(
        tickers=tickers,
        periods_days=30,
        progress_callback=progress
    )
    
    if trades:
        results = backtest.analyze_results(trades)
        
        print(f'\n🎯 RESULTADOS CON RSI DIVERGENCE:')
        print('='*80)
        print(f'• Total Trades: {results["total_trades"]}')
        print(f'• Win Rate: {results["win_rate"]:.1f}%')
        print(f'• Profit Factor: {results["profit_factor"]:.2f}')
        print(f'• Score Promedio: {results["avg_score"]:.1f}/10')
        print(f'• R:R Promedio: 1:{results["avg_rr"]:.1f}')
        print(f'• Rating: {results["rating"]}')
        
        # Evaluar progreso hacia objetivo 65%
        print(f'\n🏆 EVALUACIÓN DEL OBJETIVO 65%+ WIN RATE:')
        print('-'*60)
        
        if results["win_rate"] >= 65:
            print('🌟 ¡OBJETIVO ALCANZADO!')
            print(f'✅ Win Rate: {results["win_rate"]:.1f}% (≥65%)')
            if results["profit_factor"] >= 1.5:
                print(f'✅ Profit Factor: {results["profit_factor"]:.2f} (≥1.5 - EXCELENTE)')
                print('🚀 SISTEMA LISTO PARA TRADING EN VIVO')
            else:
                print(f'📊 Profit Factor: {results["profit_factor"]:.2f} (ACEPTABLE)')
                print('✅ SISTEMA APTO PARA TRADING')
        elif results["win_rate"] >= 60:
            gap = 65 - results["win_rate"]
            print(f'📈 MUY CERCA del objetivo (faltan {gap:.1f}%)')
            print('✅ PROGRESO EXCELENTE - Sistema muy prometedor')
        elif results["win_rate"] >= 55:
            gap = 65 - results["win_rate"]
            print(f'📊 PROGRESO BUENO (faltan {gap:.1f}%)')
            print('✅ Sistema en la dirección correcta')
        else:
            gap = 65 - results["win_rate"]
            print(f'⚠️ Aún faltan {gap:.1f}% para el objetivo')
        
        # Progresión histórica completa
        print(f'\n📈 EVOLUCIÓN COMPLETA DEL SISTEMA:')
        print('-'*60)
        print(f'1. Sistema Original:           52.0% WR, 1.07 PF')
        print(f'2. + Empírico V2:             56.5% WR, 1.37 PF (+4.5%)')
        print(f'3. + Liquidez (falló):        31.8% WR, 0.50 PF (-24.7%)')
        print(f'4. + Over-optimización:       36.0% WR, 0.62 PF (falló)')
        print(f'5. + RSI Divergence:          {results["win_rate"]:.1f}% WR, {results["profit_factor"]:.2f} PF', end='')
        
        improvement_from_original = results["win_rate"] - 52.0
        if improvement_from_original > 0:
            print(f' (+{improvement_from_original:.1f}%)')
        else:
            print(f' ({improvement_from_original:.1f}%)')
        
        # Análisis de leverage performance
        leverage_analysis = {}
        for trade in trades:
            lev = trade['leverage']
            if lev not in leverage_analysis:
                leverage_analysis[lev] = {'total': 0, 'wins': 0, 'profits': []}
            leverage_analysis[lev]['total'] += 1
            leverage_analysis[lev]['profits'].append(trade['profit_pct'])
            if trade['profit_pct'] > 0:
                leverage_analysis[lev]['wins'] += 1
        
        print(f'\n🎯 PERFORMANCE POR LEVERAGE:')
        for lev in sorted(leverage_analysis.keys()):
            data = leverage_analysis[lev]
            wr = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            avg_profit = sum(data['profits']) / len(data['profits']) if data['profits'] else 0
            count = data['total']
            pct = (count / len(trades)) * 100
            
            print(f'• {lev}x: {count} trades ({pct:.1f}%), WR: {wr:.1f}%, Avg: {avg_profit:+.2f}%', end='')
            
            if wr >= 70:
                print(' 🌟 EXCELENTE')
            elif wr >= 60:
                print(' ✅ BUENO')
            elif wr >= 50:
                print(' 📊 ACEPTABLE')
            else:
                print(' ⚠️ MEJORABLE')
        
        # Análisis de componentes RSI Divergence
        print(f'\n🔬 ANÁLISIS RSI DIVERGENCE:')
        
        # Simular estadísticas de divergencias
        trades_with_divergence = [t for t in trades if hasattr(t, 'score_details')]
        if trades_with_divergence:
            print(f'• Trades analizados para divergencias: {len(trades)}')
            # Aquí se podrían mostrar estadísticas más detalladas si estuvieran disponibles
        
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
        
        if results["win_rate"] >= 65:
            print('🌟 SISTEMA APROBADO PARA TRADING')
            print('📋 Plan de implementación:')
            print('  1. Usar RSI Divergence como confirmación principal')
            print('  2. Empezar con capital pequeño para validar')
            print('  3. Monitorear divergencias manualmente')
            print('  4. Escalar gradualmente si mantiene performance')
            
        elif results["win_rate"] >= 60:
            print('📊 SISTEMA MUY PROMETEDOR')
            print('🔧 Pasos siguientes:')
            print('  1. Paper trading por 2 semanas')
            print('  2. Refinar detección de divergencias')
            print('  3. Considerar ajustes menores en pesos')
            print('  4. Implementar con capital mínimo')
            
        elif results["win_rate"] >= 55:
            print('📈 PROGRESO SIGNIFICATIVO')
            print('🔧 Mejoras sugeridas:')
            print('  1. Optimizar parámetros de divergencia')
            print('  2. Añadir filtros adicionales de calidad')
            print('  3. Considerar combinación con otro indicador')
            
        else:
            print('⚠️ SISTEMA NECESITA MÁS TRABAJO')
            print('📝 Próximos pasos:')
            print('  1. Revisar implementación de divergencias')
            print('  2. Probar otros períodos de lookback')
            print('  3. Considerar enfoques alternativos')
        
        # Status de objetivo
        if results["win_rate"] >= 65:
            print(f'\n🎯 OBJETIVO 65%+ WIN RATE: ✅ ALCANZADO')
        else:
            remaining = 65 - results["win_rate"]
            print(f'\n🎯 OBJETIVO 65%+ WIN RATE: ⏳ Faltan {remaining:.1f}%')
        
    else:
        print('\n❌ No se generaron trades')
        print('Posibles causas:')
        print('• Filtros de divergencia muy estrictos')
        print('• Período de análisis insuficiente')
        print('• Problemas en detección de divergencias')

if __name__ == "__main__":
    main()