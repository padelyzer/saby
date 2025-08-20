#!/usr/bin/env python3
"""
Validación de señales DOGE en tiempo real
"""

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Obtener datos de DOGE
ticker = yf.Ticker('DOGE-USD')

# Datos de las últimas 24 horas con intervalo de 5 minutos
df_5m = ticker.history(period='1d', interval='5m')
current_price = df_5m['Close'].iloc[-1]

# Datos horarios para análisis más amplio
df_1h = ticker.history(period='2d', interval='1h')
df_4h = ticker.history(period='5d', interval='1h')

# Resample a 4H
df_4h = df_4h.resample('4H').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

# Calcular indicadores técnicos
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df_1h['RSI'] = calculate_rsi(df_1h['Close'])
df_4h['RSI'] = calculate_rsi(df_4h['Close'])

# EMAs
df_1h['EMA_9'] = df_1h['Close'].ewm(span=9).mean()
df_1h['EMA_21'] = df_1h['Close'].ewm(span=21).mean()
df_4h['EMA_20'] = df_4h['Close'].ewm(span=20).mean()
df_4h['EMA_50'] = df_4h['Close'].ewm(span=50).mean()

# Bollinger Bands
df_1h['BB_Middle'] = df_1h['Close'].rolling(20).mean()
bb_std = df_1h['Close'].rolling(20).std()
df_1h['BB_Upper'] = df_1h['BB_Middle'] + (bb_std * 2)
df_1h['BB_Lower'] = df_1h['BB_Middle'] - (bb_std * 2)

# MACD
df_1h['EMA_12'] = df_1h['Close'].ewm(span=12).mean()
df_1h['EMA_26'] = df_1h['Close'].ewm(span=26).mean()
df_1h['MACD'] = df_1h['EMA_12'] - df_1h['EMA_26']
df_1h['MACD_Signal'] = df_1h['MACD'].ewm(span=9).mean()

print('=' * 70)
print(' VALIDACIÓN DE SEÑALES DOGE/USDT - SISTEMA FILOSÓFICO '.center(70))
print('=' * 70)

print(f'\n📊 DATOS DE MERCADO ACTUALES')
print('-' * 40)
print(f'Precio actual: ${current_price:.6f}')
print(f'Precio hace 1 hora: ${df_1h["Close"].iloc[-2]:.6f}')
print(f'Cambio 1H: {((current_price / df_1h["Close"].iloc[-2]) - 1) * 100:.2f}%')
print(f'Cambio 24H: {((current_price / df_1h["Close"].iloc[-24]) - 1) * 100:.2f}%')

# Análisis del nivel $0.22
target_price = 0.22
distance_pct = ((target_price - current_price) / current_price) * 100

print(f'\n📍 VALIDACIÓN DEL NIVEL $0.22000')
print('-' * 40)
print(f'Distancia desde precio actual: {distance_pct:.2f}%')

if abs(distance_pct) < 1:
    print('✅ Precio muy cerca del nivel objetivo')
elif abs(distance_pct) < 3:
    print('⚠️ Precio moderadamente cerca del objetivo')
else:
    print('❌ Precio alejado del objetivo')

# Análisis de los últimos máximos y mínimos
print(f'\n📈 ESTRUCTURA DE PRECIO')
print('-' * 40)
print(f'Máximo 24h: ${df_1h["High"].max():.6f}')
print(f'Mínimo 24h: ${df_1h["Low"].min():.6f}')
print(f'Rango 24h: ${df_1h["High"].max() - df_1h["Low"].min():.6f}')

# Soporte y resistencia
support = df_1h['Low'].rolling(20).min().iloc[-1]
resistance = df_1h['High'].rolling(20).max().iloc[-1]
print(f'\nNiveles clave:')
print(f'  Soporte (20h): ${support:.6f}')
print(f'  Resistencia (20h): ${resistance:.6f}')

# Indicadores actuales
print(f'\n🎯 INDICADORES TÉCNICOS')
print('-' * 40)
print(f'RSI(14) 1H: {df_1h["RSI"].iloc[-1]:.2f}')
print(f'RSI(14) 4H: {df_4h["RSI"].iloc[-1]:.2f}')

# Interpretación RSI
if df_1h["RSI"].iloc[-1] > 70:
    rsi_signal = "SOBRECOMPRA - Favorable para SELL"
elif df_1h["RSI"].iloc[-1] < 30:
    rsi_signal = "SOBREVENTA - Favorable para BUY"
