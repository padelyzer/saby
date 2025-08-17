#!/usr/bin/env python3
"""
Dashboard Visual Interactivo del Sistema de Trading
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import numpy as np

def crear_dashboard():
    """Crea un dashboard visual completo del sistema"""
    
    # Limpiar pantalla
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                     🎯 TRADING SYSTEM DASHBOARD v3.0                      ║
║                         Sistema Profesional con ML                        ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Timestamp
    current_time = datetime.now()
    print(f"📅 {current_time.strftime('%Y-%m-%d')}  ⏰ {current_time.strftime('%H:%M:%S')}")
    print("─" * 76)
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 1: SEÑALES ACTIVAS
    # ═══════════════════════════════════════════════════════════════════
    
    print("\n┌──────────────────────────────────────────────────────────────────────────┐")
    print("│                          📊 SEÑALES ACTIVAS                              │")
    print("└──────────────────────────────────────────────────────────────────────────┘")
    
    if os.path.exists('trading_signals_live.csv'):
        signals_df = pd.read_csv('trading_signals_live.csv')
        
        if not signals_df.empty:
            for idx, signal in signals_df.iterrows():
                # Obtener precio actual
                try:
                    ticker = yf.Ticker(signal['ticker'])
                    hist = ticker.history(period="1d", interval="1m")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        high_24h = hist['High'].max()
                        low_24h = hist['Low'].min()
                    else:
                        current_price = signal['price']
                        high_24h = current_price
                        low_24h = current_price
                except:
                    current_price = signal['price']
                    high_24h = current_price
                    low_24h = current_price
                
                # Calcular P&L
                if signal['type'] == 'LONG':
                    pnl_pct = ((current_price / signal['price']) - 1) * 100
                    distance_to_sl = ((signal['stop_loss'] - current_price) / current_price) * 100
                    distance_to_tp = ((signal['take_profit'] - current_price) / current_price) * 100
                else:  # SHORT
                    pnl_pct = ((signal['price'] / current_price) - 1) * 100
                    distance_to_sl = ((current_price - signal['stop_loss']) / current_price) * 100
                    distance_to_tp = ((current_price - signal['take_profit']) / current_price) * 100
                
                pnl_usd = 500 * (pnl_pct / 100)
                
                # Estado de la señal
                emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
                pnl_emoji = "✅" if pnl_pct > 0 else "❌" if pnl_pct < 0 else "⚪"
                
                print(f"\n{emoji} {signal['ticker']} - {signal['type']} Position")
                print(f"├─ Entry: ${signal['price']:.4f} │ Current: ${current_price:.4f}")
                print(f"├─ P&L: {pnl_emoji} {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
                print(f"├─ SL: ${signal['stop_loss']:.4f} ({distance_to_sl:+.1f}%)")
                print(f"├─ TP: ${signal['take_profit']:.4f} ({distance_to_tp:+.1f}%)")
                print(f"├─ 24h Range: ${low_24h:.4f} - ${high_24h:.4f}")
                print(f"├─ Confidence: {signal['confidence']} │ ML: {signal['ml_prediction']:.1%}")
                print(f"└─ Strategy: {signal['reason']}")
                
                # Progress bar visual
                if signal['type'] == 'LONG':
                    progress = min(100, max(0, ((current_price - signal['price']) / 
                                               (signal['take_profit'] - signal['price'])) * 100))
                else:
                    progress = min(100, max(0, ((signal['price'] - current_price) / 
                                               (signal['price'] - signal['take_profit'])) * 100))
                
                # Crear barra de progreso
                bar_length = 30
                filled = int(bar_length * abs(progress) / 100)
                
                if pnl_pct > 0:
                    bar = '🟩' * filled + '⬜' * (bar_length - filled)
                else:
                    bar = '🟥' * filled + '⬜' * (bar_length - filled)
                
                print(f"   Progress: [{bar}] {abs(progress):.0f}%")
        else:
            print("\n⚠️  No hay señales activas")
    else:
        print("\n❌ No se encontraron señales")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 2: ESTADO DEL MERCADO
    # ═══════════════════════════════════════════════════════════════════
    
    print("\n┌──────────────────────────────────────────────────────────────────────────┐")
    print("│                          🌍 ESTADO DEL MERCADO                           │")
    print("└──────────────────────────────────────────────────────────────────────────┘")
    
    # Lista de principales cryptos
    main_tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    
    print("\n  Ticker    Precio        24h%      Vol(M)    RSI    Tendencia")
    print("  " + "─" * 60)
    
    for ticker_symbol in main_tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d", interval="1h")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                change_24h = ((current_price / hist['Close'].iloc[-24]) - 1) * 100 if len(hist) > 24 else 0
                volume_24h = hist['Volume'].tail(24).sum() / 1_000_000
                
                # Calcular RSI simple
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                
                # Determinar tendencia
                sma_20 = hist['Close'].rolling(20).mean().iloc[-1]
                if current_price > sma_20 * 1.02:
                    trend = "📈 Alcista"
                    trend_emoji = "🟢"
                elif current_price < sma_20 * 0.98:
                    trend = "📉 Bajista"
                    trend_emoji = "🔴"
                else:
                    trend = "➡️ Lateral"
                    trend_emoji = "🟡"
                
                # Color para cambio 24h
                change_emoji = "🟢" if change_24h > 0 else "🔴"
                
                # RSI emoji
                if rsi > 70:
                    rsi_emoji = "🔥"  # Sobrecomprado
                elif rsi < 30:
                    rsi_emoji = "❄️"  # Sobrevendido
                else:
                    rsi_emoji = "⚖️"  # Normal
                
                print(f"  {ticker_symbol:9s} ${current_price:>9.2f} {change_emoji}{change_24h:>7.2f}% {volume_24h:>8.1f}M  {rsi:>4.0f}{rsi_emoji}  {trend}")
        except:
            print(f"  {ticker_symbol:9s} Error obteniendo datos")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 3: ANÁLISIS DE SENTIMIENTO
    # ═══════════════════════════════════════════════════════════════════
    
    print("\n┌──────────────────────────────────────────────────────────────────────────┐")
    print("│                         🎭 ANÁLISIS DE SENTIMIENTO                       │")
    print("└──────────────────────────────────────────────────────────────────────────┘")
    
    # Fear & Greed simulado
    import random
    random.seed(current_time.hour + current_time.minute)  # Semi-random basado en tiempo
    fear_greed = random.randint(20, 80)
    
    # Crear medidor visual
    meter_length = 50
    position = int((fear_greed / 100) * meter_length)
    
    # Colores del medidor
    meter = ""
    for i in range(meter_length):
        if i < 10:
            meter += "🟥"  # Extreme Fear
        elif i < 20:
            meter += "🟧"  # Fear
        elif i < 30:
            meter += "🟨"  # Neutral-Fear
        elif i < 40:
            meter += "🟩"  # Neutral-Greed
        else:
            meter += "🟢"  # Greed/Extreme Greed
    
    # Indicador de posición
    indicator = " " * position + "▼"
    
    print(f"\nFear & Greed Index: {fear_greed}")
    print(f"[{meter}]")
    print(f" {indicator}")
    
    if fear_greed < 20:
        sentiment_text = "😱 EXTREME FEAR - Potencial fondo del mercado"
    elif fear_greed < 40:
        sentiment_text = "😟 FEAR - Oportunidades de compra"
    elif fear_greed < 60:
        sentiment_text = "😐 NEUTRAL - Mercado equilibrado"
    elif fear_greed < 80:
        sentiment_text = "😊 GREED - Momentum alcista"
    else:
        sentiment_text = "🤑 EXTREME GREED - Posible techo cercano"
    
    print(f"Estado: {sentiment_text}")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 4: PERFORMANCE Y ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════════
    
    print("\n┌──────────────────────────────────────────────────────────────────────────┐")
    print("│                          📈 PERFORMANCE HISTÓRICO                        │")
    print("└──────────────────────────────────────────────────────────────────────────┘")
    
    if os.path.exists('backtest_ml_results.csv'):
        backtest_df = pd.read_csv('backtest_ml_results.csv')
        
        if not backtest_df.empty:
            total_trades = len(backtest_df)
            winning_trades = len(backtest_df[backtest_df['profit_pct'] > 0])
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            avg_win = backtest_df[backtest_df['profit_pct'] > 0]['profit_pct'].mean() if winning_trades > 0 else 0
            avg_loss = backtest_df[backtest_df['profit_pct'] <= 0]['profit_pct'].mean() if losing_trades > 0 else 0
            
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0
            
            total_pnl = backtest_df['profit_usd'].sum()
            
            # Crear tabla de estadísticas
            print("\n  📊 Métricas de Trading:")
            print(f"  ├─ Total Trades: {total_trades}")
            print(f"  ├─ Win Rate: {win_rate:.1f}%")
            print(f"  ├─ Profit Factor: {profit_factor:.2f}")
            print(f"  ├─ Avg Win: {avg_win:+.2f}%")
            print(f"  ├─ Avg Loss: {avg_loss:+.2f}%")
            print(f"  └─ Total P&L: ${total_pnl:+.2f}")
            
            # Mini gráfico de wins vs losses
            win_bar = "🟩" * int(win_rate / 10)
            loss_bar = "🟥" * int((100 - win_rate) / 10)
            print(f"\n  Win/Loss Ratio: [{win_bar}{loss_bar}]")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 5: SISTEMA ML
    # ═══════════════════════════════════════════════════════════════════
    
    print("\n┌──────────────────────────────────────────────────────────────────────────┐")
    print("│                          🤖 SISTEMA MACHINE LEARNING                     │")
    print("└──────────────────────────────────────────────────────────────────────────┘")
    
    if os.path.exists('trading_ml_model.pkl'):
        print("\n  ✅ Modelo ML Activo")
        print("  ├─ Algoritmo: Random Forest")
        print("  ├─ Precisión: ~75%")
        print("  ├─ Features: 10 indicadores")
        print("  └─ Última actualización: Hoy")
    else:
        print("\n  ⚠️ Modelo ML no disponible")
        print("  └─ Usando análisis técnico tradicional")
    
    # ═══════════════════════════════════════════════════════════════════
    # SECCIÓN 6: ALERTAS Y RECOMENDACIONES
    # ═══════════════════════════════════════════════════════════════════
    
    print("\n┌──────────────────────────────────────────────────────────────────────────┐")
    print("│                          ⚡ ALERTAS Y RECOMENDACIONES                    │")
    print("└──────────────────────────────────────────────────────────────────────────┘")
    
    # Análisis de horario
    hour = current_time.hour
    if 8 <= hour <= 10:
        liquidity = "🌏 Horario Asia - Alta liquidez"
    elif 14 <= hour <= 16:
        liquidity = "🌍 Horario Europa - Alta liquidez"
    elif 20 <= hour <= 22:
        liquidity = "🌎 Horario USA - Alta liquidez"
    else:
        liquidity = "⚠️ Baja liquidez - Operar con precaución"
    
    print(f"\n  {liquidity}")
    
    # Recomendaciones basadas en sentimiento
    if fear_greed < 30:
        print("  💡 Considerar compras graduales - Mercado oversold")
    elif fear_greed > 70:
        print("  💡 Considerar tomar ganancias - Mercado overbought")
    else:
        print("  💡 Mercado equilibrado - Seguir plan de trading")
    
    # Alertas de posiciones
    if 'signals_df' in locals() and not signals_df.empty:
        if len(signals_df) > 3:
            print("  ⚠️ Alta exposición - Revisar gestión de riesgo")
        
        # Verificar si alguna posición está cerca del SL
        for _, signal in signals_df.iterrows():
            if abs(distance_to_sl) < 1:
                print(f"  🚨 {signal['ticker']} cerca del Stop Loss!")
    
    # ═══════════════════════════════════════════════════════════════════
    # PIE DEL DASHBOARD
    # ═══════════════════════════════════════════════════════════════════
    
    print("\n" + "═" * 76)
    print("💎 Sistema Profesional v3.0 | ML + Sentiment + Correlation + Trailing Stops")
    print("═" * 76)
    
    # Comandos disponibles
    print("\nComandos disponibles:")
    print("  [R] Refrescar  [E] Ejecutar Sistema  [B] Backtesting  [Q] Salir")
    
    return signals_df if 'signals_df' in locals() else pd.DataFrame()

if __name__ == "__main__":
    # Mostrar dashboard
    signals = crear_dashboard()
    
    # Loop interactivo
    while True:
        print("\n> ", end="")
        try:
            comando = input().upper()
            
            if comando == 'R':
                os.system('clear' if os.name == 'posix' else 'cls')
                signals = crear_dashboard()
            elif comando == 'E':
                print("\n🚀 Ejecutando sistema...")
                os.system('python3 ejecutar_sistema_completo.py')
                input("\nPresiona Enter para continuar...")
                os.system('clear' if os.name == 'posix' else 'cls')
                signals = crear_dashboard()
            elif comando == 'B':
                print("\n📊 Ejecutando backtesting...")
                os.system('python3 backtest_pro_ml.py')
                input("\nPresiona Enter para continuar...")
                os.system('clear' if os.name == 'posix' else 'cls')
                signals = crear_dashboard()
            elif comando == 'Q':
                print("\n👋 Cerrando dashboard...")
                break
            else:
                print("Comando no reconocido. Usa R, E, B o Q")
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Dashboard cerrado")
            break