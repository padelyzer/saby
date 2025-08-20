#!/usr/bin/env python3
"""
Sistema de Paper Trading Filosófico
Trading simulado en tiempo real con el sistema de consenso filosófico
"""

import json
import sqlite3
import pandas as pd
import numpy as np
# Usar Binance en lugar de Yahoo Finance
from binance_client import binance_client
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
import time
import os
from pathlib import Path

# Importar el sistema filosófico y configuración
from trading_api.philosophical_trading_system import PhilosophicalConsensusSystem
from trading_config import TRADING_SYMBOLS, DEFAULT_CONFIG, RISK_LEVELS
from binance_client import binance_client

@dataclass 
class PaperTrade:
    """Representa un trade en paper trading"""
    id: Optional[int]
    timestamp: datetime
    symbol: str
    action: str  # BUY o SELL
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    position_value: float
    philosophers: List[str]
    confidence: float
    market_regime: str
    status: str  # OPEN, CLOSED_WIN, CLOSED_LOSS, CLOSED_MANUAL
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    exit_reason: Optional[str] = None
    holding_time_hours: Optional[float] = None

class PhilosophicalPaperTrading:
    """Sistema completo de paper trading filosófico"""
    
    def __init__(self, initial_capital: float = 10000, risk_level: str = 'balanced'):
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.risk_level = risk_level
        self.philosophical_system = PhilosophicalConsensusSystem()
        
        # Configuración según nivel de riesgo
        self._configure_risk_parameters()
        self.max_open_trades = 5
        self.scan_interval = 300  # 5 minutos
        
        # Símbolos a monitorear (desde configuración central)
        self.symbols = TRADING_SYMBOLS
        
        # Tracking
        self.open_positions = {}
        self.closed_trades = []
        self.signal_history = []
        self.running = False
        
        print("\n" + "="*70)
        print(" PAPER TRADING FILOSÓFICO INICIALIZADO ".center(70))
        print("="*70)
        print(f"💰 Capital inicial: ${initial_capital:,.2f}")
        print(f"⚠️  Nivel de riesgo: {risk_level.upper()}")
        print(f"📊 Símbolos: {len(self.symbols)}")
        print(f"🎯 Max trades: {self.max_open_trades}")
        print(f"📈 Position size: {self.max_position_size*100}%")
        print(f"📈 Take Profit: {self.take_profit_base*100}%")
        print(f"🔴 Stop Loss: {self.stop_loss_base*100}%")
    
    def _configure_risk_parameters(self):
        """Configura parámetros según nivel de riesgo"""
        
        if self.risk_level == 'conservative':
            self.max_position_size = 0.015  # 1.5% del capital
            self.take_profit_base = 0.025   # 2.5% base
            self.stop_loss_base = 0.015     # 1.5% base
            self.confidence_multiplier = 0.5  # Menos agresivo con confianza
        elif self.risk_level == 'aggressive':
            self.max_position_size = 0.04   # 4% del capital
            self.take_profit_base = 0.08    # 8% base
            self.stop_loss_base = 0.025     # 2.5% base
            self.confidence_multiplier = 1.5  # Más agresivo con confianza
        else:  # balanced
            self.max_position_size = 0.025  # 2.5% del capital
            self.take_profit_base = 0.04    # 4% base
            self.stop_loss_base = 0.02      # 2% base
            self.confidence_multiplier = 1.0  # Normal
    
    def calculate_dynamic_tp_sl(self, signal: Dict) -> Tuple[float, float]:
        """Calcula TP/SL dinámicos basados en la señal y el riesgo"""
        
        confidence = signal.get('confidence', 0.7)
        market_regime = signal.get('market_regime', 'RANGING')
        volatility = signal.get('volatility', 1.0)
        
        # Ajustar por confianza
        confidence_factor = 0.5 + (confidence * 0.5)  # Entre 0.5 y 1.0
        
        # Ajustar por régimen de mercado
        if market_regime == 'TRENDING':
            # En tendencia, ampliar TP y ajustar SL
            tp_multiplier = 1.5
            sl_multiplier = 0.8
        elif market_regime == 'VOLATILE':
            # En volatilidad, ajustar ambos
            tp_multiplier = 1.2
            sl_multiplier = 1.2
        else:  # RANGING
            # En rango, objetivos más conservadores
            tp_multiplier = 0.8
            sl_multiplier = 1.0
        
        # Calcular valores finales
        take_profit = self.take_profit_base * tp_multiplier * confidence_factor
        stop_loss = self.stop_loss_base * sl_multiplier
        
        # Aplicar límites según nivel de riesgo
        if self.risk_level == 'conservative':
            take_profit = min(take_profit, 0.03)  # Máx 3%
            stop_loss = min(stop_loss, 0.015)     # Máx 1.5%
        elif self.risk_level == 'aggressive':
            take_profit = min(take_profit, 0.10)  # Máx 10%
            stop_loss = min(stop_loss, 0.03)      # Máx 3%
        else:  # balanced
            take_profit = min(take_profit, 0.05)  # Máx 5%
            stop_loss = min(stop_loss, 0.02)      # Máx 2%
        
        return take_profit, stop_loss
    
    def calculate_position_size(self, signal: Dict) -> Tuple[float, float]:
        """Calcula el tamaño de posición basado en el capital inicial del día"""
        
        # Usar capital inicial para cálculos (no el balance actual)
        # Esto evita que los trades se reduzcan con pérdidas o aumenten con ganancias
        base_capital = self.initial_capital
        
        # Ajustar por confianza y nivel de riesgo
        base_size = self.max_position_size
        confidence_adjustment = 0.5 + (signal['confidence'] * 0.5)  # Entre 0.5 y 1.0
        adjusted_size = base_size * confidence_adjustment * self.confidence_multiplier
        
        # Calcular valor en dólares basado en capital inicial
        position_value = base_capital * adjusted_size
        
        # Verificar que tengamos suficiente balance disponible
        if position_value > self.current_balance:
            # Si no hay suficiente balance, ajustar al disponible
            position_value = self.current_balance * 0.95  # Dejar 5% de margen
        
        # Calcular cantidad de unidades
        position_size = position_value / signal['entry_price']
        
        return position_size, position_value
    
    def execute_signal(self, signal: Dict) -> bool:
        """Ejecuta una señal de trading"""
        
        # Verificar límites
        if len(self.open_positions) >= self.max_open_trades:
            print(f"⚠️ Límite de trades alcanzado ({self.max_open_trades})")
            return False
        
        # Verificar si ya tenemos posición
        if signal['symbol'] in self.open_positions:
            print(f"⚠️ Ya hay posición en {signal['symbol']}")
            return False
        
        # Calcular TP/SL dinámicos
        tp_percent, sl_percent = self.calculate_dynamic_tp_sl(signal)
        
        # Actualizar señal con TP/SL calculados
        if signal['action'] == 'BUY':
            signal['stop_loss'] = signal['entry_price'] * (1 - sl_percent)
            signal['take_profit'] = signal['entry_price'] * (1 + tp_percent)
        else:  # SELL
            signal['stop_loss'] = signal['entry_price'] * (1 + sl_percent)
            signal['take_profit'] = signal['entry_price'] * (1 - tp_percent)
        
        # Calcular tamaño
        position_size, position_value = self.calculate_position_size(signal)
        
        # Crear trade
        trade = {
            'timestamp': datetime.now(),
            'symbol': signal['symbol'],
            'action': signal['action'],
            'entry_price': signal['entry_price'],
            'current_price': signal['entry_price'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'position_size': position_size,
            'position_value': position_value,
            'philosophers': signal['philosophers_agree'],
            'confidence': signal['confidence'],
            'market_regime': signal['market_regime'],
            'status': 'OPEN',
            'pnl': 0.0,
            'pnl_percent': 0.0
        }
        
        # Guardar posición
        self.open_positions[signal['symbol']] = trade
        
        print(f"\n🎯 TRADE EJECUTADO:")
        print(f"   Símbolo: {signal['symbol']}")
        print(f"   Acción: {signal['action']}")
        print(f"   Precio: ${signal['entry_price']:.4f}")
        print(f"   SL: ${signal['stop_loss']:.4f} ({sl_percent:.1%})")
        print(f"   TP: ${signal['take_profit']:.4f} ({tp_percent:.1%})")
        print(f"   Valor: ${position_value:.2f} ({adjusted_size*100:.1f}% del capital)")
        print(f"   Confianza: {signal['confidence']:.1%}")
        print(f"   Régimen: {signal.get('market_regime', 'UNKNOWN')}")
        print(f"   Filósofos: {', '.join(signal['philosophers_agree'][:3])}")
        
        return True
    
    def update_positions(self):
        """Actualiza todas las posiciones abiertas"""
        
        positions_to_close = []
        
        for symbol, trade in self.open_positions.items():
            try:
                # Obtener precio actual
                ticker = yf.Ticker(symbol)
                current_price = ticker.history(period='1d')['Close'].iloc[-1]
                trade['current_price'] = current_price
                
                # Calcular PnL
                if trade['action'] == 'BUY':
                    pnl_percent = ((current_price - trade['entry_price']) / 
                                 trade['entry_price']) * 100
                    
                    # Check stops
                    if current_price <= trade['stop_loss']:
                        positions_to_close.append((symbol, 'STOP_LOSS'))
                    elif current_price >= trade['take_profit']:
                        positions_to_close.append((symbol, 'TAKE_PROFIT'))
                        
                else:  # SELL
                    pnl_percent = ((trade['entry_price'] - current_price) / 
                                 trade['entry_price']) * 100
                    
                    # Check stops
                    if current_price >= trade['stop_loss']:
                        positions_to_close.append((symbol, 'STOP_LOSS'))
                    elif current_price <= trade['take_profit']:
                        positions_to_close.append((symbol, 'TAKE_PROFIT'))
                
                # Actualizar PnL
                trade['pnl_percent'] = pnl_percent
                trade['pnl'] = trade['position_value'] * (pnl_percent / 100)
                
            except Exception as e:
                print(f"Error actualizando {symbol}: {e}")
        
        # Cerrar posiciones
        for symbol, reason in positions_to_close:
            self.close_position(symbol, reason)
    
    def close_position(self, symbol: str, reason: str):
        """Cierra una posición"""
        
        if symbol not in self.open_positions:
            return
        
        trade = self.open_positions[symbol]
        
        # Marcar como cerrada
        trade['status'] = 'CLOSED_WIN' if trade['pnl'] > 0 else 'CLOSED_LOSS'
        trade['exit_price'] = trade['current_price']
        trade['exit_timestamp'] = datetime.now()
        trade['exit_reason'] = reason
        trade['holding_time_hours'] = (
            (trade['exit_timestamp'] - trade['timestamp']).total_seconds() / 3600
        )
        
        # Actualizar balance
        self.current_balance += trade['pnl']
        
        # Mover a historial
        self.closed_trades.append(trade)
        del self.open_positions[symbol]
        
        # Log
        emoji = "✅" if trade['pnl'] > 0 else "❌"
        print(f"\n{emoji} TRADE CERRADO: {symbol}")
        print(f"   Razón: {reason}")
        print(f"   PnL: ${trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")
        print(f"   Duración: {trade['holding_time_hours']:.1f}h")
    
    def scan_markets(self):
        """Escanea mercados en busca de señales"""
        
        print(f"\n🔍 Escaneando {len(self.symbols)} mercados...")
        
        # Obtener señales del sistema filosófico
        signals = self.philosophical_system.scan_symbols(self.symbols)
        
        if signals:
            print(f"📡 {len(signals)} señales detectadas")
            
            for signal_obj in signals:
                # Convertir a diccionario
                signal = {
                    'symbol': signal_obj.symbol,
                    'action': signal_obj.action,
                    'entry_price': signal_obj.entry_price,
                    'stop_loss': signal_obj.stop_loss,
                    'take_profit': signal_obj.take_profit,
                    'confidence': signal_obj.confidence,
                    'philosophers_agree': signal_obj.philosophers_agree,
                    'market_regime': signal_obj.market_regime,
                    'risk_reward': signal_obj.risk_reward
                }
                
                # Guardar en historial
                self.signal_history.append({
                    'timestamp': datetime.now(),
                    'signal': signal
                })
                
                # Ejecutar
                self.execute_signal(signal)
        else:
            print("❌ Sin señales con consenso")
    
    def get_statistics(self) -> Dict:
        """Calcula estadísticas de trading"""
        
        total_trades = len(self.closed_trades)
        
        if total_trades == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'total_pnl': 0,
                'profit_factor': 0
            }
        
        winning_trades = len([t for t in self.closed_trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        
        total_profit = sum([t['pnl'] for t in self.closed_trades if t['pnl'] > 0])
        total_loss = abs(sum([t['pnl'] for t in self.closed_trades if t['pnl'] < 0]))
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'avg_pnl': sum([t['pnl'] for t in self.closed_trades]) / total_trades,
            'total_pnl': sum([t['pnl'] for t in self.closed_trades]),
            'profit_factor': total_profit / total_loss if total_loss > 0 else 0,
            'avg_holding_time': np.mean([t['holding_time_hours'] for t in self.closed_trades if 'holding_time_hours' in t]) if self.closed_trades else 0
        }
    
    def show_status(self):
        """Muestra el estado actual"""
        
        stats = self.get_statistics()
        open_pnl = sum([t['pnl'] for t in self.open_positions.values()])
        equity = self.current_balance + open_pnl
        
        print("\n" + "="*60)
        print(" ESTADO DEL SISTEMA ".center(60))
        print("="*60)
        
        print(f"\n💰 CAPITAL:")
        print(f"   Balance: ${self.current_balance:,.2f}")
        print(f"   Equity: ${equity:,.2f}")
        print(f"   PnL Total: ${equity - self.initial_capital:,.2f} "
              f"({((equity - self.initial_capital) / self.initial_capital) * 100:.2f}%)")
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Trades totales: {stats['total_trades']}")
        print(f"   Win rate: {stats['win_rate']:.1f}%")
        print(f"   PnL promedio: ${stats['avg_pnl']:.2f}")
        print(f"   Profit factor: {stats['profit_factor']:.2f}")
        
        if self.open_positions:
            print(f"\n🔓 POSICIONES ABIERTAS ({len(self.open_positions)}):")
            for symbol, trade in self.open_positions.items():
                emoji = "🟢" if trade['pnl'] > 0 else "🔴"
                print(f"   {emoji} {symbol}: {trade['action']} @ ${trade['entry_price']:.4f} "
                      f"(PnL: {trade['pnl_percent']:.2f}%)")
    
    def run(self, duration_hours: float = 24):
        """Ejecuta el sistema de paper trading"""
        
        print(f"\n🚀 INICIANDO PAPER TRADING")
        print(f"⏰ Duración: {duration_hours} horas")
        print(f"🔄 Intervalo: {self.scan_interval/60} minutos")
        
        self.running = True
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Para demo, hacer solo un ciclo
        demo_cycles = 3
        
        for cycle in range(demo_cycles):
            if not self.running:
                break
            
            print(f"\n⏰ CICLO {cycle+1}/{demo_cycles} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Escanear mercados
            self.scan_markets()
            
            # Actualizar posiciones
            time.sleep(2)  # Pequeña pausa para demo
            self.update_positions()
            
            # Mostrar estado
            self.show_status()
            
            if cycle < demo_cycles - 1:
                print(f"\n💤 Esperando próximo ciclo...")
                time.sleep(5)  # Pausa corta para demo
        
        # Resumen final
        self.show_final_report()
        
        return True
    
    def show_final_report(self):
        """Muestra reporte final"""
        
        print("\n" + "="*70)
        print(" REPORTE FINAL DE PAPER TRADING ".center(70))
        print("="*70)
        
        stats = self.get_statistics()
        final_equity = self.current_balance + sum([t['pnl'] for t in self.open_positions.values()])
        total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        print(f"\n💰 RESULTADOS FINANCIEROS:")
        print(f"   Capital inicial: ${self.initial_capital:,.2f}")
        print(f"   Capital final: ${final_equity:,.2f}")
        print(f"   Retorno total: {total_return:.2f}%")
        print(f"   PnL total: ${final_equity - self.initial_capital:,.2f}")
        
        print(f"\n📊 MÉTRICAS DE TRADING:")
        print(f"   Total trades: {stats['total_trades']}")
        print(f"   Ganadores: {stats['winning_trades']}")
        print(f"   Perdedores: {stats['losing_trades']}")
        print(f"   Win rate: {stats['win_rate']:.1f}%")
        print(f"   Profit factor: {stats['profit_factor']:.2f}")
        print(f"   Tiempo promedio: {stats['avg_holding_time']:.1f}h")
        
        if self.closed_trades:
            print(f"\n📜 ÚLTIMOS TRADES:")
            for trade in self.closed_trades[-5:]:
                emoji = "✅" if trade['pnl'] > 0 else "❌"
                print(f"   {emoji} {trade['symbol']}: {trade['pnl_percent']:.2f}% en {trade.get('holding_time_hours', 0):.1f}h")
        
        # Análisis por filósofo
        philosopher_stats = {}
        for trade in self.closed_trades:
            for philosopher in trade['philosophers']:
                if philosopher not in philosopher_stats:
                    philosopher_stats[philosopher] = {'trades': 0, 'wins': 0}
                philosopher_stats[philosopher]['trades'] += 1
                if trade['pnl'] > 0:
                    philosopher_stats[philosopher]['wins'] += 1
        
        if philosopher_stats:
            print(f"\n🎓 PERFORMANCE POR FILÓSOFO:")
            sorted_philosophers = sorted(
                philosopher_stats.items(),
                key=lambda x: x[1]['wins'] / x[1]['trades'] if x[1]['trades'] > 0 else 0,
                reverse=True
            )
            for philosopher, stats in sorted_philosophers[:5]:
                win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
                print(f"   {philosopher}: {win_rate:.1f}% win rate ({stats['trades']} trades)")
        
        # Guardar reporte
        report = {
            'timestamp': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'statistics': stats,
            'closed_trades': len(self.closed_trades),
            'open_positions': len(self.open_positions)
        }
        
        filename = f"paper_trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Reporte guardado en {filename}")


def main():
    """Función principal"""
    
    print("\n" + "="*70)
    print(" PAPER TRADING FILOSÓFICO ".center(70))
    print("="*70)
    
    # Crear sistema con nivel de riesgo por defecto
    paper_trader = PhilosophicalPaperTrading(initial_capital=10000, risk_level='balanced')
    
    # Menú
    while True:
        print("\n📋 OPCIONES:")
        print("1. Ejecutar paper trading (demo 3 ciclos)")
        print("2. Ver estado actual")
        print("3. Ver estadísticas")
        print("4. Salir")
        
        choice = input("\nOpción: ")
        
        if choice == '1':
            paper_trader.run(duration_hours=0.1)  # Demo corta
            
        elif choice == '2':
            paper_trader.show_status()
            
        elif choice == '3':
            stats = paper_trader.get_statistics()
            print(f"\n📊 ESTADÍSTICAS:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")
        
        elif choice == '4':
            print("\n👋 Hasta luego!")
            break
        
        else:
            print("❌ Opción inválida")


if __name__ == "__main__":
    main()