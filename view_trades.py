#!/usr/bin/env python3
"""
Visualizador de Trades y Performance
Muestra todos los trades activos y completados con estadísticas
"""

import json
import os
import pandas as pd
from datetime import datetime
from trade_tracker import TradeTracker
import yfinance as yf

def show_trades():
    """Muestra todos los trades y estadísticas"""
    tracker = TradeTracker()
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║                    📊 SISTEMA DE TRACKING DE TRADES             ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # 1. Trades Activos
    print("\n🔴 TRADES ACTIVOS:")
    print("=" * 70)
    
    if tracker.active_trades:
        for trade_id, trade in tracker.active_trades.items():
            # Obtener precio actual
            try:
                ticker = yf.Ticker(trade['ticker'])
                data = ticker.history(period='1d', interval='1m')
                if not data.empty:
                    current_price = float(data['Close'].iloc[-1])
                    
                    # Calcular PnL actual
                    if trade['direction'] == 'LONG':
                        pnl_pct = ((current_price - trade['entry_price']) / trade['entry_price']) * 100
                    else:  # SHORT
                        pnl_pct = ((trade['entry_price'] - current_price) / trade['entry_price']) * 100
                    
                    pnl_pct_leveraged = pnl_pct * trade['leverage']
                    
                    # Mostrar info
                    emoji = "🟢" if pnl_pct_leveraged > 0 else "🔴" if pnl_pct_leveraged < 0 else "⚪"
                    
                    print(f"\n{emoji} {trade['ticker']} - {trade['direction']}")
                    print(f"   Entry: ${trade['entry_price']:.2f} → Current: ${current_price:.2f}")
                    print(f"   SL: ${trade['stop_loss']:.2f} | TP: ${trade['take_profit']:.2f}")
                    print(f"   PnL: {pnl_pct_leveraged:+.2f}% (Leverage: {trade['leverage']}x)")
                    print(f"   Score: {trade['score']:.1f} | Size: {trade['position_size_pct']}%")
                    
                    # Calcular distancia a SL/TP
                    if trade['direction'] == 'LONG':
                        dist_to_sl = ((current_price - trade['stop_loss']) / current_price) * 100
                        dist_to_tp = ((trade['take_profit'] - current_price) / current_price) * 100
                    else:
                        dist_to_sl = ((trade['stop_loss'] - current_price) / current_price) * 100
                        dist_to_tp = ((current_price - trade['take_profit']) / current_price) * 100
                    
                    print(f"   Distancia: SL {dist_to_sl:.1f}% | TP {dist_to_tp:.1f}%")
                    
                    # Tiempo en trade
                    open_time = datetime.fromisoformat(trade['timestamp_open'])
                    duration = (datetime.now() - open_time).total_seconds() / 3600
                    print(f"   Duración: {duration:.1f} horas")
                    
            except Exception as e:
                print(f"\n❌ Error obteniendo datos para {trade['ticker']}: {e}")
    else:
        print("   No hay trades activos")
    
    # 2. Historial de Trades
    print("\n\n📈 HISTORIAL DE TRADES CERRADOS:")
    print("=" * 70)
    
    if os.path.exists('trade_results.csv'):
        df = pd.read_csv('trade_results.csv')
        
        if not df.empty:
            # Mostrar últimos 10 trades
            recent_trades = df.tail(10)
            
            for _, trade in recent_trades.iterrows():
                emoji = "✅" if trade['PnL_Percent'] > 0 else "❌"
                result_emoji = "🎯" if trade['Result'] == 'TAKE_PROFIT' else "🛑" if trade['Result'] == 'STOP_LOSS' else "🔧"
                
                print(f"\n{emoji} {trade['Ticker']} - {trade['Direction']}")
                print(f"   {result_emoji} {trade['Result']}")
                print(f"   Entry: ${trade['Entry_Price']:.2f} → Exit: ${trade['Exit_Price']:.2f}")
                print(f"   PnL: {trade['PnL_Percent']:.2f}% (${trade['PnL_USD']:.2f})")
                print(f"   Duración: {trade['Duration_Hours']:.1f} horas")
        else:
            print("   No hay trades cerrados aún")
    else:
        print("   No hay historial de trades")
    
    # 3. Estadísticas Generales
    print("\n\n📊 ESTADÍSTICAS GENERALES:")
    print("=" * 70)
    
    stats = tracker.get_statistics()
    
    if stats:
        print(f"📈 Total Trades: {stats.get('total_trades', 0)}")
        print(f"🔄 Trades Activos: {stats.get('active_trades', 0)}")
        print(f"✅ Ganadores: {stats.get('winning_trades', 0)}")
        print(f"❌ Perdedores: {stats.get('losing_trades', 0)}")
        print(f"🎯 Win Rate: {stats.get('win_rate', 0):.1f}%")
        print(f"💰 PnL Total: ${stats.get('total_pnl', 0):.2f}")
        print(f"📊 Profit Factor: {stats.get('profit_factor', 0):.2f}")
        print(f"⏱️ Duración Promedio: {stats.get('avg_duration', 0):.1f} horas")
        print(f"🚀 Mejor Trade: {stats.get('best_trade', 0):+.2f}%")
        print(f"💥 Peor Trade: {stats.get('worst_trade', 0):+.2f}%")
        
        # Expectativa matemática
        if stats.get('winning_trades', 0) > 0 and stats.get('losing_trades', 0) > 0:
            expectancy = (
                (stats['win_rate'] / 100 * stats['avg_win']) +
                ((100 - stats['win_rate']) / 100 * stats['avg_loss'])
            )
            print(f"🎲 Expectativa: {expectancy:.2f}% por trade")
    else:
        print("   No hay estadísticas disponibles aún")
    
    print("""
════════════════════════════════════════════════════════════════
💡 Tips:
   • Los trades se actualizan automáticamente cada minuto
   • El sistema cierra trades cuando alcanzan SL o TP
   • Todos los resultados se guardan en trade_results.csv
════════════════════════════════════════════════════════════════
""")

def monitor_live():
    """Monitorea trades en tiempo real"""
    import time
    
    print("🔄 Monitoreando trades en vivo (Ctrl+C para salir)...")
    print("=" * 70)
    
    tracker = TradeTracker()
    tracker.start_monitoring()
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            show_trades()
            time.sleep(30)  # Actualizar cada 30 segundos
    except KeyboardInterrupt:
        print("\n🛑 Monitoreo detenido")
        tracker.stop_monitoring()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'live':
        monitor_live()
    else:
        show_trades()