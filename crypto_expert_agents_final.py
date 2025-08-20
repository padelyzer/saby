#!/usr/bin/env python3
"""
Sistema de Agentes Expertos para Trading de Criptomonedas - VERSIÓN FINAL
Cada agente especializado en un par específico con calibración independiente
Objetivo: 60-70% win rate mediante especialización y análisis profundo por par

✅ CARACTERÍSTICAS PRINCIPALES:
- 7 agentes expertos especializados (BNB, SOL, DOT, ADA, AVAX, LINK, DOGE)
- Calibración automática basada en volatilidad histórica
- Parámetros independientes optimizados por par
- Sistema de confluence scoring personalizado
- Gestión de riesgo adaptada por características del activo
- Detección de régimen de mercado compartida
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
    Inteligencia de mercado compartida entre todos los agentes
    Análisis macro y detección de tendencia general de Bitcoin
    """
    
    @staticmethod
    def get_market_regime():
        """Detecta el régimen actual del mercado crypto"""
        try:
            # Obtener datos de Bitcoin como indicador principal
            btc_data = yf.download("BTC-USD", period="30d", interval="1d")
            if len(btc_data) < 10:
                return {"regime": "NEUTRAL", "strength": 0.5}
            
            # Análisis de tendencia usando EMAs
            current_price = btc_data['Close'].iloc[-1]
            ema_10 = btc_data['Close'].ewm(span=10).mean().iloc[-1]
            ema_21 = btc_data['Close'].ewm(span=21).mean().iloc[-1]
            
            # Determinar régimen
            if current_price > ema_10 > ema_21:
                if current_price > ema_10 * 1.02:
                    return {"regime": "STRONG_BULL", "strength": 0.9}
                else:
                    return {"regime": "BULL", "strength": 0.7}
            elif current_price < ema_10 < ema_21:
                if current_price < ema_10 * 0.98:
                    return {"regime": "STRONG_BEAR", "strength": 0.9}
                else:
                    return {"regime": "BEAR", "strength": 0.7}
            else:
                return {"regime": "SIDEWAYS", "strength": 0.5}
                
        except Exception as e:
            print(f"Error detecting market regime: {e}")
            return {"regime": "NEUTRAL", "strength": 0.5}
    
    @staticmethod
    def validate_volume_conditions(df):
        """Validación de condiciones de volumen saludables"""
        try:
            if 'Volume' not in df.columns or len(df) < 20:
                return True
            
            current_volume = df['Volume'].iloc[-1]
            avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Volumen debe estar en rango normal (no extremos)
            if pd.isna(avg_volume) or avg_volume == 0:
                return True
                
            volume_ratio = current_volume / avg_volume
            return 0.3 < volume_ratio < 4.0  # Rango aceptable
            
        except Exception:
            return True

