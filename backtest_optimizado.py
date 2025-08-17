#!/usr/bin/env python3
"""
Sistema de Backtesting Optimizado - Mayor Win Rate
Incluye filtros mejorados y confirmaciones múltiples
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class OptimizedBacktest:
    """Sistema optimizado con mayor win rate"""
    
    def __init__(self, capital_inicial=10000):
        self.capital_inicial = capital_inicial
        self.capital = capital_inicial
        self.position_size = 0.10  # 10% por trade (más conservador)
        self.trades = []
        
    def calculate_trend_strength(self, df, lookback=50):
        """Calcula la fuerza de la tendencia"""
        if len(df) < lookback:
            return 0
            
        # Pendiente de la regresión lineal
        prices = df['Close'].tail(lookback).values
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        
        # Normalizar por el precio actual
        trend_strength = (slope / prices[-1]) * 100
        
        return trend_strength
    
    def calculate_atr(self, df, period=14):
        """Calcula el Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        
        return atr
    
    def is_support_resistance(self, df, price, tolerance=0.02):
        """Verifica si el precio está en zona de soporte/resistencia"""
        if len(df) < 100:
            return False, None
            
        # Buscar máximos y mínimos históricos
        highs = df['High'].tail(100)
        lows = df['Low'].tail(100)
        
        # Contar toques en la zona
        zone_high = price * (1 + tolerance)
        zone_low = price * (1 - tolerance)
        
        touches = 0
        touches += ((highs >= zone_low) & (highs <= zone_high)).sum()
        touches += ((lows >= zone_low) & (lows <= zone_high)).sum()
        
        # Si hay más de 3 toques, es una zona importante
        if touches >= 3:
            # Determinar si es soporte o resistencia
            current_price = df['Close'].iloc[-1]
            if current_price < price:
                return True, 'resistance'
            else:
                return True, 'support'
                
        return False, None
    
    def calculate_volume_profile(self, df, periods=20):
        """Analiza el perfil de volumen"""
        if len(df) < periods:
            return 0
            
        # Volumen promedio
        avg_volume = df['Volume'].tail(periods).mean()
        current_volume = df['Volume'].iloc[-1]
        
        # Ratio de volumen
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Volumen en tendencia
        price_change = (df['Close'].iloc[-1] / df['Close'].iloc[-periods] - 1) * 100
        
        # Alto volumen + movimiento de precio = confirmación
        if volume_ratio > 1.5 and abs(price_change) > 1:
            return 2  # Fuerte confirmación
        elif volume_ratio > 1.2:
            return 1  # Confirmación moderada
        else:
            return 0  # Sin confirmación
    
    def calculate_market_structure(self, df):
        """Analiza la estructura del mercado (HH, HL, LL, LH)"""
        if len(df) < 20:
            return 'undefined'
            
        # Encontrar pivotes
        highs = []
        lows = []
        
        for i in range(2, len(df)-2):
            # High pivot
            if (df['High'].iloc[i] > df['High'].iloc[i-1] and 
                df['High'].iloc[i] > df['High'].iloc[i-2] and
                df['High'].iloc[i] > df['High'].iloc[i+1] and
                df['High'].iloc[i] > df['High'].iloc[i+2]):
                highs.append((i, df['High'].iloc[i]))
            
            # Low pivot
            if (df['Low'].iloc[i] < df['Low'].iloc[i-1] and 
                df['Low'].iloc[i] < df['Low'].iloc[i-2] and
                df['Low'].iloc[i] < df['Low'].iloc[i+1] and
                df['Low'].iloc[i] < df['Low'].iloc[i+2]):
                lows.append((i, df['Low'].iloc[i]))
        
        if len(highs) >= 2 and len(lows) >= 2:
            # Últimos dos highs y lows
            last_high = highs[-1][1]
            prev_high = highs[-2][1]
            last_low = lows[-1][1]
            prev_low = lows[-2][1]
            
            # Determinar estructura
            if last_high > prev_high and last_low > prev_low:
                return 'bullish'  # Higher High, Higher Low
            elif last_high < prev_high and last_low < prev_low:
                return 'bearish'  # Lower High, Lower Low
            else:
                return 'ranging'  # Lateral
        
        return 'undefined'
    
    def momentum_strategy_optimized(self, df, ticker):
        """Estrategia de Momentum con filtros mejorados"""
        signals = []
        
        if len(df) < 200:
            return signals
            
        # Calcular indicadores
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['SMA_200'] = df['Close'].rolling(200).mean()
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ATR para stops dinámicos
        df['ATR'] = self.calculate_atr(df)
        
        # Análisis de últimas 200 barras para más oportunidades
        for i in range(max(200, len(df)-200), len(df)-1):
            current_idx = i
            current_price = df['Close'].iloc[current_idx]
            
            # === FILTROS PRINCIPALES ===
            
            # 1. Tendencia principal
            trend_strength = self.calculate_trend_strength(df.iloc[:current_idx+1])
            market_structure = self.calculate_market_structure(df.iloc[:current_idx+1])
            
            # 2. Confirmación de volumen
            volume_confirm = self.calculate_volume_profile(df.iloc[:current_idx+1])
            
            # 3. Niveles clave
            is_key_level, level_type = self.is_support_resistance(df.iloc[:current_idx+1], current_price)
            
            # === SEÑALES LONG ===
            if (market_structure in ['bullish', 'ranging']) and trend_strength > 0.2:  # Más flexible
                
                # Condiciones para LONG
                conditions_met = 0
                
                # 1. Cruce de medias
                if (df['SMA_20'].iloc[current_idx] > df['SMA_50'].iloc[current_idx] and
                    df['SMA_20'].iloc[current_idx-1] <= df['SMA_50'].iloc[current_idx-1]):
                    conditions_met += 2
                
                # 2. MACD positivo
                if df['MACD'].iloc[current_idx] > df['MACD_Signal'].iloc[current_idx]:
                    conditions_met += 1
                
                # 3. RSI en zona óptima (40-70)
                if 40 <= df['RSI'].iloc[current_idx] <= 70:
                    conditions_met += 1
                
                # 4. Precio sobre SMA 200
                if current_price > df['SMA_200'].iloc[current_idx]:
                    conditions_met += 1
                
                # 5. Confirmación de volumen
                conditions_met += volume_confirm
                
                # 6. Rebote en soporte
                if is_key_level and level_type == 'support':
                    conditions_met += 2
                
                # 7. Momentum positivo reciente
                momentum_5d = (current_price / df['Close'].iloc[current_idx-5] - 1) * 100
                if momentum_5d > 2:
                    conditions_met += 1
                
                # ENTRADA si cumple suficientes condiciones
                if conditions_met >= 5:  # Reducir requisito de 6 a 5
                    # Stop y Target dinámicos basados en ATR
                    atr = df['ATR'].iloc[current_idx]
                    
                    signal = {
                        'date': df.index[current_idx],
                        'ticker': ticker,
                        'type': 'LONG',
                        'entry_price': current_price,
                        'stop_loss': current_price - (atr * 1.5),  # 1.5 ATR stop
                        'take_profit': current_price + (atr * 3),   # 3 ATR target (2:1 ratio)
                        'confidence': conditions_met,
                        'atr': atr
                    }
                    signals.append(signal)
            
            # === SEÑALES SHORT ===
            elif (market_structure in ['bearish', 'ranging']) and trend_strength < -0.2:  # Más flexible
                
                conditions_met = 0
                
                # 1. Cruce de medias bajista
                if (df['SMA_20'].iloc[current_idx] < df['SMA_50'].iloc[current_idx] and
                    df['SMA_20'].iloc[current_idx-1] >= df['SMA_50'].iloc[current_idx-1]):
                    conditions_met += 2
                
                # 2. MACD negativo
                if df['MACD'].iloc[current_idx] < df['MACD_Signal'].iloc[current_idx]:
                    conditions_met += 1
                
                # 3. RSI en zona óptima (30-60)
                if 30 <= df['RSI'].iloc[current_idx] <= 60:
                    conditions_met += 1
                
                # 4. Precio bajo SMA 200
                if current_price < df['SMA_200'].iloc[current_idx]:
                    conditions_met += 1
                
                # 5. Confirmación de volumen
                conditions_met += volume_confirm
                
                # 6. Rechazo en resistencia
                if is_key_level and level_type == 'resistance':
                    conditions_met += 2
                
                # 7. Momentum negativo reciente
                momentum_5d = (current_price / df['Close'].iloc[current_idx-5] - 1) * 100
                if momentum_5d < -2:
                    conditions_met += 1
                
                # ENTRADA si cumple suficientes condiciones
                if conditions_met >= 5:  # Reducir requisito de 6 a 5
                    atr = df['ATR'].iloc[current_idx]
                    
                    signal = {
                        'date': df.index[current_idx],
                        'ticker': ticker,
                        'type': 'SHORT',
                        'entry_price': current_price,
                        'stop_loss': current_price + (atr * 1.5),
                        'take_profit': current_price - (atr * 3),
                        'confidence': conditions_met,
                        'atr': atr
                    }
                    signals.append(signal)
        
        return signals
    
    def mean_reversion_optimized(self, df, ticker):
        """Estrategia Mean Reversion con filtros mejorados"""
        signals = []
        
        if len(df) < 50:
            return signals
            
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ATR
        df['ATR'] = self.calculate_atr(df)
        
        for i in range(max(50, len(df)-100), len(df)-1):
            current_idx = i
            current_price = df['Close'].iloc[current_idx]
            
            # Verificar que estamos en rango (no tendencia fuerte)
            trend_strength = self.calculate_trend_strength(df.iloc[:current_idx+1], lookback=20)
            
            if abs(trend_strength) < 1:  # Mercado lateral
                
                # LONG en oversold
                if (current_price <= df['BB_Lower'].iloc[current_idx] and
                    df['RSI'].iloc[current_idx] < 30):
                    
                    # Confirmaciones adicionales
                    conditions_met = 3  # Ya cumple 2 condiciones principales
                    
                    # Divergencia alcista en RSI
                    if (df['RSI'].iloc[current_idx] > df['RSI'].iloc[current_idx-5] and
                        current_price < df['Close'].iloc[current_idx-5]):
                        conditions_met += 2
                    
                    # Volumen alto
                    volume_confirm = self.calculate_volume_profile(df.iloc[:current_idx+1], periods=10)
                    conditions_met += volume_confirm
                    
                    # Martillo o patrón de reversión
                    body = abs(df['Close'].iloc[current_idx] - df['Open'].iloc[current_idx])
                    lower_shadow = df['Open'].iloc[current_idx] - df['Low'].iloc[current_idx]
                    if lower_shadow > body * 2:  # Martillo
                        conditions_met += 1
                    
                    if conditions_met >= 5:
                        atr = df['ATR'].iloc[current_idx]
                        
                        signal = {
                            'date': df.index[current_idx],
                            'ticker': ticker,
                            'type': 'LONG',
                            'entry_price': current_price,
                            'stop_loss': df['BB_Lower'].iloc[current_idx] - (atr * 0.5),
                            'take_profit': df['BB_Middle'].iloc[current_idx],  # Target: media
                            'confidence': conditions_met,
                            'atr': atr
                        }
                        signals.append(signal)
                
                # SHORT en overbought
                elif (current_price >= df['BB_Upper'].iloc[current_idx] and
                      df['RSI'].iloc[current_idx] > 70):
                    
                    conditions_met = 3
                    
                    # Divergencia bajista en RSI
                    if (df['RSI'].iloc[current_idx] < df['RSI'].iloc[current_idx-5] and
                        current_price > df['Close'].iloc[current_idx-5]):
                        conditions_met += 2
                    
                    # Volumen alto
                    volume_confirm = self.calculate_volume_profile(df.iloc[:current_idx+1], periods=10)
                    conditions_met += volume_confirm
                    
                    # Shooting star o patrón de reversión
                    body = abs(df['Close'].iloc[current_idx] - df['Open'].iloc[current_idx])
                    upper_shadow = df['High'].iloc[current_idx] - df['Close'].iloc[current_idx]
                    if upper_shadow > body * 2:  # Shooting star
                        conditions_met += 1
                    
                    if conditions_met >= 5:
                        atr = df['ATR'].iloc[current_idx]
                        
                        signal = {
                            'date': df.index[current_idx],
                            'ticker': ticker,
                            'type': 'SHORT',
                            'entry_price': current_price,
                            'stop_loss': df['BB_Upper'].iloc[current_idx] + (atr * 0.5),
                            'take_profit': df['BB_Middle'].iloc[current_idx],
                            'confidence': conditions_met,
                            'atr': atr
                        }
                        signals.append(signal)
        
        return signals
    
    def simulate_trades(self, signals, df):
        """Simula la ejecución de trades con las señales optimizadas"""
        
        for signal in signals:
            # Buscar índice de entrada
            entry_idx = df.index.get_loc(signal['date'])
            
            if entry_idx >= len(df) - 2:
                continue
                
            # Simular desde el siguiente período
            exit_price = None
            exit_reason = None
            exit_date = None
            
            for j in range(entry_idx + 1, min(entry_idx + 100, len(df))):
                current_bar = df.iloc[j]
                
                # Verificar TP/SL
                if signal['type'] == 'LONG':
                    if current_bar['High'] >= signal['take_profit']:
                        exit_price = signal['take_profit']
                        exit_reason = 'TP'
                        exit_date = current_bar.name
                        break
                    elif current_bar['Low'] <= signal['stop_loss']:
                        exit_price = signal['stop_loss']
                        exit_reason = 'SL'
                        exit_date = current_bar.name
                        break
                
                else:  # SHORT
                    if current_bar['Low'] <= signal['take_profit']:
                        exit_price = signal['take_profit']
                        exit_reason = 'TP'
                        exit_date = current_bar.name
                        break
                    elif current_bar['High'] >= signal['stop_loss']:
                        exit_price = signal['stop_loss']
                        exit_reason = 'SL'
                        exit_date = current_bar.name
                        break
                
                # Salida por tiempo (máximo 20 barras)
                if j >= entry_idx + 20:
                    exit_price = current_bar['Close']
                    exit_reason = 'TIME'
                    exit_date = current_bar.name
                    break
            
            if exit_price:
                # Calcular profit
                if signal['type'] == 'LONG':
                    profit_pct = ((exit_price - signal['entry_price']) / signal['entry_price']) * 100
                else:
                    profit_pct = ((signal['entry_price'] - exit_price) / signal['entry_price']) * 100
                
                profit_usd = self.capital * self.position_size * (profit_pct / 100)
                
                trade = {
                    'ticker': signal['ticker'],
                    'type': signal['type'],
                    'entry_date': signal['date'],
                    'exit_date': exit_date,
                    'entry_price': signal['entry_price'],
                    'exit_price': exit_price,
                    'profit_pct': profit_pct,
                    'profit_usd': profit_usd,
                    'exit_reason': exit_reason,
                    'confidence': signal['confidence']
                }
                
                self.trades.append(trade)
                self.capital += profit_usd
    
    def run(self, tickers):
        """Ejecuta el backtesting optimizado"""
        
        print("""
╔════════════════════════════════════════════════════════════════╗
║          BACKTESTING OPTIMIZADO - MAYOR WIN RATE                ║
╚════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"📊 Configuración:")
        print(f"• Capital Inicial: ${self.capital_inicial:,}")
        print(f"• Tickers: {tickers}")
        print(f"• Tamaño Posición: {self.position_size*100}%")
        print(f"• Risk/Reward: 1:2 mínimo")
        print("="*60)
        
        # Descargar datos
        print("\n📥 Descargando datos...")
        
        for ticker in tickers:
            try:
                print(f"\n📈 Analizando {ticker}...")
                
                # Descargar datos
                data = yf.Ticker(ticker)
                df = data.history(period="2mo", interval="1h")  # 2 meses para más datos
                
                if len(df) < 200:
                    print(f"   ⚠️ Datos insuficientes para {ticker}")
                    continue
                
                # Generar señales con estrategias optimizadas
                momentum_signals = self.momentum_strategy_optimized(df, ticker)
                reversion_signals = self.mean_reversion_optimized(df, ticker)
                
                # Combinar y filtrar señales (evitar duplicados)
                all_signals = momentum_signals + reversion_signals
                
                # Ordenar por fecha
                all_signals.sort(key=lambda x: x['date'])
                
                # Filtrar señales muy cercanas (mínimo 10 barras de separación)
                filtered_signals = []
                last_signal_date = None
                
                for signal in all_signals:
                    if last_signal_date is None or (signal['date'] - last_signal_date).total_seconds() / 3600 > 10:
                        filtered_signals.append(signal)
                        last_signal_date = signal['date']
                
                print(f"   📊 Señales generadas: {len(filtered_signals)}")
                
                # Simular trades
                self.simulate_trades(filtered_signals, df)
                
            except Exception as e:
                print(f"   ❌ Error con {ticker}: {e}")
        
        # Mostrar resultados
        self.show_results()
    
    def show_results(self):
        """Muestra los resultados del backtesting"""
        
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL BACKTESTING OPTIMIZADO")
        print("="*60)
        
        if not self.trades:
            print("❌ No se generaron trades")
            return
            
        # Calcular métricas
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['profit_pct'] > 0]
        losing_trades = [t for t in self.trades if t['profit_pct'] <= 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100
        total_return = ((self.capital / self.capital_inicial) - 1) * 100
        
        avg_win = np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Profit Factor
        gross_profit = sum(t['profit_usd'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['profit_usd'] for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss
        
        # Risk/Reward Ratio
        risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        print(f"\n💰 CAPITAL:")
        print(f"• Inicial: ${self.capital_inicial:,.2f}")
        print(f"• Final: ${self.capital:,.2f}")
        print(f"• Retorno: {total_return:+.2f}%")
        
        print(f"\n📈 MÉTRICAS PRINCIPALES:")
        print(f"• Total Trades: {total_trades}")
        print(f"• Trades Ganadores: {len(winning_trades)}")
        print(f"• Trades Perdedores: {len(losing_trades)}")
        print(f"• Win Rate: {win_rate:.1f}%")
        print(f"• Profit Factor: {profit_factor:.2f}")
        print(f"• Risk/Reward: 1:{risk_reward:.1f}")
        
        print(f"\n🎯 ANÁLISIS DE TRADES:")
        print(f"• Promedio Ganancia: {avg_win:+.2f}%")
        print(f"• Promedio Pérdida: {avg_loss:+.2f}%")
        
        # Análisis por razón de salida
        exit_reasons = {}
        for trade in self.trades:
            reason = trade['exit_reason']
            if reason not in exit_reasons:
                exit_reasons[reason] = {'count': 0, 'profit': 0}
            exit_reasons[reason]['count'] += 1
            exit_reasons[reason]['profit'] += trade['profit_usd']
        
        print(f"\n📊 ANÁLISIS POR SALIDA:")
        for reason, stats in exit_reasons.items():
            pct = (stats['count'] / total_trades) * 100
            print(f"• {reason}: {stats['count']} trades ({pct:.1f}%) | PnL: ${stats['profit']:+.2f}")
        
        # Análisis por confianza
        high_confidence = [t for t in self.trades if t['confidence'] >= 7]
        if high_confidence:
            hc_wins = [t for t in high_confidence if t['profit_pct'] > 0]
            hc_wr = (len(hc_wins) / len(high_confidence)) * 100
            print(f"\n🌟 TRADES ALTA CONFIANZA (Score ≥ 7):")
            print(f"• Total: {len(high_confidence)}")
            print(f"• Win Rate: {hc_wr:.1f}%")
        
        # Mejor y peor trade
        if self.trades:
            best_trade = max(self.trades, key=lambda t: t['profit_pct'])
            worst_trade = min(self.trades, key=lambda t: t['profit_pct'])
            print(f"\n💡 EXTREMOS:")
            print(f"• Mejor Trade: {best_trade['ticker']} {best_trade['profit_pct']:+.2f}% ({best_trade['exit_reason']})")
            print(f"• Peor Trade: {worst_trade['ticker']} {worst_trade['profit_pct']:+.2f}% ({worst_trade['exit_reason']})")
        
        # Evaluación de calidad
        print(f"\n✨ EVALUACIÓN DE CALIDAD:")
        
        if win_rate >= 65:
            print("🌟 EXCELENTE: Win Rate superior al 65%")
        elif win_rate >= 55:
            print("✅ BUENO: Win Rate entre 55-65%")
        else:
            print("⚠️ MEJORABLE: Win Rate menor al 55%")
        
        if profit_factor >= 2:
            print("🌟 EXCELENTE: Profit Factor superior a 2")
        elif profit_factor >= 1.5:
            print("✅ BUENO: Profit Factor entre 1.5-2")
        else:
            print("⚠️ MEJORABLE: Profit Factor menor a 1.5")
        
        if risk_reward >= 2:
            print("🌟 EXCELENTE: Risk/Reward superior a 1:2")
        elif risk_reward >= 1.5:
            print("✅ BUENO: Risk/Reward entre 1:1.5-2")
        else:
            print("⚠️ MEJORABLE: Risk/Reward menor a 1:1.5")
        
        # Proyección
        print(f"\n💡 PROYECCIÓN (si se mantiene el performance):")
        monthly_return = total_return * (30 / 60)  # Ajustar a 30 días
        print(f"• Retorno Mensual Estimado: {monthly_return:+.1f}%")
        print(f"• Retorno Anualizado: {(((1 + monthly_return/100) ** 12) - 1) * 100:+.1f}%")
        
        print("\n" + "="*60)
        print("✅ BACKTESTING OPTIMIZADO COMPLETADO")
        print("="*60)
        
        # Guardar resultados
        if self.trades:
            df_trades = pd.DataFrame(self.trades)
            df_trades.to_csv('backtest_optimizado_results.csv', index=False)
            print("\n💾 Resultados guardados en backtest_optimizado_results.csv")

if __name__ == "__main__":
    # Ejecutar backtesting optimizado
    backtest = OptimizedBacktest(capital_inicial=10000)
    
    # Tickers a analizar
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
    
    # Ejecutar
    backtest.run(tickers)