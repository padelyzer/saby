#!/usr/bin/env python3
"""
Backtest Individual por Símbolo - Sistema V2.5
Analiza cada crypto individualmente y genera reportes detallados
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

class BacktestV25:
    def __init__(self, symbol):
        self.symbol = symbol
        self.params = {
            'rsi_oversold': 35,  # Menos estricto para más señales
            'rsi_overbought': 65,  # Menos estricto para más señales  
            'atr_stop_multiplier': 2.0,
            'atr_target_multiplier': 3.0,
            'counter_trend_forbidden': True,
            'min_confidence': 0.25,  # Reducido para más señales
            'min_volume_ratio': 1.0,  # Menos estricto con volumen
            'risk_per_trade': 0.01,  # 1% por trade
            'initial_capital': 1000,
        }
        
        self.trades = []
        self.signals = []
        
    def get_data(self, days=90):
        """Obtiene datos históricos"""
        try:
            ticker = yf.Ticker(self.symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obtener datos horarios
            df = ticker.history(start=start_date, end=end_date, interval='1h')
            
            if len(df) < 50:
                print(f"⚠️ {self.symbol}: Datos insuficientes ({len(df)} velas)")
                return None
                
            return df
        except Exception as e:
            print(f"❌ Error obteniendo {self.symbol}: {e}")
            return None
    
    def calculate_indicators(self, df):
        """Calcula indicadores técnicos"""
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # EMAs
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # Tendencia
        df['Uptrend'] = df['EMA_20'] > df['EMA_50']
        df['Downtrend'] = df['EMA_20'] < df['EMA_50']
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volumen promedio
        df['Avg_Volume'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Avg_Volume']
        
        return df
    
    def generate_signal(self, row, prev_rows):
        """Genera señal basada en V2.5"""
        if pd.isna(row['RSI']) or pd.isna(row['ATR']):
            return None
            
        score = 0
        signals = []
        signal_type = None
        
        # Validar volumen
        if row['Volume_Ratio'] < self.params['min_volume_ratio']:
            return None
            
        # Determinar tendencia
        if row['Uptrend']:
            trend = 'UP'
            if row['EMA_20'] > prev_rows['EMA_20'].iloc[-1]:
                signals.append('STRONG_UPTREND')
            else:
                signals.append('UPTREND')
        elif row['Downtrend']:
            trend = 'DOWN'
            if row['EMA_20'] < prev_rows['EMA_20'].iloc[-1]:
                signals.append('STRONG_DOWNTREND')
            else:
                signals.append('DOWNTREND')
        else:
            trend = 'NEUTRAL'
            signals.append('NEUTRAL')
            
        # Aplicar filtro anti-tendencia
        if self.params['counter_trend_forbidden']:
            if trend == 'UP':
                # Solo LONGs en uptrend
                if row['RSI'] < self.params['rsi_oversold']:
                    score += 2
                    signals.append('RSI_OVERSOLD')
                    signal_type = 'LONG'
                    
                if row['MACD'] > row['MACD_Signal']:
                    score += 1
                    signals.append('MACD_BULLISH')
                    signal_type = 'LONG'
                    
            elif trend == 'DOWN':
                # Solo SHORTs en downtrend
                if row['RSI'] > self.params['rsi_overbought']:
                    score += 2
                    signals.append('RSI_OVERBOUGHT')
                    signal_type = 'SHORT'
                    
                if row['MACD'] < row['MACD_Signal']:
                    score += 1
                    signals.append('MACD_BEARISH')
                    signal_type = 'SHORT'
        
        # Evaluar señal
        if score >= 2 and signal_type:
            confidence = min(score / 4, 0.9)
            if confidence >= self.params['min_confidence']:
                return {
                    'type': signal_type,
                    'confidence': confidence,
                    'signals': signals,
                    'entry': row['Close'],
                    'atr': row['ATR'],
                    'volume_ratio': row['Volume_Ratio']
                }
        
        return None
    
    def simulate_trade(self, signal, entry_date, df_future):
        """Simula un trade con SL y TP"""
        entry_price = signal['entry']
        atr = signal['atr']
        
        if signal['type'] == 'LONG':
            stop_loss = entry_price - (atr * self.params['atr_stop_multiplier'])
            take_profit = entry_price + (atr * self.params['atr_target_multiplier'])
        else:
            stop_loss = entry_price + (atr * self.params['atr_stop_multiplier'])
            take_profit = entry_price - (atr * self.params['atr_target_multiplier'])
        
        # Simular salida
        for idx, row in df_future.iterrows():
            if signal['type'] == 'LONG':
                if row['Low'] <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'STOP_LOSS'
                    pnl_pct = ((exit_price / entry_price) - 1) * 100
                    break
                elif row['High'] >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TAKE_PROFIT'
                    pnl_pct = ((exit_price / entry_price) - 1) * 100
                    break
            else:  # SHORT
                if row['High'] >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'STOP_LOSS'
                    pnl_pct = ((entry_price / exit_price) - 1) * 100
                    break
                elif row['Low'] <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TAKE_PROFIT'
                    pnl_pct = ((entry_price / exit_price) - 1) * 100
                    break
        else:
            # Si no se alcanzó SL o TP, cerrar al final
            exit_price = df_future.iloc[-1]['Close']
            exit_reason = 'TIME_OUT'
            if signal['type'] == 'LONG':
                pnl_pct = ((exit_price / entry_price) - 1) * 100
            else:
                pnl_pct = ((entry_price / exit_price) - 1) * 100
        
        return {
            'entry_date': entry_date,
            'exit_date': idx if exit_reason != 'TIME_OUT' else df_future.index[-1],
            'type': signal['type'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'exit_reason': exit_reason,
            'pnl_pct': pnl_pct,
            'confidence': signal['confidence'],
            'signals': ', '.join(signal['signals']),
            'volume_ratio': signal['volume_ratio']
        }
    
    def run_backtest(self):
        """Ejecuta el backtest completo"""
        print(f"\n{'='*60}")
        print(f"🔍 BACKTEST: {self.symbol}")
        print(f"{'='*60}")
        
        # Obtener datos
        df = self.get_data()
        if df is None:
            return None
            
        # Calcular indicadores
        df = self.calculate_indicators(df)
        
        # Generar señales y trades
        for i in range(50, len(df) - 24):  # Dejar 24h para simular trade
            if len(self.trades) >= 100:  # Límite de trades
                break
                
            row = df.iloc[i]
            prev_rows = df.iloc[i-5:i]
            
            signal = self.generate_signal(row, prev_rows)
            if signal:
                # Registrar señal
                signal_data = {
                    'date': df.index[i],
                    'price': row['Close'],
                    'type': signal['type'],
                    'confidence': signal['confidence'],
                    'signals': signal['signals'],
                    'rsi': row['RSI'],
                    'volume_ratio': signal['volume_ratio']
                }
                self.signals.append(signal_data)
                
                # Simular trade
                df_future = df.iloc[i+1:i+25]  # Próximas 24 horas
                if len(df_future) > 0:
                    trade = self.simulate_trade(signal, df.index[i], df_future)
                    self.trades.append(trade)
        
        return self.generate_report()
    
    def generate_report(self):
        """Genera reporte detallado"""
        if not self.trades:
            return f"❌ {self.symbol}: No se generaron trades\n"
            
        trades_df = pd.DataFrame(self.trades)
        signals_df = pd.DataFrame(self.signals)
        
        # Estadísticas
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl_pct'] > 0])
        losing_trades = len(trades_df[trades_df['pnl_pct'] <= 0])
        win_rate = (winning_trades / total_trades) * 100
        
        avg_win = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl_pct'] <= 0]['pnl_pct'].mean() if losing_trades > 0 else 0
        
        total_pnl = trades_df['pnl_pct'].sum()
        avg_pnl = trades_df['pnl_pct'].mean()
        
        # Profit factor
        gross_profit = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].sum() if winning_trades > 0 else 0
        gross_loss = abs(trades_df[trades_df['pnl_pct'] <= 0]['pnl_pct'].sum()) if losing_trades > 0 else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Análisis por tipo
        long_trades = trades_df[trades_df['type'] == 'LONG']
        short_trades = trades_df[trades_df['type'] == 'SHORT']
        
        # Crear reporte
        report = f"""
