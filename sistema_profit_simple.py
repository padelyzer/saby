#!/usr/bin/env python3
"""
Sistema de Trading Simplificado para Máximos Profits
Enfoque en señales claras y rentables
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def sistema_profit_maximizado():
    """
    Sistema simplificado pero optimizado para profits
    """
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                  SISTEMA PROFIT MAXIMIZED v1.0                           ║
║             Enfoque: Señales Simples pero Rentables                      ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Configuración optimizada
    capital = 10000
    position_size = 0.08  # 8% por trade
    min_risk_reward = 2.0  # Mínimo 1:2
    
    print(f"\n💰 Capital: ${capital:,}")
    print(f"📊 Position Size: {position_size*100}%")
    print(f"🎯 Min R:R: 1:{min_risk_reward}")
    print("="*60)
    
    # Cryptos más líquidas y volátiles
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD', 
               'ADA-USD', 'AVAX-USD', 'LINK-USD', 'DOGE-USD']
    
    signals = []
    
    print("\n🔍 ANÁLISIS DE OPORTUNIDADES:")
    print("="*60)
    
    for ticker in tickers:
        try:
            print(f"\n📈 {ticker}:")
            
            # Descargar datos
            data = yf.Ticker(ticker)
            df = data.history(period="7d", interval="1h")
            
            if len(df) < 50:
                print("   ⚠️ Datos insuficientes")
                continue
            
            # Variables
            current_price = df['Close'].iloc[-1]
            volume = df['Volume'].iloc[-1]
            volume_avg = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Indicadores técnicos
            sma_20 = df['Close'].rolling(20).mean().iloc[-1]
            sma_50 = df['Close'].rolling(50).mean().iloc[-1] if len(df) > 50 else sma_20
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # ATR para stops
            high_low = df['High'] - df['Low']
            atr = high_low.rolling(14).mean().iloc[-1]
            atr_pct = (atr / current_price) * 100
            
            # MACD
            ema_12 = df['Close'].ewm(span=12).mean().iloc[-1]
            ema_26 = df['Close'].ewm(span=26).mean().iloc[-1]
            macd = ema_12 - ema_26
            
            # Bollinger Bands
            bb_middle = df['Close'].rolling(20).mean().iloc[-1]
            bb_std = df['Close'].rolling(20).std().iloc[-1]
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            # === ESTRATEGIAS OPTIMIZADAS ===
            
            signal_type = None
            score = 0
            reasons = []
            
            # ESTRATEGIA 1: Reversión en Bollinger Bands
            if current_price <= bb_lower and rsi < 35:
                signal_type = 'LONG'
                score += 4
                reasons.append("Oversold BB + RSI")
                stop_loss = current_price - (atr * 1.5)
                take_profit = bb_middle  # Target: vuelta a la media
                
            elif current_price >= bb_upper and rsi > 65:
                signal_type = 'SHORT'
                score += 4
                reasons.append("Overbought BB + RSI")
                stop_loss = current_price + (atr * 1.5)
                take_profit = bb_middle
            
            # ESTRATEGIA 2: Momentum con volumen
            elif current_price > sma_20 > sma_50 and volume > volume_avg * 1.5:
                if rsi > 50 and macd > 0:
                    signal_type = 'LONG'
                    score += 3
                    reasons.append("Momentum alcista + volumen")
                    stop_loss = sma_20 * 0.98
                    take_profit = current_price + (atr * 3)
                    
            elif current_price < sma_20 < sma_50 and volume > volume_avg * 1.5:
                if rsi < 50 and macd < 0:
                    signal_type = 'SHORT'
                    score += 3
                    reasons.append("Momentum bajista + volumen")
                    stop_loss = sma_20 * 1.02
                    take_profit = current_price - (atr * 3)
            
            # ESTRATEGIA 3: Ruptura de rangos
            elif atr_pct > 2:  # Suficiente volatilidad
                recent_high = df['High'].tail(24).max()  # Últimas 24 horas
                recent_low = df['Low'].tail(24).min()
                
                if current_price > recent_high * 0.999 and volume > volume_avg * 2:
                    signal_type = 'LONG'
                    score += 3
                    reasons.append("Breakout alcista")
                    stop_loss = recent_low
                    take_profit = current_price + (recent_high - recent_low) * 1.5
                    
                elif current_price < recent_low * 1.001 and volume > volume_avg * 2:
                    signal_type = 'SHORT'
                    score += 3
                    reasons.append("Breakdown bajista")
                    stop_loss = recent_high
                    take_profit = current_price - (recent_high - recent_low) * 1.5
            
            # === FILTROS DE CALIDAD ===
            
            # Volumen mínimo
            vol_ratio = volume / volume_avg if volume_avg > 0 else 1
            if vol_ratio > 1.2:
                score += 1
                reasons.append(f"Volumen {vol_ratio:.1f}x")
            
            # Evitar mercados demasiado volátiles o planos
            if 1 < atr_pct < 8:  # Entre 1% y 8% de volatilidad
                score += 1
                reasons.append(f"Volatilidad óptima ({atr_pct:.1f}%)")
            
            # === GENERAR SEÑAL ===
            
            if signal_type and score >= 3:
                # Calcular Risk/Reward
                risk = abs(current_price - stop_loss)
                reward = abs(take_profit - current_price)
                rr_ratio = reward / risk if risk > 0 else 0
                
                if rr_ratio >= min_risk_reward:
                    # Calcular potencial profit
                    risk_pct = (risk / current_price) * 100
                    reward_pct = (reward / current_price) * 100
                    
                    position_value = capital * position_size
                    potential_loss = position_value * (risk_pct / 100)
                    potential_gain = position_value * (reward_pct / 100)
                    
                    signal = {
                        'ticker': ticker,
                        'type': signal_type,
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'score': score,
                        'risk_reward': rr_ratio,
                        'risk_pct': risk_pct,
                        'reward_pct': reward_pct,
                        'position_size': position_size,
                        'potential_loss': potential_loss,
                        'potential_gain': potential_gain,
                        'volatility': atr_pct,
                        'volume_ratio': vol_ratio,
                        'rsi': rsi,
                        'reasons': ', '.join(reasons)
                    }
                    
                    signals.append(signal)
                    
                    # Mostrar señal
                    emoji = "🟢" if signal_type == 'LONG' else "🔴"
                    print(f"   {emoji} {signal_type} SIGNAL")
                    print(f"   ├─ Score: {score}/10")
                    print(f"   ├─ R:R: 1:{rr_ratio:.1f}")
                    print(f"   ├─ Risk: {risk_pct:.1f}% | Reward: {reward_pct:.1f}%")
                    print(f"   ├─ Entry: ${current_price:.4f}")
                    print(f"   ├─ SL: ${stop_loss:.4f}")
                    print(f"   ├─ TP: ${take_profit:.4f}")
                    print(f"   └─ Razón: {', '.join(reasons)}")
                else:
                    print(f"   ⚠️ R:R insuficiente: 1:{rr_ratio:.1f}")
            else:
                trend_status = "alcista" if current_price > sma_20 else "bajista" if current_price < sma_20 else "lateral"
                print(f"   💤 Sin señal - Tendencia {trend_status}, RSI {rsi:.0f}, Score {score}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # === RESUMEN FINAL ===
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE OPORTUNIDADES")
    print("="*60)
    
    if signals:
        print(f"\n🚀 SEÑALES GENERADAS: {len(signals)}")
        
        # Ordenar por score
        signals.sort(key=lambda x: x['score'], reverse=True)
        
        total_risk = sum(s['potential_loss'] for s in signals)
        total_reward = sum(s['potential_gain'] for s in signals)
        avg_rr = np.mean([s['risk_reward'] for s in signals])
        
        print(f"\n💰 POTENCIAL DE PORTFOLIO:")
        print(f"• Riesgo total: ${total_risk:.2f}")
        print(f"• Recompensa total: ${total_reward:.2f}")
        print(f"• R:R promedio: 1:{avg_rr:.1f}")
        print(f"• Exposición: {len(signals) * position_size * 100:.0f}%")
        
        # Análisis de probabilidades
        print(f"\n📈 PROYECCIÓN (estimada):")
        win_rates = [0.45, 0.55, 0.65]  # Diferentes escenarios
        
        for wr in win_rates:
            expected_value = (wr * avg_rr) - ((1-wr) * 1)
            monthly_return = expected_value * len(signals) * position_size * 4 * 100  # 4 ciclos/mes
            
            print(f"• Win Rate {wr*100:.0f}%: Retorno mensual {monthly_return:+.1f}%")
        
        # Recomendaciones por señal
        print(f"\n🎯 SEÑALES RECOMENDADAS:")
        
        for i, signal in enumerate(signals[:5], 1):  # Top 5
            emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
            
            print(f"\n{i}. {emoji} {signal['ticker']} {signal['type']}")
            print(f"   Score: {signal['score']}/10 | R:R: 1:{signal['risk_reward']:.1f}")
            print(f"   Entrada: ${signal['price']:.4f}")
            print(f"   Potencial: -${signal['potential_loss']:.0f} / +${signal['potential_gain']:.0f}")
            print(f"   Razón: {signal['reasons']}")
        
        # Guardar señales
        df_signals = pd.DataFrame(signals)
        df_signals.to_csv('profit_signals.csv', index=False)
        print(f"\n💾 Señales guardadas en profit_signals.csv")
        
    else:
        print("\n⚠️ No se encontraron oportunidades de alta calidad")
        print("Recomendaciones:")
        print("• Esperar mejores setups")
        print("• Verificar en 2-4 horas")
        print("• Considerar timeframes mayores")
    
    # Horario y recomendaciones
    current_hour = datetime.now().hour
    
    print(f"\n⏰ TIMING:")
    if 8 <= current_hour <= 10:
        print("• Horario Asia - Liquidez moderada")
    elif 14 <= current_hour <= 16:
        print("• Horario Europa - Alta liquidez ✅")
    elif 20 <= current_hour <= 22:
        print("• Horario USA - Máxima liquidez ✅")
    else:
        print("• Baja liquidez - Usar stops más amplios")
    
    print(f"\n💡 TIPS PARA MÁXIMOS PROFITS:")
    print("1. Tomar solo señales con Score ≥ 5")
    print("2. Usar position size dinámico según volatilidad")
    print("3. Cerrar 50% en primer target, trailing el resto")
    print("4. Evitar más de 3 posiciones correlacionadas")
    print("5. Revisar señales cada 2 horas")
    print("6. Salir si el setup se invalida")
    
    print("\n" + "="*60)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*60)
    
    return signals

if __name__ == "__main__":
    signals = sistema_profit_maximizado()
    
    if signals:
        print(f"\n🎯 {len(signals)} señales listas para operar")
        print("¡Buena suerte y que los profits estén contigo! 📈💰")
    else:
        print("\n💤 Mercado sin oportunidades claras ahora")
        print("La paciencia es la clave del trading exitoso 🧘‍♂️")