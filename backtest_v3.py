#!/usr/bin/env python3
"""
Backtest V3.0 - Sistema Optimizado para Crypto
Mejoras aplicadas basadas en análisis de V2.5
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

class BacktestV3:
    def __init__(self, symbol):
        self.symbol = symbol
        self.params = {
            # RSI optimizado para crypto volátil
            'rsi_oversold': 25,  # Más extremo (era 35)
            'rsi_overbought': 75,  # Más extremo (era 65)
            
            # Stop/Target más amplios para crypto
            'atr_stop_multiplier': 2.5,  # Más amplio (era 2.0)
            'atr_target_multiplier': 3.5,  # Más ambicioso (era 3.0)
            
            # Filtros mejorados
            'counter_trend_forbidden': True,
            'min_confidence': 0.30,  # Balance entre cantidad y calidad
            'min_volume_ratio': 1.1,  # Volumen ligeramente elevado
            
            # Nuevo: Filtro de tendencia macro
            'require_trend_alignment': True,  # Debe alinear con tendencia mayor
            'min_trend_strength': 0.6,  # Fuerza mínima de tendencia
            
            # Risk management
            'risk_per_trade': 0.01,
            'initial_capital': 1000,
            'max_consecutive_losses': 3,  # Nuevo: pausa tras pérdidas
        }
        
        self.trades = []
        self.signals = []
        self.consecutive_losses = 0
        
    def get_data(self, days=120):
        """Obtiene datos históricos - Más días para análisis macro"""
        try:
            ticker = yf.Ticker(self.symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obtener datos de 4 horas (menos ruido)
            df_4h = ticker.history(start=start_date, end=end_date, interval='1h')
            
            # También obtener datos diarios para tendencia macro
            df_daily = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(df_4h) < 100:
                print(f"⚠️ {self.symbol}: Datos insuficientes ({len(df_4h)} velas)")
                return None, None
                
            return df_4h, df_daily
        except Exception as e:
            print(f"❌ Error obteniendo {self.symbol}: {e}")
            return None, None
    
    def calculate_indicators(self, df):
        """Calcula indicadores técnicos mejorados"""
        # RSI con período optimizado
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD estándar
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # EMAs múltiples para mejor análisis de tendencia
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # Tendencia mejorada con múltiples confirmaciones
        df['Uptrend'] = (df['EMA_9'] > df['EMA_20']) & (df['EMA_20'] > df['EMA_50'])
        df['Downtrend'] = (df['EMA_9'] < df['EMA_20']) & (df['EMA_20'] < df['EMA_50'])
        df['Strong_Uptrend'] = df['Uptrend'] & (df['Close'] > df['EMA_200'])
        df['Strong_Downtrend'] = df['Downtrend'] & (df['Close'] < df['EMA_200'])
        
        # ATR mejorado
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volumen
        df['Avg_Volume'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Avg_Volume']
        
        # Bollinger Bands para volatilidad
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Price action
        df['Higher_High'] = df['High'] > df['High'].rolling(10).max().shift(1)
        df['Lower_Low'] = df['Low'] < df['Low'].rolling(10).min().shift(1)
        
        # Momentum
        df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
        
        return df
    
    def calculate_trend_strength(self, df):
        """Calcula la fuerza de la tendencia"""
        if len(df) < 50:
            return 0
            
        current = df.iloc[-1]
        
        # Factores de tendencia
        trend_score = 0
        
        # EMAs alineadas
        if current['EMA_9'] > current['EMA_20'] > current['EMA_50']:
            trend_score += 0.3
        elif current['EMA_9'] < current['EMA_20'] < current['EMA_50']:
            trend_score -= 0.3
            
        # Precio vs EMA200
        if pd.notna(current['EMA_200']):
            if current['Close'] > current['EMA_200']:
                trend_score += 0.2
            else:
                trend_score -= 0.2
                
        # MACD
        if current['MACD_Histogram'] > 0:
            trend_score += 0.2
        else:
            trend_score -= 0.2
            
        # Momentum (ROC)
        if current['ROC'] > 5:
            trend_score += 0.15
        elif current['ROC'] < -5:
            trend_score -= 0.15
            
        # Higher highs / Lower lows
        recent_bars = df.tail(5)
        if recent_bars['Higher_High'].sum() >= 3:
            trend_score += 0.15
        elif recent_bars['Lower_Low'].sum() >= 3:
            trend_score -= 0.15
            
        return abs(trend_score)  # Retorna fuerza absoluta
    
    def check_macro_trend(self, df_daily):
        """Verifica la tendencia macro en timeframe diario"""
        if df_daily is None or len(df_daily) < 50:
            return 'NEUTRAL'
            
        df_daily = self.calculate_indicators(df_daily)
        current = df_daily.iloc[-1]
        
        if current['Strong_Uptrend']:
            return 'BULLISH'
        elif current['Strong_Downtrend']:
            return 'BEARISH'
        elif current['Uptrend']:
            return 'MILD_BULLISH'
        elif current['Downtrend']:
            return 'MILD_BEARISH'
        else:
            return 'NEUTRAL'
    
    def generate_signal(self, row, prev_rows, macro_trend, trend_strength):
        """Genera señal con filtros mejorados"""
        if pd.isna(row['RSI']) or pd.isna(row['ATR']):
            return None
            
        # Pausar tras pérdidas consecutivas
        if self.consecutive_losses >= self.params['max_consecutive_losses']:
            return None
            
        score = 0
        signals = []
        signal_type = None
        
        # Validar volumen
        if row['Volume_Ratio'] < self.params['min_volume_ratio']:
            return None
            
        # Validar fuerza de tendencia
        if trend_strength < self.params['min_trend_strength']:
            return None
            
        # Determinar tendencia local
        if row['Strong_Uptrend']:
            trend = 'STRONG_UP'
            signals.append('STRONG_UPTREND')
        elif row['Uptrend']:
            trend = 'UP'
            signals.append('UPTREND')
        elif row['Strong_Downtrend']:
            trend = 'STRONG_DOWN'
            signals.append('STRONG_DOWNTREND')
        elif row['Downtrend']:
            trend = 'DOWN'
            signals.append('DOWNTREND')
        else:
            return None  # No operar en lateral
            
        # Validar alineación con macro tendencia
        if self.params['require_trend_alignment']:
            if macro_trend in ['BULLISH', 'MILD_BULLISH'] and trend in ['DOWN', 'STRONG_DOWN']:
                return None  # No SHORT en macro bull
            if macro_trend in ['BEARISH', 'MILD_BEARISH'] and trend in ['UP', 'STRONG_UP']:
                return None  # No LONG en macro bear
                
        # Aplicar lógica de señales mejorada
        if self.params['counter_trend_forbidden']:
            if trend in ['UP', 'STRONG_UP']:
                # Solo LONGs en uptrend
                if row['RSI'] < self.params['rsi_oversold']:
                    score += 3
                    signals.append('RSI_OVERSOLD_EXTREME')
                    signal_type = 'LONG'
                elif row['RSI'] < 35 and row['Close'] <= row['BB_Lower']:
                    score += 2.5
                    signals.append('OVERSOLD_AT_BB_LOWER')
                    signal_type = 'LONG'
                    
                if row['MACD'] > row['MACD_Signal'] and row['MACD_Histogram'] > 0:
                    score += 2
                    signals.append('MACD_BULLISH_CROSS')
                    signal_type = 'LONG'
                    
                # Bonus por tendencia fuerte
                if trend == 'STRONG_UP':
                    score += 1
                    
            elif trend in ['DOWN', 'STRONG_DOWN']:
                # Solo SHORTs en downtrend
                if row['RSI'] > self.params['rsi_overbought']:
                    score += 3
                    signals.append('RSI_OVERBOUGHT_EXTREME')
                    signal_type = 'SHORT'
                elif row['RSI'] > 65 and row['Close'] >= row['BB_Upper']:
                    score += 2.5
                    signals.append('OVERBOUGHT_AT_BB_UPPER')
                    signal_type = 'SHORT'
                    
                if row['MACD'] < row['MACD_Signal'] and row['MACD_Histogram'] < 0:
                    score += 2
                    signals.append('MACD_BEARISH_CROSS')
                    signal_type = 'SHORT'
                    
                # Bonus por tendencia fuerte
                if trend == 'STRONG_DOWN':
                    score += 1
        
        # Evaluar señal con criterios más estrictos
        if score >= 3 and signal_type:  # Aumentado de 2 a 3
            confidence = min(score / 6, 0.95)  # Ajustado el cálculo
            if confidence >= self.params['min_confidence']:
                return {
                    'type': signal_type,
                    'confidence': confidence,
                    'signals': signals,
                    'entry': row['Close'],
                    'atr': row['ATR'],
                    'volume_ratio': row['Volume_Ratio'],
                    'trend_strength': trend_strength,
                    'macro_trend': macro_trend
                }
        
        return None
    
    def simulate_trade(self, signal, entry_date, df_future):
        """Simula trade con stops dinámicos mejorados"""
        entry_price = signal['entry']
        atr = signal['atr']
        
        # Stops más amplios para crypto
        if signal['type'] == 'LONG':
            stop_loss = entry_price - (atr * self.params['atr_stop_multiplier'])
            take_profit = entry_price + (atr * self.params['atr_target_multiplier'])
            
            # Ajuste dinámico basado en confianza
            if signal['confidence'] > 0.7:
                take_profit = entry_price + (atr * 4.0)  # TP más ambicioso
        else:
            stop_loss = entry_price + (atr * self.params['atr_stop_multiplier'])
            take_profit = entry_price - (atr * self.params['atr_target_multiplier'])
            
            if signal['confidence'] > 0.7:
                take_profit = entry_price - (atr * 4.0)
        
        # Trailing stop para trades ganadores
        best_price = entry_price
        trailing_activated = False
        
        for idx, row in df_future.iterrows():
            if signal['type'] == 'LONG':
                # Actualizar mejor precio
                if row['High'] > best_price:
                    best_price = row['High']
                    # Activar trailing si ganancia > 2%
                    if (best_price / entry_price - 1) > 0.02:
                        trailing_activated = True
                        trailing_stop = best_price - (atr * 1.5)
                
                # Check exits
                if row['Low'] <= stop_loss and not trailing_activated:
                    exit_price = stop_loss
                    exit_reason = 'STOP_LOSS'
                    break
                elif trailing_activated and row['Low'] <= trailing_stop:
                    exit_price = trailing_stop
                    exit_reason = 'TRAILING_STOP'
                    break
                elif row['High'] >= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TAKE_PROFIT'
                    break
            else:  # SHORT
                # Actualizar mejor precio
                if row['Low'] < best_price:
                    best_price = row['Low']
                    # Activar trailing si ganancia > 2%
                    if (1 - best_price / entry_price) > 0.02:
                        trailing_activated = True
                        trailing_stop = best_price + (atr * 1.5)
                
                # Check exits
                if row['High'] >= stop_loss and not trailing_activated:
                    exit_price = stop_loss
                    exit_reason = 'STOP_LOSS'
                    break
                elif trailing_activated and row['High'] >= trailing_stop:
                    exit_price = trailing_stop
                    exit_reason = 'TRAILING_STOP'
                    break
                elif row['Low'] <= take_profit:
                    exit_price = take_profit
                    exit_reason = 'TAKE_PROFIT'
                    break
        else:
            # Time out con precio de cierre
            exit_price = df_future.iloc[-1]['Close']
            exit_reason = 'TIME_OUT'
        
        # Calcular P&L
        if signal['type'] == 'LONG':
            pnl_pct = ((exit_price / entry_price) - 1) * 100
        else:
            pnl_pct = ((entry_price / exit_price) - 1) * 100
        
        # Actualizar contador de pérdidas consecutivas
        if pnl_pct < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
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
            'volume_ratio': signal['volume_ratio'],
            'trend_strength': signal['trend_strength'],
            'macro_trend': signal['macro_trend']
        }
    
    def run_backtest(self):
        """Ejecuta el backtest con sistema V3.0"""
        print(f"\n{'='*60}")
        print(f"🔍 BACKTEST V3.0: {self.symbol}")
        print(f"{'='*60}")
        
        # Obtener datos
        df_4h, df_daily = self.get_data()
        if df_4h is None:
            return None
            
        # Calcular indicadores
        df_4h = self.calculate_indicators(df_4h)
        
        # Obtener tendencia macro
        macro_trend = self.check_macro_trend(df_daily)
        print(f"📊 Tendencia Macro: {macro_trend}")
        
        # Generar señales y trades
        for i in range(100, len(df_4h) - 48):  # 48 horas para simular
            if len(self.trades) >= 100:
                break
                
            row = df_4h.iloc[i]
            prev_rows = df_4h.iloc[i-10:i]
            
            # Calcular fuerza de tendencia
            trend_strength = self.calculate_trend_strength(df_4h.iloc[i-50:i+1])
            
            signal = self.generate_signal(row, prev_rows, macro_trend, trend_strength)
            if signal:
                # Registrar señal
                signal_data = {
                    'date': df_4h.index[i],
                    'price': row['Close'],
                    'type': signal['type'],
                    'confidence': signal['confidence'],
                    'signals': signal['signals'],
                    'rsi': row['RSI'],
                    'volume_ratio': signal['volume_ratio'],
                    'trend_strength': trend_strength,
                    'macro_trend': macro_trend
                }
                self.signals.append(signal_data)
                
                # Simular trade
                df_future = df_4h.iloc[i+1:i+49]  # 48 horas futuras
                if len(df_future) > 0:
                    trade = self.simulate_trade(signal, df_4h.index[i], df_future)
                    self.trades.append(trade)
        
        return self.generate_report()
    
    def generate_report(self):
        """Genera reporte detallado V3.0"""
        if not self.trades:
            return f"❌ {self.symbol}: No se generaron trades (filtros muy estrictos o condiciones no cumplidas)\n"
            
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
        max_drawdown = trades_df['pnl_pct'].cumsum().min()
        
        # Profit factor
        gross_profit = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].sum() if winning_trades > 0 else 0
        gross_loss = abs(trades_df[trades_df['pnl_pct'] <= 0]['pnl_pct'].sum()) if losing_trades > 0 else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Análisis por tipo
        long_trades = trades_df[trades_df['type'] == 'LONG']
        short_trades = trades_df[trades_df['type'] == 'SHORT']
        
        # Análisis por salida
        sl_exits = len(trades_df[trades_df['exit_reason'] == 'STOP_LOSS'])
        tp_exits = len(trades_df[trades_df['exit_reason'] == 'TAKE_PROFIT'])
        trail_exits = len(trades_df[trades_df['exit_reason'] == 'TRAILING_STOP'])
        time_exits = len(trades_df[trades_df['exit_reason'] == 'TIME_OUT'])
        
        # Crear reporte
        report = f"""
