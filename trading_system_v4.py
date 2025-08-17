#!/usr/bin/env python3
"""
Trading System V4.0 - Sistema Adaptativo Inteligente
Detecta el régimen del mercado y ajusta estrategias automáticamente
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import json
warnings.filterwarnings('ignore')

class MarketRegimeDetector:
    """Detecta el régimen actual del mercado"""
    
    @staticmethod
    def calculate_atr_ratio(df):
        """Calcula ratio de volatilidad"""
        current_atr = df['ATR'].iloc[-1]
        avg_atr = df['ATR'].rolling(50).mean().iloc[-1]
        return current_atr / avg_atr if avg_atr > 0 else 1
    
    @staticmethod
    def calculate_trend_strength(df):
        """Calcula fuerza de tendencia usando ADX"""
        # ADX simplificado
        plus_dm = df['High'].diff()
        minus_dm = -df['Low'].diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = pd.concat([
            df['High'] - df['Low'],
            abs(df['High'] - df['Close'].shift()),
            abs(df['Low'] - df['Close'].shift())
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(14).mean()
        
        return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 25
    
    @staticmethod
    def calculate_atr(df):
        """Calcula ATR para el dataframe"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(14).mean()
        return atr
    
    @staticmethod
    def detect_regime(df_1h, df_4h, df_daily):
        """
        Detecta el régimen del mercado
        Returns: TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE
        """
        regime_scores = {
            'TRENDING_UP': 0,
            'TRENDING_DOWN': 0,
            'RANGING': 0,
            'VOLATILE': 0
        }
        
        # Calcular ATR primero
        df_4h['ATR'] = MarketRegimeDetector.calculate_atr(df_4h)
        
        # 1. Análisis de tendencia en daily
        if len(df_daily) > 50:
            daily_ema20 = df_daily['Close'].ewm(span=20).mean()
            daily_ema50 = df_daily['Close'].ewm(span=50).mean()
            
            if daily_ema20.iloc[-1] > daily_ema50.iloc[-1]:
                if daily_ema20.iloc[-1] > daily_ema20.iloc[-5]:
                    regime_scores['TRENDING_UP'] += 3
            elif daily_ema20.iloc[-1] < daily_ema50.iloc[-1]:
                if daily_ema20.iloc[-1] < daily_ema20.iloc[-5]:
                    regime_scores['TRENDING_DOWN'] += 3
        
        # 2. Análisis de volatilidad
        atr_ratio = MarketRegimeDetector.calculate_atr_ratio(df_4h)
        if atr_ratio > 1.5:
            regime_scores['VOLATILE'] += 2
        elif atr_ratio < 0.7:
            regime_scores['RANGING'] += 2
        
        # 3. ADX para fuerza de tendencia
        adx = MarketRegimeDetector.calculate_trend_strength(df_4h)
        if adx > 40:
            # Tendencia fuerte
            if df_4h['Close'].iloc[-1] > df_4h['Close'].iloc[-20]:
                regime_scores['TRENDING_UP'] += 2
            else:
                regime_scores['TRENDING_DOWN'] += 2
        elif adx < 20:
            # Sin tendencia
            regime_scores['RANGING'] += 3
        
        # 4. Análisis de estructura de precio
        recent_highs = df_4h['High'].rolling(10).max()
        recent_lows = df_4h['Low'].rolling(10).min()
        
        higher_highs = (recent_highs.iloc[-1] > recent_highs.iloc[-10])
        higher_lows = (recent_lows.iloc[-1] > recent_lows.iloc[-10])
        lower_highs = (recent_highs.iloc[-1] < recent_highs.iloc[-10])
        lower_lows = (recent_lows.iloc[-1] < recent_lows.iloc[-10])
        
        if higher_highs and higher_lows:
            regime_scores['TRENDING_UP'] += 2
        elif lower_highs and lower_lows:
            regime_scores['TRENDING_DOWN'] += 2
        else:
            regime_scores['RANGING'] += 1
        
        # 5. Bollinger Bands para detectar rango
        bb_middle = df_4h['Close'].rolling(20).mean()
        bb_std = df_4h['Close'].rolling(20).std()
        bb_width = (bb_std * 2) / bb_middle
        
        if bb_width.iloc[-1] < bb_width.rolling(50).mean().iloc[-1] * 0.8:
            regime_scores['RANGING'] += 2
        
        # Determinar régimen dominante
        max_regime = max(regime_scores.items(), key=lambda x: x[1])
        
        # Información adicional
        regime_info = {
            'regime': max_regime[0],
            'confidence': max_regime[1] / sum(regime_scores.values()) if sum(regime_scores.values()) > 0 else 0,
            'scores': regime_scores,
            'adx': adx,
            'atr_ratio': atr_ratio
        }
        
        return regime_info


