#!/usr/bin/env python3
"""
Tester de Confirmaciones
Prueba cada tipo de confirmación para encontrar la mejor
"""

from backtesting_integration import BacktestingIntegrado
from scoring_empirico_v2 import ScoringEmpiricoV2
from confirmaciones_sistema import ConfirmacionesModulares

class TesterConfirmaciones:
    """Tester para diferentes tipos de confirmación"""
    
    def __init__(self):
        self.confirmaciones_disponibles = [
            'none',           # Sin confirmación (baseline)
            'orderblocks',    # Order Blocks
            'fibonacci',      # Fibonacci retracements
            'orderflow',      # Order Flow básico
            'rsi_divergence', # Divergencias RSI
            'multitimeframe'  # Multi-timeframe
        ]
        
        self.resultados = {}
    
    def test_all_confirmations(self, tickers=['BTC-USD', 'ETH-USD', 'SOL-USD'], periods_days=30):
        """Prueba todas las confirmaciones disponibles"""
        
        print('🧪 TESTING TODAS LAS CONFIRMACIONES')
        print('='*80)
        print('Objetivo: Encontrar la confirmación que mejore más el win rate')
        print('Baseline: Sistema Empírico V2 sin confirmación')
        print('='*80)
        
        for confirmacion in self.confirmaciones_disponibles:
            print(f'\n📊 TESTING: {confirmacion.upper()}')
            print('-'*50)
            
            try:
                if confirmacion == 'none':
                    # Test baseline sin confirmación
                    resultado = self._test_baseline(tickers, periods_days)
                else:
                    # Test con confirmación específica
                    resultado = self._test_with_confirmation(confirmacion, tickers, periods_days)
                
                self.resultados[confirmacion] = resultado
                
                print(f'✅ {confirmacion}: {resultado["win_rate"]:.1f}% WR, {resultado["profit_factor"]:.2f} PF')
                
            except Exception as e:
                print(f'❌ Error en {confirmacion}: {e}')
                self.resultados[confirmacion] = None
        
        # Mostrar comparación final
        self._mostrar_comparacion_final()
        
        return self.resultados
    
    def _test_baseline(self, tickers, periods_days):
        """Test del sistema baseline sin confirmación"""
        
        backtest = BacktestingIntegrado(capital_inicial=10000)
        
        # Asegurar que no hay confirmación activa
        scoring_system = ScoringEmpiricoV2()
        scoring_system.config['liquidity_enabled'] = False
        
        trades = backtest.run_backtest(tickers=tickers, periods_days=periods_days)
        
        if trades:
            results = backtest.analyze_results(trades)
            
            return {
                'total_trades': results['total_trades'],
                'win_rate': results['win_rate'],
                'profit_factor': results['profit_factor'],
                'avg_score': results['avg_score'],
                'total_return': results['total_return'],
                'trades': trades
            }
        else:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_score': 0,
                'total_return': 0,
                'trades': []
            }
    
    def _test_with_confirmation(self, confirmacion_type, tickers, periods_days):
        """Test con confirmación específica"""
        
        # Modificar temporalmente el sistema empírico para usar confirmación
        original_calculate_long = ScoringEmpiricoV2.calculate_empirical_score_long
        original_calculate_short = ScoringEmpiricoV2.calculate_empirical_score_short
        
        confirmacion_system = ConfirmacionesModulares(confirmacion_type)
        
        def enhanced_score_long(self, df, current, prev=None):
            # Obtener score base
            base_score, base_details = original_calculate_long(self, df, current, prev)
            
            # Añadir confirmación
            conf_score, conf_details = confirmacion_system.get_confirmacion_score(df, current, 'LONG')
            
            # Integrar confirmación (15% del score total)
            enhanced_score = base_score * 0.85 + conf_score * 1.5  # 1.5 para que sea 15% del total
            enhanced_details = base_details.copy()
            enhanced_details['confirmacion'] = conf_details
            
            return min(enhanced_score, 10.0), enhanced_details
        
        def enhanced_score_short(self, df, current, prev=None):
            # Obtener score base
            base_score, base_details = original_calculate_short(self, df, current, prev)
            
            # Añadir confirmación
            conf_score, conf_details = confirmacion_system.get_confirmacion_score(df, current, 'SHORT')
            
            # Integrar confirmación
            enhanced_score = base_score * 0.85 + conf_score * 1.5
            enhanced_details = base_details.copy()
            enhanced_details['confirmacion'] = conf_details
            
            return min(enhanced_score, 10.0), enhanced_details
        
        # Monkey patch temporal
        ScoringEmpiricoV2.calculate_empirical_score_long = enhanced_score_long
        ScoringEmpiricoV2.calculate_empirical_score_short = enhanced_score_short
        
        try:
            # Ejecutar backtesting
            backtest = BacktestingIntegrado(capital_inicial=10000)
            trades = backtest.run_backtest(tickers=tickers, periods_days=periods_days)
            
            if trades:
                results = backtest.analyze_results(trades)
                
                resultado = {
                    'total_trades': results['total_trades'],
                    'win_rate': results['win_rate'],
                    'profit_factor': results['profit_factor'],
                    'avg_score': results['avg_score'],
                    'total_return': results['total_return'],
                    'trades': trades,
                    'confirmacion_type': confirmacion_type
                }
            else:
                resultado = {
                    'total_trades': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'avg_score': 0,
                    'total_return': 0,
                    'trades': [],
                    'confirmacion_type': confirmacion_type
                }
        
        finally:
            # Restaurar métodos originales
            ScoringEmpiricoV2.calculate_empirical_score_long = original_calculate_long
            ScoringEmpiricoV2.calculate_empirical_score_short = original_calculate_short
        
        return resultado
    
    def _mostrar_comparacion_final(self):
        """Muestra comparación final de todas las confirmaciones"""
        
        print(f'\n🏆 COMPARACIÓN FINAL DE CONFIRMACIONES')
        print('='*80)
        
        # Ordenar por win rate
        resultados_validos = {k: v for k, v in self.resultados.items() if v is not None}
        resultados_ordenados = sorted(resultados_validos.items(), 
                                    key=lambda x: x[1]['win_rate'], reverse=True)
        
        print(f'{"Confirmación":<15} {"Trades":<8} {"Win Rate":<10} {"P.Factor":<10} {"Score":<8} {"Return":<8}')
        print('-'*80)
        
        baseline_wr = 0
        for confirmacion, resultado in resultados_ordenados:
            if confirmacion == 'none':
                baseline_wr = resultado['win_rate']
            
            improvement = ""
            if confirmacion != 'none' and baseline_wr > 0:
                diff = resultado['win_rate'] - baseline_wr
                improvement = f"({diff:+.1f}%)"
            
            print(f'{confirmacion:<15} {resultado["total_trades"]:<8} '
                  f'{resultado["win_rate"]:<9.1f}% {resultado["profit_factor"]:<9.2f} '
                  f'{resultado["avg_score"]:<7.1f} {resultado["total_return"]:<7.1f}% {improvement}')
        
        # Identificar la mejor confirmación
        if len(resultados_ordenados) > 1:
            mejor_confirmacion = resultados_ordenados[0]
            baseline = next((r for name, r in resultados_ordenados if name == 'none'), None)
            
            print(f'\n🎯 MEJOR CONFIRMACIÓN: {mejor_confirmacion[0].upper()}')
            
            if baseline:
                wr_improvement = mejor_confirmacion[1]['win_rate'] - baseline['win_rate']
                pf_improvement = mejor_confirmacion[1]['profit_factor'] - baseline['profit_factor']
                
                print(f'• Mejora Win Rate: {wr_improvement:+.1f}%')
                print(f'• Mejora Profit Factor: {pf_improvement:+.2f}')
                
                if wr_improvement >= 5.0:
                    print('✅ MEJORA SIGNIFICATIVA - Implementar inmediatamente')
                elif wr_improvement >= 2.0:
                    print('📊 MEJORA MODERADA - Considerar implementar')
                elif wr_improvement >= 0.5:
                    print('⚠️ MEJORA MARGINAL - Evaluar trade-off complejidad/beneficio')
                else:
                    print('❌ SIN MEJORA SIGNIFICATIVA - Mantener sistema actual')
        
        # Recomendación final
        print(f'\n💡 RECOMENDACIÓN:')
        if len(resultados_ordenados) > 0:
            mejor = resultados_ordenados[0]
            if mejor[1]['win_rate'] >= 60:
                print(f'🌟 Usar {mejor[0]} - Win Rate de {mejor[1]["win_rate"]:.1f}% es prometedor')
            elif mejor[1]['win_rate'] >= 55:
                print(f'📊 Considerar {mejor[0]} - Win Rate de {mejor[1]["win_rate"]:.1f}% es aceptable')
            else:
                print(f'🔧 Ninguna confirmación mejora suficientemente el sistema')
                print(f'   Mejor opción: {mejor[0]} con {mejor[1]["win_rate"]:.1f}% WR')

def main():
    """Función principal para testing"""
    
    tester = TesterConfirmaciones()
    
    print('🚀 INICIANDO TESTS DE CONFIRMACIONES')
    print('Esto puede tomar varios minutos...\n')
    
    # Ejecutar todos los tests
    resultados = tester.test_all_confirmations(
        tickers=['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD'],
        periods_days=30
    )
    
    print(f'\n✅ TESTING COMPLETADO')
    print(f'Resultados guardados para análisis posterior')

if __name__ == "__main__":
    main()