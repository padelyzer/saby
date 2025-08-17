#!/usr/bin/env python3
"""
Sistema de Gestión y Entrega de Señales de Trading
Proporciona múltiples canales de notificación para señales en tiempo real
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from dataclasses import dataclass, asdict
# Importaciones async removidas - no se usan actualmente
# import asyncio
# import aiohttp
# from concurrent.futures import ThreadPoolExecutor

# Importar módulos del sistema
from motor_trading import (
    obtener_datos,
    calcular_indicadores,
    calcular_score,
    calcular_semaforo_mercado
)

@dataclass
class TradingSignal:
    """Estructura de una señal de trading"""
    timestamp: str
    ticker: str
    action: str  # BUY_LONG, BUY_SHORT, SELL
    price: float
    stop_loss: float
    take_profit: float
    score: float
    direccion: str  # LONG/SHORT
    timeframe: str
    exchange: str = "Binance"
    leverage: int = 3
    position_size_pct: float = 5.0  # % del capital
    risk_reward_ratio: float = 2.5
    confidence: str = "HIGH"  # HIGH, MEDIUM, LOW
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)
    
    def format_message(self):
        """Formatea la señal para mensajes legibles"""
        emoji = "🟢" if self.direccion == "LONG" else "🔴"
        action_text = "COMPRAR" if "BUY" in self.action else "VENDER"
        
        message = f"""
{emoji} **SEÑAL {self.direccion}** {emoji}
━━━━━━━━━━━━━━━━━━━
📊 **Par:** {self.ticker}
⚡ **Acción:** {action_text}
💰 **Precio Entrada:** ${self.price:.4f}
🛑 **Stop Loss:** ${self.stop_loss:.4f}
🎯 **Take Profit:** ${self.take_profit:.4f}
📈 **Score:** {self.score:.1f}/10
⚙️ **Apalancamiento:** {self.leverage}x
📏 **Tamaño:** {self.position_size_pct}% del capital
⏰ **Hora:** {self.timestamp}
━━━━━━━━━━━━━━━━━━━
"""
        return message

class NotificationChannel:
    """Clase base para canales de notificación"""
    
    def send(self, signal: TradingSignal) -> bool:
        raise NotImplementedError

class TelegramNotifier(NotificationChannel):
    """Envía señales por Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send(self, signal: TradingSignal) -> bool:
        """Envía señal por Telegram"""
        try:
            message = signal.format_message()
            
            # Agregar botones inline para copiar valores
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "📋 Copiar Entry", "callback_data": f"copy_entry_{signal.price}"},
                        {"text": "📋 Copiar SL", "callback_data": f"copy_sl_{signal.stop_loss}"}
                    ],
                    [
                        {"text": "📋 Copiar TP", "callback_data": f"copy_tp_{signal.take_profit}"},
                        {"text": "✅ Aplicar Trade", "callback_data": f"apply_{signal.ticker}"}
                    ]
                ]
            }
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'reply_markup': json.dumps(keyboard)
            }
            
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json=payload
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")
            return False

