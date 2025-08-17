#!/usr/bin/env python3
"""
Backtesting Rápido Sistema v2.0
Validación eficiente con muestreo optimizado
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BacktestingRapidoV2:
    """
    Backtesting rápido para sistema v2.0 con muestreo eficiente
    """
    
    def __init__(self):
        # Configuración simplificada pero efectiva
        self.min_volume_ratio = 2.5
        self.min_risk_reward = 2.0
        self.min_score = 8
        
    def calcular_indicadores_rapidos(self, df):
        """Indicadores esenciales optimizados"""
        
        # EMAs clave
        df['EMA_8'] = df['Close'].ewm(span=8).mean()
        df['EMA_21'] = df['Close'].ewm(span=21).mean()
        df['EMA_55'] = df['Close'].ewm(span=55).mean()
        
        # RSI simplificado
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['High'] - df['Low']
        df['ATR'] = high_low.rolling(14).mean()
        
        # Volumen
        df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
        
        # MACD
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        return df
    
    def multi_timeframe_simple(self, ticker, target_date):
        """MTF simplificado y rápido"""
        try:
            # Solo 1h y 4h para velocidad
            timeframes = [('1h', '7d'), ('4h', '1mo')]
            scores = []
            
            for interval, period in timeframes:
                data = yf.Ticker(ticker)
                df = data.history(period=period, interval=interval, end=target_date + timedelta(days=1))
                
                if len(df) < 20:
                    continue
                
                df = self.calcular_indicadores_rapidos(df)
                
                if len(df) == 0:
                    continue
                    
                current = df.iloc[-1]
                
                # Score simple pero efectivo
                score = 0
                
                # Tendencia EMAs
                if current['EMA_8'] > current['EMA_21'] > current['EMA_55']:
                    score += 3
                elif current['EMA_8'] < current['EMA_21'] < current['EMA_55']:
                    score -= 3
                
                # MACD
                if current['MACD'] > current['MACD_Signal']:
                    score += 1
                else:
                    score -= 1
                
                # RSI momentum
                if 40 < current['RSI'] < 60:
                    score += 1
                
                scores.append(score)
            
            return np.mean(scores) if scores else 0
            
        except:
            return 0
    
    def detectar_signal_v2_rapido(self, df, ticker, idx):
        """Detección de señales v2.0 optimizada"""
        
        if idx < 55 or idx >= len(df) - 1:
            return None
        
        current = df.iloc[idx]
        
        # Filtros básicos obligatorios
        if (pd.isna(current['Volume_Ratio']) or 
            current['Volume_Ratio'] < self.min_volume_ratio or
            pd.isna(current['ATR'])):
            return None
        
        # MTF confirmation
        mtf_score = self.multi_timeframe_simple(ticker, df.index[idx])
        if abs(mtf_score) < 1.5:
            return None
        
        # Buscar setup de alta probabilidad
        lookback = df.iloc[idx-24:idx+1]  # Últimas 24 horas
        recent_high = lookback['High'].max()
        recent_low = lookback['Low'].min()
        range_size = recent_high - recent_low
        
        if range_size < current['Close'] * 0.02:  # Rango mínimo 2%
            return None
        
        score = 0
        signal_type = None
        
        # LONG Setup
        if (mtf_score > 1.5 and
            current['Close'] > recent_high * 0.998 and
            30 < current['RSI'] < 65 and
            current['Volume_Ratio'] > 3.0):
            
            signal_type = 'LONG'
            score = 8
            
            # Stops inteligentes
            stop_loss = recent_high * 0.985
            take_profit = current['Close'] + (range_size * 1.5)
        
        # SHORT Setup
        elif (mtf_score < -1.5 and
              current['Close'] < recent_low * 1.002 and
              35 < current['RSI'] < 70 and
              current['Volume_Ratio'] > 3.0):
            
            signal_type = 'SHORT'
            score = 8
            
            stop_loss = recent_low * 1.015
            take_profit = current['Close'] - (range_size * 1.5)
        
        # Verificar calidad
        if signal_type and score >= self.min_score:
            risk = abs(current['Close'] - stop_loss)
            reward = abs(take_profit - current['Close'])
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio >= self.min_risk_reward:
                return {
                    'ticker': ticker,
                    'type': signal_type,
                    'entry_price': current['Close'],
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'score': score,
                    'risk_reward': rr_ratio,
                    'mtf_score': mtf_score,
                    'volume_ratio': current['Volume_Ratio'],
                    'rsi': current['RSI'],
                    'timestamp': df.index[idx]
                }
        
        return None
    
    def simular_trade_rapido(self, signal, df, entry_idx):
        """Simulación rápida de trade"""
        
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        signal_type = signal['type']
        
        trailing_stop = None
        
        # Simular hasta 72 horas
        for i in range(entry_idx + 1, min(entry_idx + 72, len(df))):
            current_bar = df.iloc[i]
            
            if signal_type == 'LONG':
                # Trailing stop activación
                profit_pct = (current_bar['Close'] - entry_price) / entry_price
                if profit_pct >= 0.015:  # 1.5%
                    new_trailing = current_bar['Close'] * 0.995  # 0.5% trailing
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
                profit_pct = (entry_price - current_bar['Close']) / entry_price
                if profit_pct >= 0.015:
                    new_trailing = current_bar['Close'] * 1.005
                    if trailing_stop is None or new_trailing < trailing_stop:
                        trailing_stop = new_trailing
                
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
            exit_price = df.iloc[min(entry_idx + 72, len(df)-1)]['Close']
            exit_reason = 'TIME'
        
        # Calcular resultado
        if signal_type == 'LONG':
            profit_pct = (exit_price - entry_price) / entry_price
        else:
            profit_pct = (entry_price - exit_price) / entry_price
        
        return {
            'ticker': signal['ticker'],
            'type': signal_type,
            'profit_pct': profit_pct * 100,
            'exit_reason': exit_reason,
            'score': signal['score'],
            'risk_reward': signal['risk_reward'],
            'mtf_score': signal['mtf_score'],
            'volume_ratio': signal['volume_ratio']
        }
    
    def backtest_periodo_rapido(self, start_date, end_date, tickers, period_name):
        """Backtesting rápido para un período"""
        
        print(f"\n⚡ BACKTEST RÁPIDO: {period_name}")
        print(f"📅 {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
        print("="*50)
        
        all_trades = []
        
        for ticker in tickers:
            try:
                print(f"📊 {ticker}...", end="")
                
                # Descargar datos
                data = yf.Ticker(ticker)
                df = data.history(start=start_date - timedelta(days=30), 
                                 end=end_date + timedelta(days=1), 
                                 interval='4h')  # 4h para velocidad
                
                if len(df) < 100:
                    print(" ⚠️ Insuficiente")
                    continue
                
                df = self.calcular_indicadores_rapidos(df)
                
                signals_count = 0
                
                # Muestreo cada 6 períodos (24h) para velocidad
                for i in range(55, len(df), 6):
                    current_date = df.index[i].date()
                    
                    if current_date < start_date.date() or current_date > end_date.date():
                        continue
                    
                    signal = self.detectar_signal_v2_rapido(df, ticker, i)
                    
                    if signal:
                        signals_count += 1
                        trade = self.simular_trade_rapido(signal, df, i)
                        all_trades.append(trade)
                        
                        if signals_count >= 5:  # Máximo 5 por ticker
                            break
                
                print(f" ✅ {signals_count} señales")
                
            except Exception as e:
                print(f" ❌ Error")
        
        return all_trades
    
    def analizar_resultados_rapido(self, trades, period_name):
        """Análisis rápido de resultados"""
        
        if not trades:
            return None
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['profit_pct'] > 0]
        win_rate = (len(winning_trades) / total_trades) * 100
        
        avg_win = np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in trades if t['profit_pct'] <= 0])
        
        # Profit Factor
        gross_profit = sum(t['profit_pct'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['profit_pct'] for t in trades if t['profit_pct'] <= 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Análisis por salida
        exit_counts = {}
        for trade in trades:
            reason = trade['exit_reason']
            exit_counts[reason] = exit_counts.get(reason, 0) + 1
        
        print(f"\n📊 {period_name}: {total_trades} trades")
        print(f"├─ Win Rate: {win_rate:.1f}%")
        print(f"├─ Profit Factor: {profit_factor:.2f}")
        print(f"├─ Avg Win: {avg_win:+.2f}%")
        print(f"├─ Avg Loss: {avg_loss:+.2f}%")
        print(f"└─ Salidas: {dict(exit_counts)}")
        
        return {
            'period': period_name,
            'trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    
    def ejecutar_backtest_completo(self):
        """Ejecuta backtest completo rápido"""
        
        print("""