else:
    rsi_signal = "NEUTRAL"
print(f'  Interpretación: {rsi_signal}')

print(f'\nMedias móviles:')
print(f'  EMA 9 (1H): ${df_1h["EMA_9"].iloc[-1]:.6f}')
print(f'  EMA 21 (1H): ${df_1h["EMA_21"].iloc[-1]:.6f}')

if df_1h['EMA_9'].iloc[-1] > df_1h['EMA_21'].iloc[-1]:
    print('  ✅ Configuración ALCISTA (EMA9 > EMA21)')
    ema_bias = "BUY"
else:
    print('  ❌ Configuración BAJISTA (EMA9 < EMA21)')
    ema_bias = "SELL"

# MACD
print(f'\nMACD:')
print(f'  MACD: {df_1h["MACD"].iloc[-1]:.8f}')
print(f'  Señal: {df_1h["MACD_Signal"].iloc[-1]:.8f}')
if df_1h["MACD"].iloc[-1] > df_1h["MACD_Signal"].iloc[-1]:
    print('  ✅ MACD alcista')
    macd_bias = "BUY"
else:
    print('  ❌ MACD bajista')
    macd_bias = "SELL"

# Bollinger Bands
print(f'\nBollinger Bands:')
print(f'  Superior: ${df_1h["BB_Upper"].iloc[-1]:.6f}')
print(f'  Medio: ${df_1h["BB_Middle"].iloc[-1]:.6f}')
print(f'  Inferior: ${df_1h["BB_Lower"].iloc[-1]:.6f}')

bb_position = (current_price - df_1h['BB_Lower'].iloc[-1]) / (df_1h['BB_Upper'].iloc[-1] - df_1h['BB_Lower'].iloc[-1])
print(f'  Posición: {bb_position * 100:.1f}% (0%=inferior, 100%=superior)')

if bb_position > 0.8:
    bb_signal = "Cerca de BB superior - Favorable para SELL"
elif bb_position < 0.2:
    bb_signal = "Cerca de BB inferior - Favorable para BUY"
else:
    bb_signal = "En zona media"
print(f'  Interpretación: {bb_signal}')

# Análisis de volumen
avg_volume = df_1h['Volume'].rolling(20).mean().iloc[-1]
current_volume = df_1h['Volume'].iloc[-1]
volume_ratio = current_volume / avg_volume

print(f'\n📊 ANÁLISIS DE VOLUMEN')
print('-' * 40)
print(f'Volumen actual: {current_volume:,.0f}')
print(f'Volumen promedio (20h): {avg_volume:,.0f}')
print(f'Ratio: {volume_ratio:.2f}x')

if volume_ratio > 1.5:
    print('✅ Volumen alto - Mayor convicción en movimiento')
elif volume_ratio < 0.5:
    print('⚠️ Volumen bajo - Posible falta de interés')
else:
    print('Volumen normal')

# Validación de señales del screenshot
print(f'\n🔮 VALIDACIÓN DE SEÑALES FILOSÓFICAS')
print('=' * 70)

# Señal BUY de Aristoteles (82.5% confianza)
print(f'\n1. ARISTOTELES - BUY @ $0.22 (82.5% confianza)')
print('-' * 40)

buy_score = 0
buy_reasons = []

if current_price < 0.22:
    buy_score += 2
    buy_reasons.append("✅ Precio actual por debajo del entry")
    
if rsi_signal == "SOBREVENTA - Favorable para BUY":
    buy_score += 2
    buy_reasons.append("✅ RSI en sobreventa")
elif df_1h["RSI"].iloc[-1] < 50:
    buy_score += 1
    buy_reasons.append("⚠️ RSI bajo pero no extremo")

if ema_bias == "BUY":
    buy_score += 2
    buy_reasons.append("✅ EMAs en configuración alcista")
else:
    buy_reasons.append("❌ EMAs en configuración bajista")

if macd_bias == "BUY":
    buy_score += 1
    buy_reasons.append("✅ MACD alcista")
else:
    buy_reasons.append("❌ MACD bajista")

if bb_position < 0.3:
    buy_score += 2
    buy_reasons.append("✅ Cerca de Bollinger inferior")

# Análisis de estructura
higher_lows = df_1h['Low'].iloc[-1] > df_1h['Low'].iloc[-5]
if higher_lows:
    buy_score += 1
    buy_reasons.append("✅ Formando mínimos más altos")