# 📊 BACKTEST REPORT: {self.symbol}

## 📈 Resumen General
- **Total Trades:** {total_trades}
- **Win Rate:** {win_rate:.1f}%
- **Profit Factor:** {profit_factor:.2f}
- **Total P&L:** {total_pnl:.2f}%
- **Avg P&L por Trade:** {avg_pnl:.2f}%

## 🎯 Análisis de Trades
- **Winning Trades:** {winning_trades} ({win_rate:.1f}%)
- **Losing Trades:** {losing_trades} ({100-win_rate:.1f}%)
- **Avg Win:** {avg_win:.2f}%
- **Avg Loss:** {avg_loss:.2f}%

## 📊 Por Tipo de Operación
### LONG Trades: {len(long_trades)}
- Win Rate: {(len(long_trades[long_trades['pnl_pct'] > 0]) / len(long_trades) * 100) if len(long_trades) > 0 else 0:.1f}%
- Avg P&L: {long_trades['pnl_pct'].mean() if len(long_trades) > 0 else 0:.2f}%

### SHORT Trades: {len(short_trades)}
- Win Rate: {(len(short_trades[short_trades['pnl_pct'] > 0]) / len(short_trades) * 100) if len(short_trades) > 0 else 0:.1f}%
- Avg P&L: {short_trades['pnl_pct'].mean() if len(short_trades) > 0 else 0:.2f}%

