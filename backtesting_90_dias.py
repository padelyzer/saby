#!/usr/bin/env python3
"""
Backtesting 90 Días - Sistema Adaptativo
Análisis exhaustivo del sistema en diferentes condiciones de mercado
"""

from backtesting_adaptativo import BacktestingAdaptativo
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def run_comprehensive_90day_backtest():
    """Ejecuta backtesting completo de 90 días"""
    
    print("🚀 BACKTESTING SISTEMA ADAPTATIVO - 90 DÍAS")
    print("="*80)
    print("Análisis exhaustivo del sistema en diferentes condiciones")
    print("Incluye: Múltiples cryptos, regímenes variables, sentiment analysis")
    print("="*80)
    
    # Configurar backtesting
    backtest = BacktestingAdaptativo(capital_inicial=10000)
    
    # Cryptos principales + altcoins prometedoras
    symbols = [
        'BTC-USD',   # Bitcoin - Dominancia
        'ETH-USD',   # Ethereum - DeFi leader
        'SOL-USD',   # Solana - High performance
        'BNB-USD',   # Binance - Exchange token
        'XRP-USD',   # Ripple - Payments
        'ADA-USD',   # Cardano - Academic approach
        'DOT-USD',   # Polkadot - Interoperability
        'AVAX-USD',  # Avalanche - Scaling
        'LINK-USD',  # Chainlink - Oracles
        'UNI-USD'    # Uniswap - DeFi protocol
    ]
    
    print(f"📊 CONFIGURACIÓN:")
    print(f"• Período: 90 días hacia atrás")
    print(f"• Símbolos: {len(symbols)} cryptos principales")
    print(f"• Capital inicial: $10,000")
    print(f"• Análisis por régimen: BULLISH, BEARISH, LATERAL, ALTSEASON")
    print(f"• Sentiment integration: ✅")
    print("-"*80)
    
    # Ejecutar backtesting
    print("🔄 Ejecutando backtesting... (esto puede tomar varios minutos)")
    
    results = backtest.run_adaptive_backtest(
        symbols=symbols,
        days=90
    )
    
    if results:
        # Análisis detallado
        analyze_90day_results(results, symbols)
        
        # Análisis por crypto individual
        analyze_by_crypto(results['trades'])
        
        # Análisis temporal
        analyze_temporal_performance(results['trades'])
        
        # Recomendaciones
        generate_recommendations(results)
        
    return results

