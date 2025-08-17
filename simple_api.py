#!/usr/bin/env python3
"""
API simple para consultar datos del bot sin frontend completo
"""

from flask import Flask, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Simulamos datos del bot (en realidad vendrían del sistema)
class TradingBotAPI:
    def __init__(self):
        # En implementación real, esto vendría del bot
        self.bot_data = {
            "active_positions": [],
            "trade_history": [],
            "system_stats": {},
            "last_signals": []
        }
    
    @app.route('/status')
    def get_status():
        """Status básico del sistema"""
        return jsonify({
            "status": "RUNNING",
            "uptime": "2d 14h 23m",
            "last_check": "2 minutes ago",
            "active_positions": len(bot.active_positions),
            "total_trades_today": 3,
            "current_capital": 10247.89
        })
    
    @app.route('/positions')
    def get_positions():
        """Posiciones activas"""
        return jsonify({
            "active_positions": [
                {
                    "symbol": "BTC-USD",
                    "type": "LONG",
                    "entry_price": 43200.50,
                    "stop_loss": 41800.00,
                    "take_profit": 46100.00,
                    "current_pnl": 145.67,
                    "entry_time": "2024-12-17T14:23:15",
                    "confidence": 0.685
                },
                {
                    "symbol": "ETH-USD", 
                    "type": "SHORT",
                    "entry_price": 2847.23,
                    "stop_loss": 2910.00,
                    "take_profit": 2650.00,
                    "current_pnl": -23.45,
                    "entry_time": "2024-12-17T14:38:42",
                    "confidence": 0.572
                }
            ]
        })
    
    @app.route('/signals')
    def get_recent_signals():
        """Señales recientes (últimas 24h)"""
        return jsonify({
            "recent_signals": [
                {
                    "timestamp": "2024-12-17T14:38:15",
                    "symbol": "SOL-USD",
                    "type": "LONG",
                    "confidence": 0.582,
                    "signals": ["RSI_OVERSOLD", "MACD_BULLISH", "UPTREND"],
                    "status": "EXECUTED",
                    "entry_price": 198.45
                },
                {
                    "timestamp": "2024-12-17T14:23:15", 
                    "symbol": "ADA-USD",
                    "type": "SHORT",
                    "confidence": 0.451,
                    "signals": ["RSI_OVERBOUGHT", "MACD_BEARISH"],
                    "status": "FILTERED",  # No ejecutado por baja confianza
                    "entry_price": 0.85
                }
            ]
        })
    
    @app.route('/stats')
    def get_stats():
        """Estadísticas de performance"""
        return jsonify({
            "performance": {
                "total_trades": 47,
                "win_rate": 68.5,
                "profit_factor": 2.34,
                "total_pnl": 1247.89,
                "roi": 12.48,
                "best_trade": 456.78,
                "worst_trade": -123.45,
                "avg_trade_duration": "4.2h",
                "current_drawdown": 2.1
            },
            "daily_stats": {
                "trades_today": 3,
                "pnl_today": 234.56,
                "win_rate_today": 66.7
            }
        })
    
    @app.route('/history')
    def get_history():
        """Historial de trades (últimos 10)"""
        return jsonify({
            "recent_trades": [
                {
                    "symbol": "BTC-USD",
                    "type": "LONG", 
                    "entry_price": 42100.00,
                    "exit_price": 43650.00,
                    "pnl": 245.67,
                    "pnl_pct": 3.68,
                    "exit_reason": "TAKE_PROFIT",
                    "duration": "3.2h",
                    "entry_time": "2024-12-17T10:15:00",
                    "exit_time": "2024-12-17T13:27:00"
                }
                # ... más trades
            ]
        })

# URLs que puedes abrir en el navegador:
"""
📱 CÓMO USAR LA API SIMPLE:

1. Abrir en navegador:
   https://tu-app.onrender.com/status
   https://tu-app.onrender.com/positions  
   https://tu-app.onrender.com/signals
   https://tu-app.onrender.com/stats

2. O usar curl:
   curl https://tu-app.onrender.com/status

3. Bookmark en móvil para acceso rápido

4. JSON fácil de leer, ejemplo:
   {
     "status": "RUNNING",
     "active_positions": 2,
     "total_trades_today": 3,
     "current_capital": 10247.89
   }
"""