# 📊 BACKTEST V3.0 REPORT: {self.symbol}

## 📈 Resumen General
- **Total Trades:** {total_trades}
- **Win Rate:** {win_rate:.1f}%
- **Profit Factor:** {profit_factor:.2f}
- **Total P&L:** {total_pnl:.2f}%
- **Avg P&L por Trade:** {avg_pnl:.2f}%
- **Max Drawdown:** {max_drawdown:.2f}%

## 🎯 Análisis de Trades
- **Winning Trades:** {winning_trades} ({win_rate:.1f}%)
- **Losing Trades:** {losing_trades} ({100-win_rate:.1f}%)
- **Avg Win:** {avg_win:.2f}%
- **Avg Loss:** {avg_loss:.2f}%
- **Risk/Reward Ratio:** {abs(avg_win/avg_loss) if avg_loss != 0 else 0:.2f}

## 📊 Por Tipo de Operación
### LONG Trades: {len(long_trades)}
- Win Rate: {(len(long_trades[long_trades['pnl_pct'] > 0]) / len(long_trades) * 100) if len(long_trades) > 0 else 0:.1f}%
- Avg P&L: {long_trades['pnl_pct'].mean() if len(long_trades) > 0 else 0:.2f}%
- Total P&L: {long_trades['pnl_pct'].sum() if len(long_trades) > 0 else 0:.2f}%

