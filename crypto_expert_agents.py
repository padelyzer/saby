#!/usr/bin/env python3
"""
Sistema de Agentes Expertos para Trading de Criptomonedas
Cada agente especializado en un par específico con calibración independiente
Objetivo: 60-70% win rate mediante especialización y análisis profundo por par
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List, Tuple, Optional
from abc import ABC, abstractmethod

warnings.filterwarnings('ignore')

class MarketIntelligence:
    """
    Componentes compartidos de inteligencia de mercado
    Análisis macro y detección de tendencia general
    """
    
    @staticmethod
    def get_bitcoin_dominance_trend():
        """Obtiene tendencia de dominancia de Bitcoin"""
        try:
            btc_data = yf.download("BTC-USD", period="30d", interval="1d")
            if len(btc_data) < 10:
                return "NEUTRAL"
                
            ema_short = btc_data['Close'].ewm(span=7).mean()
            ema_long = btc_data['Close'].ewm(span=21).mean()
            
            if ema_short.iloc[-1] > ema_long.iloc[-1] and ema_short.iloc[-3] > ema_short.iloc[-1]:
                return "BTC_WEAKENING"  # Favorable para altcoins
            elif ema_short.iloc[-1] > ema_long.iloc[-1]:
                return "BTC_STRONG"     # Desfavorable para altcoins
            else:
                return "BTC_DECLINING"  # Muy favorable para altcoins
        except:
            return "NEUTRAL"
    
    @staticmethod
    def get_market_sentiment():
        """Análisis de sentimiento general del mercado"""
        try:
            # Usar ETH como proxy del sentiment altcoin
            eth_data = yf.download("ETH-USD", period="7d", interval="1h")
            if len(eth_data) < 24:
                return {"sentiment": "NEUTRAL", "strength": 0.5}
            
            # RSI de ETH como indicador de sentiment
            delta = eth_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            
            if current_rsi > 70:
                return {"sentiment": "EXTREME_GREED", "strength": 0.9}
            elif current_rsi > 60:
                return {"sentiment": "GREED", "strength": 0.7}
            elif current_rsi < 30:
                return {"sentiment": "EXTREME_FEAR", "strength": 0.9}
            elif current_rsi < 40:
                return {"sentiment": "FEAR", "strength": 0.7}
            else:
                return {"sentiment": "NEUTRAL", "strength": 0.5}
        except:
            return {"sentiment": "NEUTRAL", "strength": 0.5}
    
    @staticmethod
    def validate_volume_conditions(df, threshold_multiplier=1.5):
        """Validación de condiciones de volumen"""
        if 'Volume' not in df.columns or len(df) < 20:
            return True
            
        current_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
        
        # Volumen debe estar por encima del promedio pero no extremo
        return avg_volume < current_volume < (avg_volume * threshold_multiplier)

class CryptoExpertAgent(ABC):
    """
    Clase base para agentes expertos especializados en pares específicos
    Cada agente tiene calibración independiente y estrategias adaptadas
    """
    
    def __init__(self, symbol: str, target_win_rate: float = 0.65):
        self.symbol = symbol
        self.target_win_rate = target_win_rate
        self.market_intelligence = MarketIntelligence()
        self.calibration_data = {}
        self.performance_history = []
        
        # Parámetros base que cada agente puede sobrescribir
        self.base_params = {
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'ema_fast': 12,
            'ema_slow': 26,
            'volume_threshold': 1.5,
            'stop_loss_pct': 2.5,
            'take_profit_pct': 5.0,
            'min_confluence_score': 65
        }
        
        # Cada agente define sus parámetros optimizados
        self.params = self.base_params.copy()
        self.initialize_expert_parameters()
        
    @abstractmethod
    def initialize_expert_parameters(self):
        """Cada agente define sus parámetros específicos calibrados"""
        pass
    
    @abstractmethod
    def get_pair_characteristics(self) -> Dict:
        """Retorna características únicas del par"""
        pass
    
    @abstractmethod
    def calculate_specialized_indicators(self, df: pd.DataFrame) -> Dict:
        """Calcula indicadores especializados para este par"""
        pass
    
    def fetch_market_data(self, period="90d", interval="1h") -> pd.DataFrame:
        """Obtiene datos de mercado para el análisis"""
        try:
            data = yf.download(self.symbol, period=period, interval=interval)
            if len(data) == 0:
                raise Exception(f"No data available for {self.symbol}")
            return data
        except Exception as e:
            print(f"Error fetching data for {self.symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_base_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos base"""
        if len(df) < 50:
            return df
            
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # EMAs
        df['EMA_Fast'] = df['Close'].ewm(span=self.params['ema_fast']).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=self.params['ema_slow']).mean()
        
        # MACD
        df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # ATR para volatilidad
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Bollinger Bands
        bb_period = 20
        bb_middle = df['Close'].rolling(bb_period).mean()
        bb_std = df['Close'].rolling(bb_period).std()
        df['BB_Middle'] = bb_middle
        df['BB_Upper'] = bb_middle + (bb_std * 2)
        df['BB_Lower'] = bb_middle - (bb_std * 2)
        
        return df
    
    def detect_pair_specific_patterns(self, df: pd.DataFrame) -> List[str]:
        """Detecta patrones específicos del par - implementado por cada agente"""
        patterns = []
        
        # Patrón base: RSI Divergence
        if len(df) > 20:
            price_higher = df['Close'].iloc[-1] > df['Close'].iloc[-10]
            rsi_lower = df['RSI'].iloc[-1] < df['RSI'].iloc[-10]
            
            if price_higher and rsi_lower:
                patterns.append("BEARISH_DIVERGENCE")
            elif not price_higher and not rsi_lower:
                patterns.append("BULLISH_DIVERGENCE")
        
        return patterns
    
    def calculate_confluence_score(self, df: pd.DataFrame) -> float:
        """
        Sistema de puntuación de confluencia personalizado por agente
        Cada agente puede tener diferentes pesos y criterios
        """
        if len(df) < 50:
            return 0
            
        score = 0
        latest = df.iloc[-1]
        
        # Análisis RSI (peso base)
        rsi_weight = self.get_pair_characteristics().get('rsi_weight', 0.25)
        if latest['RSI'] < self.params['rsi_oversold']:
            score += 25 * rsi_weight
        elif latest['RSI'] > self.params['rsi_overbought']:
            score -= 20 * rsi_weight
            
        # Análisis MACD
        macd_weight = self.get_pair_characteristics().get('macd_weight', 0.2)
        if latest['MACD'] > latest['MACD_Signal'] and df['MACD'].iloc[-2] <= df['MACD_Signal'].iloc[-2]:
            score += 20 * macd_weight
        elif latest['MACD'] < latest['MACD_Signal'] and df['MACD'].iloc[-2] >= df['MACD_Signal'].iloc[-2]:
            score -= 20 * macd_weight
            
        # Análisis de tendencia EMA
        trend_weight = self.get_pair_characteristics().get('trend_weight', 0.3)
        if latest['EMA_Fast'] > latest['EMA_Slow']:
            score += 15 * trend_weight
        else:
            score -= 15 * trend_weight
            
        # Volatilidad (específico por par)
        volatility_weight = self.get_pair_characteristics().get('volatility_weight', 0.15)
        atr_ratio = latest['ATR'] / df['ATR'].rolling(50).mean().iloc[-1]
        if 0.8 < atr_ratio < 1.3:  # Volatilidad moderada
            score += 10 * volatility_weight
        elif atr_ratio > 2.0:  # Volatilidad excesiva
            score -= 15 * volatility_weight
            
        # Análisis de volumen
        volume_weight = self.get_pair_characteristics().get('volume_weight', 0.1)
        if self.market_intelligence.validate_volume_conditions(df):
            score += 10 * volume_weight
        else:
            score -= 5 * volume_weight
            
        # Patrones específicos del par
        patterns = self.detect_pair_specific_patterns(df)
        pattern_weight = self.get_pair_characteristics().get('pattern_weight', 0.1)
        if "BULLISH_DIVERGENCE" in patterns:
            score += 15 * pattern_weight
        elif "BEARISH_DIVERGENCE" in patterns:
            score -= 10 * pattern_weight
            
        # Factores macro compartidos
        btc_trend = self.market_intelligence.get_bitcoin_dominance_trend()
        market_sentiment = self.market_intelligence.get_market_sentiment()
        
        # Ajuste por dominancia de Bitcoin (crítico para altcoins)
        if btc_trend == "BTC_WEAKENING":
            score += 10  # Favorable para altcoins
        elif btc_trend == "BTC_DECLINING":
            score += 15  # Muy favorable para altcoins
        elif btc_trend == "BTC_STRONG":
            score -= 10  # Desfavorable para altcoins
            
        # Ajuste por sentiment
        if market_sentiment['sentiment'] == "EXTREME_FEAR" and score > 0:
            score += 10  # Oportunidad de compra
        elif market_sentiment['sentiment'] == "EXTREME_GREED" and score > 0:
            score -= 15  # Reducir posiciones
            
        return max(0, min(100, score))
    
    def generate_signal(self) -> Dict:
        """Genera señal de trading basada en análisis especializado"""
        try:
            df = self.fetch_market_data()
            if df.empty:
                return {"signal": "HOLD", "confidence": 0, "reason": "No data available"}
                
            df = self.calculate_base_indicators(df)
            specialized_indicators = self.calculate_specialized_indicators(df)
            confluence_score = self.calculate_confluence_score(df)
            
            # Determinar señal basada en confluence score y parámetros del agente
            min_score = self.params['min_confluence_score']
            
            signal_data = {
                "symbol": self.symbol,
                "timestamp": datetime.now(),
                "confluence_score": confluence_score,
                "specialized_indicators": specialized_indicators,
                "pair_characteristics": self.get_pair_characteristics(),
                "signal": "HOLD",
                "confidence": confluence_score / 100,
                "reason": "Insufficient confluence",
                "stop_loss_pct": self.params['stop_loss_pct'],
                "take_profit_pct": self.params['take_profit_pct']
            }
            
            if confluence_score >= min_score:
                latest = df.iloc[-1]
                
                # Lógica de señal específica del agente
                if (latest['RSI'] < self.params['rsi_oversold'] and 
                    latest['EMA_Fast'] > latest['EMA_Slow']):
                    signal_data.update({
                        "signal": "BUY",
                        "reason": f"High confluence ({confluence_score:.1f}) + RSI oversold + EMA bullish"
                    })
                elif (latest['RSI'] > self.params['rsi_overbought'] and 
                      latest['EMA_Fast'] < latest['EMA_Slow']):
                    signal_data.update({
                        "signal": "SELL", 
                        "reason": f"High confluence ({confluence_score:.1f}) + RSI overbought + EMA bearish"
                    })
                else:
                    signal_data.update({
                        "signal": "HOLD",
                        "reason": f"High confluence ({confluence_score:.1f}) but mixed signals"
                    })
            
            return signal_data
            
        except Exception as e:
            return {
                "signal": "ERROR", 
                "confidence": 0, 
                "reason": f"Error generating signal: {str(e)}"
            }
    
    def calibrate_parameters(self, historical_data: pd.DataFrame = None):
        """Calibra parámetros basado en rendimiento histórico"""
        if historical_data is None:
            historical_data = self.fetch_market_data(period="180d", interval="1h")
            
        if historical_data.empty:
            print(f"No data available for calibration of {self.symbol}")
            return
            
        print(f"🔧 Calibrando parámetros para {self.symbol}...")
        
        # Análisis de volatilidad para ajustar stops/targets
        atr_analysis = self.analyze_volatility_patterns(historical_data)
        
        # Ajustar stop loss y take profit basado en volatilidad
        avg_volatility = atr_analysis['avg_volatility_pct']
        self.params['stop_loss_pct'] = max(1.5, avg_volatility * 1.2)
        self.params['take_profit_pct'] = max(3.0, avg_volatility * 2.5)
        
        # Ajustar RSI levels basado en características del par
        rsi_analysis = self.analyze_rsi_effectiveness(historical_data)
        if rsi_analysis['optimal_oversold']:
            self.params['rsi_oversold'] = rsi_analysis['optimal_oversold']
        if rsi_analysis['optimal_overbought']:
            self.params['rsi_overbought'] = rsi_analysis['optimal_overbought']
            
        print(f"✅ Calibración completada para {self.symbol}")
        print(f"   Stop Loss: {self.params['stop_loss_pct']:.1f}%")
        print(f"   Take Profit: {self.params['take_profit_pct']:.1f}%")
        print(f"   RSI Levels: {self.params['rsi_oversold']}/{self.params['rsi_overbought']}")
    
    def analyze_volatility_patterns(self, df: pd.DataFrame) -> Dict:
        """Analiza patrones de volatilidad específicos del par"""
        df = self.calculate_base_indicators(df)
        
        # Calcular volatilidad como porcentaje del precio
        volatility_pct = (df['ATR'] / df['Close']) * 100
        
        return {
            'avg_volatility_pct': volatility_pct.mean(),
            'volatility_std': volatility_pct.std(),
            'max_volatility_pct': volatility_pct.max(),
            'volatility_trend': 'increasing' if volatility_pct.iloc[-20:].mean() > volatility_pct.iloc[-50:-20].mean() else 'stable'
        }
    
    def analyze_rsi_effectiveness(self, df: pd.DataFrame) -> Dict:
        """Analiza efectividad de diferentes niveles de RSI"""
        df = self.calculate_base_indicators(df)
        
        # Testear diferentes niveles de RSI
        best_oversold = 30
        best_overbought = 70
        
        # Análisis simplificado - en implementación real sería más complejo
        rsi_mean = df['RSI'].mean()
        rsi_std = df['RSI'].std()
        
        if rsi_std > 15:  # Alta variabilidad de RSI
            best_oversold = max(25, rsi_mean - rsi_std)
            best_overbought = min(75, rsi_mean + rsi_std)
        
        return {
            'optimal_oversold': best_oversold,
            'optimal_overbought': best_overbought,
            'rsi_volatility': rsi_std
        }

