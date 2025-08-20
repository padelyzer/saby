#!/usr/bin/env python3
"""
Backtest Detallado V4.0 - Sistema Adaptativo
Analiza cada símbolo individualmente con detalles exactos de trades
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import json
warnings.filterwarnings('ignore')

# Import del sistema adaptativo
from trading_system_v4 import (
    MarketRegimeDetector,
    TrendStrategy,
    RangeStrategy,
    VolatileStrategy,
    AdaptiveTradingSystem
)

class DetailedBacktestV4:
    """Backtest detallado para el sistema adaptativo V4.0"""
    
    def __init__(self, symbol, initial_capital=206):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        # Sistema adaptativo
        self.adaptive_system = AdaptiveTradingSystem(symbol, capital=initial_capital)
        
        # Registro detallado
        self.trades = []
        self.signals = []
        self.regime_history = []
        
    def simulate_trade(self, signal, df, entry_idx):
        """Simula un trade con el sistema adaptativo"""
        
        entry_price = signal['entry']
        entry_date = df.index[entry_idx]
        
        # Calcular stops según estrategia
        if signal['type'] == 'LONG':
            stop_loss = entry_price - (signal['atr'] * signal.get('stop_multiplier', 2.0))
            if 'target_price' in signal:
                take_profit = signal['target_price']
            else:
                take_profit = entry_price + (signal['atr'] * signal.get('target_multiplier', 2.5))
        else:
            stop_loss = entry_price + (signal['atr'] * signal.get('stop_multiplier', 2.0))
            if 'target_price' in signal:
                take_profit = signal['target_price']
            else:
                take_profit = entry_price - (signal['atr'] * signal.get('target_multiplier', 2.5))
        
        # Simular salida
        exit_price = None
        exit_date = None
        exit_reason = None
        
        for i in range(entry_idx + 1, min(entry_idx + 100, len(df))):
            current = df.iloc[i]
            
            if signal['type'] == 'LONG':
                # Check stop loss
                if current['Low'] <= stop_loss:
                    exit_price = stop_loss
                    exit_date = df.index[i]
                    exit_reason = 'STOP_LOSS'
                    break
                # Check take profit
                elif current['High'] >= take_profit:
                    exit_price = take_profit
                    exit_date = df.index[i]
                    exit_reason = 'TAKE_PROFIT'
                    break
            else:  # SHORT
                # Check stop loss
                if current['High'] >= stop_loss:
                    exit_price = stop_loss
                    exit_date = df.index[i]
                    exit_reason = 'STOP_LOSS'
                    break
                # Check take profit
                elif current['Low'] <= take_profit:
                    exit_price = take_profit
                    exit_date = df.index[i]
                    exit_reason = 'TAKE_PROFIT'
                    break
        
        # Si no se activó ningún stop, cerrar al final del período
        if exit_price is None:
            exit_price = df.iloc[-1]['Close']
            exit_date = df.index[-1]
            exit_reason = 'TIME_OUT'
        
        # Calcular P&L
        if signal['type'] == 'LONG':
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100
        
        trade = {
            'entry_date': entry_date,
            'exit_date': exit_date,
            'type': signal['type'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'pnl_pct': pnl_pct,
            'exit_reason': exit_reason,
            'regime': signal['regime'],
            'strategy': signal['strategy'],
            'confidence': signal['confidence'],
            'signals': signal['signals'][:3],  # Top 3 señales
            'risk': signal.get('risk', 0.01)
        }
        
        self.trades.append(trade)
        self.capital *= (1 + pnl_pct/100)
        
        return trade
    
    def run_backtest(self, start_date=None, end_date=None):
        """Ejecuta backtest detallado"""
        
        if start_date is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
        
        print(f"\n{'='*80}")
        print(f" BACKTEST DETALLADO V4.0: {self.symbol} ".center(80, '='))
        print(f"{'='*80}")
        print(f"Período: {start_date.date()} a {end_date.date()}")
        print(f"Capital inicial: ${self.initial_capital:,.2f}\n")
        
        # Obtener datos históricos
        ticker = yf.Ticker(self.symbol)
        df_1h = ticker.history(start=start_date, end=end_date, interval='1h')
        
        if len(df_1h) < 100:
            print(f"❌ Datos insuficientes para {self.symbol}")
            return None
        
        # Resample para 4H
        df_4h = df_1h.resample('4H').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        # Daily data
        df_daily = ticker.history(start=start_date, end=end_date, interval='1d')
        
        # Variables de control
        last_trade_idx = 0
        signals_generated = 0
        regime_changes = 0
        last_regime = None
        
        # Iterar por ventanas de tiempo
        for i in range(50, len(df_1h) - 1, 4):  # Cada 4 horas
            
            # Preparar datos para análisis
            current_1h = df_1h.iloc[:i+1]
            current_4h = df_4h[df_4h.index <= df_1h.index[i]]
            current_daily = df_daily[df_daily.index <= df_1h.index[i]]
            
            if len(current_4h) < 20 or len(current_daily) < 10:
                continue
            
            # Detectar régimen
            regime_info = MarketRegimeDetector.detect_regime(
                current_1h.tail(100), 
                current_4h.tail(50), 
                current_daily.tail(30)
            )
            
            current_regime = regime_info['regime']
            
            # Registrar cambio de régimen
            if last_regime and last_regime != current_regime:
                regime_changes += 1
                print(f"🔄 Cambio de régimen: {last_regime} → {current_regime} (en {df_1h.index[i].strftime('%Y-%m-%d %H:%M')})")
            
            last_regime = current_regime
            
            # Solo generar señal si no hay trade activo
            if i < last_trade_idx + 24:  # Esperar 24 horas entre trades
                continue
            
            # Generar señal adaptativa
            signal = self.adaptive_system.generate_adaptive_signal(
                current_1h.tail(100),
                current_4h.tail(50),
                current_daily.tail(30)
            )
            
            if signal and signal['confidence'] >= 0.5:
                signals_generated += 1
                
                # Registrar señal
                self.signals.append({
                    'date': df_1h.index[i],
                    'signal': signal
                })
                
                # Simular trade
                trade = self.simulate_trade(signal, df_1h, i)
                
                print(f"\n📊 Trade #{len(self.trades)}:")
                print(f"  Fecha: {trade['entry_date'].strftime('%Y-%m-%d %H:%M')}")
                print(f"  Régimen: {trade['regime']} | Estrategia: {trade['strategy']}")
                print(f"  Tipo: {trade['type']} | Confianza: {trade['confidence']:.1%}")
                print(f"  Entry: ${trade['entry_price']:.4f}")
                print(f"  Exit: ${trade['exit_price']:.4f} ({trade['exit_reason']})")
                print(f"  P&L: {trade['pnl_pct']:+.2f}%")
                print(f"  Señales: {', '.join(trade['signals'])}")
                
                last_trade_idx = i
        
        # Calcular estadísticas
        if self.trades:
            self.calculate_statistics()
        else:
            print("\n⚠️ No se generaron trades en el período")
        
        return self.trades
    
    def calculate_statistics(self):
        """Calcula estadísticas detalladas"""
        
        df_trades = pd.DataFrame(self.trades)
        
        total_trades = len(df_trades)
        winning_trades = df_trades[df_trades['pnl_pct'] > 0]
        losing_trades = df_trades[df_trades['pnl_pct'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        avg_win = winning_trades['pnl_pct'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl_pct'].mean() if len(losing_trades) > 0 else 0
        
        total_pnl = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        # Estadísticas por régimen
        regime_stats = df_trades.groupby('regime').agg({
            'pnl_pct': ['count', 'mean', 'sum'],
            'confidence': 'mean'
        })
        
        # Estadísticas por estrategia
        strategy_stats = df_trades.groupby('strategy').agg({
            'pnl_pct': ['count', 'mean', 'sum'],
            'confidence': 'mean'
        })
        
        # Estadísticas por tipo
        type_stats = df_trades.groupby('type').agg({
            'pnl_pct': ['count', 'mean', 'sum']
        })
        
        # Razones de salida
        exit_reasons = df_trades['exit_reason'].value_counts()
        
        print(f"\n{'='*80}")
        print(f" ESTADÍSTICAS FINALES ".center(80, '='))
        print(f"{'='*80}")
        
        print(f"\n📊 Resumen General:")
        print(f"  Total trades: {total_trades}")
        print(f"  Ganadores: {len(winning_trades)} ({win_rate:.1f}%)")
        print(f"  Perdedores: {len(losing_trades)} ({100-win_rate:.1f}%)")
        print(f"  Promedio ganancia: {avg_win:+.2f}%")
        print(f"  Promedio pérdida: {avg_loss:+.2f}%")
        print(f"  P&L Total: {total_pnl:+.2f}%")
        print(f"  Capital final: ${self.capital:,.2f}")
        
        if avg_loss != 0:
            profit_factor = abs(avg_win * len(winning_trades)) / abs(avg_loss * len(losing_trades)) if len(losing_trades) > 0 else 0
            print(f"  Profit Factor: {profit_factor:.2f}")
        
        print(f"\n📈 Por Régimen de Mercado:")
        for regime in regime_stats.index:
            count = regime_stats.loc[regime, ('pnl_pct', 'count')]
            avg_pnl = regime_stats.loc[regime, ('pnl_pct', 'mean')]
            total = regime_stats.loc[regime, ('pnl_pct', 'sum')]
            conf = regime_stats.loc[regime, ('confidence', 'mean')]
            print(f"  {regime}: {count} trades, Avg P&L: {avg_pnl:+.2f}%, Total: {total:+.2f}%, Conf: {conf:.1%}")
        
        print(f"\n🎯 Por Estrategia:")
        for strategy in strategy_stats.index:
            count = strategy_stats.loc[strategy, ('pnl_pct', 'count')]
            avg_pnl = strategy_stats.loc[strategy, ('pnl_pct', 'mean')]
            total = strategy_stats.loc[strategy, ('pnl_pct', 'sum')]
            print(f"  {strategy}: {count} trades, Avg P&L: {avg_pnl:+.2f}%, Total: {total:+.2f}%")
        
        print(f"\n🔄 Por Tipo de Operación:")
        for op_type in type_stats.index:
            count = type_stats.loc[op_type, ('pnl_pct', 'count')]
            avg_pnl = type_stats.loc[op_type, ('pnl_pct', 'mean')]
            print(f"  {op_type}: {count} trades, Avg P&L: {avg_pnl:+.2f}%")
        
        print(f"\n🚪 Razones de Salida:")
        for reason, count in exit_reasons.items():
            pct = count / total_trades * 100
            print(f"  {reason}: {count} ({pct:.1f}%)")
        
        # Análisis de trades ganadores vs perdedores
        print(f"\n✅ Top 3 Mejores Trades:")
        best_trades = df_trades.nlargest(3, 'pnl_pct')
        for idx, trade in best_trades.iterrows():
            print(f"  {trade['entry_date'].strftime('%m/%d')}: {trade['type']} {trade['regime']}/{trade['strategy']} → {trade['pnl_pct']:+.2f}%")
        
        print(f"\n❌ Top 3 Peores Trades:")
        worst_trades = df_trades.nsmallest(3, 'pnl_pct')
        for idx, trade in worst_trades.iterrows():
            print(f"  {trade['entry_date'].strftime('%m/%d')}: {trade['type']} {trade['regime']}/{trade['strategy']} → {trade['pnl_pct']:+.2f}%")
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pnl': total_pnl,
            'final_capital': self.capital
        }
    
    def save_report(self):
        """Guarda reporte detallado en archivo"""
        
        filename = f"backtest_v4_{self.symbol.replace('-USD', '').lower()}.md"
        
        with open(filename, 'w') as f:
            f.write(f"# 🤖 BACKTEST V4.0 ADAPTATIVO: {self.symbol}\n\n")
            f.write(f"**Sistema:** Trading Adaptativo V4.0\n")
            f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Capital Inicial:** ${self.initial_capital:,.2f}\n")
            f.write(f"**Capital Final:** ${self.capital:,.2f}\n\n")
            
            if self.trades:
                df_trades = pd.DataFrame(self.trades)
                
                f.write(f"## 📊 Resumen de Resultados\n\n")
                f.write(f"- **Total Trades:** {len(self.trades)}\n")
                f.write(f"- **Win Rate:** {len(df_trades[df_trades['pnl_pct'] > 0]) / len(df_trades) * 100:.1f}%\n")
                f.write(f"- **P&L Total:** {((self.capital - self.initial_capital) / self.initial_capital) * 100:+.2f}%\n\n")
                
                f.write(f"## 📝 Detalle de Trades\n\n")
                f.write(f"| # | Fecha | Régimen | Estrategia | Tipo | Entry | Exit | P&L% | Razón | Confianza | Señales |\n")
                f.write(f"|---|-------|---------|------------|------|-------|------|------|-------|-----------|---------|\n")
                
                for i, trade in enumerate(self.trades, 1):
                    f.write(f"| {i} | {trade['entry_date'].strftime('%m/%d %H:%M')} | ")
                    f.write(f"{trade['regime']} | {trade['strategy']} | {trade['type']} | ")
                    f.write(f"${trade['entry_price']:.4f} | ${trade['exit_price']:.4f} | ")
                    f.write(f"{trade['pnl_pct']:+.2f}% | {trade['exit_reason']} | ")
                    f.write(f"{trade['confidence']:.1%} | {', '.join(trade['signals'][:2])} |\n")
            else:
                f.write(f"## ⚠️ No se generaron trades\n")
        
        print(f"\n💾 Reporte guardado en: {filename}")


def run_all_backtests():
    """Ejecuta backtests para todos los símbolos"""
    
    symbols = [
        'ADA-USD', 'XRP-USD', 'DOGE-USD', 
        'AVAX-USD', 'SOL-USD', 'LINK-USD', 'DOT-USD'
    ]
    
    results = {}
    
    print("\n" + "="*80)
    print(" INICIANDO BACKTESTS V4.0 ADAPTATIVOS ".center(80, "="))
    print("="*80)
    
    for symbol in symbols:
        try:
            backtest = DetailedBacktestV4(symbol, initial_capital=206)
            trades = backtest.run_backtest()
            
            if trades:
                stats = {
                    'trades': len(trades),
                    'win_rate': len([t for t in trades if t['pnl_pct'] > 0]) / len(trades) * 100,
                    'total_pnl': ((backtest.capital - backtest.initial_capital) / backtest.initial_capital) * 100,
                    'final_capital': backtest.capital
                }
                results[symbol] = stats
                
                # Guardar reporte individual
                backtest.save_report()
            else:
                results[symbol] = {
                    'trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'final_capital': 206
                }
            
            print("\n" + "-"*80 + "\n")
            
        except Exception as e:
            print(f"❌ Error en {symbol}: {e}")
            results[symbol] = None
    
    # Resumen final
    print("\n" + "="*80)
    print(" RESUMEN FINAL DE TODOS LOS SÍMBOLOS ".center(80, "="))
    print("="*80 + "\n")
    
    print("| Símbolo | Trades | Win Rate | P&L Total | Capital Final |")
    print("|---------|--------|----------|-----------|---------------|")
    
    total_pnl = 0
    total_trades = 0
    
    for symbol, stats in results.items():
        if stats:
            print(f"| {symbol.replace('-USD', ''):8} | {stats['trades']:6} | {stats['win_rate']:7.1f}% | {stats['total_pnl']:+8.2f}% | ${stats['final_capital']:10.2f} |")
            total_pnl += stats['total_pnl']
            total_trades += stats['trades']
    
    avg_pnl = total_pnl / len([r for r in results.values() if r])
    print(f"\n📊 Promedio P&L: {avg_pnl:+.2f}%")
    print(f"📊 Total Trades: {total_trades}")
    
    # Guardar resumen general
    with open('backtest_v4_summary.md', 'w') as f:
        f.write(f"# 📊 RESUMEN BACKTEST V4.0 ADAPTATIVO\n\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Sistema:** Trading Adaptativo con Detección de Régimen\n\n")
        
        f.write(f"## Resultados por Símbolo\n\n")
        f.write(f"| Símbolo | Trades | Win Rate | P&L Total | Capital Final |\n")
        f.write(f"|---------|--------|----------|-----------|---------------|\n")
        
        for symbol, stats in results.items():
            if stats:
                f.write(f"| {symbol} | {stats['trades']} | {stats['win_rate']:.1f}% | {stats['total_pnl']:+.2f}% | ${stats['final_capital']:.2f} |\n")
        
        f.write(f"\n## Estadísticas Globales\n\n")
        f.write(f"- **Total Trades:** {total_trades}\n")
        f.write(f"- **Promedio P&L:** {avg_pnl:+.2f}%\n")
    
    print(f"\n✅ Backtests completados. Resumen guardado en backtest_v4_summary.md")


if __name__ == "__main__":
    run_all_backtests()