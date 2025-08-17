#!/usr/bin/env python3
"""
Integración con Discord para recibir señales en tiempo real
"""

import requests
import json
from datetime import datetime

class DiscordNotifier:
    """
    Envía notificaciones a Discord cuando hay señales
    """
    
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_signal_alert(self, trade_data):
        """Envía alerta de nueva señal"""
        
        # Determinar color del embed
        color = 0x00ff00 if trade_data['type'] == 'LONG' else 0xff0000  # Verde/Rojo
        
        embed = {
            "title": f"🎯 NUEVA SEÑAL: {trade_data['symbol']}",
            "color": color,
            "fields": [
                {
                    "name": "📊 Tipo",
                    "value": f"**{trade_data['type']}**",
                    "inline": True
                },
                {
                    "name": "💰 Entry Price",
                    "value": f"${trade_data['entry_price']:,.2f}",
                    "inline": True
                },
                {
                    "name": "🎯 Confianza",
                    "value": f"{trade_data['confidence']:.1%}",
                    "inline": True
                },
                {
                    "name": "🛡️ Stop Loss",
                    "value": f"${trade_data['stop_loss']:,.2f}",
                    "inline": True
                },
                {
                    "name": "🎊 Take Profit",
                    "value": f"${trade_data['take_profit']:,.2f}",
                    "inline": True
                },
                {
                    "name": "📈 Risk/Reward",
                    "value": f"1:{((trade_data['take_profit'] - trade_data['entry_price']) / (trade_data['entry_price'] - trade_data['stop_loss'])):.1f}",
                    "inline": True
                },
                {
                    "name": "🔍 Señales",
                    "value": ", ".join(trade_data['signals'][:3]),
                    "inline": False
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Trading Bot V2.5"
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 204
        except Exception as e:
            print(f"Error enviando a Discord: {e}")
            return False
    
    def send_trade_close(self, trade_data):
        """Envía alerta cuando se cierra un trade"""
        
        # Color basado en P&L
        color = 0x00ff00 if trade_data['pnl'] > 0 else 0xff0000
        result_emoji = "✅" if trade_data['pnl'] > 0 else "❌"
        
        embed = {
            "title": f"{result_emoji} TRADE CERRADO: {trade_data['symbol']}",
            "color": color,
            "fields": [
                {
                    "name": "📊 Resultado",
                    "value": f"**{trade_data['exit_reason']}**",
                    "inline": True
                },
                {
                    "name": "💰 P&L",
                    "value": f"${trade_data['pnl']:,.2f}",
                    "inline": True
                },
                {
                    "name": "📈 P&L %",
                    "value": f"{trade_data['pnl_pct']:+.2f}%",
                    "inline": True
                },
                {
                    "name": "🕐 Duración",
                    "value": f"{(trade_data['exit_time'] - trade_data['entry_time']).total_seconds() / 3600:.1f}h",
                    "inline": True
                },
                {
                    "name": "📍 Entry → Exit",
                    "value": f"${trade_data['entry_price']:,.2f} → ${trade_data['exit_price']:,.2f}",
                    "inline": False
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Trading Bot V2.5"
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 204
        except Exception as e:
            print(f"Error enviando a Discord: {e}")
            return False
    
    def send_daily_summary(self, stats):
        """Envía resumen diario"""
        
        color = 0x00ff00 if stats['total_pnl'] > 0 else 0xff0000
        
        embed = {
            "title": "📊 RESUMEN DIARIO",
            "color": color,
            "fields": [
                {
                    "name": "💰 P&L Total",
                    "value": f"${stats['total_pnl']:,.2f}",
                    "inline": True
                },
                {
                    "name": "📈 ROI",
                    "value": f"{stats['roi']:+.2f}%",
                    "inline": True
                },
                {
                    "name": "🎯 Win Rate",
                    "value": f"{stats['win_rate']:.1f}%",
                    "inline": True
                },
                {
                    "name": "📊 Total Trades",
                    "value": f"{stats['total_trades']}",
                    "inline": True
                },
                {
                    "name": "⚡ Profit Factor",
                    "value": f"{stats['profit_factor']:.2f}",
                    "inline": True
                },
                {
                    "name": "💼 Capital Actual",
                    "value": f"${stats['current_capital']:,.2f}",
                    "inline": True
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "Trading Bot V2.5 - Reporte Diario"
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 204
        except Exception as e:
            print(f"Error enviando a Discord: {e}")
            return False

# Ejemplo de uso:
"""
# 1. Crear webhook en Discord:
#    Servidor > Configuración > Integraciones > Webhooks > Nuevo Webhook
#    Copiar URL del webhook

# 2. En el trading bot:
discord = DiscordNotifier("https://discord.com/api/webhooks/123456...")

# 3. Cuando hay nueva señal:
discord.send_signal_alert(trade_data)

# 4. Cuando se cierra trade:
discord.send_trade_close(closed_trade)
"""