# ================================
# AGENTES EXPERTOS ESPECIALIZADOS
# ================================

class BNBExpert(CryptoExpertAgent):
    """
    Agente Experto para BNB-USD
    Características: Token de exchange con correlación fuerte con volumen de trading
    """
    
    def initialize_expert_parameters(self):
        self.params = self.base_params.copy()
        # BNB tiende a tener movimientos más estables
        self.params.update({
            'rsi_period': 14,
            'rsi_overbought': 75,  # Más conservador
            'rsi_oversold': 25,    # Más agresivo en oversold
            'ema_fast': 10,
            'ema_slow': 20,
            'stop_loss_pct': 2.0,  # Menos volátil que otros
            'take_profit_pct': 4.0,
            'min_confluence_score': 60  # Menor threshold por estabilidad
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM',
            'correlation_with_btc': 0.7,
            'best_trading_hours': [13, 14, 15, 16, 17],  # UTC, horario asiático
            'rsi_weight': 0.3,
            'macd_weight': 0.25,
            'trend_weight': 0.3,
            'volatility_weight': 0.1,
            'volume_weight': 0.15,
            'pattern_weight': 0.1,
            'sector': 'EXCHANGE_TOKEN',
            'key_levels': {
                'support': [580, 550, 500],
                'resistance': [650, 700, 750]
            }
        }
    
    def calculate_specialized_indicators(self, df: pd.DataFrame) -> Dict:
        """Indicadores específicos para BNB"""
        indicators = {}
        
        # BNB específico: Análisis de volumen de exchange
        indicators['volume_trend'] = 'increasing' if df['Volume'].iloc[-5:].mean() > df['Volume'].iloc[-20:-5].mean() else 'decreasing'
        
        # Momentum específico para tokens de exchange
        if len(df) > 20:
            momentum = ((df['Close'].iloc[-1] / df['Close'].iloc[-20]) - 1) * 100
            indicators['momentum_20d'] = momentum
            indicators['momentum_signal'] = 'bullish' if momentum > 5 else 'bearish' if momentum < -5 else 'neutral'
        
        # Análisis de Bollinger Band position (BNB responde bien)
        if 'BB_Upper' in df.columns:
            bb_position = (df['Close'].iloc[-1] - df['BB_Lower'].iloc[-1]) / (df['BB_Upper'].iloc[-1] - df['BB_Lower'].iloc[-1])
            indicators['bb_position'] = bb_position
            indicators['bb_signal'] = 'overbought' if bb_position > 0.8 else 'oversold' if bb_position < 0.2 else 'neutral'
        
        return indicators
    
    def detect_pair_specific_patterns(self, df: pd.DataFrame) -> List[str]:
        patterns = super().detect_pair_specific_patterns(df)
        
        # Patrón específico BNB: Breakout de consolidación
        if len(df) > 50:
            recent_range = df['High'].iloc[-20:].max() - df['Low'].iloc[-20:].min()
            longer_range = df['High'].iloc[-50:-20].max() - df['Low'].iloc[-50:-20].min()
            
            if recent_range < longer_range * 0.6:  # Consolidación
                if df['Close'].iloc[-1] > df['High'].iloc[-20:].max() * 0.99:
                    patterns.append("CONSOLIDATION_BREAKOUT_UP")
                elif df['Close'].iloc[-1] < df['Low'].iloc[-20:].min() * 1.01:
                    patterns.append("CONSOLIDATION_BREAKOUT_DOWN")
        
        return patterns

class SOLExpert(CryptoExpertAgent):
    """
    Agente Experto para SOL-USD
    Características: Alta volatilidad, movimientos rápidos, correlación con DeFi
    """
    
    def initialize_expert_parameters(self):
        self.params = self.base_params.copy()
        # SOL es muy volátil, necesita parámetros más agresivos
        self.params.update({
            'rsi_period': 12,      # Más responsive
            'rsi_overbought': 78,  # Levels más extremos
            'rsi_oversold': 22,
            'ema_fast': 8,         # EMAs más rápidas
            'ema_slow': 18,
            'stop_loss_pct': 3.5,  # Stops más amplios por volatilidad
            'take_profit_pct': 7.0,
            'min_confluence_score': 70  # Score más alto por volatilidad
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'HIGH',
            'correlation_with_btc': 0.6,
            'best_trading_hours': [14, 15, 16, 20, 21],  # Horarios US
            'rsi_weight': 0.35,    # RSI muy efectivo en SOL
            'macd_weight': 0.3,
            'trend_weight': 0.2,
            'volatility_weight': 0.2,
            'volume_weight': 0.1,
            'pattern_weight': 0.05,
            'sector': 'SMART_CONTRACT',
            'key_levels': {
                'support': [140, 120, 100],
                'resistance': [180, 200, 220]
            }
        }
    
    def calculate_specialized_indicators(self, df: pd.DataFrame) -> Dict:
        """Indicadores específicos para SOL"""
        indicators = {}
        
        # SOL específico: Velocity indicator (cambios rápidos de precio)
        if len(df) > 10:
            price_velocity = df['Close'].pct_change().rolling(5).std() * 100
            indicators['price_velocity'] = price_velocity.iloc[-1]
            indicators['velocity_signal'] = 'high' if price_velocity.iloc[-1] > price_velocity.quantile(0.8) else 'low'
        
        # DeFi correlation proxy
        if len(df) > 30:
            volume_price_correlation = df['Volume'].rolling(20).corr(df['Close'])
            indicators['volume_price_corr'] = volume_price_correlation.iloc[-1]
        
        # SOL-specific: Intraday momentum
        if len(df) > 24:
            intraday_momentum = (df['Close'].iloc[-1] / df['Open'].iloc[-24]) - 1
            indicators['intraday_momentum'] = intraday_momentum * 100
            indicators['momentum_signal'] = 'strong' if abs(intraday_momentum) > 0.05 else 'weak'
        
        return indicators
    
    def detect_pair_specific_patterns(self, df: pd.DataFrame) -> List[str]:
        patterns = super().detect_pair_specific_patterns(df)
        
        # Patrón específico SOL: Explosive moves
        if len(df) > 10:
            recent_change = (df['Close'].iloc[-1] / df['Close'].iloc[-5]) - 1
            if recent_change > 0.15:  # 15% en 5 períodos
                patterns.append("EXPLOSIVE_MOVE_UP")
            elif recent_change < -0.15:
                patterns.append("EXPLOSIVE_MOVE_DOWN")
        
        # Gap analysis (SOL tiende a gaps)
        if len(df) > 2:
            current_open = df['Open'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            gap_pct = abs(current_open - prev_close) / prev_close
            
            if gap_pct > 0.02:  # Gap > 2%
                if current_open > prev_close:
                    patterns.append("GAP_UP")
                else:
                    patterns.append("GAP_DOWN")
        
        return patterns

class DOTExpert(CryptoExpertAgent):
    """
    Agente Experto para DOT-USD
    Características: Movimientos institucionales, correlación con desarrollo del ecosistema
    """
    
    def initialize_expert_parameters(self):
        self.params = self.base_params.copy()
        # DOT tiene movimientos más predecibles
        self.params.update({
            'rsi_period': 16,      # Período más largo
            'rsi_overbought': 72,
            'rsi_oversold': 28,
            'ema_fast': 15,
            'ema_slow': 35,
            'stop_loss_pct': 2.8,
            'take_profit_pct': 5.5,
            'min_confluence_score': 65
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM_HIGH',
            'correlation_with_btc': 0.75,
            'best_trading_hours': [8, 9, 10, 14, 15, 16],
            'rsi_weight': 0.25,
            'macd_weight': 0.3,     # MACD muy efectivo en DOT
            'trend_weight': 0.35,   # Sigue tendencias bien
            'volatility_weight': 0.05,
            'volume_weight': 0.2,
            'pattern_weight': 0.05,
            'sector': 'INTEROPERABILITY',
            'key_levels': {
                'support': [6.5, 6.0, 5.5],
                'resistance': [8.0, 9.0, 10.0]
            }
        }
    
    def calculate_specialized_indicators(self, df: pd.DataFrame) -> Dict:
        """Indicadores específicos para DOT"""
        indicators = {}
        
        # DOT específico: Institutional flow proxy
        if len(df) > 50:
            large_move_frequency = (abs(df['Close'].pct_change()) > 0.05).rolling(20).sum()
            indicators['institutional_activity'] = large_move_frequency.iloc[-1]
        
        # Weekly momentum (DOT responds to weekly cycles)
        if len(df) > 168:  # 1 week of hourly data
            weekly_momentum = (df['Close'].iloc[-1] / df['Close'].iloc[-168]) - 1
            indicators['weekly_momentum'] = weekly_momentum * 100
            indicators['weekly_signal'] = 'bullish' if weekly_momentum > 0.1 else 'bearish' if weekly_momentum < -0.1 else 'neutral'
        
        # Volume-weighted price momentum
        if 'Volume' in df.columns and len(df) > 20:
            vwap = (df['Close'] * df['Volume']).rolling(20).sum() / df['Volume'].rolling(20).sum()
            indicators['price_vs_vwap'] = (df['Close'].iloc[-1] / vwap.iloc[-1]) - 1
        
        return indicators
    
    def detect_pair_specific_patterns(self, df: pd.DataFrame) -> List[str]:
        patterns = super().detect_pair_specific_patterns(df)
        
        # Patrón específico DOT: Steady accumulation
        if len(df) > 30:
            price_change = (df['Close'].iloc[-1] / df['Close'].iloc[-30]) - 1
            volume_trend = df['Volume'].iloc[-15:].mean() / df['Volume'].iloc[-30:-15].mean()
            
            if 0.02 < price_change < 0.08 and volume_trend > 1.1:
                patterns.append("STEADY_ACCUMULATION")
            elif -0.08 < price_change < -0.02 and volume_trend > 1.1:
                patterns.append("STEADY_DISTRIBUTION")
        
        return patterns

class ADAExpert(CryptoExpertAgent):
    """
    Agente Experto para ADA-USD
    Características: Movimientos graduales, correlación con noticias de desarrollo
    """
    
    def initialize_expert_parameters(self):
        self.params = self.base_params.copy()
        # ADA tiene movimientos más suaves
        self.params.update({
            'rsi_period': 18,      # Período más largo para suavizar
            'rsi_overbought': 74,
            'rsi_oversold': 26,
            'ema_fast': 16,
            'ema_slow': 40,
            'stop_loss_pct': 2.2,  # Menos volátil
            'take_profit_pct': 4.5,
            'min_confluence_score': 62
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM_LOW',
            'correlation_with_btc': 0.8,   # Alta correlación
            'best_trading_hours': [12, 13, 14, 15, 16, 17],
            'rsi_weight': 0.35,    # RSI muy confiable en ADA
            'macd_weight': 0.2,
            'trend_weight': 0.3,
            'volatility_weight': 0.05,
            'volume_weight': 0.25,  # Volumen importante en ADA
            'pattern_weight': 0.05,
            'sector': 'SMART_CONTRACT',
            'key_levels': {
                'support': [0.35, 0.30, 0.25],
                'resistance': [0.50, 0.60, 0.70]
            }
        }
    
    def calculate_specialized_indicators(self, df: pd.DataFrame) -> Dict:
        """Indicadores específicos para ADA"""
        indicators = {}
        
        # ADA específico: Gradual trend strength
        if len(df) > 40:
            trend_consistency = 0
            for i in range(1, 21):
                if df['Close'].iloc[-i] < df['Close'].iloc[-i-1]:
                    trend_consistency += 1
            indicators['trend_consistency'] = trend_consistency / 20
        
        # Development cycle correlation (proxy via volume patterns)
        if len(df) > 100:
            volume_cycles = df['Volume'].rolling(30).mean().pct_change().rolling(10).std()
            indicators['development_cycle_proxy'] = volume_cycles.iloc[-1]
        
        # ADA-specific: Stability index
        if len(df) > 30:
            price_stability = 1 - (df['Close'].pct_change().rolling(30).std())
            indicators['stability_index'] = price_stability.iloc[-1]
        
        return indicators

class AVAXExpert(CryptoExpertAgent):
    """
    Agente Experto para AVAX-USD  
    Características: Responde bien a tendencias de DeFi, volatilidad media-alta
    """
    
    def initialize_expert_parameters(self):
        self.params = self.base_params.copy()
        self.params.update({
            'rsi_period': 14,
            'rsi_overbought': 76,
            'rsi_oversold': 24,
            'ema_fast': 12,
            'ema_slow': 28,
            'stop_loss_pct': 3.0,
            'take_profit_pct': 6.0,
            'min_confluence_score': 68
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM_HIGH',
            'correlation_with_btc': 0.65,
            'best_trading_hours': [13, 14, 15, 16, 19, 20],
            'rsi_weight': 0.3,
            'macd_weight': 0.25,
            'trend_weight': 0.25,
            'volatility_weight': 0.15,
            'volume_weight': 0.15,
            'pattern_weight': 0.1,
            'sector': 'SMART_CONTRACT',
            'key_levels': {
                'support': [25, 22, 18],
                'resistance': [35, 40, 45]
            }
        }
    
    def calculate_specialized_indicators(self, df: pd.DataFrame) -> Dict:
        indicators = {}
        
        # AVAX específico: DeFi momentum proxy
        if len(df) > 20:
            defi_momentum = df['Volume'].rolling(10).mean().pct_change().iloc[-1]
            indicators['defi_momentum'] = defi_momentum
        
        return indicators

class LINKExpert(CryptoExpertAgent):
    """
    Agente Experto para LINK-USD
    Características: Oracle token, correlación con adoption de smart contracts
    """
    
    def initialize_expert_parameters(self):
        self.params = self.base_params.copy()
        self.params.update({
            'rsi_period': 15,
            'rsi_overbought': 73,
            'rsi_oversold': 27,
            'ema_fast': 14,
            'ema_slow': 32,
            'stop_loss_pct': 2.7,
            'take_profit_pct': 5.2,
            'min_confluence_score': 66
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM',
            'correlation_with_btc': 0.72,
            'best_trading_hours': [14, 15, 16, 17, 20, 21],
            'rsi_weight': 0.28,
            'macd_weight': 0.27,
            'trend_weight': 0.3,
            'volatility_weight': 0.1,
            'volume_weight': 0.2,
            'pattern_weight': 0.05,
            'sector': 'ORACLE',
            'key_levels': {
                'support': [14, 12, 10],
                'resistance': [18, 20, 25]
            }
        }
    
    def calculate_specialized_indicators(self, df: pd.DataFrame) -> Dict:
        indicators = {}
        
        # LINK específico: Oracle adoption proxy via volume analysis
        if len(df) > 50:
            adoption_proxy = df['Volume'].rolling(30).mean() / df['Volume'].rolling(90).mean()
            indicators['adoption_proxy'] = adoption_proxy.iloc[-1]
        
        return indicators

class DOGEExpert(CryptoExpertAgent):
    """
    Agente Experto para DOGE-USD
    Características: Altamente especulativo, correlación con sentiment/redes sociales
    """
    
    def initialize_expert_parameters(self):
        self.params = self.base_params.copy()
        # DOGE es muy volátil y especulativo
        self.params.update({
            'rsi_period': 10,      # Muy responsive
            'rsi_overbought': 80,  # Levels extremos
            'rsi_oversold': 20,
            'ema_fast': 6,
            'ema_slow': 15,
            'stop_loss_pct': 4.0,  # Stops amplios
            'take_profit_pct': 8.0,
            'min_confluence_score': 75  # Score alto por volatilidad
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'VERY_HIGH',
            'correlation_with_btc': 0.5,   # Menor correlación
            'best_trading_hours': [18, 19, 20, 21, 22, 23],  # Horarios US
            'rsi_weight': 0.4,     # RSI crítico en DOGE
            'macd_weight': 0.2,
            'trend_weight': 0.15,
            'volatility_weight': 0.25,  # Volatilidad muy importante
            'volume_weight': 0.05,
            'pattern_weight': 0.05,
            'sector': 'MEME',
            'key_levels': {
                'support': [0.08, 0.06, 0.05],
                'resistance': [0.12, 0.15, 0.20]
            }
        }
    
    def calculate_specialized_indicators(self, df: pd.DataFrame) -> Dict:
        """Indicadores específicos para DOGE"""
        indicators = {}
        
        # DOGE específico: Sentiment momentum (proxy via price velocity)
        if len(df) > 5:
            sentiment_momentum = df['Close'].pct_change().rolling(3).mean() * 100
            indicators['sentiment_momentum'] = sentiment_momentum.iloc[-1]
            indicators['sentiment_signal'] = 'euphoric' if sentiment_momentum.iloc[-1] > 5 else 'despair' if sentiment_momentum.iloc[-1] < -5 else 'neutral'
        
        # Social media proxy (via extreme volume spikes)
        if len(df) > 30:
            volume_spike_ratio = df['Volume'].iloc[-1] / df['Volume'].rolling(30).mean().iloc[-1]
            indicators['social_activity_proxy'] = volume_spike_ratio
            indicators['viral_signal'] = 'viral' if volume_spike_ratio > 3 else 'normal'
        
        # DOGE-specific: Meme cycle position
        if len(df) > 100:
            long_term_trend = (df['Close'].iloc[-1] / df['Close'].iloc[-100]) - 1
            indicators['meme_cycle_position'] = long_term_trend * 100
        
        return indicators
    
    def detect_pair_specific_patterns(self, df: pd.DataFrame) -> List[str]:
        patterns = super().detect_pair_specific_patterns(df)
        
        # Patrón específico DOGE: Viral pump
        if len(df) > 5:
            rapid_increase = all(df['Close'].iloc[-i] > df['Close'].iloc[-i-1] for i in range(1, 4))
            volume_spike = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1] * 2
            
            if rapid_increase and volume_spike:
                patterns.append("VIRAL_PUMP")
        
        # Crash pattern (common in DOGE)
        if len(df) > 3:
            rapid_decrease = (df['Close'].iloc[-1] / df['Close'].iloc[-3]) < 0.85
            if rapid_decrease:
                patterns.append("MEME_CRASH")
        
        return patterns

class CryptoExpertSystem:
    """
    Sistema coordinador de todos los agentes expertos
    Gestiona la ejecución, calibración y análisis conjunto
    """
    
    def __init__(self):
        self.agents = {
            'BNB-USD': BNBExpert('BNB-USD'),
            'SOL-USD': SOLExpert('SOL-USD'), 
            'DOT-USD': DOTExpert('DOT-USD'),
            'ADA-USD': ADAExpert('ADA-USD'),
            'AVAX-USD': AVAXExpert('AVAX-USD'),
            'LINK-USD': LINKExpert('LINK-USD'),
            'DOGE-USD': DOGEExpert('DOGE-USD')
        }
        
        self.performance_tracker = {}
        self.calibration_history = {}
    
    def calibrate_all_agents(self):
        """Calibra todos los agentes basado en datos históricos"""
        print("🚀 INICIANDO CALIBRACIÓN DEL SISTEMA DE AGENTES EXPERTOS")
        print("=" * 80)
        
        for symbol, agent in self.agents.items():
            print(f"\n📊 Calibrando agente experto para {symbol}")
            print("-" * 50)
            
            try:
                agent.calibrate_parameters()
                
                # Mostrar características del par
                characteristics = agent.get_pair_characteristics()
                print(f"   Sector: {characteristics['sector']}")
                print(f"   Volatilidad: {characteristics['volatility_class']}")
                print(f"   Correlación BTC: {characteristics['correlation_with_btc']}")
                print(f"   Mejores horas: {characteristics['best_trading_hours']}")
                
            except Exception as e:
                print(f"   ❌ Error calibrando {symbol}: {e}")
        
        print(f"\n✅ CALIBRACIÓN COMPLETADA PARA TODOS LOS AGENTES")
    
    def generate_all_signals(self) -> Dict:
        """Genera señales de todos los agentes expertos"""
        signals = {}
        
        print("🎯 GENERANDO SEÑALES DE AGENTES EXPERTOS")
        print("=" * 60)
        
        for symbol, agent in self.agents.items():
            try:
                signal = agent.generate_signal()
                signals[symbol] = signal
                
                # Mostrar resumen de señal
                print(f"\n{symbol}: {signal['signal']} "
                      f"(Confidence: {signal['confidence']:.1%}, "
                      f"Score: {signal['confluence_score']:.1f})")
                print(f"   Razón: {signal['reason']}")
                
            except Exception as e:
                print(f"❌ Error generando señal para {symbol}: {e}")
                signals[symbol] = {"signal": "ERROR", "error": str(e)}
        
        return signals
    
    def get_best_opportunities(self, min_confidence=0.7) -> List[Dict]:
        """Identifica las mejores oportunidades de trading"""
        signals = self.generate_all_signals()
        opportunities = []
        
        for symbol, signal_data in signals.items():
            if (signal_data.get('signal') in ['BUY', 'SELL'] and 
                signal_data.get('confidence', 0) >= min_confidence):
                opportunities.append({
                    'symbol': symbol,
                    'signal': signal_data['signal'],
                    'confidence': signal_data['confidence'],
                    'confluence_score': signal_data.get('confluence_score', 0),
                    'agent_type': type(self.agents[symbol]).__name__,
                    'specialized_data': signal_data.get('specialized_indicators', {}),
                    'risk_data': {
                        'stop_loss_pct': signal_data.get('stop_loss_pct', 2.5),
                        'take_profit_pct': signal_data.get('take_profit_pct', 5.0)
                    }
                })
        
        # Ordenar por confluence score
        opportunities.sort(key=lambda x: x['confluence_score'], reverse=True)
        
        return opportunities
    
    def analyze_system_performance(self) -> Dict:
        """Analiza rendimiento del sistema de agentes"""
        print("\n📈 ANÁLISIS DE RENDIMIENTO DEL SISTEMA")
        print("=" * 50)
        
        analysis = {
            'total_agents': len(self.agents),
            'agent_performance': {},
            'system_statistics': {},
            'recommendations': []
        }
        
        for symbol, agent in self.agents.items():
            characteristics = agent.get_pair_characteristics()
            analysis['agent_performance'][symbol] = {
                'volatility_class': characteristics['volatility_class'],
                'sector': characteristics['sector'],
                'calibrated_params': agent.params,
                'optimal_hours': characteristics['best_trading_hours']
            }
        
        # Estadísticas del sistema
        volatility_distribution = {}
        for symbol, agent in self.agents.items():
            vol_class = agent.get_pair_characteristics()['volatility_class']
            volatility_distribution[vol_class] = volatility_distribution.get(vol_class, 0) + 1
        
        analysis['system_statistics']['volatility_distribution'] = volatility_distribution
        analysis['system_statistics']['sector_coverage'] = len(set(
            agent.get_pair_characteristics()['sector'] for agent in self.agents.values()
        ))
        
        # Recomendaciones
        if volatility_distribution.get('HIGH', 0) + volatility_distribution.get('VERY_HIGH', 0) > 3:
            analysis['recommendations'].append("Alto número de pares volátiles - considerar gestión de riesgo estricta")
        
        if analysis['system_statistics']['sector_coverage'] >= 4:
            analysis['recommendations'].append("Buena diversificación sectorial")
        
        return analysis
    
    def save_system_state(self, filename: str = "expert_agents_state.json"):
        """Guarda el estado del sistema"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'agents': {}
        }
        
        for symbol, agent in self.agents.items():
            state['agents'][symbol] = {
                'params': agent.params,
                'characteristics': agent.get_pair_characteristics(),
                'agent_type': type(agent).__name__
            }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"💾 Estado del sistema guardado en {filename}")

def demo_expert_agents_system():
    """Demostración del sistema de agentes expertos"""
    print("🤖 DEMO: SISTEMA DE AGENTES EXPERTOS CRYPTO")
    print("=" * 80)
    
    # Inicializar sistema
    expert_system = CryptoExpertSystem()
    
    # Calibrar todos los agentes
    expert_system.calibrate_all_agents()
    
    # Generar señales
    print("\n" + "=" * 80)
    signals = expert_system.generate_all_signals()
    
    # Encontrar mejores oportunidades
    print("\n" + "=" * 80)
    print("🏆 MEJORES OPORTUNIDADES DE TRADING")
    print("=" * 50)
    
    opportunities = expert_system.get_best_opportunities(min_confidence=0.6)
    
    if opportunities:
        for i, opp in enumerate(opportunities[:3], 1):  # Top 3
            print(f"\n{i}. {opp['symbol']} - {opp['signal']}")
            print(f"   Agente: {opp['agent_type']}")
            print(f"   Confianza: {opp['confidence']:.1%}")
            print(f"   Score Confluencia: {opp['confluence_score']:.1f}")
            print(f"   Stop Loss: {opp['risk_data']['stop_loss_pct']:.1f}%")
            print(f"   Take Profit: {opp['risk_data']['take_profit_pct']:.1f}%")
    else:
        print("No hay oportunidades que cumplan los criterios mínimos")
    
    # Análisis de rendimiento del sistema
    print("\n" + "=" * 80)
    performance = expert_system.analyze_system_performance()
    
    print(f"Total de agentes: {performance['total_agents']}")
    print(f"Cobertura sectorial: {performance['system_statistics']['sector_coverage']} sectores")
    print(f"Distribución de volatilidad: {performance['system_statistics']['volatility_distribution']}")
    
    if performance['recommendations']:
        print("\n📋 RECOMENDACIONES DEL SISTEMA:")
        for rec in performance['recommendations']:
            print(f"   • {rec}")
    
    # Guardar estado
    expert_system.save_system_state()
    
    return expert_system, signals, opportunities

if __name__ == "__main__":
    # Ejecutar demo
    system, signals, opportunities = demo_expert_agents_system()
    
    print(f"\n🎯 RESUMEN FINAL:")
    print(f"   • {len(system.agents)} agentes expertos calibrados")
    print(f"   • {len([s for s in signals.values() if s.get('signal') in ['BUY', 'SELL']])} señales activas")
    print(f"   • {len(opportunities)} oportunidades de alta calidad")
    print(f"\n✅ Sistema de agentes expertos listo para trading!")