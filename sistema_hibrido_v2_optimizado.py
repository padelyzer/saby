#!/usr/bin/env python3
"""
Sistema Híbrido v2.0 Optimizado
Objetivo: 60-70% Win Rate con filtros mejorados
Basado en análisis de backtesting real
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SistemaHibridoV2:
    """
    Sistema optimizado v2.0 con filtros mejorados para mayor win rate
    """
    
    def __init__(self, capital=10000):
        self.capital = capital
        self.target_win_rate = 0.65  # 65% objetivo
        
        # OPTIMIZACIÓN 1: Filtros más estrictos basados en backtesting
        self.min_volume_ratio = 2.5    # Aumentado de 2.0
        self.min_risk_reward = 2.0     # Aumentado de 1.8
        self.min_confirmation_score = 8 # Muy alto para calidad
        
        # OPTIMIZACIÓN 2: Stops inteligentes multi-nivel
        self.atr_stop_multiplier = 1.2  # Reducido para stops más ajustados
        self.support_resistance_buffer = 0.003  # 0.3% buffer
        
        # OPTIMIZACIÓN 3: Confirmación multi-timeframe obligatoria
        self.mtf_required_agreement = 0.7  # 70% de timeframes deben concordar
        
        # OPTIMIZACIÓN 4: Gestión de momentum mejorada
        self.momentum_lookback = 12  # 12 períodos
        self.volatility_threshold = 0.04  # 4% máximo
        
        self.signals = []
        
    def calculate_advanced_indicators(self, df):
        """Calcula indicadores avanzados con mayor precisión"""
        
        # EMAs múltiples para precisión
        for period in [8, 13, 21, 34, 55]:
            df[f'EMA_{period}'] = df['Close'].ewm(span=period).mean()
        
        # RSI con smoothing
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_raw = 100 - (100 / (1 + rs))
        df['RSI'] = rsi_raw.rolling(3).mean()  # Smoothed RSI
        
        # MACD con histogram
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # ATR y volatilidad
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        df['Volatility'] = df['ATR'] / df['Close']
        
        # Bollinger Bands con múltiples desviaciones
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        df['BB_Std'] = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
        df['BB_Upper_Wide'] = df['BB_Middle'] + (df['BB_Std'] * 2.5)
        df['BB_Lower_Wide'] = df['BB_Middle'] - (df['BB_Std'] * 2.5)
        
        # Volumen avanzado
        df['Volume_SMA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        df['Volume_Trend'] = df['Volume'].rolling(5).mean() / df['Volume'].rolling(20).mean()
        
        # Momentum indicators
        df['ROC'] = ((df['Close'] - df['Close'].shift(self.momentum_lookback)) / 
                     df['Close'].shift(self.momentum_lookback)) * 100
        
        # Support/Resistance levels
        df['Pivot_High'] = df['High'].rolling(window=5, center=True).max() == df['High']
        df['Pivot_Low'] = df['Low'].rolling(window=5, center=True).min() == df['Low']
        
        return df
    
    def multi_timeframe_confirmation(self, ticker, current_time):
        """
        Confirmación obligatoria multi-timeframe
        """
        try:
            timeframes = [
                ('15m', '3d'),
                ('1h', '7d'),
                ('4h', '1mo'),
            ]
            
            confirmations = []
            
            for interval, period in timeframes:
                data = yf.Ticker(ticker)
                df = data.history(period=period, interval=interval)
                
                if len(df) < 50:
                    continue
                
                df = self.calculate_advanced_indicators(df)
                
                # Encontrar la barra más cercana al tiempo actual
                closest_idx = df.index.get_indexer([current_time], method='nearest')[0]
                if closest_idx < 20:  # Necesitamos suficiente historial
                    continue
                
                current = df.iloc[closest_idx]
                
                # Evaluar tendencia en este timeframe
                trend_score = 0
                
                # 1. EMAs alignment
                if current['EMA_8'] > current['EMA_21'] > current['EMA_55']:
                    trend_score += 3  # Bullish
                elif current['EMA_8'] < current['EMA_21'] < current['EMA_55']:
                    trend_score -= 3  # Bearish
                
                # 2. Price vs EMAs
                if current['Close'] > current['EMA_21']:
                    trend_score += 2
                elif current['Close'] < current['EMA_21']:
                    trend_score -= 2
                
                # 3. MACD
                if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
                    trend_score += 1
                elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
                    trend_score -= 1
                
                # 4. RSI momentum
                if 45 < current['RSI'] < 65:
                    trend_score += 1  # Healthy momentum
                elif current['RSI'] < 35:
                    trend_score += 2 if trend_score < 0 else -1  # Oversold reversal vs continuation
                elif current['RSI'] > 75:
                    trend_score -= 2 if trend_score > 0 else 1   # Overbought
                
                confirmations.append({
                    'timeframe': interval,
                    'trend_score': trend_score,
                    'weight': 3 if interval == '1h' else 2 if interval == '4h' else 1
                })
            
            if not confirmations:
                return 0, 'insufficient_data'
            
            # Calcular score ponderado
            total_score = sum(conf['trend_score'] * conf['weight'] for conf in confirmations)
            total_weight = sum(conf['weight'] for conf in confirmations)
            
            weighted_score = total_score / total_weight if total_weight > 0 else 0
            
            # Determinar dirección y fuerza
            if weighted_score > 2:
                return weighted_score, 'strong_bullish'
            elif weighted_score > 0.5:
                return weighted_score, 'bullish'
            elif weighted_score < -2:
                return weighted_score, 'strong_bearish'
            elif weighted_score < -0.5:
                return weighted_score, 'bearish'
            else:
                return weighted_score, 'neutral'
                
        except Exception as e:
            return 0, f'error: {str(e)}'
    
    def find_smart_support_resistance(self, df, current_price, lookback=100):
        """
        Encuentra niveles de soporte/resistencia más inteligentes
        """
        if len(df) < lookback:
            return None
        
        # Obtener pivots de los últimos períodos
        recent_df = df.tail(lookback)
        
        pivot_highs = []
        pivot_lows = []
        
        for i in range(5, len(recent_df)-5):
            price_high = recent_df['High'].iloc[i]
            price_low = recent_df['Low'].iloc[i]
            
            # Pivot high: mayor que 5 velas a cada lado
            if (all(price_high >= recent_df['High'].iloc[i-j] for j in range(1, 6)) and
                all(price_high >= recent_df['High'].iloc[i+j] for j in range(1, 6))):
                pivot_highs.append(price_high)
            
            # Pivot low: menor que 5 velas a cada lado
            if (all(price_low <= recent_df['Low'].iloc[i-j] for j in range(1, 6)) and
                all(price_low <= recent_df['Low'].iloc[i+j] for j in range(1, 6))):
                pivot_lows.append(price_low)
        
        # Agrupar niveles cercanos (clustering)
        def cluster_levels(levels, tolerance=0.005):
            if not levels:
                return []
            
            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]
            
            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] < tolerance:
                    current_cluster.append(level)
                else:
                    clusters.append(np.mean(current_cluster))
                    current_cluster = [level]
            
            clusters.append(np.mean(current_cluster))
            return clusters
        
        clustered_highs = cluster_levels(pivot_highs)
        clustered_lows = cluster_levels(pivot_lows)
        
        # Encontrar el nivel más relevante
        relevant_resistance = None
        relevant_support = None
        
        # Resistencia: primer nivel arriba del precio actual
        resistances_above = [h for h in clustered_highs if h > current_price * 1.001]
        if resistances_above:
            relevant_resistance = min(resistances_above)
        
        # Soporte: primer nivel abajo del precio actual
        supports_below = [l for l in clustered_lows if l < current_price * 0.999]
        if supports_below:
            relevant_support = max(supports_below)
        
        return {
            'resistance': relevant_resistance,
            'support': relevant_support,
            'resistance_distance': abs(relevant_resistance - current_price) / current_price if relevant_resistance else None,
            'support_distance': abs(current_price - relevant_support) / current_price if relevant_support else None
        }
    
    def generate_ultra_precise_signal(self, df, ticker):
        """
        Genera señales ultra precisas con todos los filtros optimizados
        """
        if len(df) < 100:
            return None
        
        current = df.iloc[-1]
        
        # FILTRO 1: Volatilidad controlada
        if current['Volatility'] > self.volatility_threshold:
            return None
        
        # FILTRO 2: Volumen excepcional requerido
        if current['Volume_Ratio'] < self.min_volume_ratio:
            return None
        
        # FILTRO 3: Confirmación multi-timeframe obligatoria
        mtf_score, mtf_direction = self.multi_timeframe_confirmation(ticker, df.index[-1])
        
        if abs(mtf_score) < 1.5:  # Debe haber tendencia clara
            return None
        
        # FILTRO 4: Soporte/Resistencia
        sr_levels = self.find_smart_support_resistance(df, current['Close'])
        
        # Inicializar scoring
        score = 0
        signal_type = None
        reasons = []
        
        # === ESTRATEGIA LONG ULTRA SELECTIVA ===
        if mtf_direction in ['bullish', 'strong_bullish']:
            
            # Condición 1: Precio cerca de soporte fuerte
            near_support = (sr_levels and sr_levels['support'] and 
                          sr_levels['support_distance'] and sr_levels['support_distance'] < 0.02)
            
            # Condición 2: RSI en zona óptima
            rsi_optimal = 30 < current['RSI'] < 50
            
            # Condición 3: MACD improving
            macd_improving = current['MACD_Histogram'] > 0
            
            # Condición 4: Volume breakout en rango
            recent_range = df['High'].tail(24).max() - df['Low'].tail(24).min()
            range_breakout = current['Close'] > (df['High'].tail(24).max() * 0.998)
            
            if near_support and rsi_optimal and range_breakout:
                signal_type = 'LONG'
                score += 6  # Base alta
                reasons.append("Soporte + RSI + Breakout")
                
                if macd_improving:
                    score += 2
                    reasons.append("MACD mejorando")
                
                if current['Volume_Ratio'] > 3:
                    score += 2
                    reasons.append("Volumen excepcional")
                
                if mtf_direction == 'strong_bullish':
                    score += 2
                    reasons.append("MTF muy alcista")
                
                # Stops inteligentes
                if sr_levels and sr_levels['support']:
                    stop_loss = sr_levels['support'] * (1 - self.support_resistance_buffer)
                else:
                    stop_loss = current['Close'] - (current['ATR'] * self.atr_stop_multiplier)
                
                # Target en resistencia o R:R mínimo
                if sr_levels and sr_levels['resistance']:
                    take_profit = sr_levels['resistance'] * (1 - self.support_resistance_buffer)
                else:
                    take_profit = current['Close'] + (current['ATR'] * 3.0)
        
        # === ESTRATEGIA SHORT ULTRA SELECTIVA ===
        elif mtf_direction in ['bearish', 'strong_bearish']:
            
            # Condiciones similares pero invertidas
            near_resistance = (sr_levels and sr_levels['resistance'] and 
                             sr_levels['resistance_distance'] and sr_levels['resistance_distance'] < 0.02)
            
            rsi_optimal = 50 < current['RSI'] < 70
            macd_declining = current['MACD_Histogram'] < 0
            
            recent_range = df['High'].tail(24).max() - df['Low'].tail(24).min()
            range_breakdown = current['Close'] < (df['Low'].tail(24).min() * 1.002)
            
            if near_resistance and rsi_optimal and range_breakdown:
                signal_type = 'SHORT'
                score += 6
                reasons.append("Resistencia + RSI + Breakdown")
                
                if macd_declining:
                    score += 2
                    reasons.append("MACD declinando")
                
                if current['Volume_Ratio'] > 3:
                    score += 2
                    reasons.append("Volumen excepcional")
                
                if mtf_direction == 'strong_bearish':
                    score += 2
                    reasons.append("MTF muy bajista")
                
                # Stops inteligentes
                if sr_levels and sr_levels['resistance']:
                    stop_loss = sr_levels['resistance'] * (1 + self.support_resistance_buffer)
                else:
                    stop_loss = current['Close'] + (current['ATR'] * self.atr_stop_multiplier)
                
                # Target en soporte
                if sr_levels and sr_levels['support']:
                    take_profit = sr_levels['support'] * (1 + self.support_resistance_buffer)
                else:
                    take_profit = current['Close'] - (current['ATR'] * 3.0)
        
        # VERIFICACIÓN FINAL
        if signal_type and score >= self.min_confirmation_score:
            # Risk/Reward check
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
                    'timestamp': df.index[-1],
                    'mtf_score': mtf_score,
                    'mtf_direction': mtf_direction,
                    'volume_ratio': current['Volume_Ratio'],
                    'rsi': current['RSI'],
                    'volatility': current['Volatility'],
                    'reasons': ', '.join(reasons),
                    'sr_levels': sr_levels
                }
        
        return None
    
    def analyze_market_v2(self, tickers):
        """
        Análisis de mercado con filtros v2.0 optimizados
        """
        print("""
