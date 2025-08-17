#!/usr/bin/env python3
"""
Sistema de Tracking Automático de Trades
Registra todas las señales y su resultado final (TP/SL/Manual)
"""

import json
import os
import csv
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional
import time
import threading

class TradeTracker:
    """Sistema completo de tracking de trades"""
    
    def __init__(self):
        self.trades_file = 'trade_history.json'
        self.csv_file = 'trade_results.csv'
        self.active_trades_file = 'active_trades.json'
        
        # Cargar trades activos
        self.active_trades = self.load_active_trades()
        
        # Crear archivos si no existen
        self._initialize_files()
        
        # Thread para monitoreo automático
        self.monitoring = False
        self.monitor_thread = None
    
    def _initialize_files(self):
        """Inicializa los archivos de tracking"""
        # JSON para historial completo
        if not os.path.exists(self.trades_file):
            with open(self.trades_file, 'w') as f:
                json.dump([], f)
        
        # CSV para análisis rápido
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'ID', 'Timestamp_Open', 'Timestamp_Close', 'Ticker', 'Direction',
                    'Entry_Price', 'Exit_Price', 'Stop_Loss', 'Take_Profit',
                    'Score', 'Result', 'PnL_Percent', 'PnL_USD', 'Duration_Hours',
                    'Max_Favorable', 'Max_Adverse', 'Leverage', 'Position_Size'
                ])
    
    def load_active_trades(self) -> Dict:
        """Carga los trades activos"""
        if os.path.exists(self.active_trades_file):
            with open(self.active_trades_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_active_trades(self):
        """Guarda los trades activos"""
        with open(self.active_trades_file, 'w') as f:
            json.dump(self.active_trades, f, indent=2)
    
    def open_trade(self, signal: dict) -> str:
        """Registra un nuevo trade basado en una señal"""
        trade_id = f"{signal['ticker']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        trade = {
            'id': trade_id,
            'timestamp_open': datetime.now().isoformat(),
            'timestamp_close': None,
            'ticker': signal['ticker'],
            'direction': signal['direccion'],
            'entry_price': signal['price'],
            'exit_price': None,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'score': signal['score'],
            'leverage': signal.get('leverage', 3),
            'position_size_pct': signal.get('position_size_pct', 5),
            'result': 'ACTIVE',
            'pnl_percent': 0,
            'pnl_usd': 0,
            'duration_hours': 0,
            'max_favorable': 0,  # Máximo profit durante el trade
            'max_adverse': 0,     # Máximo drawdown durante el trade
            'price_history': [],  # Historial de precios
            'notes': signal.get('notes', '')
        }
        
        # Guardar en trades activos
        self.active_trades[trade_id] = trade
        self.save_active_trades()
        
        # Log
        print(f"📊 Trade abierto: {trade_id}")
        print(f"   {signal['direccion']} {signal['ticker']} @ ${signal['price']:.2f}")
        print(f"   SL: ${signal['stop_loss']:.2f} | TP: ${signal['take_profit']:.2f}")
        
        return trade_id
    
    def update_trade_price(self, trade_id: str, current_price: float):
        """Actualiza el precio actual y estadísticas del trade"""
        if trade_id not in self.active_trades:
            return
        
        trade = self.active_trades[trade_id]
        entry_price = trade['entry_price']
        
        # Calcular PnL actual
        if trade['direction'] == 'LONG':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Actualizar estadísticas
        trade['current_price'] = current_price
        trade['pnl_percent'] = pnl_pct
        trade['price_history'].append({
            'timestamp': datetime.now().isoformat(),
            'price': current_price,
            'pnl': pnl_pct
        })
        
        # Actualizar máximos
        if pnl_pct > trade['max_favorable']:
            trade['max_favorable'] = pnl_pct
        if pnl_pct < trade['max_adverse']:
            trade['max_adverse'] = pnl_pct
        
        # Verificar si hit SL o TP
        if trade['direction'] == 'LONG':
            if current_price >= trade['take_profit']:
                self.close_trade(trade_id, trade['take_profit'], 'TAKE_PROFIT')
            elif current_price <= trade['stop_loss']:
                self.close_trade(trade_id, trade['stop_loss'], 'STOP_LOSS')
        else:  # SHORT
            if current_price <= trade['take_profit']:
                self.close_trade(trade_id, trade['take_profit'], 'TAKE_PROFIT')
            elif current_price >= trade['stop_loss']:
                self.close_trade(trade_id, trade['stop_loss'], 'STOP_LOSS')
        
        self.save_active_trades()
    
    def close_trade(self, trade_id: str, exit_price: float, result: str = 'MANUAL'):
        """Cierra un trade y calcula resultados finales"""
        if trade_id not in self.active_trades:
            print(f"❌ Trade {trade_id} no encontrado")
            return
        
        trade = self.active_trades[trade_id]
        
        # Calcular resultados finales
        trade['timestamp_close'] = datetime.now().isoformat()
        trade['exit_price'] = exit_price
        trade['result'] = result
        
        # Calcular PnL final
        if trade['direction'] == 'LONG':
            pnl_pct = ((exit_price - trade['entry_price']) / trade['entry_price']) * 100
        else:  # SHORT
            pnl_pct = ((trade['entry_price'] - exit_price) / trade['entry_price']) * 100
        
        # Con apalancamiento
        pnl_pct_leveraged = pnl_pct * trade['leverage']
        
        trade['pnl_percent'] = pnl_pct_leveraged
        trade['pnl_usd'] = 1000 * (pnl_pct_leveraged / 100)  # Asumiendo $1000 base
        
        # Calcular duración
        open_time = datetime.fromisoformat(trade['timestamp_open'])
        close_time = datetime.fromisoformat(trade['timestamp_close'])
        duration = (close_time - open_time).total_seconds() / 3600
        trade['duration_hours'] = round(duration, 2)
        
        # Guardar en historial
        self._save_to_history(trade)
        
        # Guardar en CSV
        self._save_to_csv(trade)
        
        # Remover de trades activos
        del self.active_trades[trade_id]
        self.save_active_trades()
        
        # Log resultado
        emoji = "✅" if pnl_pct_leveraged > 0 else "❌"
        print(f"{emoji} Trade cerrado: {trade_id}")
        print(f"   Resultado: {result}")
        print(f"   PnL: {pnl_pct_leveraged:+.2f}% (${trade['pnl_usd']:+.2f})")
        print(f"   Duración: {duration:.1f} horas")
        
        return trade
    
    def _save_to_history(self, trade: dict):
        """Guarda el trade en el historial JSON"""
        with open(self.trades_file, 'r') as f:
            history = json.load(f)
        
        history.append(trade)
        
        with open(self.trades_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _save_to_csv(self, trade: dict):
        """Guarda el trade en CSV para análisis"""
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                trade['id'],
                trade['timestamp_open'],
                trade['timestamp_close'],
                trade['ticker'],
                trade['direction'],
                trade['entry_price'],
                trade['exit_price'],
                trade['stop_loss'],
                trade['take_profit'],
                trade['score'],
                trade['result'],
                f"{trade['pnl_percent']:.2f}",
                f"{trade['pnl_usd']:.2f}",
                trade['duration_hours'],
                f"{trade['max_favorable']:.2f}",
                f"{trade['max_adverse']:.2f}",
                trade['leverage'],
                trade['position_size_pct']
            ])
    
    def monitor_active_trades(self):
        """Monitorea los trades activos y actualiza precios"""
        print("🔍 Iniciando monitoreo de trades activos...")
        
        while self.monitoring:
            if self.active_trades:
                for trade_id, trade in list(self.active_trades.items()):
                    try:
                        # Obtener precio actual
                        ticker = yf.Ticker(trade['ticker'])
                        data = ticker.history(period='1d', interval='1m')
                        
                        if not data.empty:
                            current_price = float(data['Close'].iloc[-1])
                            self.update_trade_price(trade_id, current_price)
                            
                            # Log
                            pnl = trade.get('pnl_percent', 0)
                            emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                            print(f"{emoji} {trade['ticker']}: ${current_price:.2f} ({pnl:+.2f}%)")
                    
                    except Exception as e:
                        print(f"Error monitoreando {trade_id}: {e}")
            
            # Esperar antes del siguiente check
            time.sleep(60)  # Check cada minuto
    
    def start_monitoring(self):
        """Inicia el monitoreo automático en background"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_active_trades)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print("✅ Monitoreo automático iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo automático"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("🛑 Monitoreo detenido")
    
    def get_statistics(self) -> dict:
        """Calcula estadísticas de trading"""
        if not os.path.exists(self.csv_file):
            return {}
        
        df = pd.read_csv(self.csv_file)
        
        if df.empty:
            return {}
        
        # Filtrar trades cerrados
        closed_trades = df[df['Result'].notna()]
        
        if closed_trades.empty:
            return {}
        
        stats = {
            'total_trades': len(closed_trades),
            'active_trades': len(self.active_trades),
            'winning_trades': len(closed_trades[closed_trades['PnL_Percent'] > 0]),
            'losing_trades': len(closed_trades[closed_trades['PnL_Percent'] < 0]),
            'win_rate': (len(closed_trades[closed_trades['PnL_Percent'] > 0]) / len(closed_trades) * 100),
            'avg_win': closed_trades[closed_trades['PnL_Percent'] > 0]['PnL_Percent'].mean(),
            'avg_loss': closed_trades[closed_trades['PnL_Percent'] < 0]['PnL_Percent'].mean(),
            'total_pnl': closed_trades['PnL_USD'].sum(),
            'avg_duration': closed_trades['Duration_Hours'].mean(),
            'best_trade': closed_trades['PnL_Percent'].max(),
            'worst_trade': closed_trades['PnL_Percent'].min(),
            'profit_factor': abs(
                closed_trades[closed_trades['PnL_Percent'] > 0]['PnL_Percent'].sum() /
                closed_trades[closed_trades['PnL_Percent'] < 0]['PnL_Percent'].sum()
            ) if len(closed_trades[closed_trades['PnL_Percent'] < 0]) > 0 else float('inf')
        }
        
        return stats
    
    def print_report(self):
        """Imprime un reporte de performance"""
        stats = self.get_statistics()
        
        if not stats:
            print("📊 No hay trades para reportar")
            return
        
        print("""
