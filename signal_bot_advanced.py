#!/usr/bin/env python3
"""
Bot de Trading Avanzado con Pools de Liquidez
Combina análisis de estructura de mercado y liquidez
"""

import time
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Importar módulos del sistema
from advanced_signals import AdvancedSignalDetector, format_advanced_signal
from liquidity_pools import LiquidityPoolDetector, format_liquidity_report
from signal_manager import SignalManager, TradingSignal
from motor_trading import calcular_semaforo_mercado

class AdvancedTradingBot:
    """Bot avanzado con análisis de liquidez"""
    
    def __init__(self, config_file='signal_config.json'):
        self.config_file = config_file
        self.signal_detector = AdvancedSignalDetector()
        self.liquidity_detector = LiquidityPoolDetector()
        self.signal_manager = SignalManager(config_file)
        self.last_signals = {}  # Para evitar duplicados
        self.stats = {
            'signals_sent': 0,
            'liquidity_alerts': 0,
            'start_time': datetime.now()
        }
        
        # Lista de criptomonedas a monitorear
        self.watchlist = [
            'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
            'ADA-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD', 'LINK-USD',
            'UNI-USD', 'ATOM-USD', 'FIL-USD', 'NEAR-USD', 'APT-USD'
        ]
    
    def check_signal_cooldown(self, ticker: str, minutes: int = 60) -> bool:
        """Verifica si ha pasado suficiente tiempo desde la última señal"""
        if ticker not in self.last_signals:
            return True
        
        last_time = self.last_signals[ticker]
        if datetime.now() - last_time > timedelta(minutes=minutes):
            return True
        
        return False
    
    def analyze_ticker(self, ticker: str) -> dict:
        """Analiza un ticker con todos los sistemas"""
        results = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'signal': None,
            'liquidity': None,
            'risk_analysis': None
        }
        
        try:
            # Obtener datos
            stock = yf.Ticker(ticker)
            df = stock.history(period='3mo', interval='1h')
            
            if len(df) < 200:
                return results
            
            current_price = float(df['Close'].iloc[-1])
            
            # 1. Buscar señal avanzada
            signal = self.signal_detector.generate_advanced_signal(ticker, df)
            
            if signal:
                results['signal'] = signal
                
                # 2. Análisis de liquidez
                liquidity_data = self.liquidity_detector.detect_liquidity_pools(df, current_price)
                results['liquidity'] = liquidity_data
                
                # 3. Análisis de riesgo basado en liquidez
                risk_analysis = self.liquidity_detector.analyze_liquidity_risk(
                    df, 
                    signal['entry_price'],
                    signal['stop_loss'],
                    signal['primary_target']['price'],
                    signal['type']
                )
                results['risk_analysis'] = risk_analysis
        
        except Exception as e:
            print(f"Error analizando {ticker}: {e}")
        
        return results
    
    def format_telegram_signal(self, analysis: dict) -> str:
        """Formatea señal completa para Telegram"""
        signal = analysis['signal']
        risk = analysis.get('risk_analysis', {})
        
        emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
        
        message = f"""
{emoji} **SEÑAL AVANZADA {signal['type']}** {emoji}
════════════════════════════════════════
📊 **{signal['ticker']}**
💯 **Score:** {signal['score']}/10
📍 **Estructura:** {signal['market_structure']}

**NIVELES DE TRADING:**
━━━━━━━━━━━━━━━━━━━━
💰 **Entrada:** ${signal['entry_price']:.4f}
🛑 **Stop Loss:** ${signal['stop_loss']:.4f}
🎯 **Target 1:** ${signal['primary_target']['price']:.4f}
   _{signal['primary_target']['reason']}_
🚀 **Target 2:** ${signal['extended_target']['price']:.4f}
   _{signal['extended_target']['reason']}_

**RATIOS:**
━━━━━━━━━━━━━━━━━━━━
📊 **R:R Target 1:** {signal['risk_reward_ratio']}:1
📈 **R:R Target 2:** {signal['extended_rr_ratio']}:1

**CONFLUENCIAS ({signal['confluence_points']}):**
━━━━━━━━━━━━━━━━━━━━
"""
        
        for reason in signal['entry_reasons'][:5]:  # Max 5 razones
            message += f"• {reason}\n"
        
        # Agregar análisis de riesgo de liquidez
        if risk:
            message += f"""
💧 **ANÁLISIS DE LIQUIDEZ:**
━━━━━━━━━━━━━━━━━━━━
Risk Score: {risk.get('risk_score', 0)}/10
Clasificación: {risk.get('classification', 'N/A')}
"""
            
            if risk.get('warnings'):
                message += "\n⚠️ **Advertencias:**\n"
                for warning in risk['warnings'][:2]:
                    message += f"• {warning}\n"
            
            if risk.get('adjustments'):
                message += "\n🔧 **Ajustes Sugeridos:**\n"
                for adj in risk['adjustments'][:2]:
                    message += f"• {adj}\n"
        
        # Agregar pools de liquidez cercanos
        if 'liquidity_pools' in signal['chart_analysis']:
            top_pools = signal['chart_analysis']['liquidity_pools'][:3]
            if top_pools:
                message += "\n💧 **Pools de Liquidez Cercanos:**\n"
                for pool in top_pools:
                    direction = "↑" if pool['direction'] == 'ABOVE' else "↓"
                    message += f"• ${pool['price']:.2f} ({pool['distance_pct']:+.2f}%) {direction}\n"
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━
⏰ {datetime.now().strftime('%H:%M:%S')}
🤖 Bot Avanzado v2.0
"""
        
        return message
    
    def send_liquidity_alert(self, ticker: str, liquidity_data: dict):
        """Envía alerta sobre pools de liquidez importantes"""
        # Solo alertar sobre pools muy fuertes
        strong_pools = [p for p in liquidity_data['heatmap'] if p['importance'] > 10]
        
        if not strong_pools:
            return
        
        message = f"""