class CryptoExpertAgent(ABC):
    """
    Clase base para agentes expertos especializados
    Cada agente tiene conocimiento profundo de su par asignado
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.market_intelligence = MarketIntelligence()
        
        # Parámetros base - cada agente los personaliza
        self.params = {
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'ema_fast': 12,
            'ema_slow': 26,
            'stop_loss_pct': 2.5,
            'take_profit_pct': 5.0,
            'min_confluence_score': 65,
            'volume_threshold': 1.5
        }
        
        # Inicializar parámetros específicos del agente
        self.setup_agent_parameters()
        
        # Estado interno del agente
        self.last_calibration = None
        self.performance_history = []
        
    @abstractmethod
    def setup_agent_parameters(self):
        """Cada agente define sus parámetros optimizados"""
        pass
    
    @abstractmethod
    def get_trading_characteristics(self) -> Dict:
        """Retorna características de trading específicas del par"""
        pass
    
    def fetch_data(self, period="60d", interval="1h") -> pd.DataFrame:
        """Obtiene datos históricos del par"""
        try:
            data = yf.download(self.symbol, period=period, interval=interval, progress=False)
            if data.empty:
                print(f"⚠️ No data available for {self.symbol}")
                return pd.DataFrame()
            return data
        except Exception as e:
            print(f"❌ Error fetching data for {self.symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos básicos"""
        if len(df) < 50:
            return df
        
        try:
            # RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=self.params['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
            
            # Evitar división por cero
            rs = gain / loss.replace(0, np.nan)
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
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR'] = true_range.rolling(14).mean()
            
            # Bollinger Bands
            bb_period = 20
            df['BB_Middle'] = df['Close'].rolling(bb_period).mean()
            bb_std = df['Close'].rolling(bb_period).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            
            return df
            
        except Exception as e:
            print(f"Error calculating indicators for {self.symbol}: {e}")
            return df
    
    def calculate_specialized_score(self, df: pd.DataFrame) -> float:
        """
        Sistema de scoring de confluencia personalizado por agente
        Cada agente pondera los indicadores según su experiencia del par
        """
        if len(df) < 30:
            return 0
        
        try:
            score = 0
            latest = df.iloc[-1]
            characteristics = self.get_trading_characteristics()
            
            # 1. Análisis RSI con peso personalizado
            rsi_weight = characteristics.get('rsi_importance', 0.25)
            rsi_value = latest['RSI'] if not pd.isna(latest['RSI']) else 50
            
            if rsi_value < self.params['rsi_oversold']:
                score += 30 * rsi_weight  # Señal de compra
            elif rsi_value > self.params['rsi_overbought']:
                score -= 25 * rsi_weight  # Señal de venta
            elif 40 < rsi_value < 60:
                score += 5 * rsi_weight   # Zona neutral favorable
            
            # 2. Análisis MACD
            macd_weight = characteristics.get('macd_importance', 0.2)
            if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_Signal']):
                if latest['MACD'] > latest['MACD_Signal']:
                    score += 20 * macd_weight
                else:
                    score -= 15 * macd_weight
            
            # 3. Tendencia EMA
            trend_weight = characteristics.get('trend_importance', 0.25)
            if not pd.isna(latest['EMA_Fast']) and not pd.isna(latest['EMA_Slow']):
                if latest['EMA_Fast'] > latest['EMA_Slow']:
                    score += 25 * trend_weight
                else:
                    score -= 20 * trend_weight
            
            # 4. Volatilidad (ATR)
            volatility_weight = characteristics.get('volatility_importance', 0.1)
            if not pd.isna(latest['ATR']) and len(df) > 50:
                atr_avg = df['ATR'].rolling(50).mean().iloc[-1]
                if not pd.isna(atr_avg) and atr_avg > 0:
                    atr_ratio = latest['ATR'] / atr_avg
                    
                    if 0.8 <= atr_ratio <= 1.3:  # Volatilidad normal
                        score += 15 * volatility_weight
                    elif atr_ratio > 2.0:  # Volatilidad excesiva
                        score -= 20 * volatility_weight
            
            # 5. Condiciones de volumen
            volume_weight = characteristics.get('volume_importance', 0.1)
            if self.market_intelligence.validate_volume_conditions(df):
                score += 10 * volume_weight
            else:
                score -= 5 * volume_weight
            
            # 6. Posición en Bollinger Bands
            bb_weight = characteristics.get('bb_importance', 0.1)
            if not any(pd.isna([latest['BB_Upper'], latest['BB_Lower'], latest['Close']])):
                bb_range = latest['BB_Upper'] - latest['BB_Lower']
                if bb_range > 0:
                    bb_position = (latest['Close'] - latest['BB_Lower']) / bb_range
                    
                    if bb_position < 0.2:  # Cerca del límite inferior
                        score += 15 * bb_weight
                    elif bb_position > 0.8:  # Cerca del límite superior
                        score -= 15 * bb_weight
            
            # 7. Factor de régimen de mercado
            market_regime = self.market_intelligence.get_market_regime()
            regime_adjustment = characteristics.get('btc_correlation', 0.7)
            
            if market_regime['regime'] in ['STRONG_BULL', 'BULL'] and score > 0:
                score += 10 * regime_adjustment * market_regime['strength']
            elif market_regime['regime'] in ['STRONG_BEAR', 'BEAR'] and score > 0:
                score -= 10 * regime_adjustment * market_regime['strength']
            
            # Normalizar score a rango 0-100
            final_score = max(0, min(100, score))
            return final_score
            
        except Exception as e:
            print(f"Error calculating specialized score for {self.symbol}: {e}")
            return 0
    
    def generate_trading_signal(self) -> Dict:
        """Genera señal de trading basada en análisis especializado"""
        try:
            # Obtener datos
            df = self.fetch_data()
            if df.empty:
                return {
                    "symbol": self.symbol,
                    "signal": "HOLD",
                    "confidence": 0,
                    "reason": "No data available",
                    "timestamp": datetime.now()
                }
            
            # Calcular indicadores
            df = self.calculate_technical_indicators(df)
            
            # Calcular score de confluencia
            confluence_score = self.calculate_specialized_score(df)
            
            # Datos base de la señal
            signal_data = {
                "symbol": self.symbol,
                "timestamp": datetime.now(),
                "agent_type": type(self).__name__,
                "confluence_score": confluence_score,
                "confidence": confluence_score / 100,
                "signal": "HOLD",
                "reason": "Analyzing...",
                "risk_management": {
                    "stop_loss_pct": self.params['stop_loss_pct'],
                    "take_profit_pct": self.params['take_profit_pct']
                },
                "market_conditions": self.market_intelligence.get_market_regime()
            }
            
            # Evaluar señal basada en confluence score
            if confluence_score >= self.params['min_confluence_score']:
                latest = df.iloc[-1]
                
                # Condiciones para BUY
                buy_conditions = (
                    not pd.isna(latest['RSI']) and latest['RSI'] < self.params['rsi_oversold'] and
                    not pd.isna(latest['EMA_Fast']) and not pd.isna(latest['EMA_Slow']) and
                    latest['EMA_Fast'] > latest['EMA_Slow'] and
                    not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_Signal']) and
                    latest['MACD'] > latest['MACD_Signal']
                )
                
                # Condiciones para SELL
                sell_conditions = (
                    not pd.isna(latest['RSI']) and latest['RSI'] > self.params['rsi_overbought'] and
                    not pd.isna(latest['EMA_Fast']) and not pd.isna(latest['EMA_Slow']) and
                    latest['EMA_Fast'] < latest['EMA_Slow']
                )
                
                if buy_conditions:
                    signal_data.update({
                        "signal": "BUY",
                        "reason": f"Strong BUY signal - Confluence: {confluence_score:.1f}, RSI oversold + bullish trend"
                    })
                elif sell_conditions:
                    signal_data.update({
                        "signal": "SELL",
                        "reason": f"Strong SELL signal - Confluence: {confluence_score:.1f}, RSI overbought + bearish trend"
                    })
                else:
                    signal_data.update({
                        "reason": f"High confluence ({confluence_score:.1f}) but mixed signals - monitoring"
                    })
            else:
                signal_data.update({
                    "reason": f"Confluence score too low ({confluence_score:.1f}) - waiting for better setup"
                })
            
            return signal_data
            
        except Exception as e:
            return {
                "symbol": self.symbol,
                "signal": "ERROR",
                "confidence": 0,
                "reason": f"Error generating signal: {str(e)}",
                "timestamp": datetime.now()
            }
    
    def calibrate_parameters(self):
        """Calibra parámetros del agente basado en volatilidad histórica"""
        try:
            df = self.fetch_data(period="180d")
            if df.empty:
                print(f"⚠️ No data for calibration of {self.symbol}")
                return
            
            df = self.calculate_technical_indicators(df)
            
            # Calibrar stop loss y take profit basado en ATR
            if 'ATR' in df.columns:
                atr_values = df['ATR'].dropna()
                if len(atr_values) > 0:
                    avg_atr_pct = (atr_values.mean() / df['Close'].mean()) * 100
                    
                    # Ajustar parámetros según volatilidad
                    self.params['stop_loss_pct'] = max(1.5, avg_atr_pct * 1.2)
                    self.params['take_profit_pct'] = max(3.0, avg_atr_pct * 2.5)
            
            # Optimizar niveles de RSI según comportamiento histórico
            if 'RSI' in df.columns:
                rsi_values = df['RSI'].dropna()
                if len(rsi_values) > 0:
                    rsi_std = rsi_values.std()
                    rsi_mean = rsi_values.mean()
                    
                    # Ajustar niveles si hay alta variabilidad
                    if rsi_std > 15:
                        self.params['rsi_oversold'] = max(20, rsi_mean - rsi_std * 0.8)
                        self.params['rsi_overbought'] = min(80, rsi_mean + rsi_std * 0.8)
            
            self.last_calibration = datetime.now()
            print(f"✅ {self.symbol} calibrado - SL: {self.params['stop_loss_pct']:.1f}% TP: {self.params['take_profit_pct']:.1f}%")
            
        except Exception as e:
            print(f"❌ Error calibrating {self.symbol}: {e}")

