#!/usr/bin/env python3
"""
Integración con Telegram para recibir señales directamente en tu móvil
"""

import requests
import json
from datetime import datetime

class TelegramNotifier:
    """
    Envía notificaciones a Telegram
    """
    
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message, parse_mode="HTML"):
        """Envía mensaje básico"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")
            return False
    
    def send_signal_alert(self, trade_data):
        """Envía alerta de nueva señal"""
        
        signal_emoji = "🟢" if trade_data['type'] == 'LONG' else "🔴"
        
        message = f"""
{signal_emoji} <b>NUEVA SEÑAL</b>

📊 <b>Símbolo:</b> {trade_data['symbol']}
📈 <b>Tipo:</b> {trade_data['type']}
💰 <b>Entry:</b> ${trade_data['entry_price']:,.2f}
🎯 <b>Confianza:</b> {trade_data['confidence']:.1%}

🛡️ <b>Stop Loss:</b> ${trade_data['stop_loss']:,.2f}
🎊 <b>Take Profit:</b> ${trade_data['take_profit']:,.2f}

🔍 <b>Señales:</b> {', '.join(trade_data['signals'][:3])}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_message(message)
    
    def send_trade_close(self, trade_data):
        """Envía alerta cuando se cierra un trade"""
        
        result_emoji = "✅" if trade_data['pnl'] > 0 else "❌"
        
        duration = (trade_data['exit_time'] - trade_data['entry_time']).total_seconds() / 3600
        
        message = f"""
{result_emoji} <b>TRADE CERRADO</b>

📊 <b>Símbolo:</b> {trade_data['symbol']}
📈 <b>Resultado:</b> {trade_data['exit_reason']}
💰 <b>P&L:</b> ${trade_data['pnl']:,.2f} ({trade_data['pnl_pct']:+.2f}%)
🕐 <b>Duración:</b> {duration:.1f}h

📍 <b>Entry → Exit:</b> ${trade_data['entry_price']:,.2f} → ${trade_data['exit_price']:,.2f}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return self.send_message(message)
    
    def send_daily_summary(self, stats):
        """Envía resumen diario"""
        
        status_emoji = "📈" if stats['total_pnl'] > 0 else "📉"
        
        message = f"""
{status_emoji} <b>RESUMEN DIARIO</b>

💰 <b>P&L Total:</b> ${stats['total_pnl']:,.2f}
📈 <b>ROI:</b> {stats['roi']:+.2f}%
🎯 <b>Win Rate:</b> {stats['win_rate']:.1f}%
📊 <b>Trades:</b> {stats['total_trades']}
⚡ <b>Profit Factor:</b> {stats['profit_factor']:.2f}
💼 <b>Capital:</b> ${stats['current_capital']:,.2f}

🤖 Trading Bot V2.5
        """.strip()
        
        return self.send_message(message)
    
    def send_system_status(self, status, error_msg=None):
        """Envía status del sistema"""
        
        if status == "STARTED":
            emoji = "🚀"
            message = f"{emoji} <b>BOT INICIADO</b>\n\n✅ Sistema V2.5 funcionando\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elif status == "STOPPED":
            emoji = "🛑"
            message = f"{emoji} <b>BOT DETENIDO</b>\n\n❌ Sistema pausado\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elif status == "ERROR":
            emoji = "⚠️"
            message = f"{emoji} <b>ERROR EN SISTEMA</b>\n\n❌ {error_msg or 'Error desconocido'}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            emoji = "ℹ️"
            message = f"{emoji} <b>STATUS UPDATE</b>\n\n📊 {status}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_message(message)

# Configuración paso a paso:
"""
🤖 CÓMO CONFIGURAR TELEGRAM BOT:

1. Hablar con @BotFather en Telegram
2. Enviar: /newbot
3. Elegir nombre: "Mi Trading Bot"
4. Elegir username: "mi_trading_v25_bot"
5. Copiar TOKEN que te da

6. Obtener tu CHAT_ID:
   - Enviar mensaje a tu bot
   - Ir a: https://api.telegram.org/bot<TOKEN>/getUpdates
   - Buscar "chat":{"id": 123456789}

7. En tu código:
telegram = TelegramNotifier(
    bot_token="123456789:ABC...",
    chat_id="123456789"
)
"""