#!/usr/bin/env python3
"""
Ejemplo de cómo se ven los logs en Render
"""

# Esto es lo que verías en Render Dashboard > Logs:

"""
2024-12-17 14:23:15 - INFO - 🔄 Iniciando ciclo de trading...
2024-12-17 14:23:16 - INFO - ⏱️ Revisando posiciones activas: 2 posiciones
2024-12-17 14:23:17 - INFO - ✅ BTC-USD LONG CLOSED | TAKE_PROFIT | P&L: $245.67
2024-12-17 14:23:18 - INFO - 🎯 NEW SIGNAL: ETH-USD SHORT | Entry: $3,847.23 | Conf: 67.5% | Signals: RSI_OVERBOUGHT, MACD_BEARISH, BELOW_EMA20
2024-12-17 14:23:19 - INFO - 📊 Stats: 15 trades, 73.3% WR, $1,247.89 P&L
2024-12-17 14:23:20 - INFO - ⏱️ Esperando 15 minutos...

2024-12-17 14:38:15 - INFO - 🔄 Iniciando ciclo de trading...
2024-12-17 14:38:16 - INFO - ⏱️ Revisando posiciones activas: 3 posiciones
2024-12-17 14:38:17 - INFO - 🎯 NEW SIGNAL: SOL-USD LONG | Entry: $198.45 | Conf: 58.2% | Signals: RSI_OVERSOLD, MACD_BULLISH, UPTREND
2024-12-17 14:38:18 - INFO - 📊 Stats: 16 trades, 75.0% WR, $1,389.12 P&L
2024-12-17 14:38:19 - INFO - ⏱️ Esperando 15 minutos...
"""

# En Render Dashboard te vez así:
# https://dashboard.render.com/web/srv-xxxxx
# Tab: "Logs" -> Stream en tiempo real