╔════════════════════════════════════════════════════════════════════════╗
║               BACKTESTING RÁPIDO SISTEMA v2.0                          ║
║                      Validación Eficiente                              ║
╚════════════════════════════════════════════════════════════════════════╝
        """)
        
        # Períodos de prueba
        periods = [
            ('Últimos 15 días', datetime.now() - timedelta(days=15), datetime.now()),
            ('Jul 2024', datetime(2024, 7, 1), datetime(2024, 7, 31)),
            ('Ago 2024', datetime(2024, 8, 1), datetime(2024, 8, 31)),
            ('Sep 2024', datetime(2024, 9, 1), datetime(2024, 9, 30)),
        ]
        
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
        
        resultados = []
        
        for period_name, start_date, end_date in periods:
            trades = self.backtest_periodo_rapido(start_date, end_date, tickers, period_name)
            resultado = self.analizar_resultados_rapido(trades, period_name)
            
            if resultado:
                resultados.append(resultado)
        
        # Resumen final
        if resultados:
            print(f"\n{'='*60}")
            print("📊 RESUMEN CONSOLIDADO")
            print(f"{'='*60}")
            
            total_trades = sum(r['trades'] for r in resultados)
            weighted_wr = sum(r['win_rate'] * r['trades'] for r in resultados) / total_trades
            avg_pf = np.mean([r['profit_factor'] for r in resultados])
            
            print(f"\n🎯 MÉTRICAS GENERALES:")
            print(f"• Total trades: {total_trades}")
            print(f"• Win Rate promedio: {weighted_wr:.1f}%")
            print(f"• Profit Factor promedio: {avg_pf:.2f}")
            
            # Evaluación
            if weighted_wr >= 65:
                evaluation = "🌟 EXCELENTE - Objetivo alcanzado"
            elif weighted_wr >= 60:
                evaluation = "✅ BUENO - Cerca del objetivo"
            elif weighted_wr >= 50:
                evaluation = "⚠️ REGULAR - Necesita optimización"
            else:
                evaluation = "❌ INSUFICIENTE - Revisar estrategia"
            
            print(f"\n🏆 EVALUACIÓN: {evaluation}")
            
            print(f"\n💡 CONCLUSIÓN:")
            if weighted_wr >= 60:
                print("✅ El sistema v2.0 muestra resultados prometedores")
                print("📈 Los filtros estrictos están funcionando")
                print("🎯 Recomendado para trading con position sizing conservador")
            else:
                print("🔧 El sistema necesita más optimización")
                print("📊 Considerar ajustar parámetros de filtros")
                print("💡 Enfoque en calidad vs cantidad funcionando parcialmente")

def main():
    """Función principal"""
    backtest = BacktestingRapidoV2()
    backtest.ejecutar_backtest_completo()

if __name__ == "__main__":
    main()