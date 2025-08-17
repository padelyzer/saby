#!/usr/bin/env python3
"""
Sistema Híbrido Balanceado Final
Combinación óptima de rentabilidad y gestión de riesgo
Target: 60-65% WR con frecuencia suficiente de señales
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SistemaHibridoBalanceado:
    """
    Sistema híbrido que balancea rentabilidad y gestión de riesgo
    """
    
    def __init__(self, capital=10000):
        self.capital = capital
        self.capital_inicial = capital
        
        # BALANCE ÓPTIMO: Filtros moderados pero efectivos
        self.min_volume_ratio = 1.8        # Reducido de 2.5 a 1.8
        self.min_risk_reward = 1.6         # Reducido de 2.0 a 1.6
        self.min_score = 6                 # Reducido de 8 a 6
        self.max_risk_per_trade = 0.015    # 1.5% máximo por trade
        
        # GESTIÓN DE RIESGO AVANZADA
        self.max_portfolio_risk = 0.06     # 6% del capital en riesgo total
        self.max_correlation = 0.7         # Evitar correlaciones altas
        self.trailing_activation = 0.012   # 1.2% (más agresivo)
        self.trailing_distance = 0.004     # 0.4% trailing distance
        
        # POSITION SIZING DINÁMICO
        self.base_position_size = 0.05     # 5% base
        self.max_position_size = 0.08      # 8% máximo
        self.volatility_adjustment = True
        
        self.active_trades = []
        self.completed_trades = []
        
    def calculate_indicators_balanced(self, df):
        """Indicadores balanceados - esenciales pero completos"""
        
        # EMAs para tendencia
        df['EMA_8'] = df['Close'].ewm(span=8).mean()
        df['EMA_21'] = df['Close'].ewm(span=21).mean()
        df['EMA_55'] = df['Close'].ewm(span=55).mean()
        
        # RSI con smoothing ligero
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_raw = 100 - (100 / (1 + rs))
        df['RSI'] = rsi_raw.rolling(2).mean()  # Smoothing ligero
        
        # MACD
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
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        df['BB_Std'] = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
        
        # Volumen
        df['Volume_SMA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        return df
    
    def quick_trend_confirmation(self, df, current_idx):
        """Confirmación de tendencia rápida y efectiva"""
        
        if current_idx < 55:
            return 0, 'insufficient_data'
        
        current = df.iloc[current_idx]
        recent = df.iloc[current_idx-20:current_idx+1]
        
        trend_score = 0
        
        # 1. EMAs alignment (peso alto)
        if current['EMA_8'] > current['EMA_21'] > current['EMA_55']:
            trend_score += 3
        elif current['EMA_8'] < current['EMA_21'] < current['EMA_55']:
            trend_score -= 3
        
        # 2. Price position vs EMAs
        if current['Close'] > current['EMA_21']:
            trend_score += 2
        elif current['Close'] < current['EMA_21']:
            trend_score -= 2
        
        # 3. MACD momentum
        if current['MACD'] > current['MACD_Signal'] and current['MACD_Histogram'] > 0:
            trend_score += 1
        elif current['MACD'] < current['MACD_Signal'] and current['MACD_Histogram'] < 0:
            trend_score -= 1
        
        # 4. Price momentum (últimos 5 períodos)
        price_momentum = (current['Close'] / recent['Close'].iloc[-6] - 1) * 100
        if abs(price_momentum) > 1:  # Momentum significativo
            trend_score += 1 if price_momentum > 0 else -1
        
        # Clasificar tendencia
        if trend_score >= 4:
            return trend_score, 'strong_bullish'
        elif trend_score >= 2:
            return trend_score, 'bullish'
        elif trend_score <= -4:
            return trend_score, 'strong_bearish'
        elif trend_score <= -2:
            return trend_score, 'bearish'
        else:
            return trend_score, 'neutral'
    
    def find_support_resistance_simple(self, df, current_price, lookback=50):
        """S/R simplificado pero efectivo"""
        
        if len(df) < lookback:
            return None
        
        recent_df = df.tail(lookback)
        
        # Encontrar pivots simples
        pivot_highs = []
        pivot_lows = []
        
        for i in range(3, len(recent_df)-3):
            high = recent_df['High'].iloc[i]
            low = recent_df['Low'].iloc[i]
            
            # Pivot high: mayor que 3 velas a cada lado
            if (high >= recent_df['High'].iloc[i-3:i].max() and
                high >= recent_df['High'].iloc[i+1:i+4].max()):
                pivot_highs.append(high)
            
            # Pivot low: menor que 3 velas a cada lado
            if (low <= recent_df['Low'].iloc[i-3:i].min() and
                low <= recent_df['Low'].iloc[i+1:i+4].min()):
                pivot_lows.append(low)
        
        # Encontrar nivel más relevante
        relevant_resistance = None
        relevant_support = None
        
        # Resistencia más cercana arriba
        resistances_above = [h for h in pivot_highs if h > current_price * 1.005]
        if resistances_above:
            relevant_resistance = min(resistances_above)
        
        # Soporte más cercano abajo
        supports_below = [l for l in pivot_lows if l < current_price * 0.995]
        if supports_below:
            relevant_support = max(supports_below)
        
        return {
            'resistance': relevant_resistance,
            'support': relevant_support,
            'resistance_distance': abs(relevant_resistance - current_price) / current_price if relevant_resistance else None,
            'support_distance': abs(current_price - relevant_support) / current_price if relevant_support else None
        }
    
    def calculate_position_size_dynamic(self, signal, current_volatility):
        """Position sizing dinámico balanceado"""
        
        # Base size según score de la señal
        if signal['score'] >= 8:
            base_size = 0.07  # 7% para señales muy fuertes
        elif signal['score'] >= 7:
            base_size = 0.06  # 6% para señales fuertes
        elif signal['score'] >= 6:
            base_size = 0.05  # 5% para señales buenas
        else:
            base_size = 0.04  # 4% para señales básicas
        
        # Ajuste por volatilidad
        if self.volatility_adjustment:
            # Reducir tamaño si alta volatilidad
            vol_adj = max(0.6, min(1.4, 1 / (current_volatility * 25)))
            base_size *= vol_adj
        
        # Ajuste por R:R ratio
        rr_adj = min(1.2, signal['risk_reward'] / 2.0)  # Bonus por buen R:R
        base_size *= rr_adj
        
        # Ajuste por drawdown de la cuenta
        current_drawdown = (self.capital / self.capital_inicial - 1) * 100
        if current_drawdown < -5:
            base_size *= 0.7  # Reducir 30% si drawdown > 5%
        elif current_drawdown < -10:
            base_size *= 0.5  # Reducir 50% si drawdown > 10%
        
        # Limites finales
        return max(0.03, min(self.max_position_size, base_size))
    
    def generate_balanced_signal(self, df, ticker):
        """Generación de señales balanceadas"""
        
        if len(df) < 60:
            return None
        
        current_idx = len(df) - 1
        current = df.iloc[current_idx]
        
        # FILTRO 1: Volatilidad controlada (más permisivo)
        if current['Volatility'] > 0.05:  # 5% máximo
            return None
        
        # FILTRO 2: Volumen significativo (moderado)
        if current['Volume_Ratio'] < self.min_volume_ratio:
            return None
        
        # FILTRO 3: Confirmación de tendencia
        trend_score, trend_direction = self.quick_trend_confirmation(df, current_idx)
        
        if abs(trend_score) < 2:  # Necesita tendencia clara pero no extrema
            return None
        
        # FILTRO 4: S/R levels
        sr_levels = self.find_support_resistance_simple(df, current['Close'])
        
        # === ESTRATEGIAS BALANCEADAS ===
        
        score = 0
        signal_type = None
        reasons = []
        
        # ESTRATEGIA 1: Volume Breakout (la más exitosa)
        lookback = df.iloc[current_idx-24:current_idx+1]  # 24 períodos
        recent_high = lookback['High'].max()
        recent_low = lookback['Low'].min()
        range_size = recent_high - recent_low
        
        if range_size > current['Close'] * 0.015:  # Rango mínimo 1.5%
            
            # BREAKOUT ALCISTA
            if (trend_direction in ['bullish', 'strong_bullish'] and
                current['Close'] > recent_high * 0.997 and
                current['Volume_Ratio'] > 2.0 and
                45 < current['RSI'] < 75):
                
                signal_type = 'LONG'
                score += 6
                reasons.append("Volume Breakout Alcista")
                
                if current['MACD_Histogram'] > 0:
                    score += 1
                    reasons.append("MACD positivo")
                
                if current['Volume_Ratio'] > 3:
                    score += 1
                    reasons.append("Volumen excepcional")
                
                # Stops inteligentes
                stop_loss = max(recent_high * 0.99, current['Close'] - current['ATR'] * 1.5)
                take_profit = current['Close'] + (range_size * 1.2)
            
            # BREAKDOWN BAJISTA
            elif (trend_direction in ['bearish', 'strong_bearish'] and
                  current['Close'] < recent_low * 1.003 and
                  current['Volume_Ratio'] > 2.0 and
                  25 < current['RSI'] < 55):
                
                signal_type = 'SHORT'
                score += 6
                reasons.append("Volume Breakdown Bajista")
                
                if current['MACD_Histogram'] < 0:
                    score += 1
                    reasons.append("MACD negativo")
                
                if current['Volume_Ratio'] > 3:
                    score += 1
                    reasons.append("Volumen excepcional")
                
                stop_loss = min(recent_low * 1.01, current['Close'] + current['ATR'] * 1.5)
                take_profit = current['Close'] - (range_size * 1.2)
        
        # ESTRATEGIA 2: Bollinger Reversal (moderada)
        if not signal_type:
            
            # REVERSAL ALCISTA
            if (current['Close'] <= current['BB_Lower'] * 1.01 and
                current['RSI'] < 40 and
                current['Volume_Ratio'] > 1.5 and
                trend_score > 0):  # Tendencia general alcista
                
                signal_type = 'LONG'
                score += 5
                reasons.append("BB Reversal Alcista")
                
                if current['Close'] > current['EMA_55']:
                    score += 1
                    reasons.append("Sobre EMA55")
                
                stop_loss = current['Close'] - current['ATR'] * 1.2
                take_profit = current['BB_Middle']
            
            # REVERSAL BAJISTA
            elif (current['Close'] >= current['BB_Upper'] * 0.99 and
                  current['RSI'] > 60 and
                  current['Volume_Ratio'] > 1.5 and
                  trend_score < 0):  # Tendencia general bajista
                
                signal_type = 'SHORT'
                score += 5
                reasons.append("BB Reversal Bajista")
                
                if current['Close'] < current['EMA_55']:
                    score += 1
                    reasons.append("Bajo EMA55")
                
                stop_loss = current['Close'] + current['ATR'] * 1.2
                take_profit = current['BB_Middle']
        
        # ESTRATEGIA 3: EMA Trend Following (conservadora)
        if not signal_type:
            
            # TREND FOLLOWING ALCISTA
            if (trend_direction == 'strong_bullish' and
                abs(current['Close'] - current['EMA_21']) / current['Close'] < 0.02 and
                current['Close'] > current['EMA_21'] and
                40 < current['RSI'] < 65):
                
                signal_type = 'LONG'
                score += 5
                reasons.append("EMA Trend Following")
                
                if current['Volume_Ratio'] > 1.3:
                    score += 1
                    reasons.append("Volumen confirmando")
                
                stop_loss = current['EMA_21'] * 0.995
                take_profit = current['Close'] + current['ATR'] * 2.5
            
            # TREND FOLLOWING BAJISTA
            elif (trend_direction == 'strong_bearish' and
                  abs(current['Close'] - current['EMA_21']) / current['Close'] < 0.02 and
                  current['Close'] < current['EMA_21'] and
                  35 < current['RSI'] < 60):
                
                signal_type = 'SHORT'
                score += 5
                reasons.append("EMA Trend Following")
                
                if current['Volume_Ratio'] > 1.3:
                    score += 1
                    reasons.append("Volumen confirmando")
                
                stop_loss = current['EMA_21'] * 1.005
                take_profit = current['Close'] - current['ATR'] * 2.5
        
        # VERIFICACIÓN FINAL BALANCEADA
        if signal_type and score >= self.min_score:
            
            # Ajustar stops por S/R si están muy cerca
            if sr_levels:
                if signal_type == 'LONG' and sr_levels['support']:
                    distance_to_support = abs(current['Close'] - sr_levels['support']) / current['Close']
                    if distance_to_support < 0.015:  # Muy cerca del soporte
                        stop_loss = max(stop_loss, sr_levels['support'] * 0.998)
                        score += 1
                        reasons.append("Stop en soporte")
                
                elif signal_type == 'SHORT' and sr_levels['resistance']:
                    distance_to_resistance = abs(sr_levels['resistance'] - current['Close']) / current['Close']
                    if distance_to_resistance < 0.015:  # Muy cerca de resistencia
                        stop_loss = min(stop_loss, sr_levels['resistance'] * 1.002)
                        score += 1
                        reasons.append("Stop en resistencia")
            
            # Verificar R:R final
            risk = abs(current['Close'] - stop_loss)
            reward = abs(take_profit - current['Close'])
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio >= self.min_risk_reward:
                
                # Verificar que el riesgo por trade sea aceptable
                risk_pct = risk / current['Close']
                if risk_pct <= self.max_risk_per_trade:
                    
                    return {
                        'ticker': ticker,
                        'type': signal_type,
                        'entry_price': current['Close'],
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'score': score,
                        'risk_reward': rr_ratio,
                        'risk_pct': risk_pct * 100,
                        'timestamp': df.index[current_idx],
                        'trend_score': trend_score,
                        'trend_direction': trend_direction,
                        'volume_ratio': current['Volume_Ratio'],
                        'rsi': current['RSI'],
                        'volatility': current['Volatility'] * 100,
                        'reasons': ', '.join(reasons),
                        'sr_levels': sr_levels
                    }
        
        return None
    
    def analyze_market_balanced(self, tickers):
        """Análisis de mercado balanceado"""
        
        print("""
