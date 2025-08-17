#!/usr/bin/env python3
"""
Backtesting Sistema Adaptativo
Prueba el sistema adaptativo completo con diferentes condiciones de mercado
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from sistema_adaptativo_completo import SistemaAdaptativoCompleto

class BacktestingAdaptativo:
    """
    Backtesting especializado para el sistema adaptativo
    """
    
    def __init__(self, capital_inicial=10000):
        self.capital_inicial = capital_inicial
        self.sistema_adaptativo = SistemaAdaptativoCompleto()
        
        # Configuraciones específicas para altseason
        self.altseason_config = {
            'altcoin_symbols': ['ETH', 'SOL', 'BNB', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK'],
            'altcoin_weight_multiplier': 1.3,  # Más peso a altcoins en altseason
            'btc_dominance_threshold': 50,     # Bajo esta dominancia = altseason
            'volume_spike_threshold': 1.5,     # Volumen 50% mayor = interés alto
            'momentum_amplifier': 1.4          # Amplificar momentum en altseason
        }
    
    def run_adaptive_backtest(self, symbols=None, days=30, regime_override=None):
        """Ejecuta backtesting adaptativo"""
        
        if symbols is None:
            symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
        
        print(f"🚀 BACKTESTING SISTEMA ADAPTATIVO")
        print("="*60)
        print(f"• Símbolos: {len(symbols)}")
        print(f"• Período: {days} días")
        print(f"• Capital inicial: ${self.capital_inicial:,}")
        if regime_override:
            print(f"• Régimen forzado: {regime_override}")
        print("="*60)
        
        all_trades = []
        regime_performance = {}
        
        for symbol in symbols:
            try:
                print(f"\\n📊 Analizando {symbol}...")
                
                # Obtener datos
                data = self._fetch_data(symbol, days + 50)  # Extra data para indicadores
                if data is None or len(data) < 30:
                    print(f"⚠️ Datos insuficientes para {symbol}")
                    continue
                
                # Preparar datos
                df = self._prepare_data(data)
                
                # Simular trading adaptativo
                trades = self._simulate_adaptive_trading(df, symbol, regime_override)
                
                if trades:
                    all_trades.extend(trades)
                    print(f"✅ {len(trades)} trades generados para {symbol}")
                else:
                    print(f"⚠️ Sin trades para {symbol}")
                    
            except Exception as e:
                print(f"❌ Error procesando {symbol}: {e}")
                continue
        
        if all_trades:
            # Analizar resultados
            results = self._analyze_adaptive_results(all_trades)
            
            # Analizar performance por régimen
            regime_analysis = self._analyze_by_regime(all_trades)
            
            # Mostrar resultados
            self._print_adaptive_results(results, regime_analysis)
            
            return {
                'trades': all_trades,
                'results': results,
                'regime_analysis': regime_analysis
            }
        else:
            print("❌ No se generaron trades")
            return None
    
    def _fetch_data(self, symbol, days):
        """Obtiene datos del símbolo"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f"{days}d", interval="1h")
            return data
        except Exception as e:
            print(f"Error obteniendo datos para {symbol}: {e}")
            return None
    
    def _prepare_data(self, data):
        """Prepara datos con indicadores técnicos"""
        
        df = data.copy()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volumen
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA'].replace(0, 1)
        df['Volume_Ratio'] = df['Volume_Ratio'].fillna(1.0).clip(lower=0.1)
        
        # EMAs
        df['EMA_20'] = df['Close'].ewm(span=20).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        df['BB_Middle'] = df['Close'].rolling(bb_period).mean()
        bb_std_dev = df['Close'].rolling(bb_period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std_dev * bb_std)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std_dev * bb_std)
        
        return df.dropna()
    
    def _simulate_adaptive_trading(self, df, symbol, regime_override=None):
        """Simula trading con sistema adaptativo"""
        
        trades = []
        
        # Simular diferentes regímenes si no hay override
        if regime_override:
            regimes_to_test = [regime_override]
        else:
            regimes_to_test = ['BULLISH', 'ALTSEASON', 'LATERAL', 'BEARISH']
        
        # Dividir datos por períodos para simular diferentes regímenes
        period_length = len(df) // len(regimes_to_test)
        
        for i, regime in enumerate(regimes_to_test):
            start_idx = i * period_length
            end_idx = start_idx + period_length if i < len(regimes_to_test) - 1 else len(df)
            
            period_data = df.iloc[start_idx:end_idx]
            
            # Forzar régimen en el sistema
            self._set_regime_override(regime)
            
            # Analizar señales en este período
            period_trades = self._find_adaptive_signals(period_data, symbol, regime)
            trades.extend(period_trades)
        
        return trades
    
    def _set_regime_override(self, regime):
        """Fuerza un régimen específico para testing"""
        
        regime_data = {
            'regime': regime,
            'confidence': 0.8,
            'description': f"Régimen forzado para testing: {regime}",
            'config': self.sistema_adaptativo.market_detector.regime_configs[regime]
        }
        
        self.sistema_adaptativo.current_regime = regime_data
        self.sistema_adaptativo.last_regime_update = datetime.now()
    
    def _find_adaptive_signals(self, df, symbol, regime):
        """Encuentra señales usando sistema adaptativo"""
        
        trades = []
        
        for i in range(50, len(df) - 1):  # Dejar margen para indicadores
            current = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Determinar tipo de señal
            signal_type = self._determine_signal_type(current, prev)
            
            if signal_type:
                # Calcular score adaptativo
                score, details = self.sistema_adaptativo.calculate_adaptive_score(
                    df.iloc[:i+1], current, prev, symbol.replace('-USD', ''), signal_type
                )
                
                # Obtener threshold adaptativo
                threshold = self.sistema_adaptativo.get_adaptive_threshold(symbol.replace('-USD', ''))
                
                # Validar señal
                if score >= threshold:
                    # Calcular leverage adaptativo
                    leverage = self.sistema_adaptativo.get_adaptive_leverage(score, symbol.replace('-USD', ''))
                    
                    # Crear trade
                    trade = self._create_adaptive_trade(df, i, signal_type, score, leverage, regime, details)
                    if trade:
                        trades.append(trade)
        
        return trades
    
    def _determine_signal_type(self, current, prev):
        """Determina el tipo de señal (LONG/SHORT)"""
        
        # Lógica simplificada para determinar señales
        if (current['RSI'] < 40 and 
            current['Close'] > current['EMA_20'] and
            current['Close'] > prev['Close']):
            return 'LONG'
        
        elif (current['RSI'] > 60 and 
              current['Close'] < current['EMA_20'] and
              current['Close'] < prev['Close']):
            return 'SHORT'
        
        return None
    
    def _create_adaptive_trade(self, df, entry_idx, signal_type, score, leverage, regime, details):
        """Crea un trade con configuración adaptativa"""
        
        entry = df.iloc[entry_idx]
        entry_price = entry['Close']
        
        # Position size adaptativo
        base_position_size = 0.02  # 2% base
        
        # Ajustar position size por régimen
        if regime == 'ALTSEASON':
            position_size = base_position_size * 1.5  # Más agresivo en altseason
        elif regime == 'BEARISH':
            position_size = base_position_size * 0.6  # Más conservador en bear
        else:
            position_size = base_position_size
        
        # Capital usado
        capital_usado = self.capital_inicial * position_size * leverage
        
        # Configurar stops adaptativos
        if regime == 'ALTSEASON':
            stop_loss_pct = 0.08  # Stop más amplio en altseason
            take_profit_pct = 0.15  # Target más ambicioso
        elif regime == 'BEARISH':
            stop_loss_pct = 0.04  # Stop más estrecho en bear
            take_profit_pct = 0.06  # Target más conservador
        else:
            stop_loss_pct = 0.06
            take_profit_pct = 0.10
        
        # Precios de salida
        if signal_type == 'LONG':
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + take_profit_pct)
        else:
            stop_loss = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 - take_profit_pct)
        
        # Simular salida
        exit_info = self._simulate_adaptive_exit(df, entry_idx + 1, stop_loss, take_profit, signal_type, regime)
        
        if exit_info:
            # Calcular resultado
            if signal_type == 'LONG':
                profit_pct = (exit_info['price'] - entry_price) / entry_price
            else:
                profit_pct = (entry_price - exit_info['price']) / entry_price
            
            profit_usd = capital_usado * profit_pct
            
            return {
                'symbol': df.index[entry_idx].strftime('%Y-%m-%d %H:%M') if hasattr(df.index[entry_idx], 'strftime') else entry_idx,
                'regime': regime,
                'signal_type': signal_type,
                'entry_price': entry_price,
                'exit_price': exit_info['price'],
                'exit_reason': exit_info['reason'],
                'score': score,
                'leverage': leverage,
                'capital_usado': capital_usado,
                'profit_pct': profit_pct * 100,
                'profit_usd': profit_usd,
                'position_size_pct': position_size * 100,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'adaptive_details': details
            }
        
        return None
    
    def _simulate_adaptive_exit(self, df, start_idx, stop_loss, take_profit, signal_type, regime):
        """Simula salida adaptativa del trade"""
        
        # Configurar duración máxima por régimen
        if regime == 'ALTSEASON':
            max_duration = 48  # Más tiempo en altseason
        elif regime == 'LATERAL':
            max_duration = 24  # Menos tiempo en lateral
        else:
            max_duration = 36  # Tiempo estándar
        
        for i in range(start_idx, min(start_idx + max_duration, len(df))):
            current = df.iloc[i]
            
            if signal_type == 'LONG':
                if current['Low'] <= stop_loss:
                    return {'price': stop_loss, 'reason': 'stop_loss'}
                elif current['High'] >= take_profit:
                    return {'price': take_profit, 'reason': 'take_profit'}
            else:
                if current['High'] >= stop_loss:
                    return {'price': stop_loss, 'reason': 'stop_loss'}
                elif current['Low'] <= take_profit:
                    return {'price': take_profit, 'reason': 'take_profit'}
        
        # Salida por tiempo
        final_price = df.iloc[min(start_idx + max_duration - 1, len(df) - 1)]['Close']
        return {'price': final_price, 'reason': 'time_exit'}
    
    def _analyze_adaptive_results(self, trades):
        """Analiza resultados del backtesting adaptativo"""
        
        df_trades = pd.DataFrame(trades)
        
        total_trades = len(trades)
        winning_trades = len(df_trades[df_trades['profit_pct'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = df_trades['profit_usd'].sum()
        total_return = (total_profit / self.capital_inicial) * 100
        
        avg_win = df_trades[df_trades['profit_pct'] > 0]['profit_pct'].mean() if winning_trades > 0 else 0
        avg_loss = df_trades[df_trades['profit_pct'] < 0]['profit_pct'].mean() if (total_trades - winning_trades) > 0 else 0
        
        profit_factor = abs(avg_win * winning_trades / (avg_loss * (total_trades - winning_trades))) if avg_loss != 0 and (total_trades - winning_trades) > 0 else 0
        
        avg_score = df_trades['score'].mean()
        avg_leverage = df_trades['leverage'].mean()
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_score': avg_score,
            'avg_leverage': avg_leverage,
            'total_profit_usd': total_profit
        }
    
    def _analyze_by_regime(self, trades):
        """Analiza performance por régimen de mercado"""
        
        df = pd.DataFrame(trades)
        regime_stats = {}
        
        for regime in df['regime'].unique():
            regime_trades = df[df['regime'] == regime]
            
            total = len(regime_trades)
            wins = len(regime_trades[regime_trades['profit_pct'] > 0])
            win_rate = (wins / total * 100) if total > 0 else 0
            
            avg_profit = regime_trades['profit_pct'].mean()
            total_profit = regime_trades['profit_usd'].sum()
            
            regime_stats[regime] = {
                'trades': total,
                'win_rate': win_rate,
                'avg_profit_pct': avg_profit,
                'total_profit_usd': total_profit,
                'avg_score': regime_trades['score'].mean(),
                'avg_leverage': regime_trades['leverage'].mean()
            }
        
        return regime_stats
    
    def _print_adaptive_results(self, results, regime_analysis):
        """Imprime resultados del backtesting adaptativo"""
        
        print(f"\\n📊 RESULTADOS BACKTESTING ADAPTATIVO")
        print("="*70)
        
        print(f"📈 MÉTRICAS GENERALES:")
        print(f"• Total Trades: {results['total_trades']}")
        print(f"• Win Rate: {results['win_rate']:.1f}%")
        print(f"• Profit Factor: {results['profit_factor']:.2f}")
        print(f"• Return Total: {results['total_return']:+.2f}%")
        print(f"• Ganancia Total: ${results['total_profit_usd']:+.2f}")
        print(f"• Score Promedio: {results['avg_score']:.1f}")
        print(f"• Leverage Promedio: {results['avg_leverage']:.1f}x")
        
        print(f"\\n📋 PERFORMANCE POR RÉGIMEN:")
        print("-" * 70)
        print(f"{'Régimen':<12} {'Trades':<8} {'WR %':<8} {'Avg%':<8} {'Total$':<10} {'Score':<7} {'Lev':<5}")
        print("-" * 70)
        
        for regime, stats in regime_analysis.items():
            print(f"{regime:<12} {stats['trades']:<8} {stats['win_rate']:<7.1f}% "
                  f"{stats['avg_profit_pct']:<7.2f}% ${stats['total_profit_usd']:<9.2f} "
                  f"{stats['avg_score']:<6.1f} {stats['avg_leverage']:<4.1f}x")
        
        # Identificar mejor régimen
        best_regime = max(regime_analysis.items(), key=lambda x: x[1]['win_rate'])
        print(f"\\n🏆 MEJOR RÉGIMEN: {best_regime[0]} ({best_regime[1]['win_rate']:.1f}% WR)")
        
        # Evaluar si está optimizado para altseason
        altseason_stats = regime_analysis.get('ALTSEASON')
        if altseason_stats:
            print(f"\\n🚀 OPTIMIZACIÓN ALTSEASON:")
            if altseason_stats['win_rate'] > results['win_rate']:
                print(f"✅ Sistema optimizado para altseason ({altseason_stats['win_rate']:.1f}% vs {results['win_rate']:.1f}% general)")
            else:
                print(f"⚠️ Necesita más optimización para altseason")

def demo_backtesting_adaptativo():
    """Demo del backtesting adaptativo"""
    
    backtest = BacktestingAdaptativo(capital_inicial=10000)
    
    print("🚀 BACKTESTING SISTEMA ADAPTATIVO")
    print("="*70)
    print("Probando configuraciones para diferentes regímenes...")
    print("="*70)
    
    # Test completo
    results = backtest.run_adaptive_backtest(
        symbols=['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD'],
        days=90  # 90 días para análisis más robusto
    )
    
    if results:
        print(f"\\n✅ Backtesting completado")
        print(f"💡 El sistema está {'✅ OPTIMIZADO' if results['results']['win_rate'] > 60 else '⚠️ NECESITA MEJORAS'} para condiciones de mercado variables")
    
    return results

if __name__ == "__main__":
    demo_backtesting_adaptativo()