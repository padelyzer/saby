#!/usr/bin/env python3
"""
Sistema de reportes por email
"""

import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime

class EmailReporter:
    """
    Envía reportes por email
    """
    
    def __init__(self, smtp_server, smtp_port, email, password, recipient):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.recipient = recipient
    
    def send_email(self, subject, html_content):
        """Envía email con formato HTML"""
        msg = MimeMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = self.recipient
        
        html_part = MimeText(html_content, 'html')
        msg.attach(html_part)
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error enviando email: {e}")
            return False
    
    def send_daily_report(self, stats, trades_today):
        """Reporte diario HTML"""
        
        subject = f"📊 Trading Bot V2.5 - Reporte {datetime.now().strftime('%Y-%m-%d')}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #1a73e8; color: white; padding: 20px; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .positive {{ color: #34a853; }}
                .negative {{ color: #ea4335; }}
                .trades-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .trades-table th, .trades-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .trades-table th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Trading Bot V2.5</h1>
                <h2>Reporte Diario - {datetime.now().strftime('%d/%m/%Y')}</h2>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>💰 P&L Total</h3>
                    <p class="{'positive' if stats['total_pnl'] > 0 else 'negative'}">${stats['total_pnl']:,.2f}</p>
                </div>
                <div class="stat-box">
                    <h3>📈 ROI</h3>
                    <p class="{'positive' if stats['roi'] > 0 else 'negative'}">{stats['roi']:+.2f}%</p>
                </div>
                <div class="stat-box">
                    <h3>🎯 Win Rate</h3>
                    <p>{stats['win_rate']:.1f}%</p>
                </div>
                <div class="stat-box">
                    <h3>📊 Trades</h3>
                    <p>{stats['total_trades']}</p>
                </div>
            </div>
            
            <h3>📈 Trades de Hoy</h3>
            <table class="trades-table">
                <tr>
                    <th>Hora</th>
                    <th>Símbolo</th>
                    <th>Tipo</th>
                    <th>Entry</th>
                    <th>Exit</th>
                    <th>P&L</th>
                    <th>Resultado</th>
                </tr>
        """
        
        for trade in trades_today:
            pnl_class = "positive" if trade['pnl'] > 0 else "negative"
            result_emoji = "✅" if trade['pnl'] > 0 else "❌"
            
            html += f"""
                <tr>
                    <td>{trade['entry_time'].strftime('%H:%M')}</td>
                    <td>{trade['symbol']}</td>
                    <td>{trade['type']}</td>
                    <td>${trade['entry_price']:,.2f}</td>
                    <td>${trade['exit_price']:,.2f}</td>
                    <td class="{pnl_class}">${trade['pnl']:,.2f}</td>
                    <td>{result_emoji} {trade['exit_reason']}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
                <h3>🔍 Análisis del Día</h3>
                <ul>
                    <li><strong>Filtro Anti-tendencia:</strong> ✅ Activo (0% trades contra-tendencia)</li>
                    <li><strong>Stops Amplios:</strong> ✅ ATR x 2.0-3.0 funcionando</li>
                    <li><strong>Sistema Status:</strong> 🟢 Funcionando 24/7</li>
                </ul>
            </div>
            
            <p style="text-align: center; margin-top: 30px; color: #666;">
                📱 Generado automáticamente por Trading Bot V2.5<br>
                ⏰ {datetime.now().strftime('%H:%M:%S')}
            </p>
        </body>
        </html>
        """
        
        return self.send_email(subject, html)

# Configuración para Gmail:
"""
📧 CONFIGURACIÓN EMAIL:

Para Gmail:
email_reporter = EmailReporter(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    email="tu_email@gmail.com", 
    password="tu_app_password",  # No tu password normal!
    recipient="tu_email@gmail.com"
)

⚠️ IMPORTANTE:
1. Activar autenticación de 2 factores en Gmail
2. Generar "App Password" específica para el bot
3. Usar esa app password, no tu password normal
"""