## 📝 Últimas 10 Señales Detalladas

| Fecha | Tipo | Precio | Confianza | RSI | Vol Ratio | Señales |
|-------|------|--------|-----------|-----|-----------|---------|
"""
        
        # Agregar últimas señales
        for _, signal in signals_df.tail(10).iterrows():
            report += f"| {signal['date'].strftime('%m/%d %H:%M')} | {signal['type']} | ${signal['price']:.4f} | {signal['confidence']:.1%} | {signal['rsi']:.1f} | {signal['volume_ratio']:.2f} | {', '.join(signal['signals'])} |\n"
        
        report += f"""

## 💰 Últimos 10 Trades Ejecutados

| Entry Date | Type | Entry | Exit | P&L% | Exit Reason |
|------------|------|-------|------|------|-------------|
"""
        
        # Agregar últimos trades
        for _, trade in trades_df.tail(10).iterrows():
            report += f"| {trade['entry_date'].strftime('%m/%d %H:%M')} | {trade['type']} | ${trade['entry_price']:.4f} | ${trade['exit_price']:.4f} | {trade['pnl_pct']:+.2f}% | {trade['exit_reason']} |\n"
        
        report += f"""

## 🔍 Análisis de Salidas
- **Stop Loss:** {len(trades_df[trades_df['exit_reason'] == 'STOP_LOSS'])} ({len(trades_df[trades_df['exit_reason'] == 'STOP_LOSS'])/total_trades*100:.1f}%)
- **Take Profit:** {len(trades_df[trades_df['exit_reason'] == 'TAKE_PROFIT'])} ({len(trades_df[trades_df['exit_reason'] == 'TAKE_PROFIT'])/total_trades*100:.1f}%)
- **Time Out:** {len(trades_df[trades_df['exit_reason'] == 'TIME_OUT'])} ({len(trades_df[trades_df['exit_reason'] == 'TIME_OUT'])/total_trades*100:.1f}%)

