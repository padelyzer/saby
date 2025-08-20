#!/usr/bin/env python3

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Obtener datos de AVAX
ticker = yf.Ticker('AVAX-USD')
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Datos de múltiples timeframes
df_1h = ticker.history(start=start_date, end=end_date, interval='1h')
df_4h = ticker.history(start=start_date, end=end_date, interval='4h')
df_daily = ticker.history(start=start_date, end=end_date, interval='1d')

print('ANÁLISIS ACTUAL DE AVAX-USD')
print('='*50)

# Precio actual
current_price = df_1h['Close'].iloc[-1]
print(f'Precio actual: ${current_price:.4f}')

# Volatilidad
atr_1h = ((df_1h['High'] - df_1h['Low']).rolling(14).mean()).iloc[-1]
vol_24h = ((df_daily['High'] - df_daily['Low']) / df_daily['Close'] * 100).iloc[-1]

print(f'ATR 1H: ${atr_1h:.4f}')
print(f'Volatilidad 24H: {vol_24h:.2f}%')

# RSI en diferentes timeframes
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

rsi_1h = calculate_rsi(df_1h['Close']).iloc[-1]
rsi_4h = calculate_rsi(df_4h['Close']).iloc[-1]
rsi_daily = calculate_rsi(df_daily['Close']).iloc[-1]

print(f'RSI 1H: {rsi_1h:.2f}')
print(f'RSI 4H: {rsi_4h:.2f}')
print(f'RSI Daily: {rsi_daily:.2f}')

# Soporte y resistencia últimos 7 días
support_7d = df_1h['Low'].rolling(168).min().iloc[-1]  # 7 días * 24 horas
resistance_7d = df_1h['High'].rolling(168).max().iloc[-1]

print(f'Soporte 7D: ${support_7d:.4f}')
print(f'Resistencia 7D: ${resistance_7d:.4f}')

# Volumen promedio
vol_avg = df_1h['Volume'].rolling(24).mean().iloc[-1]
vol_current = df_1h['Volume'].iloc[-1]

print(f'Volumen promedio 24H: {vol_avg:,.0f}')
print(f'Volumen actual: {vol_current:,.0f}')
print(f'Ratio volumen: {vol_current/vol_avg:.2f}x')

# Tendencia EMAs
ema_20 = df_1h['Close'].ewm(span=20).mean().iloc[-1]
ema_50 = df_1h['Close'].ewm(span=50).mean().iloc[-1]

print(f'EMA 20: ${ema_20:.4f}')
print(f'EMA 50: ${ema_50:.4f}')
print(f'Precio vs EMA20: {((current_price/ema_20-1)*100):+.2f}%')
print(f'Precio vs EMA50: {((current_price/ema_50-1)*100):+.2f}%')