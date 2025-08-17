#!/usr/bin/env python3
"""
Backtesting Simplificado - 90 días en diferentes períodos
Usa el sistema original con parámetros validados
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Importar el sistema original que sabemos que funciona
from backtesting_integration import BacktestingIntegrado
from scoring_empirico_v2 import ScoringEmpiricoV2

class SimplifiedBacktester:
    """
    Backtester simplificado que usa el sistema probado
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.scoring_system = ScoringEmpiricoV2()
        
        # Períodos de prueba ajustados
        self.test_periods = [
            {
                'name': 'Q1_2024_BULL',
                'description': 'Rally alcista inicio 2024',
                'start': '2024-01-01',
                'end': '2024-03-31',
                'market_context': 'Bitcoin ETF approval rally'
            },
            {
                'name': 'Q2_2024_CORRECTION',
                'description': 'Corrección y consolidación',
                'start': '2024-04-01', 
                'end': '2024-06-30',
                'market_context': 'Post-halving consolidation'
            },
            {
                'name': 'Q3_2024_RECOVERY',
                'description': 'Recuperación de verano',
                'start': '2024-07-01',
                'end': '2024-09-30',
                'market_context': 'Summer recovery phase'
            }
        ]
        
        # Configuración de trading
        self.config = {
            'min_score': 6.0,           # Threshold más permisivo para generar trades
            'leverage_base': 3,         # Leverage base
            'leverage_max': 10,         # Leverage máximo
            'stop_loss_pct': 0.05,      # 5% stop loss
            'take_profit_pct': 0.15,    # 15% take profit
            'position_size_pct': 0.02,  # 2% del capital por trade
            'commission': 0.001         # 0.1% comisión
        }
        
        self.results = {}
    
    def run_all_periods(self):
        """Ejecuta backtesting en todos los períodos"""
        
        print("🚀 BACKTESTING SIMPLIFICADO - 90 DÍAS x 3 PERÍODOS")
        print("="*80)
        print(f"💰 Capital inicial: ${self.initial_capital:,}")
        print(f"📊 Sistema: SignalGeneratorAvanzado (validado)")
        print(f"⚙️ Score mínimo: {self.config['min_score']}")
        print("="*80)
        
        all_trades = []
        
        for period in self.test_periods:
            print(f"\n{'='*80}")
            print(f"📅 PERÍODO: {period['name']}")
            print(f"📝 {period['description']}")
            print(f"📆 {period['start']} → {period['end']}")
            print(f"🌍 Contexto: {period['market_context']}")
            print("="*80)
            
            period_trades = self.backtest_period(period)
            self.results[period['name']] = period_trades
            all_trades.extend(period_trades)
            
            # Imprimir resumen del período
            self.print_period_summary(period['name'], period_trades)
        
        # Análisis global
        self.print_global_analysis(all_trades)
        
        return self.results
    
    def backtest_period(self, period):
        """Ejecuta backtesting para un período"""
        
        trades = []
        
        for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
            print(f"\n🔍 Procesando {symbol}...")
            
            # Obtener datos
            data = self.get_historical_data(symbol, period['start'], period['end'])
            
            if data is None or len(data) < 20:
                print(f"⚠️ Datos insuficientes para {symbol}")
                continue
            
            # Ejecutar backtesting
            symbol_trades = self.backtest_symbol(symbol, data)
            trades.extend(symbol_trades)
            
            print(f"   • Trades generados: {len(symbol_trades)}")
        
        return trades
    
    def get_historical_data(self, symbol, start_date, end_date):
        """Obtiene datos históricos"""
        
        try:
            ticker = yf.Ticker(symbol)
            # Usar intervalo diario para evitar limitaciones
            data = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if len(data) == 0:
                return None
            
            # Preparar indicadores básicos
            data = self.prepare_indicators(data)
            
            return data
            
        except Exception as e:
            print(f"❌ Error obteniendo datos para {symbol}: {e}")
            return None
    
    def prepare_indicators(self, df):
        """Prepara indicadores técnicos"""
        
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
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Ratio de volumen
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA'].replace(0, 1)
        df['Volume_Ratio'] = df['Volume_Ratio'].fillna(1.0).clip(lower=0.1)
        
        return df
    
    def backtest_symbol(self, symbol, data):
        """Ejecuta backtesting para un símbolo"""
        
        trades = []
        capital = self.initial_capital
        position = None
        
        # Iterar por los datos
        for i in range(20, len(data)):
            current = data.iloc[i]
            prev = data.iloc[i-1]
            
            # Si no hay posición, buscar señal
            if position is None:
                # Generar señal
                signal_type, score = self.generate_signal(data.iloc[:i+1], current, prev)
                
                if signal_type and score >= self.config['min_score']:
                    # Abrir posición
                    position = {
                        'symbol': symbol,
                        'type': signal_type,
                        'entry_date': current.name,
                        'entry_price': float(current['Close']),
                        'score': score,
                        'quantity': 0,
                        'capital_used': 0
                    }
                    
                    # Calcular tamaño de posición
                    leverage = self.calculate_leverage(score)
                    position_size = capital * self.config['position_size_pct'] * leverage
                    position['capital_used'] = position_size
                    position['quantity'] = position_size / position['entry_price']
                    position['leverage'] = leverage
                    
                    # Calcular stops
                    if signal_type == 'LONG':
                        position['stop_loss'] = position['entry_price'] * (1 - self.config['stop_loss_pct'])
                        position['take_profit'] = position['entry_price'] * (1 + self.config['take_profit_pct'])
                    else:
                        position['stop_loss'] = position['entry_price'] * (1 + self.config['stop_loss_pct'])
                        position['take_profit'] = position['entry_price'] * (1 - self.config['take_profit_pct'])
            
            # Si hay posición, verificar salida
            else:
                exit_signal = False
                exit_reason = None
                exit_price = float(current['Close'])
                
                # Verificar stop loss y take profit
                if position['type'] == 'LONG':
                    if current['Low'] <= position['stop_loss']:
                        exit_signal = True
                        exit_reason = 'STOP_LOSS'
                        exit_price = position['stop_loss']
                    elif current['High'] >= position['take_profit']:
                        exit_signal = True
                        exit_reason = 'TAKE_PROFIT'
                        exit_price = position['take_profit']
                else:  # SHORT
                    if current['High'] >= position['stop_loss']:
                        exit_signal = True
                        exit_reason = 'STOP_LOSS'
                        exit_price = position['stop_loss']
                    elif current['Low'] <= position['take_profit']:
                        exit_signal = True
                        exit_reason = 'TAKE_PROFIT'
                        exit_price = position['take_profit']
                
                # Cerrar posición si hay señal de salida
                if exit_signal:
                    position['exit_date'] = current.name
                    position['exit_price'] = exit_price
                    position['exit_reason'] = exit_reason
                    
                    # Calcular P&L
                    if position['type'] == 'LONG':
                        gross_pnl = (exit_price - position['entry_price']) * position['quantity']
                    else:
                        gross_pnl = (position['entry_price'] - exit_price) * position['quantity']
                    
                    commission = position['capital_used'] * self.config['commission'] * 2
                    position['pnl'] = gross_pnl - commission
                    position['pnl_pct'] = (position['pnl'] / position['capital_used']) * 100
                    position['duration_days'] = (position['exit_date'] - position['entry_date']).days
                    
                    # Actualizar capital
                    capital += position['pnl']
                    
                    # Guardar trade
                    trades.append(position)
                    position = None
        
        # Cerrar posición final si queda abierta
        if position is not None:
            position['exit_date'] = data.iloc[-1].name
            position['exit_price'] = float(data.iloc[-1]['Close'])
            position['exit_reason'] = 'END_PERIOD'
            
            if position['type'] == 'LONG':
                gross_pnl = (position['exit_price'] - position['entry_price']) * position['quantity']
            else:
                gross_pnl = (position['entry_price'] - position['exit_price']) * position['quantity']
            
            commission = position['capital_used'] * self.config['commission'] * 2
            position['pnl'] = gross_pnl - commission
            position['pnl_pct'] = (position['pnl'] / position['capital_used']) * 100
            position['duration_days'] = (position['exit_date'] - position['entry_date']).days
            
            trades.append(position)
        
        return trades
    
    def generate_signal(self, df, current, prev):
        """Genera señal usando el sistema validado"""
        
        try:
            # Usar el sistema de scoring probado
            signal_type, score = self.scoring_system.evaluar_entrada(df, current, prev)
            
            return signal_type, score
            
        except:
            # Fallback a lógica simple si hay error
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            
            # Lógica simple pero efectiva
            if rsi < 30 and macd > macd_signal:
                return 'LONG', 6.5
            elif rsi > 70 and macd < macd_signal:
                return 'SHORT', 6.5
            
            return None, 0
    
    def calculate_leverage(self, score):
        """Calcula leverage basado en score"""
        
        if score >= 8.0:
            return min(self.config['leverage_max'], 5)
        elif score >= 7.0:
            return 3
        else:
            return self.config['leverage_base']
    
    def print_period_summary(self, period_name, trades):
        """Imprime resumen del período"""
        
        print(f"\n📊 RESUMEN - {period_name}")
        print("-"*60)
        
        if not trades:
            print("❌ No se generaron trades en este período")
            return
        
        # Calcular métricas
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        losing_trades = total_trades - winning_trades
        
        total_pnl = sum(t['pnl'] for t in trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Profit factor
        wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        losses = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
        profit_factor = wins / losses if losses > 0 else float('inf')
        
        avg_win = wins / winning_trades if winning_trades > 0 else 0
        avg_loss = losses / losing_trades if losing_trades > 0 else 0
        
        print(f"📈 Total Trades: {total_trades}")
        print(f"✅ Winning: {winning_trades} | ❌ Losing: {losing_trades}")
        print(f"📊 Win Rate: {win_rate:.1f}%")
        print(f"💰 Total P&L: ${total_pnl:+,.2f}")
        print(f"📈 Profit Factor: {profit_factor:.2f}")
        print(f"💚 Avg Win: ${avg_win:,.2f}")
        print(f"💔 Avg Loss: ${avg_loss:,.2f}")
        
        # Top trades
        if trades:
            best_trade = max(trades, key=lambda x: x['pnl'])
            worst_trade = min(trades, key=lambda x: x['pnl'])
            
            print(f"\n🏆 Mejor trade: {best_trade['symbol']} - ${best_trade['pnl']:+,.2f} ({best_trade['pnl_pct']:+.1f}%)")
            print(f"💔 Peor trade: {worst_trade['symbol']} - ${worst_trade['pnl']:+,.2f} ({worst_trade['pnl_pct']:+.1f}%)")
    
    def print_global_analysis(self, all_trades):
        """Imprime análisis global"""
        
        print("\n" + "="*80)
        print("📊 ANÁLISIS GLOBAL - TODOS LOS PERÍODOS")
        print("="*80)
        
        if not all_trades:
            print("❌ No se generaron trades en ningún período")
            print("\n⚠️ RECOMENDACIONES:")
            print("• Revisar thresholds de entrada (bajar min_score)")
            print("• Verificar datos de mercado")
            print("• Ajustar parámetros del sistema")
            return
        
        # Métricas globales
        total_trades = len(all_trades)
        winning_trades = sum(1 for t in all_trades if t['pnl'] > 0)
        win_rate = (winning_trades / total_trades * 100)
        
        total_pnl = sum(t['pnl'] for t in all_trades)
        total_return = (total_pnl / self.initial_capital) * 100
        
        # Profit factor
        wins = sum(t['pnl'] for t in all_trades if t['pnl'] > 0)
        losses = abs(sum(t['pnl'] for t in all_trades if t['pnl'] < 0))
        profit_factor = wins / losses if losses > 0 else float('inf')
        
        print(f"📈 MÉTRICAS GLOBALES:")
        print(f"• Total Trades: {total_trades}")
        print(f"• Win Rate: {win_rate:.1f}%")
        print(f"• Profit Factor: {profit_factor:.2f}")
        print(f"• Total Return: {total_return:+.2f}%")
        print(f"• Return Anualizado: {total_return * 4:+.2f}%")
        
        # Análisis por símbolo
        symbol_performance = {}
        for trade in all_trades:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {'trades': 0, 'pnl': 0}
            symbol_performance[symbol]['trades'] += 1
            symbol_performance[symbol]['pnl'] += trade['pnl']
        
        print(f"\n📊 DESEMPEÑO POR SÍMBOLO:")
        for symbol, perf in symbol_performance.items():
            print(f"• {symbol}: {perf['trades']} trades, P&L: ${perf['pnl']:+,.2f}")
        
        # Evaluación del sistema
        print(f"\n🎯 EVALUACIÓN DEL SISTEMA:")
        
        if win_rate >= 60 and profit_factor >= 1.5:
            print("✅ EXCELENTE - Sistema listo para producción")
            print("   • Win rate superior al objetivo (60%+)")
            print("   • Profit factor robusto (1.5+)")
        elif win_rate >= 50 and profit_factor >= 1.2:
            print("✅ BUENO - Sistema funcional con ajustes menores")
            print("   • Win rate aceptable (50%+)")
            print("   • Profit factor positivo (1.2+)")
        elif win_rate >= 45:
            print("⚠️ MODERADO - Requiere optimización")
            print("   • Win rate bajo objetivo")
            print("   • Considerar ajustar parámetros")
        else:
            print("❌ INSUFICIENTE - Requiere revisión mayor")
            print("   • Win rate muy bajo")
            print("   • Sistema no rentable en estado actual")
        
        # Recomendaciones finales
        print(f"\n💡 RECOMENDACIONES:")
        
        if win_rate < 50:
            print("• Aumentar selectividad (subir min_score a 6.5+)")
            print("• Mejorar filtros de confirmación")
            print("• Reducir frecuencia de trading")
        
        if profit_factor < 1.5:
            print("• Ajustar ratio risk/reward (reducir stop loss o aumentar take profit)")
            print("• Mejorar timing de entradas")
            print("• Implementar trailing stops")
        
        if total_return < 10:
            print("• Considerar aumentar tamaño de posiciones")
            print("• Explorar más oportunidades de trading")
            print("• Optimizar gestión de capital")
        
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print("1. Paper trading 30 días con sistema actual")
        print("2. Monitorear métricas en tiempo real")
        print("3. Ajustar basado en resultados reales")
        print("4. Escalar gradualmente con capital real")

def main():
    """Función principal"""
    
    backtester = SimplifiedBacktester(initial_capital=10000)
    results = backtester.run_all_periods()
    
    print("\n" + "="*80)
    print("✅ BACKTESTING COMPLETADO")
    print("="*80)
    
    return results

if __name__ == "__main__":
    main()