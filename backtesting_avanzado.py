#!/usr/bin/env python3
"""
Sistema Avanzado de Backtesting con Múltiples Estrategias
Permite seleccionar estrategias, pares y optimizar parámetros
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Importar módulos del sistema
from motor_trading import obtener_datos, calcular_indicadores
from advanced_signals import AdvancedSignalDetector
from liquidity_pools import LiquidityPoolDetector

@dataclass
class TradeResult:
    """Resultado de un trade individual"""
    ticker: str
    strategy: str
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    direction: str  # LONG/SHORT
    profit_pct: float
    profit_usd: float
    exit_reason: str  # TP/SL/SIGNAL
    score: float

class TradingStrategy(ABC):
    """Clase base para todas las estrategias"""
    
    def __init__(self, name: str):
        self.name = name
        self.min_score = 5
        self.take_profit = 0.03  # 3%
        self.stop_loss = 0.015   # 1.5%
        self.leverage = 3
        
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, ticker: str) -> Optional[Dict]:
        """Genera señal de trading si las condiciones se cumplen"""
        pass
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calcula el RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    def calculate_score(self, df: pd.DataFrame) -> float:
        """Calcula score base común"""
        score = 0
        
        # RSI - Calcular si no existe
        if 'RSI' in df.columns:
            rsi = df['RSI'].iloc[-1]
            # Convertir a escalar si es Serie
            if isinstance(rsi, pd.Series):
                rsi = rsi.iloc[0] if len(rsi) > 0 else 50
        else:
            # Cálculo manual de RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            if isinstance(rsi, pd.Series):
                rsi = rsi.iloc[0] if len(rsi) > 0 else 50
        
        if 30 <= rsi <= 40:
            score += 2  # Oversold
        elif 60 <= rsi <= 70:
            score += 2  # Overbought
            
        # Volumen
        if 'Volume' in df.columns and len(df) >= 20:
            try:
                vol_current = df['Volume'].iloc[-1]
                vol_mean = df['Volume'].rolling(20).mean().iloc[-1]
                
                # Convertir a escalares si son Series
                if isinstance(vol_current, pd.Series):
                    vol_current = vol_current.iloc[0] if len(vol_current) > 0 else 0
                if isinstance(vol_mean, pd.Series):
                    vol_mean = vol_mean.iloc[0] if len(vol_mean) > 0 else 0
                
                if vol_mean > 0 and vol_current > 0:
                    if vol_current / vol_mean > 1.5:
                        score += 1
            except:
                pass  # Ignorar errores de volumen
            
        return score

class MomentumStrategy(TradingStrategy):
    """Estrategia basada en momentum y tendencia"""
    
    def __init__(self):
        super().__init__("Momentum")
        self.min_score = 6
        self.take_profit = 0.05  # 5%
        self.stop_loss = 0.02    # 2%
    
    def generate_signal(self, df: pd.DataFrame, ticker: str) -> Optional[Dict]:
        if len(df) < 200:
            return None
            
        # Calcular indicadores
        current_price = df['Close'].iloc[-1]
        if isinstance(current_price, pd.Series):
            current_price = current_price.iloc[0]
        
        sma50 = df['SMA_50'].iloc[-1] if 'SMA_50' in df.columns else df['Close'].rolling(50).mean().iloc[-1]
        if isinstance(sma50, pd.Series):
            sma50 = sma50.iloc[0]
        
        sma200 = df['SMA_200'].iloc[-1] if 'SMA_200' in df.columns else df['Close'].rolling(200).mean().iloc[-1]
        if isinstance(sma200, pd.Series):
            sma200 = sma200.iloc[0]
        
        rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
        if isinstance(rsi, pd.Series):
            rsi = rsi.iloc[0] if len(rsi) > 0 else 50
        
        score = self.calculate_score(df)
        signal_type = None
        
        # LONG: Precio sobre medias, momentum alcista
        if current_price > sma50 > sma200 and rsi < 70:
            signal_type = 'LONG'
            score += 3
            
            # Momentum adicional
            returns_5d = (current_price / df['Close'].iloc[-5] - 1)
            if returns_5d > 0.02:  # +2% en 5 días
                score += 2
        
        # SHORT: Precio bajo medias, momentum bajista
        elif current_price < sma50 < sma200 and rsi > 30:
            signal_type = 'SHORT'
            score += 3
            
            returns_5d = (current_price / df['Close'].iloc[-5] - 1)
            if returns_5d < -0.02:  # -2% en 5 días
                score += 2
        
        if score >= self.min_score and signal_type:
            return {
                'ticker': ticker,
                'type': signal_type,
                'score': score,
                'entry_price': current_price,
                'stop_loss': current_price * (1 - self.stop_loss) if signal_type == 'LONG' else current_price * (1 + self.stop_loss),
                'take_profit': current_price * (1 + self.take_profit) if signal_type == 'LONG' else current_price * (1 - self.take_profit),
                'strategy': self.name
            }
        
        return None

class MeanReversionStrategy(TradingStrategy):
    """Estrategia de reversión a la media"""
    
    def __init__(self):
        super().__init__("Mean Reversion")
        self.min_score = 5
        self.take_profit = 0.025  # 2.5%
        self.stop_loss = 0.015    # 1.5%
        self.bb_period = 20
        self.bb_std = 2
    
    def generate_signal(self, df: pd.DataFrame, ticker: str) -> Optional[Dict]:
        if len(df) < 50:
            return None
        
        # Calcular Bollinger Bands
        sma = df['Close'].rolling(self.bb_period).mean()
        std = df['Close'].rolling(self.bb_period).std()
        upper_band = sma + (std * self.bb_std)
        lower_band = sma - (std * self.bb_std)
        
        current_price = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else self.calculate_rsi(df['Close'])
        
        score = self.calculate_score(df)
        signal_type = None
        
        # LONG: Precio toca banda inferior (oversold)
        if current_price <= lower_band.iloc[-1] and rsi < 35:
            signal_type = 'LONG'
            score += 4
            
            # Confirmación adicional
            if current_price < lower_band.iloc[-2]:  # Segunda vela fuera
                score += 2
        
        # SHORT: Precio toca banda superior (overbought)
        elif current_price >= upper_band.iloc[-1] and rsi > 65:
            signal_type = 'SHORT'
            score += 4
            
            if current_price > upper_band.iloc[-2]:
                score += 2
        
        if score >= self.min_score and signal_type:
            # Target: volver a la media
            target = sma.iloc[-1]
            
            return {
                'ticker': ticker,
                'type': signal_type,
                'score': score,
                'entry_price': current_price,
                'stop_loss': current_price * (1 - self.stop_loss) if signal_type == 'LONG' else current_price * (1 + self.stop_loss),
                'take_profit': target,
                'strategy': self.name
            }
        
        return None

class BreakoutStrategy(TradingStrategy):
    """Estrategia de ruptura de rangos"""
    
    def __init__(self):
        super().__init__("Breakout")
        self.min_score = 7
        self.take_profit = 0.08  # 8%
        self.stop_loss = 0.03    # 3%
        self.lookback = 20
    
    def generate_signal(self, df: pd.DataFrame, ticker: str) -> Optional[Dict]:
        if len(df) < self.lookback:
            return None
        
        # Identificar rangos
        recent_high = df['High'].tail(self.lookback).max()
        recent_low = df['Low'].tail(self.lookback).min()
        current_price = df['Close'].iloc[-1]
        
        # Calcular ATR para volatilidad
        if 'ATR' in df.columns:
            atr = df['ATR'].iloc[-1]
        else:
            # Cálculo manual de ATR
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(14).mean().iloc[-1]
        range_size = recent_high - recent_low
        
        score = self.calculate_score(df)
        signal_type = None
        
        # LONG: Ruptura alcista
        if current_price > recent_high * 0.995:  # Casi rompiendo
            signal_type = 'LONG'
            score += 4
            
            # Volumen de confirmación
            if len(df) >= 20:
                try:
                    vol_current = df['Volume'].iloc[-1]
                    vol_mean = df['Volume'].rolling(20).mean().iloc[-1]
                    if isinstance(vol_current, pd.Series):
                        vol_current = vol_current.iloc[0]
                    if isinstance(vol_mean, pd.Series):
                        vol_mean = vol_mean.iloc[0]
                    if vol_mean > 0 and vol_current / vol_mean > 2:
                        score += 3
                except:
                    pass
        
        # SHORT: Ruptura bajista
        elif current_price < recent_low * 1.005:
            signal_type = 'SHORT'
            score += 4
            
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1]
            if vol_ratio > 2:
                score += 3
        
        if score >= self.min_score and signal_type:
            # Proyección basada en rango
            projection = range_size * 1.5
            
            return {
                'ticker': ticker,
                'type': signal_type,
                'score': score,
                'entry_price': current_price,
                'stop_loss': recent_low if signal_type == 'LONG' else recent_high,
                'take_profit': current_price + projection if signal_type == 'LONG' else current_price - projection,
                'strategy': self.name
            }
        
        return None

class ScalpingStrategy(TradingStrategy):
    """Estrategia de scalping rápido"""
    
    def __init__(self):
        super().__init__("Scalping")
        self.min_score = 4
        self.take_profit = 0.01   # 1%
        self.stop_loss = 0.005    # 0.5%
        self.leverage = 5
    
    def generate_signal(self, df: pd.DataFrame, ticker: str) -> Optional[Dict]:
        if len(df) < 20:
            return None
        
        # Indicadores rápidos
        current_price = df['Close'].iloc[-1]
        sma5 = df['Close'].rolling(5).mean().iloc[-1]
        sma10 = df['Close'].rolling(10).mean().iloc[-1]
        
        # VWAP (Volume Weighted Average Price)
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
        vwap = df['VWAP'].iloc[-1]
        
        score = self.calculate_score(df)
        signal_type = None
        
        # LONG: Precio cruza SMA5 al alza
        if current_price > sma5 > sma10 and current_price > vwap:
            signal_type = 'LONG'
            score += 3
            
            # Momentum micro
            if df['Close'].iloc[-1] > df['Close'].iloc[-2] > df['Close'].iloc[-3]:
                score += 2
        
        # SHORT: Precio cruza SMA5 a la baja
        elif current_price < sma5 < sma10 and current_price < vwap:
            signal_type = 'SHORT'
            score += 3
            
            if df['Close'].iloc[-1] < df['Close'].iloc[-2] < df['Close'].iloc[-3]:
                score += 2
        
        if score >= self.min_score and signal_type:
            return {
                'ticker': ticker,
                'type': signal_type,
                'score': score,
                'entry_price': current_price,
                'stop_loss': current_price * (1 - self.stop_loss) if signal_type == 'LONG' else current_price * (1 + self.stop_loss),
                'take_profit': current_price * (1 + self.take_profit) if signal_type == 'LONG' else current_price * (1 - self.take_profit),
                'strategy': self.name
            }
        
        return None

class LiquidityHuntStrategy(TradingStrategy):
    """Estrategia basada en barridos de liquidez"""
    
    def __init__(self):
        super().__init__("Liquidity Hunt")
        self.min_score = 6
        self.take_profit = 0.04  # 4%
        self.stop_loss = 0.02    # 2%
        self.liquidity_detector = LiquidityPoolDetector()
    
    def generate_signal(self, df: pd.DataFrame, ticker: str) -> Optional[Dict]:
        if len(df) < 100:
            return None
        
        current_price = df['Close'].iloc[-1]
        
        # Detectar pools de liquidez
        liquidity_data = self.liquidity_detector.detect_liquidity_pools(df, current_price)
        
        score = self.calculate_score(df)
        signal_type = None
        
        # Buscar barridos recientes
        recent_high = df['High'].tail(5).max()
        recent_low = df['Low'].tail(5).min()
        
        # LONG: Barrido de stops por debajo
        below_pools = liquidity_data['pools'].get('below_price', [])
        if below_pools:
            nearest_pool = min(below_pools, key=lambda x: abs(x['price'] - current_price))
            
            # Si el precio tocó el pool y rebotó
            if recent_low <= nearest_pool['price'] <= current_price:
                signal_type = 'LONG'
                score += 4
                
                if nearest_pool['strength'] > 10:
                    score += 2
        
        # SHORT: Barrido de stops por arriba
        above_pools = liquidity_data['pools'].get('above_price', [])
        if above_pools and not signal_type:
            nearest_pool = min(above_pools, key=lambda x: abs(x['price'] - current_price))
            
            if recent_high >= nearest_pool['price'] >= current_price:
                signal_type = 'SHORT'
                score += 4
                
                if nearest_pool['strength'] > 10:
                    score += 2
        
        if score >= self.min_score and signal_type:
            return {
                'ticker': ticker,
                'type': signal_type,
                'score': score,
                'entry_price': current_price,
                'stop_loss': nearest_pool['price'] * 0.98 if signal_type == 'LONG' else nearest_pool['price'] * 1.02,
                'take_profit': current_price * (1 + self.take_profit) if signal_type == 'LONG' else current_price * (1 - self.take_profit),
                'strategy': self.name
            }
        
        return None

class GridTradingStrategy(TradingStrategy):
    """Estrategia de grid trading para mercados laterales"""
    
    def __init__(self):
        super().__init__("Grid Trading")
        self.min_score = 3
        self.take_profit = 0.015  # 1.5% por nivel
        self.stop_loss = 0.05     # 5% stop global
        self.grid_levels = 5
    
    def generate_signal(self, df: pd.DataFrame, ticker: str) -> Optional[Dict]:
        if len(df) < 50:
            return None
        
        # Detectar rango
        recent_high = df['High'].tail(20).max() if 'High' in df.columns else df['Close'].tail(20).max()
        recent_low = df['Low'].tail(20).min() if 'Low' in df.columns else df['Close'].tail(20).min()
        range_size = recent_high - recent_low
        range_pct = range_size / recent_low
        
        # Solo operar en rangos definidos (no tendencias fuertes)
        if range_pct < 0.05 or range_pct > 0.15:
            return None
        
        current_price = df['Close'].iloc[-1]
        
        # Calcular niveles de grid
        grid_size = range_size / self.grid_levels
        current_level = int((current_price - recent_low) / grid_size)
        
        score = self.calculate_score(df)
        signal_type = None
        
        # LONG: En niveles bajos del grid
        if current_level <= 1:
            signal_type = 'LONG'
            score += 3
        
        # SHORT: En niveles altos del grid
        elif current_level >= self.grid_levels - 1:
            signal_type = 'SHORT'
            score += 3
        
        if score >= self.min_score and signal_type:
            # Target: siguiente nivel del grid
            if signal_type == 'LONG':
                target = recent_low + (grid_size * (current_level + 1.5))
            else:
                target = recent_low + (grid_size * (current_level - 1.5))
            
            return {
                'ticker': ticker,
                'type': signal_type,
                'score': score,
                'entry_price': current_price,
                'stop_loss': recent_low * 0.98 if signal_type == 'LONG' else recent_high * 1.02,
                'take_profit': target,
                'strategy': self.name
            }
        
        return None

class BacktestEngine:
    """Motor principal de backtesting"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.strategies = {
            'Momentum': MomentumStrategy(),
            'Mean Reversion': MeanReversionStrategy(),
            'Breakout': BreakoutStrategy(),
            'Scalping': ScalpingStrategy(),
            'Liquidity Hunt': LiquidityHuntStrategy(),
            'Grid Trading': GridTradingStrategy()
        }
        self.results = []
        self.trades = []
    
    def run_backtest(self, 
                     tickers: List[str], 
                     strategies: List[str],
                     start_date: datetime,
                     end_date: datetime,
                     position_size: float = 0.1,  # 10% del capital por trade
                     max_positions: int = 5) -> Dict:
        """
        Ejecuta backtesting con las estrategias seleccionadas
        """
        
        print(f"🚀 Iniciando Backtesting")
        print(f"📊 Tickers: {len(tickers)}")
        print(f"🎯 Estrategias: {strategies}")
        print(f"📅 Período: {start_date.date()} a {end_date.date()}")
        
        # Obtener datos históricos
        all_data = {}
        for ticker in tickers:
            print(f"📥 Descargando {ticker}...")
            df = yf.download(ticker, start=start_date, end=end_date, interval='1h', progress=False)
            if not df.empty:
                df = calcular_indicadores(df)
                all_data[ticker] = df
        
        print(f"✅ Datos obtenidos para {len(all_data)} tickers")
        
        # Simular día por día
        capital = self.initial_capital
        open_positions = {}
        equity_curve = []
        
        # Obtener todas las fechas únicas
        all_dates = set()
        for df in all_data.values():
            all_dates.update(df.index.date)
        all_dates = sorted(list(all_dates))
        
        for current_date in all_dates:
            daily_pnl = 0
            
            # 1. Verificar salidas de posiciones abiertas
            for position_id in list(open_positions.keys()):
                position = open_positions[position_id]
                ticker = position['ticker']
                
                if ticker in all_data:
                    df = all_data[ticker]
                    day_data = df[df.index.date == current_date]
                    
                    if not day_data.empty:
                        high = day_data['High'].max()
                        low = day_data['Low'].min()
                        close = day_data['Close'].iloc[-1]
                        
                        exit_price = None
                        exit_reason = None
                        
                        # Verificar TP/SL
                        if position['type'] == 'LONG':
                            if high >= position['take_profit']:
                                exit_price = position['take_profit']
                                exit_reason = 'TP'
                            elif low <= position['stop_loss']:
                                exit_price = position['stop_loss']
                                exit_reason = 'SL'
                        else:  # SHORT
                            if low <= position['take_profit']:
                                exit_price = position['take_profit']
                                exit_reason = 'TP'
                            elif high >= position['stop_loss']:
                                exit_price = position['stop_loss']
                                exit_reason = 'SL'
                        
                        # Salida por tiempo (opcional)
                        days_held = (current_date - position['entry_date'].date()).days
                        if not exit_price and days_held > 5:
                            exit_price = close
                            exit_reason = 'TIME'
                        
                        if exit_price:
                            # Calcular PnL
                            if position['type'] == 'LONG':
                                profit_pct = (exit_price - position['entry_price']) / position['entry_price']
                            else:
                                profit_pct = (position['entry_price'] - exit_price) / position['entry_price']
                            
                            profit_pct *= position['leverage']
                            profit_usd = position['size'] * profit_pct
                            
                            # Registrar trade
                            trade = TradeResult(
                                ticker=ticker,
                                strategy=position['strategy'],
                                entry_date=position['entry_date'],
                                exit_date=datetime.combine(current_date, datetime.min.time()),
                                entry_price=position['entry_price'],
                                exit_price=exit_price,
                                direction=position['type'],
                                profit_pct=profit_pct * 100,
                                profit_usd=profit_usd,
                                exit_reason=exit_reason,
                                score=position['score']
                            )
                            self.trades.append(trade)
                            
                            # Actualizar capital
                            capital += profit_usd
                            daily_pnl += profit_usd
                            
                            # Cerrar posición
                            del open_positions[position_id]
                            
                            print(f"{'✅' if profit_pct > 0 else '❌'} {current_date} | "
                                 f"{exit_reason} {ticker} {position['type']} | "
                                 f"PnL: {profit_pct*100:+.2f}% (${profit_usd:+.2f})")
            
            # 2. Buscar nuevas entradas
            if len(open_positions) < max_positions:
                for ticker in all_data:
                    # No abrir múltiples posiciones en el mismo ticker
                    ticker_positions = [p for p in open_positions.values() if p['ticker'] == ticker]
                    if ticker_positions:
                        continue
                    
                    df = all_data[ticker]
                    day_data = df[df.index.date <= current_date]
                    
                    if len(day_data) >= 200:  # Suficientes datos históricos
                        # Probar cada estrategia
                        for strategy_name in strategies:
                            if strategy_name in self.strategies:
                                strategy = self.strategies[strategy_name]
                                signal = strategy.generate_signal(day_data, ticker)
                                
                                if signal and len(open_positions) < max_positions:
                                    # Abrir posición
                                    position_id = f"{ticker}_{current_date}_{strategy_name}"
                                    size = capital * position_size
                                    
                                    open_positions[position_id] = {
                                        'ticker': ticker,
                                        'strategy': strategy_name,
                                        'type': signal['type'],
                                        'entry_date': datetime.combine(current_date, datetime.min.time()),
                                        'entry_price': signal['entry_price'],
                                        'stop_loss': signal['stop_loss'],
                                        'take_profit': signal['take_profit'],
                                        'score': signal['score'],
                                        'size': size,
                                        'leverage': strategy.leverage
                                    }
                                    
                                    emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
                                    print(f"{emoji} {current_date} | ENTRADA {ticker} {signal['type']} | "
                                         f"Estrategia: {strategy_name} | Score: {signal['score']}")
                                    
                                    break  # Solo una estrategia por ticker
            
            # Guardar equity curve
            equity_curve.append({
                'date': current_date,
                'capital': capital,
                'daily_pnl': daily_pnl,
                'open_positions': len(open_positions)
            })
        
        # Calcular métricas finales
        return self.calculate_metrics(equity_curve)
    
    def calculate_metrics(self, equity_curve: List[Dict]) -> Dict:
        """Calcula métricas de performance"""
        
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'equity_curve': equity_curve,
                'trades_by_strategy': {},
                'performance_by_ticker': {}
            }
        
        # Métricas básicas
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.profit_pct > 0]
        losing_trades = [t for t in self.trades if t.profit_pct <= 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        
        # Profit Factor
        gross_profit = sum(t.profit_usd for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.profit_usd for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Returns
        final_capital = equity_curve[-1]['capital'] if equity_curve else self.initial_capital
        total_return = ((final_capital / self.initial_capital) - 1) * 100
        
        # Sharpe Ratio
        if len(equity_curve) > 1:
            returns = []
            for i in range(1, len(equity_curve)):
                daily_return = (equity_curve[i]['capital'] / equity_curve[i-1]['capital']) - 1
                returns.append(daily_return)
            
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Drawdown
        peak = self.initial_capital
        max_drawdown = 0
        for point in equity_curve:
            if point['capital'] > peak:
                peak = point['capital']
            drawdown = ((peak - point['capital']) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Promedios
        avg_win = np.mean([t.profit_pct for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit_pct for t in losing_trades]) if losing_trades else 0
        
        # Mejores y peores
        best_trade = max(self.trades, key=lambda t: t.profit_pct).profit_pct if self.trades else 0
        worst_trade = min(self.trades, key=lambda t: t.profit_pct).profit_pct if self.trades else 0
        
        # Análisis por estrategia
        trades_by_strategy = {}
        for trade in self.trades:
            if trade.strategy not in trades_by_strategy:
                trades_by_strategy[trade.strategy] = {
                    'total': 0,
                    'wins': 0,
                    'total_pnl': 0
                }
            trades_by_strategy[trade.strategy]['total'] += 1
            if trade.profit_pct > 0:
                trades_by_strategy[trade.strategy]['wins'] += 1
            trades_by_strategy[trade.strategy]['total_pnl'] += trade.profit_usd
        
        # Win rate por estrategia
        for strategy in trades_by_strategy:
            total = trades_by_strategy[strategy]['total']
            wins = trades_by_strategy[strategy]['wins']
            trades_by_strategy[strategy]['win_rate'] = (wins / total * 100) if total > 0 else 0
        
        # Análisis por ticker
        performance_by_ticker = {}
        for trade in self.trades:
            if trade.ticker not in performance_by_ticker:
                performance_by_ticker[trade.ticker] = {
                    'total': 0,
                    'wins': 0,
                    'total_pnl': 0
                }
            performance_by_ticker[trade.ticker]['total'] += 1
            if trade.profit_pct > 0:
                performance_by_ticker[trade.ticker]['wins'] += 1
            performance_by_ticker[trade.ticker]['total_pnl'] += trade.profit_usd
        
        return {
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'equity_curve': equity_curve,
            'trades': self.trades,
            'trades_by_strategy': trades_by_strategy,
            'performance_by_ticker': performance_by_ticker
        }

def main():
    """Función principal de prueba"""
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║          SISTEMA AVANZADO DE BACKTESTING v2.0                   ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Configuración
    tickers = [
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
        'ADA-USD', 'AVAX-USD', 'MATIC-USD', 'LINK-USD', 'DOT-USD'
    ]
    
    strategies = ['Momentum', 'Mean Reversion', 'Breakout']
    
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()
    
    # Ejecutar backtest
    engine = BacktestEngine(initial_capital=10000)
    results = engine.run_backtest(
        tickers=tickers,
        strategies=strategies,
        start_date=start_date,
        end_date=end_date,
        position_size=0.1,  # 10% por trade
        max_positions=5
    )
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("📊 RESULTADOS DEL BACKTESTING")
    print("="*60)
    
    print(f"\n💰 Capital Inicial: $10,000")
    print(f"💰 Capital Final: ${results['equity_curve'][-1]['capital']:,.2f}")
    print(f"📈 Retorno Total: {results['total_return']:+.2f}%")
    
    print(f"\n📊 MÉTRICAS DE PERFORMANCE:")
    print(f"• Total Trades: {results['total_trades']}")
    print(f"• Win Rate: {results['win_rate']:.2f}%")
    print(f"• Profit Factor: {results['profit_factor']:.2f}")
    print(f"• Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"• Max Drawdown: -{results['max_drawdown']:.2f}%")
    print(f"• Promedio Ganancia: {results['avg_win']:+.2f}%")
    print(f"• Promedio Pérdida: {results['avg_loss']:+.2f}%")
    print(f"• Mejor Trade: {results['best_trade']:+.2f}%")
    print(f"• Peor Trade: {results['worst_trade']:+.2f}%")
    
    print(f"\n🎯 PERFORMANCE POR ESTRATEGIA:")
    for strategy, stats in results['trades_by_strategy'].items():
        print(f"\n{strategy}:")
        print(f"  • Trades: {stats['total']}")
        print(f"  • Win Rate: {stats['win_rate']:.1f}%")
        print(f"  • PnL Total: ${stats['total_pnl']:+,.2f}")
    
    print(f"\n📊 TOP 5 TICKERS POR PERFORMANCE:")
    sorted_tickers = sorted(results['performance_by_ticker'].items(), 
                          key=lambda x: x[1]['total_pnl'], 
                          reverse=True)[:5]
    
    for ticker, stats in sorted_tickers:
        print(f"{ticker}: ${stats['total_pnl']:+,.2f} ({stats['total']} trades)")
    
    # Guardar resultados
    with open('backtest_results.json', 'w') as f:
        # Convertir trades a dict para serialización
        results_copy = results.copy()
        results_copy['trades'] = [
            {
                'ticker': t.ticker,
                'strategy': t.strategy,
                'entry_date': t.entry_date.isoformat(),
                'exit_date': t.exit_date.isoformat(),
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'direction': t.direction,
                'profit_pct': t.profit_pct,
                'profit_usd': t.profit_usd,
                'exit_reason': t.exit_reason,
                'score': t.score
            }
            for t in results['trades']
        ]
        
        # Convertir dates en equity_curve
        results_copy['equity_curve'] = [
            {
                'date': point['date'].isoformat(),
                'capital': point['capital'],
                'daily_pnl': point['daily_pnl'],
                'open_positions': point['open_positions']
            }
            for point in results['equity_curve']
        ]
        
        json.dump(results_copy, f, indent=2, default=str)
    
    print("\n💾 Resultados guardados en backtest_results.json")

if __name__ == "__main__":
    main()