print("Análisis:")
for reason in buy_reasons:
    print(f"  {reason}")

buy_confidence = min(buy_score / 10 * 100, 90)
print(f"\nConfianza calculada: {buy_confidence:.1f}%")
print(f"Confianza de Aristoteles: 82.5%")

if abs(buy_confidence - 82.5) < 15:
    print("✅ SEÑAL VALIDADA - Confianza alineada")
else:
    print("⚠️ DISCREPANCIA en nivel de confianza")

# Señal SELL de Platon (77.5% confianza)
print(f'\n2. PLATON - SELL @ $0.22 (77.5% confianza)')
print('-' * 40)

sell_score = 0
sell_reasons = []

if current_price > 0.22:
    sell_score += 2
    sell_reasons.append("✅ Precio actual por encima del entry")
    
if rsi_signal == "SOBRECOMPRA - Favorable para SELL":
    sell_score += 2
    sell_reasons.append("✅ RSI en sobrecompra")
elif df_1h["RSI"].iloc[-1] > 50:
    sell_score += 1
    sell_reasons.append("⚠️ RSI alto pero no extremo")

if ema_bias == "SELL":
    sell_score += 2
    sell_reasons.append("✅ EMAs en configuración bajista")
else:
    sell_reasons.append("❌ EMAs en configuración alcista")

if macd_bias == "SELL":
    sell_score += 1
    sell_reasons.append("✅ MACD bajista")
else:
    sell_reasons.append("❌ MACD alcista")

if bb_position > 0.7:
    sell_score += 2
    sell_reasons.append("✅ Cerca de Bollinger superior")

# Resistencia cercana
if abs(0.22 - resistance) < 0.005:
    sell_score += 1
    sell_reasons.append("✅ En zona de resistencia")

print("Análisis:")
for reason in sell_reasons:
    print(f"  {reason}")

sell_confidence = min(sell_score / 10 * 100, 90)
print(f"\nConfianza calculada: {sell_confidence:.1f}%")
print(f"Confianza de Platon: 77.5%")

if abs(sell_confidence - 77.5) < 15:
    print("✅ SEÑAL VALIDADA - Confianza alineada")
else:
    print("⚠️ DISCREPANCIA en nivel de confianza")

# Resumen final
print(f'\n' + '=' * 70)
print(' RESUMEN DE VALIDACIÓN '.center(70))
print('=' * 70)

print(f'\n📋 CONCLUSIONES:')
print('-' * 40)

# Determinar sesgo general
total_buy_signals = sum([1 for x in [ema_bias, macd_bias] if x == "BUY"])
total_sell_signals = sum([1 for x in [ema_bias, macd_bias] if x == "SELL"])

if current_price < 0.22:
    print(f"1. Precio actual (${current_price:.6f}) DEBAJO de $0.22")
    print("   → Favorable para entradas LONG si hay confirmación")
elif current_price > 0.22:
    print(f"1. Precio actual (${current_price:.6f}) ENCIMA de $0.22")
    print("   → Favorable para entradas SHORT si hay confirmación")
else:
    print(f"1. Precio exactamente en $0.22 - Zona de decisión")

print(f"\n2. Indicadores técnicos:")
print(f"   - Señales BUY: {total_buy_signals}")
print(f"   - Señales SELL: {total_sell_signals}")

if volume_ratio > 1.2:
    print(f"\n3. ✅ Volumen elevado ({volume_ratio:.1f}x) confirma interés del mercado")
else:
    print(f"\n3. ⚠️ Volumen normal/bajo ({volume_ratio:.1f}x) - Precaución")

print(f"\n4. VALIDACIÓN FILOSÓFICA:")
if buy_confidence > 60 and sell_confidence > 60:
    print("   ⚠️ MERCADO INDECISO - Ambas señales tienen validez")
    print("   → Recomienda esperar confirmación o usar stops ajustados")
elif buy_confidence > sell_confidence:
    print("   ✅ Sesgo ALCISTA - Señal BUY de Aristoteles más probable")
else:
    print("   ✅ Sesgo BAJISTA - Señal SELL de Platon más probable")

# Análisis de tiempo de las señales (de la captura de pantalla)
print(f"\n5. TIMING DE SEÑALES (según screenshot):")
print("   - Señales generadas entre 1:42 AM - 1:57 AM")
print("   - Múltiples confirmaciones en ventana de 15 minutos")
print("   → Sugiere zona de alta actividad y decisión del mercado")

print("\n" + "=" * 70)