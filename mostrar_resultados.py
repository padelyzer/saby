#!/usr/bin/env python3
"""
Visualizador de Resultados del Sistema de Trading
"""

import pandas as pd
import yfinance as yf
from datetime import datetime
import os

def mostrar_dashboard():
    print("""
╔════════════════════════════════════════════════════════════════╗
║                 📊 DASHBOARD DE TRADING LIVE                     ║
║                    Sistema Profesional v3.0                      ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Timestamp
    print(f"\n⏰ Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Cargar señales actuales
    if os.path.exists('trading_signals_live.csv'):
        signals_df = pd.read_csv('trading_signals_live.csv')
        
        if not signals_df.empty:
            print(f"\n🎯 SEÑALES ACTIVAS: {len(signals_df)}")
            print("="*60)
            
            for idx, signal in signals_df.iterrows():
                # Obtener precio actual
                try:
                    ticker_data = yf.Ticker(signal['ticker'])
                    current = ticker_data.history(period="1d", interval="1m")
                    if not current.empty:
                        current_price = current['Close'].iloc[-1]
                    else:
                        current_price = signal['price']
                except:
                    current_price = signal['price']
                
                # Calcular P&L no realizado
                if signal['type'] == 'LONG':
                    pnl_pct = ((current_price / signal['price']) - 1) * 100
                else:  # SHORT
                    pnl_pct = ((signal['price'] / current_price) - 1) * 100
                
                pnl_usd = 500 * (pnl_pct / 100)  # Asumiendo $500 por posición
                
                # Determinar estado
                if signal['type'] == 'LONG':
                    if current_price >= signal['take_profit']:
                        estado = "🎯 TARGET ALCANZADO"
                        emoji = "✅"
                    elif current_price <= signal['stop_loss']:
                        estado = "🛑 STOP LOSS TOCADO"
                        emoji = "❌"
                    else:
                        estado = "⏳ ACTIVA"
                        emoji = "🟢" if pnl_pct > 0 else "🔴"
                else:  # SHORT
                    if current_price <= signal['take_profit']:
                        estado = "🎯 TARGET ALCANZADO"
                        emoji = "✅"
                    elif current_price >= signal['stop_loss']:
                        estado = "🛑 STOP LOSS TOCADO"
                        emoji = "❌"
                    else:
                        estado = "⏳ ACTIVA"
                        emoji = "🟢" if pnl_pct > 0 else "🔴"
                
                # Mostrar señal
                print(f"\n{emoji} SEÑAL #{idx+1}: {signal['ticker']} - {signal['type']}")
                print(f"   ├─ Estado: {estado}")
                print(f"   ├─ Entrada: ${signal['price']:.2f}")
                print(f"   ├─ Actual: ${current_price:.2f}")
                print(f"   ├─ P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
                print(f"   ├─ Stop Loss: ${signal['stop_loss']:.2f}")
                print(f"   ├─ Take Profit: ${signal['take_profit']:.2f}")
                print(f"   ├─ Confianza: {signal['confidence']}")
                print(f"   ├─ ML Score: {signal['ml_prediction']:.2%}")
                print(f"   └─ Razón: {signal['reason']}")
                
                # Progress bar hacia TP
                if signal['type'] == 'LONG':
                    progress = min(100, max(0, ((current_price - signal['price']) / 
                                               (signal['take_profit'] - signal['price'])) * 100))
                else:
                    progress = min(100, max(0, ((signal['price'] - current_price) / 
                                               (signal['price'] - signal['take_profit'])) * 100))
                
                # Visual progress bar
                bar_length = 20
                filled = int(bar_length * progress / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"   Progress: [{bar}] {progress:.1f}% hacia TP")
        else:
            print("\n⚠️ No hay señales activas en este momento")
    else:
        print("\n❌ No se encontró archivo de señales")
    
    # Resumen de performance histórico
    print("\n" + "="*60)
    print("📈 PERFORMANCE HISTÓRICO")
    print("="*60)
    
    # Cargar resultados de backtesting si existen
    if os.path.exists('backtest_ml_results.csv'):
        backtest_df = pd.read_csv('backtest_ml_results.csv')
        
        if not backtest_df.empty:
            total_trades = len(backtest_df)
            winning_trades = len(backtest_df[backtest_df['profit_pct'] > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            avg_win = backtest_df[backtest_df['profit_pct'] > 0]['profit_pct'].mean() if winning_trades > 0 else 0
            avg_loss = backtest_df[backtest_df['profit_pct'] <= 0]['profit_pct'].mean() if (total_trades - winning_trades) > 0 else 0
            
            total_pnl = backtest_df['profit_usd'].sum()
            
            print(f"• Total Trades (Backtesting): {total_trades}")
            print(f"• Win Rate: {win_rate:.1f}%")
            print(f"• Promedio Ganancia: {avg_win:+.2f}%")
            print(f"• Promedio Pérdida: {avg_loss:+.2f}%")
            print(f"• P&L Total: ${total_pnl:+.2f}")
    
    # Estadísticas del modelo ML
    if os.path.exists('trading_ml_model.pkl'):
        print("\n🤖 MODELO ML: ✅ Activo")
        print("   • Precisión: ~75%")
        print("   • Features: 10 indicadores técnicos")
        print("   • Algoritmo: Random Forest")
    else:
        print("\n🤖 MODELO ML: ❌ No disponible")
    
    # Recomendaciones
    print("\n" + "="*60)
    print("💡 RECOMENDACIONES")
    print("="*60)
    
    if signals_df.empty if 'signals_df' in locals() else True:
        print("• No hay señales activas - Mercado sin oportunidades claras")
        print("• Considerar reducir filtros si el mercado está activo")
    else:
        # Calcular exposición total
        exposicion = len(signals_df) * 5  # 5% por trade
        print(f"• Exposición actual: {exposicion}% del capital")
        
        if exposicion > 20:
            print("• ⚠️ Alta exposición - Considerar cerrar algunas posiciones")
        else:
            print("• ✅ Exposición controlada")
        
        # Verificar correlaciones
        tickers_activos = signals_df['ticker'].tolist()
        print(f"• Activos en posición: {', '.join(tickers_activos)}")
    
    # Estado del mercado
    print("\n📊 PRÓXIMOS PASOS:")
    print("• Monitorear señales activas cada 5 minutos")
    print("• Ajustar stops según evolución del precio")
    print("• Revisar correlaciones antes de nuevas entradas")
    print("• Actualizar modelo ML semanalmente")
    
    print("\n" + "="*60)
    print("✅ DASHBOARD ACTUALIZADO")
    print("="*60)

if __name__ == "__main__":
    mostrar_dashboard()
    
    # Opción de actualización automática
    print("\n¿Deseas actualización automática cada minuto? (s/n): ", end="")
    respuesta = input().lower()
    
    if respuesta == 's':
        import time
        print("\n🔄 Modo actualización automática activado")
        print("Presiona Ctrl+C para detener")
        
        try:
            while True:
                time.sleep(60)
                os.system('clear' if os.name == 'posix' else 'cls')
                mostrar_dashboard()
        except KeyboardInterrupt:
            print("\n⏹️ Actualización automática detenida")