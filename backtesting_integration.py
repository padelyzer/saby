#!/usr/bin/env python3
"""
Módulo de Backtesting Integrado para la UX
Backtesting completo optimizado para interfaz Streamlit
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BacktestingIntegrado:
    """
    Sistema de backtesting integrado para la UX
    """
    
    def __init__(self, capital_inicial=10000):
        self.capital_inicial = capital_inicial
        self.capital_actual = capital_inicial
        
        # Configuración V2 + Liquidez (QUE FUNCIONABA)
        self.config = {
            'min_volume_ratio': 1.2,      # Accesible para generar señales
            'min_risk_reward': 1.8,       # R:R realista
            'min_score': 6.0,             # Score V2 original
            'atr_stop_multiplier': 2.0,   # Stops amplios para mejor R:R
            'trailing_activation': 0.015, # 1.5% conservador
            'trailing_distance': 0.005,  # 0.5% estándar
            'partial_close_pct': 0.30,   # 30% para dejar correr ganadores
            'max_position_size': 0.02    # 2% base (antes de leverage)
        }
        
        self.trades_ejecutados = []
        self.equity_curve = []
    
    def calculate_indicators(self, df):
        """Calcula indicadores técnicos optimizados"""
        
        # EMAs
        df['EMA_21'] = df['Close'].ewm(span=21).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        
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
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # ATR
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                np.abs(df['High'] - df['Close'].shift(1)),
                np.abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        # Volume ratio con protección contra división por cero
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA'].replace(0, 1)
        
        # Rellenar NaN con 1.0 para evitar problemas
        df['Volume_Ratio'] = df['Volume_Ratio'].fillna(1.0)
        
        # Asegurar valores mínimos realistas
        df['Volume_Ratio'] = df['Volume_Ratio'].clip(lower=0.1)
        
        return df
    
    def generate_signal(self, df, ticker):
        """Genera señal usando estrategias del sistema definitivo"""
        
        if len(df) < 50:
            return None
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Verificar datos válidos
        required_fields = ['Close', 'EMA_21', 'RSI', 'ATR', 'Volume_Ratio']
        if any(pd.isna(current[field]) for field in required_fields):
            return None
        
        signal = None
        
        # Estrategia 1: EMA Pullback (Principal)
        trend_bullish = current['Close'] > current['EMA_21'] > current['EMA_50']
        trend_bearish = current['Close'] < current['EMA_21'] < current['EMA_50']
        
        pullback_long = (trend_bullish and 
                        prev['Close'] < prev['EMA_21'] and 
                        current['Close'] > current['EMA_21'] and
                        current['RSI'] > 30 and current['RSI'] < 70)  # RSI en zona neutral
        
        pullback_short = (trend_bearish and 
                         prev['Close'] > prev['EMA_21'] and 
                         current['Close'] < current['EMA_21'] and
                         current['RSI'] > 30 and current['RSI'] < 70)  # RSI en zona neutral
        
        if pullback_long and current['Volume_Ratio'] >= self.config['min_volume_ratio']:
            signal = self._create_long_signal(df, ticker, current, "EMA Pullback")
            
        elif pullback_short and current['Volume_Ratio'] >= self.config['min_volume_ratio']:
            signal = self._create_short_signal(df, ticker, current, "EMA Pullback")
        
        # Estrategia 2: Volume Breakout
        if not signal:
            range_24h = df['High'].rolling(24).max() - df['Low'].rolling(24).min()
            if range_24h.iloc[-1] > 0:
                
                breakout_long = (current['Close'] > df['High'].rolling(24).max().iloc[-2] and
                               current['Volume_Ratio'] >= 1.5)  # Reducido
                
                breakout_short = (current['Close'] < df['Low'].rolling(24).min().iloc[-2] and
                                current['Volume_Ratio'] >= 1.5)  # Reducido
                
                if breakout_long:
                    signal = self._create_long_signal(df, ticker, current, "Volume Breakout")
                elif breakout_short:
                    signal = self._create_short_signal(df, ticker, current, "Volume Breakout")
        
        # Estrategia 3: RSI Extremos más accesible
        if not signal:
            # RSI Oversold más accesible
            if (current['RSI'] <= 35 and 
                current['Volume_Ratio'] >= self.config['min_volume_ratio']):
                signal = self._create_long_signal(df, ticker, current, "RSI Oversold")
            
            # RSI Overbought más accesible
            elif (current['RSI'] >= 65 and 
                  current['Volume_Ratio'] >= self.config['min_volume_ratio']):
                signal = self._create_short_signal(df, ticker, current, "RSI Overbought")
        
        # Verificar calidad mínima
        if signal and signal['score'] >= self.config['min_score']:
            return signal
        
        return None
    
    def _create_long_signal(self, df, ticker, current, strategy):
        """Crea señal LONG optimizada"""
        
        entry_price = current['Close']
        atr = current['ATR']
        
        # Stop loss amplio (clave del éxito)
        stop_loss = entry_price - (atr * self.config['atr_stop_multiplier'])
        
        # Targets más ambiciosos para mejor R:R
        target_1 = entry_price + (atr * 2.0)   # Target 1 más lejano
        target_2 = entry_price + (atr * 4.0)   # Target 2 mucho más lejano
        
        # REVERTIR A SISTEMA EMPÍRICO V2 (QUE FUNCIONABA)
        # Importar sistema empírico V2
        from scoring_empirico_v2 import ScoringEmpiricoV2
        scoring_system = ScoringEmpiricoV2()
        
        # Calcular score empírico
        score, score_details = scoring_system.calculate_empirical_score_long(df, current)
        
        # Risk-reward
        risk = entry_price - stop_loss
        reward = target_2 - entry_price
        risk_reward = reward / risk if risk > 0 else 0
        
        if risk_reward >= self.config['min_risk_reward']:
            return {
                'ticker': ticker,
                'type': 'LONG',
                'strategy': strategy,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'target_1': target_1,
                'target_2': target_2,
                'score': min(score, 10),
                'risk_reward': risk_reward,
                'volume_ratio': current['Volume_Ratio'],
                'rsi': current['RSI']
            }
        
        return None
    
    def _create_short_signal(self, df, ticker, current, strategy):
        """Crea señal SHORT optimizada"""
        
        entry_price = current['Close']
        atr = current['ATR']
        
        # Stop loss amplio
        stop_loss = entry_price + (atr * self.config['atr_stop_multiplier'])
        
        # Targets más ambiciosos para SHORT
        target_1 = entry_price - (atr * 2.0)   # Target 1 más lejano
        target_2 = entry_price - (atr * 4.0)   # Target 2 mucho más lejano
        
        # REVERTIR A SISTEMA EMPÍRICO V2 para SHORT
        from scoring_empirico_v2 import ScoringEmpiricoV2
        scoring_system = ScoringEmpiricoV2()
        
        # Calcular score empírico para SHORT
        score, score_details = scoring_system.calculate_empirical_score_short(df, current)
        
        # Risk-reward
        risk = stop_loss - entry_price
        reward = entry_price - target_2
        risk_reward = reward / risk if risk > 0 else 0
        
        if risk_reward >= self.config['min_risk_reward']:
            return {
                'ticker': ticker,
                'type': 'SHORT',
                'strategy': strategy,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'target_1': target_1,
                'target_2': target_2,
                'score': min(score, 10),
                'risk_reward': risk_reward,
                'volume_ratio': current['Volume_Ratio'],
                'rsi': current['RSI']
            }
        
        return None
    
    def simulate_trade(self, signal, df, entry_idx):
        """Simula trade con gestión optimizada del sistema definitivo"""
        
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        target_1 = signal['target_1']
        target_2 = signal['target_2']
        signal_type = signal['type']
        
        # Position sizing con apalancamiento dinámico por score
        score = signal['score']
        
        # Base position size (capital real)
        base_position = 0.02  # 2% base
        
        # Apalancamiento empírico V2
        from scoring_empirico_v2 import ScoringEmpiricoV2
        scoring_system = ScoringEmpiricoV2()
        leverage = scoring_system.get_leverage_empirical(score)
        position_size = base_position
        
        # Calcular exposición total con apalancamiento
        total_exposure = position_size * leverage
        
        # Usar position_size original para cálculos (representa exposición total)
        position_size = min(total_exposure, 0.15)  # Cap al 15% de exposición máxima
        
        # Variables de gestión
        trailing_stop = None
        partial_closed = False
        remaining_size = 1.0
        total_profit = 0
        exit_reason = 'TIME'
        
        # Simular hasta 96 períodos (4 días)
        for i in range(entry_idx + 1, min(entry_idx + 96, len(df))):
            current_bar = df.iloc[i]
            current_price = current_bar['Close']
            
            if signal_type == 'LONG':
                current_profit_pct = (current_price - entry_price) / entry_price
                
                # Gestión de trailing stop agresivo
                if current_profit_pct >= self.config['trailing_activation']:
                    new_trailing = current_price * (1 - self.config['trailing_distance'])
                    if trailing_stop is None or new_trailing > trailing_stop:
                        trailing_stop = new_trailing
                
                # Target 1 (cierre parcial)
                if current_bar['High'] >= target_1 and not partial_closed:
                    partial_profit = ((target_1 - entry_price) / entry_price) * self.config['partial_close_pct']
                    total_profit += partial_profit
                    remaining_size = 1 - self.config['partial_close_pct']
                    partial_closed = True
                    continue
                
                # Target 2 (cierre total)
                elif current_bar['High'] >= target_2:
                    final_profit = ((target_2 - entry_price) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'TP'
                    break
                
                # Stop loss
                elif current_bar['Low'] <= stop_loss:
                    final_profit = ((stop_loss - entry_price) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'SL'
                    break
                
                # Trailing stop
                elif trailing_stop and current_bar['Low'] <= trailing_stop:
                    final_profit = ((trailing_stop - entry_price) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'TRAIL'
                    break
            
            else:  # SHORT
                current_profit_pct = (entry_price - current_price) / entry_price
                
                if current_profit_pct >= self.config['trailing_activation']:
                    new_trailing = current_price * (1 + self.config['trailing_distance'])
                    if trailing_stop is None or new_trailing < trailing_stop:
                        trailing_stop = new_trailing
                
                if current_bar['Low'] <= target_1 and not partial_closed:
                    partial_profit = ((entry_price - target_1) / entry_price) * self.config['partial_close_pct']
                    total_profit += partial_profit
                    remaining_size = 1 - self.config['partial_close_pct']
                    partial_closed = True
                    continue
                
                elif current_bar['Low'] <= target_2:
                    final_profit = ((entry_price - target_2) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'TP'
                    break
                
                elif current_bar['High'] >= stop_loss:
                    final_profit = ((entry_price - stop_loss) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'SL'
                    break
                
                elif trailing_stop and current_bar['High'] >= trailing_stop:
                    final_profit = ((entry_price - trailing_stop) / entry_price) * remaining_size
                    total_profit += final_profit
                    exit_reason = 'TRAIL'
                    break
        else:
            # Salida por tiempo
            final_profit = ((current_price - entry_price) / entry_price if signal_type == 'LONG' 
                          else (entry_price - current_price) / entry_price) * remaining_size
            total_profit += final_profit
        
        # Calcular montos en dólares con apalancamiento
        capital_real = self.capital_inicial * (position_size / leverage)  # Capital real sin leverage
        exposicion_total = self.capital_inicial * position_size  # Exposición con leverage
        profit_usd = exposicion_total * total_profit  # Ganancia amplificada por leverage
        exit_price_final = current_price if 'current_price' in locals() else (target_2 if exit_reason == 'TP' else stop_loss)
        
        return {
            'ticker': signal['ticker'],
            'type': signal_type,
            'strategy': signal['strategy'],
            'entry_price': entry_price,
            'exit_price': exit_price_final,
            'profit_pct': total_profit * 100,
            'profit_usd': profit_usd,
            'capital_usado': capital_real,  # Capital real invertido
            'exposicion_total': exposicion_total,  # Exposición con leverage
            'leverage': leverage,  # Nivel de apalancamiento usado
            'exit_reason': exit_reason,
            'position_size': position_size,
            'score': signal['score'],
            'risk_reward': signal['risk_reward'],
            'had_partial_close': partial_closed,
            'had_trailing': trailing_stop is not None,
            'duration_periods': i - entry_idx if 'i' in locals() else 96
        }
    
    def run_backtest(self, tickers, periods_days=30, progress_callback=None):
        """Ejecuta backtesting completo"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=periods_days)
        
        all_trades = []
        total_tickers = len(tickers)
        
        for idx, ticker in enumerate(tickers):
            if progress_callback:
                progress_callback(f"Analizando {ticker}...", (idx + 1) / total_tickers)
            
            try:
                # Descargar datos
                data = yf.Ticker(ticker)
                df = data.history(
                    start=start_date - timedelta(days=30), 
                    end=end_date + timedelta(days=1), 
                    interval='1h'
                )
                
                if len(df) < 100:
                    continue
                
                # Calcular indicadores
                df = self.calculate_indicators(df)
                
                # Buscar señales (muestreo cada 6 horas para calidad)
                señales_encontradas = 0
                for i in range(50, len(df), 6):
                    if señales_encontradas >= 5:  # Máximo por ticker para calidad
                        break
                    
                    current_date = df.index[i].date()
                    if current_date < start_date.date():
                        continue
                    
                    # Subset histórico
                    historical_df = df.iloc[:i+1].copy()
                    
                    signal = self.generate_signal(historical_df, ticker)
                    if signal:
                        trade_result = self.simulate_trade(signal, df, i)
                        all_trades.append(trade_result)
                        señales_encontradas += 1
                        
            except Exception as e:
                continue
        
        return all_trades
    
    def analyze_results(self, trades):
        """Análisis completo de resultados"""
        
        if not trades:
            return None
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['profit_pct'] > 0]
        losing_trades = [t for t in trades if t['profit_pct'] <= 0]
        
        # Métricas básicas
        win_rate = (len(winning_trades) / total_trades) * 100
        avg_win = np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Profit Factor
        gross_profit = sum(t['profit_pct'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['profit_pct'] for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Total return
        total_return = sum(t['profit_pct'] * t['position_size'] for t in trades)
        
        # Métricas avanzadas
        avg_score = np.mean([t['score'] for t in trades])
        avg_rr = np.mean([t['risk_reward'] for t in trades])
        avg_duration = np.mean([t['duration_periods'] for t in trades])
        
        # Análisis por estrategia
        strategies = {}
        for trade in trades:
            strategy = trade['strategy']
            if strategy not in strategies:
                strategies[strategy] = {'trades': [], 'wins': 0}
            strategies[strategy]['trades'].append(trade)
            if trade['profit_pct'] > 0:
                strategies[strategy]['wins'] += 1
        
        strategy_analysis = {}
        for strategy, data in strategies.items():
            strategy_analysis[strategy] = {
                'count': len(data['trades']),
                'win_rate': (data['wins'] / len(data['trades']) * 100),
                'avg_profit': np.mean([t['profit_pct'] for t in data['trades']])
            }
        
        # Análisis por exit reason
        exit_reasons = {}
        for trade in trades:
            reason = trade['exit_reason']
            if reason not in exit_reasons:
                exit_reasons[reason] = {'count': 0, 'profits': [], 'wins': 0}
            exit_reasons[reason]['count'] += 1
            exit_reasons[reason]['profits'].append(trade['profit_pct'])
            if trade['profit_pct'] > 0:
                exit_reasons[reason]['wins'] += 1
        
        # Gestión avanzada
        partial_trades = len([t for t in trades if t['had_partial_close']])
        trailing_trades = len([t for t in trades if t['had_trailing']])
        
        # Evaluación del sistema
        if win_rate >= 65 and profit_factor >= 1.5:
            rating = "🌟 EXCELENTE"
            status = "LISTO PARA TRADING"
        elif win_rate >= 60 and profit_factor >= 1.3:
            rating = "✅ BUENO"
            status = "APTO CON MONITOREO"
        elif win_rate >= 55 and profit_factor >= 1.1:
            rating = "⚠️ ACEPTABLE"
            status = "NECESITA AJUSTES"
        else:
            rating = "❌ INSUFICIENTE"
            status = "REVISAR ESTRATEGIA"
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_return': total_return,
            'avg_score': avg_score,
            'avg_rr': avg_rr,
            'avg_duration': avg_duration,
            'partial_trades': partial_trades,
            'trailing_trades': trailing_trades,
            'strategy_analysis': strategy_analysis,
            'exit_analysis': exit_reasons,
            'rating': rating,
            'status': status,
            'trades': trades
        }