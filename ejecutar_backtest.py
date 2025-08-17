#!/usr/bin/env python3
"""
Ejecutar sistema de backtesting con datos reales
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def run_simple_backtest():
    """
    Ejecuta un backtesting simplificado con datos reales
    """
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║              SISTEMA DE BACKTESTING EN EJECUCIÓN                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Configuración
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD']
    capital_inicial = 10000
    position_size = 0.15  # 15% por trade
    
    # Período de backtesting
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"📊 Configuración:")
    print(f"• Capital Inicial: ${capital_inicial:,}")
    print(f"• Tickers: {tickers}")
    print(f"• Período: {start_date.date()} a {end_date.date()}")
    print(f"• Tamaño Posición: {position_size*100}%")
    print("="*60)
    
    # Descargar datos
    print("\n📥 Descargando datos...")
    all_data = {}
    
    for ticker in tickers:
        try:
            print(f"   Descargando {ticker}...")
            # Descargar datos sin multiindex
            data = yf.Ticker(ticker)
            df = data.history(period="1mo", interval="1h")
            
            if not df.empty:
                # Calcular indicadores básicos
                df['SMA_20'] = df['Close'].rolling(20).mean()
                df['SMA_50'] = df['Close'].rolling(50).mean()
                
                # RSI
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
                # Bollinger Bands
                df['BB_Middle'] = df['Close'].rolling(20).mean()
                bb_std = df['Close'].rolling(20).std()
                df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
                df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
                
                all_data[ticker] = df
                print(f"   ✅ {ticker}: {len(df)} barras")
        except Exception as e:
            print(f"   ❌ Error con {ticker}: {e}")
    
    if not all_data:
        print("❌ No se pudieron obtener datos")
        return
    
    print(f"\n✅ Datos obtenidos para {len(all_data)} tickers")
    
    # Simular estrategias simples
    print("\n🎯 Ejecutando estrategias...")
    trades = []
    capital = capital_inicial
    
    for ticker, df in all_data.items():
        if len(df) < 50:
            continue
        
        print(f"\n📈 Analizando {ticker}...")
        
        # Estrategia 1: Momentum (Cruce de medias)
        for i in range(50, len(df)-1):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Señal LONG: SMA20 cruza SMA50 al alza
            if (prev_row['SMA_20'] <= prev_row['SMA_50'] and 
                current_row['SMA_20'] > current_row['SMA_50'] and
                current_row['RSI'] < 70):
                
                entry_price = current_row['Close']
                take_profit = entry_price * 1.03  # 3%
                stop_loss = entry_price * 0.98    # 2%
                
                # Simular salida
                exit_price = None
                exit_reason = None
                
                for j in range(i+1, min(i+50, len(df))):
                    future_row = df.iloc[j]
                    
                    if future_row['High'] >= take_profit:
                        exit_price = take_profit
                        exit_reason = 'TP'
                        break
                    elif future_row['Low'] <= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'SL'
                        break
                
                if not exit_price and i+10 < len(df):
                    exit_price = df.iloc[i+10]['Close']
                    exit_reason = 'TIME'
                
                if exit_price:
                    profit_pct = ((exit_price - entry_price) / entry_price) * 100
                    profit_usd = capital * position_size * (profit_pct / 100)
                    
                    trades.append({
                        'ticker': ticker,
                        'strategy': 'Momentum',
                        'entry_date': df.index[i],
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'profit_pct': profit_pct,
                        'profit_usd': profit_usd,
                        'exit_reason': exit_reason
                    })
                    
                    capital += profit_usd
                    
                    emoji = "✅" if profit_pct > 0 else "❌"
                    print(f"   {emoji} Trade: {profit_pct:+.2f}% | ${profit_usd:+.2f} | {exit_reason}")
                    
                    # Saltar para evitar múltiples entradas
                    i += 10
        
        # Estrategia 2: Mean Reversion (Bollinger Bands)
        for i in range(50, len(df)-1):
            current_row = df.iloc[i]
            
            # Señal LONG: Precio toca banda inferior
            if (current_row['Close'] <= current_row['BB_Lower'] and 
                current_row['RSI'] < 35):
                
                entry_price = current_row['Close']
                take_profit = current_row['BB_Middle']  # Target: media
                stop_loss = entry_price * 0.97          # 3% stop
                
                # Simular salida
                exit_price = None
                exit_reason = None
                
                for j in range(i+1, min(i+20, len(df))):
                    future_row = df.iloc[j]
                    
                    if future_row['High'] >= take_profit:
                        exit_price = take_profit
                        exit_reason = 'TP'
                        break
                    elif future_row['Low'] <= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'SL'
                        break
                
                if not exit_price and i+5 < len(df):
                    exit_price = df.iloc[i+5]['Close']
                    exit_reason = 'TIME'
                
                if exit_price:
                    profit_pct = ((exit_price - entry_price) / entry_price) * 100
                    profit_usd = capital * position_size * (profit_pct / 100)
                    
                    trades.append({
                        'ticker': ticker,
                        'strategy': 'Mean Reversion',
                        'entry_date': df.index[i],
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'profit_pct': profit_pct,
                        'profit_usd': profit_usd,
                        'exit_reason': exit_reason
                    })
                    
                    capital += profit_usd
                    
                    emoji = "✅" if profit_pct > 0 else "❌"
                    print(f"   {emoji} Trade: {profit_pct:+.2f}% | ${profit_usd:+.2f} | {exit_reason}")
                    
                    # Saltar para evitar múltiples entradas
                    i += 5
    
    # Mostrar resultados finales
    print("\n" + "="*60)
    print("📊 RESULTADOS DEL BACKTESTING")
    print("="*60)
    
    total_trades = len(trades)
    if total_trades > 0:
        winning_trades = [t for t in trades if t['profit_pct'] > 0]
        losing_trades = [t for t in trades if t['profit_pct'] <= 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100
        total_return = ((capital / capital_inicial) - 1) * 100
        
        avg_win = np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Profit Factor
        gross_profit = sum(t['profit_usd'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['profit_usd'] for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        print(f"\n💰 CAPITAL:")
        print(f"• Inicial: ${capital_inicial:,.2f}")
        print(f"• Final: ${capital:,.2f}")
        print(f"• Retorno: {total_return:+.2f}%")
        
        print(f"\n📈 MÉTRICAS:")
        print(f"• Total Trades: {total_trades}")
        print(f"• Trades Ganadores: {len(winning_trades)}")
        print(f"• Trades Perdedores: {len(losing_trades)}")
        print(f"• Win Rate: {win_rate:.1f}%")
        print(f"• Profit Factor: {profit_factor:.2f}")
        
        print(f"\n🎯 ANÁLISIS:")
        print(f"• Promedio Ganancia: {avg_win:+.2f}%")
        print(f"• Promedio Pérdida: {avg_loss:+.2f}%")
        
        if trades:
            best_trade = max(trades, key=lambda t: t['profit_pct'])
            worst_trade = min(trades, key=lambda t: t['profit_pct'])
            print(f"• Mejor Trade: {best_trade['ticker']} {best_trade['profit_pct']:+.2f}%")
            print(f"• Peor Trade: {worst_trade['ticker']} {worst_trade['profit_pct']:+.2f}%")
        
        # Análisis por estrategia
        strategies = {}
        for trade in trades:
            strategy = trade['strategy']
            if strategy not in strategies:
                strategies[strategy] = {'total': 0, 'wins': 0, 'pnl': 0}
            strategies[strategy]['total'] += 1
            if trade['profit_pct'] > 0:
                strategies[strategy]['wins'] += 1
            strategies[strategy]['pnl'] += trade['profit_usd']
        
        print(f"\n🎯 PERFORMANCE POR ESTRATEGIA:")
        for strategy, stats in strategies.items():
            wr = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"\n{strategy}:")
            print(f"  • Trades: {stats['total']}")
            print(f"  • Win Rate: {wr:.1f}%")
            print(f"  • PnL: ${stats['pnl']:+,.2f}")
        
        # Análisis de calidad
        print(f"\n✨ ANÁLISIS DE CALIDAD:")
        
        if total_return > 5:
            print("🌟 EXCELENTE: Retorno superior al 5% mensual")
        elif total_return > 2:
            print("✅ BUENO: Retorno entre 2-5% mensual")
        else:
            print("⚠️ REGULAR: Retorno menor al 2% mensual")
        
        if win_rate > 60:
            print("🌟 EXCELENTE: Win Rate superior al 60%")
        elif win_rate > 50:
            print("✅ BUENO: Win Rate entre 50-60%")
        else:
            print("⚠️ MEJORABLE: Win Rate menor al 50%")
        
        if profit_factor > 1.5:
            print("🌟 EXCELENTE: Profit Factor superior a 1.5")
        elif profit_factor > 1.2:
            print("✅ BUENO: Profit Factor entre 1.2-1.5")
        else:
            print("⚠️ MEJORABLE: Profit Factor menor a 1.2")
        
        # Proyección
        print(f"\n💡 PROYECCIÓN:")
        monthly_return = total_return
        print(f"• Retorno Mensual: {monthly_return:+.1f}%")
        print(f"• Retorno Anualizado: {(((1 + monthly_return/100) ** 12) - 1) * 100:+.1f}%")
        print(f"• Capital en 3 meses: ${capital_inicial * ((1 + monthly_return/100) ** 3):,.2f}")
        print(f"• Capital en 6 meses: ${capital_inicial * ((1 + monthly_return/100) ** 6):,.2f}")
        print(f"• Capital en 1 año: ${capital_inicial * ((1 + monthly_return/100) ** 12):,.2f}")
    else:
        print("❌ No se generaron trades en el período")
    
    print("\n" + "="*60)
    print("✅ SISTEMA EJECUTADO EXITOSAMENTE")
    print("="*60)
    
    # Guardar resultados
    if trades:
        df_trades = pd.DataFrame(trades)
        df_trades.to_csv('backtest_results.csv', index=False)
        print("\n💾 Resultados guardados en backtest_results.csv")
    
    return capital, trades

if __name__ == "__main__":
    final_capital, trades = run_simple_backtest()