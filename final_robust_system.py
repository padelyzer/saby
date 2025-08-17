#!/usr/bin/env python3
"""
Sistema Final Robusto - Versión Simplificada y Validada
Basado en los aprendizajes del rediseño
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class FinalRobustSystem:
    """
    Sistema final con parámetros robustos y validados
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Parámetros finales basados en análisis previo
        # Estos son conservadores pero consistentes
        self.params = {
            'rsi_oversold': 35,
            'rsi_overbought': 65,
            'min_volume_ratio': 1.1,
            'atr_stop_multiplier': 1.5,
            'atr_target_multiplier': 2.0,
            'risk_per_trade': 0.02,  # 2% riesgo
            'max_position_size': 0.25,  # 25% máximo del capital
            'min_trade_interval_days': 1,
            'trend_filter': True,
            'confirmation_required': 2
        }
        
        self.trades = []
        self.positions = {}
        
    def calculate_indicators(self, df):
        """
        Calcula indicadores técnicos esenciales
        """
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 1)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # EMAs para tendencia
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # ATR para volatilidad
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volume ratio
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        return df
    
    def check_trend(self, df, idx):
        """
        Verifica la tendencia actual
        """
        if idx < 50:
            return 'NEUTRAL'
        
        current = df.iloc[idx]
        
        # Tendencia alcista
        if current['EMA20'] > current['EMA50'] and current['Close'] > current['EMA20']:
            return 'BULLISH'
        # Tendencia bajista
        elif current['EMA20'] < current['EMA50'] and current['Close'] < current['EMA20']:
            return 'BEARISH'
        
        return 'NEUTRAL'
    
    def generate_signal(self, df, idx):
        """
        Genera señales de trading simples pero efectivas
        """
        if idx < 50:
            return None
        
        current = df.iloc[idx]
        prev = df.iloc[idx-1]
        
        confirmations_long = 0
        confirmations_short = 0
        
        # Condiciones LONG
        # 1. RSI oversold
        if current['RSI'] < self.params['rsi_oversold']:
            confirmations_long += 1
        
        # 2. MACD cruce alcista
        if prev['MACD'] < prev['Signal'] and current['MACD'] > current['Signal']:
            confirmations_long += 1
        
        # 3. Volumen alto
        if current['Volume_Ratio'] > self.params['min_volume_ratio']:
            confirmations_long += 0.5
        
        # 4. Tendencia alcista (si está activado el filtro)
        if self.params['trend_filter']:
            trend = self.check_trend(df, idx)
            if trend == 'BULLISH':
                confirmations_long += 1
        
        # Condiciones SHORT
        # 1. RSI overbought
        if current['RSI'] > self.params['rsi_overbought']:
            confirmations_short += 1
        
        # 2. MACD cruce bajista
        if prev['MACD'] > prev['Signal'] and current['MACD'] < current['Signal']:
            confirmations_short += 1
        
        # 3. Volumen alto
        if current['Volume_Ratio'] > self.params['min_volume_ratio']:
            confirmations_short += 0.5
        
        # 4. Tendencia bajista (si está activado el filtro)
        if self.params['trend_filter']:
            trend = self.check_trend(df, idx)
            if trend == 'BEARISH':
                confirmations_short += 1
        
        # Generar señal si hay suficientes confirmaciones
        min_conf = self.params['confirmation_required']
        
        if confirmations_long >= min_conf and confirmations_long > confirmations_short:
            return 'LONG'
        elif confirmations_short >= min_conf and confirmations_short > confirmations_long:
            return 'SHORT'
        
        return None
    
    def calculate_position_size(self, capital, entry_price, stop_price):
        """
        Calcula el tamaño de posición basado en el riesgo
        """
        risk_amount = capital * self.params['risk_per_trade']
        price_diff = abs(entry_price - stop_price)
        
        if price_diff == 0:
            return 0
        
        shares = risk_amount / price_diff
        position_value = shares * entry_price
        
        # Limitar al máximo permitido
        max_value = capital * self.params['max_position_size']
        if position_value > max_value:
            shares = max_value / entry_price
        
        return shares
    
    def backtest(self, symbol, start_date, end_date):
        """
        Ejecuta backtesting del sistema
        """
        print(f"\n📊 Backtesting {symbol}")
        print(f"   Period: {start_date} → {end_date}")
        
        # Obtener datos
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval='1d')
        
        if len(df) < 50:
            print("   ❌ Insufficient data")
            return []
        
        # Calcular indicadores
        df = self.calculate_indicators(df)
        
        # Variables de tracking
        trades = []
        position = None
        last_trade_date = None
        capital = self.initial_capital
        
        # Iterar por cada día
        for i in range(50, len(df)):
            current_date = df.index[i]
            current = df.iloc[i]
            
            # Si no hay posición abierta
            if position is None:
                # Verificar intervalo mínimo entre trades
                if last_trade_date:
                    days_since = (current_date - last_trade_date).days
                    if days_since < self.params['min_trade_interval_days']:
                        continue
                
                # Generar señal
                signal = self.generate_signal(df, i)
                
                if signal:
                    # Calcular stops
                    atr = current['ATR']
                    
                    if signal == 'LONG':
                        stop_loss = current['Close'] - (atr * self.params['atr_stop_multiplier'])
                        take_profit = current['Close'] + (atr * self.params['atr_target_multiplier'])
                    else:  # SHORT
                        stop_loss = current['Close'] + (atr * self.params['atr_stop_multiplier'])
                        take_profit = current['Close'] - (atr * self.params['atr_target_multiplier'])
                    
                    # Calcular tamaño
                    shares = self.calculate_position_size(capital, current['Close'], stop_loss)
                    
                    if shares > 0:
                        position = {
                            'symbol': symbol,
                            'type': signal,
                            'entry_date': current_date,
                            'entry_price': current['Close'],
                            'shares': shares,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'entry_rsi': current['RSI']
                        }
                        
                        last_trade_date = current_date
            
            # Si hay posición abierta, verificar salida
            else:
                exit_triggered = False
                exit_price = current['Close']
                exit_reason = ''
                
                if position['type'] == 'LONG':
                    if current['Low'] <= position['stop_loss']:
                        exit_triggered = True
                        exit_price = position['stop_loss']
                        exit_reason = 'Stop Loss'
                    elif current['High'] >= position['take_profit']:
                        exit_triggered = True
                        exit_price = position['take_profit']
                        exit_reason = 'Take Profit'
                else:  # SHORT
                    if current['High'] >= position['stop_loss']:
                        exit_triggered = True
                        exit_price = position['stop_loss']
                        exit_reason = 'Stop Loss'
                    elif current['Low'] <= position['take_profit']:
                        exit_triggered = True
                        exit_price = position['take_profit']
                        exit_reason = 'Take Profit'
                
                if exit_triggered:
                    # Calcular resultado
                    if position['type'] == 'LONG':
                        pnl = (exit_price - position['entry_price']) * position['shares']
                        return_pct = ((exit_price / position['entry_price']) - 1) * 100
                    else:
                        pnl = (position['entry_price'] - exit_price) * position['shares']
                        return_pct = ((position['entry_price'] / exit_price) - 1) * 100
                    
                    # Registrar trade
                    trade = {
                        **position,
                        'exit_date': current_date,
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'pnl': pnl,
                        'return_pct': return_pct,
                        'duration_days': (current_date - position['entry_date']).days
                    }
                    
                    trades.append(trade)
                    capital += pnl
                    position = None
        
        # Cerrar posición final si existe
        if position:
            last_price = df.iloc[-1]['Close']
            
            if position['type'] == 'LONG':
                pnl = (last_price - position['entry_price']) * position['shares']
                return_pct = ((last_price / position['entry_price']) - 1) * 100
            else:
                pnl = (position['entry_price'] - last_price) * position['shares']
                return_pct = ((position['entry_price'] / last_price) - 1) * 100
            
            trade = {
                **position,
                'exit_date': df.index[-1],
                'exit_price': last_price,
                'exit_reason': 'End of Period',
                'pnl': pnl,
                'return_pct': return_pct,
                'duration_days': (df.index[-1] - position['entry_date']).days
            }
            
            trades.append(trade)
        
        return trades
    
    def analyze_performance(self, trades):
        """
        Analiza el performance de los trades
        """
        if not trades:
            return None
        
        # Métricas básicas
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Returns
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (total_pnl / self.initial_capital) * 100
        
        # Average trade
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 0
        avg_return = np.mean([t['return_pct'] for t in trades])
        
        # Risk metrics
        returns = [t['return_pct'] for t in trades]
        sharpe = np.mean(returns) / (np.std(returns) + 0.0001) if len(returns) > 1 else 0
        
        # Max drawdown
        cumulative = []
        cum_pnl = 0
        for t in sorted(trades, key=lambda x: x['entry_date']):
            cum_pnl += t['pnl']
            cumulative.append(cum_pnl)
        
        if cumulative:
            peak = cumulative[0]
            max_dd = 0
            for val in cumulative:
                peak = max(peak, val)
                dd = (peak - val) / self.initial_capital * 100 if peak > 0 else 0
                max_dd = max(max_dd, dd)
        else:
            max_dd = 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd
        }
    
    def run_full_test(self):
        """
        Ejecuta test completo con múltiples períodos y símbolos
        """
        print("="*80)
        print("🚀 FINAL ROBUST SYSTEM - COMPREHENSIVE TEST")
        print("="*80)
        
        # Configuración de test
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        periods = [
            {'name': '2023_Full', 'start': '2023-01-01', 'end': '2023-12-31'},
            {'name': '2024_YTD', 'start': '2024-01-01', 'end': '2024-11-15'}
        ]
        
        all_results = []
        
        for period in periods:
            print(f"\n📅 PERIOD: {period['name']}")
            print(f"   {period['start']} → {period['end']}")
            print("-"*60)
            
            period_trades = []
            
            for symbol in symbols:
                trades = self.backtest(symbol, period['start'], period['end'])
                
                if trades:
                    metrics = self.analyze_performance(trades)
                    print(f"\n   {symbol} Results:")
                    print(f"     • Trades: {metrics['total_trades']}")
                    print(f"     • Win Rate: {metrics['win_rate']:.1f}%")
                    print(f"     • Profit Factor: {metrics['profit_factor']:.2f}")
                    print(f"     • Return: {metrics['total_return']:.1f}%")
                    
                    period_trades.extend(trades)
                else:
                    print(f"\n   {symbol}: No trades")
            
            # Análisis del período completo
            if period_trades:
                period_metrics = self.analyze_performance(period_trades)
                all_results.append({
                    'period': period['name'],
                    'metrics': period_metrics,
                    'trades': period_trades
                })
                
                print(f"\n   📊 PERIOD SUMMARY:")
                print(f"     • Total Trades: {period_metrics['total_trades']}")
                print(f"     • Win Rate: {period_metrics['win_rate']:.1f}%")
                print(f"     • Profit Factor: {period_metrics['profit_factor']:.2f}")
                print(f"     • Total Return: {period_metrics['total_return']:.1f}%")
                print(f"     • Sharpe Ratio: {period_metrics['sharpe_ratio']:.2f}")
                print(f"     • Max Drawdown: {period_metrics['max_drawdown']:.1f}%")
        
        # Análisis global
        self.print_final_analysis(all_results)
        
        return all_results
    
    def print_final_analysis(self, results):
        """
        Imprime análisis final del sistema
        """
        print("\n" + "="*80)
        print("📊 FINAL SYSTEM ANALYSIS")
        print("="*80)
        
        if not results:
            print("❌ No results to analyze")
            return
        
        # Combinar todos los trades
        all_trades = []
        for r in results:
            all_trades.extend(r['trades'])
        
        if all_trades:
            final_metrics = self.analyze_performance(all_trades)
            
            print("\n🎯 OVERALL METRICS:")
            print(f"  • Total Trades: {final_metrics['total_trades']}")
            print(f"  • Win Rate: {final_metrics['win_rate']:.1f}%")
            print(f"  • Profit Factor: {final_metrics['profit_factor']:.2f}")
            print(f"  • Total Return: {final_metrics['total_return']:.1f}%")
            print(f"  • Average Return per Trade: {final_metrics['avg_return']:.2f}%")
            print(f"  • Sharpe Ratio: {final_metrics['sharpe_ratio']:.2f}")
            print(f"  • Max Drawdown: {final_metrics['max_drawdown']:.1f}%")
            
            # Evaluación
            print("\n📈 SYSTEM EVALUATION:")
            
            score = 0
            if final_metrics['win_rate'] >= 45:
                score += 1
                print("  ✅ Win rate acceptable (>45%)")
            else:
                print("  ❌ Win rate too low (<45%)")
            
            if final_metrics['profit_factor'] >= 1.2:
                score += 1
                print("  ✅ Profit factor good (>1.2)")
            else:
                print("  ❌ Profit factor insufficient (<1.2)")
            
            if final_metrics['sharpe_ratio'] >= 0.5:
                score += 1
                print("  ✅ Risk-adjusted returns acceptable (Sharpe >0.5)")
            else:
                print("  ❌ Poor risk-adjusted returns (Sharpe <0.5)")
            
            if final_metrics['max_drawdown'] <= 25:
                score += 1
                print("  ✅ Drawdown controlled (<25%)")
            else:
                print("  ⚠️ High drawdown (>25%)")
            
            print(f"\n🏆 FINAL SCORE: {score}/4")
            
            if score >= 3:
                print("\n✅ SYSTEM READY FOR PAPER TRADING")
                print("   Recommended next steps:")
                print("   1. Run 30-day paper trading")
                print("   2. Monitor real-time performance")
                print("   3. Adjust parameters if needed")
                print("   4. Start with small real capital")
            elif score >= 2:
                print("\n⚠️ SYSTEM NEEDS REFINEMENT")
                print("   Consider:")
                print("   1. Adjusting entry filters")
                print("   2. Improving risk management")
                print("   3. Adding market regime filters")
            else:
                print("\n❌ SYSTEM NOT READY")
                print("   Major improvements needed")

def main():
    """
    Función principal
    """
    system = FinalRobustSystem(initial_capital=10000)
    results = system.run_full_test()
    
    # Guardar configuración si es exitosa
    if results:
        config = {
            'date': datetime.now().isoformat(),
            'system': 'FinalRobustSystem',
            'parameters': system.params,
            'test_results': {
                'periods_tested': len(results),
                'total_trades': sum(r['metrics']['total_trades'] for r in results),
                'average_win_rate': np.mean([r['metrics']['win_rate'] for r in results]),
                'average_profit_factor': np.mean([r['metrics']['profit_factor'] for r in results])
            }
        }
        
        with open('final_system_config.json', 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print("\n💾 Configuration saved to 'final_system_config.json'")
    
    return results

if __name__ == "__main__":
    results = main()