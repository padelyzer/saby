#!/usr/bin/env python3
"""
Diagnóstico del Sistema de Scoring
Análisis de por qué trades con alto score fallan
"""

from backtesting_integration import BacktestingIntegrado
import pandas as pd
import numpy as np
from collections import defaultdict

class DiagnosticoScoring:
    """Diagnóstico profundo del sistema de scoring"""
    
    def __init__(self):
        self.backtest = BacktestingIntegrado(capital_inicial=10000)
        
    def analizar_correlacion_score_exito(self):
        """Analiza correlación entre score y éxito real"""
        
        print('🔍 DIAGNÓSTICO SISTEMA DE SCORING')
        print('='*70)
        
        # Ejecutar backtesting con score mínimo bajo para capturar más datos
        original_min_score = self.backtest.config['min_score']
        self.backtest.config['min_score'] = 4.0  # Capturar más trades
        
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
        
        def progress(msg, pct):
            print(f'📊 {msg}')
        
        trades = self.backtest.run_backtest(
            tickers=tickers,
            periods_days=45,  # Más datos
            progress_callback=progress
        )
        
        # Restaurar configuración
        self.backtest.config['min_score'] = original_min_score
        
        if not trades:
            print('❌ No hay suficientes trades para análisis')
            return
        
        print(f'\n📈 DATOS CAPTURADOS: {len(trades)} trades')
        print('='*70)
        
        # Separar ganadores y perdedores
        ganadores = [t for t in trades if t['profit_pct'] > 0]
        perdedores = [t for t in trades if t['profit_pct'] <= 0]
        
        print(f'🟢 Ganadores: {len(ganadores)} ({len(ganadores)/len(trades)*100:.1f}%)')
        print(f'🔴 Perdedores: {len(perdedores)} ({len(perdedores)/len(trades)*100:.1f}%)')
        
        # Análisis por rangos de score
        self.analizar_por_rangos_score(trades)
        
        # Análisis de componentes específicos
        self.analizar_componentes_detallado(trades)
        
        # Análisis de estrategias vs score
        self.analizar_estrategias_vs_score(trades)
        
        # Identificar patrones de fallo
        self.identificar_patrones_fallo(trades)
        
        return trades
    
    def analizar_por_rangos_score(self, trades):
        """Analiza performance por rangos de score"""
        
        print(f'\n📊 ANÁLISIS POR RANGOS DE SCORE')
        print('-'*50)
        
        # Definir rangos
        rangos = [
            (4.0, 5.5, 'Bajo'),
            (5.5, 6.5, 'Medio'),
            (6.5, 7.5, 'Alto'),
            (7.5, 10.0, 'Muy Alto')
        ]
        
        for min_score, max_score, nombre in rangos:
            trades_rango = [t for t in trades if min_score <= t['score'] < max_score]
            
            if not trades_rango:
                continue
                
            ganadores_rango = [t for t in trades_rango if t['profit_pct'] > 0]
            wr_rango = len(ganadores_rango) / len(trades_rango) * 100
            
            avg_profit_ganadores = np.mean([t['profit_pct'] for t in ganadores_rango]) if ganadores_rango else 0
            avg_profit_perdedores = np.mean([t['profit_pct'] for t in trades_rango if t['profit_pct'] <= 0])
            
            profit_factor = abs(avg_profit_ganadores * len(ganadores_rango)) / abs(avg_profit_perdedores * (len(trades_rango) - len(ganadores_rango))) if len(trades_rango) > len(ganadores_rango) else 0
            
            print(f'{nombre} ({min_score}-{max_score}): {len(trades_rango)} trades')
            print(f'  • Win Rate: {wr_rango:.1f}%')
            print(f'  • Avg Win: {avg_profit_ganadores:+.2f}%')
            print(f'  • Avg Loss: {avg_profit_perdedores:+.2f}%')
            print(f'  • Profit Factor: {profit_factor:.2f}')
            print()
    
    def analizar_componentes_detallado(self, trades):
        """Analiza cada componente del score vs performance"""
        
        print(f'🔬 ANÁLISIS DETALLADO DE COMPONENTES')
        print('-'*50)
        
        # Simular cálculo de componentes para trades existentes
        # (Esto requiere re-calcular indicadores, por simplicidad usamos correlaciones)
        
        ganadores = [t for t in trades if t['profit_pct'] > 0]
        perdedores = [t for t in trades if t['profit_pct'] <= 0]
        
        print(f'📊 SCORES PROMEDIO:')
        score_ganadores = np.mean([t['score'] for t in ganadores])
        score_perdedores = np.mean([t['score'] for t in perdedores])
        
        print(f'• Ganadores: {score_ganadores:.2f}/10')
        print(f'• Perdedores: {score_perdedores:.2f}/10')
        print(f'• Diferencia: {score_ganadores - score_perdedores:+.2f}')
        
        if score_ganadores - score_perdedores < 1.0:
            print('⚠️ PROBLEMA: Diferencia de score muy pequeña entre ganadores y perdedores')
            print('💡 El sistema de scoring no discrimina bien')
        
        # Análisis por exit reason
        print(f'\n🚪 ANÁLISIS POR RAZÓN DE SALIDA:')
        exit_reasons = defaultdict(list)
        for trade in trades:
            exit_reasons[trade['exit_reason']].append(trade)
        
        for reason, trades_reason in exit_reasons.items():
            ganadores_reason = [t for t in trades_reason if t['profit_pct'] > 0]
            wr_reason = len(ganadores_reason) / len(trades_reason) * 100
            avg_score_reason = np.mean([t['score'] for t in trades_reason])
            
            print(f'• {reason}: {len(trades_reason)} trades, WR: {wr_reason:.1f}%, Score: {avg_score_reason:.1f}')
    
    def analizar_estrategias_vs_score(self, trades):
        """Analiza performance por estrategia vs score"""
        
        print(f'\n🎯 ANÁLISIS ESTRATEGIAS VS SCORE')
        print('-'*50)
        
        estrategias = defaultdict(list)
        for trade in trades:
            estrategias[trade['strategy']].append(trade)
        
        for estrategia, trades_est in estrategias.items():
            if len(trades_est) < 3:  # Filtrar estrategias con pocos trades
                continue
                
            ganadores_est = [t for t in trades_est if t['profit_pct'] > 0]
            wr_est = len(ganadores_est) / len(trades_est) * 100
            avg_score_est = np.mean([t['score'] for t in trades_est])
            
            print(f'{estrategia}:')
            print(f'  • Trades: {len(trades_est)}')
            print(f'  • Win Rate: {wr_est:.1f}%')
            print(f'  • Score Promedio: {avg_score_est:.1f}/10')
            
            # Analizar si scores altos en esta estrategia correlacionan con éxito
            trades_est_sorted = sorted(trades_est, key=lambda x: x['score'], reverse=True)
            top_tercio = trades_est_sorted[:len(trades_est)//3] if len(trades_est) >= 6 else trades_est_sorted[:2]
            
            if top_tercio:
                ganadores_top = [t for t in top_tercio if t['profit_pct'] > 0]
                wr_top = len(ganadores_top) / len(top_tercio) * 100
                print(f'  • Top scores WR: {wr_top:.1f}%')
                
                if wr_top < wr_est:
                    print(f'  ⚠️ PROBLEMA: Scores altos rinden PEOR que promedio')
            print()
    
    def identificar_patrones_fallo(self, trades):
        """Identifica patrones comunes en trades fallidos con score alto"""
        
        print(f'🔍 PATRONES DE FALLO EN SCORES ALTOS')
        print('-'*50)
        
        # Trades con score alto que fallaron
        trades_alto_score = [t for t in trades if t['score'] >= 7.0]
        fallos_alto_score = [t for t in trades_alto_score if t['profit_pct'] <= 0]
        
        if not fallos_alto_score:
            print('✅ No hay fallos significativos en scores altos')
            return
        
        print(f'📊 Trades score ≥7.0 que fallaron: {len(fallos_alto_score)}/{len(trades_alto_score)}')
        
        # Analizar razones de salida
        exit_reasons_fallos = defaultdict(int)
        for trade in fallos_alto_score:
            exit_reasons_fallos[trade['exit_reason']] += 1
        
        print(f'\n🚪 Razones de fallo más comunes:')
        for reason, count in sorted(exit_reasons_fallos.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(fallos_alto_score) * 100
            print(f'• {reason}: {count} ({pct:.1f}%)')
        
        # Analizar estrategias que fallan más
        estrategias_fallos = defaultdict(int)
        for trade in fallos_alto_score:
            estrategias_fallos[trade['strategy']] += 1
        
        print(f'\n🎯 Estrategias que más fallan con score alto:')
        for estrategia, count in sorted(estrategias_fallos.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(fallos_alto_score) * 100
            print(f'• {estrategia}: {count} ({pct:.1f}%)')
        
        # Analizar leverage vs fallos
        leverage_fallos = defaultdict(int)
        for trade in fallos_alto_score:
            leverage_fallos[trade['leverage']] += 1
        
        print(f'\n⚡ Leverage en trades fallidos de score alto:')
        for leverage, count in sorted(leverage_fallos.items()):
            pct = count / len(fallos_alto_score) * 100
            print(f'• {leverage}x: {count} ({pct:.1f}%)')
    
    def generar_recomendaciones(self, trades):
        """Genera recomendaciones para mejorar el scoring"""
        
        print(f'\n💡 RECOMENDACIONES PARA MEJORAR SCORING')
        print('='*70)
        
        ganadores = [t for t in trades if t['profit_pct'] > 0]
        perdedores = [t for t in trades if t['profit_pct'] <= 0]
        
        # Calcular diferencia real de performance
        score_diff = np.mean([t['score'] for t in ganadores]) - np.mean([t['score'] for t in perdedores])
        
        if score_diff < 0.5:
            print('🚨 CRÍTICO: Score no discrimina entre ganadores y perdedores')
            print('📋 Acciones requeridas:')
            print('1. Revisar completamente la fórmula de scoring')
            print('2. Identificar indicadores que SÍ predicen éxito')
            print('3. Reducir peso de componentes no predictivos')
            print('4. Añadir nuevos componentes más efectivos')
        
        elif score_diff < 1.0:
            print('⚠️ MODERADO: Score discrimina poco')
            print('📋 Mejoras sugeridas:')
            print('1. Ajustar pesos de componentes existentes')
            print('2. Añadir factor de confirmación multi-timeframe')
            print('3. Incluir análisis de momentum más estricto')
        
        else:
            print('✅ Score discrimina razonablemente')
            print('📋 Optimizaciones menores:')
            print('1. Ajustar umbrales de componentes')
            print('2. Refinar cálculo de volatilidad')
        
        # Análisis específico por exit reason
        if 'SL' in [t['exit_reason'] for t in trades]:
            sl_trades = [t for t in trades if t['exit_reason'] == 'SL']
            sl_high_score = [t for t in sl_trades if t['score'] >= 7.0]
            
            if len(sl_high_score) > len(sl_trades) * 0.3:
                print('\n🛑 PROBLEMA ESPECÍFICO: Muchos stop-loss en scores altos')
                print('💡 Posibles causas:')
                print('• Score no evalúa correctamente dirección del precio')
                print('• Falta componente de timing de entrada')
                print('• Stop-loss demasiado ajustado para la volatilidad')
        
        return {
            'score_discrimination': score_diff,
            'total_trades': len(trades),
            'win_rate': len(ganadores) / len(trades) * 100,
            'avg_score_winners': np.mean([t['score'] for t in ganadores]),
            'avg_score_losers': np.mean([t['score'] for t in perdedores])
        }

def main():
    """Función principal"""
    diagnostico = DiagnosticoScoring()
    trades = diagnostico.analizar_correlacion_score_exito()
    
    if trades:
        stats = diagnostico.generar_recomendaciones(trades)
        
        print(f'\n📊 RESUMEN EJECUTIVO')
        print('='*70)
        print(f'• Discriminación Score: {stats["score_discrimination"]:.2f} puntos')
        print(f'• Win Rate General: {stats["win_rate"]:.1f}%')
        print(f'• Score Ganadores: {stats["avg_score_winners"]:.2f}/10')
        print(f'• Score Perdedores: {stats["avg_score_losers"]:.2f}/10')
        
        if stats["score_discrimination"] < 0.5:
            print('\n🚨 VEREDICTO: Sistema de scoring DEFECTUOSO')
            print('📊 Requiere rediseño completo')
        elif stats["score_discrimination"] < 1.0:
            print('\n⚠️ VEREDICTO: Sistema de scoring MEJORABLE')
            print('📊 Requiere ajustes significativos')
        else:
            print('\n✅ VEREDICTO: Sistema de scoring FUNCIONAL')
            print('📊 Requiere optimizaciones menores')

if __name__ == "__main__":
    main()