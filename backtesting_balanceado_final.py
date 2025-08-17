#!/usr/bin/env python3
"""
Backtesting Final del Sistema Híbrido Balanceado
Validación completa de la configuración óptima
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
from sistema_hibrido_balanceado_final import SistemaHibridoBalanceado
warnings.filterwarnings('ignore')

class BacktestingBalanceadoFinal:
    """
    Backtesting del sistema híbrido balanceado
    """
    
    def __init__(self, capital_inicial=10000):
        self.capital_inicial = capital_inicial
        self.capital_actual = capital_inicial
        self.sistema = SistemaHibridoBalanceado(capital=capital_inicial)
        
        # Configuración de trading
        self.trailing_activation = 0.012  # 1.2%
        self.trailing_distance = 0.004   # 0.4%
        self.partial_close_pct = 0.4     # Cerrar 40% en primer target
        
        # Tracking
        self.trades_ejecutados = []
        self.equity_curve = []
        
    def simular_trade_balanceado(self, signal, df, entry_idx):
        """Simula trade con gestión balanceada"""
        
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        signal_type = signal['type']
        
        # Position size según el sistema
        position_size = self.sistema.calculate_position_size_dynamic(signal, signal['volatility']/100)
        
        # Variables de gestión
        trailing_stop = None
        partial_closed = False
        remaining_size = 1.0
        total_profit = 0
        
        # Simular hasta 80 períodos (80 horas)
        for i in range(entry_idx + 1, min(entry_idx + 80, len(df))):
            current_bar = df.iloc[i]
            current_price = current_bar['Close']
            
            if signal_type == 'LONG':
                # Calcular profit actual
                current_profit_pct = (current_price - entry_price) / entry_price
                
                # Gestión de trailing stop
                if current_profit_pct >= self.trailing_activation:
                    new_trailing = current_price * (1 - self.trailing_distance)
                    if trailing_stop is None or new_trailing > trailing_stop:
                        trailing_stop = new_trailing
                
                # Verificar take profit (cerrar parcial primero)
                if current_bar['High'] >= take_profit and not partial_closed:
                    # Cerrar 40% en take profit
                    partial_profit = ((take_profit - entry_price) / entry_price) * self.partial_close_pct
                    total_profit += partial_profit
                    remaining_size = 1 - self.partial_close_pct
                    partial_closed = True
                    
                    # Ajustar trailing para el resto
                    if trailing_stop is None:
                        trailing_stop = take_profit * 0.995
                    
                    continue
                
                # Verificar stop loss
                elif current_bar['Low'] <= stop_loss:
                    final_profit = ((stop_loss - entry_price) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'SL' if not partial_closed else 'SL_PARTIAL'
                    break
                
                # Verificar trailing stop
                elif trailing_stop and current_bar['Low'] <= trailing_stop:
                    final_profit = ((trailing_stop - entry_price) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'TRAIL' if not partial_closed else 'TRAIL_PARTIAL'
                    break
            
            else:  # SHORT
                current_profit_pct = (entry_price - current_price) / entry_price
                
                if current_profit_pct >= self.trailing_activation:
                    new_trailing = current_price * (1 + self.trailing_distance)
                    if trailing_stop is None or new_trailing < trailing_stop:
                        trailing_stop = new_trailing
                
                if current_bar['Low'] <= take_profit and not partial_closed:
                    partial_profit = ((entry_price - take_profit) / entry_price) * self.partial_close_pct
                    total_profit += partial_profit
                    remaining_size = 1 - self.partial_close_pct
                    partial_closed = True
                    
                    if trailing_stop is None:
                        trailing_stop = take_profit * 1.005
                    
                    continue
                
                elif current_bar['High'] >= stop_loss:
                    final_profit = ((entry_price - stop_loss) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'SL' if not partial_closed else 'SL_PARTIAL'
                    break
                
                elif trailing_stop and current_bar['High'] >= trailing_stop:
                    final_profit = ((entry_price - trailing_stop) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'TRAIL' if not partial_closed else 'TRAIL_PARTIAL'
                    break
        else:
            # Salida por tiempo
            final_profit = ((current_price - entry_price) / entry_price if signal_type == 'LONG' 
                          else (entry_price - current_price) / entry_price) * remaining_size
            total_profit += final_profit
            exit_reason = 'TIME' if not partial_closed else 'TIME_PARTIAL'
        
        return {
            'ticker': signal['ticker'],
            'type': signal_type,
            'entry_price': entry_price,
            'profit_pct': total_profit * 100,
            'exit_reason': exit_reason,
            'position_size': position_size,
            'score': signal['score'],
            'risk_reward': signal['risk_reward'],
            'had_partial_close': partial_closed,
            'had_trailing': trailing_stop is not None,
            'duration_hours': i - entry_idx if 'i' in locals() else 80
        }
    
    def backtest_periodo_balanceado(self, start_date, end_date, tickers, period_name):
        """Backtesting balanceado para un período"""
        
        print(f"\n🔄 BACKTESTING BALANCEADO: {period_name}")
        print(f"📅 {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
        print("="*60)
        
        # Descargar datos
        ticker_data = {}
        for ticker in tickers:
            try:
                data = yf.Ticker(ticker)
                df = data.history(start=start_date - timedelta(days=60), 
                                 end=end_date + timedelta(days=1), 
                                 interval='1h')
                
                if len(df) > 100:
                    df = self.sistema.calculate_indicators_balanced(df)
                    ticker_data[ticker] = df
                    print(f"   ✅ {ticker}: {len(df)} barras")
                else:
                    print(f"   ⚠️ {ticker}: Insuficiente")
            except Exception as e:
                print(f"   ❌ {ticker}: Error")
        
        if not ticker_data:
            print("❌ Sin datos suficientes")
            return []
        
        # Buscar señales y simular trades
        all_trades = []
        
        print(f"\n🔍 Buscando señales balanceadas...")
        
        for ticker, df in ticker_data.items():
            señales_encontradas = 0
            
            # Muestreo cada 12 horas para eficiencia
            for i in range(60, len(df), 12):
                current_date = df.index[i].date()
                
                if current_date < start_date.date() or current_date > end_date.date():
                    continue
                
                # Crear subset hasta el punto actual
                historical_df = df.iloc[:i+1].copy()
                
                try:
                    signal = self.sistema.generate_balanced_signal(historical_df, ticker)
                    
                    if signal:
                        señales_encontradas += 1
                        
                        # Simular el trade
                        trade_result = self.simular_trade_balanceado(signal, df, i)
                        all_trades.append(trade_result)
                        
                        # Limitar señales por ticker
                        if señales_encontradas >= 8:
                            break
                            
                except Exception as e:
                    continue
            
            print(f"   📊 {ticker}: {señales_encontradas} señales")
        
        return all_trades
    
    def analizar_resultados_balanceados(self, trades, period_name):
        """Análisis detallado de resultados balanceados"""
        
        if not trades:
            print(f"\n❌ No hay trades en {period_name}")
            return None
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['profit_pct'] > 0]
        losing_trades = [t for t in trades if t['profit_pct'] <= 0]
        
        # Métricas básicas
        win_rate = (len(winning_trades) / total_trades) * 100
        avg_win = np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Profit Factor
        gross_profit = sum(t['profit_pct'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['profit_pct'] for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Métricas avanzadas del sistema balanceado
        avg_score = np.mean([t['score'] for t in trades])
        avg_rr = np.mean([t['risk_reward'] for t in trades])
        avg_duration = np.mean([t['duration_hours'] for t in trades])
        
        # Análisis de gestión avanzada
        partial_close_trades = [t for t in trades if t['had_partial_close']]
        trailing_trades = [t for t in trades if t['had_trailing']]
        
        partial_close_wr = (len([t for t in partial_close_trades if t['profit_pct'] > 0]) / 
                           len(partial_close_trades) * 100) if partial_close_trades else 0
        
        trailing_wr = (len([t for t in trailing_trades if t['profit_pct'] > 0]) / 
                      len(trailing_trades) * 100) if trailing_trades else 0
        
        # Análisis por exit reason
        exit_analysis = {}
        for trade in trades:
            reason = trade['exit_reason']
            if reason not in exit_analysis:
                exit_analysis[reason] = {'count': 0, 'profits': [], 'wins': 0}
            exit_analysis[reason]['count'] += 1
            exit_analysis[reason]['profits'].append(trade['profit_pct'])
            if trade['profit_pct'] > 0:
                exit_analysis[reason]['wins'] += 1
        
        print(f"\n📊 RESULTADOS BALANCEADOS - {period_name}")
        print("="*60)
        print(f"• Total Trades: {total_trades}")
        print(f"• Win Rate: {win_rate:.1f}%")
        print(f"• Profit Factor: {profit_factor:.2f}")
        print(f"• Avg Win: {avg_win:+.2f}%")
        print(f"• Avg Loss: {avg_loss:+.2f}%")
        print(f"• Score Promedio: {avg_score:.1f}/10")
        print(f"• R:R Promedio: 1:{avg_rr:.1f}")
        print(f"• Duración Promedio: {avg_duration:.1f}h")
        
        print(f"\n🎯 GESTIÓN AVANZADA:")
        print(f"• Trades con cierre parcial: {len(partial_close_trades)} (WR: {partial_close_wr:.0f}%)")
        print(f"• Trades con trailing: {len(trailing_trades)} (WR: {trailing_wr:.0f}%)")
        
        print(f"\n🚪 ANÁLISIS POR SALIDA:")
        for reason, data in exit_analysis.items():
            reason_wr = (data['wins'] / data['count'] * 100) if data['count'] > 0 else 0
            reason_avg = np.mean(data['profits'])
            print(f"• {reason}: {data['count']} trades, WR: {reason_wr:.0f}%, Avg: {reason_avg:+.2f}%")
        
        # Calificación del sistema balanceado
        if win_rate >= 65 and profit_factor >= 1.5:
            grade = "🌟 EXCELENTE - Sistema Balanceado Óptimo"
        elif win_rate >= 60 and profit_factor >= 1.3:
            grade = "✅ BUENO - Sistema Balanceado Efectivo"
        elif win_rate >= 55 and profit_factor >= 1.1:
            grade = "⚠️ ACEPTABLE - Necesita ajustes menores"
        else:
            grade = "❌ INSUFICIENTE - Revisar balance"
        
        print(f"\n🏆 CALIFICACIÓN: {grade}")
        
        return {
            'period': period_name,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_score': avg_score,
            'avg_rr': avg_rr,
            'partial_close_count': len(partial_close_trades),
            'trailing_count': len(trailing_trades),
            'grade': grade
        }
    
    def ejecutar_backtesting_completo(self):
        """Ejecuta backtesting completo del sistema balanceado"""
        
        print("""