# ================================
# AGENTES EXPERTOS ESPECIALIZADOS
# ================================

class BNBExpert(CryptoExpertAgent):
    """
    Agente Experto para BNB-USD
    ESPECIALIZACIÓN: Token de exchange con movimientos más estables
    CARACTERÍSTICAS: Correlación con volumen de trading, menos volatilidad
    """
    
    def setup_agent_parameters(self):
        self.params.update({
            'rsi_overbought': 75,  # Más conservador por menor volatilidad
            'rsi_oversold': 25,
            'ema_fast': 10,        # EMAs más rápidas para captar movimientos
            'ema_slow': 20,
            'stop_loss_pct': 2.0,  # Stops más ajustados
            'take_profit_pct': 4.0,
            'min_confluence_score': 60  # Threshold menor por estabilidad
        })
    
    def get_trading_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM',
            'sector': 'EXCHANGE_TOKEN',
            'rsi_importance': 0.3,
            'macd_importance': 0.25,
            'trend_importance': 0.3,
            'volatility_importance': 0.1,
            'volume_importance': 0.15,
            'bb_importance': 0.1,
            'btc_correlation': 0.7,
            'optimal_timeframes': ['1h', '4h'],
            'key_support_levels': [580, 550, 500],
            'key_resistance_levels': [650, 700, 750]
        }