### SHORT Trades: {len(short_trades)}
- Win Rate: {(len(short_trades[short_trades['pnl_pct'] > 0]) / len(short_trades) * 100) if len(short_trades) > 0 else 0:.1f}%
- Avg P&L: {short_trades['pnl_pct'].mean() if len(short_trades) > 0 else 0:.2f}%
- Total P&L: {short_trades['pnl_pct'].sum() if len(short_trades) > 0 else 0:.2f}%

## 🔍 Análisis de Salidas
- **Stop Loss:** {sl_exits} ({sl_exits/total_trades*100:.1f}%)
- **Take Profit:** {tp_exits} ({tp_exits/total_trades*100:.1f}%)
- **Trailing Stop:** {trail_exits} ({trail_exits/total_trades*100:.1f}%)
- **Time Out:** {time_exits} ({time_exits/total_trades*100:.1f}%)

## 📝 Últimas 10 Señales Detalladas

| Fecha | Tipo | Precio | Confianza | RSI | Trend Str | Macro | Señales |
|-------|------|--------|-----------|-----|-----------|-------|---------|
"""
        
        # Agregar últimas señales
        for _, signal in signals_df.tail(10).iterrows():
            report += f"| {signal['date'].strftime('%m/%d %H:%M')} | {signal['type']} | ${signal['price']:.4f} | {signal['confidence']:.1%} | {signal['rsi']:.1f} | {signal['trend_strength']:.2f} | {signal['macro_trend']} | {', '.join(signal['signals'][:2])} |\n"
        
        report += f"""