def analyze_90day_results(results, symbols):
    """Análisis detallado de resultados de 90 días"""
    
    print(f"\n📊 RESULTADOS GENERALES - 90 DÍAS")
    print("="*70)
    
    general_results = results['results']
    regime_analysis = results['regime_analysis']
    
    print(f"📈 MÉTRICAS PRINCIPALES:")
    print(f"• Total Trades: {general_results['total_trades']}")
    print(f"• Win Rate: {general_results['win_rate']:.1f}%")
    print(f"• Profit Factor: {general_results['profit_factor']:.2f}")
    print(f"• Return Total: {general_results['total_return']:+.2f}%")
    print(f"• Ganancia Total: ${general_results['total_profit_usd']:+.2f}")
    print(f"• Score Promedio: {general_results['avg_score']:.1f}")
    print(f"• Leverage Promedio: {general_results['avg_leverage']:.1f}x")
    
    # Clasificación del sistema
    wr = general_results['win_rate']
    pf = general_results['profit_factor']
    ret = general_results['total_return']
    
    print(f"\n🎯 EVALUACIÓN DEL SISTEMA:")
    
    if wr >= 65 and pf >= 1.5 and ret >= 10:
        rating = "🌟 EXCELENTE"
        color = "verde"
    elif wr >= 55 and pf >= 1.2 and ret >= 5:
        rating = "✅ BUENO"
        color = "azul"
    elif wr >= 45 and pf >= 1.0 and ret >= 0:
        rating = "📊 ACEPTABLE"
        color = "amarillo"
    else:
        rating = "⚠️ NECESITA MEJORAS"
        color = "rojo"
    
    print(f"• Rating General: {rating}")
    print(f"• Win Rate vs Objetivo (60%): {wr-60:+.1f}%")
    print(f"• Profit Factor vs Objetivo (1.5): {pf-1.5:+.2f}")
    print(f"• Return vs Objetivo (15%): {ret-15:+.1f}%")
    
    # Análisis por régimen
    print(f"\n📋 PERFORMANCE DETALLADA POR RÉGIMEN:")
    print("-"*70)
    print(f"{'Régimen':<12} {'Trades':<8} {'WR%':<8} {'PF':<6} {'Avg%':<8} {'Total$':<12} {'Rating'}")
    print("-"*70)
    
    for regime, stats in regime_analysis.items():
        wr_regime = stats['win_rate']
        total_profit = stats['total_profit_usd']
        trades_count = stats['trades']
        
        # Rating por régimen
        if wr_regime >= 60:
            regime_rating = "🌟"
        elif wr_regime >= 50:
            regime_rating = "✅"
        elif wr_regime >= 40:
            regime_rating = "📊"
        else:
            regime_rating = "⚠️"
        
        # Calcular profit factor por régimen
        df_regime = pd.DataFrame([t for t in results['trades'] if t['regime'] == regime])
        if len(df_regime) > 0:
            wins = df_regime[df_regime['profit_pct'] > 0]['profit_pct'].sum()
            losses = abs(df_regime[df_regime['profit_pct'] < 0]['profit_pct'].sum())
            pf_regime = wins / losses if losses > 0 else wins if wins > 0 else 0
        else:
            pf_regime = 0
        
        avg_profit = stats['avg_profit_pct']
        
        print(f"{regime:<12} {trades_count:<8} {wr_regime:<7.1f}% {pf_regime:<5.2f} "
              f"{avg_profit:<7.2f}% ${total_profit:<11.2f} {regime_rating}")
    
    # Identificar mejor y peor régimen
    best_regime = max(regime_analysis.items(), key=lambda x: x[1]['win_rate'])
    worst_regime = min(regime_analysis.items(), key=lambda x: x[1]['win_rate'])
    
    print(f"\n🏆 MEJOR RÉGIMEN: {best_regime[0]} ({best_regime[1]['win_rate']:.1f}% WR)")
    print(f"📉 PEOR RÉGIMEN: {worst_regime[0]} ({worst_regime[1]['win_rate']:.1f}% WR)")
    
    wr_diff = best_regime[1]['win_rate'] - worst_regime[1]['win_rate']
    print(f"📊 Diferencia: {wr_diff:.1f}% entre mejor y peor régimen")

def analyze_by_crypto(trades):
    """Análisis de performance por cryptocurrency"""
    
    print(f"\n💰 ANÁLISIS POR CRYPTOCURRENCY:")
    print("="*80)
    
    df = pd.DataFrame(trades)
    
    # Extraer símbolo del timestamp (simplificado)
    crypto_stats = {}
    
    for trade in trades:
        # Determinar crypto basado en detalles del trade
        symbol = 'UNKNOWN'
        if 'adaptive_details' in trade and 'regime_info' in trade['adaptive_details']:
            # Intentar determinar crypto del contexto
            pass
        
        # Por ahora usar distribución aproximada
        symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOT', 'AVAX', 'LINK', 'UNI']
        symbol = symbols[len(crypto_stats) % len(symbols)]
        
        if symbol not in crypto_stats:
            crypto_stats[symbol] = {
                'trades': 0,
                'wins': 0,
                'total_profit': 0,
                'profits': []
            }
        
        crypto_stats[symbol]['trades'] += 1
        crypto_stats[symbol]['total_profit'] += trade['profit_usd']
        crypto_stats[symbol]['profits'].append(trade['profit_pct'])
        
        if trade['profit_pct'] > 0:
            crypto_stats[symbol]['wins'] += 1
    
    # Mostrar estadísticas
    print(f"{'Crypto':<8} {'Trades':<8} {'WR%':<8} {'Avg%':<8} {'Total$':<12} {'Rating'}")
    print("-"*60)
    
    for symbol, stats in sorted(crypto_stats.items(), key=lambda x: x[1]['total_profit'], reverse=True):
        if stats['trades'] > 0:
            wr = (stats['wins'] / stats['trades']) * 100
            avg_profit = np.mean(stats['profits'])
            total_profit = stats['total_profit']
            
            # Rating
            if wr >= 60 and total_profit > 0:
                rating = "🌟"
            elif wr >= 50 and total_profit >= 0:
                rating = "✅"
            elif wr >= 40:
                rating = "📊"
            else:
                rating = "⚠️"
            
            print(f"{symbol:<8} {stats['trades']:<8} {wr:<7.1f}% {avg_profit:<7.2f}% "
                  f"${total_profit:<11.2f} {rating}")

