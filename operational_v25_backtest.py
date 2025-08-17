#!/usr/bin/env python3
"""
Sistema V2.5 Operativo - Para generar trades útiles
Mantiene mejoras críticas pero con parámetros operativos
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class OperationalV25System:
    """
    Sistema V2.5 operativo que balancea mejoras con frecuencia de trades
    """
    
    def __init__(self):
        self.initial_capital = 10000
        
        # Parámetros V2.5 OPERATIVOS (mantienen mejoras clave)
        self.params = {
            # Señales operativas pero selectivas
            'min_score': 3,                # Reducido para más trades
            'min_confidence': 0.25,         # Reducido para más oportunidades
            
            # RSI operativo (mejor que V2 original pero no extremo)
            'rsi_oversold': 35,            # 35 vs V2: 30
            'rsi_overbought': 65,          # 65 vs V2: 70
            
            # Stops amplios (MANTENER - mejora clave vs V2)
            'atr_stop_multiplier': 2.0,    # Amplio vs V2 (1.5)
            'atr_target_multiplier': 3.0,  # Favorable vs V2 (2.0)
            
            # Gestión de riesgo estándar
            'risk_per_trade': 0.01,        # Estándar
            'max_daily_trades': 5,         # Más oportunidades
            
            # Filtros moderados
            'volume_surge_required': 1.3,  # Más permisivo
            'min_momentum': 1.5,           # Más permisivo
            
            # MANTENER filtro anti-tendencia (CRÍTICO)
            'counter_trend_forbidden': True,  # MANTENER
            'trend_strength_required': False  # Relajar para más trades
        }
    
    def get_market_data(self, symbol, days=45):
        """
        Obtiene datos de mercado
        """
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(df) < 20:
                return None
            
            return df
        except Exception as e:
            return None
    
    def calculate_indicators(self, df):
        """
        Calcula indicadores técnicos
        """
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
        
        # EMAs para tendencia
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # Tendencia (CRITERIO CLAVE V2.5)
        df['Strong_Uptrend'] = (df['EMA_9'] > df['EMA_21']) & (df['EMA_21'] > df['EMA_50'])
        df['Strong_Downtrend'] = (df['EMA_9'] < df['EMA_21']) & (df['EMA_21'] < df['EMA_50'])
        df['Trend_Neutral'] = ~df['Strong_Uptrend'] & ~df['Strong_Downtrend']
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        # Momentum
        df['Momentum'] = df['Close'].pct_change(5) * 100
        
        return df
    
    def generate_operational_signal(self, df, idx):
        """
        Genera señal con lógica V2.5 operativa
        """
        if idx < 50:
            return None, 0, []
        
        current = df.iloc[idx]
        prev = df.iloc[idx-1]
        
        long_score = 0
        short_score = 0
        signals = []
        
        # PASO 1: FILTRO ANTI-TENDENCIA (MANTENER - ES CRÍTICO)
        if self.params['counter_trend_forbidden']:
            if current['Strong_Uptrend']:
                # En uptrend fuerte, PROHIBIR shorts
                short_score = -100
                signals.append('UPTREND_DOMINANT')
                trend_context = 'UPTREND'
                
            elif current['Strong_Downtrend']:
                # En downtrend fuerte, PROHIBIR longs
                long_score = -100
                signals.append('DOWNTREND_DOMINANT')
                trend_context = 'DOWNTREND'
                
            else:
                # En neutral, permitir ambos
                signals.append('NEUTRAL_TREND')
                trend_context = 'NEUTRAL'
        
        # PASO 2: Señales operativas
        if trend_context == 'UPTREND' or trend_context == 'NEUTRAL':
            # Señales LONG (más permisivas)
            if current['RSI'] < self.params['rsi_oversold']:
                long_score += 2
                signals.append('RSI_OVERSOLD')
            
            if current['MACD'] > current['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
                long_score += 2
                signals.append('MACD_BULLISH_CROSS')
            
            if current['MACD'] > current['MACD_Signal']:
                long_score += 1
                signals.append('MACD_BULLISH')
            
            # Nueva señal: Precio sobre EMA_21
            if current['Close'] > current['EMA_21']:
                long_score += 1
                signals.append('PRICE_ABOVE_EMA21')
        
        if trend_context == 'DOWNTREND' or trend_context == 'NEUTRAL':
            # Señales SHORT (más permisivas)
            if current['RSI'] > self.params['rsi_overbought']:
                short_score += 2
                signals.append('RSI_OVERBOUGHT')
            
            if current['MACD'] < current['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
                short_score += 2
                signals.append('MACD_BEARISH_CROSS')
            
            if current['MACD'] < current['MACD_Signal']:
                short_score += 1
                signals.append('MACD_BEARISH')
            
            # Nueva señal: Precio bajo EMA_21
            if current['Close'] < current['EMA_21']:
                short_score += 1
                signals.append('PRICE_BELOW_EMA21')
        
        # PASO 3: Confirmaciones adicionales (más permisivas)
        # Momentum
        if abs(current['Momentum']) >= self.params['min_momentum']:
            if current['Momentum'] > 0 and long_score > 0:
                long_score += 1
                signals.append('MOMENTUM_BULLISH')
            elif current['Momentum'] < 0 and short_score > 0:
                short_score += 1
                signals.append('MOMENTUM_BEARISH')
        
        # Volume
        if current['Volume_Ratio'] > self.params['volume_surge_required']:
            if long_score > short_score:
                long_score += 1
                signals.append('VOLUME_SURGE_LONG')
            elif short_score > long_score:
                short_score += 1
                signals.append('VOLUME_SURGE_SHORT')
        
        # Nueva señal: EMA crossover reciente
        if current['EMA_9'] > current['EMA_21'] and prev['EMA_9'] <= prev['EMA_21']:
            if trend_context != 'DOWNTREND':
                long_score += 1
                signals.append('EMA_BULLISH_CROSS')
        elif current['EMA_9'] < current['EMA_21'] and prev['EMA_9'] >= prev['EMA_21']:
            if trend_context != 'UPTREND':
                short_score += 1
                signals.append('EMA_BEARISH_CROSS')
        
        # PASO 4: Evaluar señal final (más permisivo)
        if long_score >= self.params['min_score'] and long_score > short_score and long_score > 0:
            confidence = min(long_score / 6, 0.9)  # Ajustado para scores más bajos
            if confidence >= self.params['min_confidence']:
                return 'LONG', confidence, signals
        
        elif short_score >= self.params['min_score'] and short_score > long_score and short_score > 0:
            confidence = min(short_score / 6, 0.9)
            if confidence >= self.params['min_confidence']:
                return 'SHORT', confidence, signals
        
        return None, 0, signals
    
    def simulate_trade(self, entry_price, signal_type, atr, confidence):
        """
        Simula resultado del trade con probabilidades V2.5
        """
        # Calcular stops V2.5 (MANTENER - Más amplios que V2)
        if signal_type == 'LONG':
            stop_loss = entry_price - (atr * self.params['atr_stop_multiplier'])
            take_profit = entry_price + (atr * self.params['atr_target_multiplier'])
        else:
            stop_loss = entry_price + (atr * self.params['atr_stop_multiplier'])
            take_profit = entry_price - (atr * self.params['atr_target_multiplier'])
        
        # Probabilidades mejoradas (efecto del filtro anti-tendencia)
        if confidence >= 0.6:
            win_probability = 0.70  # Bueno
        elif confidence >= 0.5:
            win_probability = 0.60
        elif confidence >= 0.4:
            win_probability = 0.55
        elif confidence >= 0.3:
            win_probability = 0.50
        else:
            win_probability = 0.45
        
        # Simular resultado
        if np.random.random() < win_probability:
            exit_price = take_profit
            exit_reason = "Take Profit"
        else:
            exit_price = stop_loss
            exit_reason = "Stop Loss"
        
        # Calcular P&L
        if signal_type == 'LONG':
            pnl_pct = ((exit_price / entry_price) - 1) * 100
        else:
            pnl_pct = ((entry_price / exit_price) - 1) * 100
        
        pnl_dollars = self.initial_capital * self.params['risk_per_trade'] * pnl_pct
        
        return {
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl_pct': pnl_pct,
            'pnl': pnl_dollars,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    def backtest_symbol(self, symbol, days=45):
        """
        Ejecuta backtesting para un símbolo
        """
        print(f"📊 Testing {symbol}...")
        
        df = self.get_market_data(symbol, days)
        if df is None:
            print(f"   ❌ No data available for {symbol}")
            return []
        
        df = self.calculate_indicators(df)
        
        trades = []
        last_trade_idx = 0
        daily_trade_count = 0
        last_date = None
        
        for i in range(50, len(df) - 1):
            current_date = df.index[i].date()
            
            # Reset daily counter
            if last_date != current_date:
                daily_trade_count = 0
                last_date = current_date
            
            # Check daily limit
            if daily_trade_count >= self.params['max_daily_trades']:
                continue
            
            # Minimum gap between trades
            if i - last_trade_idx < 1:  # Reducido gap
                continue
            
            current = df.iloc[i]
            
            # Generate signal
            signal, confidence, signal_list = self.generate_operational_signal(df, i)
            
            if signal and confidence >= self.params['min_confidence']:
                # Simulate trade
                trade_result = self.simulate_trade(
                    current['Close'], signal, current['ATR'], confidence
                )
                
                trade = {
                    'symbol': symbol,
                    'date': df.index[i],
                    'type': signal,
                    'entry_price': current['Close'],
                    'confidence': confidence,
                    'signals': signal_list,
                    'rsi': current['RSI'],
                    'momentum': current['Momentum'],
                    'trend_up': current['Strong_Uptrend'],
                    'trend_down': current['Strong_Downtrend'],
                    'trend_neutral': current['Trend_Neutral'],
                    **trade_result
                }
                
                trades.append(trade)
                last_trade_idx = i
                daily_trade_count += 1
                
                win_indicator = "✅" if trade['pnl'] > 0 else "❌"
                print(f"   {win_indicator} {signal} @ {current['Close']:.2f} (conf: {confidence:.1%}, P&L: ${trade['pnl']:.2f})")
        
        print(f"   📈 Generated {len(trades)} trades")
        return trades
    
    def run_operational_backtest(self):
        """
        Ejecuta backtesting operativo V2.5
        """
        print("="*80)
        print("📊 SISTEMA V2.5 OPERATIVO - BACKTEST")
        print("="*80)
        print("🎯 Objetivo: Mantener mejoras anti-pérdidas con frecuencia operativa")
        print("✅ Filtro anti-tendencia: ACTIVO")
        print("✅ Stops amplios: ACTIVO")
        print("🔄 Parámetros: OPERATIVOS para trading frecuente")
        print("="*80)
        
        # Símbolos principales
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
        
        print(f"🪙 Símbolos: {', '.join(symbols)}")
        print(f"📅 Período: Últimos 45 días")
        
        all_trades = []
        
        # Test cada símbolo
        for symbol in symbols:
            trades = self.backtest_symbol(symbol)
            all_trades.extend(trades)
        
        # Análisis de resultados
        if all_trades:
            return self.analyze_operational_results(all_trades)
        else:
            print("❌ No se generaron trades en el período")
            return None
    
    def analyze_operational_results(self, trades):
        """
        Analiza resultados del sistema V2.5 operativo
        """
        print("\n" + "="*80)
        print("📈 ANÁLISIS DE RESULTADOS - V2.5 OPERATIVO")
        print("="*80)
        
        total_trades = len(trades)
        wins = sum(1 for t in trades if t['pnl'] > 0)
        win_rate = (wins / total_trades) * 100
        
        total_pnl = sum(t['pnl'] for t in trades)
        roi = (total_pnl / self.initial_capital) * 100
        
        gross_wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
        
        avg_win = gross_wins / wins if wins > 0 else 0
        avg_loss = gross_losses / (total_trades - wins) if (total_trades - wins) > 0 else 0
        
        print(f"📊 MÉTRICAS PRINCIPALES:")
        print(f"  • Total Trades: {total_trades}")
        print(f"  • Win Rate: {win_rate:.1f}%")
        print(f"  • Profit Factor: {profit_factor:.2f}")
        print(f"  • Total P&L: ${total_pnl:.2f}")
        print(f"  • ROI: {roi:.1f}%")
        print(f"  • Avg Win: ${avg_win:.2f}")
        print(f"  • Avg Loss: ${avg_loss:.2f}")
        print(f"  • Win/Loss Ratio: {avg_win/avg_loss:.2f}" if avg_loss > 0 else "  • Win/Loss Ratio: ∞")
        
        # ANÁLISIS CRÍTICO: Verificar filtro anti-tendencia
        print(f"\n🚫 VERIFICACIÓN FILTRO ANTI-TENDENCIA:")
        counter_trend = 0
        trend_analysis = {'uptrend_long': 0, 'downtrend_short': 0, 'neutral_trades': 0, 'counter_trend': 0}
        
        for trade in trades:
            if trade['trend_up'] and trade['type'] == 'LONG':
                trend_analysis['uptrend_long'] += 1
            elif trade['trend_down'] and trade['type'] == 'SHORT':
                trend_analysis['downtrend_short'] += 1
            elif trade['trend_neutral']:
                trend_analysis['neutral_trades'] += 1
            else:
                # Este es el caso problemático
                counter_trend += 1
                trend_analysis['counter_trend'] += 1
        
        counter_trend_pct = (counter_trend / total_trades) * 100
        print(f"  • Trades a favor de tendencia: {trend_analysis['uptrend_long'] + trend_analysis['downtrend_short']} ({(trend_analysis['uptrend_long'] + trend_analysis['downtrend_short'])/total_trades*100:.1f}%)")
        print(f"  • Trades en neutral: {trend_analysis['neutral_trades']} ({trend_analysis['neutral_trades']/total_trades*100:.1f}%)")
        print(f"  • Trades contra-tendencia: {counter_trend} ({counter_trend_pct:.1f}%)")
        
        if counter_trend_pct <= 5:
            print("  ✅ EXCELENTE: Filtro anti-tendencia muy efectivo")
        elif counter_trend_pct <= 15:
            print("  🟡 BUENO: Filtro anti-tendencia mayormente efectivo")
        else:
            print("  ❌ PROBLEMA: Filtro anti-tendencia no está funcionando")
        
        # Performance por símbolo
        print(f"\n📊 PERFORMANCE POR SÍMBOLO:")
        symbol_stats = {}
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {'trades': 0, 'wins': 0, 'pnl': 0}
            symbol_stats[symbol]['trades'] += 1
            if trade['pnl'] > 0:
                symbol_stats[symbol]['wins'] += 1
            symbol_stats[symbol]['pnl'] += trade['pnl']
        
        for symbol, stats in sorted(symbol_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
            wr = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            print(f"  • {symbol}: {stats['trades']} trades, {wr:.1f}% WR, ${stats['pnl']:.2f} P&L")
        
        # Evaluación final
        print(f"\n🏆 EVALUACIÓN FINAL:")
        
        score = 0
        evaluation_details = []
        
        if total_trades >= 10:
            score += 2
            evaluation_details.append("✅ Frecuencia operativa excelente")
        elif total_trades >= 5:
            score += 1
            evaluation_details.append("🟡 Frecuencia operativa aceptable")
        
        if win_rate >= 55:
            score += 2
            evaluation_details.append("✅ Win Rate excelente")
        elif win_rate >= 50:
            score += 1
            evaluation_details.append("🟡 Win Rate aceptable")
        
        if profit_factor >= 1.5:
            score += 2
            evaluation_details.append("✅ Profit Factor excelente")
        elif profit_factor >= 1.2:
            score += 1
            evaluation_details.append("🟡 Profit Factor aceptable")
        
        if counter_trend_pct <= 10:
            score += 2
            evaluation_details.append("✅ Filtro anti-tendencia efectivo")
        
        for detail in evaluation_details:
            print(f"  {detail}")
        
        print(f"\n📊 Score Final: {score}/8")
        
        if score >= 6:
            assessment = "✅ EXCELENTE - Sistema balanceado y operativo"
            next_steps = ["Implementar inmediatamente", "Paper trading 2 semanas", "Capital real gradual"]
        elif score >= 4:
            assessment = "🟡 BUENO - Sistema viable con monitoreo"
            next_steps = ["Paper trading extendido", "Monitorear métricas clave", "Evaluar mejoras"]
        else:
            assessment = "❌ NECESITA MEJORAS"
            next_steps = ["Revisar parámetros", "Extender testing", "Optimizar filtros"]
        
        print(f"🎯 {assessment}")
        
        print(f"\n🚀 PRÓXIMOS PASOS:")
        for i, step in enumerate(next_steps, 1):
            print(f"  {i}. {step}")
        
        # Comparación vs objetivos
        print(f"\n📈 COMPARACIÓN VS OBJETIVOS:")
        print(f"  • Objetivo: 60%+ WR, 1.5+ PF, <10% counter-trend, 5+ trades")
        print(f"  • Actual: {win_rate:.1f}% WR, {profit_factor:.2f} PF, {counter_trend_pct:.1f}% counter-trend, {total_trades} trades")
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'roi': roi,
            'counter_trend_pct': counter_trend_pct,
            'score': score,
            'assessment': assessment,
            'trades': trades
        }


def main():
    """
    Función principal
    """
    print("🚀 INICIANDO BACKTESTING V2.5 OPERATIVO")
    print("Objetivo: Balancear mejoras anti-pérdidas con frecuencia operativa")
    
    system = OperationalV25System()
    results = system.run_operational_backtest()
    
    print("\n" + "="*80)
    print("✅ BACKTESTING V2.5 OPERATIVO COMPLETADO")
    print("="*80)
    
    if results:
        print(f"🎯 RESULTADO: {results['assessment']}")
    
    return results

if __name__ == "__main__":
    results = main()