## ⚠️ Observaciones
"""
        
        # Agregar observaciones
        if win_rate >= 60:
            report += "- ✅ **Excelente win rate** - Sistema muy efectivo\n"
        elif win_rate >= 50:
            report += "- ✅ **Buen win rate** - Sistema rentable\n"
        else:
            report += "- ⚠️ **Win rate bajo** - Revisar parámetros\n"
            
        if profit_factor >= 2:
            report += "- ✅ **Profit factor excelente** - Alta rentabilidad\n"
        elif profit_factor >= 1.5:
            report += "- ✅ **Profit factor bueno** - Sistema sólido\n"
        else:
            report += "- ⚠️ **Profit factor mejorable** - Optimizar SL/TP\n"
            
        if len(short_trades) > len(long_trades) * 2:
            report += "- ⚠️ **Sesgo a SHORTs** - Mercado bajista detectado\n"
        elif len(long_trades) > len(short_trades) * 2:
            report += "- ⚠️ **Sesgo a LONGs** - Mercado alcista detectado\n"
        
        report += f"\n---\n*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report

def run_all_backtests():
    """Ejecuta backtest para todos los símbolos"""
    symbols = [
        'ADA-USD',
        'XRP-USD', 
        'DOGE-USD',
        'AVAX-USD',
        'SOL-USD',
        'LINK-USD',
        'DOT-USD',
        'PEPE-USD'
    ]
    
    results = {}
    summary = []
    
    print("\n" + "="*60)
    print("🚀 INICIANDO BACKTESTS V2.5")
    print("="*60)
    
    for symbol in symbols:
        print(f"\n⏳ Procesando {symbol}...")
        backtest = BacktestV25(symbol)
        report = backtest.run_backtest()
        
        if report:
            # Guardar reporte individual
            filename = f"{symbol.replace('-USD', '').lower()}.md"
            with open(filename, 'w') as f:
                f.write(report)
            print(f"✅ {symbol}: Reporte guardado en {filename}")
            
            # Extraer métricas para resumen
            if backtest.trades:
                trades_df = pd.DataFrame(backtest.trades)
                win_rate = (len(trades_df[trades_df['pnl_pct'] > 0]) / len(trades_df)) * 100
                total_pnl = trades_df['pnl_pct'].sum()
                summary.append({
                    'symbol': symbol,
                    'trades': len(trades_df),
                    'win_rate': win_rate,
                    'total_pnl': total_pnl
                })
        else:
            print(f"❌ {symbol}: Sin datos o trades")
    
    # Crear resumen general
    if summary:
        summary_df = pd.DataFrame(summary)
        
        print("\n" + "="*60)
        print("📊 RESUMEN GENERAL")
        print("="*60)
        print(f"\n{summary_df.to_string(index=False)}")
        
        # Guardar resumen
        with open('backtest_summary.md', 'w') as f:
            f.write("# 📊 BACKTEST SUMMARY V2.5\n\n")
            f.write("## Resultados por Símbolo\n\n")
            f.write("| Símbolo | Trades | Win Rate | Total P&L |\n")
            f.write("|---------|--------|----------|----------|\n")
            for _, row in summary_df.iterrows():
                f.write(f"| {row['symbol']} | {row['trades']} | {row['win_rate']:.1f}% | {row['total_pnl']:.2f}% |\n")
            
            f.write(f"\n## Estadísticas Globales\n")
            f.write(f"- **Total Símbolos:** {len(summary_df)}\n")
            f.write(f"- **Total Trades:** {summary_df['trades'].sum()}\n")
            f.write(f"- **Avg Win Rate:** {summary_df['win_rate'].mean():.1f}%\n")
            f.write(f"- **Mejor Símbolo:** {summary_df.loc[summary_df['total_pnl'].idxmax()]['symbol']}\n")
            f.write(f"- **Peor Símbolo:** {summary_df.loc[summary_df['total_pnl'].idxmin()]['symbol']}\n")
            f.write(f"\n---\n*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        print("\n✅ Resumen guardado en backtest_summary.md")

if __name__ == "__main__":
    run_all_backtests()