class SOLExpert(CryptoExpertAgent):
    """
    Agente Experto para SOL-USD
    ESPECIALIZACIÓN: Alta volatilidad, movimientos explosivos
    CARACTERÍSTICAS: Correlación con DeFi, momentum trading
    """
    
    def setup_agent_parameters(self):
        self.params.update({
            'rsi_period': 12,      # Más responsive para alta volatilidad
            'rsi_overbought': 78,  # Niveles más extremos
            'rsi_oversold': 22,
            'ema_fast': 8,         # EMAs muy rápidas
            'ema_slow': 18,
            'stop_loss_pct': 3.5,  # Stops más amplios
            'take_profit_pct': 7.0,
            'min_confluence_score': 70  # Score más alto por volatilidad
        })
    
    def get_trading_characteristics(self) -> Dict:
        return {
            'volatility_class': 'HIGH',
            'sector': 'SMART_CONTRACT_L1',
            'rsi_importance': 0.35,  # RSI muy efectivo en SOL
            'macd_importance': 0.3,
            'trend_importance': 0.2,
            'volatility_importance': 0.2,
            'volume_importance': 0.1,
            'bb_importance': 0.05,
            'btc_correlation': 0.6,
            'optimal_timeframes': ['15m', '1h'],
            'key_support_levels': [140, 120, 100],
            'key_resistance_levels': [180, 200, 220]
        }