class DiscordWebhook(NotificationChannel):
    """Envía señales por Discord Webhook"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, signal: TradingSignal) -> bool:
        """Envía señal por Discord"""
        try:
            # Crear embed para Discord
            embed = {
                "title": f"{signal.direccion} Signal - {signal.ticker}",
                "color": 0x00ff00 if signal.direccion == "LONG" else 0xff0000,
                "fields": [
                    {"name": "💰 Entry Price", "value": f"${signal.price:.4f}", "inline": True},
                    {"name": "🛑 Stop Loss", "value": f"${signal.stop_loss:.4f}", "inline": True},
                    {"name": "🎯 Take Profit", "value": f"${signal.take_profit:.4f}", "inline": True},
                    {"name": "📊 Score", "value": f"{signal.score:.1f}/10", "inline": True},
                    {"name": "⚡ Leverage", "value": f"{signal.leverage}x", "inline": True},
                    {"name": "📏 Size", "value": f"{signal.position_size_pct}%", "inline": True}
                ],
                "footer": {"text": f"Signal generated at {signal.timestamp}"},
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {
                "embeds": [embed],
                "content": f"@everyone New {signal.confidence} confidence signal!"
            }
            
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 204
            
        except Exception as e:
            print(f"Error enviando a Discord: {e}")
            return False

class EmailNotifier(NotificationChannel):
    """Envía señales por Email (usando servicio SMTP)"""
    
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str, to_email: str):
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.to_email = to_email
        self.smtplib = smtplib
        self.MIMEText = MIMEText
        self.MIMEMultipart = MIMEMultipart
    
    def send(self, signal: TradingSignal) -> bool:
        """Envía señal por Email"""
        try:
            msg = self.MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.to_email
            msg['Subject'] = f"🚨 Trading Signal: {signal.direccion} {signal.ticker}"
            
            body = signal.format_message()
            msg.attach(self.MIMEText(body, 'plain'))
            
            server = self.smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error enviando Email: {e}")
            return False

class WebhookNotifier(NotificationChannel):
    """Envía señales a un webhook personalizado (para automatización)"""
    
    def __init__(self, webhook_url: str, api_key: Optional[str] = None):
        self.webhook_url = webhook_url
        self.api_key = api_key
    
    def send(self, signal: TradingSignal) -> bool:
        """Envía señal al webhook"""
        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['X-API-Key'] = self.api_key
            
            # Formato para trading bots (TradingView, 3Commas, etc)
            payload = {
                "symbol": signal.ticker,
                "side": "buy" if "BUY" in signal.action else "sell",
                "type": "market",
                "leverage": signal.leverage,
                "position_size_percent": signal.position_size_pct,
                "entry_price": signal.price,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "comment": f"Score: {signal.score}, Direction: {signal.direccion}",
                "timestamp": signal.timestamp
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            return response.status_code in [200, 201, 204]
            
        except Exception as e:
            print(f"Error enviando al webhook: {e}")
            return False

class SignalManager:
    """Gestor principal de señales de trading"""
    
    def __init__(self, config_file='signal_config.json'):
        self.config_file = config_file
        self.channels: List[NotificationChannel] = []
        self.signal_history: List[TradingSignal] = []
        self.active_signals: Dict[str, TradingSignal] = {}
        self.load_config()
    
    def load_config(self):
        """Carga configuración de canales desde archivo"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.setup_channels(config)
        else:
            # Crear configuración por defecto
            self.create_default_config()
    
    def create_default_config(self):
        """Crea archivo de configuración por defecto"""
        config = {
            "telegram": {
                "enabled": False,
                "bot_token": "YOUR_BOT_TOKEN",
                "chat_id": "YOUR_CHAT_ID"
            },
            "discord": {
                "enabled": False,
                "webhook_url": "YOUR_DISCORD_WEBHOOK_URL"
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "email": "your_email@gmail.com",
                "password": "your_app_password",
                "to_email": "recipient@gmail.com"
            },
            "webhook": {
                "enabled": False,
                "url": "https://your-trading-bot.com/webhook",
                "api_key": "YOUR_API_KEY"
            },
            "filters": {
                "min_score": 5,
                "max_simultaneous_signals": 5,
                "cooldown_minutes": 15
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"📝 Archivo de configuración creado: {self.config_file}")
        print("⚠️ Por favor, edita el archivo con tus credenciales")
    
    def setup_channels(self, config: dict):
        """Configura los canales de notificación activos"""
        self.channels = []
        
        # Telegram
        if config.get('telegram', {}).get('enabled'):
            self.channels.append(
                TelegramNotifier(
                    config['telegram']['bot_token'],
                    config['telegram']['chat_id']
                )
            )
            print("✅ Canal Telegram activado")
        
        # Discord
        if config.get('discord', {}).get('enabled'):
            self.channels.append(
                DiscordWebhook(config['discord']['webhook_url'])
            )
            print("✅ Canal Discord activado")
        
        # Email
        if config.get('email', {}).get('enabled'):
            self.channels.append(
                EmailNotifier(
                    config['email']['smtp_server'],
                    config['email']['smtp_port'],
                    config['email']['email'],
                    config['email']['password'],
                    config['email']['to_email']
                )
            )
            print("✅ Canal Email activado")
        
        # Webhook
        if config.get('webhook', {}).get('enabled'):
            self.channels.append(
                WebhookNotifier(
                    config['webhook']['url'],
                    config['webhook'].get('api_key')
                )
            )
            print("✅ Canal Webhook activado")
        
        self.filters = config.get('filters', {})
    
    def generate_signal(self, ticker: str, df: pd.DataFrame, estado_mercado: str) -> Optional[TradingSignal]:
        """Genera una señal de trading si las condiciones se cumplen"""
        try:
            # Calcular indicadores y score
            df = calcular_indicadores(df)
            score, etapa, direccion = calcular_score(df, estado_mercado)
            
            # Verificar filtros
            min_score = self.filters.get('min_score', 5)
            if score < min_score or direccion == 'NONE':
                return None
            
            # Verificar cooldown - CORREGIDO para evitar repeticiones
            if ticker in self.active_signals:
                last_signal = self.active_signals[ticker]
                last_time = datetime.fromisoformat(last_signal.timestamp)
                cooldown = self.filters.get('cooldown_minutes', 60)  # Aumentado a 60 minutos
                
                if datetime.now() - last_time < timedelta(minutes=cooldown):
                    # No generar señal si ya existe una reciente
                    return None
            
            # Obtener precio actual
            precio_actual = float(df['Close'].iloc[-1])
            
            # Calcular SL y TP según dirección
            leverage = 3
            if direccion == 'LONG':
                stop_loss = precio_actual * 0.99    # -1%
                take_profit = precio_actual * 1.025  # +2.5%
                action = "BUY_LONG"
            else:  # SHORT
                stop_loss = precio_actual * 1.01    # +1%
                take_profit = precio_actual * 0.975  # -2.5%
                action = "BUY_SHORT"
            
            # Determinar confianza
            if score >= 7:
                confidence = "HIGH"
                position_size = 5.0
            elif score >= 5:
                confidence = "MEDIUM"
                position_size = 3.0
            else:
                confidence = "LOW"
                position_size = 2.0
            
            # Crear señal
            signal = TradingSignal(
                timestamp=datetime.now().isoformat(),
                ticker=ticker,
                action=action,
                price=precio_actual,
                stop_loss=stop_loss,
                take_profit=take_profit,
                score=score,
                direccion=direccion,
                timeframe="1H",
                leverage=leverage,
                position_size_pct=position_size,
                risk_reward_ratio=2.5,
                confidence=confidence
            )
            
            return signal
            
        except Exception as e:
            print(f"Error generando señal para {ticker}: {e}")
            return None
    
    def broadcast_signal(self, signal: TradingSignal) -> dict:
        """Envía la señal a todos los canales activos"""
        results = {}
        
        # Guardar en historial
        self.signal_history.append(signal)
        self.active_signals[signal.ticker] = signal
        
        # NUEVO: Registrar en Trade Tracker
        try:
            from trade_tracker import TradeTracker
            tracker = TradeTracker()
            
            # Convertir señal a formato para tracker
            trade_signal = {
                'ticker': signal.ticker,
                'direccion': signal.direccion,
                'price': signal.price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'score': signal.score,
                'leverage': signal.leverage,
                'position_size_pct': signal.position_size_pct,
                'notes': f"Auto-signal {signal.confidence} confidence"
            }
            
            # Abrir trade automáticamente
            trade_id = tracker.open_trade(trade_signal)
            print(f"📊 Trade registrado: {trade_id}")
            
            # Iniciar monitoreo si no está activo
            tracker.start_monitoring()
            
        except Exception as e:
            print(f"⚠️ Error registrando trade: {e}")
        
        # Enviar a cada canal
        for channel in self.channels:
            channel_name = channel.__class__.__name__
            try:
                success = channel.send(signal)
                results[channel_name] = success
                if success:
                    print(f"✅ Señal enviada por {channel_name}")
                else:
                    print(f"❌ Error enviando por {channel_name}")
            except Exception as e:
                print(f"❌ Error en {channel_name}: {e}")
                results[channel_name] = False
        
        # Guardar señal en archivo
        self.save_signal_to_file(signal)
        
        return results
    
    def save_signal_to_file(self, signal: TradingSignal):
        """Guarda la señal en un archivo JSON para registro"""
        filename = f"signals_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Cargar señales existentes o crear nueva lista
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                signals = json.load(f)
        else:
            signals = []
        
        # Agregar nueva señal
        signals.append(signal.to_dict())
        
        # Guardar
        with open(filename, 'w') as f:
            json.dump(signals, f, indent=2)
    
    def scan_market(self, tickers: List[str]) -> List[TradingSignal]:
        """Escanea el mercado en busca de señales"""
        signals = []
        estado_mercado = calcular_semaforo_mercado()
        
        if estado_mercado == 'AMARILLO':
            print("⚠️ Mercado neutral - Sin señales")
            return signals
        
        print(f"🔍 Escaneando {len(tickers)} activos...")
        print(f"📊 Estado del mercado: {estado_mercado}")
        
        for ticker in tickers:
            try:
                # Obtener datos
                df = obtener_datos(ticker, period='1y')
                if df is None or len(df) < 200:
                    continue
                
                # Generar señal si cumple condiciones
                signal = self.generate_signal(ticker, df, estado_mercado)
                if signal:
                    signals.append(signal)
                    print(f"🎯 Señal encontrada: {signal.direccion} {ticker} (Score: {signal.score:.1f})")
            
            except Exception as e:
                print(f"Error analizando {ticker}: {e}")
                continue
        
        return signals
    
    def get_active_signals(self) -> List[TradingSignal]:
        """Retorna las señales activas"""
        return list(self.active_signals.values())
    
    def close_signal(self, ticker: str, reason: str = "manual"):
        """Cierra una señal activa"""
        if ticker in self.active_signals:
            signal = self.active_signals[ticker]
            del self.active_signals[ticker]
            
            # Notificar cierre
            close_msg = f"❌ Señal cerrada: {ticker}\nRazón: {reason}"
            # Enviar notificación de cierre
            print(close_msg)
            
            return True
        return False

def main():
    """Función principal para pruebas"""
    print("🚀 Iniciando Signal Manager")
    print("=" * 50)
    
    # Crear instancia del gestor
    manager = SignalManager()
    
    # Lista de criptos a monitorear
    tickers = [
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
        'ADA-USD', 'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD'
    ]
    
    print("\n📡 Sistema de señales configurado")
    print(f"📊 Monitoreando {len(tickers)} activos")
    print(f"🔔 Canales activos: {len(manager.channels)}")
    
    # Escanear mercado
    print("\n🔍 Escaneando mercado...")
    signals = manager.scan_market(tickers)
    
    if signals:
        print(f"\n✅ {len(signals)} señales encontradas!")
        for signal in signals:
            print(f"\n{signal.format_message()}")
            
            # Enviar señal
            results = manager.broadcast_signal(signal)
            print(f"📤 Resultados de envío: {results}")
    else:
        print("\n❌ No se encontraron señales en este momento")
    
    print("\n✅ Escaneo completado")

if __name__ == "__main__":
    main()