╔════════════════════════════════════════════════════════════════════════╗
║                SISTEMA HÍBRIDO BALANCEADO FINAL                        ║
║           Rentabilidad Óptima + Gestión de Riesgo Inteligente          ║
╚════════════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"💰 Capital: ${self.capital:,}")
        print(f"🎯 Target: Rentabilidad sostenible con riesgo controlado")
        print(f"📊 Min Score: {self.min_score} (balanceado)")
        print(f"⚡ Min Volume: {self.min_volume_ratio}x (moderado)")
        print(f"🛡️ Max Risk/Trade: {self.max_risk_per_trade*100:.1f}%")
        print(f"🏦 Max Portfolio Risk: {self.max_portfolio_risk*100:.1f}%")
        print("="*70)
        
        signals = []
        
        for ticker in tickers:
            try:
                print(f"\n🔍 Analizando {ticker}...")
                
                # Descargar datos
                data = yf.Ticker(ticker)
                df = data.history(period="2mo", interval="1h")
                
                if len(df) < 100:
                    print(f"   ⚠️ Datos insuficientes")
                    continue
                
                # Calcular indicadores
                df = self.calculate_indicators_balanced(df)
                
                # Buscar señal balanceada
                signal = self.generate_balanced_signal(df, ticker)
                
                if signal:
                    signals.append(signal)
                    emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
                    print(f"   {emoji} SEÑAL BALANCEADA")
                    print(f"   ├─ Score: {signal['score']:.1f}/10")
                    print(f"   ├─ R:R: 1:{signal['risk_reward']:.1f}")
                    print(f"   ├─ Riesgo: {signal['risk_pct']:.1f}%")
                    print(f"   ├─ Trend: {signal['trend_direction']}")
                    print(f"   └─ Razones: {signal['reasons']}")
                else:
                    print(f"   💤 Sin señal - Esperando setup balanceado")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Filtrar por riesgo de portfolio y correlación
        if signals:
            signals = self.filter_portfolio_risk(signals)
            self.show_balanced_analysis(signals)
        else:
            print(f"\n⚠️ No se generaron señales")
            print("💡 Mercado sin setups balanceados en este momento")
            print("🔄 Los filtros moderados buscan calidad sin ser extremos")
        
        return signals
    
    def filter_portfolio_risk(self, signals):
        """Filtrar señales por riesgo de portfolio"""
        
        if not signals:
            return signals
        
        # Ordenar por score
        signals.sort(key=lambda x: x['score'], reverse=True)
        
        # Filtrar por riesgo acumulado
        filtered_signals = []
        total_risk = 0
        
        for signal in signals:
            signal_risk = signal['risk_pct'] / 100
            
            if total_risk + signal_risk <= self.max_portfolio_risk:
                filtered_signals.append(signal)
                total_risk += signal_risk
                
                # Máximo 4 posiciones
                if len(filtered_signals) >= 4:
                    break
        
        return filtered_signals
    
    def show_balanced_analysis(self, signals):
        """Mostrar análisis balanceado"""
        
        print(f"\n🎯 SEÑALES BALANCEADAS: {len(signals)}")
        print("="*70)
        
        if not signals:
            return
        
        total_risk = 0
        total_potential_reward = 0
        
        for i, signal in enumerate(signals, 1):
            emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
            
            # Calcular position size
            position_size = self.calculate_position_size_dynamic(signal, signal['volatility']/100)
            signal['position_size'] = position_size
            
            # Calcular potencial P&L
            risk_usd = self.capital * position_size * (signal['risk_pct'] / 100)
            reward_usd = risk_usd * signal['risk_reward']
            
            total_risk += risk_usd
            total_potential_reward += reward_usd
            
            print(f"\n{emoji} SEÑAL #{i}: {signal['ticker']} - {signal['type']}")
            print(f"├─ ⭐ Score Balanceado: {signal['score']:.1f}/10")
            print(f"├─ 💰 Precio: ${signal['entry_price']:.4f}")
            print(f"├─ 🛑 Stop: ${signal['stop_loss']:.4f}")
            print(f"├─ 🎯 Target: ${signal['take_profit']:.4f}")
            print(f"├─ ⚖️ R:R: 1:{signal['risk_reward']:.1f}")
            print(f"├─ 📊 Position: {position_size*100:.1f}%")
            print(f"├─ 🛡️ Riesgo: {signal['risk_pct']:.1f}%")
            print(f"├─ 📈 RSI: {signal['rsi']:.0f}")
            print(f"├─ 🔊 Vol: {signal['volume_ratio']:.1f}x")
            print(f"├─ 📊 Trend: {signal['trend_direction']} ({signal['trend_score']})")
            print(f"├─ 💥 Potencial: -${risk_usd:.0f} / +${reward_usd:.0f}")
            print(f"└─ 📋 {signal['reasons']}")
        
        # Resumen del portfolio balanceado
        print("\n" + "="*70)
        print("💎 PORTFOLIO BALANCEADO")
        print("="*70)
        
        avg_score = np.mean([s['score'] for s in signals])
        avg_rr = np.mean([s['risk_reward'] for s in signals])
        total_exposure = sum([s['position_size'] for s in signals])
        portfolio_risk_pct = (total_risk / self.capital) * 100
        
        print(f"• ⭐ Score promedio: {avg_score:.1f}/10")
        print(f"• ⚖️ R:R promedio: 1:{avg_rr:.1f}")
        print(f"• 💼 Exposición total: {total_exposure*100:.1f}%")
        print(f"• 🛡️ Riesgo portfolio: {portfolio_risk_pct:.1f}%")
        print(f"• 💰 Capital en riesgo: ${total_risk:.0f}")
        print(f"• 🎯 Potencial total: ${total_potential_reward:.0f}")
        
        # Proyección balanceada
        print(f"\n💡 PROYECCIÓN BALANCEADA:")
        
        # Win rates realistas para sistema balanceado
        for wr in [0.60, 0.65, 0.70]:
            expected_return = (wr * avg_rr - (1-wr) * 1) * total_exposure
            monthly_return = expected_return * 12 * 100  # 12 ciclos/mes balanceado
            
            print(f"• 🎯 Win Rate {wr*100:.0f}%: Retorno mensual {monthly_return:+.1f}%")
        
        # Análisis de riesgo
        print(f"\n🛡️ ANÁLISIS DE RIESGO:")
        print(f"• Máximo drawdown teórico: {portfolio_risk_pct:.1f}%")
        print(f"• Riesgo por señal: {portfolio_risk_pct/len(signals):.1f}% promedio")
        print(f"• Diversificación: {len(signals)} posiciones")
        
        if portfolio_risk_pct > 5:
            print(f"⚠️ Riesgo alto - Considerar reducir position sizes")
        elif portfolio_risk_pct < 3:
            print(f"✅ Riesgo conservador - Margen para más oportunidades")
        else:
            print(f"✅ Riesgo balanceado - Óptimo para crecimiento sostenible")
        
        # Guardar señales
        df_signals = pd.DataFrame(signals)
        df_signals.to_csv('sistema_hibrido_balanceado_signals.csv', index=False)
        print(f"\n💾 Señales guardadas en sistema_hibrido_balanceado_signals.csv")
        
        print(f"\n🎯 TRADING PLAN BALANCEADO:")
        print("1. ✅ Ejecutar solo estas señales balanceadas")
        print("2. 🛑 Respetar stops sin excepciones")
        print("3. 📈 Activar trailing stops a +1.2R")
        print("4. 💰 Cerrar 40% en primer target")
        print("5. ⏰ Re-evaluar cada 4 horas")
        print("6. 🔄 Mantener máximo 4 posiciones")
        print("7. 📊 Seguir position sizing dinámico")

def main():
    """Función principal del sistema balanceado"""
    
    sistema = SistemaHibridoBalanceado(capital=10000)
    
    # Tickers principales
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD', 
               'ADA-USD', 'AVAX-USD', 'LINK-USD', 'DOGE-USD']
    
    # Ejecutar análisis balanceado
    signals = sistema.analyze_market_balanced(tickers)
    
    if signals:
        print(f"\n🎯 {len(signals)} señales balanceadas activas")
        print("⚖️ ¡Rentabilidad optimizada con riesgo controlado!")
    else:
        print(f"\n💎 Sin señales balanceadas disponibles")
        print("🧘‍♂️ La paciencia es parte de la estrategia balanceada")
    
    print("\n" + "="*70)
    print("✅ ANÁLISIS BALANCEADO COMPLETADO")
    print("="*70)

if __name__ == "__main__":
    main()