class TrendStrategy:
    """Estrategia para mercados en tendencia"""
    
    @staticmethod
    def generate_signal(df_1h, df_4h, df_daily, regime_info):
        """Genera señales para mercados trending"""
        signals = []
        
        # Calcular indicadores en 1H
        df_1h = TrendStrategy.calculate_indicators(df_1h)
        current = df_1h.iloc[-1]
        
        signal_strength = 0
        signal_type = None
        
        if regime_info['regime'] == 'TRENDING_UP':
            # Buscar pullbacks en uptrend
            if current['RSI'] < 40:  # Oversold en uptrend
                signal_strength += 3
                signal_type = 'LONG'
                signals.append('PULLBACK_IN_UPTREND')
            
            if current['Close'] > current['EMA_20'] and current['MACD'] > current['MACD_Signal']:
                signal_strength += 2
                signals.append('TREND_CONTINUATION')
            
            # Breakout
            if current['Close'] > df_1h['High'].rolling(20).max().iloc[-2]:
                signal_strength += 2
                signal_type = 'LONG'
                signals.append('BREAKOUT_UP')
                
        elif regime_info['regime'] == 'TRENDING_DOWN':
            # Buscar rallies en downtrend
            if current['RSI'] > 60:  # Overbought en downtrend
                signal_strength += 3
                signal_type = 'SHORT'
                signals.append('RALLY_IN_DOWNTREND')
            
            if current['Close'] < current['EMA_20'] and current['MACD'] < current['MACD_Signal']:
                signal_strength += 2
                signals.append('TREND_CONTINUATION')
            
            # Breakdown
            if current['Close'] < df_1h['Low'].rolling(20).min().iloc[-2]:
                signal_strength += 2
                signal_type = 'SHORT'
                signals.append('BREAKDOWN')
        
        if signal_strength >= 4 and signal_type:
            return {
                'type': signal_type,
                'strength': signal_strength,
                'confidence': min(signal_strength / 7, 0.9),
                'signals': signals,
                'entry': current['Close'],
                'atr': current['ATR'],
                'strategy': 'TREND'
            }
        
        return None
    
    @staticmethod
    def calculate_indicators(df):
        """Calcula indicadores para trend following"""
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # EMAs
        df['EMA_20'] = df['Close'].ewm(span=20).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        return df