class DOTExpert(CryptoExpertAgent):
    """
    Agente Experto para DOT-USD
    ESPECIALIZACIÓN: Movimientos institucionales, interoperabilidad
    CARACTERÍSTICAS: Sigue tendencias, correlación con desarrollo ecosistema
    """
    
    def setup_agent_parameters(self):
        self.params.update({
            'rsi_period': 16,      # Período más largo para suavizar
            'rsi_overbought': 72,
            'rsi_oversold': 28,
            'ema_fast': 15,
            'ema_slow': 35,
            'stop_loss_pct': 2.8,
            'take_profit_pct': 5.5,
            'min_confluence_score': 65
        })
    
    def get_trading_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM_HIGH',
            'sector': 'INTEROPERABILITY',
            'rsi_importance': 0.25,
            'macd_importance': 0.3,   # MACD muy efectivo en DOT
            'trend_importance': 0.35, # Sigue tendencias muy bien
            'volatility_importance': 0.05,
            'volume_importance': 0.2,
            'bb_importance': 0.05,
            'btc_correlation': 0.75,
            'optimal_timeframes': ['1h', '4h'],
            'key_support_levels': [6.5, 6.0, 5.5],
            'key_resistance_levels': [8.0, 9.0, 10.0]
        }

class ADAExpert(CryptoExpertAgent):
    """
    Agente Experto para ADA-USD
    ESPECIALIZACIÓN: Movimientos graduales, alta correlación BTC
    CARACTERÍSTICAS: Desarrollo académico, adopción institucional
    """
    
    def setup_agent_parameters(self):
        self.params.update({
            'rsi_period': 18,      # Período largo para suavizar
            'rsi_overbought': 74,
            'rsi_oversold': 26,
            'ema_fast': 16,
            'ema_slow': 40,
            'stop_loss_pct': 2.2,  # Menor volatilidad
            'take_profit_pct': 4.5,
            'min_confluence_score': 62
        })
    
    def get_trading_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM_LOW',
            'sector': 'SMART_CONTRACT_L1',
            'rsi_importance': 0.35,  # RSI muy confiable en ADA
            'macd_importance': 0.2,
            'trend_importance': 0.3,
            'volatility_importance': 0.05,
            'volume_importance': 0.25, # Volumen importante en ADA
            'bb_importance': 0.05,
            'btc_correlation': 0.8,   # Alta correlación
            'optimal_timeframes': ['1h', '4h', '1d'],
            'key_support_levels': [0.35, 0.30, 0.25],
            'key_resistance_levels': [0.50, 0.60, 0.70]
        }

class AVAXExpert(CryptoExpertAgent):
    """
    Agente Experto para AVAX-USD
    ESPECIALIZACIÓN: Ecosistema DeFi, subnets
    CARACTERÍSTICAS: Volatilidad media-alta, momentum DeFi
    """
    
    def setup_agent_parameters(self):
        self.params.update({
            'rsi_overbought': 76,
            'rsi_oversold': 24,
            'ema_fast': 12,
            'ema_slow': 28,
            'stop_loss_pct': 3.0,
            'take_profit_pct': 6.0,
            'min_confluence_score': 68
        })
    
    def get_trading_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM_HIGH',
            'sector': 'SMART_CONTRACT_L1',
            'rsi_importance': 0.3,
            'macd_importance': 0.25,
            'trend_importance': 0.25,
            'volatility_importance': 0.15,
            'volume_importance': 0.15,
            'bb_importance': 0.1,
            'btc_correlation': 0.65,
            'optimal_timeframes': ['1h', '4h'],
            'key_support_levels': [25, 22, 18],
            'key_resistance_levels': [35, 40, 45]
        }

class LINKExpert(CryptoExpertAgent):
    """
    Agente Experto para LINK-USD
    ESPECIALIZACIÓN: Oracle líder, adopción enterprise
    CARACTERÍSTICAS: Correlación con smart contracts, estabilidad relativa
    """
    
    def setup_agent_parameters(self):
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
    
    def get_trading_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM',
            'sector': 'ORACLE_INFRASTRUCTURE',
            'rsi_importance': 0.28,
            'macd_importance': 0.27,
            'trend_importance': 0.3,
            'volatility_importance': 0.1,
            'volume_importance': 0.2,
            'bb_importance': 0.05,
            'btc_correlation': 0.72,
            'optimal_timeframes': ['1h', '4h'],
            'key_support_levels': [14, 12, 10],
            'key_resistance_levels': [18, 20, 25]
        }

