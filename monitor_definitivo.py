#!/usr/bin/env python3
"""
Monitor Definitivo en Tiempo Real
Sistema de seguimiento para las señales definitivas
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

class MonitorDefinitivo:
    """
    Monitor en tiempo real para el sistema definitivo
    """
    
    def __init__(self):
        # Configuración del monitor
        self.trailing_activation = 0.010  # 1.0%
        self.trailing_distance = 0.005   # 0.5%
        self.partial_close_pct = 0.40    # 40%
        
        # Trades activos (ejemplo con la señal generada)
        self.active_trades = [
            {
                'id': 1,
                'ticker': 'DOGE-USD',
                'type': 'SHORT',
                'entry_price': 0.2295,
                'stop_loss': 0.2334,
                'partial_target': 0.2238,
                'main_target': 0.2180,
                'position_size': 0.05,
                'entry_time': datetime.now(),
                'trailing_stop': None,
                'partial_closed': False,
                'status': 'ACTIVE'
            }
        ]
        
        self.completed_trades = []
        
    def get_current_price(self, ticker):
        """Obtiene precio actual"""
        try:
            data = yf.Ticker(ticker)
            hist = data.history(period="1d", interval="1m")
            if len(hist) > 0:
                return hist['Close'].iloc[-1]
        except:
            pass
        return None
    
    def update_trailing_stop(self, trade, current_price):
        """Actualiza trailing stop"""
        
        if trade['type'] == 'SHORT':
            # Calcular profit actual
            profit_pct = (trade['entry_price'] - current_price) / trade['entry_price']
            
            if profit_pct >= self.trailing_activation:
                # Calcular nuevo trailing stop
                new_trailing = current_price * (1 + self.trailing_distance)
                
                # Actualizar si es mejor
                if trade['trailing_stop'] is None or new_trailing < trade['trailing_stop']:
                    old_trailing = trade['trailing_stop']
                    trade['trailing_stop'] = new_trailing
                    
                    print(f"   📈 Trailing actualizado: ${old_trailing:.4f} → ${new_trailing:.4f}")
                    return True
        
        else:  # LONG
            profit_pct = (current_price - trade['entry_price']) / trade['entry_price']
            
            if profit_pct >= self.trailing_activation:
                new_trailing = current_price * (1 - self.trailing_distance)
                
                if trade['trailing_stop'] is None or new_trailing > trade['trailing_stop']:
                    old_trailing = trade['trailing_stop']
                    trade['trailing_stop'] = new_trailing
                    
                    print(f"   📈 Trailing actualizado: ${old_trailing:.4f} → ${new_trailing:.4f}")
                    return True
        
        return False
    
    def check_exit_conditions(self, trade, current_price):
        """Verifica condiciones de salida"""
        
        exit_price = None
        exit_reason = None
        
        if trade['type'] == 'SHORT':
            # Verificar partial target
            if not trade['partial_closed'] and current_price <= trade['partial_target']:
                # Cerrar 40%
                trade['partial_closed'] = True
                partial_profit = ((trade['entry_price'] - trade['partial_target']) / trade['entry_price']) * self.partial_close_pct
                
                print(f"   💰 CIERRE PARCIAL (40%): ${trade['partial_target']:.4f}")
                print(f"   ✅ Profit parcial: {partial_profit*100:+.2f}%")
                return None, 'PARTIAL_CLOSE'
            
            # Verificar main target
            elif current_price <= trade['main_target']:
                exit_price = trade['main_target']
                exit_reason = 'TP'
            
            # Verificar stop loss
            elif current_price >= trade['stop_loss']:
                exit_price = trade['stop_loss']
                exit_reason = 'SL'
            
            # Verificar trailing stop
            elif trade['trailing_stop'] and current_price >= trade['trailing_stop']:
                exit_price = trade['trailing_stop']
                exit_reason = 'TRAIL'
        
        else:  # LONG
            if not trade['partial_closed'] and current_price >= trade['partial_target']:
                trade['partial_closed'] = True
                partial_profit = ((trade['partial_target'] - trade['entry_price']) / trade['entry_price']) * self.partial_close_pct
                
                print(f"   💰 CIERRE PARCIAL (40%): ${trade['partial_target']:.4f}")
                print(f"   ✅ Profit parcial: {partial_profit*100:+.2f}%")
                return None, 'PARTIAL_CLOSE'
            
            elif current_price >= trade['main_target']:
                exit_price = trade['main_target']
                exit_reason = 'TP'
            
            elif current_price <= trade['stop_loss']:
                exit_price = trade['stop_loss']
                exit_reason = 'SL'
            
            elif trade['trailing_stop'] and current_price <= trade['trailing_stop']:
                exit_price = trade['trailing_stop']
                exit_reason = 'TRAIL'
        
        return exit_price, exit_reason
    
    def close_trade(self, trade, exit_price, exit_reason):
        """Cierra un trade"""
        
        # Calcular profit total
        remaining_size = 1 - self.partial_close_pct if trade['partial_closed'] else 1.0
        
        if trade['type'] == 'SHORT':
            profit_pct = ((trade['entry_price'] - exit_price) / trade['entry_price']) * remaining_size
        else:
            profit_pct = ((exit_price - trade['entry_price']) / trade['entry_price']) * remaining_size
        
        # Si hubo cierre parcial, sumar profit parcial
        if trade['partial_closed']:
            if trade['type'] == 'SHORT':
                partial_profit = ((trade['entry_price'] - trade['partial_target']) / trade['entry_price']) * self.partial_close_pct
            else:
                partial_profit = ((trade['partial_target'] - trade['entry_price']) / trade['entry_price']) * self.partial_close_pct
            
            profit_pct += partial_profit
        
        # Actualizar trade
        trade.update({
            'exit_price': exit_price,
            'exit_time': datetime.now(),
            'exit_reason': exit_reason,
            'total_profit_pct': profit_pct * 100,
            'status': 'CLOSED'
        })
        
        # Mover a completados
        self.active_trades.remove(trade)
        self.completed_trades.append(trade)
        
        # Mostrar resultado
        emoji = "🟢" if profit_pct > 0 else "🔴"
        print(f"\n{emoji} TRADE CERRADO: {trade['ticker']} {trade['type']}")
        print(f"   Exit: {exit_reason} @ ${exit_price:.4f}")
        print(f"   Profit Total: {profit_pct*100:+.2f}%")
        print(f"   Duración: {trade['exit_time'] - trade['entry_time']}")
        
        return trade
    
    def monitor_cycle(self):
        """Ejecuta un ciclo de monitoreo"""
        
        print(f"\n{'='*60}")
        print(f"🔍 MONITOR DEFINITIVO - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        if not self.active_trades:
            print("💤 No hay trades activos para monitorear")
            return
        
        for trade in self.active_trades[:]:  # Copia para modificar durante iteración
            ticker = trade['ticker']
            current_price = self.get_current_price(ticker)
            
            if current_price is None:
                print(f"❌ {ticker}: Error obteniendo precio")
                continue
            
            # Calcular profit actual
            if trade['type'] == 'SHORT':
                current_profit_pct = (trade['entry_price'] - current_price) / trade['entry_price']
            else:
                current_profit_pct = (current_price - trade['entry_price']) / trade['entry_price']
            
            # Mostrar estado
            emoji = "🟢" if current_profit_pct > 0 else "🔴"
            trailing_status = f"${trade['trailing_stop']:.4f}" if trade['trailing_stop'] else "No activo"
            partial_status = "SÍ" if trade['partial_closed'] else "No"
            
            print(f"\n{emoji} {ticker} {trade['type']} (ID: {trade['id']})")
            print(f"   💰 Precio actual: ${current_price:.4f}")
            print(f"   📊 Entry: ${trade['entry_price']:.4f}")
            print(f"   🛑 Stop: ${trade['stop_loss']:.4f}")
            print(f"   🎯 Targets: ${trade['partial_target']:.4f} | ${trade['main_target']:.4f}")
            print(f"   📈 Trailing: {trailing_status}")
            print(f"   💰 Parcial cerrado: {partial_status}")
            print(f"   📊 P&L actual: {current_profit_pct*100:+.2f}%")
            
            # Actualizar trailing stop
            self.update_trailing_stop(trade, current_price)
            
            # Verificar condiciones de salida
            exit_price, exit_reason = self.check_exit_conditions(trade, current_price)
            
            if exit_reason == 'PARTIAL_CLOSE':
                continue  # Ya se procesó el cierre parcial
            elif exit_price:
                self.close_trade(trade, exit_price, exit_reason)
        
        # Resumen
        print(f"\n📊 RESUMEN:")
        print(f"   Trades activos: {len(self.active_trades)}")
        print(f"   Trades completados: {len(self.completed_trades)}")
        
        if self.completed_trades:
            total_profit = sum(t['total_profit_pct'] for t in self.completed_trades)
            avg_profit = total_profit / len(self.completed_trades)
            winning_trades = len([t for t in self.completed_trades if t['total_profit_pct'] > 0])
            win_rate = (winning_trades / len(self.completed_trades)) * 100
            
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   Profit promedio: {avg_profit:+.2f}%")
            print(f"   Profit total: {total_profit:+.2f}%")
    
    def run_monitor(self, cycles=10, interval=30):
        """Ejecuta el monitor por varios ciclos"""
        
        print("""
