#!/usr/bin/env python3
"""
Backtesting Extenso para Sistema Híbrido v2.0
Validación completa de filtros optimizados
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
from sistema_hibrido_v2_optimizado import SistemaHibridoV2
warnings.filterwarnings('ignore')

class BacktestingExtensoV2:
    """
    Backtesting extenso para validar sistema v2.0 optimizado
    """
    
    def __init__(self, capital_inicial=10000):
        self.capital_inicial = capital_inicial
        self.sistema = SistemaHibridoV2(capital=capital_inicial)
        
        # Configuración de backtesting
        self.max_trades_concurrentes = 3
        self.trailing_activation = 0.015  # 1.5%
        self.trailing_distance = 0.005   # 0.5%
        
        # Resultados
        self.all_results = []
        
    def simular_trade_completo(self, signal, df, entry_idx):
        """
        Simula un trade completo con gestión avanzada
        """
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        signal_type = signal['type']
        
        # Calcular position size dinámico
        risk_pct = abs(entry_price - stop_loss) / entry_price
        position_size = min(0.06, 0.02 / risk_pct)  # Máximo 6%, respetando 2% risk
        
        trailing_stop = None
        max_favorable_excursion = 0
        max_adverse_excursion = 0
        
        # Simular hasta 100 períodos (100 horas)
        for i in range(entry_idx + 1, min(entry_idx + 100, len(df))):
            current_bar = df.iloc[i]
            current_price = current_bar['Close']
            
            if signal_type == 'LONG':
                # Calcular excursiones
                favorable_move = (current_price - entry_price) / entry_price
                adverse_move = (entry_price - current_bar['Low']) / entry_price
                
                max_favorable_excursion = max(max_favorable_excursion, favorable_move)
                max_adverse_excursion = max(max_adverse_excursion, adverse_move)
                
                # Gestión de trailing stop
                if favorable_move >= self.trailing_activation:
                    new_trailing = current_price * (1 - self.trailing_distance)
                    if trailing_stop is None or new_trailing > trailing_stop:
                        trailing_stop = new_trailing
                
                # Verificar salidas
                if current_bar['High'] >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TP'
                    break
                elif current_bar['Low'] <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'SL'
                    break
                elif trailing_stop and current_bar['Low'] <= trailing_stop:
                    exit_price = trailing_stop
                    exit_reason = 'TRAIL'
                    break
            
            else:  # SHORT
                favorable_move = (entry_price - current_price) / entry_price
                adverse_move = (current_bar['High'] - entry_price) / entry_price
                
                max_favorable_excursion = max(max_favorable_excursion, favorable_move)
                max_adverse_excursion = max(max_adverse_excursion, adverse_move)
                
                # Trailing stop para SHORT
                if favorable_move >= self.trailing_activation:
                    new_trailing = current_price * (1 + self.trailing_distance)
                    if trailing_stop is None or new_trailing < trailing_stop:
                        trailing_stop = new_trailing
                
                # Verificar salidas
                if current_bar['Low'] <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TP'
                    break
                elif current_bar['High'] >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'SL'
                    break
                elif trailing_stop and current_bar['High'] >= trailing_stop:
                    exit_price = trailing_stop
                    exit_reason = 'TRAIL'
                    break
        else:
            # Salida por tiempo
            exit_price = df.iloc[min(entry_idx + 100, len(df)-1)]['Close']
            exit_reason = 'TIME'
        
        # Calcular resultado
        if signal_type == 'LONG':
            profit_pct = (exit_price - entry_price) / entry_price
        else:
            profit_pct = (entry_price - exit_price) / entry_price
        
        return {
            'ticker': signal['ticker'],
            'type': signal_type,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'profit_pct': profit_pct * 100,
            'exit_reason': exit_reason,
            'position_size': position_size,
            'score': signal['score'],
            'risk_reward': signal['risk_reward'],
            'mtf_score': signal['mtf_score'],
            'volume_ratio': signal['volume_ratio'],
            'max_favorable': max_favorable_excursion * 100,
            'max_adverse': max_adverse_excursion * 100,
            'duration_hours': i - entry_idx if 'i' in locals() else 100,
            'had_trailing': trailing_stop is not None
        }
    
    def ejecutar_backtesting_periodo(self, start_date, end_date, tickers, period_name):
        """
        Ejecuta backtesting para un período específico
        """
        print(f"\n🔄 BACKTESTING PERÍODO: {period_name}")
        print(f"📅 {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
        print("="*60)
        
        # Descargar datos para todos los tickers
        ticker_data = {}
        for ticker in tickers:
            try:
                data = yf.Ticker(ticker)
                df = data.history(start=start_date - timedelta(days=90), 
                                 end=end_date + timedelta(days=1), 
                                 interval='1h')
                
                if len(df) > 200:
                    # Usar el mismo método del sistema v2.0
                    df = self.sistema.calculate_advanced_indicators(df)
                    ticker_data[ticker] = df
                    print(f"   ✅ {ticker}: {len(df)} barras descargadas")
                else:
                    print(f"   ⚠️ {ticker}: Datos insuficientes")
            except Exception as e:
                print(f"   ❌ {ticker}: Error - {e}")
        
        if not ticker_data:
            print("❌ No se pudieron descargar datos suficientes")
            return None
        
        # Buscar señales en el período
        all_signals = []
        all_trades = []
        
        print(f"\n🔍 Buscando señales premium...")
        
        for ticker, df in ticker_data.items():
            signals_encontradas = 0
            
            # Analizar período por período
            for i in range(200, len(df)):
                current_date = df.index[i].date()
                
                # Solo buscar en el período objetivo
                if current_date < start_date.date() or current_date > end_date.date():
                    continue
                
                # Obtener datos hasta este punto
                historical_df = df.iloc[:i+1]
                
                # Generar señal con sistema v2.0
                try:
                    signal = self.sistema.generate_ultra_precise_signal(historical_df, ticker)
                    
                    if signal:
                        signals_encontradas += 1
                        signal['entry_idx'] = i
                        all_signals.append(signal)
                        
                        # Simular el trade
                        trade_result = self.simular_trade_completo(signal, df, i)
                        all_trades.append(trade_result)
                        
                        # Limitar señales por ticker para evitar oversaturation
                        if signals_encontradas >= 10:  # Máximo 10 señales por ticker por período
                            break
                            
                except Exception as e:
                    continue  # Skip en caso de error
            
            if signals_encontradas > 0:
                print(f"   📊 {ticker}: {signals_encontradas} señales generadas")
            else:
                print(f"   💤 {ticker}: Sin señales (filtros estrictos)")
        
        # Analizar resultados
        if all_trades:
            resultado = self.analizar_resultados_detallados(all_trades, period_name)
            return resultado
        else:
            print(f"\n❌ No se ejecutaron trades en {period_name}")
            return None
    
    def analizar_resultados_detallados(self, trades, period_name):
        """
        Análisis detallado de resultados con métricas avanzadas
        """
        total_trades = len(trades)
        trades_ganadores = [t for t in trades if t['profit_pct'] > 0]
        trades_perdedores = [t for t in trades if t['profit_pct'] <= 0]
        
        # Métricas básicas
        win_rate = (len(trades_ganadores) / total_trades) * 100
        avg_win = np.mean([t['profit_pct'] for t in trades_ganadores]) if trades_ganadores else 0
        avg_loss = np.mean([t['profit_pct'] for t in trades_perdedores]) if trades_perdedores else 0
        
        # Profit Factor
        gross_profit = sum(t['profit_pct'] for t in trades_ganadores) if trades_ganadores else 0
        gross_loss = abs(sum(t['profit_pct'] for t in trades_perdedores)) if trades_perdedores else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Métricas avanzadas
        avg_score = np.mean([t['score'] for t in trades])
        avg_rr = np.mean([t['risk_reward'] for t in trades])
        avg_mtf = np.mean([t['mtf_score'] for t in trades])
        avg_volume = np.mean([t['volume_ratio'] for t in trades])
        
        # Análisis por salida
        exit_analysis = {}
        for trade in trades:
            reason = trade['exit_reason']
            if reason not in exit_analysis:
                exit_analysis[reason] = {'count': 0, 'profits': [], 'wins': 0}
            exit_analysis[reason]['count'] += 1
            exit_analysis[reason]['profits'].append(trade['profit_pct'])
            if trade['profit_pct'] > 0:
                exit_analysis[reason]['wins'] += 1
        
        # Mejores métricas
        best_trade = max(trades, key=lambda t: t['profit_pct'])
        worst_trade = min(trades, key=lambda t: t['profit_pct'])
        
        # Análisis de excursiones
        avg_favorable = np.mean([t['max_favorable'] for t in trades])
        avg_adverse = np.mean([t['max_adverse'] for t in trades])
        
        print(f"\n📊 RESULTADOS DETALLADOS - {period_name}")
        print("="*60)
        print(f"• Total Trades: {total_trades}")
        print(f"• Win Rate: {win_rate:.1f}%")
        print(f"• Profit Factor: {profit_factor:.2f}")
        print(f"• Avg Win: {avg_win:+.2f}%")
        print(f"• Avg Loss: {avg_loss:+.2f}%")
        print(f"• Score Promedio: {avg_score:.1f}/10")
        print(f"• R:R Promedio: 1:{avg_rr:.1f}")
        print(f"• MTF Promedio: {avg_mtf:.1f}")
        print(f"• Volumen Promedio: {avg_volume:.1f}x")
        
        print(f"\n🎯 ANÁLISIS POR SALIDA:")
        for reason, data in exit_analysis.items():
            reason_wr = (data['wins'] / data['count'] * 100) if data['count'] > 0 else 0
            reason_avg = np.mean(data['profits'])
            print(f"• {reason}: {data['count']} trades, WR: {reason_wr:.0f}%, Avg: {reason_avg:+.2f}%")
        
        print(f"\n🏆 EXTREMOS:")
        print(f"• Mejor: {best_trade['ticker']} {best_trade['type']} ({best_trade['profit_pct']:+.2f}%)")
        print(f"• Peor: {worst_trade['ticker']} {worst_trade['type']} ({worst_trade['profit_pct']:+.2f}%)")
        
        print(f"\n📈 EXCURSIONES:")
        print(f"• Favorable promedio: {avg_favorable:+.2f}%")
        print(f"• Adversa promedio: {avg_adverse:+.2f}%")
        
        # Trailing analysis
        trades_with_trailing = [t for t in trades if t['had_trailing']]
        if trades_with_trailing:
            trailing_wr = (len([t for t in trades_with_trailing if t['profit_pct'] > 0]) / 
                          len(trades_with_trailing) * 100)
            print(f"• Trades con trailing: {len(trades_with_trailing)} (WR: {trailing_wr:.0f}%)")
        
        # Calificación final
        if win_rate >= 70:
            grade = "🌟 EXCELENTE"
        elif win_rate >= 65:
            grade = "✅ BUENO"
        elif win_rate >= 60:
            grade = "⚠️ ACEPTABLE"
        else:
            grade = "❌ INSUFICIENTE"
        
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
            'avg_mtf': avg_mtf,
            'exit_analysis': exit_analysis,
            'best_trade': best_trade['profit_pct'],
            'worst_trade': worst_trade['profit_pct'],
            'grade': grade
        }
    
    def ejecutar_backtesting_completo(self):
        """
        Ejecuta backtesting completo en múltiples períodos
        """
        print("""
