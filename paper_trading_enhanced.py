#!/usr/bin/env python3
"""
Paper Trading System Enhanced - Con datos de Binance
Sistema mejorado de paper trading con integración a Binance
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import uuid
import os

from binance_data_fetcher import BinanceDataFetcher
from error_handler import error_handler, TradingErrorContext
from signal_validator import signal_validator

class PaperTradingEnhanced:
    """
    Sistema mejorado de paper trading con:
    - Integración con Binance
    - Gestión de riesgo avanzada
    - Tracking detallado de performance
    - Sistema de alertas
    """
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.available_capital = initial_capital
        
        # Portfolio state
        self.positions = {}  # {symbol: position_data}
        self.pending_orders = {}  # Órdenes pendientes
        self.trade_history = []
        self.daily_pnl = []
        
        # Risk management
        self.risk_config = {
            'max_position_size_pct': 0.10,    # 10% max por posición
            'max_total_exposure_pct': 0.60,   # 60% max exposición total
            'max_correlation_exposure': 0.30,  # 30% max en activos correlacionados
            'default_stop_loss_pct': 0.03,    # 3% stop loss
            'default_take_profit_pct': 0.09,  # 9% take profit (R:R 1:3)
            'trailing_stop_pct': 0.02,        # 2% trailing stop
            'max_daily_loss_pct': 0.05,       # 5% pérdida máxima diaria
            'commission_pct': 0.0004          # 0.04% comisión Binance
        }
        
        # Performance metrics
        self.reset_performance_metrics()
        
        # Data fetcher
        self.data_fetcher = BinanceDataFetcher()
        
        # Files for persistence
        self.positions_file = "active_trades.json"
        self.history_file = "trade_history.json"
        self.performance_file = "trade_results.csv"
        
        self.load_state()
        
        error_handler.logger.info(f"💼 Paper Trading Enhanced inicializado con ${initial_capital:,.2f}")
    
    def reset_performance_metrics(self):
        """Resetea métricas de performance"""
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_pct': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'total_return': 0.0,
            'total_return_pct': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'avg_trade_duration': 0,
            'total_commission': 0.0
        }
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> Tuple[float, float]:
        """
        Calcula tamaño de posición usando Kelly Criterion modificado
        
        Returns:
            (position_size, capital_to_use)
        """
        with TradingErrorContext("calculate_position_size", symbol):
            # Risk per trade (1-2% del capital)
            risk_per_trade = self.available_capital * 0.015  # 1.5%
            
            # Calcular stop loss en %
            stop_loss_pct = abs(entry_price - stop_loss) / entry_price
            
            # Capital máximo por posición
            max_position_capital = self.available_capital * self.risk_config['max_position_size_pct']
            
            # Capital basado en riesgo
            capital_based_on_risk = risk_per_trade / stop_loss_pct
            
            # Usar el menor entre ambos
            capital_to_use = min(capital_based_on_risk, max_position_capital)
            
            # Calcular cantidad
            position_size = capital_to_use / entry_price
            
            # Verificar límites de Binance
            symbol_info = self.data_fetcher.check_symbol_status(symbol)
            if symbol_info:
                min_qty = symbol_info['min_qty']
                step_size = symbol_info['step_size']
                
                # Redondear al step_size
                position_size = round(position_size / step_size) * step_size
                
                # Verificar mínimo
                if position_size < min_qty:
                    position_size = 0
                    capital_to_use = 0
            
            return position_size, capital_to_use
    
    def open_position(
        self,
        symbol: str,
        side: str,  # 'LONG' o 'SHORT'
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confidence: float = 0.5,
        signal_source: str = "manual"
    ) -> Dict:
        """Abre una nueva posición"""
        
        with TradingErrorContext("open_position", symbol):
            # Validar capital disponible
            if self.available_capital < 100:
                return {
                    'success': False,
                    'error': 'Capital insuficiente',
                    'available': self.available_capital
                }
            
            # Calcular tamaño de posición
            position_size, capital_to_use = self.calculate_position_size(
                symbol, entry_price, stop_loss
            )
            
            if position_size == 0:
                return {
                    'success': False,
                    'error': 'Tamaño de posición muy pequeño'
                }
            
            # Verificar exposición total
            total_exposure = sum(p['capital_used'] for p in self.positions.values())
            if (total_exposure + capital_to_use) > (self.initial_capital * self.risk_config['max_total_exposure_pct']):
                return {
                    'success': False,
                    'error': 'Exposición máxima alcanzada'
                }
            
            # Calcular comisión
            commission = capital_to_use * self.risk_config['commission_pct']
            
            # Crear posición
            position_id = str(uuid.uuid4())[:8]
            position = {
                'id': position_id,
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'current_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'initial_stop_loss': stop_loss,
                'trailing_stop_active': False,
                'position_size': position_size,
                'capital_used': capital_to_use,
                'commission_paid': commission,
                'entry_time': datetime.now().isoformat(),
                'exit_time': None,
                'status': 'OPEN',
                'pnl': 0,
                'pnl_pct': 0,
                'max_profit': 0,
                'max_loss': 0,
                'confidence': confidence,
                'signal_source': signal_source,
                'risk_reward_ratio': abs(take_profit - entry_price) / abs(entry_price - stop_loss)
            }
            
            # Actualizar estado
            self.positions[position_id] = position
            self.available_capital -= (capital_to_use + commission)
            self.performance_metrics['total_commission'] += commission
            
            # Log de trading
            error_handler.log_trading_action(
                "POSITION_OPENED",
                symbol,
                {
                    'position_id': position_id,
                    'side': side,
                    'size': position_size,
                    'capital': capital_to_use,
                    'entry': entry_price,
                    'sl': stop_loss,
                    'tp': take_profit
                }
            )
            
            # Guardar estado
            self.save_state()
            
            return {
                'success': True,
                'position_id': position_id,
                'position': position
            }
    
    def update_positions(self):
        """Actualiza precios y P&L de todas las posiciones"""
        
        for position_id, position in self.positions.items():
            if position['status'] != 'OPEN':
                continue
            
            with TradingErrorContext("update_position", position['symbol']):
                # Obtener precio actual
                ticker = self.data_fetcher.get_ticker_24hr(position['symbol'])
                if not ticker:
                    continue
                
                current_price = ticker['current_price']
                position['current_price'] = current_price
                
                # Calcular P&L
                if position['side'] == 'LONG':
                    pnl_pct = (current_price - position['entry_price']) / position['entry_price']
                else:  # SHORT
                    pnl_pct = (position['entry_price'] - current_price) / position['entry_price']
                
                position['pnl'] = position['capital_used'] * pnl_pct
                position['pnl_pct'] = pnl_pct * 100
                
                # Actualizar max profit/loss
                position['max_profit'] = max(position['max_profit'], position['pnl'])
                position['max_loss'] = min(position['max_loss'], position['pnl'])
                
                # Verificar stop loss
                if position['side'] == 'LONG':
                    if current_price <= position['stop_loss']:
                        self.close_position(position_id, current_price, 'STOP_LOSS')
                    elif current_price >= position['take_profit']:
                        self.close_position(position_id, current_price, 'TAKE_PROFIT')
                else:  # SHORT
                    if current_price >= position['stop_loss']:
                        self.close_position(position_id, current_price, 'STOP_LOSS')
                    elif current_price <= position['take_profit']:
                        self.close_position(position_id, current_price, 'TAKE_PROFIT')
                
                # Trailing stop
                if position['pnl_pct'] > 5 and not position['trailing_stop_active']:
                    position['trailing_stop_active'] = True
                
                if position['trailing_stop_active']:
                    self.update_trailing_stop(position_id, current_price)
    
    def update_trailing_stop(self, position_id: str, current_price: float):
        """Actualiza trailing stop loss"""
        position = self.positions[position_id]
        trailing_pct = self.risk_config['trailing_stop_pct']
        
        if position['side'] == 'LONG':
            new_stop = current_price * (1 - trailing_pct)
            if new_stop > position['stop_loss']:
                position['stop_loss'] = new_stop
        else:  # SHORT
            new_stop = current_price * (1 + trailing_pct)
            if new_stop < position['stop_loss']:
                position['stop_loss'] = new_stop
    
    def close_position(self, position_id: str, exit_price: float, reason: str = "MANUAL"):
        """Cierra una posición"""
        
        if position_id not in self.positions:
            return {'success': False, 'error': 'Posición no encontrada'}
        
        position = self.positions[position_id]
        
        with TradingErrorContext("close_position", position['symbol']):
            # Calcular P&L final
            if position['side'] == 'LONG':
                pnl_pct = (exit_price - position['entry_price']) / position['entry_price']
            else:  # SHORT
                pnl_pct = (position['entry_price'] - exit_price) / position['entry_price']
            
            pnl = position['capital_used'] * pnl_pct
            
            # Comisión de salida
            commission = position['capital_used'] * self.risk_config['commission_pct']
            pnl -= commission
            
            # Actualizar posición
            position['exit_price'] = exit_price
            position['exit_time'] = datetime.now().isoformat()
            position['status'] = 'CLOSED'
            position['pnl'] = pnl
            position['pnl_pct'] = (pnl / position['capital_used']) * 100
            position['exit_reason'] = reason
            position['commission_paid'] += commission
            position['trade_duration'] = (
                datetime.fromisoformat(position['exit_time']) - 
                datetime.fromisoformat(position['entry_time'])
            ).total_seconds() / 3600  # en horas
            
            # Actualizar capital
            self.available_capital += position['capital_used'] + pnl
            self.current_capital = self.available_capital + sum(
                p['capital_used'] for p in self.positions.values() if p['status'] == 'OPEN'
            )
            
            # Actualizar métricas
            self.update_performance_metrics(position)
            
            # Agregar a historial
            self.trade_history.append(position)
            
            # Log
            error_handler.log_trading_action(
                "POSITION_CLOSED",
                position['symbol'],
                {
                    'position_id': position_id,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_pct': position['pnl_pct'],
                    'reason': reason
                }
            )
            
            # Remover de posiciones activas
            del self.positions[position_id]
            
            # Guardar estado
            self.save_state()
            
            return {
                'success': True,
                'pnl': pnl,
                'pnl_pct': position['pnl_pct'],
                'position': position
            }
    
    def update_performance_metrics(self, closed_position: Dict):
        """Actualiza métricas de performance"""
        
        # Contadores básicos
        self.performance_metrics['total_trades'] += 1
        
        if closed_position['pnl'] > 0:
            self.performance_metrics['winning_trades'] += 1
            self.performance_metrics['consecutive_wins'] += 1
            self.performance_metrics['consecutive_losses'] = 0
        else:
            self.performance_metrics['losing_trades'] += 1
            self.performance_metrics['consecutive_losses'] += 1
            self.performance_metrics['consecutive_wins'] = 0
        
        # Max consecutivos
        self.performance_metrics['max_consecutive_wins'] = max(
            self.performance_metrics['max_consecutive_wins'],
            self.performance_metrics['consecutive_wins']
        )
        self.performance_metrics['max_consecutive_losses'] = max(
            self.performance_metrics['max_consecutive_losses'],
            self.performance_metrics['consecutive_losses']
        )
        
        # Win rate
        if self.performance_metrics['total_trades'] > 0:
            self.performance_metrics['win_rate'] = (
                self.performance_metrics['winning_trades'] / 
                self.performance_metrics['total_trades']
            ) * 100
        
        # Promedios
        all_trades = [t for t in self.trade_history if t['status'] == 'CLOSED']
        if all_trades:
            wins = [t['pnl'] for t in all_trades if t['pnl'] > 0]
            losses = [t['pnl'] for t in all_trades if t['pnl'] <= 0]
            
            if wins:
                self.performance_metrics['avg_win'] = np.mean(wins)
                self.performance_metrics['largest_win'] = max(wins)
            
            if losses:
                self.performance_metrics['avg_loss'] = np.mean(losses)
                self.performance_metrics['largest_loss'] = min(losses)
            
            # Profit factor
            if losses and sum(np.abs(losses)) > 0:
                self.performance_metrics['profit_factor'] = sum(wins) / sum(np.abs(losses))
            
            # Duración promedio
            durations = [t.get('trade_duration', 0) for t in all_trades]
            if durations:
                self.performance_metrics['avg_trade_duration'] = np.mean(durations)
        
        # Return total
        self.performance_metrics['total_return'] = self.current_capital - self.initial_capital
        self.performance_metrics['total_return_pct'] = (
            (self.current_capital - self.initial_capital) / self.initial_capital
        ) * 100
        
        # Drawdown
        self.calculate_drawdown()
        
        # Ratios (simplificados)
        self.calculate_risk_ratios()
    
    def calculate_drawdown(self):
        """Calcula el drawdown máximo"""
        if not self.trade_history:
            return
        
        # Construir curva de equity
        equity_curve = [self.initial_capital]
        running_capital = self.initial_capital
        
        for trade in self.trade_history:
            if trade['status'] == 'CLOSED':
                running_capital += trade['pnl']
                equity_curve.append(running_capital)
        
        # Calcular drawdown
        peak = equity_curve[0]
        max_dd = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = peak - value
            if dd > max_dd:
                max_dd = dd
        
        self.performance_metrics['max_drawdown'] = max_dd
        if peak > 0:
            self.performance_metrics['max_drawdown_pct'] = (max_dd / peak) * 100
    
    def calculate_risk_ratios(self):
        """Calcula ratios de riesgo"""
        if len(self.trade_history) < 2:
            return
        
        returns = [t['pnl_pct'] for t in self.trade_history if t['status'] == 'CLOSED']
        
        if not returns:
            return
        
        # Sharpe Ratio simplificado
        if np.std(returns) > 0:
            self.performance_metrics['sharpe_ratio'] = np.mean(returns) / np.std(returns)
        
        # Sortino Ratio (solo considera volatilidad negativa)
        negative_returns = [r for r in returns if r < 0]
        if negative_returns and np.std(negative_returns) > 0:
            self.performance_metrics['sortino_ratio'] = np.mean(returns) / np.std(negative_returns)
        
        # Calmar Ratio
        if self.performance_metrics['max_drawdown_pct'] > 0:
            self.performance_metrics['calmar_ratio'] = (
                self.performance_metrics['total_return_pct'] / 
                self.performance_metrics['max_drawdown_pct']
            )
    
    def get_portfolio_status(self) -> Dict:
        """Obtiene estado actual del portfolio"""
        
        # Actualizar posiciones primero
        self.update_positions()
        
        open_positions = [p for p in self.positions.values() if p['status'] == 'OPEN']
        
        # P&L no realizado
        unrealized_pnl = sum(p['pnl'] for p in open_positions)
        
        # Exposición actual
        current_exposure = sum(p['capital_used'] for p in open_positions)
        exposure_pct = (current_exposure / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        return {
            'current_capital': self.current_capital,
            'available_capital': self.available_capital,
            'initial_capital': self.initial_capital,
            'total_return': self.performance_metrics['total_return'],
            'total_return_pct': self.performance_metrics['total_return_pct'],
            'open_positions': len(open_positions),
            'current_exposure': current_exposure,
            'exposure_pct': exposure_pct,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': self.performance_metrics['total_return'] - unrealized_pnl,
            'performance_metrics': self.performance_metrics,
            'positions': open_positions,
            'last_update': datetime.now().isoformat()
        }
    
    def save_state(self):
        """Guarda el estado actual"""
        try:
            # Guardar posiciones activas
            with open(self.positions_file, 'w') as f:
                json.dump(
                    {pid: pos for pid, pos in self.positions.items() if pos['status'] == 'OPEN'},
                    f, indent=2, default=str
                )
            
            # Guardar historial
            with open(self.history_file, 'w') as f:
                json.dump(self.trade_history[-100:], f, indent=2, default=str)  # Últimos 100 trades
            
            # Guardar performance en CSV
            if self.trade_history:
                df = pd.DataFrame(self.trade_history)
                df.to_csv(self.performance_file, index=False)
        
        except Exception as e:
            error_handler.handle_error(e, context={'operation': 'save_state'})
    
    def load_state(self):
        """Carga el estado guardado"""
        try:
            # Cargar posiciones activas
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r') as f:
                    self.positions = json.load(f)
            
            # Cargar historial
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.trade_history = json.load(f)
            
            # Recalcular capital disponible
            open_positions = [p for p in self.positions.values() if p.get('status') == 'OPEN']
            capital_in_use = sum(p.get('capital_used', 0) for p in open_positions)
            self.available_capital = self.current_capital - capital_in_use
            
            error_handler.logger.info(f"📂 Estado cargado: {len(self.positions)} posiciones activas")
        
        except Exception as e:
            error_handler.handle_error(e, context={'operation': 'load_state'})


if __name__ == "__main__":
    # Test del sistema
    paper_trader = PaperTradingEnhanced(initial_capital=10000)
    
    # Test abrir posición
    result = paper_trader.open_position(
        symbol="SOLUSDT",
        side="LONG",
        entry_price=234.50,
        stop_loss=227.50,
        take_profit=248.50,
        confidence=0.75,
        signal_source="test"
    )
    
    print(f"\n📊 Posición abierta: {json.dumps(result, indent=2, default=str)}")
    
    # Actualizar posiciones
    paper_trader.update_positions()
    
    # Obtener estado
    status = paper_trader.get_portfolio_status()
    print(f"\n💼 Estado del portfolio:")
    print(f"Capital: ${status['current_capital']:,.2f}")
    print(f"Return: {status['total_return_pct']:.2f}%")
    print(f"Posiciones abiertas: {status['open_positions']}")
    print(f"Exposición: {status['exposure_pct']:.2f}%")