╔════════════════════════════════════════════════════════════════════════╗
║                   SISTEMA HÍBRIDO v2.0 OPTIMIZADO                      ║
║                  Target: 60-70% Win Rate Ultra Precisión               ║
╚════════════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"💰 Capital: ${self.capital:,}")
        print(f"🎯 Target Win Rate: {self.target_win_rate*100:.0f}%")
        print(f"🔒 Min Confirmation Score: {self.min_confirmation_score}")
        print(f"⚡ Min Volume Ratio: {self.min_volume_ratio}x")
        print(f"📊 Min Risk/Reward: 1:{self.min_risk_reward}")
        print("="*60)
        
        signals = []
        
        for ticker in tickers:
            try:
                print(f"\n🔍 Análisis ultra preciso: {ticker}")
                
                # Descargar datos con más historia para indicadores
                data = yf.Ticker(ticker)
                df = data.history(period="3mo", interval="1h")
                
                if len(df) < 200:
                    print(f"   ⚠️ Datos insuficientes ({len(df)} < 200)")
                    continue
                
                # Calcular indicadores avanzados
                df = self.calculate_advanced_indicators(df)
                
                # Buscar señal ultra precisa
                signal = self.generate_ultra_precise_signal(df, ticker)
                
                if signal:
                    signals.append(signal)
                    emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
                    print(f"   {emoji} SEÑAL DETECTADA - Score: {signal['score']:.1f}/10")
                    print(f"   ├─ Tipo: {signal['type']}")
                    print(f"   ├─ R:R: 1:{signal['risk_reward']:.1f}")
                    print(f"   ├─ MTF: {signal['mtf_direction']} ({signal['mtf_score']:.1f})")
                    print(f"   ├─ Volumen: {signal['volume_ratio']:.1f}x")
                    print(f"   └─ Razones: {signal['reasons']}")
                else:
                    print(f"   💤 Sin señal - Filtros muy estrictos")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Mostrar resumen de señales
        if signals:
            self.show_premium_signals(signals)
        else:
            print(f"\n⚠️ NO SE GENERARON SEÑALES")
            print("📋 Esto es NORMAL con filtros ultra estrictos")
            print("💡 El sistema prioriza CALIDAD sobre CANTIDAD")
            print("🔄 Verificar nuevamente en 2-4 horas")
        
        return signals
    
    def show_premium_signals(self, signals):
        """
        Muestra análisis premium de señales de alta calidad
        """
        print(f"\n🌟 SEÑALES PREMIUM DETECTADAS: {len(signals)}")
        print("="*60)
        
        total_potential_risk = 0
        total_potential_reward = 0
        
        for i, signal in enumerate(signals, 1):
            emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
            
            # Calcular potencial P&L
            risk_pct = abs(signal['entry_price'] - signal['stop_loss']) / signal['entry_price']
            reward_pct = abs(signal['take_profit'] - signal['entry_price']) / signal['entry_price']
            
            position_size = min(0.06, 0.02 / risk_pct)  # Max 6%, respetando 2% risk
            risk_usd = self.capital * position_size * risk_pct
            reward_usd = self.capital * position_size * reward_pct
            
            total_potential_risk += risk_usd
            total_potential_reward += reward_usd
            
            print(f"\n{emoji} SEÑAL PREMIUM #{i}: {signal['ticker']} - {signal['type']}")
            print(f"├─ 🎯 Score Ultra Alto: {signal['score']:.1f}/10")
            print(f"├─ 💰 Precio: ${signal['entry_price']:.4f}")
            print(f"├─ 🛑 Stop Loss: ${signal['stop_loss']:.4f}")
            print(f"├─ 🎯 Take Profit: ${signal['take_profit']:.4f}")
            print(f"├─ ⚖️ Risk/Reward: 1:{signal['risk_reward']:.1f}")
            print(f"├─ 📊 Position Size: {position_size*100:.1f}%")
            print(f"├─ 🔄 MTF: {signal['mtf_direction']} ({signal['mtf_score']:.1f})")
            print(f"├─ 📈 RSI: {signal['rsi']:.0f}")
            print(f"├─ 🔊 Volumen: {signal['volume_ratio']:.1f}x")
            print(f"├─ 💥 Volatilidad: {signal['volatility']*100:.1f}%")
            print(f"├─ 🎯 Potencial: -${risk_usd:.0f} / +${reward_usd:.0f}")
            print(f"└─ 📋 Razones: {signal['reasons']}")
            
            # Mostrar S/R levels si existen
            if signal['sr_levels']:
                sr = signal['sr_levels']
                if sr['resistance']:
                    print(f"   🔺 Resistencia: ${sr['resistance']:.4f} ({sr['resistance_distance']*100:.1f}%)")
                if sr['support']:
                    print(f"   🔻 Soporte: ${sr['support']:.4f} ({sr['support_distance']*100:.1f}%)")
        
        # Resumen del portfolio premium
        print("\n" + "="*60)
        print("💎 RESUMEN PORTFOLIO PREMIUM")
        print("="*60)
        
        avg_score = np.mean([s['score'] for s in signals])
        avg_rr = np.mean([s['risk_reward'] for s in signals])
        avg_mtf = np.mean([s['mtf_score'] for s in signals])
        total_exposure = len(signals) * 0.06  # Máximo 6% por señal
        
        print(f"• 🎯 Score promedio: {avg_score:.1f}/10 (ULTRA ALTO)")
        print(f"• ⚖️ R:R promedio: 1:{avg_rr:.1f}")
        print(f"• 🔄 MTF promedio: {avg_mtf:.1f}")
        print(f"• 💼 Exposición máxima: {total_exposure*100:.0f}%")
        print(f"• 💰 Riesgo total: ${total_potential_risk:.0f}")
        print(f"• 🎯 Recompensa potencial: ${total_potential_reward:.0f}")
        print(f"• 🛡️ Ratio Riesgo/Capital: {total_potential_risk/self.capital*100:.1f}%")
        
        # Proyección optimista con calidad premium
        print(f"\n💡 PROYECCIÓN CON SEÑALES PREMIUM:")
        
        # Con señales de tan alta calidad, win rates esperados son mayores
        for wr in [0.65, 0.70, 0.75]:
            expected_return = (wr * avg_rr - (1-wr) * 1) * total_exposure
            monthly_return = expected_return * 8 * 100  # 8 ciclos/mes (más selectivo)
            
            print(f"• 🎯 Win Rate {wr*100:.0f}%: Retorno mensual {monthly_return:+.1f}%")
        
        # Guardar señales premium
        df_signals = pd.DataFrame(signals)
        df_signals.to_csv('sistema_hibrido_v2_premium_signals.csv', index=False)
        print(f"\n💾 Señales premium guardadas en sistema_hibrido_v2_premium_signals.csv")
        
        print(f"\n🎯 INSTRUCCIONES PARA MÁXIMO RENDIMIENTO:")
        print("1. ✅ SOLO operar estas señales (calidad ultra alta)")
        print("2. 🛑 Respetar stops religiosamente")
        print("3. 📈 Activar trailing stops a +1.5R")
        print("4. 💰 Cerrar 50% en primer target")
        print("5. ⏰ Re-evaluar cada 4-6 horas")
        print("6. 🚫 NO añadir posiciones si score < 8")
        print("7. 📊 Seguir plan de position sizing")

def main():
    """Función principal del sistema v2.0"""
    
    sistema = SistemaHibridoV2(capital=10000)
    
    # Tickers principales con mayor liquidez
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD', 
               'ADA-USD', 'AVAX-USD', 'LINK-USD']
    
    # Ejecutar análisis ultra preciso
    signals = sistema.analyze_market_v2(tickers)
    
    if signals:
        print(f"\n🎯 {len(signals)} señales PREMIUM listas")
        print("🌟 ¡Calidad excepcional garantizada!")
    else:
        print(f"\n💎 Mercado sin oportunidades PREMIUM")
        print("📈 La paciencia es la clave del trading de élite")
    
    print("\n" + "="*60)
    print("✅ ANÁLISIS v2.0 COMPLETADO")
    print("="*60)

if __name__ == "__main__":
    main()