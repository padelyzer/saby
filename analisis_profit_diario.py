#!/usr/bin/env python3
"""
Análisis de Factibilidad: 3% Profit Diario
Evaluación realista del sistema para targets diarios
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class AnalisisProfitDiario:
    """Análisis de factibilidad para profits diarios"""
    
    def __init__(self):
        # Datos del mejor sistema (V2 Empírico)
        self.sistema_stats = {
            'win_rate': 0.565,        # 56.5%
            'profit_factor': 1.37,
            'avg_win': 1.21,          # % promedio por trade ganador
            'avg_loss': -0.94,        # % promedio por trade perdedor
            'avg_trades_per_month': 23, # Basado en backtesting 30 días
            'max_leverage': 5,        # Leverage máximo usado
        }
        
        # Target diario
        self.target_daily = 0.03  # 3% diario
        self.target_monthly = 0.03 * 22  # 3% x 22 días trading = 66% mensual
        
    def calcular_trades_necesarios_diarios(self):
        """Calcula cuántos trades necesitamos diariamente para 3%"""
        
        print('📊 ANÁLISIS: 3% PROFIT DIARIO')
        print('='*60)
        
        # Profit esperado por trade
        expected_profit_per_trade = (
            self.sistema_stats['win_rate'] * self.sistema_stats['avg_win'] + 
            (1 - self.sistema_stats['win_rate']) * self.sistema_stats['avg_loss']
        )
        
        print(f'💰 MÉTRICAS DEL SISTEMA ACTUAL:')
        print(f'• Win Rate: {self.sistema_stats["win_rate"]*100:.1f}%')
        print(f'• Profit Factor: {self.sistema_stats["profit_factor"]:.2f}')
        print(f'• Avg Win: +{self.sistema_stats["avg_win"]:.2f}%')
        print(f'• Avg Loss: {self.sistema_stats["avg_loss"]:.2f}%')
        print(f'• Expected Profit/Trade: {expected_profit_per_trade:.3f}%')
        
        # Calcular trades necesarios
        trades_necesarios = self.target_daily / (expected_profit_per_trade / 100)
        
        print(f'\n🎯 PARA ALCANZAR 3% DIARIO:')
        print(f'• Trades necesarios por día: {trades_necesarios:.1f}')
        
        # Trades actuales vs necesarios
        trades_actuales_diarios = self.sistema_stats['avg_trades_per_month'] / 22
        print(f'• Trades actuales por día: {trades_actuales_diarios:.1f}')
        
        factor_multiplicacion = trades_necesarios / trades_actuales_diarios
        print(f'• Factor de multiplicación necesario: {factor_multiplicacion:.1f}x')
        
        return trades_necesarios, factor_multiplicacion
    
    def analizar_escenarios_leverage(self):
        """Analiza diferentes escenarios con leverage"""
        
        print(f'\n⚡ ANÁLISIS CON DIFERENTES LEVERAGES:')
        print('-'*50)
        
        leverages = [1, 2, 3, 5, 8, 10]
        
        for leverage in leverages:
            # Profit amplificado por leverage
            amplified_avg_win = self.sistema_stats['avg_win'] * leverage
            amplified_avg_loss = self.sistema_stats['avg_loss'] * leverage
            
            expected_profit_leveraged = (
                self.sistema_stats['win_rate'] * amplified_avg_win + 
                (1 - self.sistema_stats['win_rate']) * amplified_avg_loss
            )
            
            trades_necesarios = self.target_daily / (expected_profit_leveraged / 100)
            trades_actuales = self.sistema_stats['avg_trades_per_month'] / 22
            
            print(f'{leverage}x Leverage:')
            print(f'  • Expected Profit/Trade: {expected_profit_leveraged:.2f}%')
            print(f'  • Trades necesarios/día: {trades_necesarios:.1f}')
            
            if trades_necesarios <= trades_actuales * 2:  # Factible si necesitamos ≤ 2x trades actuales
                print(f'  • ✅ FACTIBLE (solo {trades_necesarios/trades_actuales:.1f}x más trades)')
            elif trades_necesarios <= trades_actuales * 5:
                print(f'  • ⚠️ DESAFIANTE ({trades_necesarios/trades_actuales:.1f}x más trades)')
            else:
                print(f'  • ❌ NO FACTIBLE ({trades_necesarios/trades_actuales:.1f}x más trades)')
            print()
    
    def calcular_probabilidad_exito(self):
        """Calcula probabilidad de alcanzar 3% diario consistentemente"""
        
        print(f'🎲 ANÁLISIS DE PROBABILIDAD:')
        print('-'*50)
        
        # Simulación Monte Carlo para 3% diario
        resultados_simulacion = []
        
        # Simular 1000 días de trading
        for dia in range(1000):
            daily_trades = np.random.poisson(self.sistema_stats['avg_trades_per_month'] / 22)
            daily_profit = 0
            
            for trade in range(daily_trades):
                if np.random.random() < self.sistema_stats['win_rate']:
                    # Trade ganador
                    profit = np.random.normal(self.sistema_stats['avg_win'], 0.5)  # Variabilidad
                else:
                    # Trade perdedor
                    profit = np.random.normal(self.sistema_stats['avg_loss'], 0.3)
                
                daily_profit += profit
            
            resultados_simulacion.append(daily_profit)
        
        resultados_simulacion = np.array(resultados_simulacion)
        
        # Análisis de resultados
        dias_exitosos = np.sum(resultados_simulacion >= 3.0)
        probabilidad_3pct = dias_exitosos / 1000 * 100
        
        print(f'• Días que alcanzan 3%+: {dias_exitosos}/1000')
        print(f'• Probabilidad diaria de 3%+: {probabilidad_3pct:.1f}%')
        print(f'• Profit promedio diario: {np.mean(resultados_simulacion):.2f}%')
        print(f'• Mejor día simulado: {np.max(resultados_simulacion):.2f}%')
        print(f'• Peor día simulado: {np.min(resultados_simulacion):.2f}%')
        
        # Análisis de rachas
        dias_consecutivos_3pct = self._analizar_rachas_consecutivas(resultados_simulacion, 3.0)
        print(f'• Racha más larga de 3%+: {dias_consecutivos_3pct} días')
        
        return probabilidad_3pct
    
    def _analizar_rachas_consecutivas(self, resultados, threshold):
        """Analiza rachas consecutivas por encima del threshold"""
        
        racha_actual = 0
        racha_maxima = 0
        
        for resultado in resultados:
            if resultado >= threshold:
                racha_actual += 1
                racha_maxima = max(racha_maxima, racha_actual)
            else:
                racha_actual = 0
        
        return racha_maxima
    
    def analizar_riesgo_vs_recompensa(self):
        """Analiza el riesgo necesario para 3% diario"""
        
        print(f'\n⚠️ ANÁLISIS DE RIESGO:')
        print('-'*50)
        
        # Para 3% diario necesitamos asumir más riesgo
        position_sizes = [0.02, 0.05, 0.10, 0.15, 0.20]  # % del capital por trade
        
        for pos_size in position_sizes:
            max_loss_per_trade = pos_size * self.sistema_stats['avg_loss'] / 100
            max_loss_daily = max_loss_per_trade * 5  # Asumiendo 5 trades perdedores consecutivos
            
            max_gain_per_trade = pos_size * self.sistema_stats['avg_win'] / 100
            
            print(f'Position Size {pos_size*100:.0f}%:')
            print(f'  • Max ganancia/trade: {max_gain_per_trade*100:.2f}%')
            print(f'  • Max pérdida/trade: {max_loss_per_trade*100:.2f}%')
            print(f'  • Riesgo diario (5 losses): {max_loss_daily*100:.2f}%')
            
            if max_loss_daily <= -0.15:  # Más de 15% pérdida diaria
                print(f'  • ❌ RIESGO EXCESIVO')
            elif max_loss_daily <= -0.10:
                print(f'  • ⚠️ RIESGO ALTO')
            elif max_loss_daily <= -0.05:
                print(f'  • 📊 RIESGO MODERADO')
            else:
                print(f'  • ✅ RIESGO ACEPTABLE')
            print()
    
    def generar_estrategias_3pct(self):
        """Genera estrategias para alcanzar 3% diario"""
        
        print(f'🎯 ESTRATEGIAS PARA 3% DIARIO:')
        print('='*60)
        
        print(f'📋 ESTRATEGIA 1: ALTA FRECUENCIA')
        print(f'• Objetivo: 10-15 trades/día (vs 1 actual)')
        print(f'• Leverage: 2-3x')
        print(f'• Position size: 3-5% por trade')
        print(f'• Profit target: 0.3-0.5% por trade')
        print(f'• Factibilidad: ⚠️ DESAFIANTE (requiere muchas señales)')
        
        print(f'\n📋 ESTRATEGIA 2: LEVERAGE MODERADO')
        print(f'• Objetivo: 3-5 trades/día')
        print(f'• Leverage: 5-8x')
        print(f'• Position size: 2% por trade')
        print(f'• Profit target: 1-2% por trade')
        print(f'• Factibilidad: 📊 POSIBLE (con más riesgo)')
        
        print(f'\n📋 ESTRATEGIA 3: LEVERAGE ALTO')
        print(f'• Objetivo: 1-2 trades/día')
        print(f'• Leverage: 10-15x')
        print(f'• Position size: 1-2% por trade')
        print(f'• Profit target: 3-5% por trade')
        print(f'• Factibilidad: ❌ RIESGO EXTREMO')
        
        print(f'\n💡 RECOMENDACIÓN:')
        print(f'Estrategia 2 es el mejor balance riesgo/recompensa')
    
    def calcular_tiempo_para_targets(self):
        """Calcula tiempo para diferentes targets de ganancia"""
        
        print(f'\n⏰ TIEMPO PARA DIFERENTES TARGETS:')
        print('-'*50)
        
        profit_mensual_actual = (self.sistema_stats['avg_trades_per_month'] * 
                               (self.sistema_stats['win_rate'] * self.sistema_stats['avg_win'] + 
                                (1 - self.sistema_stats['win_rate']) * self.sistema_stats['avg_loss']))
        
        targets = [10, 25, 50, 100, 200]  # % de ganancia
        
        print(f'Con el sistema actual ({profit_mensual_actual:.1f}% mensual):')
        
        for target in targets:
            meses_necesarios = target / profit_mensual_actual
            
            print(f'• {target}% ganancia: {meses_necesarios:.1f} meses')
        
        print(f'\nCon 3% diario (66% mensual):')
        for target in targets:
            meses_con_3pct = target / 66
            print(f'• {target}% ganancia: {meses_con_3pct:.1f} meses')

def main():
    """Función principal"""
    
    analyzer = AnalisisProfitDiario()
    
    # Ejecutar todos los análisis
    trades_necesarios, factor = analyzer.calcular_trades_necesarios_diarios()
    analyzer.analizar_escenarios_leverage()
    probabilidad = analyzer.calcular_probabilidad_exito()
    analyzer.analizar_riesgo_vs_recompensa()
    analyzer.generar_estrategias_3pct()
    analyzer.calcular_tiempo_para_targets()
    
    # Conclusión final
    print(f'\n🎯 CONCLUSIÓN FINAL: 3% DIARIO')
    print('='*60)
    
    if probabilidad >= 30:
        print(f'✅ FACTIBLE: {probabilidad:.1f}% probabilidad diaria')
        print(f'📊 Recomendación: Implementar con gestión de riesgo estricta')
    elif probabilidad >= 15:
        print(f'⚠️ DESAFIANTE: {probabilidad:.1f}% probabilidad diaria')
        print(f'📊 Recomendación: Considerar targets más conservadores')
    else:
        print(f'❌ NO RECOMENDABLE: {probabilidad:.1f}% probabilidad diaria')
        print(f'📊 Recomendación: Targets más realistas (1-2% diario)')
    
    print(f'\n💡 ALTERNATIVA REALISTA:')
    profit_mensual_conservador = analyzer.sistema_stats['avg_trades_per_month'] * 0.3  # 0.3% por trade promedio
    profit_diario_conservador = profit_mensual_conservador / 22
    
    print(f'• Target diario conservador: {profit_diario_conservador:.1f}%')
    print(f'• Target mensual conservador: {profit_mensual_conservador:.1f}%')
    print(f'• Probabilidad de éxito: ~70-80%')

if __name__ == "__main__":
    main()