💧 **ALERTA DE LIQUIDEZ - {ticker}** 💧
━━━━━━━━━━━━━━━━━━━━

Pools de liquidez importantes detectados:
"""
        
        for pool in strong_pools[:3]:
            direction = "↑" if pool['direction'] == 'ABOVE' else "↓"
            emoji = "🔴" if 'SHORT' in pool['type'] else "🟢"
            
            message += f"""
{emoji} ${pool['price']:.2f} ({pool['distance_pct']:+.2f}%) {direction}
   Fuerza: {'█' * int(pool['strength']/2)}
   Tipo: {pool['type']}
"""
        
        message += """
━━━━━━━━━━━━━━━━━━━━
⚠️ Estos niveles pueden actuar como imanes de precio
"""
        
        # Enviar alerta
        try:
            for channel in self.signal_manager.channels:
                if hasattr(channel, 'send'):
                    # Crear señal especial para alerta
                    alert_signal = TradingSignal(
                        timestamp=datetime.now().isoformat(),
                        ticker=ticker,
                        action="ALERT",
                        price=liquidity_data['current_price'],
                        stop_loss=0,
                        take_profit=0,
                        score=0,
                        direccion="NEUTRAL",
                        timeframe="1H"
                    )
                    alert_signal.format_message = lambda: message
                    channel.send(alert_signal)
            
            self.stats['liquidity_alerts'] += 1
            
        except Exception as e:
            print(f"Error enviando alerta de liquidez: {e}")
    
    def scan_market(self):
        """Escanea el mercado buscando oportunidades"""
        print(f"\n🔍 Escaneando {len(self.watchlist)} activos...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Verificar estado del mercado
        estado_mercado = calcular_semaforo_mercado()
        print(f"📊 Estado del mercado: {estado_mercado}")
        
        if estado_mercado == 'AMARILLO':
            print("⚠️ Mercado neutral - Modo conservador activado")
        
        signals_found = []
        liquidity_alerts = []
        
        for ticker in self.watchlist:
            try:
                # Verificar cooldown
                if not self.check_signal_cooldown(ticker, minutes=60):
                    continue
                
                print(f"  Analizando {ticker}...", end="")
                
                # Análisis completo
                analysis = self.analyze_ticker(ticker)
                
                if analysis['signal']:
                    signal = analysis['signal']
                    
                    # Filtro adicional basado en riesgo
                    risk = analysis.get('risk_analysis', {})
                    if risk.get('risk_score', 10) > 7:
                        print(f" ⚠️ Riesgo alto ({risk['risk_score']}/10)")
                        continue
                    
                    print(f" ✅ Señal {signal['type']} (Score: {signal['score']})")
                    signals_found.append(analysis)
                    
                    # Actualizar último tiempo de señal
                    self.last_signals[ticker] = datetime.now()
                    
                elif analysis['liquidity']:
                    # Verificar si hay pools importantes aunque no haya señal
                    liquidity = analysis['liquidity']
                    strong_pools = [p for p in liquidity['heatmap'] if p['importance'] > 15]
                    
                    if strong_pools:
                        print(f" 💧 Pools de liquidez detectados")
                        liquidity_alerts.append((ticker, liquidity))
                    else:
                        print(" ✓")
                else:
                    print(" ✓")
                
            except Exception as e:
                print(f" ❌ Error: {e}")
                continue
        
        return signals_found, liquidity_alerts
    
    def run(self, interval_minutes: int = 5):
        """Ejecuta el bot continuamente"""
        print("""
