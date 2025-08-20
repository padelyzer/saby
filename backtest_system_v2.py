#!/usr/bin/env python3
"""
Backtest System V2 - Sistema mejorado de backtesting
Con integración a Binance y optimizaciones de rendimiento
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

from binance_data_fetcher import BinanceDataFetcher
from cache_manager import cache_manager, cached, BinanceCache, performance_monitor
from error_handler import error_handler, TradingErrorContext
from signal_validator import signal_validator
from paper_trading_enhanced import PaperTradingEnhanced
from trading_config import get_asset_type, get_strategy_config, get_recommended_strategies

class BacktestSystemV2:
    """
    Sistema avanzado de backtesting con:
    - Datos históricos de Binance
    - Simulación realista con slippage y comisiones
    - Análisis detallado de performance
    - Optimización de parámetros
    """
    
    def __init__(self):
        self.data_fetcher = BinanceDataFetcher()
        self.results = []
        self.best_parameters = {}
        
        # Configuración de backtest
        self.config = {
            'initial_capital': 10000,
            'commission': 0.0004,  # 0.04% Binance
            'slippage': 0.0005,    # 0.05% slippage estimado
            'min_data_points': 100,
            'use_cache': True
        }
    
    @cached(ttl=3600)  # Cache por 1 hora
    def fetch_historical_data(self, symbol: str, interval: str, days_back: int) -> pd.DataFrame:
        """Obtiene datos históricos con caché"""
        
        start_timer = performance_monitor.start_timer("fetch_historical_data")
        
        try:
            # Calcular límite basado en días
            intervals_per_day = {
                '1m': 1440, '5m': 288, '15m': 96, '30m': 48,
                '1h': 24, '4h': 6, '1d': 1
            }
            
            limit = min(days_back * intervals_per_day.get(interval, 24), 1000)
            
            # Obtener datos
            df = self.data_fetcher.get_klines(symbol, interval, limit)
            
            if not df.empty:
                # Calcular indicadores
                df = self.data_fetcher.calculate_indicators(df)
            
            performance_monitor.end_timer("fetch_historical_data", start_timer)
            return df
            
        except Exception as e:
            error_handler.handle_error(e, context={'symbol': symbol, 'interval': interval})
            performance_monitor.end_timer("fetch_historical_data", start_timer)
            return pd.DataFrame()
    
    def generate_signals(self, df: pd.DataFrame, strategy: str = "momentum", symbol: str = None) -> pd.DataFrame:
        """Genera señales de trading basadas en la estrategia y tipo de activo"""
        
        if df.empty or len(df) < self.config['min_data_points']:
            return df
        
        df['signal'] = 0
        df['position'] = 0
        
        # Obtener configuración específica para el activo
        if symbol:
            asset_type = get_asset_type(symbol)
            config = get_strategy_config(strategy, symbol)
        else:
            asset_type = 'LARGE_CAP'  # Default
            config = {}
        
        if strategy == "momentum":
            # Configuración adaptativa por tipo de activo
            rsi_buy = config.get('rsi_buy', 30)
            rsi_sell = config.get('rsi_sell', 70)
            volume_mult = config.get('volume_multiplier', 1.5)
            
            # Estrategia de momentum con RSI y MACD
            df['signal'] = np.where(
                (df['RSI'] < rsi_buy) & (df['MACD'] > df['Signal']) & 
                (df['Close'] > df['EMA_20']) & (df['Volume'] > df['Volume_SMA'] * volume_mult), 1, 0
            )
            df['signal'] = np.where(
                (df['RSI'] > rsi_sell) & (df['MACD'] < df['Signal']) & 
                (df['Close'] < df['EMA_20']) & (df['Volume'] > df['Volume_SMA'] * volume_mult), -1, df['signal']
            )
            
        elif strategy == "mean_reversion":
            # Configuración adaptativa por tipo de activo
            bb_std = config.get('bb_std', 2.0)
            rsi_oversold = config.get('rsi_oversold', 35)
            rsi_overbought = config.get('rsi_overbought', 65)
            
            # Recalcular Bollinger Bands con std específico
            bb_window = 20
            bb_center = df['Close'].rolling(bb_window).mean()
            bb_std_dev = df['Close'].rolling(bb_window).std()
            df['BB_Upper_Custom'] = bb_center + (bb_std_dev * bb_std)
            df['BB_Lower_Custom'] = bb_center - (bb_std_dev * bb_std)
            
            # Estrategia de reversión a la media con Bollinger Bands
            df['signal'] = np.where(
                (df['Close'] < df['BB_Lower_Custom']) & (df['RSI'] < rsi_oversold), 1, 0
            )
            df['signal'] = np.where(
                (df['Close'] > df['BB_Upper_Custom']) & (df['RSI'] > rsi_overbought), -1, df['signal']
            )
            
        elif strategy == "trend_following":
            # Configuración adaptativa por tipo de activo
            ema_fast = config.get('ema_fast', 9)
            ema_medium = config.get('ema_medium', 20)
            ema_slow = config.get('ema_slow', 50)
            volume_mult = config.get('volume_multiplier', 1.3)
            
            # Calcular EMAs específicas
            df[f'EMA_{ema_fast}'] = df['Close'].ewm(span=ema_fast).mean()
            df[f'EMA_{ema_medium}'] = df['Close'].ewm(span=ema_medium).mean()
            df[f'EMA_{ema_slow}'] = df['Close'].ewm(span=ema_slow).mean()
            
            # Estrategia de seguimiento de tendencia
            df['signal'] = np.where(
                (df[f'EMA_{ema_fast}'] > df[f'EMA_{ema_medium}']) & 
                (df[f'EMA_{ema_medium}'] > df[f'EMA_{ema_slow}']) & 
                (df['Volume'] > df['Volume_SMA'] * volume_mult), 1, 0
            )
            df['signal'] = np.where(
                (df[f'EMA_{ema_fast}'] < df[f'EMA_{ema_medium}']) & 
                (df[f'EMA_{ema_medium}'] < df[f'EMA_{ema_slow}']) & 
                (df['Volume'] > df['Volume_SMA'] * volume_mult), -1, df['signal']
            )
            
        elif strategy == "volume_breakout":
            # NUEVA ESTRATEGIA: Volume Profile Breakout
            volume_spike = config.get('volume_spike', 2.0)
            price_breakout = config.get('price_breakout', 0.02)
            confirmation_periods = config.get('confirmation_periods', 3)
            
            # Calcular niveles de soporte y resistencia (últimos 50 períodos)
            window = 50
            df['Resistance'] = df['High'].rolling(window).max()
            df['Support'] = df['Low'].rolling(window).min()
            
            # Detectar volume spikes
            df['Volume_Spike'] = df['Volume'] > (df['Volume_SMA'] * volume_spike)
            
            # Detectar breakouts de precio
            df['Price_Breakout_Up'] = df['Close'] > (df['Resistance'].shift(1) * (1 + price_breakout))
            df['Price_Breakout_Down'] = df['Close'] < (df['Support'].shift(1) * (1 - price_breakout))
            
            # Confirmación de señales
            if confirmation_periods > 1:
                # Requiere confirmación en múltiples períodos
                df['Breakout_Confirmed_Up'] = (
                    df['Price_Breakout_Up'].rolling(confirmation_periods).sum() >= confirmation_periods
                )
                df['Breakout_Confirmed_Down'] = (
                    df['Price_Breakout_Down'].rolling(confirmation_periods).sum() >= confirmation_periods
                )
            else:
                # Sin confirmación adicional (más agresivo)
                df['Breakout_Confirmed_Up'] = df['Price_Breakout_Up']
                df['Breakout_Confirmed_Down'] = df['Price_Breakout_Down']
            
            # Generar señales
            df['signal'] = np.where(
                df['Breakout_Confirmed_Up'] & df['Volume_Spike'] & (df['RSI'] < 80), 1, 0
            )
            df['signal'] = np.where(
                df['Breakout_Confirmed_Down'] & df['Volume_Spike'] & (df['RSI'] > 20), -1, df['signal']
            )
        
        # Calcular posiciones (evitar cambios muy rápidos)
        df['position'] = df['signal'].replace(to_replace=0, method='ffill')
        
        # Calcular puntos de entrada y salida
        df['entry'] = df['position'].diff() != 0
        
        return df
    
    def calculate_trade_metrics(self, df: pd.DataFrame, initial_capital: float) -> Dict:
        """Calcula métricas detalladas de los trades"""
        
        if df.empty or 'position' not in df:
            return {}
        
        # Identificar trades
        trades = []
        position = 0
        entry_price = 0
        entry_time = None
        
        for i, row in df.iterrows():
            if row['position'] != position:
                if position != 0:
                    # Cerrar posición anterior
                    exit_price = row['Close'] * (1 - self.config['slippage'] * np.sign(position))
                    
                    # Calcular P&L
                    if position > 0:  # Long
                        pnl_pct = (exit_price - entry_price) / entry_price
                    else:  # Short
                        pnl_pct = (entry_price - exit_price) / entry_price
                    
                    # Restar comisiones
                    pnl_pct -= 2 * self.config['commission']
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': i,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'position': position,
                        'pnl_pct': pnl_pct,
                        'duration': (i - entry_time).total_seconds() / 3600 if entry_time else 0
                    })
                
                # Abrir nueva posición
                if row['position'] != 0:
                    position = row['position']
                    entry_price = row['Close'] * (1 + self.config['slippage'] * np.sign(position))
                    entry_time = i
                else:
                    position = 0
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        # Calcular métricas
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['pnl_pct'] > 0]
        losing_trades = trades_df[trades_df['pnl_pct'] <= 0]
        
        # Calcular equity curve
        equity = initial_capital
        equity_curve = [initial_capital]
        peak = initial_capital
        max_drawdown = 0
        
        for trade in trades:
            equity *= (1 + trade['pnl_pct'])
            equity_curve.append(equity)
            
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calcular Sharpe Ratio
        returns = trades_df['pnl_pct'].values
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe_ratio = np.sqrt(252) * np.mean(returns) / np.std(returns)
        else:
            sharpe_ratio = 0
        
        metrics = {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) * 100 if trades else 0,
            'avg_win': winning_trades['pnl_pct'].mean() * 100 if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl_pct'].mean() * 100 if len(losing_trades) > 0 else 0,
            'profit_factor': abs(winning_trades['pnl_pct'].sum() / losing_trades['pnl_pct'].sum()) 
                           if len(losing_trades) > 0 and losing_trades['pnl_pct'].sum() != 0 else 0,
            'total_return': (equity - initial_capital) / initial_capital * 100,
            'final_equity': equity,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'avg_trade_duration': trades_df['duration'].mean() if 'duration' in trades_df else 0,
            'best_trade': trades_df['pnl_pct'].max() * 100 if len(trades) > 0 else 0,
            'worst_trade': trades_df['pnl_pct'].min() * 100 if len(trades) > 0 else 0,
            'equity_curve': equity_curve,
            'trades': trades
        }
        
        return metrics
    
    def run_backtest(
        self,
        symbol: str,
        strategy: str = "momentum",
        interval: str = "1h",
        days_back: int = 30,
        initial_capital: float = None
    ) -> Dict:
        """Ejecuta un backtest completo"""
        
        with TradingErrorContext("run_backtest", symbol):
            start_timer = performance_monitor.start_timer("run_backtest")
            
            # Configuración
            initial_capital = initial_capital or self.config['initial_capital']
            
            # Obtener datos históricos
            df = self.fetch_historical_data(symbol, interval, days_back)
            
            if df.empty:
                return {
                    'success': False,
                    'error': 'No se pudieron obtener datos históricos'
                }
            
            # Generar señales
            df = self.generate_signals(df, strategy, symbol)
            
            # Calcular métricas
            metrics = self.calculate_trade_metrics(df, initial_capital)
            
            # Preparar resultado
            result = {
                'success': True,
                'symbol': symbol,
                'strategy': strategy,
                'interval': interval,
                'days_back': days_back,
                'initial_capital': initial_capital,
                'data_points': len(df),
                'date_range': {
                    'start': df.index[0].isoformat() if not df.empty else None,
                    'end': df.index[-1].isoformat() if not df.empty else None
                },
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            # Guardar resultado
            self.results.append(result)
            
            performance_monitor.end_timer("run_backtest", start_timer)
            
            # Log resultado
            error_handler.logger.info(
                f"Backtest completado para {symbol}: "
                f"Return: {metrics.get('total_return', 0):.2f}%, "
                f"Trades: {metrics.get('total_trades', 0)}, "
                f"Win Rate: {metrics.get('win_rate', 0):.1f}%"
            )
            
            return result
    
    def optimize_strategy(
        self,
        symbol: str,
        strategy: str,
        parameter_ranges: Dict[str, List],
        interval: str = "1h",
        days_back: int = 30
    ) -> Dict:
        """Optimiza parámetros de estrategia"""
        
        best_result = None
        best_score = -float('inf')
        all_results = []
        
        # Generar combinaciones de parámetros
        import itertools
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        
        for combination in itertools.product(*param_values):
            params = dict(zip(param_names, combination))
            
            # Ejecutar backtest con estos parámetros
            # (Aquí necesitarías modificar generate_signals para aceptar parámetros)
            result = self.run_backtest(symbol, strategy, interval, days_back)
            
            if result['success']:
                # Score basado en Sharpe Ratio y Return
                score = (
                    result['metrics'].get('sharpe_ratio', 0) * 0.5 +
                    result['metrics'].get('total_return', 0) * 0.3 +
                    result['metrics'].get('win_rate', 0) * 0.2
                )
                
                result['parameters'] = params
                result['optimization_score'] = score
                all_results.append(result)
                
                if score > best_score:
                    best_score = score
                    best_result = result
                    self.best_parameters[symbol] = params
        
        return {
            'best_result': best_result,
            'best_parameters': self.best_parameters.get(symbol),
            'all_results': sorted(all_results, key=lambda x: x.get('optimization_score', 0), reverse=True)[:10],
            'total_combinations_tested': len(all_results)
        }
    
    def run_optimal_strategy_backtest(
        self,
        symbol: str,
        interval: str = "1h",
        days_back: int = 30
    ) -> Dict:
        """Ejecuta backtest con las estrategias recomendadas para el activo"""
        
        # Obtener estrategias recomendadas para este activo
        recommended_strategies = get_recommended_strategies(symbol)
        asset_type = get_asset_type(symbol)
        
        if not recommended_strategies:
            recommended_strategies = ['momentum', 'mean_reversion', 'trend_following']
        
        results = {}
        best_result = None
        best_score = -float('inf')
        
        for strategy in recommended_strategies:
            result = self.run_backtest(symbol, strategy, interval, days_back)
            
            if result['success']:
                # Score basado en Sharpe Ratio, Return y Win Rate
                metrics = result['metrics']
                score = (
                    metrics.get('sharpe_ratio', 0) * 0.4 +
                    (metrics.get('total_return', 0) / 100) * 0.4 +
                    (metrics.get('win_rate', 0) / 100) * 0.2
                )
                
                result['optimization_score'] = score
                results[strategy] = result
                
                if score > best_score:
                    best_score = score
                    best_result = result
        
        return {
            'symbol': symbol,
            'asset_type': asset_type,
            'strategies_tested': list(results.keys()),
            'best_strategy': best_result['strategy'] if best_result else None,
            'best_score': best_score,
            'best_result': best_result,
            'all_results': results,
            'timestamp': datetime.now().isoformat()
        }

    def run_multi_symbol_backtest(
        self,
        symbols: List[str],
        strategy: str = "momentum",
        interval: str = "1h",
        days_back: int = 30
    ) -> Dict:
        """Ejecuta backtest en múltiples símbolos"""
        
        results = {}
        summary = {
            'total_symbols': len(symbols),
            'successful': 0,
            'failed': 0,
            'avg_return': 0,
            'best_symbol': None,
            'best_return': -float('inf'),
            'worst_symbol': None,
            'worst_return': float('inf')
        }
        
        returns = []
        
        for symbol in symbols:
            result = self.run_backtest(symbol, strategy, interval, days_back)
            results[symbol] = result
            
            if result['success']:
                summary['successful'] += 1
                ret = result['metrics'].get('total_return', 0)
                returns.append(ret)
                
                if ret > summary['best_return']:
                    summary['best_return'] = ret
                    summary['best_symbol'] = symbol
                
                if ret < summary['worst_return']:
                    summary['worst_return'] = ret
                    summary['worst_symbol'] = symbol
            else:
                summary['failed'] += 1
        
        if returns:
            summary['avg_return'] = np.mean(returns)
            summary['median_return'] = np.median(returns)
            summary['std_return'] = np.std(returns)
        
        return {
            'results': results,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_report(self, result: Dict) -> str:
        """Genera un reporte detallado del backtest"""
        
        if not result.get('success'):
            return f"❌ Backtest fallido: {result.get('error', 'Error desconocido')}"
        
        metrics = result['metrics']
        
        report = f"""
