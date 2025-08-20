#!/usr/bin/env python3
"""
Sistema de Backtesting para el Sistema Filosófico de Trading
Analiza períodos de 7 días en diferentes ventanas temporales
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import json
import warnings
warnings.filterwarnings('ignore')

@dataclass
class Trade:
    """Representa un trade ejecutado en backtesting"""
    symbol: str
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    action: str  # BUY o SELL
    stop_loss: float
    take_profit: float
    philosophers: List[str]
    confidence: float
    market_regime: str
    status: str  # OPEN, WIN, LOSS, BREAKEVEN
    pnl: float = 0.0
    pnl_percent: float = 0.0
    holding_days: int = 0
    exit_reason: str = ""

@dataclass
class BacktestPeriod:
    """Período de backtesting"""
    start_date: datetime
    end_date: datetime
    symbol: str
    trades: List[Trade] = field(default_factory=list)
    total_return: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

class PhilosophicalBacktester:
    """Sistema de backtesting para señales filosóficas"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.position_size = 0.02  # 2% del capital por trade
        self.min_consensus = 0.65
        self.commission = 0.001  # 0.1% comisión
        
        # Configuración de filósofos simplificada para backtesting
        self.philosophers = ['Socrates', 'Aristoteles', 'Platon', 'Nietzsche', 
                            'Kant', 'Descartes', 'Confucio', 'SunTzu']
        
        # Régimenes y sus pesos
        self.regime_weights = {
            'TRENDING': {
                'Aristoteles': 1.3, 'Descartes': 1.2, 'SunTzu': 1.1,
                'Kant': 1.0, 'Platon': 0.9, 'Nietzsche': 0.8,
                'Socrates': 0.6, 'Confucio': 0.7
            },
            'RANGING': {
                'Socrates': 1.4, 'Confucio': 1.3, 'Platon': 1.0,
                'Kant': 1.0, 'Descartes': 0.9, 'Aristoteles': 0.7,
                'Nietzsche': 0.8, 'SunTzu': 0.9
            },
            'VOLATILE': {
                'SunTzu': 1.4, 'Nietzsche': 1.3, 'Descartes': 1.2,
                'Kant': 1.1, 'Aristoteles': 0.8, 'Platon': 0.7,
                'Socrates': 0.6, 'Confucio': 0.5
            }
        }
    
    def detect_market_regime(self, df: pd.DataFrame) -> str:
        """Detecta el régimen del mercado"""
        # ATR para volatilidad
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        atr = ranges.max(axis=1).rolling(14).mean()
        
        current_atr = atr.iloc[-1]
        avg_atr = atr.rolling(50).mean().iloc[-1]
        volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1
        
        # EMAs para tendencia
        ema_20 = df['Close'].ewm(span=20).mean()
        ema_50 = df['Close'].ewm(span=50).mean()
        
        # Determinar régimen
        if volatility_ratio > 1.5:
            return 'VOLATILE'
        elif abs(ema_20.iloc[-1] - ema_50.iloc[-1]) / ema_50.iloc[-1] > 0.01:
            return 'TRENDING'
        else:
            return 'RANGING'
    
    def get_philosophical_signal(self, df: pd.DataFrame, date_idx: int) -> Optional[Dict]:
        """Genera señal filosófica para una fecha específica"""
        
        if date_idx < 50:  # Necesitamos historia para indicadores
            return None
        
        # Subset de datos hasta la fecha actual
        df_subset = df.iloc[:date_idx+1]
        current = df_subset.iloc[-1]
        
        # Detectar régimen
        regime = self.detect_market_regime(df_subset)
        
        # Calcular indicadores
        delta = df_subset['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        ema_9 = df_subset['Close'].ewm(span=9).mean().iloc[-1]
        ema_21 = df_subset['Close'].ewm(span=21).mean().iloc[-1]
        
        bb_middle = df_subset['Close'].rolling(20).mean().iloc[-1]
        bb_std = df_subset['Close'].rolling(20).std().iloc[-1]
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        # Obtener votos de filósofos
        votes = {}
        
        # Socrates - Mean reversion
        if current['Close'] <= bb_lower and rsi < 35:
            votes['Socrates'] = ('BUY', 0.7)
        elif current['Close'] >= bb_upper and rsi > 65:
            votes['Socrates'] = ('SELL', 0.7)
        
        # Aristoteles - Trend following
        if ema_9 > ema_21 and rsi < 70:
            votes['Aristoteles'] = ('BUY', 0.65)
        elif ema_9 < ema_21 and rsi > 30:
            votes['Aristoteles'] = ('SELL', 0.65)
        
        # Nietzsche - Contrarian
        if rsi < 25:
            votes['Nietzsche'] = ('BUY', 0.8)
        elif rsi > 75:
            votes['Nietzsche'] = ('SELL', 0.8)
        
        # Platon - Patterns
        support = df_subset['Low'].rolling(20).min().iloc[-1]
        resistance = df_subset['High'].rolling(20).max().iloc[-1]
        
        if abs(current['Close'] - support) / support < 0.02:
            votes['Platon'] = ('BUY', 0.75)
        elif abs(current['Close'] - resistance) / resistance < 0.02:
            votes['Platon'] = ('SELL', 0.75)
        
        # Kant - Strict rules
        if rsi < 30 and current['Close'] < bb_lower:
            votes['Kant'] = ('BUY', 0.85)
        elif rsi > 70 and current['Close'] > bb_upper:
            votes['Kant'] = ('SELL', 0.85)
        
        # Descartes - Multiple confirmations
        buy_signals = sum([
            rsi < 40,
            current['Close'] < bb_middle,
            ema_9 > ema_21,
            current['Volume'] > df_subset['Volume'].rolling(20).mean().iloc[-1]
        ])
        sell_signals = sum([
            rsi > 60,
            current['Close'] > bb_middle,
            ema_9 < ema_21,
            current['Volume'] > df_subset['Volume'].rolling(20).mean().iloc[-1]
        ])
        
        if buy_signals >= 3:
            votes['Descartes'] = ('BUY', 0.5 + buy_signals * 0.15)
        elif sell_signals >= 3:
            votes['Descartes'] = ('SELL', 0.5 + sell_signals * 0.15)
        
        # Confucio - Balance
        distance_from_middle = (current['Close'] - bb_middle) / bb_middle
        if distance_from_middle < -0.02 and rsi < 45:
            votes['Confucio'] = ('BUY', 0.7)
        elif distance_from_middle > 0.02 and rsi > 55:
            votes['Confucio'] = ('SELL', 0.7)
        
        # SunTzu - Strategic timing
        volume_surge = current['Volume'] > df_subset['Volume'].rolling(20).mean().iloc[-1] * 1.5
        if volume_surge:
            if rsi < 40 and ema_9 > ema_21:
                votes['SunTzu'] = ('BUY', 0.8)
            elif rsi > 60 and ema_9 < ema_21:
                votes['SunTzu'] = ('SELL', 0.8)
        
        if not votes:
            return None
        
        # Aplicar pesos según régimen
        weights = self.regime_weights[regime]
        
        buy_score = 0
        sell_score = 0
        buy_philosophers = []
        sell_philosophers = []
        
        for philosopher, (vote, confidence) in votes.items():
            weighted_confidence = confidence * weights.get(philosopher, 1.0)
            
            if vote == 'BUY':
                buy_score += weighted_confidence
                buy_philosophers.append(philosopher)
            else:
                sell_score += weighted_confidence
                sell_philosophers.append(philosopher)
        
        total_score = buy_score + sell_score
        if total_score == 0:
            return None
        
        buy_consensus = buy_score / total_score
        sell_consensus = sell_score / total_score
        
        # Verificar consenso mínimo y número de filósofos
        if buy_consensus >= self.min_consensus and len(buy_philosophers) >= 3:
            action = 'BUY'
            confidence = buy_consensus
            philosophers = buy_philosophers
        elif sell_consensus >= self.min_consensus and len(sell_philosophers) >= 3:
            action = 'SELL'
            confidence = sell_consensus
            philosophers = sell_philosophers
        else:
            return None
        
        # Calcular stops y targets
        atr = ranges.max(axis=1).rolling(14).mean().iloc[-1]
        
        if action == 'BUY':
            stop_loss = current['Close'] - (atr * 2)
            take_profit = current['Close'] + (atr * 3)
        else:
            stop_loss = current['Close'] + (atr * 2)
            take_profit = current['Close'] - (atr * 3)
        
        return {
            'date': df_subset.index[-1],
            'action': action,
            'price': current['Close'],
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'philosophers': philosophers,
            'regime': regime
        }
    
    def execute_backtest(self, symbol: str, start_date: datetime, 
                        end_date: datetime) -> BacktestPeriod:
        """Ejecuta backtesting para un período específico"""
        
        # Obtener datos históricos
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date - timedelta(days=60), 
                          end=end_date + timedelta(days=1))
        
        if len(df) < 100:
            print(f"⚠️ Datos insuficientes para {symbol} en período {start_date.date()} a {end_date.date()}")
            return BacktestPeriod(start_date, end_date, symbol)
        
        # Inicializar período
        period = BacktestPeriod(start_date, end_date, symbol)
        
        # Variables de tracking
        capital = self.initial_capital
        open_trade = None
        equity_curve = []
        
        # Iterar por cada día
        for i in range(len(df)):
            current_date = df.index[i]
            
            # Solo operar dentro del período de backtest
            if current_date < start_date or current_date > end_date:
                continue
            
            current_price = df.iloc[i]['Close']
            
            # Verificar trades abiertos
            if open_trade:
                # Verificar stop loss
                if open_trade.action == 'BUY':
                    if current_price <= open_trade.stop_loss:
                        open_trade.exit_date = current_date
                        open_trade.exit_price = open_trade.stop_loss
                        open_trade.status = 'LOSS'
                        open_trade.exit_reason = 'Stop Loss'
                        open_trade.pnl_percent = -2.0  # 2% loss
                    elif current_price >= open_trade.take_profit:
                        open_trade.exit_date = current_date
                        open_trade.exit_price = open_trade.take_profit
                        open_trade.status = 'WIN'
                        open_trade.exit_reason = 'Take Profit'
                        open_trade.pnl_percent = 3.0  # 3% win (R:R 1.5)
                else:  # SELL
                    if current_price >= open_trade.stop_loss:
                        open_trade.exit_date = current_date
                        open_trade.exit_price = open_trade.stop_loss
                        open_trade.status = 'LOSS'
                        open_trade.exit_reason = 'Stop Loss'
                        open_trade.pnl_percent = -2.0
                    elif current_price <= open_trade.take_profit:
                        open_trade.exit_date = current_date
                        open_trade.exit_price = open_trade.take_profit
                        open_trade.status = 'WIN'
                        open_trade.exit_reason = 'Take Profit'
                        open_trade.pnl_percent = 3.0
                
                # Si se cerró el trade
                if open_trade.exit_date:
                    open_trade.holding_days = (open_trade.exit_date - open_trade.entry_date).days
                    open_trade.pnl = capital * (open_trade.pnl_percent / 100)
                    capital += open_trade.pnl
                    period.trades.append(open_trade)
                    open_trade = None
            
            # Buscar nueva señal si no hay trade abierto
            if not open_trade:
                signal = self.get_philosophical_signal(df, i)
                
                if signal:
                    open_trade = Trade(
                        symbol=symbol,
                        entry_date=current_date,
                        exit_date=None,
                        entry_price=signal['price'],
                        exit_price=None,
                        action=signal['action'],
                        stop_loss=signal['stop_loss'],
                        take_profit=signal['take_profit'],
                        philosophers=signal['philosophers'],
                        confidence=signal['confidence'],
                        market_regime=signal['regime'],
                        status='OPEN'
                    )
            
            equity_curve.append(capital)
        
        # Cerrar trade abierto al final del período
        if open_trade:
            open_trade.exit_date = end_date
            open_trade.exit_price = df.iloc[-1]['Close']
            open_trade.status = 'BREAKEVEN'
            open_trade.exit_reason = 'End of Period'
            
            if open_trade.action == 'BUY':
                open_trade.pnl_percent = ((open_trade.exit_price - open_trade.entry_price) / 
                                         open_trade.entry_price) * 100
            else:
                open_trade.pnl_percent = ((open_trade.entry_price - open_trade.exit_price) / 
                                         open_trade.entry_price) * 100
            
            open_trade.pnl = capital * (open_trade.pnl_percent / 100)
            open_trade.holding_days = (open_trade.exit_date - open_trade.entry_date).days
            capital += open_trade.pnl
            period.trades.append(open_trade)
        
        # Calcular métricas
        if period.trades:
            period.total_trades = len(period.trades)
            period.winning_trades = len([t for t in period.trades if t.status == 'WIN'])
            period.losing_trades = len([t for t in period.trades if t.status == 'LOSS'])
            
            if period.total_trades > 0:
                period.win_rate = period.winning_trades / period.total_trades * 100
            
            wins = [t.pnl for t in period.trades if t.status == 'WIN']
            losses = [abs(t.pnl) for t in period.trades if t.status == 'LOSS']
            
            if wins:
                period.avg_win = np.mean(wins)
            if losses:
                period.avg_loss = np.mean(losses)
            
            if period.avg_loss > 0:
                period.profit_factor = period.avg_win / period.avg_loss
            
            period.total_return = ((capital - self.initial_capital) / self.initial_capital) * 100
            
            # Max drawdown
            equity_array = np.array(equity_curve)
            running_max = np.maximum.accumulate(equity_array)
            drawdown = (equity_array - running_max) / running_max * 100
            period.max_drawdown = np.min(drawdown)
            
            # Sharpe ratio simplificado
            if len(equity_curve) > 1:
                returns = np.diff(equity_array) / equity_array[:-1]
                if np.std(returns) > 0:
                    period.sharpe_ratio = (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252))
        
        return period
    
    def run_multiple_periods(self, symbol: str, periods: List[Tuple[datetime, datetime]]) -> List[BacktestPeriod]:
        """Ejecuta backtesting en múltiples períodos"""
        
        results = []
        
        for start_date, end_date in periods:
            print(f"\n📊 Backtesting {symbol} del {start_date.date()} al {end_date.date()}")
            period_result = self.execute_backtest(symbol, start_date, end_date)
            results.append(period_result)
            
            # Mostrar resumen
            print(f"   Trades: {period_result.total_trades}")
            print(f"   Win Rate: {period_result.win_rate:.1f}%")
            print(f"   Return: {period_result.total_return:.2f}%")
            print(f"   Max DD: {period_result.max_drawdown:.2f}%")
        
        return results


