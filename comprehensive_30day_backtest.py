#!/usr/bin/env python3
"""
Backtesting Comprehensivo de 30 Días
Sistema Daily Trading V2 con WIF y PEPE incluidos
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

from daily_trading_system_v2 import DailyTradingSystemV2

class Comprehensive30DayBacktest:
    """
    Backtesting detallado de 30 días con análisis completo
    """
    
    def __init__(self):
        self.system = DailyTradingSystemV2(initial_capital=10000)
        self.results = {}
        
    def run_comprehensive_backtest(self):
        """
        Ejecuta backtesting comprehensivo de 30 días
        """
        print("="*80)
        print("📈 BACKTESTING COMPREHENSIVO - ÚLTIMOS 30 DÍAS")
        print("="*80)
        print("Sistema: Daily Trading V2 (Corregido)")
        print("Capital inicial: $10,000")
        print("="*80)
        
        # Símbolos expandidos
        symbols = [
            'BTC-USD',    # Bitcoin
            'ETH-USD',    # Ethereum  
            'SOL-USD',    # Solana
            'BNB-USD',    # Binance Coin
            'MATIC-USD',  # Polygon
            'WIF-USD',    # Dogwifhat (nuevo)
            'PEPE-USD'    # Pepe (nuevo)
        ]
        
        # Fechas - últimos 30 días
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"\n📅 Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
        print(f"🪙 Símbolos: {len(symbols)} activos")
        for i, symbol in enumerate(symbols, 1):
            print(f"   {i}. {symbol}")
        print("-"*80)
        
        # Ejecutar backtest
        print("\n⏳ Ejecutando backtesting...")
        trades = self.system.backtest_daily(symbols, start_date, end_date)
        
        # Análisis detallado
        if trades:
            self.analyze_detailed_results(trades, symbols, start_date, end_date)
            self.analyze_market_conditions(symbols, start_date, end_date)
            self.compare_vs_hodl(symbols, start_date, end_date, trades)
            self.risk_analysis(trades)
            self.final_recommendations(trades)
        else:
            print("❌ No se generaron trades en el período")
        
        return trades
    
    def analyze_detailed_results(self, trades, symbols, start_date, end_date):
        """
        Análisis detallado de resultados
        """
        print("\n" + "="*80)
        print("📊 ANÁLISIS DETALLADO DE RESULTADOS")
        print("="*80)
        
        # Métricas generales
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in trades)
        gross_wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
        
        avg_win = gross_wins / winning_trades if winning_trades > 0 else 0
        avg_loss = gross_losses / losing_trades if losing_trades > 0 else 0
        
        print(f"📈 MÉTRICAS PRINCIPALES:")
        print(f"  • Total Trades: {total_trades}")
        print(f"  • Trades Ganadores: {winning_trades} ({win_rate:.1f}%)")
        print(f"  • Trades Perdedores: {losing_trades}")
        print(f"  • Profit Factor: {profit_factor:.2f}")
        print(f"  • Total P&L: ${total_pnl:,.2f}")
        print(f"  • ROI: {(total_pnl/10000)*100:.1f}%")
        print(f"  • Promedio Ganancia: ${avg_win:.2f}")
        print(f"  • Promedio Pérdida: ${avg_loss:.2f}")
        print(f"  • Ratio Ganancia/Pérdida: {avg_win/avg_loss:.2f}" if avg_loss > 0 else "  • Ratio Ganancia/Pérdida: ∞")
        
        # Análisis por símbolo
        print(f"\n📊 PERFORMANCE POR SÍMBOLO:")
        symbol_stats = {}
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    'trades': 0, 'wins': 0, 'pnl': 0, 
                    'best_trade': 0, 'worst_trade': 0,
                    'avg_confidence': 0, 'confidences': []
                }
            
            symbol_stats[symbol]['trades'] += 1
            symbol_stats[symbol]['pnl'] += trade['pnl']
            symbol_stats[symbol]['confidences'].append(trade['confidence'])
            
            if trade['pnl'] > 0:
                symbol_stats[symbol]['wins'] += 1
            
            if trade['pnl'] > symbol_stats[symbol]['best_trade']:
                symbol_stats[symbol]['best_trade'] = trade['pnl']
            if trade['pnl'] < symbol_stats[symbol]['worst_trade']:
                symbol_stats[symbol]['worst_trade'] = trade['pnl']
        
        # Calcular promedios
        for symbol, stats in symbol_stats.items():
            if stats['confidences']:
                stats['avg_confidence'] = np.mean(stats['confidences'])
        
        # Ordenar por P&L
        sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['pnl'], reverse=True)
        
        print(f"  {'Símbolo':<12} {'Trades':<8} {'WR':<8} {'P&L':<12} {'Mejor':<10} {'Peor':<10} {'Conf':<8}")
        print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*12} {'-'*10} {'-'*10} {'-'*8}")
        
        for symbol, stats in sorted_symbols:
            wr = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            print(f"  {symbol:<12} {stats['trades']:<8} {wr:<7.1f}% "
                  f"${stats['pnl']:<11.2f} ${stats['best_trade']:<9.2f} "
                  f"${stats['worst_trade']:<9.2f} {stats['avg_confidence']:<7.1%}")
        
        # Top performers
        print(f"\n🏆 TOP PERFORMERS:")
        best_symbol = sorted_symbols[0]
        worst_symbol = sorted_symbols[-1]
        
        print(f"  🥇 Mejor símbolo: {best_symbol[0]} (${best_symbol[1]['pnl']:.2f})")
        print(f"  💔 Peor símbolo: {worst_symbol[0]} (${worst_symbol[1]['pnl']:.2f})")
        
        # Análisis de nuevos tokens (WIF, PEPE)
        new_tokens = ['WIF-USD', 'PEPE-USD']
        new_token_performance = {token: symbol_stats.get(token, {'trades': 0, 'pnl': 0}) 
                                for token in new_tokens}
        
        print(f"\n🆕 PERFORMANCE NUEVOS TOKENS:")
        total_new_pnl = sum(stats['pnl'] for stats in new_token_performance.values())
        total_new_trades = sum(stats['trades'] for stats in new_token_performance.values())
        
        for token, stats in new_token_performance.items():
            if stats['trades'] > 0:
                wr = (symbol_stats[token]['wins'] / stats['trades'] * 100)
                print(f"  • {token}: {stats['trades']} trades, {wr:.1f}% WR, ${stats['pnl']:.2f} P&L")
            else:
                print(f"  • {token}: No trades generados")
        
        print(f"  📊 Total nuevos tokens: ${total_new_pnl:.2f} P&L, {total_new_trades} trades")
        
        # Análisis temporal
        print(f"\n⏰ ANÁLISIS TEMPORAL:")
        days_with_trades = len(set(t['date'].date() for t in trades))
        total_days = (end_date - start_date).days
        trading_frequency = days_with_trades / total_days * 100
        
        print(f"  • Días con trades: {days_with_trades}/{total_days} ({trading_frequency:.1f}%)")
        print(f"  • Promedio trades/día: {total_trades/total_days:.1f}")
        
        # Distribución por tipo de trade
        long_trades = [t for t in trades if t['type'] == 'LONG']
        short_trades = [t for t in trades if t['type'] == 'SHORT']
        
        long_wins = sum(1 for t in long_trades if t['pnl'] > 0)
        short_wins = sum(1 for t in short_trades if t['pnl'] > 0)
        
        long_wr = (long_wins / len(long_trades) * 100) if long_trades else 0
        short_wr = (short_wins / len(short_trades) * 100) if short_trades else 0
        
        long_pnl = sum(t['pnl'] for t in long_trades)
        short_pnl = sum(t['pnl'] for t in short_trades)
        
        print(f"\n📈 DISTRIBUCIÓN POR TIPO:")
        print(f"  • LONG: {len(long_trades)} trades, {long_wr:.1f}% WR, ${long_pnl:.2f} P&L")
        print(f"  • SHORT: {len(short_trades)} trades, {short_wr:.1f}% WR, ${short_pnl:.2f} P&L")
    
    def analyze_market_conditions(self, symbols, start_date, end_date):
        """
        Analiza condiciones del mercado durante el período
        """
        print("\n" + "="*80)
        print("🌍 ANÁLISIS DE CONDICIONES DEL MERCADO")
        print("="*80)
        
        market_performance = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, interval='1d')
                
                if len(df) > 1:
                    start_price = df['Close'].iloc[0]
                    end_price = df['Close'].iloc[-1]
                    performance = ((end_price / start_price) - 1) * 100
                    
                    volatility = df['Close'].pct_change().std() * np.sqrt(252) * 100  # Anualizada
                    max_price = df['High'].max()
                    min_price = df['Low'].min()
                    price_range = ((max_price / min_price) - 1) * 100
                    
                    market_performance[symbol] = {
                        'performance': performance,
                        'volatility': volatility,
                        'price_range': price_range,
                        'start_price': start_price,
                        'end_price': end_price
                    }
            except Exception as e:
                print(f"  ⚠️ Error obteniendo datos de {symbol}: {e}")
        
        if market_performance:
            print(f"  {'Símbolo':<12} {'Rendimiento':<12} {'Volatilidad':<12} {'Rango':<10} {'Precio Inicial':<12} {'Precio Final':<12}")
            print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*10} {'-'*12} {'-'*12}")
            
            for symbol, data in sorted(market_performance.items(), key=lambda x: x[1]['performance'], reverse=True):
                print(f"  {symbol:<12} {data['performance']:>10.1f}% {data['volatility']:>10.1f}% "
                      f"{data['price_range']:>8.1f}% ${data['start_price']:>10.2f} ${data['end_price']:>10.2f}")
            
            # Estadísticas del mercado
            avg_performance = np.mean([data['performance'] for data in market_performance.values()])
            avg_volatility = np.mean([data['volatility'] for data in market_performance.values()])
            
            print(f"\n📊 ESTADÍSTICAS DEL MERCADO:")
            print(f"  • Rendimiento promedio: {avg_performance:.1f}%")
            print(f"  • Volatilidad promedio: {avg_volatility:.1f}%")
            
            # Clasificar tipo de mercado
            if avg_performance > 10:
                market_type = "BULL MARKET 🐂"
            elif avg_performance < -10:
                market_type = "BEAR MARKET 🐻"
            else:
                market_type = "SIDEWAYS MARKET ➡️"
            
            print(f"  • Tipo de mercado: {market_type}")
            
            # Análisis de nuevos tokens
            new_tokens_perf = {k: v for k, v in market_performance.items() if k in ['WIF-USD', 'PEPE-USD']}
            if new_tokens_perf:
                print(f"\n🆕 RENDIMIENTO NUEVOS TOKENS:")
                for token, data in new_tokens_perf.items():
                    print(f"  • {token}: {data['performance']:+.1f}% (Vol: {data['volatility']:.1f}%)")
        
        return market_performance
    
    def compare_vs_hodl(self, symbols, start_date, end_date, trades):
        """
        Compara performance del sistema vs HODL
        """
        print("\n" + "="*80)
        print("⚖️ COMPARACIÓN: SISTEMA vs HODL")
        print("="*80)
        
        # Calcular HODL performance
        total_hodl_performance = 0
        hodl_investments = 10000 / len(symbols)  # Dividir capital igualmente
        
        print(f"📊 HODL Strategy (${hodl_investments:.0f} por símbolo):")
        
        hodl_results = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, interval='1d')
                
                if len(df) > 1:
                    start_price = df['Close'].iloc[0]
                    end_price = df['Close'].iloc[-1]
                    performance = ((end_price / start_price) - 1) * 100
                    hodl_value = hodl_investments * (1 + performance/100)
                    hodl_pnl = hodl_value - hodl_investments
                    
                    hodl_results[symbol] = {
                        'performance': performance,
                        'value': hodl_value,
                        'pnl': hodl_pnl
                    }
                    
                    total_hodl_performance += hodl_pnl
                    print(f"  • {symbol}: {performance:+.1f}% (${hodl_pnl:+.2f})")
            except Exception as e:
                print(f"  ⚠️ {symbol}: Error - {e}")
        
        # Comparar resultados
        system_pnl = sum(t['pnl'] for t in trades)
        system_roi = (system_pnl / 10000) * 100
        hodl_roi = (total_hodl_performance / 10000) * 100
        
        print(f"\n🏆 COMPARACIÓN DE RESULTADOS:")
        print(f"  📈 Sistema Trading:")
        print(f"     • P&L: ${system_pnl:,.2f}")
        print(f"     • ROI: {system_roi:.1f}%")
        print(f"     • Trades: {len(trades)}")
        
        print(f"  💎 HODL Strategy:")
        print(f"     • P&L: ${total_hodl_performance:,.2f}")
        print(f"     • ROI: {hodl_roi:.1f}%")
        print(f"     • Rebalanceos: 0")
        
        # Veredicto
        advantage = system_pnl - total_hodl_performance
        print(f"\n🎯 VEREDICTO:")
        if advantage > 0:
            print(f"  ✅ Sistema SUPERA a HODL por ${advantage:,.2f}")
            print(f"  📊 Ventaja: {(advantage/abs(total_hodl_performance))*100:.1f}%")
        else:
            print(f"  ❌ HODL SUPERA al sistema por ${abs(advantage):,.2f}")
            print(f"  📊 Desventaja: {(abs(advantage)/abs(total_hodl_performance))*100:.1f}%")
        
        # Análisis de riesgo-retorno
        print(f"\n⚖️ ANÁLISIS RIESGO-RETORNO:")
        
        # Calcular volatilidad del sistema
        daily_returns = []
        for i in range(1, len(trades)):
            daily_returns.append(trades[i]['pnl'] - trades[i-1]['pnl'])
        
        if daily_returns:
            system_volatility = np.std(daily_returns) * np.sqrt(252)
            sharpe_ratio = (system_roi / 100) / (system_volatility / 100) if system_volatility > 0 else 0
            
            print(f"  • Sistema - Volatilidad: {system_volatility:.1f}%")
            print(f"  • Sistema - Sharpe Ratio: {sharpe_ratio:.2f}")
        
        return {'system': system_pnl, 'hodl': total_hodl_performance, 'advantage': advantage}
    
    def risk_analysis(self, trades):
        """
        Análisis detallado de riesgo
        """
        print("\n" + "="*80)
        print("⚠️ ANÁLISIS DE RIESGO")
        print("="*80)
        
        # Calcular drawdown
        equity_curve = []
        running_pnl = 10000
        
        for trade in trades:
            running_pnl += trade['pnl']
            equity_curve.append(running_pnl)
        
        if equity_curve:
            peak = equity_curve[0]
            max_drawdown = 0
            max_drawdown_pct = 0
            
            for value in equity_curve:
                if value > peak:
                    peak = value
                
                drawdown = peak - value
                drawdown_pct = (drawdown / peak) * 100
                
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct
            
            print(f"📉 DRAWDOWN:")
            print(f"  • Máximo Drawdown: ${max_drawdown:.2f} ({max_drawdown_pct:.1f}%)")
            print(f"  • Capital Final: ${equity_curve[-1]:,.2f}")
            print(f"  • Capital Máximo: ${max(equity_curve):,.2f}")
        
        # Análisis de rachas
        consecutive_wins = 0
        consecutive_losses = 0
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for trade in trades:
            if trade['pnl'] > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        print(f"\n🔄 ANÁLISIS DE RACHAS:")
        print(f"  • Máxima racha ganadora: {max_win_streak} trades")
        print(f"  • Máxima racha perdedora: {max_loss_streak} trades")
        
        # Análisis de confianza
        confidences = [t['confidence'] for t in trades]
        if confidences:
            avg_confidence = np.mean(confidences)
            min_confidence = min(confidences)
            max_confidence = max(confidences)
            
            print(f"\n🎯 ANÁLISIS DE CONFIANZA:")
            print(f"  • Confianza promedio: {avg_confidence:.1%}")
            print(f"  • Confianza mínima: {min_confidence:.1%}")
            print(f"  • Confianza máxima: {max_confidence:.1%}")
            
            # Correlación confianza-resultado
            high_conf_trades = [t for t in trades if t['confidence'] >= 0.6]
            if high_conf_trades:
                high_conf_wr = sum(1 for t in high_conf_trades if t['pnl'] > 0) / len(high_conf_trades) * 100
                print(f"  • WR con confianza >60%: {high_conf_wr:.1f}% ({len(high_conf_trades)} trades)")
        
        # Risk-Reward por trade
        risk_rewards = []
        for trade in trades:
            entry = trade['entry_price']
            stop = trade['stop_loss']
            target = trade['take_profit']
            
            if trade['type'] == 'LONG':
                risk = abs(entry - stop)
                reward = abs(target - entry)
            else:
                risk = abs(stop - entry)
                reward = abs(entry - target)
            
            if risk > 0:
                rr_ratio = reward / risk
                risk_rewards.append(rr_ratio)
        
        if risk_rewards:
            avg_rr = np.mean(risk_rewards)
            print(f"\n⚖️ RISK-REWARD:")
            print(f"  • Ratio R/R promedio: 1:{avg_rr:.1f}")
            print(f"  • Ratio R/R mínimo: 1:{min(risk_rewards):.1f}")
            print(f"  • Ratio R/R máximo: 1:{max(risk_rewards):.1f}")
    
    def final_recommendations(self, trades):
        """
        Recomendaciones finales basadas en el análisis
        """
        print("\n" + "="*80)
        print("💡 RECOMENDACIONES FINALES")
        print("="*80)
        
        total_pnl = sum(t['pnl'] for t in trades)
        win_rate = sum(1 for t in trades if t['pnl'] > 0) / len(trades) * 100
        
        recommendations = []
        
        # Evaluación general
        if total_pnl > 0 and win_rate >= 55:
            recommendations.append("✅ Sistema funcionando bien - Continuar operación")
        elif total_pnl > 0:
            recommendations.append("🟡 Sistema rentable pero mejorable - Ajustar parámetros")
        else:
            recommendations.append("❌ Sistema necesita revisión - Revisar estrategia")
        
        # Análisis por símbolo
        symbol_stats = {}
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {'trades': 0, 'wins': 0, 'pnl': 0}
            symbol_stats[symbol]['trades'] += 1
            symbol_stats[symbol]['pnl'] += trade['pnl']
            if trade['pnl'] > 0:
                symbol_stats[symbol]['wins'] += 1
        
        # Símbolos problemáticos
        problem_symbols = []
        excellent_symbols = []
        
        for symbol, stats in symbol_stats.items():
            wr = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            if stats['pnl'] < 0 or wr < 40:
                problem_symbols.append(symbol)
            elif wr >= 70 and stats['pnl'] > 100:
                excellent_symbols.append(symbol)
        
        if problem_symbols:
            recommendations.append(f"⚠️ Considerar excluir símbolos problemáticos: {', '.join(problem_symbols)}")
        
        if excellent_symbols:
            recommendations.append(f"🌟 Enfocar en símbolos top: {', '.join(excellent_symbols)}")
        
        # Análisis de nuevos tokens
        new_tokens_trades = [t for t in trades if t['symbol'] in ['WIF-USD', 'PEPE-USD']]
        if new_tokens_trades:
            new_tokens_pnl = sum(t['pnl'] for t in new_tokens_trades)
            new_tokens_wr = sum(1 for t in new_tokens_trades if t['pnl'] > 0) / len(new_tokens_trades) * 100
            
            if new_tokens_pnl > 0 and new_tokens_wr >= 60:
                recommendations.append("🆕 Nuevos tokens (WIF/PEPE) muestran buen potencial")
            elif new_tokens_pnl < 0:
                recommendations.append("⚠️ Nuevos tokens necesitan más validación antes de incluir")
        else:
            recommendations.append("📊 Nuevos tokens no generaron señales - Revisar parámetros")
        
        # Recomendaciones técnicas
        if win_rate < 50:
            recommendations.append("🔧 Aumentar filtros de calidad - WR muy bajo")
        
        avg_confidence = np.mean([t['confidence'] for t in trades])
        if avg_confidence < 0.5:
            recommendations.append("🎯 Aumentar umbral de confianza mínima")
        
        # Gestión de riesgo
        largest_loss = min([t['pnl'] for t in trades])
        if abs(largest_loss) > 500:
            recommendations.append("🛡️ Revisar stops - Pérdida máxima muy alta")
        
        print("\n📋 LISTA DE RECOMENDACIONES:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i:2d}. {rec}")
        
        # Plan de acción
        print(f"\n🎯 PLAN DE ACCIÓN INMEDIATO:")
        if total_pnl > 1000:
            print("1. ✅ Sistema validado - Comenzar paper trading")
            print("2. 📊 Monitorear performance semanal")
            print("3. 🔄 Escalar gradualmente capital")
        elif total_pnl > 0:
            print("1. 🔧 Optimizar parámetros identificados")
            print("2. 📝 Extender período de prueba a 60 días")
            print("3. ⚖️ Re-evaluar símbolos problemáticos")
        else:
            print("1. ❌ Detener trading en vivo")
            print("2. 🔍 Análisis profundo de fallos")
            print("3. 🛠️ Rediseñar estrategia fundamental")


def main():
    """
    Función principal para ejecutar el backtesting comprehensivo
    """
    print("🚀 INICIANDO BACKTESTING COMPREHENSIVO")
    print("Sistema: Daily Trading V2 (Con correcciones)")
    print("Período: Últimos 30 días")
    print("Símbolos: BTC, ETH, SOL, BNB, MATIC, WIF, PEPE")
    
    backtester = Comprehensive30DayBacktest()
    trades = backtester.run_comprehensive_backtest()
    
    print("\n" + "="*80)
    print("✅ BACKTESTING COMPREHENSIVO COMPLETADO")
    print("="*80)
    
    return trades


if __name__ == "__main__":
    trades = main()