╔════════════════════════════════════════════════════════════════════════╗
║                        MONITOR DEFINITIVO                              ║
║                    Seguimiento en Tiempo Real                         ║
╚════════════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"🔄 Iniciando monitor por {cycles} ciclos (cada {interval} segundos)")
        
        for cycle in range(cycles):
            print(f"\n--- CICLO {cycle + 1}/{cycles} ---")
            
            try:
                self.monitor_cycle()
                
                if cycle < cycles - 1:  # No esperar en el último ciclo
                    print(f"\n⏰ Esperando {interval} segundos...")
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                print("\n🛑 Monitor detenido por usuario")
                break
            except Exception as e:
                print(f"❌ Error en ciclo {cycle + 1}: {e}")
        
        # Resumen final
        print(f"\n{'='*60}")
        print("📊 RESUMEN FINAL DEL MONITOR")
        print(f"{'='*60}")
        
        if self.completed_trades:
            for trade in self.completed_trades:
                emoji = "🟢" if trade['total_profit_pct'] > 0 else "🔴"
                print(f"{emoji} {trade['ticker']} {trade['type']}: {trade['total_profit_pct']:+.2f}% ({trade['exit_reason']})")
        
        if self.active_trades:
            print(f"\n⚠️ {len(self.active_trades)} trades aún activos:")
            for trade in self.active_trades:
                print(f"   • {trade['ticker']} {trade['type']} (desde {trade['entry_time'].strftime('%H:%M')})")

def main():
    """Función principal"""
    monitor = MonitorDefinitivo()
    
    # Ejecutar monitor (10 ciclos de 30 segundos = 5 minutos)
    monitor.run_monitor(cycles=10, interval=30)

if __name__ == "__main__":
    main()