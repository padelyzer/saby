#!/usr/bin/env python3
"""
Paper Trading System
Sistema de trading en papel para validar estrategias sin riesgo real
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, List, Optional
import uuid

class PaperTradingSystem:
    """
    Sistema completo de paper trading con:
    1. Gestión de posiciones virtuales
    2. Cálculo de P&L en tiempo real
    3. Análisis de performance
    4. Logging detallado de trades
    5. Interfaz de monitoreo
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.available_capital = initial_capital
        
        # Estado del portfolio
        self.positions = {}  # {symbol: position_data}
        self.trade_history = []
        self.daily_pnl = []
        
        # Configuración de trading
        self.trading_config = {
            'max_position_size': 0.10,  # 10% máximo por posición
            'max_total_exposure': 0.80,  # 80% máximo total
            'stop_loss_pct': 0.05,      # 5% stop loss default
            'take_profit_pct': 0.15,    # 15% take profit default
            'max_leverage': 5,          # Leverage máximo
            'commission_pct': 0.001     # 0.1% comisión
        }
        
        # Performance tracking
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'total_return': 0.0
        }
        
        # Sistema integrado (importar scoring y optimizadores)
        self._initialize_trading_systems()
        
        print(f"🎯 Paper Trading System inicializado")
        print(f"💰 Capital inicial: ${self.initial_capital:,}")
    
    def _initialize_trading_systems(self):
        """Inicializa los sistemas de trading integrados"""
        
        try:
            from sistema_adaptativo_completo import SistemaAdaptativoCompleto
            from onchain_analysis import OnChainAnalyzer
            from macro_correlations import MacroCorrelationAnalyzer
            from entry_signals_optimizer import EntrySignalsOptimizer
            
            self.adaptive_system = SistemaAdaptativoCompleto()
            self.onchain_analyzer = OnChainAnalyzer()
            self.macro_analyzer = MacroCorrelationAnalyzer()
            self.entry_optimizer = EntrySignalsOptimizer()
            
            print("✅ Sistemas de trading integrados")
            
        except ImportError as e:
            print(f"⚠️ Algunos sistemas no disponibles: {e}")
            self.adaptive_system = None
            self.onchain_analyzer = None
            self.macro_analyzer = None
            self.entry_optimizer = None
    
    def analyze_signal(self, symbol, timeframe='1h'):
        """Analiza señal de trading usando todos los sistemas"""
        
        try:
            # Obtener datos
            data = self._fetch_market_data(symbol, timeframe)
            if data is None or len(data) < 50:
                return None, "Datos insuficientes"
            
            current = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Determinar señal base
            base_signal = self._generate_base_signal(data, current, prev)
            if base_signal['type'] is None:
                return None, "Sin señal base"
            
            # Aplicar sistema adaptativo
            if self.adaptive_system:
                adaptive_score, adaptive_details = self.adaptive_system.calculate_adaptive_score(
                    data, current, prev, symbol.replace('-USD', ''), base_signal['type']
                )
            else:
                adaptive_score = base_signal['score']
                adaptive_details = {}
            
            # Aplicar optimizador de entrada
            if self.entry_optimizer:
                decision, optimized_score, optimization_details = self.entry_optimizer.optimize_entry_signal(
                    data, current, prev, base_signal['type'], adaptive_score
                )
            else:
                decision = base_signal['type']
                optimized_score = adaptive_score
                optimization_details = {}
            
            # Aplicar análisis on-chain
            onchain_adjustment = 1.0
            if self.onchain_analyzer:
                adjusted_score_onchain, onchain_details = self.onchain_analyzer.get_trading_signal_adjustment(
                    symbol.replace('-USD', ''), optimized_score
                )
                onchain_adjustment = onchain_details['adjustment_factor']
            
            # Aplicar análisis macro
            macro_adjustment = 1.0
            if self.macro_analyzer:
                adjusted_score_macro, macro_details = self.macro_analyzer.get_trading_adjustment(
                    optimized_score, symbol
                )
                macro_adjustment = macro_details['adjustment_factor']
            
            # Score final
            final_score = optimized_score * onchain_adjustment * macro_adjustment
            
            # Threshold adaptativo
            if self.adaptive_system:
                threshold = self.adaptive_system.get_adaptive_threshold(symbol.replace('-USD', ''))
            else:
                threshold = 6.0
            
            # Validar señal final
            if decision == 'REJECTED' or final_score < threshold:
                return None, f"Señal rechazada (Score: {final_score:.2f} < {threshold:.2f})"
            
            # Construir señal completa
            signal = {
                'symbol': symbol,
                'type': base_signal['type'],
                'decision': decision,
                'entry_price': float(current['Close']),
                'base_score': base_signal['score'],
                'adaptive_score': adaptive_score,
                'optimized_score': optimized_score,
                'final_score': final_score,
                'threshold': threshold,
                'onchain_adjustment': onchain_adjustment,
                'macro_adjustment': macro_adjustment,
                'timestamp': datetime.now(),
                'details': {
                    'adaptive': adaptive_details,
                    'optimization': optimization_details,
                    'onchain': onchain_details if 'onchain_details' in locals() else {},
                    'macro': macro_details if 'macro_details' in locals() else {}
                }
            }
            
            return signal, "Señal válida"
            
        except Exception as e:
            return None, f"Error analizando señal: {e}"
    
    def _fetch_market_data(self, symbol, timeframe='1h', periods=100):
        """Obtiene datos de mercado"""
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="30d", interval=timeframe)
            
            if len(data) == 0:
                return None
            
            # Añadir indicadores básicos
            data = self._add_technical_indicators(data)
            
            return data.tail(periods)
            
        except Exception as e:
            print(f"⚠️ Error obteniendo datos para {symbol}: {e}")
            return None
    
    def _add_technical_indicators(self, data):
        """Añade indicadores técnicos básicos"""
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = data['Close'].ewm(span=12).mean()
        exp2 = data['Close'].ewm(span=26).mean()
        data['MACD'] = exp1 - exp2
        data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        
        # ATR
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        data['ATR'] = true_range.rolling(14).mean()
        
        # Volume indicators
        data['Volume_MA'] = data['Volume'].rolling(20).mean()
        data['Volume_Ratio'] = data['Volume'] / data['Volume_MA'].replace(0, 1)
        data['Volume_Ratio'] = data['Volume_Ratio'].fillna(1.0).clip(lower=0.1)
        
        return data
    
    def _generate_base_signal(self, data, current, prev):
        """Genera señal base usando lógica simplificada"""
        
        rsi = current['RSI']
        macd = current['MACD']
        macd_signal = current['MACD_Signal']
        price_change = (current['Close'] - prev['Close']) / prev['Close']
        
        signal_score = 5.0  # Score base
        signal_type = None
        
        # Lógica LONG
        if (rsi < 40 and 
            macd > macd_signal and 
            price_change > 0.01):
            signal_type = 'LONG'
            signal_score = 6.5 + (40 - rsi) * 0.05  # Bonus por RSI bajo
        
        # Lógica SHORT
        elif (rsi > 60 and 
              macd < macd_signal and 
              price_change < -0.01):
            signal_type = 'SHORT'
            signal_score = 6.5 + (rsi - 60) * 0.05  # Bonus por RSI alto
        
        return {
            'type': signal_type,
            'score': signal_score,
            'rsi': rsi,
            'macd_cross': macd > macd_signal,
            'price_change': price_change
        }
    
    def place_order(self, signal, position_size_pct=None, leverage=1):
        """Coloca orden de trading"""
        
        if signal is None:
            return False, "Señal inválida"
        
        symbol = signal['symbol']
        
        # Verificar si ya tenemos posición en este símbolo
        if symbol in self.positions:
            return False, f"Ya existe posición en {symbol}"
        
        # Calcular position size
        if position_size_pct is None:
            if self.adaptive_system:
                leverage = self.adaptive_system.get_adaptive_leverage(signal['final_score'], symbol.replace('-USD', ''))
                position_size_pct = min(0.02 * leverage, self.trading_config['max_position_size'])
            else:
                position_size_pct = 0.02  # 2% default
        
        # Capital para esta posición
        position_capital = self.available_capital * position_size_pct * leverage
        
        # Verificar límites
        if position_capital > self.available_capital * self.trading_config['max_position_size'] * self.trading_config['max_leverage']:
            return False, "Excede límite de position size"
        
        # Calcular cantidad
        entry_price = signal['entry_price']
        commission = position_capital * self.trading_config['commission_pct']
        net_capital = position_capital - commission
        quantity = net_capital / entry_price
        
        # Calcular stops
        if signal['type'] == 'LONG':
            stop_loss = entry_price * (1 - self.trading_config['stop_loss_pct'])
            take_profit = entry_price * (1 + self.trading_config['take_profit_pct'])
        else:  # SHORT
            stop_loss = entry_price * (1 + self.trading_config['stop_loss_pct'])
            take_profit = entry_price * (1 - self.trading_config['take_profit_pct'])
        
        # Crear posición
        position_id = str(uuid.uuid4())[:8]
        position = {
            'id': position_id,
            'symbol': symbol,
            'type': signal['type'],
            'quantity': quantity,
            'entry_price': entry_price,
            'entry_time': datetime.now(),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'leverage': leverage,
            'position_size_pct': position_size_pct,
            'capital_used': position_capital,
            'commission_paid': commission,
            'signal_score': signal['final_score'],
            'signal_details': signal,
            'status': 'OPEN',
            'current_price': entry_price,
            'unrealized_pnl': 0.0,
            'unrealized_pnl_pct': 0.0
        }
        
        # Guardar posición
        self.positions[symbol] = position
        self.available_capital -= position_capital
        
        # Log
        print(f"📊 NUEVA POSICIÓN: {signal['type']} {symbol}")
        print(f"   • Entry: ${entry_price:.2f}")
        print(f"   • Cantidad: {quantity:.6f}")
        print(f"   • Capital: ${position_capital:.2f}")
        print(f"   • Leverage: {leverage}x")
        print(f"   • Score: {signal['final_score']:.2f}")
        print(f"   • Stop Loss: ${stop_loss:.2f}")
        print(f"   • Take Profit: ${take_profit:.2f}")
        
        return True, f"Posición abierta: {position_id}"
    
    def update_positions(self):
        """Actualiza todas las posiciones abiertas"""
        
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            if position['status'] != 'OPEN':
                continue
            
            # Obtener precio actual
            current_price = self._get_current_price(symbol)
            if current_price is None:
                continue
            
            # Actualizar posición
            position['current_price'] = current_price
            
            # Calcular P&L
            if position['type'] == 'LONG':
                pnl = (current_price - position['entry_price']) * position['quantity']
                pnl_pct = (current_price / position['entry_price'] - 1) * 100
            else:  # SHORT
                pnl = (position['entry_price'] - current_price) * position['quantity']
                pnl_pct = (position['entry_price'] / current_price - 1) * 100
            
            position['unrealized_pnl'] = pnl
            position['unrealized_pnl_pct'] = pnl_pct
            
            # Verificar stops
            close_reason = None
            
            if position['type'] == 'LONG':
                if current_price <= position['stop_loss']:
                    close_reason = 'STOP_LOSS'
                elif current_price >= position['take_profit']:
                    close_reason = 'TAKE_PROFIT'
            else:  # SHORT
                if current_price >= position['stop_loss']:
                    close_reason = 'STOP_LOSS'
                elif current_price <= position['take_profit']:
                    close_reason = 'TAKE_PROFIT'
            
            # Marcar para cierre si hay trigger
            if close_reason:
                positions_to_close.append((symbol, close_reason))
        
        # Cerrar posiciones triggered
        for symbol, reason in positions_to_close:
            self.close_position(symbol, reason)
    
    def _get_current_price(self, symbol):
        """Obtiene precio actual del símbolo"""
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if len(data) > 0:
                return float(data['Close'].iloc[-1])
            else:
                return None
                
        except Exception as e:
            print(f"⚠️ Error obteniendo precio para {symbol}: {e}")
            return None
    
    def close_position(self, symbol, reason='MANUAL'):
        """Cierra una posición"""
        
        if symbol not in self.positions:
            return False, f"No existe posición en {symbol}"
        
        position = self.positions[symbol]
        
        if position['status'] != 'OPEN':
            return False, f"Posición ya cerrada"
        
        # Precio de cierre
        exit_price = position['current_price']
        exit_time = datetime.now()
        
        # Calcular P&L final
        if position['type'] == 'LONG':
            realized_pnl = (exit_price - position['entry_price']) * position['quantity']
        else:  # SHORT
            realized_pnl = (position['entry_price'] - exit_price) * position['quantity']
        
        # Comisión de cierre
        exit_commission = position['capital_used'] * self.trading_config['commission_pct']
        net_pnl = realized_pnl - exit_commission
        
        # Actualizar capital
        returned_capital = position['capital_used'] + net_pnl
        self.available_capital += returned_capital
        self.current_capital = self.available_capital
        
        # Actualizar posición
        position.update({
            'status': 'CLOSED',
            'exit_price': exit_price,
            'exit_time': exit_time,
            'exit_reason': reason,
            'realized_pnl': net_pnl,
            'realized_pnl_pct': (net_pnl / position['capital_used']) * 100,
            'holding_time': exit_time - position['entry_time'],
            'exit_commission': exit_commission,
            'total_commission': position['commission_paid'] + exit_commission
        })
        
        # Mover a historial
        self.trade_history.append(position.copy())
        
        # Actualizar métricas
        self._update_performance_metrics()
        
        # Log
        pnl_color = "🟢" if net_pnl > 0 else "🔴"
        print(f"{pnl_color} POSICIÓN CERRADA: {position['type']} {symbol}")
        print(f"   • Entry: ${position['entry_price']:.2f}")
        print(f"   • Exit: ${exit_price:.2f}")
        print(f"   • P&L: ${net_pnl:+.2f} ({position['realized_pnl_pct']:+.2f}%)")
        print(f"   • Razón: {reason}")
        print(f"   • Duración: {position['holding_time']}")
        
        # Remover del portfolio activo
        del self.positions[symbol]
        
        return True, f"Posición cerrada: P&L ${net_pnl:+.2f}"
    
    def _update_performance_metrics(self):
        """Actualiza métricas de performance"""
        
        if not self.trade_history:
            return
        
        # Métricas básicas
        total_trades = len(self.trade_history)
        winning_trades = len([t for t in self.trade_history if t['realized_pnl'] > 0])
        losing_trades = total_trades - winning_trades
        
        # Win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Profit factor
        total_wins = sum([t['realized_pnl'] for t in self.trade_history if t['realized_pnl'] > 0])
        total_losses = abs(sum([t['realized_pnl'] for t in self.trade_history if t['realized_pnl'] < 0]))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Total return
        total_return = ((self.current_capital / self.initial_capital) - 1) * 100
        
        # Max drawdown (simplificado)
        peak_capital = self.initial_capital
        max_drawdown = 0
        
        for trade in self.trade_history:
            if 'capital_after_trade' in trade:
                peak_capital = max(peak_capital, trade['capital_after_trade'])
                drawdown = (peak_capital - trade['capital_after_trade']) / peak_capital
                max_drawdown = max(max_drawdown, drawdown)
        
        # Actualizar métricas
        self.performance_metrics.update({
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown * 100,
            'total_return': total_return,
            'current_capital': self.current_capital
        })
    
    def get_portfolio_status(self):
        """Obtiene estado actual del portfolio"""
        
        # Actualizar posiciones
        self.update_positions()
        
        # Calcular P&L no realizado
        total_unrealized_pnl = sum([pos['unrealized_pnl'] for pos in self.positions.values()])
        
        # Portfolio value
        portfolio_value = self.available_capital + sum([pos['capital_used'] for pos in self.positions.values()]) + total_unrealized_pnl
        
        status = {
            'timestamp': datetime.now(),
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'available_capital': self.available_capital,
            'portfolio_value': portfolio_value,
            'total_return': ((portfolio_value / self.initial_capital) - 1) * 100,
            'open_positions': len(self.positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'capital_utilization': ((self.initial_capital - self.available_capital) / self.initial_capital) * 100,
            'performance': self.performance_metrics
        }
        
        return status
    
    def print_portfolio_status(self):
        """Imprime estado del portfolio"""
        
        status = self.get_portfolio_status()
        
        print(f"\n💼 PORTFOLIO STATUS - {status['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Capital y returns
        print(f"💰 CAPITAL:")
        print(f"   • Inicial: ${status['initial_capital']:,}")
        print(f"   • Actual: ${status['current_capital']:,.2f}")
        print(f"   • Disponible: ${status['available_capital']:,.2f}")
        print(f"   • Portfolio Value: ${status['portfolio_value']:,.2f}")
        
        # Returns
        return_color = "🟢" if status['total_return'] > 0 else "🔴" if status['total_return'] < 0 else "⚪"
        print(f"\n📈 PERFORMANCE:")
        print(f"   • Total Return: {return_color} {status['total_return']:+.2f}%")
        print(f"   • Unrealized P&L: ${status['total_unrealized_pnl']:+,.2f}")
        print(f"   • Capital Utilizado: {status['capital_utilization']:.1f}%")
        
        # Trading metrics
        metrics = status['performance']
        if metrics['total_trades'] > 0:
            print(f"\n📊 TRADING METRICS:")
            print(f"   • Total Trades: {metrics['total_trades']}")
            print(f"   • Win Rate: {metrics['win_rate']:.1f}%")
            print(f"   • Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"   • Max Drawdown: {metrics['max_drawdown']:.2f}%")
        
        # Posiciones abiertas
        if self.positions:
            print(f"\n🔓 POSICIONES ABIERTAS ({len(self.positions)}):")
            for symbol, pos in self.positions.items():
                pnl_color = "🟢" if pos['unrealized_pnl'] > 0 else "🔴"
                print(f"   • {pos['type']} {symbol}: ${pos['unrealized_pnl']:+.2f} ({pos['unrealized_pnl_pct']:+.1f}%) {pnl_color}")
        
        return status
    
    def run_paper_trading_session(self, symbols=None, duration_hours=24):
        """Ejecuta sesión de paper trading"""
        
        if symbols is None:
            symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD']
        
        print(f"🎯 INICIANDO PAPER TRADING SESSION")
        print(f"📊 Símbolos: {symbols}")
        print(f"⏰ Duración: {duration_hours} horas")
        print("="*70)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        check_interval = 30  # minutos
        
        session_log = []
        
        while datetime.now() < end_time:
            try:
                print(f"\n🔄 Análisis de mercado - {datetime.now().strftime('%H:%M:%S')}")
                
                # Analizar cada símbolo
                for symbol in symbols:
                    if symbol not in self.positions:  # Solo si no tenemos posición
                        signal, message = self.analyze_signal(symbol)
                        
                        if signal:
                            success, result = self.place_order(signal)
                            if success:
                                session_log.append({
                                    'timestamp': datetime.now(),
                                    'action': 'OPEN_POSITION',
                                    'symbol': symbol,
                                    'signal': signal,
                                    'result': result
                                })
                
                # Actualizar posiciones existentes
                self.update_positions()
                
                # Status cada hora
                if datetime.now().minute in [0, 30]:
                    self.print_portfolio_status()
                
                # Esperar próximo check
                print(f"⏳ Próximo análisis en {check_interval} minutos...")
                
                # En demo, solo hacer un ciclo
                break
                
            except KeyboardInterrupt:
                print(f"\n⏹️ Paper trading interrumpido por usuario")
                break
            except Exception as e:
                print(f"⚠️ Error en sesión: {e}")
                continue
        
        # Resumen final
        print(f"\n🏁 SESIÓN FINALIZADA")
        final_status = self.print_portfolio_status()
        
        return {
            'session_log': session_log,
            'final_status': final_status,
            'duration': datetime.now() - start_time
        }

def demo_paper_trading():
    """Demo del sistema de paper trading"""
    
    print("🎯 PAPER TRADING SYSTEM DEMO")
    print("="*70)
    
    # Inicializar sistema
    paper_trader = PaperTradingSystem(initial_capital=10000)
    
    # Status inicial
    paper_trader.print_portfolio_status()
    
    # Simular análisis de señal
    print(f"\n🔍 ANÁLISIS DE SEÑAL DEMO:")
    signal, message = paper_trader.analyze_signal('BTC-USD')
    
    if signal:
        print(f"✅ Señal detectada: {signal['type']} {signal['symbol']}")
        print(f"   • Score: {signal['final_score']:.2f}")
        print(f"   • Entry: ${signal['entry_price']:.2f}")
        
        # Colocar orden
        success, result = paper_trader.place_order(signal)
        print(f"   • Orden: {result}")
        
        # Status después de orden
        paper_trader.print_portfolio_status()
    else:
        print(f"❌ Sin señal: {message}")
    
    return paper_trader

if __name__ == "__main__":
    demo_paper_trading()