class RangeStrategy:
    """Estrategia para mercados laterales (mean reversion)"""
    
    @staticmethod
    def generate_signal(df_1h, df_4h, df_daily, regime_info):
        """Genera señales para mercados ranging"""
        signals = []
        
        # Calcular indicadores
        df_1h = RangeStrategy.calculate_indicators(df_1h)
        current = df_1h.iloc[-1]
        
        signal_strength = 0
        signal_type = None
        
        # Mean Reversion con Bollinger Bands
        if current['Close'] <= current['BB_Lower']:
            signal_strength += 3
            signal_type = 'LONG'
            signals.append('BOUNCE_FROM_BB_LOWER')
        elif current['Close'] >= current['BB_Upper']:
            signal_strength += 3
            signal_type = 'SHORT'
            signals.append('BOUNCE_FROM_BB_UPPER')
        
        # RSI extremos para ranging
        if current['RSI'] < 30:
            signal_strength += 2
            if signal_type != 'SHORT':
                signal_type = 'LONG'
            signals.append('RSI_OVERSOLD_EXTREME')
        elif current['RSI'] > 70:
            signal_strength += 2
            if signal_type != 'LONG':
                signal_type = 'SHORT'
            signals.append('RSI_OVERBOUGHT_EXTREME')
        
        # Stochastic para confirmación
        if current['Stoch_K'] < 20 and current['Stoch_D'] < 20:
            signal_strength += 1
            if signal_type != 'SHORT':
                signal_type = 'LONG'
            signals.append('STOCH_OVERSOLD')
        elif current['Stoch_K'] > 80 and current['Stoch_D'] > 80:
            signal_strength += 1
            if signal_type != 'LONG':
                signal_type = 'SHORT'
            signals.append('STOCH_OVERBOUGHT')
        
        # Support/Resistance levels
        support = df_1h['Low'].rolling(50).min().iloc[-1]
        resistance = df_1h['High'].rolling(50).max().iloc[-1]
        range_size = resistance - support
        
        if current['Close'] <= support + (range_size * 0.1):
            signal_strength += 2
            if signal_type != 'SHORT':
                signal_type = 'LONG'
            signals.append('AT_SUPPORT')
        elif current['Close'] >= resistance - (range_size * 0.1):
            signal_strength += 2
            if signal_type != 'LONG':
                signal_type = 'SHORT'
            signals.append('AT_RESISTANCE')
        
        if signal_strength >= 4 and signal_type:
            return {
                'type': signal_type,
                'strength': signal_strength,
                'confidence': min(signal_strength / 8, 0.85),
                'signals': signals,
                'entry': current['Close'],
                'atr': current['ATR'],
                'support': support,
                'resistance': resistance,
                'strategy': 'RANGE'
            }
        
        return None
    
    @staticmethod
    def calculate_indicators(df):
        """Calcula indicadores para mean reversion"""
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        
        # Stochastic
        low_min = df['Low'].rolling(14).min()
        high_max = df['High'].rolling(14).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        return df


class VolatileStrategy:
    """Estrategia para mercados volátiles"""
    
    @staticmethod
    def generate_signal(df_1h, df_4h, df_daily, regime_info):
        """Genera señales para mercados volátiles - más conservador"""
        # En mercados muy volátiles, ser más selectivo
        signals = []
        
        df_1h = VolatileStrategy.calculate_indicators(df_1h)
        current = df_1h.iloc[-1]
        
        signal_strength = 0
        signal_type = None
        
        # Solo operar en extremos con confirmación múltiple
        if current['RSI'] < 20:  # Ultra oversold
            signal_strength += 4
            signal_type = 'LONG'
            signals.append('EXTREME_OVERSOLD')
        elif current['RSI'] > 80:  # Ultra overbought
            signal_strength += 4
            signal_type = 'SHORT'
            signals.append('EXTREME_OVERBOUGHT')
        else:
            return None  # No operar si no hay extremos
        
        # Confirmación con volumen
        if current['Volume'] > df_1h['Volume'].rolling(20).mean().iloc[-1] * 2:
            signal_strength += 2
            signals.append('HIGH_VOLUME_CONFIRMATION')
        
        # Divergencia para confirmación
        if signal_type == 'LONG' and current['MACD'] > df_1h['MACD'].iloc[-5]:
            signal_strength += 1
            signals.append('BULLISH_DIVERGENCE')
        elif signal_type == 'SHORT' and current['MACD'] < df_1h['MACD'].iloc[-5]:
            signal_strength += 1
            signals.append('BEARISH_DIVERGENCE')
        
        if signal_strength >= 5:
            return {
                'type': signal_type,
                'strength': signal_strength,
                'confidence': min(signal_strength / 7, 0.75),  # Menor confianza en volátil
                'signals': signals,
                'entry': current['Close'],
                'atr': current['ATR'],
                'strategy': 'VOLATILE'
            }
        
        return None
    
    @staticmethod
    def calculate_indicators(df):
        """Calcula indicadores para mercados volátiles"""
        # RSI más sensible
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=10).mean()  # Periodo más corto
        loss = (-delta.where(delta < 0, 0)).rolling(window=10).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        return df