class DOGEExpert(CryptoExpertAgent):
    """
    Agente Experto para DOGE-USD
    ESPECIALIZACIÓN: Meme coin, alta especulación
    CARACTERÍSTICAS: Volatilidad extrema, sentiment-driven, baja correlación BTC
    """
    
    def setup_agent_parameters(self):
        self.params.update({
            'rsi_period': 10,      # Muy responsive
            'rsi_overbought': 80,  # Niveles extremos
            'rsi_oversold': 20,
            'ema_fast': 6,         # EMAs muy rápidas
            'ema_slow': 15,
            'stop_loss_pct': 4.0,  # Stops amplios por volatilidad
            'take_profit_pct': 8.0,
            'min_confluence_score': 75  # Score alto por especulación
        })
    
    def get_trading_characteristics(self) -> Dict:
        return {
            'volatility_class': 'VERY_HIGH',
            'sector': 'MEME_CURRENCY',
            'rsi_importance': 0.4,   # RSI crítico en DOGE
            'macd_importance': 0.2,
            'trend_importance': 0.15,
            'volatility_importance': 0.25, # Volatilidad muy importante
            'volume_importance': 0.05,     # Volumen menos relevante
            'bb_importance': 0.1,
            'btc_correlation': 0.5,        # Menor correlación
            'optimal_timeframes': ['15m', '1h'],
            'key_support_levels': [0.08, 0.06, 0.05],
            'key_resistance_levels': [0.12, 0.15, 0.20]
        }