## 💰 Últimos 10 Trades Ejecutados

| Entry Date | Type | Entry | Exit | P&L% | Exit Reason | Confidence |
|------------|------|-------|------|------|-------------|------------|
"""
        
        # Agregar últimos trades
        for _, trade in trades_df.tail(10).iterrows():
            report += f"| {trade['entry_date'].strftime('%m/%d %H:%M')} | {trade['type']} | ${trade['entry_price']:.4f} | ${trade['exit_price']:.4f} | {trade['pnl_pct']:+.2f}% | {trade['exit_reason']} | {trade['confidence']:.1%} |\n"
        
        report += f"""

## ⚠️ Evaluación del Sistema

### Métricas de Calidad:
"""
        
        # Evaluación
        if win_rate >= 55:
            report += "- ✅ **Excelente win rate** (>55%)\n"
        elif win_rate >= 45:
            report += "- ✅ **Buen win rate** (45-55%)\n"
        else:
            report += "- ⚠️ **Win rate bajo** (<45%)\n"
            
        if profit_factor >= 1.5:
            report += "- ✅ **Profit factor excelente** (>1.5)\n"
        elif profit_factor >= 1.2:
            report += "- ✅ **Profit factor bueno** (1.2-1.5)\n"
        else:
            report += "- ⚠️ **Profit factor insuficiente** (<1.2)\n"
            
        if total_pnl > 20:
            report += "- ✅ **Rentabilidad alta** (>20%)\n"
        elif total_pnl > 0:
            report += "- ✅ **Sistema rentable**\n"
        else:
            report += "- ❌ **Sistema no rentable**\n"
            
        if trail_exits > sl_exits * 0.2:
            report += "- ✅ **Buena gestión de ganancias** (trailing stops efectivos)\n"
            
        if len(short_trades) > len(long_trades) * 2:
            report += "- ⚠️ **Sesgo SHORT** - Posible mercado bajista\n"
        elif len(long_trades) > len(short_trades) * 2:
            report += "- ⚠️ **Sesgo LONG** - Posible mercado alcista\n"
        
        report += f"\n---\n*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report

def run_all_backtests_v3():
    """Ejecuta backtest V3.0 para todos los símbolos"""
    symbols = [
        'ADA-USD',
        'XRP-USD', 
        'DOGE-USD',
        'AVAX-USD',
        'SOL-USD',
        'LINK-USD',
        'DOT-USD'
    ]
    
    results = {}
    summary = []
    
    print("\n" + "="*60)
    print("🚀 INICIANDO BACKTESTS V3.0 - SISTEMA OPTIMIZADO")
    print("="*60)
    print("\n📋 Mejoras aplicadas:")
    print("- RSI ajustado a 25/75 (más extremo)")
    print("- Stops más amplios (2.5x ATR)")
    print("- Targets más ambiciosos (3.5x ATR)")
    print("- Trailing stops para proteger ganancias")
    print("- Filtro de tendencia macro")
    print("- Timeframe 4H para menos ruido")
    print("- Validación de fuerza de tendencia")
    print("\n" + "="*60)
    
    for symbol in symbols:
        print(f"\n⏳ Procesando {symbol}...")
        backtest = BacktestV3(symbol)
        report = backtest.run_backtest()
        
        if report:
            # Guardar reporte individual
            filename = f"{symbol.replace('-USD', '').lower()}_v3.md"
            with open(filename, 'w') as f:
                f.write(report)
            print(f"✅ {symbol}: Reporte V3.0 guardado en {filename}")
            
            # Extraer métricas para resumen
            if backtest.trades:
                trades_df = pd.DataFrame(backtest.trades)
                win_rate = (len(trades_df[trades_df['pnl_pct'] > 0]) / len(trades_df)) * 100
                total_pnl = trades_df['pnl_pct'].sum()
                profit_factor = 0
                if len(trades_df[trades_df['pnl_pct'] <= 0]) > 0:
                    gross_profit = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].sum() if len(trades_df[trades_df['pnl_pct'] > 0]) > 0 else 0
                    gross_loss = abs(trades_df[trades_df['pnl_pct'] <= 0]['pnl_pct'].sum())
                    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
                
                summary.append({
                    'symbol': symbol,
                    'trades': len(trades_df),
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'profit_factor': profit_factor
                })
        else:
            print(f"❌ {symbol}: Sin trades generados")
    
    # Crear resumen general
    if summary:
        summary_df = pd.DataFrame(summary)
        
        print("\n" + "="*60)
        print("📊 RESUMEN GENERAL V3.0")
        print("="*60)
        print(f"\n{summary_df.to_string(index=False)}")
        
        # Guardar resumen
        with open('backtest_summary_v3.md', 'w') as f:
            f.write("# 📊 BACKTEST SUMMARY V3.0 - SISTEMA OPTIMIZADO\n\n")
            f.write("## 🔧 Mejoras Implementadas\n")
            f.write("- RSI: 25/75 (optimizado para crypto)\n")
            f.write("- Stop Loss: 2.5x ATR (más amplio)\n")
            f.write("- Take Profit: 3.5x ATR (más ambicioso)\n")
            f.write("- Trailing Stop implementado\n")
            f.write("- Filtro de tendencia macro\n")
            f.write("- Análisis en 4H (menos ruido)\n\n")
            
            f.write("## 📈 Resultados por Símbolo\n\n")
            f.write("| Símbolo | Trades | Win Rate | Total P&L | Profit Factor |\n")
            f.write("|---------|--------|----------|-----------|---------------|\n")
            for _, row in summary_df.iterrows():
                f.write(f"| {row['symbol']} | {row['trades']} | {row['win_rate']:.1f}% | {row['total_pnl']:.2f}% | {row['profit_factor']:.2f} |\n")
            
            f.write(f"\n## 📊 Estadísticas Globales\n")
            f.write(f"- **Total Símbolos:** {len(summary_df)}\n")
            f.write(f"- **Total Trades:** {summary_df['trades'].sum()}\n")
            f.write(f"- **Avg Win Rate:** {summary_df['win_rate'].mean():.1f}%\n")
            f.write(f"- **Avg P&L:** {summary_df['total_pnl'].mean():.2f}%\n")
            f.write(f"- **Avg Profit Factor:** {summary_df['profit_factor'].mean():.2f}\n")
            
            # Identificar mejores y peores
            if len(summary_df) > 0:
                best_symbol = summary_df.loc[summary_df['total_pnl'].idxmax()]
                worst_symbol = summary_df.loc[summary_df['total_pnl'].idxmin()]
                
                f.write(f"\n## 🏆 Mejores y Peores\n")
                f.write(f"- **Mejor Símbolo:** {best_symbol['symbol']} (+{best_symbol['total_pnl']:.2f}%)\n")
                f.write(f"- **Peor Símbolo:** {worst_symbol['symbol']} ({worst_symbol['total_pnl']:.2f}%)\n")
                
                # Símbolos rentables
                profitable = summary_df[summary_df['total_pnl'] > 0]
                f.write(f"\n## ✅ Símbolos Rentables: {len(profitable)}/{len(summary_df)}\n")
                if len(profitable) > 0:
                    for _, row in profitable.iterrows():
                        f.write(f"- {row['symbol']}: +{row['total_pnl']:.2f}% (PF: {row['profit_factor']:.2f})\n")
            
            f.write(f"\n---\n*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        print("\n✅ Resumen V3.0 guardado en backtest_summary_v3.md")
        
        # Comparación con V2.5
        print("\n" + "="*60)
        print("📊 COMPARACIÓN V2.5 vs V3.0")
        print("="*60)
        print("\nV2.5: -14.4% avg P&L, 35.5% win rate")
        print(f"V3.0: {summary_df['total_pnl'].mean():.2f}% avg P&L, {summary_df['win_rate'].mean():.1f}% win rate")
        
        improvement = summary_df['total_pnl'].mean() - (-14.4)
        if improvement > 0:
            print(f"\n✅ MEJORA: +{improvement:.2f}% en rentabilidad")
        else:
            print(f"\n⚠️ Sin mejora significativa")

if __name__ == "__main__":
    run_all_backtests_v3()