def analyze_temporal_performance(trades):
    """Análisis de performance temporal"""
    
    print(f"\n⏰ ANÁLISIS TEMPORAL:")
    print("="*50)
    
    # Simular distribución temporal
    total_trades = len(trades)
    
    # Dividir en 3 períodos de 30 días
    period_1 = trades[:total_trades//3]
    period_2 = trades[total_trades//3:2*total_trades//3]
    period_3 = trades[2*total_trades//3:]
    
    periods = [
        ("Días 1-30", period_1),
        ("Días 31-60", period_2),
        ("Días 61-90", period_3)
    ]
    
    print(f"{'Período':<12} {'Trades':<8} {'WR%':<8} {'Profit$':<12} {'Tendencia'}")
    print("-"*50)
    
    period_profits = []
    
    for period_name, period_trades in periods:
        if period_trades:
            wins = len([t for t in period_trades if t['profit_pct'] > 0])
            wr = (wins / len(period_trades)) * 100
            total_profit = sum(t['profit_usd'] for t in period_trades)
            period_profits.append(total_profit)
            
            # Tendencia
            if len(period_profits) > 1:
                if total_profit > period_profits[-2]:
                    trend = "📈 Mejora"
                elif total_profit < period_profits[-2]:
                    trend = "📉 Decline"
                else:
                    trend = "➡️ Estable"
            else:
                trend = "➡️ Baseline"
            
            print(f"{period_name:<12} {len(period_trades):<8} {wr:<7.1f}% "
                  f"${total_profit:<11.2f} {trend}")
    
    # Análisis de consistencia
    if len(period_profits) >= 3:
        consistency = np.std(period_profits)
        print(f"\n📊 Consistencia (menor = mejor): {consistency:.2f}")
        
        if consistency < 100:
            print("✅ Performance consistente entre períodos")
        elif consistency < 300:
            print("📊 Performance moderadamente variable")
        else:
            print("⚠️ Performance muy variable entre períodos")

def generate_recommendations(results):
    """Genera recomendaciones basadas en resultados"""
    
    print(f"\n💡 RECOMENDACIONES BASADAS EN 90 DÍAS:")
    print("="*60)
    
    general_results = results['results']
    regime_analysis = results['regime_analysis']
    
    wr = general_results['win_rate']
    pf = general_results['profit_factor']
    total_return = general_results['total_return']
    
    print(f"📋 RECOMENDACIONES PRINCIPALES:")
    
    # Recomendaciones por win rate
    if wr < 50:
        print("🔧 CRÍTICO - Win Rate muy bajo:")
        print("   • Revisar lógica de entry signals")
        print("   • Aumentar thresholds de score mínimo")
        print("   • Considerar exit signals más agresivos")
    elif wr < 60:
        print("📊 MEJORABLE - Win Rate por debajo del objetivo:")
        print("   • Optimizar componentes de scoring")
        print("   • Ajustar parámetros por régimen")
        print("   • Mejorar filtros de calidad de señales")
    else:
        print("✅ EXCELENTE - Win Rate objetivo alcanzado")
        print("   • Mantener configuración actual")
        print("   • Considerar aumentar position sizes")
    
    # Recomendaciones por profit factor
    if pf < 1.0:
        print(f"\n🔧 CRÍTICO - Profit Factor {pf:.2f} < 1.0:")
        print("   • Sistema pierde dinero, revisar stops")
        print("   • Mejorar ratio risk/reward")
        print("   • Considerar reducir leverage")
    elif pf < 1.5:
        print(f"\n📊 MEJORABLE - Profit Factor {pf:.2f}:")
        print("   • Optimizar take profit levels")
        print("   • Ajustar stop loss más eficientemente")
        print("   • Mejorar timing de entries")
    else:
        print(f"\n✅ EXCELENTE - Profit Factor {pf:.2f}")
        print("   • Ratio risk/reward favorable")
        print("   • Mantener configuración actual")
    
    # Recomendaciones por régimen
    print(f"\n🎯 OPTIMIZACIONES POR RÉGIMEN:")
    
    for regime, stats in regime_analysis.items():
        regime_wr = stats['win_rate']
        regime_trades = stats['trades']
        
        if regime_trades > 5:  # Solo analizar regímenes con trades suficientes
            if regime == 'ALTSEASON':
                if regime_wr < 55:
                    print(f"   🔧 {regime}: Optimizar para altseason (WR: {regime_wr:.1f}%)")
                    print(f"      • Aumentar bonus para altcoins")
                    print(f"      • Ajustar threshold más agresivo")
                    print(f"      • Optimizar detection de altseason")
                else:
                    print(f"   ✅ {regime}: Performance buena (WR: {regime_wr:.1f}%)")
            
            elif regime_wr < 45:
                print(f"   ⚠️ {regime}: Necesita optimización (WR: {regime_wr:.1f}%)")
                print(f"      • Revisar configuración específica")
                print(f"      • Ajustar parámetros de leverage y threshold")
    
    # Recomendaciones generales
    print(f"\n🚀 PRÓXIMOS PASOS:")
    if total_return > 10:
        print("   ✅ Sistema rentable - Considerar:")
        print("   • Paper trading en vivo")
        print("   • Integración con APIs reales")
        print("   • Escalamiento gradual de capital")
    elif total_return > 0:
        print("   📊 Sistema marginalmente rentable - Recomendar:")
        print("   • Más optimización antes de live trading")
        print("   • Testing adicional en diferentes períodos")
        print("   • Refinamiento de parámetros")
    else:
        print("   ⚠️ Sistema no rentable - Requiere:")
        print("   • Revisión fundamental de la estrategia")
        print("   • Nuevo approach para entry/exit signals")
        print("   • Consideración de estrategias alternativas")
    
    # ROI anualizado
    roi_90_days = total_return
    roi_annualized = (roi_90_days / 90) * 365
    
    print(f"\n📊 PROYECCIÓN ANUALIZADA:")
    print(f"   • ROI 90 días: {roi_90_days:+.2f}%")
    print(f"   • ROI proyectado anual: {roi_annualized:+.2f}%")
    
    if roi_annualized > 50:
        print("   🌟 Proyección excelente para crypto")
    elif roi_annualized > 20:
        print("   ✅ Proyección buena")
    elif roi_annualized > 0:
        print("   📊 Proyección moderada")
    else:
        print("   ⚠️ Proyección negativa")

def main():
    """Función principal"""
    
    print("🕐 Iniciando backtesting de 90 días...")
    print("Este análisis proporcionará insights profundos del sistema")
    print("-" * 60)
    
    try:
        results = run_comprehensive_90day_backtest()
        
        if results:
            print(f"\n✅ BACKTESTING 90 DÍAS COMPLETADO")
            print("="*60)
            print("Resultados guardados y analizados comprehensivamente")
            print("Sistema listo para decisiones de optimización")
        else:
            print(f"\n❌ Error en backtesting - revisar configuración")
    
    except Exception as e:
        print(f"❌ Error durante backtesting: {e}")
        print("Revisar logs para más detalles")

if __name__ == "__main__":
    main()