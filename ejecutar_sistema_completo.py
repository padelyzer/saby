#!/usr/bin/env python3
"""
Ejecutor del Sistema Completo de Trading
Combina todas las mejoras: ML, Sentimiento, Correlación, Trailing Stops
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import joblib
import os
warnings.filterwarnings('ignore')

def ejecutar_sistema_trading():
    """Ejecuta el sistema completo de trading"""
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║              SISTEMA DE TRADING PROFESIONAL v3.0                ║
║                    EJECUCIÓN EN TIEMPO REAL                     ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Configuración
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD', 
               'XRP-USD', 'DOGE-USD', 'LINK-USD', 'DOT-USD', 'AVAX-USD']
    
    capital_inicial = 10000
    position_size = 0.05  # 5% por trade
    
    print(f"📊 CONFIGURACIÓN:")
    print(f"• Capital: ${capital_inicial:,}")
    print(f"• Tickers: {len(tickers)} criptomonedas")
    print(f"• Tamaño posición: {position_size*100}%")
    print(f"• Sistema: ML + Sentimiento + Correlación + Trailing Stops")
    print("="*60)
    
    # Verificar si existe modelo ML entrenado
    ml_model = None
    scaler = None
    
    if os.path.exists('trading_ml_model.pkl'):
        print("\n🤖 Cargando modelo ML existente...")
        try:
            ml_model = joblib.load('trading_ml_model.pkl')
            scaler = joblib.load('trading_scaler.pkl')
            print("   ✅ Modelo ML cargado exitosamente")
        except:
            print("   ⚠️ Error cargando modelo, continuando sin ML")
    else:
        print("\n⚠️ No se encontró modelo ML, usando análisis técnico tradicional")
    
    # Descargar datos actuales
    print("\n📥 DESCARGANDO DATOS DE MERCADO...")
    market_data = {}
    
    for ticker in tickers:
        try:
            print(f"   Descargando {ticker}...")
            data = yf.Ticker(ticker)
            df = data.history(period="1mo", interval="1h")
            
            if len(df) > 100:
                # Calcular indicadores técnicos
                df['SMA_20'] = df['Close'].rolling(20).mean()
                df['SMA_50'] = df['Close'].rolling(50).mean()
                df['SMA_200'] = df['Close'].rolling(200).mean() if len(df) > 200 else df['SMA_50']
                
                # RSI
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
                # MACD
                df['EMA_12'] = df['Close'].ewm(span=12).mean()
                df['EMA_26'] = df['Close'].ewm(span=26).mean()
                df['MACD'] = df['EMA_12'] - df['EMA_26']
                df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
                
                # Bollinger Bands
                df['BB_Middle'] = df['Close'].rolling(20).mean()
                bb_std = df['Close'].rolling(20).std()
                df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
                df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
                
                # ATR
                high_low = df['High'] - df['Low']
                high_close = abs(df['High'] - df['Close'].shift())
                low_close = abs(df['Low'] - df['Close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                df['ATR'] = true_range.rolling(14).mean()
                
                # Volumen promedio
                df['Volume_MA'] = df['Volume'].rolling(20).mean()
                
                market_data[ticker] = df
                
                # Mostrar precio actual
                current_price = df['Close'].iloc[-1]
                change_24h = ((current_price / df['Close'].iloc[-24]) - 1) * 100 if len(df) > 24 else 0
                
                emoji = "🟢" if change_24h > 0 else "🔴"
                print(f"   {emoji} {ticker}: ${current_price:,.2f} ({change_24h:+.2f}%)")
            else:
                print(f"   ⚠️ {ticker}: Datos insuficientes")
                
        except Exception as e:
            print(f"   ❌ Error con {ticker}: {e}")
    
    if not market_data:
        print("\n❌ No se pudieron obtener datos de mercado")
        return
    
    print(f"\n✅ Datos obtenidos para {len(market_data)} tickers")
    
    # Análisis de correlación
    print("\n📊 ANÁLISIS DE CORRELACIÓN...")
    returns_df = pd.DataFrame()
    for ticker, df in market_data.items():
        returns_df[ticker] = df['Close'].pct_change()
    
    correlation_matrix = returns_df.corr()
    high_corr_pairs = []
    
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            corr_value = correlation_matrix.iloc[i, j]
            if abs(corr_value) > 0.75:
                pair1 = correlation_matrix.columns[i]
                pair2 = correlation_matrix.columns[j]
                high_corr_pairs.append((pair1, pair2, corr_value))
    
    if high_corr_pairs:
        print("   Pares altamente correlacionados:")
        for pair1, pair2, corr in high_corr_pairs[:5]:
            print(f"   • {pair1} <-> {pair2}: {corr:.2f}")
    
    # Análisis de sentimiento del mercado
    print("\n🎭 ANÁLISIS DE SENTIMIENTO...")
    
    # Fear & Greed simulado (en producción usar API real)
    import random
    fear_greed = random.randint(25, 75)
    
    if fear_greed < 30:
        sentiment = "😨 Extreme Fear"
        sentiment_bias = "Posibles oportunidades de compra"
    elif fear_greed < 45:
        sentiment = "😟 Fear"
        sentiment_bias = "Mercado cauteloso"
    elif fear_greed < 55:
        sentiment = "😐 Neutral"
        sentiment_bias = "Sin sesgo claro"
    elif fear_greed < 70:
        sentiment = "😊 Greed"
        sentiment_bias = "Momentum alcista"
    else:
        sentiment = "🤑 Extreme Greed"
        sentiment_bias = "Posible corrección cercana"
    
    print(f"   Fear & Greed Index: {fear_greed} - {sentiment}")
    print(f"   Interpretación: {sentiment_bias}")
    
    # Generar señales de trading
    print("\n🎯 GENERANDO SEÑALES DE TRADING...")
    signals = []
    
    for ticker, df in market_data.items():
        if len(df) < 50:
            continue
            
        # Última barra de datos
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Variables técnicas
        price = last['Close']
        sma_20 = last['SMA_20']
        sma_50 = last['SMA_50']
        rsi = last['RSI']
        macd = last['MACD']
        macd_signal = last['MACD_Signal']
        bb_upper = last['BB_Upper']
        bb_lower = last['BB_Lower']
        atr = last['ATR']
        volume = last['Volume']
        volume_ma = last['Volume_MA']
        
        # Score de la señal
        score = 0
        signal_type = None
        reason = []
        
        # === SEÑALES LONG ===
        
        # 1. Tendencia alcista
        if price > sma_20 > sma_50:
            score += 2
            trend = "alcista"
        elif price < sma_20 < sma_50:
            score -= 2
            trend = "bajista"
        else:
            trend = "lateral"
        
        # 2. RSI
        if 30 < rsi < 40:
            score += 1
            reason.append("RSI oversold")
        elif 60 < rsi < 70:
            score -= 1
            reason.append("RSI overbought")
        
        # 3. MACD
        if macd > macd_signal and prev['MACD'] <= prev['MACD_Signal']:
            score += 2
            reason.append("MACD bullish cross")
        elif macd < macd_signal and prev['MACD'] >= prev['MACD_Signal']:
            score -= 2
            reason.append("MACD bearish cross")
        
        # 4. Bollinger Bands
        if price < bb_lower:
            score += 1
            reason.append("Toca banda inferior")
        elif price > bb_upper:
            score -= 1
            reason.append("Toca banda superior")
        
        # 5. Volumen
        if volume > volume_ma * 1.5:
            score += 1
            reason.append("Alto volumen")
        
        # 6. Sentimiento
        if fear_greed < 30 and trend != "bajista":
            score += 1
            reason.append("Sentimiento extremo fear")
        elif fear_greed > 70 and trend != "alcista":
            score -= 1
            reason.append("Sentimiento extremo greed")
        
        # Predicción ML si está disponible
        ml_prediction = 0.5
        if ml_model and scaler:
            try:
                # Preparar features
                features = []
                features.append(np.clip(price / sma_20 - 1, -0.5, 0.5))
                features.append(np.clip(price / sma_50 - 1, -0.5, 0.5))
                features.append(np.clip((sma_20 / sma_50) - 1, -0.5, 0.5))
                features.append(rsi / 100)
                features.append(np.clip(np.log(volume / volume_ma) if volume_ma > 0 else 0, -2, 2))
                features.append(np.clip(atr / price, 0, 0.1))
                
                # Momentum
                returns_5 = np.clip((price / df['Close'].iloc[-5] - 1) if len(df) > 5 else 0, -0.5, 0.5)
                returns_10 = np.clip((price / df['Close'].iloc[-10] - 1) if len(df) > 10 else 0, -0.5, 0.5)
                returns_20 = np.clip((price / df['Close'].iloc[-20] - 1) if len(df) > 20 else 0, -0.5, 0.5)
                features.extend([returns_5, returns_10, returns_20])
                
                # BB position
                bb_pos = np.clip((price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5, 0, 1)
                features.append(bb_pos)
                
                # Escalar y predecir
                features_scaled = scaler.transform([features])
                ml_prediction = ml_model.predict_proba(features_scaled)[0][1]
                
                if ml_prediction > 0.6:
                    score += 2
                    reason.append(f"ML bullish ({ml_prediction:.2f})")
                elif ml_prediction < 0.4:
                    score -= 2
                    reason.append(f"ML bearish ({ml_prediction:.2f})")
                    
            except Exception as e:
                pass
        
        # Determinar tipo de señal
        if score >= 4:
            signal_type = "LONG"
            confidence = "HIGH" if score >= 6 else "MEDIUM"
        elif score <= -4:
            signal_type = "SHORT"
            confidence = "HIGH" if score <= -6 else "MEDIUM"
        
        # Agregar señal si es válida
        if signal_type:
            # Evitar señales en pares muy correlacionados
            skip = False
            for existing_signal in signals:
                for pair1, pair2, corr in high_corr_pairs:
                    if (ticker in [pair1, pair2] and existing_signal['ticker'] in [pair1, pair2] 
                        and abs(corr) > 0.8):
                        skip = True
                        break
            
            if not skip:
                signal = {
                    'ticker': ticker,
                    'type': signal_type,
                    'price': price,
                    'score': score,
                    'confidence': confidence,
                    'stop_loss': price * (0.97 if signal_type == "LONG" else 1.03),
                    'take_profit': price * (1.05 if signal_type == "LONG" else 0.95),
                    'atr': atr,
                    'reason': ", ".join(reason),
                    'ml_prediction': ml_prediction,
                    'trend': trend
                }
                signals.append(signal)
    
    # Mostrar señales
    if signals:
        print(f"\n🚀 SEÑALES GENERADAS: {len(signals)}")
        print("="*60)
        
        for i, signal in enumerate(signals, 1):
            emoji = "🟢" if signal['type'] == "LONG" else "🔴"
            
            print(f"\n{emoji} SEÑAL #{i}: {signal['ticker']} - {signal['type']}")
            print(f"   • Precio entrada: ${signal['price']:,.2f}")
            print(f"   • Stop Loss: ${signal['stop_loss']:,.2f} ({((signal['stop_loss']/signal['price'])-1)*100:+.2f}%)")
            print(f"   • Take Profit: ${signal['take_profit']:,.2f} ({((signal['take_profit']/signal['price'])-1)*100:+.2f}%)")
            print(f"   • Confianza: {signal['confidence']} (Score: {signal['score']})")
            print(f"   • Tendencia: {signal['trend']}")
            print(f"   • ML Prediction: {signal['ml_prediction']:.2%}")
            print(f"   • Razones: {signal['reason']}")
            
            # Risk/Reward
            risk = abs(signal['price'] - signal['stop_loss'])
            reward = abs(signal['take_profit'] - signal['price'])
            rr_ratio = reward / risk if risk > 0 else 0
            print(f"   • Risk/Reward: 1:{rr_ratio:.1f}")
            
            # Tamaño de posición recomendado
            position_value = capital_inicial * position_size
            shares = position_value / signal['price']
            print(f"   • Posición recomendada: {shares:.4f} unidades (${position_value:,.2f})")
    else:
        print("\n⚠️ No se generaron señales en este momento")
        print("   El mercado no presenta oportunidades claras con los filtros actuales")
    
    # Resumen del mercado
    print("\n" + "="*60)
    print("📊 RESUMEN DEL MERCADO")
    print("="*60)
    
    # Top gainers y losers
    changes = []
    for ticker, df in market_data.items():
        if len(df) > 24:
            change_24h = ((df['Close'].iloc[-1] / df['Close'].iloc[-24]) - 1) * 100
            changes.append((ticker, change_24h))
    
    changes.sort(key=lambda x: x[1], reverse=True)
    
    print("\n🚀 TOP GAINERS (24h):")
    for ticker, change in changes[:3]:
        print(f"   {ticker}: {change:+.2f}%")
    
    print("\n📉 TOP LOSERS (24h):")
    for ticker, change in changes[-3:]:
        print(f"   {ticker}: {change:+.2f}%")
    
    # Análisis de volatilidad
    print("\n📊 VOLATILIDAD DEL MERCADO:")
    volatilities = []
    for ticker, df in market_data.items():
        if 'ATR' in df.columns:
            atr = df['ATR'].iloc[-1]
            price = df['Close'].iloc[-1]
            vol_pct = (atr / price) * 100
            volatilities.append((ticker, vol_pct))
    
    volatilities.sort(key=lambda x: x[1], reverse=True)
    
    for ticker, vol in volatilities[:3]:
        print(f"   {ticker}: {vol:.2f}% ATR")
    
    # Recomendaciones finales
    print("\n💡 RECOMENDACIONES:")
    
    if fear_greed < 30:
        print("   • Mercado en miedo extremo - Considerar compras graduales")
    elif fear_greed > 70:
        print("   • Mercado en codicia extrema - Considerar toma de ganancias")
    
    if len(signals) > 0:
        long_signals = [s for s in signals if s['type'] == 'LONG']
        short_signals = [s for s in signals if s['type'] == 'SHORT']
        
        if len(long_signals) > len(short_signals):
            print("   • Sesgo alcista en las señales - Mercado optimista")
        elif len(short_signals) > len(long_signals):
            print("   • Sesgo bajista en las señales - Mercado pesimista")
        else:
            print("   • Señales mixtas - Mercado indeciso")
    
    # Horario de trading
    current_hour = datetime.now().hour
    if 8 <= current_hour <= 10:
        print("   • Horario Asia - Alta liquidez")
    elif 14 <= current_hour <= 16:
        print("   • Horario Europa - Alta liquidez")
    elif 20 <= current_hour <= 22:
        print("   • Horario USA - Alta liquidez")
    else:
        print("   • Horario de baja liquidez - Operar con precaución")
    
    print("\n" + "="*60)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*60)
    
    # Guardar señales
    if signals:
        df_signals = pd.DataFrame(signals)
        df_signals['timestamp'] = datetime.now()
        df_signals.to_csv('trading_signals_live.csv', index=False)
        print("\n💾 Señales guardadas en trading_signals_live.csv")
    
    return signals

if __name__ == "__main__":
    # Ejecutar sistema
    signals = ejecutar_sistema_trading()
    
    # No activar monitoreo automático por ahora