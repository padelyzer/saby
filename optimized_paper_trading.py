#!/usr/bin/env python3
"""
Sistema de Paper Trading Optimizado con Estrategias Validadas
Integra los resultados del backtesting para usar las mejores estrategias por activo
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
import time

# Importar sistemas optimizados
from backtest_system_v2 import BacktestSystemV2
from trading_config import (
    TRADING_SYMBOLS, get_asset_type, get_strategy_config, 
    get_recommended_strategies, SYMBOL_DECIMALS
)
from binance_data_fetcher import BinanceDataFetcher
from error_handler import error_handler, TradingErrorContext

# Configuración optimizada basada en resultados del backtesting
PRODUCTION_STRATEGY_CONFIG = {
    'BNBUSDT': {'strategy': 'mean_reversion', 'timeframe': '1h', 'confidence': 'high'},
    'SOLUSDT': {'strategy': 'mean_reversion', 'timeframe': '1h', 'confidence': 'high'},
    'XRPUSDT': {'strategy': 'mean_reversion', 'timeframe': '1h', 'confidence': 'high'},
    'ADAUSDT': {'strategy': 'mean_reversion', 'timeframe': '1h', 'confidence': 'medium'},  # Cambiado de trend_following
    'AVAXUSDT': {'strategy': 'avax_optimized', 'timeframe': '1h', 'confidence': 'ultra_high'},
    'LINKUSDT': {'strategy': 'mean_reversion', 'timeframe': '4h', 'confidence': 'medium'},  # Oracle - mean_reversion menos estricto
    'DOTUSDT': {'strategy': 'momentum', 'timeframe': '1h', 'confidence': 'medium'},  # Cambiado a momentum por bajo WR
    'DOGEUSDT': {'strategy': 'volume_breakout', 'timeframe': '15m', 'confidence': 'medium', 'risk': 'high'}  # Cambiado a volume_breakout
}

@dataclass 
class OptimizedTrade:
    """Trade optimizado con información de estrategia"""
    id: str
    timestamp: datetime
    symbol: str
    action: str  # BUY o SELL
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    position_value: float
    strategy_used: str
    asset_type: str
    confidence: float
    status: str  # OPEN, CLOSED_WIN, CLOSED_LOSS, CLOSED_MANUAL
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    exit_reason: Optional[str] = None
    holding_time_hours: Optional[float] = None

class OptimizedPaperTrading:
    """Sistema de paper trading con estrategias optimizadas"""
    
    def __init__(self, initial_capital: float = 10000, risk_level: str = 'balanced'):
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        self.risk_level = risk_level
        
        # Sistemas de trading
        self.data_fetcher = BinanceDataFetcher()
        self.backtest_system = BacktestSystemV2()
        
        # Configuración de riesgo
        self._configure_risk_parameters()
        
        # Tracking
        self.open_positions = {}
        self.closed_trades = []
        self.signal_history = []
        self.performance_metrics = {}
        self.running = False
        
        # Límites
        self.max_open_trades = 5
        self.scan_interval = 300  # 5 minutos
        self.symbols = TRADING_SYMBOLS
        
        print("\n" + "="*70)
        print(" PAPER TRADING OPTIMIZADO V2.0 ".center(70))
        print("="*70)
        print(f"💰 Capital inicial: ${initial_capital:,.2f}")
        print(f"⚠️  Nivel de riesgo: {risk_level.upper()}")
        print(f"🧠 Estrategias validadas: {len(PRODUCTION_STRATEGY_CONFIG)}")
        print(f"📊 Símbolos monitoreados: {len(self.symbols)}")
        print(f"🎯 Max trades simultáneos: {self.max_open_trades}")
        
        # Mostrar configuración de estrategias
        print(f"\n📋 CONFIGURACIÓN DE ESTRATEGIAS:")
        for symbol, config in PRODUCTION_STRATEGY_CONFIG.items():
            asset_type = get_asset_type(symbol)
            print(f"   {symbol} ({asset_type}): {config['strategy']} @ {config['timeframe']}")
    
    def _configure_risk_parameters(self):
        """Configura parámetros de riesgo según nivel"""
        
        risk_configs = {
            'conservative': {
                'max_position_size': 0.015,  # 1.5%
                'position_multiplier': 0.8,
                'confidence_threshold': 0.7
            },
            'balanced': {
                'max_position_size': 0.025,  # 2.5%
                'position_multiplier': 1.0,
                'confidence_threshold': 0.6
            },
            'aggressive': {
                'max_position_size': 0.04,   # 4%
                'position_multiplier': 1.2,
                'confidence_threshold': 0.5
            }
        }
        
        config = risk_configs[self.risk_level]
        self.max_position_size = config['max_position_size']
        self.position_multiplier = config['position_multiplier']
        self.confidence_threshold = config['confidence_threshold']
    
    def format_price(self, price: float, symbol: str) -> float:
        """Formatea precio según precisión del símbolo"""
        decimals = SYMBOL_DECIMALS.get(symbol, 4)
        return float(f"{price:.{decimals}f}")
    
    def generate_optimized_signal(self, symbol: str) -> Optional[Dict]:
        """Genera señal usando la estrategia optimizada para el símbolo"""
        
        try:
            with TradingErrorContext("generate_signal", symbol):
                # Obtener configuración optimizada
                if symbol not in PRODUCTION_STRATEGY_CONFIG:
                    return None
                
                config = PRODUCTION_STRATEGY_CONFIG[symbol]
                strategy = config['strategy']
                timeframe = config['timeframe']
                
                # Obtener datos históricos
                df = self.data_fetcher.get_klines(symbol, timeframe, 100)
                
                if df.empty or len(df) < 50:
                    return None
                
                # Calcular indicadores
                df = self.data_fetcher.calculate_indicators(df)
                
                # Generar señales usando sistema de backtest
                df = self.backtest_system.generate_signals(df, strategy, symbol)
                
                # Verificar última señal
                if df.empty:
                    return None
                
                latest = df.iloc[-1]
                
                # Solo procesar señales nuevas (no position 0)
                if latest['signal'] == 0:
                    return None
                
                # Obtener configuración específica para este activo
                strategy_config = get_strategy_config(strategy, symbol)
                asset_type = get_asset_type(symbol)
                
                # Calcular precios optimizados
                current_price = self.format_price(latest['Close'], symbol)
                
                if latest['signal'] > 0:  # BUY
                    action = "BUY"
                    
                    # Take profit y stop loss específicos
                    tp_pct = strategy_config.get('take_profit', 0.04)
                    sl_pct = strategy_config.get('stop_loss', 0.02)
                    
                    take_profit = self.format_price(current_price * (1 + tp_pct), symbol)
                    stop_loss = self.format_price(current_price * (1 - sl_pct), symbol)
                    
                elif latest['signal'] < 0:  # SELL (short)
                    action = "SELL"
                    
                    tp_pct = strategy_config.get('take_profit', 0.04)
                    sl_pct = strategy_config.get('stop_loss', 0.02)
                    
                    take_profit = self.format_price(current_price * (1 - tp_pct), symbol)
                    stop_loss = self.format_price(current_price * (1 + sl_pct), symbol)
                
                else:
                    return None
                
                # Calcular confianza basada en indicadores
                confidence = self._calculate_signal_confidence(latest, strategy, asset_type)
                
                # Filtrar por confianza mínima
                if confidence < self.confidence_threshold:
                    return None
                
                signal = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': action,
                    'entry_price': current_price,
                    'take_profit': take_profit,
                    'stop_loss': stop_loss,
                    'strategy': strategy,
                    'asset_type': asset_type,
                    'confidence': confidence,
                    'timeframe': timeframe,
                    'indicators': {
                        'rsi': latest.get('RSI', 0),
                        'volume_ratio': latest.get('Volume', 0) / latest.get('Volume_SMA', 1) if latest.get('Volume_SMA', 0) > 0 else 1,
                        'price_vs_ema20': current_price / latest.get('EMA_20', current_price) if latest.get('EMA_20', 0) > 0 else 1
                    }
                }
                
                return signal
                
        except Exception as e:
            error_handler.handle_error(e, context={'symbol': symbol, 'operation': 'generate_signal'})
            return None
    
    def _calculate_signal_confidence(self, data: pd.Series, strategy: str, asset_type: str) -> float:
        """Calcula confianza de la señal basada en indicadores"""
        
        confidence = 0.5  # Base
        
        # Factores por estrategia
        if strategy == 'mean_reversion':
            # RSI extremos = mayor confianza
            rsi = data.get('RSI', 50)
            if rsi < 30 or rsi > 70:
                confidence += 0.2
            if rsi < 25 or rsi > 75:
                confidence += 0.1
                
            # Bollinger Bands
            if 'BB_Lower' in data and 'BB_Upper' in data:
                close = data.get('Close', 0)
                if close < data['BB_Lower'] or close > data['BB_Upper']:
                    confidence += 0.15
        
        elif strategy == 'trend_following':
            # EMA alignment
            ema_9 = data.get('EMA_9', 0)
            ema_20 = data.get('EMA_20', 0)
            ema_50 = data.get('EMA_50', 0)
            
            if ema_9 > ema_20 > ema_50 or ema_9 < ema_20 < ema_50:
                confidence += 0.2
            
            # MACD confirmación
            macd = data.get('MACD', 0)
            signal = data.get('Signal', 0)
            if abs(macd - signal) > 0.1:  # Divergencia significativa
                confidence += 0.1
        
        # Factores por tipo de activo
        if asset_type == 'LARGE_CAP':
            confidence += 0.05  # Más estables
        elif asset_type == 'MEME':
            confidence -= 0.1   # Más volátiles
        
        # Volume confirmation
        volume_ratio = data.get('Volume', 0) / data.get('Volume_SMA', 1) if data.get('Volume_SMA', 0) > 0 else 1
        if volume_ratio > 1.5:
            confidence += 0.1
        
        return min(max(confidence, 0.1), 0.95)  # Clamp entre 0.1 y 0.95
    
    def execute_trade(self, signal: Dict) -> Optional[OptimizedTrade]:
        """Ejecuta un trade basado en la señal optimizada"""
        
        try:
            symbol = signal['symbol']
            
            # Verificar si ya hay posición abierta para este símbolo
            if symbol in self.open_positions:
                return None
            
            # Verificar límite de trades
            if len(self.open_positions) >= self.max_open_trades:
                return None
            
            # Calcular tamaño de posición
            available_capital = self.current_balance * 0.95  # 5% buffer
            position_size = available_capital * self.max_position_size * self.position_multiplier
            
            # Ajustar por confianza
            confidence_factor = signal['confidence']
            position_size *= confidence_factor
            
            # Ajustar por tipo de activo
            asset_type = signal['asset_type']
            if asset_type == 'MEME':
                position_size *= 0.5  # Reducir para meme coins
            elif asset_type == 'LARGE_CAP':
                position_size *= 1.1  # Aumentar para large caps
            
            entry_price = signal['entry_price']
            position_value = position_size
            
            # Crear trade
            trade = OptimizedTrade(
                id=f"{symbol}_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                symbol=symbol,
                action=signal['action'],
                entry_price=entry_price,
                current_price=entry_price,
                stop_loss=signal['stop_loss'],
                take_profit=signal['take_profit'],
                position_size=position_size,
                position_value=position_value,
                strategy_used=signal['strategy'],
                asset_type=asset_type,
                confidence=confidence_factor,
                status='OPEN'
            )
            
            # Registrar trade
            self.open_positions[symbol] = trade
            self.current_balance -= position_size
            
            print(f"\n🚀 TRADE EJECUTADO:")
            print(f"   {symbol} {signal['action']} @ ${entry_price}")
            print(f"   Estrategia: {signal['strategy']} ({asset_type})")
            print(f"   Confianza: {confidence_factor:.1%}")
            print(f"   TP: ${signal['take_profit']} | SL: ${signal['stop_loss']}")
            print(f"   Capital usado: ${position_size:.2f}")
            
            return trade
            
        except Exception as e:
            error_handler.handle_error(e, context={'symbol': signal.get('symbol'), 'operation': 'execute_trade'})
            return None
    
    def update_positions(self):
        """Actualiza todas las posiciones abiertas"""
        
        for symbol in list(self.open_positions.keys()):
            try:
                self._update_single_position(symbol)
            except Exception as e:
                error_handler.handle_error(e, context={'symbol': symbol, 'operation': 'update_position'})
    
    def _update_single_position(self, symbol: str):
        """Actualiza una posición específica"""
        
        trade = self.open_positions[symbol]
        
        # Obtener precio actual
        ticker_data = self.data_fetcher.get_ticker_24hr(symbol)
        if not ticker_data:
            return
        
        current_price = self.format_price(ticker_data['price'], symbol)
        trade.current_price = current_price
        
        # Calcular PnL
        if trade.action == 'BUY':
            pnl = (current_price - trade.entry_price) / trade.entry_price
        else:  # SELL
            pnl = (trade.entry_price - current_price) / trade.entry_price
        
        trade.pnl_percent = pnl * 100
        trade.pnl = trade.position_value * pnl
        
        # Verificar condiciones de cierre
        should_close, reason = self._should_close_position(trade, current_price)
        
        if should_close:
            self._close_position(symbol, reason, current_price)
    
    def _should_close_position(self, trade: OptimizedTrade, current_price: float) -> Tuple[bool, str]:
        """Determina si una posición debe cerrarse"""
        
        # Take profit
        if trade.action == 'BUY' and current_price >= trade.take_profit:
            return True, "TAKE_PROFIT"
        elif trade.action == 'SELL' and current_price <= trade.take_profit:
            return True, "TAKE_PROFIT"
        
        # Stop loss
        if trade.action == 'BUY' and current_price <= trade.stop_loss:
            return True, "STOP_LOSS"
        elif trade.action == 'SELL' and current_price >= trade.stop_loss:
            return True, "STOP_LOSS"
        
        # Time-based exit (para meme coins)
        if trade.asset_type == 'MEME':
            hours_open = (datetime.now() - trade.timestamp).total_seconds() / 3600
            if hours_open > 24:  # Máximo 24 horas para meme coins
                return True, "TIME_LIMIT"
        
        return False, ""
    
    def _close_position(self, symbol: str, reason: str, exit_price: float):
        """Cierra una posición"""
        
        if symbol not in self.open_positions:
            return
        
        trade = self.open_positions[symbol]
        
        # Actualizar trade
        trade.exit_price = exit_price
        trade.exit_timestamp = datetime.now()
        trade.exit_reason = reason
        trade.holding_time_hours = (trade.exit_timestamp - trade.timestamp).total_seconds() / 3600
        
        # Determinar status
        if trade.pnl > 0:
            trade.status = 'CLOSED_WIN'
        else:
            trade.status = 'CLOSED_LOSS'
        
        # Actualizar balance
        final_value = trade.position_value * (1 + trade.pnl_percent / 100)
        self.current_balance += final_value
        
        # Mover a historial
        self.closed_trades.append(trade)
        del self.open_positions[symbol]
        
        print(f"\n📊 POSICIÓN CERRADA:")
        print(f"   {symbol} {trade.action} @ ${exit_price}")
        print(f"   Razón: {reason}")
        print(f"   PnL: {trade.pnl_percent:.2f}% (${trade.pnl:.2f})")
        print(f"   Tiempo: {trade.holding_time_hours:.1f}h")
    
    def scan_markets(self):
        """Escanea mercados en busca de señales"""
        
        print(f"\n🔍 Escaneando mercados... ({datetime.now().strftime('%H:%M:%S')})")
        
        signals_found = 0
        
        for symbol in self.symbols:
            # Skip si ya hay posición abierta
            if symbol in self.open_positions:
                continue
            
            signal = self.generate_optimized_signal(symbol)
            
            if signal:
                signals_found += 1
                
                # Guardar en historial
                self.signal_history.append({
                    'timestamp': signal['timestamp'],
                    'signal': signal
                })
                
                # Intentar ejecutar trade
                trade = self.execute_trade(signal)
                
                if not trade:
                    print(f"   ⚠️ {symbol}: Señal detectada pero no ejecutada")
        
        print(f"   📈 Señales encontradas: {signals_found}")
        print(f"   💼 Posiciones abiertas: {len(self.open_positions)}")
        print(f"   💰 Balance actual: ${self.current_balance:.2f}")
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del sistema"""
        
        total_trades = len(self.closed_trades)
        if total_trades == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'current_balance': self.current_balance,
                'open_positions': len(self.open_positions)
            }
        
        winning_trades = len([t for t in self.closed_trades if t.pnl > 0])
        losing_trades = total_trades - winning_trades
        total_pnl = sum(t.pnl for t in self.closed_trades)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades) * 100,
            'total_pnl': total_pnl,
            'total_return': ((self.current_balance - self.initial_capital) / self.initial_capital) * 100,
            'current_balance': self.current_balance,
            'open_positions': len(self.open_positions)
        }
    
    def run_live_trading(self):
        """Ejecuta trading en vivo"""
        
        self.running = True
        
        print(f"\n🚀 INICIANDO TRADING EN VIVO")
        print(f"Intervalo de escaneo: {self.scan_interval}s")
        
        while self.running:
            try:
                # Escanear mercados
                self.scan_markets()
                
                # Actualizar posiciones
                self.update_positions()
                
                # Mostrar estadísticas periódicamente
                stats = self.get_statistics()
                if stats['total_trades'] > 0:
                    print(f"📊 Stats: {stats['win_rate']:.1f}% WR, {stats['total_return']:.2f}% Return")
                
                # Esperar
                time.sleep(self.scan_interval)
                
            except KeyboardInterrupt:
                print("\n⏹️ Deteniendo trading...")
                break
            except Exception as e:
                error_handler.handle_error(e, context={'operation': 'live_trading'})
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
        
        self.running = False
        print("\n✅ Trading detenido")

if __name__ == "__main__":
    # Test del sistema optimizado
    trading_system = OptimizedPaperTrading(initial_capital=10000, risk_level='balanced')
    
    print("\n🧪 MODO TEST - Presiona Ctrl+C para detener")
    trading_system.run_live_trading()