def generate_test_periods():
    """Genera períodos de prueba de 7 días en 2024"""
    
    periods = []
    
    # Usar datos de 2024 (datos históricos disponibles)
    # 12 períodos de 7 días, uno cada mes
    test_dates = [
        (datetime(2024, 12, 1), datetime(2024, 12, 8)),
        (datetime(2024, 11, 15), datetime(2024, 11, 22)),
        (datetime(2024, 11, 1), datetime(2024, 11, 8)),
        (datetime(2024, 10, 15), datetime(2024, 10, 22)),
        (datetime(2024, 10, 1), datetime(2024, 10, 8)),
        (datetime(2024, 9, 15), datetime(2024, 9, 22)),
        (datetime(2024, 9, 1), datetime(2024, 9, 8)),
        (datetime(2024, 8, 15), datetime(2024, 8, 22)),
        (datetime(2024, 8, 1), datetime(2024, 8, 8)),
        (datetime(2024, 7, 15), datetime(2024, 7, 22)),
        (datetime(2024, 7, 1), datetime(2024, 7, 8)),
        (datetime(2024, 6, 15), datetime(2024, 6, 22)),
    ]
    
    return test_dates


def analyze_macro_results(all_results: Dict[str, List[BacktestPeriod]]):
    """Analiza resultados macro de todos los símbolos"""
    
    print("\n" + "="*80)
    print(" ANÁLISIS MACRO DE RESULTADOS ".center(80))
    print("="*80)
    
    # Estadísticas por símbolo
    symbol_stats = {}
    
    for symbol, periods in all_results.items():
        total_trades = sum(p.total_trades for p in periods)
        total_wins = sum(p.winning_trades for p in periods)
        total_losses = sum(p.losing_trades for p in periods)
        avg_return = np.mean([p.total_return for p in periods])
        best_return = max(p.total_return for p in periods)
        worst_return = min(p.total_return for p in periods)
        avg_win_rate = np.mean([p.win_rate for p in periods if p.total_trades > 0])
        avg_sharpe = np.mean([p.sharpe_ratio for p in periods if p.sharpe_ratio != 0])
        
        symbol_stats[symbol] = {
            'total_trades': total_trades,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'avg_return': avg_return,
            'best_return': best_return,
            'worst_return': worst_return,
            'avg_win_rate': avg_win_rate,
            'avg_sharpe': avg_sharpe
        }
    
    # Tabla de resultados por símbolo
    print("\n📊 RESUMEN POR SÍMBOLO")
    print("-" * 80)
    print(f"{'Símbolo':<10} {'Trades':<8} {'Win%':<8} {'Avg Ret%':<10} {'Best%':<10} {'Worst%':<10} {'Sharpe':<8}")
    print("-" * 80)
    
    for symbol, stats in symbol_stats.items():
        print(f"{symbol:<10} {stats['total_trades']:<8} "
              f"{stats['avg_win_rate']:<8.1f} {stats['avg_return']:<10.2f} "
              f"{stats['best_return']:<10.2f} {stats['worst_return']:<10.2f} "
              f"{stats['avg_sharpe']:<8.2f}")
    
    # Análisis de filósofos
    print("\n🎓 ANÁLISIS POR FILÓSOFO")
    print("-" * 80)
    
    philosopher_performance = {}
    
    for symbol, periods in all_results.items():
        for period in periods:
            for trade in period.trades:
                for philosopher in trade.philosophers:
                    if philosopher not in philosopher_performance:
                        philosopher_performance[philosopher] = {
                            'trades': 0,
                            'wins': 0,
                            'losses': 0,
                            'total_pnl': 0
                        }
                    
                    philosopher_performance[philosopher]['trades'] += 1
                    if trade.status == 'WIN':
                        philosopher_performance[philosopher]['wins'] += 1
                    elif trade.status == 'LOSS':
                        philosopher_performance[philosopher]['losses'] += 1
                    philosopher_performance[philosopher]['total_pnl'] += trade.pnl_percent
    
    print(f"{'Filósofo':<15} {'Trades':<10} {'Win%':<10} {'Avg PnL%':<12}")
    print("-" * 80)
    
    for philosopher, stats in sorted(philosopher_performance.items(), 
                                    key=lambda x: x[1]['total_pnl'], reverse=True):
        if stats['trades'] > 0:
            win_rate = (stats['wins'] / stats['trades']) * 100
            avg_pnl = stats['total_pnl'] / stats['trades']
            print(f"{philosopher:<15} {stats['trades']:<10} {win_rate:<10.1f} {avg_pnl:<12.2f}")
    
    # Análisis por régimen de mercado
    print("\n📈 ANÁLISIS POR RÉGIMEN DE MERCADO")
    print("-" * 80)
    
    regime_performance = {}
    
    for symbol, periods in all_results.items():
        for period in periods:
            for trade in period.trades:
                regime = trade.market_regime
                if regime not in regime_performance:
                    regime_performance[regime] = {
                        'trades': 0,
                        'wins': 0,
                        'losses': 0,
                        'total_pnl': 0
                    }
                
                regime_performance[regime]['trades'] += 1
                if trade.status == 'WIN':
                    regime_performance[regime]['wins'] += 1
                elif trade.status == 'LOSS':
                    regime_performance[regime]['losses'] += 1
                regime_performance[regime]['total_pnl'] += trade.pnl_percent
    
    print(f"{'Régimen':<15} {'Trades':<10} {'Win%':<10} {'Avg PnL%':<12}")
    print("-" * 80)
    
    for regime, stats in regime_performance.items():
        if stats['trades'] > 0:
            win_rate = (stats['wins'] / stats['trades']) * 100
            avg_pnl = stats['total_pnl'] / stats['trades']
            print(f"{regime:<15} {stats['trades']:<10} {win_rate:<10.1f} {avg_pnl:<12.2f}")
    
    # Estadísticas generales
    print("\n📊 ESTADÍSTICAS GENERALES")
    print("-" * 80)
    
    total_all_trades = sum(s['total_trades'] for s in symbol_stats.values())
    total_all_wins = sum(s['total_wins'] for s in symbol_stats.values())
    total_all_losses = sum(s['total_losses'] for s in symbol_stats.values())
    
    if total_all_trades > 0:
        overall_win_rate = (total_all_wins / total_all_trades) * 100
        print(f"Total de trades ejecutados: {total_all_trades}")
        print(f"Win rate general: {overall_win_rate:.1f}%")
        print(f"Trades ganadores: {total_all_wins}")
        print(f"Trades perdedores: {total_all_losses}")
        
        avg_return_all = np.mean([s['avg_return'] for s in symbol_stats.values()])
        print(f"Retorno promedio por período: {avg_return_all:.2f}%")
        
        best_symbol = max(symbol_stats.items(), key=lambda x: x[1]['avg_return'])
        worst_symbol = min(symbol_stats.items(), key=lambda x: x[1]['avg_return'])
        
        print(f"\nMejor símbolo: {best_symbol[0]} ({best_symbol[1]['avg_return']:.2f}% promedio)")
        print(f"Peor símbolo: {worst_symbol[0]} ({worst_symbol[1]['avg_return']:.2f}% promedio)")
    
    # Guardar resultados
    results_summary = {
        'timestamp': datetime.now().isoformat(),
        'symbol_stats': symbol_stats,
        'philosopher_performance': philosopher_performance,
        'regime_performance': regime_performance,
        'overall_stats': {
            'total_trades': total_all_trades,
            'total_wins': total_all_wins,
            'total_losses': total_all_losses,
            'overall_win_rate': overall_win_rate if total_all_trades > 0 else 0
        }
    }
    
    with open('backtest_results_macro.json', 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print("\n💾 Resultados guardados en backtest_results_macro.json")
    
    return results_summary


def main():
    """Función principal de backtesting"""
    
    print("\n" + "="*80)
    print(" BACKTESTING SISTEMA FILOSÓFICO - ANÁLISIS MULTI-PERÍODO ".center(80))
    print("="*80)
    
    # Símbolos a analizar
    symbols = [
        'BTC-USD',
        'ETH-USD',
        'SOL-USD',
        'DOGE-USD',
        'ADA-USD',
        'AVAX-USD',
        'LINK-USD',
        'DOT-USD'
    ]
    
    # Generar períodos de prueba
    test_periods = generate_test_periods()
    
    print(f"\n📅 Analizando {len(test_periods)} períodos de 7 días cada uno")
    print(f"📊 Para {len(symbols)} símbolos diferentes")
    print(f"⏰ Total de backtests: {len(symbols) * len(test_periods)}")
    
    # Inicializar backtester
    backtester = PhilosophicalBacktester(initial_capital=10000)
    
    # Ejecutar backtesting para cada símbolo
    all_results = {}
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f" Analizando {symbol} ".center(60))
        print(f"{'='*60}")
        
        symbol_results = backtester.run_multiple_periods(symbol, test_periods)
        all_results[symbol] = symbol_results
    
    # Análisis macro
    macro_analysis = analyze_macro_results(all_results)
    
    print("\n" + "="*80)
    print(" BACKTESTING COMPLETADO ".center(80))
    print("="*80)


if __name__ == "__main__":
    main()