📊 REPORTE DE BACKTEST
{'='*50}

🎯 Configuración:
- Símbolo: {result['symbol']}
- Estrategia: {result['strategy']}
- Intervalo: {result['interval']}
- Período: {result['days_back']} días
- Capital Inicial: ${result['initial_capital']:,.2f}

📈 Resultados:
- Return Total: {metrics['total_return']:.2f}%
- Capital Final: ${metrics.get('final_equity', 0):,.2f}
- Total Trades: {metrics['total_trades']}
- Win Rate: {metrics['win_rate']:.1f}%

💰 Trades:
- Trades Ganadores: {metrics['winning_trades']}
- Trades Perdedores: {metrics['losing_trades']}
- Promedio Ganancia: {metrics['avg_win']:.2f}%
- Promedio Pérdida: {metrics['avg_loss']:.2f}%
- Mejor Trade: {metrics.get('best_trade', 0):.2f}%
- Peor Trade: {metrics.get('worst_trade', 0):.2f}%

📊 Métricas de Riesgo:
- Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
- Profit Factor: {metrics['profit_factor']:.2f}
- Max Drawdown: {metrics['max_drawdown']:.2f}%
- Duración Promedio: {metrics.get('avg_trade_duration', 0):.1f} horas

{'='*50}
"""
        return report
    
    def export_results(self, filename: str = "backtest_results.json"):
        """Exporta resultados a archivo"""
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # También exportar a CSV para análisis
            if self.results:
                df_results = pd.DataFrame([
                    {
                        'symbol': r['symbol'],
                        'strategy': r['strategy'],
                        'interval': r['interval'],
                        'days_back': r['days_back'],
                        'total_return': r['metrics'].get('total_return', 0),
                        'win_rate': r['metrics'].get('win_rate', 0),
                        'total_trades': r['metrics'].get('total_trades', 0),
                        'sharpe_ratio': r['metrics'].get('sharpe_ratio', 0),
                        'max_drawdown': r['metrics'].get('max_drawdown', 0)
                    }
                    for r in self.results if r.get('success')
                ])
                
                csv_filename = filename.replace('.json', '.csv')
                df_results.to_csv(csv_filename, index=False)
                
                return True
        
        except Exception as e:
            error_handler.handle_error(e, context={'operation': 'export_results'})
            return False


if __name__ == "__main__":
    # Test del sistema de backtest
    backtest = BacktestSystemV2()
    
    # Test backtest simple
    print("🚀 Ejecutando backtest...")
    result = backtest.run_backtest(
        symbol="SOLUSDT",
        strategy="momentum",
        interval="1h",
        days_back=7
    )
    
    # Mostrar reporte
    print(backtest.generate_report(result))
    
    # Test multi-símbolo
    print("\n🔄 Ejecutando backtest multi-símbolo...")
    symbols = ["SOLUSDT", "ADAUSDT", "DOGEUSDT"]
    multi_result = backtest.run_multi_symbol_backtest(symbols, days_back=7)
    
    print(f"\n📊 Resumen Multi-Símbolo:")
    print(json.dumps(multi_result['summary'], indent=2, default=str))
    
    # Exportar resultados
    backtest.export_results("backtest_results.json")
    print("\n✅ Resultados exportados a backtest_results.json")
    
    # Mostrar estadísticas de rendimiento
    print(f"\n⚡ Estadísticas de Rendimiento:")
    print(json.dumps(performance_monitor.get_stats(), indent=2))
    
    # Mostrar estadísticas de caché
    print(f"\n💾 Estadísticas de Caché:")
    print(json.dumps(cache_manager.get_stats(), indent=2))