╔════════════════════════════════════════════════════════════════════════╗
║              BACKTESTING SISTEMA HÍBRIDO BALANCEADO FINAL              ║
║                     Validación de Configuración Óptima                ║
╚════════════════════════════════════════════════════════════════════════╝
        """)
        
        # Períodos de validación
        periods = [
            ('Últimos 20 días', datetime.now() - timedelta(days=20), datetime.now()),
            ('Julio 2024', datetime(2024, 7, 1), datetime(2024, 7, 31)),
            ('Agosto 2024', datetime(2024, 8, 1), datetime(2024, 8, 31)),
            ('Septiembre 2024', datetime(2024, 9, 1), datetime(2024, 9, 30)),
            ('Octubre 2024', datetime(2024, 10, 1), datetime(2024, 10, 31))
        ]
        
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
        
        resultados = []
        
        for period_name, start_date, end_date in periods:
            try:
                trades = self.backtest_periodo_balanceado(start_date, end_date, tickers, period_name)
                resultado = self.analizar_resultados_balanceados(trades, period_name)
                
                if resultado:
                    resultados.append(resultado)
                    
            except Exception as e:
                print(f"❌ Error en {period_name}: {e}")
        
        # Análisis consolidado final
        if resultados:
            self.mostrar_evaluacion_final(resultados)
        else:
            print("\n❌ No se obtuvieron resultados para evaluar")
    
    def mostrar_evaluacion_final(self, resultados):
        """Evaluación final del sistema balanceado"""
        
        print(f"\n{'='*80}")
        print("📊 EVALUACIÓN FINAL - SISTEMA HÍBRIDO BALANCEADO")
        print(f"{'='*80}")
        
        # Tabla consolidada
        print(f"\n{'Período':<18} {'Trades':<8} {'WR%':<8} {'PF':<6} {'Score':<7} {'Calificación'}")
        print("-" * 80)
        
        total_trades = sum(r['total_trades'] for r in resultados)
        total_wins = sum(r['total_trades'] * r['win_rate'] / 100 for r in resultados)
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        avg_pf = np.mean([r['profit_factor'] for r in resultados])
        avg_score = np.mean([r['avg_score'] for r in resultados])
        avg_rr = np.mean([r['avg_rr'] for r in resultados])
        
        for resultado in resultados:
            print(f"{resultado['period']:<18} {resultado['total_trades']:<8} "
                  f"{resultado['win_rate']:<7.1f} {resultado['profit_factor']:<5.2f} "
                  f"{resultado['avg_score']:<6.1f} {resultado['grade'][:12]}")
        
        print("-" * 80)
        print(f"{'PROMEDIO GENERAL':<18} {total_trades:<8} {overall_wr:<7.1f} {avg_pf:<5.2f} {avg_score:<6.1f}")
        
        # Métricas de gestión avanzada
        total_partial = sum(r['partial_close_count'] for r in resultados)
        total_trailing = sum(r['trailing_count'] for r in resultados)
        
        print(f"\n🎯 MÉTRICAS DEL SISTEMA BALANCEADO:")
        print(f"• Win Rate General: {overall_wr:.1f}%")
        print(f"• Profit Factor Promedio: {avg_pf:.2f}")
        print(f"• Score Promedio: {avg_score:.1f}/10")
        print(f"• R:R Promedio: 1:{avg_rr:.1f}")
        print(f"• Trades con Gestión Parcial: {total_partial}")
        print(f"• Trades con Trailing: {total_trailing}")
        
        # Evaluación del balance rentabilidad vs riesgo
        print(f"\n⚖️ EVALUACIÓN DEL BALANCE:")
        
        # Contar períodos exitosos
        periods_60_plus = [r for r in resultados if r['win_rate'] >= 60]
        periods_65_plus = [r for r in resultados if r['win_rate'] >= 65]
        
        consistency_score = len(periods_60_plus) / len(resultados) * 100
        excellence_score = len(periods_65_plus) / len(resultados) * 100
        
        print(f"• Consistencia (≥60% WR): {len(periods_60_plus)}/{len(resultados)} ({consistency_score:.0f}%)")
        print(f"• Excelencia (≥65% WR): {len(periods_65_plus)}/{len(resultados)} ({excellence_score:.0f}%)")
        print(f"• Estabilidad PF: {min([r['profit_factor'] for r in resultados]):.2f} - {max([r['profit_factor'] for r in resultados]):.2f}")
        
        # Evaluación final
        print(f"\n💡 VEREDICTO FINAL:")
        
        if overall_wr >= 65 and avg_pf >= 1.5 and consistency_score >= 80:
            veredicto = "🌟 SISTEMA BALANCEADO ÓPTIMO"
            status = "APROBADO PARA TRADING EN VIVO"
            recommendation = "Implementar con capital real siguiendo el plan de gestión"
        elif overall_wr >= 60 and avg_pf >= 1.3 and consistency_score >= 60:
            veredicto = "✅ SISTEMA BALANCEADO BUENO"
            status = "APTO CON MONITOREO"
            recommendation = "Usar con position sizing conservador y seguimiento estricto"
        elif overall_wr >= 55 and avg_pf >= 1.1:
            veredicto = "⚠️ SISTEMA NECESITA OPTIMIZACIÓN"
            status = "PAPER TRADING RECOMENDADO"
            recommendation = "Ajustar parámetros antes de usar capital real"
        else:
            veredicto = "❌ SISTEMA INSUFICIENTE"
            status = "REVISAR ESTRATEGIA"
            recommendation = "Cambiar enfoque o ajustar filtros significativamente"
        
        print(f"\n🎯 {veredicto}")
        print(f"📊 Status: {status}")
        print(f"💡 Recomendación: {recommendation}")
        
        # Plan de implementación
        if overall_wr >= 60:
            print(f"\n📋 PLAN DE IMPLEMENTACIÓN:")
            print("1. ✅ Usar sistema tal como está configurado")
            print("2. 📊 Empezar con position sizing conservador (50% del calculado)")
            print("3. 🎯 Seguir trailing stops religiosamente")
            print("4. 💰 Implementar cierres parciales en targets")
            print("5. 📈 Monitorear performance semanalmente")
            print("6. ⚖️ Mantener balance riesgo-recompensa")
            print("7. 🔄 Re-evaluar parámetros cada mes")
        
        # Guardar resultados
        df_resultados = pd.DataFrame(resultados)
        df_resultados.to_csv('backtesting_balanceado_final_resultados.csv', index=False)
        print(f"\n💾 Resultados guardados en backtesting_balanceado_final_resultados.csv")

def main():
    """Función principal"""
    backtest = BacktestingBalanceadoFinal(capital_inicial=10000)
    backtest.ejecutar_backtesting_completo()

if __name__ == "__main__":
    main()