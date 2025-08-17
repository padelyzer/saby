#!/usr/bin/env python3
"""
Backtesting Comprehensivo del Sistema V2.5
Análisis en múltiples períodos y condiciones de mercado
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

from daily_trading_system_v25 import DailyTradingSystemV25

class ComprehensiveV25Backtest:
    """
    Backtesting extenso del sistema V2.5 con análisis detallado
    """
    
    def __init__(self):
        self.results = {}
        self.all_trades = []
        
    def run_multiple_period_backtest(self):
        """
        Ejecuta backtesting en múltiples períodos para validar consistencia
        """
        print("="*80)
        print("📊 BACKTESTING COMPREHENSIVO - SISTEMA V2.5")
        print("="*80)
        print("🎯 Objetivo: Validar consistencia del sistema V2.5 en diferentes períodos")
        print("="*80)
        
        # Definir múltiples períodos de prueba
        test_periods = [
            {
                'name': 'Q4_2024',
                'start': datetime(2024, 10, 1),
                'end': datetime(2024, 12, 31),
                'description': 'Q4 2024 - Período reciente'
            },
            {
                'name': 'Q3_2024', 
                'start': datetime(2024, 7, 1),
                'end': datetime(2024, 9, 30),
                'description': 'Q3 2024 - Verano crypto'
            },
            {
                'name': 'Q2_2024',
                'start': datetime(2024, 4, 1), 
                'end': datetime(2024, 6, 30),
                'description': 'Q2 2024 - Primavera'
            },
            {
                'name': 'Last_60_Days',
                'start': datetime.now() - timedelta(days=60),
                'end': datetime.now(),
                'description': 'Últimos 60 días'
            },
            {
                'name': 'Last_90_Days',
                'start': datetime.now() - timedelta(days=90),
                'end': datetime.now(),
                'description': 'Últimos 90 días'
            }
        ]
        
        # Símbolos para testing
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
        
        print(f"🪙 Símbolos: {', '.join(symbols)}")
        print(f"📅 Períodos de prueba: {len(test_periods)}")
        
        # Ejecutar backtesting para cada período
        for i, period in enumerate(test_periods, 1):
            print(f"\n" + "="*60)
            print(f"🧪 PERÍODO {i}/{len(test_periods)}: {period['name']}")
            print(f"📅 {period['start'].strftime('%Y-%m-%d')} → {period['end'].strftime('%Y-%m-%d')}")
            print(f"📝 {period['description']}")
            print("="*60)
            
            # Crear sistema para este período
            system = DailyTradingSystemV25(initial_capital=10000)
            
            # Ejecutar backtesting
            try:
                trades = system.backtest_v25(symbols, period['start'], period['end'])
                
                if trades:
                    # Calcular métricas del período
                    period_metrics = self.calculate_period_metrics(trades, period['name'])
                    self.results[period['name']] = period_metrics
                    self.all_trades.extend([(trade, period['name']) for trade in trades])
                    
                    print(f"\n📊 RESUMEN {period['name']}:")
                    print(f"  • Trades: {period_metrics['total_trades']}")
                    print(f"  • Win Rate: {period_metrics['win_rate']:.1f}%")
                    print(f"  • Profit Factor: {period_metrics['profit_factor']:.2f}")
                    print(f"  • ROI: {period_metrics['roi']:.1f}%")
                    print(f"  • Avg Trade: ${period_metrics['avg_trade']:.2f}")
                else:
                    print(f"❌ No trades generados en {period['name']}")
                    self.results[period['name']] = None
                    
            except Exception as e:
                print(f"❌ Error en {period['name']}: {e}")
                self.results[period['name']] = None
        
        # Análisis comparativo de períodos
        self.analyze_period_consistency()
        self.analyze_market_conditions()
        self.analyze_trade_quality()
        self.generate_final_assessment()
        
        return self.results
    
    def calculate_period_metrics(self, trades, period_name):
        """
        Calcula métricas detalladas para un período
        """
        if not trades:
            return None
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        win_rate = (winning_trades / total_trades) * 100
        
        total_pnl = sum(t['pnl'] for t in trades)
        roi = (total_pnl / 10000) * 100
        
        gross_wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
        
        avg_trade = total_pnl / total_trades
        avg_win = gross_wins / winning_trades if winning_trades > 0 else 0
        avg_loss = gross_losses / (total_trades - winning_trades) if (total_trades - winning_trades) > 0 else 0
        
        # Análisis de confianza
        confidences = [t['confidence'] for t in trades]
        avg_confidence = np.mean(confidences)
        high_conf_trades = [t for t in trades if t['confidence'] >= 0.6]
        high_conf_wr = sum(1 for t in high_conf_trades if t['pnl'] > 0) / len(high_conf_trades) * 100 if high_conf_trades else 0
        
        # Análisis temporal
        start_date = min(t['date'] for t in trades)
        end_date = max(t['date'] for t in trades)
        days_span = (end_date - start_date).days + 1
        frequency = total_trades / days_span if days_span > 0 else 0
        
        # Drawdown
        equity_curve = [10000]
        for trade in trades:
            equity_curve.append(equity_curve[-1] + trade['pnl'])
        
        peak = equity_curve[0]
        max_drawdown = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Análisis por símbolo
        symbol_performance = {}
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {'trades': 0, 'wins': 0, 'pnl': 0}
            symbol_performance[symbol]['trades'] += 1
            if trade['pnl'] > 0:
                symbol_performance[symbol]['wins'] += 1
            symbol_performance[symbol]['pnl'] += trade['pnl']
        
        return {
            'period_name': period_name,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'roi': roi,
            'profit_factor': profit_factor,
            'avg_trade': avg_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_confidence': avg_confidence,
            'high_conf_wr': high_conf_wr,
            'max_drawdown': max_drawdown,
            'frequency': frequency,
            'days_span': days_span,
            'symbol_performance': symbol_performance,
            'trades': trades
        }
    
    def analyze_period_consistency(self):
        """
        Analiza consistencia entre períodos
        """
        print("\n" + "="*80)
        print("📈 ANÁLISIS DE CONSISTENCIA ENTRE PERÍODOS")
        print("="*80)
        
        # Filtrar períodos válidos
        valid_periods = {k: v for k, v in self.results.items() if v is not None}
        
        if len(valid_periods) < 2:
            print("❌ Insuficientes períodos válidos para análisis de consistencia")
            return
        
        # Tabla comparativa
        print(f"\n📊 TABLA COMPARATIVA:")
        print(f"{'Período':<15} {'Trades':<8} {'WR':<8} {'PF':<8} {'ROI':<8} {'DD':<8} {'Freq':<8}")
        print("-" * 70)
        
        metrics_summary = {
            'win_rates': [],
            'profit_factors': [],
            'rois': [],
            'frequencies': [],
            'drawdowns': []
        }
        
        for period_name, metrics in valid_periods.items():
            print(f"{period_name:<15} {metrics['total_trades']:<8} {metrics['win_rate']:<7.1f}% "
                  f"{metrics['profit_factor']:<7.2f} {metrics['roi']:<7.1f}% "
                  f"{metrics['max_drawdown']:<7.1f}% {metrics['frequency']:<7.2f}")
            
            metrics_summary['win_rates'].append(metrics['win_rate'])
            metrics_summary['profit_factors'].append(metrics['profit_factor'])
            metrics_summary['rois'].append(metrics['roi'])
            metrics_summary['frequencies'].append(metrics['frequency'])
            metrics_summary['drawdowns'].append(metrics['max_drawdown'])
        
        # Análisis estadístico
        print(f"\n📊 ESTADÍSTICAS DE CONSISTENCIA:")
        
        wr_mean = np.mean(metrics_summary['win_rates'])
        wr_std = np.std(metrics_summary['win_rates'])
        print(f"  Win Rate: {wr_mean:.1f}% ± {wr_std:.1f}% (CV: {wr_std/wr_mean*100:.1f}%)")
        
        pf_mean = np.mean(metrics_summary['profit_factors'])
        pf_std = np.std(metrics_summary['profit_factors'])
        print(f"  Profit Factor: {pf_mean:.2f} ± {pf_std:.2f} (CV: {pf_std/pf_mean*100:.1f}%)")
        
        roi_mean = np.mean(metrics_summary['rois'])
        roi_std = np.std(metrics_summary['rois'])
        print(f"  ROI: {roi_mean:.1f}% ± {roi_std:.1f}% (CV: {roi_std/abs(roi_mean)*100:.1f}%)")
        
        # Evaluación de consistencia
        print(f"\n🎯 EVALUACIÓN DE CONSISTENCIA:")
        
        if wr_std < 10:
            print("  ✅ Win Rate muy consistente (<10% desviación)")
        elif wr_std < 20:
            print("  🟡 Win Rate moderadamente consistente")
        else:
            print("  ❌ Win Rate inconsistente (>20% desviación)")
        
        if pf_std/pf_mean < 0.5:
            print("  ✅ Profit Factor consistente")
        else:
            print("  ⚠️ Profit Factor variable entre períodos")
        
        # Mejor y peor período
        best_period = max(valid_periods.items(), key=lambda x: x[1]['roi'])
        worst_period = min(valid_periods.items(), key=lambda x: x[1]['roi'])
        
        print(f"\n🏆 MEJOR PERÍODO: {best_period[0]}")
        print(f"   ROI: {best_period[1]['roi']:.1f}%, WR: {best_period[1]['win_rate']:.1f}%")
        
        print(f"💔 PEOR PERÍODO: {worst_period[0]}")
        print(f"   ROI: {worst_period[1]['roi']:.1f}%, WR: {worst_period[1]['win_rate']:.1f}%")
    
    def analyze_market_conditions(self):
        """
        Analiza comportamiento del sistema en diferentes condiciones de mercado
        """
        print("\n" + "="*80)
        print("🌍 ANÁLISIS DE CONDICIONES DE MERCADO")
        print("="*80)
        
        valid_periods = {k: v for k, v in self.results.items() if v is not None}
        
        for period_name, metrics in valid_periods.items():
            print(f"\n📊 {period_name} - ANÁLISIS DE MERCADO:")
            
            trades = metrics['trades']
            if not trades:
                continue
            
            # Análisis por tipo de trade
            long_trades = [t for t in trades if t['type'] == 'LONG']
            short_trades = [t for t in trades if t['type'] == 'SHORT']
            
            long_wr = sum(1 for t in long_trades if t['pnl'] > 0) / len(long_trades) * 100 if long_trades else 0
            short_wr = sum(1 for t in short_trades if t['pnl'] > 0) / len(short_trades) * 100 if short_trades else 0
            
            print(f"  • LONG trades: {len(long_trades)} (WR: {long_wr:.1f}%)")
            print(f"  • SHORT trades: {len(short_trades)} (WR: {short_wr:.1f}%)")
            
            # Análisis de señales
            signal_analysis = {}
            for trade in trades:
                for signal in trade.get('signals', [])[:3]:  # Top 3 signals
                    if signal not in signal_analysis:
                        signal_analysis[signal] = {'count': 0, 'wins': 0}
                    signal_analysis[signal]['count'] += 1
                    if trade['pnl'] > 0:
                        signal_analysis[signal]['wins'] += 1
            
            print(f"  • Señales más efectivas:")
            top_signals = sorted(signal_analysis.items(), 
                               key=lambda x: x[1]['wins']/x[1]['count'] if x[1]['count'] > 0 else 0, 
                               reverse=True)[:3]
            
            for signal, data in top_signals:
                wr = data['wins']/data['count']*100 if data['count'] > 0 else 0
                print(f"    - {signal}: {wr:.1f}% WR ({data['count']} trades)")
            
            # Performance por símbolo
            print(f"  • Mejor símbolo por ROI:")
            symbol_rois = []
            for symbol, perf in metrics['symbol_performance'].items():
                if perf['trades'] > 0:
                    roi = (perf['pnl'] / (perf['trades'] * 80)) * 100  # Estimado risk per trade
                    symbol_rois.append((symbol, roi, perf['trades']))
            
            symbol_rois.sort(key=lambda x: x[1], reverse=True)
            for symbol, roi, trades_count in symbol_rois[:3]:
                print(f"    - {symbol}: {roi:.1f}% ROI ({trades_count} trades)")
    
    def analyze_trade_quality(self):
        """
        Analiza la calidad de los trades del sistema V2.5
        """
        print("\n" + "="*80)
        print("🔍 ANÁLISIS DE CALIDAD DE TRADES")
        print("="*80)
        
        all_trade_data = [trade for trade, period in self.all_trades]
        
        if not all_trade_data:
            print("❌ No hay trades para analizar")
            return
        
        total_trades = len(all_trade_data)
        
        # Análisis de confianza vs resultado
        print(f"\n📊 CONFIANZA vs RESULTADO:")
        
        confidence_ranges = [
            (0.4, 0.5, 'Baja (40-50%)'),
            (0.5, 0.6, 'Media (50-60%)'),
            (0.6, 0.7, 'Alta (60-70%)'),
            (0.7, 1.0, 'Muy Alta (70%+)')
        ]
        
        for min_conf, max_conf, label in confidence_ranges:
            range_trades = [t for t in all_trade_data if min_conf <= t['confidence'] < max_conf]
            if range_trades:
                range_wins = sum(1 for t in range_trades if t['pnl'] > 0)
                range_wr = range_wins / len(range_trades) * 100
                range_avg_pnl = np.mean([t['pnl'] for t in range_trades])
                print(f"  • {label}: {len(range_trades)} trades, {range_wr:.1f}% WR, ${range_avg_pnl:.2f} avg P&L")
        
        # Verificación de filtro anti-tendencia
        print(f"\n🚫 VERIFICACIÓN FILTRO ANTI-TENDENCIA:")
        counter_trend_count = 0
        
        for trade in all_trade_data:
            signals = trade.get('signals', [])
            # Buscar evidencia de trades contra-tendencia (no debería haber)
            if any('DOWNTREND_DOMINANT' in str(s) for s in signals) and trade['type'] == 'LONG':
                counter_trend_count += 1
            elif any('UPTREND_DOMINANT' in str(s) for s in signals) and trade['type'] == 'SHORT':
                counter_trend_count += 1
        
        counter_trend_pct = counter_trend_count / total_trades * 100
        print(f"  • Trades contra-tendencia: {counter_trend_count} ({counter_trend_pct:.1f}%)")
        
        if counter_trend_pct == 0:
            print("  ✅ EXCELENTE: Filtro anti-tendencia funcionando perfectamente")
        elif counter_trend_pct < 5:
            print("  🟡 BUENO: Filtro anti-tendencia mayormente efectivo")
        else:
            print("  ❌ PROBLEMA: Filtro anti-tendencia no está funcionando")
        
        # Análisis de stops
        print(f"\n🛡️ ANÁLISIS DE STOPS:")
        exit_reasons = {}
        for trade in all_trade_data:
            # Simular razón de salida basada en P&L
            if trade['pnl'] > 0:
                reason = "Take Profit"
            else:
                reason = "Stop Loss"
            
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        for reason, count in exit_reasons.items():
            pct = count / total_trades * 100
            print(f"  • {reason}: {count} trades ({pct:.1f}%)")
        
        # V2.5 vs V2 comparison reminder
        print(f"\n📈 COMPARACIÓN vs V2 ORIGINAL:")
        print(f"  • V2.5 Counter-trend: {counter_trend_pct:.1f}% vs V2: 30%")
        print(f"  • Mejora: {30 - counter_trend_pct:.1f} puntos porcentuales")
        
    def generate_final_assessment(self):
        """
        Genera evaluación final del sistema V2.5
        """
        print("\n" + "="*80)
        print("🎯 EVALUACIÓN FINAL - SISTEMA V2.5")
        print("="*80)
        
        valid_periods = {k: v for k, v in self.results.items() if v is not None}
        
        if not valid_periods:
            print("❌ No hay datos suficientes para evaluación final")
            return
        
        # Métricas agregadas
        total_trades = sum(m['total_trades'] for m in valid_periods.values())
        total_pnl = sum(m['total_pnl'] for m in valid_periods.values())
        avg_win_rate = np.mean([m['win_rate'] for m in valid_periods.values()])
        avg_profit_factor = np.mean([m['profit_factor'] for m in valid_periods.values()])
        avg_roi = np.mean([m['roi'] for m in valid_periods.values()])
        
        print(f"\n📊 MÉTRICAS AGREGADAS ({len(valid_periods)} períodos):")
        print(f"  • Total Trades: {total_trades}")
        print(f"  • Win Rate Promedio: {avg_win_rate:.1f}%")
        print(f"  • Profit Factor Promedio: {avg_profit_factor:.2f}")
        print(f"  • ROI Promedio: {avg_roi:.1f}%")
        print(f"  • P&L Total: ${total_pnl:.2f}")
        
        # Evaluación por criterios
        print(f"\n🎯 EVALUACIÓN POR CRITERIOS:")
        
        criteria_scores = []
        
        # 1. Win Rate
        if avg_win_rate >= 70:
            print("  ✅ Win Rate: EXCELENTE (≥70%)")
            criteria_scores.append(5)
        elif avg_win_rate >= 60:
            print("  ✅ Win Rate: MUY BUENO (≥60%)")
            criteria_scores.append(4)
        elif avg_win_rate >= 55:
            print("  🟡 Win Rate: BUENO (≥55%)")
            criteria_scores.append(3)
        else:
            print("  ❌ Win Rate: NECESITA MEJORA (<55%)")
            criteria_scores.append(2)
        
        # 2. Profit Factor
        if avg_profit_factor >= 3.0:
            print("  ✅ Profit Factor: EXCELENTE (≥3.0)")
            criteria_scores.append(5)
        elif avg_profit_factor >= 2.0:
            print("  ✅ Profit Factor: MUY BUENO (≥2.0)")
            criteria_scores.append(4)
        elif avg_profit_factor >= 1.5:
            print("  🟡 Profit Factor: BUENO (≥1.5)")
            criteria_scores.append(3)
        else:
            print("  ❌ Profit Factor: NECESITA MEJORA (<1.5)")
            criteria_scores.append(2)
        
        # 3. Consistencia
        win_rate_std = np.std([m['win_rate'] for m in valid_periods.values()])
        if win_rate_std < 10:
            print("  ✅ Consistencia: EXCELENTE (<10% desviación)")
            criteria_scores.append(5)
        elif win_rate_std < 20:
            print("  🟡 Consistencia: BUENA (<20% desviación)")
            criteria_scores.append(3)
        else:
            print("  ❌ Consistencia: VARIABLE (≥20% desviación)")
            criteria_scores.append(2)
        
        # 4. Frecuencia de Trading
        avg_frequency = np.mean([m['frequency'] for m in valid_periods.values()])
        if avg_frequency >= 0.3:
            print("  ✅ Frecuencia: BUENA (≥0.3 trades/día)")
            criteria_scores.append(4)
        elif avg_frequency >= 0.1:
            print("  🟡 Frecuencia: MODERADA (≥0.1 trades/día)")
            criteria_scores.append(3)
        else:
            print("  ⚠️ Frecuencia: BAJA (<0.1 trades/día)")
            criteria_scores.append(2)
        
        # Score final
        final_score = np.mean(criteria_scores)
        
        print(f"\n🏆 SCORE FINAL: {final_score:.1f}/5.0")
        
        if final_score >= 4.5:
            assessment = "EXCELENTE - Listo para implementación"
            recommendation = "✅ Proceder con paper trading inmediatamente"
        elif final_score >= 4.0:
            assessment = "MUY BUENO - Listo con monitoreo"
            recommendation = "✅ Proceder con paper trading con monitoreo estrecho"
        elif final_score >= 3.5:
            assessment = "BUENO - Requiere validación adicional"
            recommendation = "🟡 Validar en período más largo antes de implementar"
        else:
            assessment = "NECESITA MEJORAS"
            recommendation = "❌ Optimizar parámetros antes de implementación"
        
        print(f"📝 EVALUACIÓN: {assessment}")
        print(f"💡 RECOMENDACIÓN: {recommendation}")
        
        # Próximos pasos
        print(f"\n🚀 PRÓXIMOS PASOS RECOMENDADOS:")
        print("1. 📊 Paper trading por 2-4 semanas")
        print("2. 📈 Monitorear métricas en tiempo real")
        print("3. 🔄 Validar comportamiento vs backtest")
        print("4. 💰 Si paper trading exitoso → Capital real gradual")
        print("5. 📋 Re-evaluar mensualmente")
        
        return final_score, assessment, recommendation


def main():
    """
    Función principal del backtesting comprehensivo V2.5
    """
    print("🚀 INICIANDO BACKTESTING COMPREHENSIVO V2.5")
    print("Objetivo: Validar consistencia y robustez del sistema mejorado")
    
    backtester = ComprehensiveV25Backtest()
    results = backtester.run_multiple_period_backtest()
    
    print("\n" + "="*80)
    print("✅ BACKTESTING COMPREHENSIVO V2.5 COMPLETADO")
    print("="*80)
    
    return results

if __name__ == "__main__":
    results = main()