╔════════════════════════════════════════════════════════════════╗
║           🤖 BOT DE TRADING AVANZADO CON LIQUIDEZ               ║
║                    Versión 2.0 - Producción                     ║
╚════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"📊 Monitoreando: {len(self.watchlist)} activos")
        print(f"⏰ Intervalo: {interval_minutes} minutos")
        print(f"🔔 Canales activos: {len(self.signal_manager.channels)}")
        print("\nPresiona Ctrl+C para detener\n")
        
        while True:
            try:
                # Escanear mercado
                signals, liquidity_alerts = self.scan_market()
                
                # Enviar señales
                if signals:
                    print(f"\n📤 Enviando {len(signals)} señales...")
                    
                    for analysis in signals:
                        signal = analysis['signal']
                        
                        # Crear objeto TradingSignal
                        trading_signal = TradingSignal(
                            timestamp=datetime.now().isoformat(),
                            ticker=signal['ticker'],
                            action=f"BUY_{signal['type']}",
                            price=signal['entry_price'],
                            stop_loss=signal['stop_loss'],
                            take_profit=signal['primary_target']['price'],
                            score=signal['score'],
                            direccion=signal['type'],
                            timeframe="1H",
                            leverage=3,
                            position_size_pct=5.0,
                            risk_reward_ratio=signal['risk_reward_ratio'],
                            confidence="HIGH" if signal['score'] >= 8 else "MEDIUM"
                        )
                        
                        # Sobrescribir método format_message con nuestro formato
                        original_format = trading_signal.format_message
                        trading_signal.format_message = lambda a=analysis: self.format_telegram_signal(a)
                        
                        # Enviar señal
                        results = self.signal_manager.broadcast_signal(trading_signal)
                        
                        # Restaurar método original
                        trading_signal.format_message = original_format
                        
                        self.stats['signals_sent'] += 1
                        
                        print(f"  ✅ {signal['ticker']} - {signal['type']} enviado")
                
                # Enviar alertas de liquidez importantes
                if liquidity_alerts:
                    print(f"\n💧 Enviando {len(liquidity_alerts)} alertas de liquidez...")
                    
                    for ticker, liquidity_data in liquidity_alerts:
                        self.send_liquidity_alert(ticker, liquidity_data)
                        print(f"  ✅ Alerta de liquidez para {ticker}")
                
                # Mostrar estadísticas
                self.print_stats()
                
                # Esperar hasta el próximo escaneo
                print(f"\n⏳ Próximo escaneo en {interval_minutes} minutos...")
                print("=" * 60)
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Bot detenido por el usuario")
                self.print_final_stats()
                break
            except Exception as e:
                print(f"\n❌ Error en el bot: {e}")
                print("Reiniciando en 30 segundos...")
                time.sleep(30)
    
    def print_stats(self):
        """Muestra estadísticas actuales"""
        runtime = datetime.now() - self.stats['start_time']
        hours = runtime.total_seconds() / 3600
        
        print(f"""
📊 ESTADÍSTICAS:
• Tiempo activo: {runtime}
• Señales enviadas: {self.stats['signals_sent']}
• Alertas de liquidez: {self.stats['liquidity_alerts']}
• Promedio: {self.stats['signals_sent']/max(hours, 1):.1f} señales/hora
        """)
    
    def print_final_stats(self):
        """Muestra estadísticas finales"""
        runtime = datetime.now() - self.stats['start_time']
        
        print(f"""
╔════════════════════════════════════════════════════════════════╗
║                     📊 RESUMEN DE SESIÓN                        ║
╚════════════════════════════════════════════════════════════════╝

Tiempo total: {runtime}
Señales enviadas: {self.stats['signals_sent']}
Alertas de liquidez: {self.stats['liquidity_alerts']}

✅ Bot finalizado correctamente
        """)

def main():
    """Función principal"""
    # Verificar configuración
    if not os.path.exists('signal_config.json'):
        print("❌ No se encontró signal_config.json")
        print("Ejecuta primero: python3 signal_manager.py")
        return
    
    # Crear y ejecutar bot
    bot = AdvancedTradingBot()
    
    # Parámetros configurables
    interval = 5  # minutos entre escaneos
    
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except:
            print("Uso: python3 signal_bot_advanced.py [intervalo_minutos]")
            return
    
    # Ejecutar bot
    bot.run(interval_minutes=interval)

if __name__ == "__main__":
    main()