╔════════════════════════════════════════════════════════════════════════╗
║                BACKTESTING EXTENSO SISTEMA v2.0                        ║
║                   Validación Ultra Precisa                             ║
╚════════════════════════════════════════════════════════════════════════╝
        """)
        
        # Períodos de prueba más extensos
        periods = [
            {
                'name': 'Últimos 30 días',
                'start': datetime.now() - timedelta(days=30),
                'end': datetime.now()
            },
            {
                'name': 'Julio 2024',
                'start': datetime(2024, 7, 1),
                'end': datetime(2024, 7, 31)
            },
            {
                'name': 'Agosto 2024',
                'start': datetime(2024, 8, 1),
                'end': datetime(2024, 8, 31)
            },
            {
                'name': 'Septiembre 2024',
                'start': datetime(2024, 9, 1),
                'end': datetime(2024, 9, 30)
            },
            {
                'name': 'Octubre 2024',
                'start': datetime(2024, 10, 1),
                'end': datetime(2024, 10, 31)
            }
        ]
        
        # Tickers principales
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
        
        resultados = []
        
        # Ejecutar backtesting por período
        for period in periods:
            try:
                resultado = self.ejecutar_backtesting_periodo(
                    period['start'], 
                    period['end'], 
                    tickers, 
                    period['name']
                )
                
                if resultado:
                    resultados.append(resultado)
                    
            except Exception as e:
                print(f"❌ Error en período {period['name']}: {e}")
        
        # Análisis consolidado
        if resultados:
            self.mostrar_resumen_consolidado(resultados)
        else:
            print("\n❌ No se obtuvieron resultados válidos")
    
    def mostrar_resumen_consolidado(self, resultados):
        """
        Muestra resumen consolidado de todos los períodos
        """
        print(f"\n{'='*80}")
        print("📊 RESUMEN CONSOLIDADO - SISTEMA v2.0 OPTIMIZADO")
        print(f"{'='*80}")
        
        # Tabla de resultados
        print(f"\n{'Período':<15} {'Trades':<8} {'Win Rate':<10} {'PF':<6} {'Score':<7} {'Calificación'}")
        print("-" * 75)
        
        total_trades = sum(r['total_trades'] for r in resultados)
        total_wins = sum(r['total_trades'] * r['win_rate'] / 100 for r in resultados)
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        avg_pf = np.mean([r['profit_factor'] for r in resultados])
        avg_score = np.mean([r['avg_score'] for r in resultados])
        
        for resultado in resultados:
            print(f"{resultado['period']:<15} {resultado['total_trades']:<8} "
                  f"{resultado['win_rate']:<9.1f}% {resultado['profit_factor']:<5.2f} "
                  f"{resultado['avg_score']:<6.1f} {resultado['grade']}")
        
        print("-" * 75)
        print(f"{'PROMEDIO':<15} {total_trades:<8} {overall_wr:<9.1f}% {avg_pf:<5.2f} {avg_score:<6.1f}")
        
        # Análisis detallado
        win_rates = [r['win_rate'] for r in resultados]
        
        print(f"\n🔍 ANÁLISIS ESTADÍSTICO:")
        print(f"• Win Rate: {min(win_rates):.1f}% - {max(win_rates):.1f}% (σ = {np.std(win_rates):.1f}%)")
        print(f"• Profit Factor promedio: {avg_pf:.2f}")
        print(f"• Score promedio: {avg_score:.1f}/10")
        
        # Evaluación del objetivo
        periods_60_plus = [r for r in resultados if r['win_rate'] >= 60]
        periods_65_plus = [r for r in resultados if r['win_rate'] >= 65]
        periods_70_plus = [r for r in resultados if r['win_rate'] >= 70]
        
        print(f"\n🎯 CUMPLIMIENTO DE OBJETIVOS:")
        print(f"• Períodos ≥ 60% WR: {len(periods_60_plus)}/{len(resultados)} ({len(periods_60_plus)/len(resultados)*100:.0f}%)")
        print(f"• Períodos ≥ 65% WR: {len(periods_65_plus)}/{len(resultados)} ({len(periods_65_plus)/len(resultados)*100:.0f}%)")
        print(f"• Períodos ≥ 70% WR: {len(periods_70_plus)}/{len(resultados)} ({len(periods_70_plus)/len(resultados)*100:.0f}%)")
        
        # Evaluación final
        print(f"\n💡 EVALUACIÓN FINAL DEL SISTEMA v2.0:")
        
        if overall_wr >= 65:
            print("🌟 OBJETIVO ALCANZADO")
            print("   ✅ Sistema v2.0 listo para trading real")
            print(f"   ✅ Win rate {overall_wr:.1f}% dentro del objetivo 60-70%")
            recommendation = "Implementar en trading en vivo"
        elif overall_wr >= 60:
            print("✅ CERCA DEL OBJETIVO")
            print(f"   🔧 Win rate {overall_wr:.1f}% cerca del objetivo")
            print("   💡 Ajustes menores pueden optimizar")
            recommendation = "Pruebas adicionales recomendadas"
        elif overall_wr >= 50:
            print("⚠️ RESULTADO MIXTO")
            print(f"   📊 Win rate {overall_wr:.1f}% por debajo del objetivo")
            print("   🔄 Optimización necesaria")
            recommendation = "Revisar filtros y parámetros"
        else:
            print("❌ OBJETIVO NO ALCANZADO")
            print(f"   💭 Win rate {overall_wr:.1f}% insuficiente")
            print("   🔄 Revisión completa necesaria")
            recommendation = "Cambiar enfoque estratégico"
        
        print(f"\n🎯 RECOMENDACIÓN: {recommendation}")
        
        # Guardar resultados
        df_resultados = pd.DataFrame(resultados)
        df_resultados.to_csv('backtesting_extenso_v2_resultados.csv', index=False)
        print(f"\n💾 Resultados guardados en backtesting_extenso_v2_resultados.csv")

def main():
    """Función principal"""
    backtest = BacktestingExtensoV2(capital_inicial=10000)
    backtest.ejecutar_backtesting_completo()

if __name__ == "__main__":
    main()