╔════════════════════════════════════════════════════════════════╗
║                     📊 REPORTE DE TRADING                       ║
╚════════════════════════════════════════════════════════════════╝
""")
        
        print(f"📈 Trades Totales: {stats.get('total_trades', 0)}")
        print(f"🔄 Trades Activos: {stats.get('active_trades', 0)}")
        print(f"✅ Ganadores: {stats.get('winning_trades', 0)}")
        print(f"❌ Perdedores: {stats.get('losing_trades', 0)}")
        print(f"🎯 Win Rate: {stats.get('win_rate', 0):.1f}%")
        print(f"💰 PnL Total: ${stats.get('total_pnl', 0):.2f}")
        print(f"📊 Profit Factor: {stats.get('profit_factor', 0):.2f}")
        print(f"⏱️ Duración Promedio: {stats.get('avg_duration', 0):.1f} horas")
        print(f"🚀 Mejor Trade: {stats.get('best_trade', 0):.2f}%")
        print(f"💥 Peor Trade: {stats.get('worst_trade', 0):.2f}%")
        
        # Trades activos
        if self.active_trades:
            print("\n🔴 TRADES ACTIVOS:")
            for trade_id, trade in self.active_trades.items():
                pnl = trade.get('pnl_percent', 0)
                emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                print(f"   {emoji} {trade['ticker']} ({trade['direction']}): {pnl:+.2f}%")

# Funciones de utilidad
def test_system():
    """Prueba el sistema con un trade de ejemplo"""
    tracker = TradeTracker()
    
    # Simular señal
    signal = {
        'ticker': 'BTC-USD',
        'direccion': 'LONG',
        'price': 43250.50,
        'stop_loss': 42385.49,
        'take_profit': 45412.53,
        'score': 7.5,
        'leverage': 3,
        'position_size_pct': 5
    }
    
    # Abrir trade
    trade_id = tracker.open_trade(signal)
    
    # Simular actualizaciones de precio
    prices = [43300, 43400, 43500, 43600, 43700, 45500]  # Hit TP
    
    for price in prices:
        print(f"\n📈 Precio actual: ${price}")
        tracker.update_trade_price(trade_id, price)
        time.sleep(1)
    
    # Mostrar reporte
    tracker.print_report()

if __name__ == "__main__":
    # Test del sistema
    print("🧪 Probando Trade Tracker...")
    test_system()