class AdaptiveTradingSystem:
    """Sistema principal adaptativo V4.0"""
    
    def __init__(self, symbol, capital=1000):
        self.symbol = symbol
        self.capital = capital
        self.initial_capital = capital
        
        # Parámetros adaptativos
        self.params = {
            'base_risk': 0.01,  # 1% riesgo base
            'max_risk': 0.02,   # 2% riesgo máximo
            'min_confidence': 0.5,
            
            # Stops dinámicos según régimen
            'trend_stop_multiplier': 2.0,
            'range_stop_multiplier': 1.5,
            'volatile_stop_multiplier': 3.0,
            
            # Targets dinámicos
            'trend_target_multiplier': 3.0,
            'range_target_multiplier': 1.0,  # Target en el otro extremo del rango
            'volatile_target_multiplier': 2.0,
        }
        
        self.trades = []
        self.signals = []
        
    def get_multi_timeframe_data(self, days=60):
        """Obtiene datos en múltiples timeframes"""
        try:
            ticker = yf.Ticker(self.symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 3 timeframes
            df_1h = ticker.history(start=start_date, end=end_date, interval='1h')
            df_4h = ticker.history(start=start_date, end=end_date, interval='1h')
            df_daily = ticker.history(start=start_date, end=end_date, interval='1d')
            
            # Resample 1h to 4h
            df_4h = df_1h.resample('4H').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            return df_1h, df_4h, df_daily
            
        except Exception as e:
            print(f"Error obteniendo datos: {e}")
            return None, None, None
    
    def generate_adaptive_signal(self, df_1h, df_4h, df_daily):
        """Genera señal adaptativa según el régimen del mercado"""
        
        # 1. Detectar régimen
        regime_info = MarketRegimeDetector.detect_regime(df_1h, df_4h, df_daily)
        
        print(f"📊 Régimen detectado: {regime_info['regime']} (confianza: {regime_info['confidence']:.1%})")
        
        # 2. Aplicar estrategia según régimen
        signal = None
        
        if regime_info['regime'] == 'TRENDING_UP' or regime_info['regime'] == 'TRENDING_DOWN':
            signal = TrendStrategy.generate_signal(df_1h, df_4h, df_daily, regime_info)
            
        elif regime_info['regime'] == 'RANGING':
            signal = RangeStrategy.generate_signal(df_1h, df_4h, df_daily, regime_info)
            
        elif regime_info['regime'] == 'VOLATILE':
            signal = VolatileStrategy.generate_signal(df_1h, df_4h, df_daily, regime_info)
        
        # 3. Ajustar parámetros según régimen
        if signal:
            signal['regime'] = regime_info['regime']
            signal['regime_confidence'] = regime_info['confidence']
            
            # Ajustar riesgo según confianza
            base_risk = self.params['base_risk']
            if regime_info['confidence'] > 0.7:
                signal['risk'] = base_risk * 1.5  # Más riesgo con alta confianza
            elif regime_info['confidence'] < 0.4:
                signal['risk'] = base_risk * 0.5  # Menos riesgo con baja confianza
            else:
                signal['risk'] = base_risk
            
            # Ajustar stops según régimen
            if regime_info['regime'] in ['TRENDING_UP', 'TRENDING_DOWN']:
                signal['stop_multiplier'] = self.params['trend_stop_multiplier']
                signal['target_multiplier'] = self.params['trend_target_multiplier']
            elif regime_info['regime'] == 'RANGING':
                signal['stop_multiplier'] = self.params['range_stop_multiplier']
                # Para ranging, el target es el otro extremo
                if signal['type'] == 'LONG':
                    signal['target_price'] = signal.get('resistance', signal['entry'] + signal['atr'])
                else:
                    signal['target_price'] = signal.get('support', signal['entry'] - signal['atr'])
            else:  # VOLATILE
                signal['stop_multiplier'] = self.params['volatile_stop_multiplier']
                signal['target_multiplier'] = self.params['volatile_target_multiplier']
        
        return signal
    
    def calculate_position_size(self, signal):
        """Calcula el tamaño de posición basado en riesgo dinámico"""
        risk_amount = self.capital * signal['risk']
        
        if signal['type'] == 'LONG':
            stop_distance = signal['entry'] - (signal['entry'] - signal['atr'] * signal['stop_multiplier'])
        else:
            stop_distance = (signal['entry'] + signal['atr'] * signal['stop_multiplier']) - signal['entry']
        
        position_size = risk_amount / abs(stop_distance) if stop_distance != 0 else 0
        
        # Limitar al capital disponible
        max_position = self.capital * 0.95  # Usar máximo 95% del capital
        position_size = min(position_size, max_position)
        
        return position_size
    
    def execute_signal(self, signal):
        """Ejecuta la señal con gestión de riesgo adaptativa"""
        
        # Calcular stops y targets
        if signal['type'] == 'LONG':
            stop_loss = signal['entry'] - (signal['atr'] * signal['stop_multiplier'])
            if 'target_price' in signal:
                take_profit = signal['target_price']
            else:
                take_profit = signal['entry'] + (signal['atr'] * signal.get('target_multiplier', 2.0))
        else:
            stop_loss = signal['entry'] + (signal['atr'] * signal['stop_multiplier'])
            if 'target_price' in signal:
                take_profit = signal['target_price']
            else:
                take_profit = signal['entry'] - (signal['atr'] * signal.get('target_multiplier', 2.0))
        
        position_size = self.calculate_position_size(signal)
        
        trade = {
            'timestamp': datetime.now(),
            'symbol': self.symbol,
            'type': signal['type'],
            'entry': signal['entry'],
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'risk': signal['risk'],
            'confidence': signal['confidence'],
            'regime': signal['regime'],
            'strategy': signal['strategy'],
            'signals': signal['signals']
        }
        
        self.trades.append(trade)
        
        return trade
    
    def run_analysis(self):
        """Ejecuta análisis completo del mercado"""
        print(f"\n{'='*60}")
        print(f"🤖 SISTEMA ADAPTATIVO V4.0 - {self.symbol}")
        print(f"{'='*60}\n")
        
        # Obtener datos multi-timeframe
        df_1h, df_4h, df_daily = self.get_multi_timeframe_data()
        
        if df_1h is None:
            print("❌ Error obteniendo datos")
            return None
        
        # Generar señal adaptativa
        signal = self.generate_adaptive_signal(df_1h, df_4h, df_daily)
        
        if signal:
            print(f"\n✅ SEÑAL GENERADA:")
            print(f"  Tipo: {signal['type']}")
            print(f"  Estrategia: {signal['strategy']}")
            print(f"  Confianza: {signal['confidence']:.1%}")
            print(f"  Señales: {', '.join(signal['signals'])}")
            
            # Ejecutar señal
            trade = self.execute_signal(signal)
            
            print(f"\n📊 TRADE EJECUTADO:")
            print(f"  Entry: ${trade['entry']:.4f}")
            print(f"  Stop Loss: ${trade['stop_loss']:.4f}")
            print(f"  Take Profit: ${trade['take_profit']:.4f}")
            print(f"  Riesgo: {trade['risk']*100:.1f}% del capital")
            
            return trade
        else:
            print("\n⚠️ No hay señal en este momento")
            print("  El sistema está esperando mejores condiciones")
            return None


class DCAStrategy:
    """Estrategia DCA (Dollar Cost Averaging) para acumulación"""
    
    def __init__(self, symbols, capital=206):
        self.symbols = symbols
        self.capital = capital
        self.initial_capital = capital
        
        self.params = {
            'buy_on_dip': -5,  # Comprar cuando baje 5%
            'strong_buy_on_dip': -10,  # Comprar más cuando baje 10%
            'allocation_per_symbol': capital / len(symbols),
            'min_purchase': 10,  # Compra mínima $10
        }
        
        self.portfolio = {symbol: 0 for symbol in symbols}
        self.purchase_history = []
    
    def check_dip_opportunity(self, symbol):
        """Verifica si hay oportunidad de compra por caída"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='7d', interval='1d')
            
            if len(df) < 2:
                return None
            
            current_price = df['Close'].iloc[-1]
            yesterday_price = df['Close'].iloc[-2]
            week_high = df['High'].max()
            
            # Calcular caída desde ayer
            daily_change = ((current_price / yesterday_price) - 1) * 100
            
            # Calcular caída desde máximo semanal
            dip_from_high = ((current_price / week_high) - 1) * 100
            
            opportunity = {
                'symbol': symbol,
                'current_price': current_price,
                'daily_change': daily_change,
                'dip_from_high': dip_from_high,
                'signal': None,
                'amount': 0
            }
            
            # Determinar si comprar
            allocated = self.params['allocation_per_symbol']
            spent = self.portfolio.get(symbol, 0)
            available = allocated - spent
            
            if available >= self.params['min_purchase']:
                if dip_from_high <= self.params['strong_buy_on_dip']:
                    opportunity['signal'] = 'STRONG_BUY'
                    opportunity['amount'] = min(available * 0.5, self.capital * 0.1)
                elif dip_from_high <= self.params['buy_on_dip']:
                    opportunity['signal'] = 'BUY'
                    opportunity['amount'] = min(available * 0.25, self.capital * 0.05)
            
            return opportunity
            
        except Exception as e:
            print(f"Error checking {symbol}: {e}")
            return None
    
    def scan_opportunities(self):
        """Escanea todos los símbolos por oportunidades DCA"""
        opportunities = []
        
        print(f"\n{'='*60}")
        print(f"🔍 ESCANEANDO OPORTUNIDADES DCA")
        print(f"Capital disponible: ${self.capital:.2f}")
        print(f"{'='*60}\n")
        
        for symbol in self.symbols:
            opp = self.check_dip_opportunity(symbol)
            if opp and opp['signal']:
                opportunities.append(opp)
                
                print(f"✅ {symbol}:")
                print(f"  Precio: ${opp['current_price']:.4f}")
                print(f"  Cambio diario: {opp['daily_change']:.2f}%")
                print(f"  Desde máximo: {opp['dip_from_high']:.2f}%")
                print(f"  Señal: {opp['signal']}")
                print(f"  Monto sugerido: ${opp['amount']:.2f}\n")
        
        if not opportunities:
            print("⚠️ No hay oportunidades de compra en este momento")
            print("  Esperando caídas de -5% o más")
        
        return opportunities


def main():
    """Función principal de demostración"""
    
    print("\n" + "="*80)
    print(" SISTEMA DE TRADING ADAPTATIVO V4.0 ".center(80, "="))
    print("="*80)
    
    # Símbolos para analizar
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'LINK-USD']
    
    # 1. Sistema Adaptativo para trading activo
    print("\n📈 ANÁLISIS ADAPTATIVO DE MERCADO")
    print("-"*60)
    
    for symbol in symbols[:3]:  # Analizar primeros 3
        system = AdaptiveTradingSystem(symbol, capital=1000)
        trade = system.run_analysis()
        
        if trade:
            # Guardar señal en archivo
            filename = f"signal_{symbol.replace('-USD', '').lower()}.json"
            with open(filename, 'w') as f:
                trade_dict = {
                    'timestamp': trade['timestamp'].isoformat(),
                    'symbol': trade['symbol'],
                    'type': trade['type'],
                    'entry': trade['entry'],
                    'stop_loss': trade['stop_loss'],
                    'take_profit': trade['take_profit'],
                    'confidence': trade['confidence'],
                    'regime': trade['regime'],
                    'strategy': trade['strategy']
                }
                json.dump(trade_dict, f, indent=2)
                print(f"  💾 Señal guardada en {filename}")
        
        print("\n" + "-"*60)
    
    # 2. Estrategia DCA para acumulación pasiva
    print("\n💰 ESTRATEGIA DCA (DOLLAR COST AVERAGING)")
    print("-"*60)
    
    dca = DCAStrategy(symbols, capital=206)
    opportunities = dca.scan_opportunities()
    
    print("\n" + "="*80)
    print(" RESUMEN ".center(80, "="))
    print("="*80)
    print("\n✅ Sistema Adaptativo V4.0 ejecutado correctamente")
    print("  - Detecta automáticamente el régimen del mercado")
    print("  - Aplica la estrategia óptima para cada condición")
    print("  - Ajusta riesgo y stops dinámicamente")
    print("  - Incluye estrategia DCA para acumulación pasiva")
    

if __name__ == "__main__":
    main()