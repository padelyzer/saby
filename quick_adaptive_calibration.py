#!/usr/bin/env python3
"""
Sistema de Calibración Adaptativa Rápida
Versión optimizada con menos combinaciones para resultados más rápidos
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

from scoring_empirico_v2 import ScoringEmpiricoV2

class QuickAdaptiveCalibration:
    """
    Calibración rápida con configuraciones preseleccionadas
    """
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.scoring_system = ScoringEmpiricoV2()
        
        # Períodos de calibración
        self.calibration_periods = [
            {
                'name': 'Q1_2024_BULL',
                'start': '2024-01-01',
                'end': '2024-03-31',
                'type': 'BULL'
            },
            {
                'name': 'Q2_2024_CORRECTION',
                'start': '2024-04-01',
                'end': '2024-06-30',
                'type': 'BEAR'
            },
            {
                'name': 'Q3_2024_RECOVERY',
                'start': '2024-07-01',
                'end': '2024-09-30',
                'type': 'RECOVERY'
            }
        ]
        
        # Configuraciones preseleccionadas basadas en análisis previo
        self.test_configs = [
            # Config conservadora
            {
                'name': 'Conservative',
                'min_score': 5.0,
                'stop_loss_pct': 0.03,
                'take_profit_pct': 0.12,
                'position_size_pct': 0.01,
                'leverage_base': 2,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            },
            # Config balanceada (basada en resultados anteriores)
            {
                'name': 'Balanced',
                'min_score': 4.5,
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10,
                'position_size_pct': 0.02,
                'leverage_base': 2,
                'rsi_oversold': 30,
                'rsi_overbought': 65
            },
            # Config agresiva
            {
                'name': 'Aggressive',
                'min_score': 4.0,
                'stop_loss_pct': 0.04,
                'take_profit_pct': 0.15,
                'position_size_pct': 0.03,
                'leverage_base': 3,
                'rsi_oversold': 35,
                'rsi_overbought': 65
            },
            # Config adaptativa
            {
                'name': 'Adaptive',
                'min_score': 4.2,
                'stop_loss_pct': 0.045,
                'take_profit_pct': 0.12,
                'position_size_pct': 0.025,
                'leverage_base': 2,
                'rsi_oversold': 32,
                'rsi_overbought': 68
            }
        ]
        
        self.market_data = None
        self.results = []
        
    def run_calibration(self):
        """Ejecuta calibración rápida"""
        
        print("🚀 CALIBRACIÓN ADAPTATIVA RÁPIDA")
        print("="*80)
        print(f"💰 Capital: ${self.initial_capital:,}")
        print(f"📊 Configuraciones a probar: {len(self.test_configs)}")
        print("="*80)
        
        # Cargar datos
        print("\n📊 Cargando datos de mercado...")
        self.market_data = self.load_market_data()
        
        if not self.market_data:
            print("❌ Error cargando datos")
            return None
        
        print("✅ Datos cargados exitosamente")
        
        # Probar cada configuración
        best_config = None
        best_score = -float('inf')
        
        for i, config in enumerate(self.test_configs, 1):
            print(f"\n{'='*60}")
            print(f"🔍 Probando Configuración {i}/{len(self.test_configs)}: {config['name']}")
            print("="*60)
            
            # Probar configuración
            results = self.test_configuration(config)
            
            # Calcular score
            score = self.calculate_score(results)
            
            # Guardar resultados
            self.results.append({
                'config': config,
                'metrics': results['metrics'],
                'score': score,
                'trades': results.get('trades', [])
            })
            
            # Actualizar mejor
            if score > best_score:
                best_score = score
                best_config = {
                    'params': config,
                    'metrics': results['metrics'],
                    'score': score
                }
            
            # Mostrar métricas
            self.print_config_results(config['name'], results['metrics'], score)
        
        # Mostrar resumen final
        self.print_final_summary(best_config)
        
        # Guardar mejor configuración
        if best_config:
            self.save_configuration(best_config)
        
        return best_config
    
    def load_market_data(self):
        """Carga datos de mercado"""
        
        market_data = {}
        # Solo 3 símbolos principales para velocidad
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        
        for symbol in symbols:
            print(f"  • Cargando {symbol}...")
            symbol_data = {}
            
            for period in self.calibration_periods:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(
                        start=period['start'],
                        end=period['end'],
                        interval='1d'
                    )
                    
                    if len(data) > 0:
                        data = self.prepare_indicators(data)
                        symbol_data[period['name']] = data
                        
                except Exception as e:
                    print(f"    ⚠️ Error: {e}")
            
            if symbol_data:
                market_data[symbol] = symbol_data
        
        return market_data
    
    def prepare_indicators(self, df):
        """Prepara indicadores técnicos"""
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 1)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # EMAs
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA'].replace(0, 1)
        df['Volume_Ratio'] = df['Volume_Ratio'].fillna(1.0).clip(lower=0.1)
        
        return df
    
    def test_configuration(self, config):
        """Prueba una configuración"""
        
        all_trades = []
        period_performance = {}
        
        for symbol, symbol_data in self.market_data.items():
            for period_name, data in symbol_data.items():
                # Obtener tipo de mercado
                period_type = next((p['type'] for p in self.calibration_periods 
                                   if p['name'] == period_name), 'NEUTRAL')
                
                # Ejecutar backtest
                trades = self.backtest_with_config(
                    symbol, data, config, period_type
                )
                
                all_trades.extend(trades)
                
                if period_name not in period_performance:
                    period_performance[period_name] = []
                period_performance[period_name].extend(trades)
        
        # Calcular métricas
        metrics = self.calculate_metrics(all_trades)
        
        # Añadir métricas por tipo de mercado
        for period in self.calibration_periods:
            period_trades = period_performance.get(period['name'], [])
            if period_trades:
                period_metrics = self.calculate_metrics(period_trades)
                metrics[f"{period['type']}_trades"] = len(period_trades)
                metrics[f"{period['type']}_win_rate"] = period_metrics['win_rate']
                metrics[f"{period['type']}_return"] = period_metrics['total_return']
        
        return {
            'config': config,
            'trades': all_trades,
            'metrics': metrics,
            'period_performance': period_performance
        }
    
    def backtest_with_config(self, symbol, data, config, market_type):
        """Ejecuta backtest con configuración específica"""
        
        trades = []
        position = None
        
        # Ajustar parámetros según tipo de mercado
        adjusted_config = self.adjust_for_market(config, market_type)
        
        # Iterar por los datos
        for i in range(20, len(data)):
            current = data.iloc[i]
            prev = data.iloc[i-1]
            
            # Si no hay posición, buscar entrada
            if position is None:
                signal_type, score = self.generate_signal(
                    data.iloc[:i+1], current, prev, adjusted_config, market_type
                )
                
                if signal_type and score >= adjusted_config['min_score']:
                    # Abrir posición
                    position = {
                        'symbol': symbol,
                        'type': signal_type,
                        'entry_date': current.name,
                        'entry_price': float(current['Close']),
                        'score': score,
                        'market_type': market_type
                    }
                    
                    # Calcular stops
                    if signal_type == 'LONG':
                        position['stop_loss'] = position['entry_price'] * (1 - adjusted_config['stop_loss_pct'])
                        position['take_profit'] = position['entry_price'] * (1 + adjusted_config['take_profit_pct'])
                    else:
                        position['stop_loss'] = position['entry_price'] * (1 + adjusted_config['stop_loss_pct'])
                        position['take_profit'] = position['entry_price'] * (1 - adjusted_config['take_profit_pct'])
            
            # Si hay posición, verificar salida
            elif position:
                exit_signal = False
                exit_price = float(current['Close'])
                exit_reason = None
                
                # Verificar stops
                if position['type'] == 'LONG':
                    if current['Low'] <= position['stop_loss']:
                        exit_signal = True
                        exit_price = position['stop_loss']
                        exit_reason = 'STOP_LOSS'
                    elif current['High'] >= position['take_profit']:
                        exit_signal = True
                        exit_price = position['take_profit']
                        exit_reason = 'TAKE_PROFIT'
                else:  # SHORT
                    if current['High'] >= position['stop_loss']:
                        exit_signal = True
                        exit_price = position['stop_loss']
                        exit_reason = 'STOP_LOSS'
                    elif current['Low'] <= position['take_profit']:
                        exit_signal = True
                        exit_price = position['take_profit']
                        exit_reason = 'TAKE_PROFIT'
                
                if exit_signal:
                    # Cerrar posición
                    position['exit_date'] = current.name
                    position['exit_price'] = exit_price
                    position['exit_reason'] = exit_reason
                    
                    # Calcular return
                    if position['type'] == 'LONG':
                        position['return_pct'] = ((exit_price / position['entry_price']) - 1) * 100
                    else:
                        position['return_pct'] = ((position['entry_price'] / exit_price) - 1) * 100
                    
                    # Aplicar leverage y comisiones
                    position['return_pct'] *= adjusted_config['leverage_base']
                    position['return_pct'] -= 0.2  # Comisiones
                    
                    position['duration_days'] = (position['exit_date'] - position['entry_date']).days
                    
                    trades.append(position)
                    position = None
        
        # Cerrar posición final si queda abierta
        if position:
            position['exit_date'] = data.iloc[-1].name
            position['exit_price'] = float(data.iloc[-1]['Close'])
            position['exit_reason'] = 'END_PERIOD'
            
            if position['type'] == 'LONG':
                position['return_pct'] = ((position['exit_price'] / position['entry_price']) - 1) * 100
            else:
                position['return_pct'] = ((position['entry_price'] / position['exit_price']) - 1) * 100
            
            position['return_pct'] *= adjusted_config['leverage_base']
            position['return_pct'] -= 0.2
            
            trades.append(position)
        
        return trades
    
    def adjust_for_market(self, config, market_type):
        """Ajusta configuración según tipo de mercado"""
        
        adjusted = config.copy()
        
        if market_type == 'BULL':
            # Mercado alcista: más agresivo
            adjusted['min_score'] = max(3.5, config['min_score'] - 0.3)
            adjusted['take_profit_pct'] = config['take_profit_pct'] * 1.1
            
        elif market_type == 'BEAR':
            # Mercado bajista: más conservador
            adjusted['min_score'] = min(5.5, config['min_score'] + 0.3)
            adjusted['stop_loss_pct'] = config['stop_loss_pct'] * 0.9
            
        return adjusted
    
    def generate_signal(self, df, current, prev, config, market_type):
        """Genera señal de trading"""
        
        try:
            # Usar sistema de scoring
            signal_type, score = self.scoring_system.evaluar_entrada(df, current, prev)
            
            # Ajustes adicionales
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            
            # Override con condiciones específicas
            if rsi <= config['rsi_oversold'] and macd > macd_signal:
                if signal_type != 'SHORT':
                    signal_type = 'LONG'
                    score = max(score, config['min_score'] + 0.5)
            elif rsi >= config['rsi_overbought'] and macd < macd_signal:
                if signal_type != 'LONG':
                    signal_type = 'SHORT'
                    score = max(score, config['min_score'] + 0.5)
            
            # Bonus por tipo de mercado
            if market_type == 'BULL' and signal_type == 'LONG':
                score += 0.3
            elif market_type == 'BEAR' and signal_type == 'SHORT':
                score += 0.3
            
            return signal_type, score
            
        except:
            # Fallback simple
            rsi = current.get('RSI', 50)
            macd = current.get('MACD', 0)
            macd_signal = current.get('MACD_Signal', 0)
            
            if rsi <= config['rsi_oversold'] and macd > macd_signal:
                return 'LONG', config['min_score'] + 0.5
            elif rsi >= config['rsi_overbought'] and macd < macd_signal:
                return 'SHORT', config['min_score'] + 0.5
            
            return None, 0
    
    def calculate_metrics(self, trades):
        """Calcula métricas de performance"""
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_return': 0,
                'avg_trade_return': 0,
                'max_drawdown': 0
            }
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['return_pct'] > 0)
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100)
        
        # Profit factor
        wins = sum(t['return_pct'] for t in trades if t['return_pct'] > 0)
        losses = abs(sum(t['return_pct'] for t in trades if t['return_pct'] < 0))
        profit_factor = wins / losses if losses > 0 else float('inf') if wins > 0 else 0
        
        # Returns
        total_return = sum(t['return_pct'] for t in trades)
        avg_return = total_return / total_trades
        
        # Max drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for trade in sorted(trades, key=lambda x: x['entry_date']):
            cumulative += trade['return_pct']
            peak = max(peak, cumulative)
            dd = peak - cumulative
            max_dd = max(max_dd, dd)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'avg_trade_return': avg_return,
            'max_drawdown': max_dd
        }
    
    def calculate_score(self, results):
        """Calcula score para una configuración"""
        
        metrics = results['metrics']
        
        score = 0
        
        # Win rate (0-40 puntos)
        score += min(40, metrics.get('win_rate', 0) * 0.7)
        
        # Profit factor (0-30 puntos)
        score += min(30, metrics.get('profit_factor', 0) * 12)
        
        # Total return (0-20 puntos)
        score += min(20, metrics.get('total_return', 0) * 0.7)
        
        # Número de trades (0-10 puntos)
        score += min(10, metrics.get('total_trades', 0) * 0.7)
        
        # Penalización por drawdown
        max_dd = metrics.get('max_drawdown', 0)
        if max_dd > 15:
            score -= (max_dd - 15) * 0.5
        
        # Bonus por consistencia en diferentes mercados
        if 'BULL_win_rate' in metrics and 'BEAR_win_rate' in metrics:
            min_wr = min(
                metrics.get('BULL_win_rate', 0),
                metrics.get('BEAR_win_rate', 0),
                metrics.get('RECOVERY_win_rate', 0)
            )
            if min_wr > 40:
                score += 10
        
        return max(0, score)
    
    def print_config_results(self, name, metrics, score):
        """Imprime resultados de una configuración"""
        
        print(f"\n📊 Resultados {name}:")
        print(f"  • Score Total: {score:.1f}")
        print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  • Total Return: {metrics['total_return']:.1f}%")
        print(f"  • Total Trades: {metrics['total_trades']}")
        print(f"  • Max Drawdown: {metrics['max_drawdown']:.1f}%")
        
        # Performance por tipo de mercado
        if 'BULL_win_rate' in metrics:
            print(f"\n  Performance por mercado:")
            for market in ['BULL', 'BEAR', 'RECOVERY']:
                trades = metrics.get(f'{market}_trades', 0)
                wr = metrics.get(f'{market}_win_rate', 0)
                ret = metrics.get(f'{market}_return', 0)
                print(f"    • {market}: {trades} trades, WR={wr:.1f}%, Return={ret:.1f}%")
    
    def print_final_summary(self, best_config):
        """Imprime resumen final"""
        
        print("\n" + "="*80)
        print("📊 RESUMEN FINAL - CALIBRACIÓN RÁPIDA")
        print("="*80)
        
        # Ranking de configuraciones
        print("\n🏆 RANKING DE CONFIGURACIONES:")
        sorted_results = sorted(self.results, key=lambda x: x['score'], reverse=True)
        
        for i, result in enumerate(sorted_results, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            print(f"\n{emoji} #{i} {result['config']['name']}")
            print(f"  Score: {result['score']:.1f}")
            print(f"  Win Rate: {result['metrics']['win_rate']:.1f}%")
            print(f"  Profit Factor: {result['metrics']['profit_factor']:.2f}")
            print(f"  Return: {result['metrics']['total_return']:.1f}%")
        
        if best_config:
            print("\n" + "="*80)
            print("✅ MEJOR CONFIGURACIÓN")
            print("="*80)
            
            params = best_config['params']
            metrics = best_config['metrics']
            
            print("\n⚙️ PARÁMETROS ÓPTIMOS:")
            print(f"  • Configuración: {params['name']}")
            print(f"  • Score Mínimo: {params['min_score']}")
            print(f"  • Stop Loss: {params['stop_loss_pct']*100:.1f}%")
            print(f"  • Take Profit: {params['take_profit_pct']*100:.1f}%")
            print(f"  • Position Size: {params['position_size_pct']*100:.1f}%")
            print(f"  • Leverage: {params['leverage_base']}x")
            
            print("\n📈 MÉTRICAS ESPERADAS:")
            print(f"  • Win Rate: {metrics['win_rate']:.1f}%")
            print(f"  • Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"  • Total Return (9 meses): {metrics['total_return']:.1f}%")
            print(f"  • Return Mensual: {metrics['total_return']/9:.1f}%")
            print(f"  • Return Anualizado: {metrics['total_return']*4/3:.1f}%")
            
            print("\n🎯 EVALUACIÓN:")
            if metrics['win_rate'] >= 55 and metrics['profit_factor'] >= 1.8:
                print("  ⭐ EXCELENTE - Sistema altamente rentable")
                print("  ✅ Listo para producción")
            elif metrics['win_rate'] >= 50 and metrics['profit_factor'] >= 1.5:
                print("  ✅ BUENO - Sistema rentable y confiable")
                print("  ✅ Recomendado para paper trading")
            elif metrics['win_rate'] >= 45:
                print("  ⚠️ ACEPTABLE - Sistema funcional")
                print("  ⚠️ Requiere monitoreo cercano")
            else:
                print("  ❌ INSUFICIENTE - Requiere ajustes")
    
    def save_configuration(self, best_config):
        """Guarda la mejor configuración"""
        
        config_to_save = {
            'calibration_date': datetime.now().isoformat(),
            'system': 'QUICK_ADAPTIVE',
            'parameters': best_config['params'],
            'metrics': best_config['metrics'],
            'score': best_config['score'],
            'periods_tested': [p['name'] for p in self.calibration_periods]
        }
        
        with open('quick_adaptive_config.json', 'w') as f:
            json.dump(config_to_save, f, indent=2, default=str)
        
        print("\n💾 Configuración guardada en 'quick_adaptive_config.json'")

def main():
    """Función principal"""
    
    print("🚀 INICIANDO CALIBRACIÓN ADAPTATIVA RÁPIDA")
    print("="*80)
    
    calibrator = QuickAdaptiveCalibration(initial_capital=10000)
    
    # Ejecutar calibración
    best_config = calibrator.run_calibration()
    
    print("\n" + "="*80)
    print("✅ CALIBRACIÓN COMPLETADA")
    print("="*80)
    
    if best_config:
        print("\n🎯 Sistema listo con configuración óptima")
        print("Próximos pasos:")
        print("1. Validar con backtesting extendido")
        print("2. Iniciar paper trading")
        print("3. Monitorear resultados en tiempo real")
    
    return best_config

if __name__ == "__main__":
    main()