class CryptoExpertSystem:
    """
    Sistema coordinador de todos los agentes expertos
    Gestiona calibración, señales y análisis de rendimiento
    """
    
    def __init__(self):
        print("🚀 Inicializando Sistema de Agentes Expertos Crypto")
        
        self.agents = {
            'BNB-USD': BNBExpert('BNB-USD'),
            'SOL-USD': SOLExpert('SOL-USD'),
            'DOT-USD': DOTExpert('DOT-USD'),
            'ADA-USD': ADAExpert('ADA-USD'),
            'AVAX-USD': AVAXExpert('AVAX-USD'),
            'LINK-USD': LINKExpert('LINK-USD'),
            'DOGE-USD': DOGEExpert('DOGE-USD')
        }
        
        self.system_metrics = {
            'total_agents': len(self.agents),
            'last_calibration': None,
            'total_signals_generated': 0
        }
        
        print(f"✅ {len(self.agents)} agentes expertos inicializados")
    
    def calibrate_all_agents(self):
        """Calibra todos los agentes basado en datos históricos"""
        print(f"\n🔧 CALIBRANDO SISTEMA DE AGENTES EXPERTOS")
        print("=" * 70)
        
        for symbol, agent in self.agents.items():
            characteristics = agent.get_trading_characteristics()
            print(f"\n📊 {symbol} ({characteristics['sector']})")
            print(f"   Volatilidad: {characteristics['volatility_class']}")
            print(f"   Correlación BTC: {characteristics['btc_correlation']}")
            
            # Calibrar agente
            agent.calibrate_parameters()
        
        self.system_metrics['last_calibration'] = datetime.now()
        print(f"\n✅ CALIBRACIÓN COMPLETADA - Todos los agentes optimizados")
    
    def generate_market_signals(self) -> Dict:
        """Genera señales de trading de todos los agentes"""
        print(f"\n🎯 GENERANDO SEÑALES DE TRADING")
        print("=" * 60)
        
        signals = {}
        active_signals = 0
        
        # Obtener régimen de mercado actual
        market_regime = MarketIntelligence.get_market_regime()
        print(f"📈 Régimen de mercado: {market_regime['regime']} (Fuerza: {market_regime['strength']:.1%})")
        print("-" * 60)
        
        for symbol, agent in self.agents.items():
            signal = agent.generate_trading_signal()
            signals[symbol] = signal
            
            # Contar señales activas
            if signal['signal'] in ['BUY', 'SELL']:
                active_signals += 1
            
            # Mostrar resumen
            status_emoji = "🟢" if signal['signal'] == 'BUY' else "🔴" if signal['signal'] == 'SELL' else "🟡"
            print(f"{status_emoji} {symbol}: {signal['signal']} "
                  f"(Score: {signal.get('confluence_score', 0):.1f}, "
                  f"Confianza: {signal['confidence']:.1%})")
        
        self.system_metrics['total_signals_generated'] += len(signals)
        
        print(f"\n📊 Resumen: {active_signals} señales activas de {len(signals)} agentes")
        return signals
    
    def get_best_opportunities(self, signals: Dict, min_confidence=0.65) -> List[Dict]:
        """Identifica las mejores oportunidades de trading"""
        opportunities = []
        
        for symbol, signal in signals.items():
            if (signal.get('signal') in ['BUY', 'SELL'] and 
                signal.get('confidence', 0) >= min_confidence):
                
                agent = self.agents[symbol]
                characteristics = agent.get_trading_characteristics()
                
                opportunity = {
                    'symbol': symbol,
                    'signal': signal['signal'],
                    'confidence': signal['confidence'],
                    'confluence_score': signal.get('confluence_score', 0),
                    'agent_type': signal.get('agent_type', ''),
                    'sector': characteristics['sector'],
                    'volatility_class': characteristics['volatility_class'],
                    'stop_loss_pct': signal['risk_management']['stop_loss_pct'],
                    'take_profit_pct': signal['risk_management']['take_profit_pct'],
                    'reason': signal.get('reason', ''),
                    'market_conditions': signal.get('market_conditions', {}),
                    'btc_correlation': characteristics['btc_correlation'],
                    'optimal_timeframes': characteristics['optimal_timeframes']
                }
                opportunities.append(opportunity)
        
        # Ordenar por confluence score (mayor a menor)
        opportunities.sort(key=lambda x: x['confluence_score'], reverse=True)
        return opportunities
    
    def analyze_system_performance(self) -> Dict:
        """Análisis comprehensivo del sistema"""
        print(f"\n📈 ANÁLISIS DEL SISTEMA DE AGENTES EXPERTOS")
        print("=" * 60)
        
        # Recopilar estadísticas
        stats = {
            'agents_by_volatility': {},
            'agents_by_sector': {},
            'correlation_analysis': {},
            'system_coverage': {}
        }
        
        for symbol, agent in self.agents.items():
            char = agent.get_trading_characteristics()
            
            # Por volatilidad
            vol_class = char['volatility_class']
            stats['agents_by_volatility'][vol_class] = stats['agents_by_volatility'].get(vol_class, 0) + 1
            
            # Por sector
            sector = char['sector']
            stats['agents_by_sector'][sector] = stats['agents_by_sector'].get(sector, 0) + 1
            
            # Análisis de correlación
            correlation = char['btc_correlation']
            if correlation >= 0.8:
                correlation_level = 'HIGH'
            elif correlation >= 0.6:
                correlation_level = 'MEDIUM'
            else:
                correlation_level = 'LOW'
            
            stats['correlation_analysis'][correlation_level] = stats['correlation_analysis'].get(correlation_level, 0) + 1
        
        # Mostrar estadísticas
        print(f"📊 Distribución por volatilidad: {stats['agents_by_volatility']}")
        print(f"🏢 Distribución por sector: {stats['agents_by_sector']}")
        print(f"📈 Correlación con BTC: {stats['correlation_analysis']}")
        
        # Análisis de cobertura
        total_sectors = len(stats['agents_by_sector'])
        total_volatility_classes = len(stats['agents_by_volatility'])
        
        stats['system_coverage'] = {
            'sector_diversification': total_sectors,
            'volatility_diversification': total_volatility_classes,
            'total_agents': len(self.agents),
            'coverage_quality': 'Excelente' if total_sectors >= 4 and total_volatility_classes >= 4 else 'Buena'
        }
        
        print(f"🎯 Cobertura del sistema: {stats['system_coverage']['coverage_quality']}")
        print(f"   • {total_sectors} sectores cubiertos")
        print(f"   • {total_volatility_classes} clases de volatilidad")
        
        return stats
    
    def save_system_state(self, filename: str = None):
        """Guarda el estado completo del sistema"""
        if filename is None:
            filename = f"expert_agents_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        state = {
            'timestamp': datetime.now().isoformat(),
            'system_version': '2.0',
            'system_metrics': self.system_metrics,
            'agents': {}
        }
        
        for symbol, agent in self.agents.items():
            state['agents'][symbol] = {
                'agent_type': type(agent).__name__,
                'parameters': agent.params,
                'characteristics': agent.get_trading_characteristics(),
                'last_calibration': agent.last_calibration.isoformat() if agent.last_calibration else None
            }
        
        try:
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            print(f"💾 Estado del sistema guardado en: {filename}")
        except Exception as e:
            print(f"❌ Error guardando estado: {e}")
    
    def load_system_state(self, filename: str):
        """Carga un estado previo del sistema"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            
            print(f"📁 Cargando estado del sistema desde: {filename}")
            print(f"   Versión: {state.get('system_version', 'Unknown')}")
            print(f"   Timestamp: {state.get('timestamp', 'Unknown')}")
            
            return state
        except Exception as e:
            print(f"❌ Error cargando estado: {e}")
            return None

def demo_complete_system():
    """Demostración completa del sistema de agentes expertos"""
    print("🤖 SISTEMA DE AGENTES EXPERTOS PARA TRADING CRYPTO")
    print("🎯 OBJETIVO: 60-70% WIN RATE MEDIANTE ESPECIALIZACIÓN")
    print("=" * 80)
    
    # 1. Inicializar sistema
    expert_system = CryptoExpertSystem()
    
    # 2. Calibrar todos los agentes
    expert_system.calibrate_all_agents()
    
    # 3. Generar señales de trading
    signals = expert_system.generate_market_signals()
    
    # 4. Buscar las mejores oportunidades
    opportunities = expert_system.get_best_opportunities(signals, min_confidence=0.6)
    
    print(f"\n🏆 MEJORES OPORTUNIDADES DE TRADING ({len(opportunities)} encontradas)")
    print("=" * 80)
    
    if opportunities:
        for i, opp in enumerate(opportunities[:5], 1):  # Top 5
            print(f"\n{i}. 🎯 {opp['symbol']} - {opp['signal']}")
            print(f"   🤖 Agente: {opp['agent_type']}")
            print(f"   🏢 Sector: {opp['sector']}")
            print(f"   📊 Confianza: {opp['confidence']:.1%}")
            print(f"   ⚡ Score Confluencia: {opp['confluence_score']:.1f}")
            print(f"   📈 Volatilidad: {opp['volatility_class']}")
            print(f"   🛡️ Stop Loss: {opp['stop_loss_pct']:.1f}%")
            print(f"   🎯 Take Profit: {opp['take_profit_pct']:.1f}%")
            print(f"   🔗 Correlación BTC: {opp['btc_correlation']:.1%}")
            print(f"   ⏰ Timeframes: {', '.join(opp['optimal_timeframes'])}")
            print(f"   💡 Razón: {opp['reason']}")
    else:
        print("📋 No hay oportunidades que cumplan los criterios mínimos")
        print("🔍 Recomendación: Esperar mejores condiciones de mercado")
    
    # 5. Análisis del sistema
    performance_stats = expert_system.analyze_system_performance()
    
    # 6. Guardar estado
    expert_system.save_system_state()
    
    # 7. Resumen final
    print(f"\n🎉 RESUMEN FINAL DEL SISTEMA")
    print("=" * 50)
    print(f"✅ {len(expert_system.agents)} agentes expertos calibrados y operativos")
    print(f"📊 {len(opportunities)} oportunidades de trading identificadas")
    print(f"🏢 {performance_stats['system_coverage']['sector_diversification']} sectores crypto cubiertos")
    print(f"📈 Calidad de cobertura: {performance_stats['system_coverage']['coverage_quality']}")
    print(f"🎯 Sistema listo para trading con especialización por par")
    
    print(f"\n💡 SIGUIENTE PASO:")
    print(f"   Usar las señales generadas para paper trading o trading en vivo")
    print(f"   Monitorear performance y ajustar parámetros según resultados")
    
    return expert_system, signals, opportunities, performance_stats

if __name__ == "__main__":
    # Ejecutar demostración completa
    system, signals, opportunities, performance = demo_complete_system()