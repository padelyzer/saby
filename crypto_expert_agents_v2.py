#!/usr/bin/env python3
"""
Sistema de Agentes Expertos para Trading de Criptomonedas V2
Versión simplificada y funcional con calibración independiente
Objetivo: 60-70% win rate mediante especialización por par
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
    """Componentes compartidos de inteligencia de mercado"""
    
    @staticmethod
    def get_bitcoin_sentiment():
        """Análisis simplificado de sentiment Bitcoin"""
        try:
            btc_data = yf.download("BTC-USD", period="7d", interval="1h")
            if len(btc_data) < 10:
                return "NEUTRAL"
                
            # Análisis simple: precio actual vs media móvil
            current_price = btc_data['Close'].iloc[-1]
            sma_7 = btc_data['Close'].rolling(7).mean().iloc[-1]
            
            if current_price > sma_7 * 1.02:
                return "BTC_STRONG"
            elif current_price < sma_7 * 0.98:
                return "BTC_WEAK"
            else:
                return "NEUTRAL"
        except:
            return "NEUTRAL"
    
    @staticmethod
    def validate_volume_conditions(df):
        """Validación básica de volumen"""
        try:
            if 'Volume' not in df.columns or len(df) < 10:
                return True
                
            current_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(10).mean().iloc[-1]
            
            return 0.5 < (current_vol / avg_vol) < 3.0
        except:
            return True

class CryptoExpertAgent(ABC):
    """Clase base para agentes expertos especializados"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.market_intelligence = MarketIntelligence()
        
        # Parámetros base que cada agente personaliza
        self.params = {
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'ema_fast': 12,
            'ema_slow': 26,
            'stop_loss_pct': 2.5,
            'take_profit_pct': 5.0,
            'min_confluence_score': 65
        }
        
        # Cada agente configura sus parámetros
        self.initialize_expert_parameters()
        
    @abstractmethod
    def initialize_expert_parameters(self):
        """Cada agente define sus parámetros específicos"""
        pass
    
    @abstractmethod
    def get_pair_characteristics(self) -> Dict:
        """Características únicas del par"""
        pass
    
    def fetch_market_data(self, period="30d", interval="1h") -> pd.DataFrame:
        """Obtiene datos de mercado"""
        try:
            data = yf.download(self.symbol, period=period, interval=interval)
            if len(data) == 0:
                print(f"No data for {self.symbol}")
                return pd.DataFrame()
            return data
        except Exception as e:
            print(f"Error fetching {self.symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos básicos"""
        if len(df) < 30:
            return df
            
        try:
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
            
            # ATR
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['ATR'] = true_range.rolling(14).mean()
            
        except Exception as e:
            print(f"Error calculating indicators for {self.symbol}: {e}")
            
        return df
    
    def calculate_confluence_score(self, df: pd.DataFrame) -> float:
        """Sistema de puntuación personalizado por agente"""
        if len(df) < 30:
            return 0
            
        try:
            score = 0
            latest = df.iloc[-1]
            characteristics = self.get_pair_characteristics()
            
            # Análisis RSI con peso personalizado
            rsi_weight = characteristics.get('rsi_weight', 0.3)
            if latest['RSI'] < self.params['rsi_oversold']:
                score += 30 * rsi_weight
            elif latest['RSI'] > self.params['rsi_overbought']:
                score -= 25 * rsi_weight
                
            # Análisis MACD
            macd_weight = characteristics.get('macd_weight', 0.25)
            if latest['MACD'] > latest['MACD_Signal']:
                score += 20 * macd_weight
            else:
                score -= 15 * macd_weight
                
            # Análisis de tendencia EMA
            trend_weight = characteristics.get('trend_weight', 0.25)
            if latest['EMA_Fast'] > latest['EMA_Slow']:
                score += 20 * trend_weight
            else:
                score -= 15 * trend_weight
                
            # Factor de volumen
            volume_weight = characteristics.get('volume_weight', 0.1)
            if self.market_intelligence.validate_volume_conditions(df):
                score += 10 * volume_weight
                
            # Análisis de volatilidad
            volatility_weight = characteristics.get('volatility_weight', 0.1)
            try:
                atr_current = latest['ATR']
                atr_avg = df['ATR'].rolling(20).mean().iloc[-1]
                atr_ratio = atr_current / atr_avg if atr_avg > 0 else 1
                
                if 0.8 < atr_ratio < 1.3:  # Volatilidad normal
                    score += 10 * volatility_weight
                elif atr_ratio > 2.0:  # Volatilidad excesiva
                    score -= 15 * volatility_weight
            except:
                pass
                
            # Factor Bitcoin sentiment
            btc_sentiment = self.market_intelligence.get_bitcoin_sentiment()
            if btc_sentiment == "BTC_WEAK" and score > 0:
                score += 10  # Favorable para altcoins
            elif btc_sentiment == "BTC_STRONG" and score > 0:
                score -= 5   # Menos favorable para altcoins
                
            return max(0, min(100, score))
            
        except Exception as e:
            print(f"Error calculating confluence for {self.symbol}: {e}")
            return 0
    
    def generate_signal(self) -> Dict:
        """Genera señal de trading"""
        try:
            df = self.fetch_market_data()
            if df.empty:
                return {"signal": "HOLD", "confidence": 0, "reason": "No data"}
                
            df = self.calculate_indicators(df)
            confluence_score = self.calculate_confluence_score(df)
            
            signal_data = {
                "symbol": self.symbol,
                "timestamp": datetime.now(),
                "confluence_score": confluence_score,
                "signal": "HOLD",
                "confidence": confluence_score / 100,
                "reason": "Insufficient confluence",
                "stop_loss_pct": self.params['stop_loss_pct'],
                "take_profit_pct": self.params['take_profit_pct'],
                "agent_type": type(self).__name__
            }
            
            if confluence_score >= self.params['min_confluence_score']:
                latest = df.iloc[-1]
                
                # Lógica de señal
                if (latest['RSI'] < self.params['rsi_oversold'] and 
                    latest['EMA_Fast'] > latest['EMA_Slow'] and
                    latest['MACD'] > latest['MACD_Signal']):
                    signal_data.update({
                        "signal": "BUY",
                        "reason": f"Strong BUY signal - Confluence: {confluence_score:.1f}"
                    })
                elif (latest['RSI'] > self.params['rsi_overbought'] and 
                      latest['EMA_Fast'] < latest['EMA_Slow']):
                    signal_data.update({
                        "signal": "SELL",
                        "reason": f"Strong SELL signal - Confluence: {confluence_score:.1f}"
                    })
                    
            return signal_data
            
        except Exception as e:
            return {"signal": "ERROR", "confidence": 0, "reason": f"Error: {str(e)}"}
    
    def calibrate_agent(self):
        """Calibra parámetros del agente"""
        try:
            df = self.fetch_market_data(period="90d")
            if df.empty:
                return
                
            df = self.calculate_indicators(df)
            
            # Calibración básica basada en volatilidad
            if 'ATR' in df.columns:
                avg_atr_pct = (df['ATR'] / df['Close']).mean() * 100
                self.params['stop_loss_pct'] = max(1.5, avg_atr_pct * 1.2)
                self.params['take_profit_pct'] = max(3.0, avg_atr_pct * 2.5)
                
            print(f"✅ {self.symbol} calibrado - SL: {self.params['stop_loss_pct']:.1f}% TP: {self.params['take_profit_pct']:.1f}%")
            
        except Exception as e:
            print(f"❌ Error calibrando {self.symbol}: {e}")

# ================================
# AGENTES EXPERTOS ESPECIALIZADOS
# ================================

class BNBExpert(CryptoExpertAgent):
    """Agente Experto para BNB - Token de exchange estable"""
    
    def initialize_expert_parameters(self):
        self.params.update({
            'rsi_overbought': 75,
            'rsi_oversold': 25,
            'ema_fast': 10,
            'ema_slow': 20,
            'stop_loss_pct': 2.0,
            'take_profit_pct': 4.0,
            'min_confluence_score': 60
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM',
            'sector': 'EXCHANGE_TOKEN',
            'rsi_weight': 0.3,
            'macd_weight': 0.25,
            'trend_weight': 0.3,
            'volatility_weight': 0.1,
            'volume_weight': 0.15,
            'correlation_with_btc': 0.7
        }

class SOLExpert(CryptoExpertAgent):
    """Agente Experto para SOL - Alta volatilidad y momentum"""
    
    def initialize_expert_parameters(self):
        self.params.update({
            'rsi_period': 12,
            'rsi_overbought': 78,
            'rsi_oversold': 22,
            'ema_fast': 8,
            'ema_slow': 18,
            'stop_loss_pct': 3.5,
            'take_profit_pct': 7.0,
            'min_confluence_score': 70
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'HIGH',
            'sector': 'SMART_CONTRACT',
            'rsi_weight': 0.35,
            'macd_weight': 0.3,
            'trend_weight': 0.2,
            'volatility_weight': 0.2,
            'volume_weight': 0.1,
            'correlation_with_btc': 0.6
        }

class DOTExpert(CryptoExpertAgent):
    """Agente Experto para DOT - Movimientos institucionales"""
    
    def initialize_expert_parameters(self):
        self.params.update({
            'rsi_period': 16,
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
            'sector': 'INTEROPERABILITY',
            'rsi_weight': 0.25,
            'macd_weight': 0.3,
            'trend_weight': 0.35,
            'volatility_weight': 0.05,
            'volume_weight': 0.2,
            'correlation_with_btc': 0.75
        }

class ADAExpert(CryptoExpertAgent):
    """Agente Experto para ADA - Movimientos graduales y estables"""
    
    def initialize_expert_parameters(self):
        self.params.update({
            'rsi_period': 18,
            'rsi_overbought': 74,
            'rsi_oversold': 26,
            'ema_fast': 16,
            'ema_slow': 40,
            'stop_loss_pct': 2.2,
            'take_profit_pct': 4.5,
            'min_confluence_score': 62
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'MEDIUM_LOW',
            'sector': 'SMART_CONTRACT',
            'rsi_weight': 0.35,
            'macd_weight': 0.2,
            'trend_weight': 0.3,
            'volatility_weight': 0.05,
            'volume_weight': 0.25,
            'correlation_with_btc': 0.8
        }

class AVAXExpert(CryptoExpertAgent):
    """Agente Experto para AVAX - DeFi momentum"""
    
    def initialize_expert_parameters(self):
        self.params.update({
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
            'sector': 'SMART_CONTRACT',
            'rsi_weight': 0.3,
            'macd_weight': 0.25,
            'trend_weight': 0.25,
            'volatility_weight': 0.15,
            'volume_weight': 0.15,
            'correlation_with_btc': 0.65
        }

class LINKExpert(CryptoExpertAgent):
    """Agente Experto para LINK - Oracle token con adopción enterprise"""
    
    def initialize_expert_parameters(self):
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
            'sector': 'ORACLE',
            'rsi_weight': 0.28,
            'macd_weight': 0.27,
            'trend_weight': 0.3,
            'volatility_weight': 0.1,
            'volume_weight': 0.2,
            'correlation_with_btc': 0.72
        }

class DOGEExpert(CryptoExpertAgent):
    """Agente Experto para DOGE - Meme coin con alta especulación"""
    
    def initialize_expert_parameters(self):
        self.params.update({
            'rsi_period': 10,
            'rsi_overbought': 80,
            'rsi_oversold': 20,
            'ema_fast': 6,
            'ema_slow': 15,
            'stop_loss_pct': 4.0,
            'take_profit_pct': 8.0,
            'min_confluence_score': 75
        })
    
    def get_pair_characteristics(self) -> Dict:
        return {
            'volatility_class': 'VERY_HIGH',
            'sector': 'MEME',
            'rsi_weight': 0.4,
            'macd_weight': 0.2,
            'trend_weight': 0.15,
            'volatility_weight': 0.25,
            'volume_weight': 0.05,
            'correlation_with_btc': 0.5
        }

class CryptoExpertSystem:
    """Sistema coordinador de agentes expertos"""
    
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
    
    def calibrate_all_agents(self):
        """Calibra todos los agentes"""
        print("🚀 CALIBRANDO SISTEMA DE AGENTES EXPERTOS")
        print("=" * 60)
        
        for symbol, agent in self.agents.items():
            print(f"\n📊 Calibrando {symbol} ({agent.get_pair_characteristics()['sector']})")
            agent.calibrate_agent()
            
            # Mostrar características
            char = agent.get_pair_characteristics()
            print(f"   Volatilidad: {char['volatility_class']}")
            print(f"   Correlación BTC: {char['correlation_with_btc']}")
        
        print(f"\n✅ TODOS LOS AGENTES CALIBRADOS")
    
    def generate_all_signals(self) -> Dict:
        """Genera señales de todos los agentes"""
        print("\n🎯 GENERANDO SEÑALES DE TRADING")
        print("=" * 50)
        
        signals = {}
        for symbol, agent in self.agents.items():
            signal = agent.generate_signal()
            signals[symbol] = signal
            
            # Mostrar resumen
            print(f"{symbol}: {signal['signal']} "
                  f"(Score: {signal.get('confluence_score', 0):.1f}, "
                  f"Conf: {signal['confidence']:.1%})")
        
        return signals
    
    def get_top_opportunities(self, signals: Dict, min_confidence=0.65) -> List[Dict]:
        """Identifica las mejores oportunidades"""
        opportunities = []
        
        for symbol, signal in signals.items():
            if (signal.get('signal') in ['BUY', 'SELL'] and 
                signal.get('confidence', 0) >= min_confidence):
                
                agent = self.agents[symbol]
                opportunities.append({
                    'symbol': symbol,
                    'signal': signal['signal'],
                    'confidence': signal['confidence'],
                    'confluence_score': signal.get('confluence_score', 0),
                    'agent_type': signal.get('agent_type', ''),
                    'sector': agent.get_pair_characteristics()['sector'],
                    'volatility': agent.get_pair_characteristics()['volatility_class'],
                    'stop_loss': signal.get('stop_loss_pct', 0),
                    'take_profit': signal.get('take_profit_pct', 0),
                    'reason': signal.get('reason', '')
                })
        
        # Ordenar por confluence score
        opportunities.sort(key=lambda x: x['confluence_score'], reverse=True)
        return opportunities
    
    def analyze_system_performance(self) -> Dict:
        """Análisis del sistema"""
        print("\n📈 ANÁLISIS DEL SISTEMA DE AGENTES")
        print("=" * 50)
        
        # Estadísticas por volatilidad
        volatility_dist = {}
        sector_dist = {}
        
        for agent in self.agents.values():
            char = agent.get_pair_characteristics()
            vol = char['volatility_class']
            sector = char['sector']
            
            volatility_dist[vol] = volatility_dist.get(vol, 0) + 1
            sector_dist[sector] = sector_dist.get(sector, 0) + 1
        
        print(f"Distribución por volatilidad: {volatility_dist}")
        print(f"Distribución por sector: {sector_dist}")
        
        return {
            'total_agents': len(self.agents),
            'volatility_distribution': volatility_dist,
            'sector_distribution': sector_dist,
            'coverage': 'Excelente diversificación'
        }
    
    def save_system_state(self):
        """Guarda estado del sistema"""
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
        
        filename = "expert_agents_state_v2.json"
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"💾 Estado guardado en {filename}")

def demo_expert_system():
    """Demo completo del sistema"""
    print("🤖 SISTEMA DE AGENTES EXPERTOS CRYPTO V2.0")
    print("=" * 70)
    
    # Inicializar sistema
    system = CryptoExpertSystem()
    
    # Calibrar agentes
    system.calibrate_all_agents()
    
    # Generar señales
    signals = system.generate_all_signals()
    
    # Buscar oportunidades
    opportunities = system.get_top_opportunities(signals, min_confidence=0.6)
    
    print(f"\n🏆 MEJORES OPORTUNIDADES ({len(opportunities)} encontradas)")
    print("=" * 60)
    
    if opportunities:
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n{i}. {opp['symbol']} - {opp['signal']}")
            print(f"   Agente: {opp['agent_type']} ({opp['sector']})")
            print(f"   Confianza: {opp['confidence']:.1%}")
            print(f"   Score: {opp['confluence_score']:.1f}")
            print(f"   Volatilidad: {opp['volatility']}")
            print(f"   Risk Management: SL {opp['stop_loss']:.1f}% / TP {opp['take_profit']:.1f}%")
            print(f"   Razón: {opp['reason']}")
    else:
        print("No hay oportunidades que cumplan los criterios")
    
    # Análisis del sistema
    performance = system.analyze_system_performance()
    
    # Guardar estado
    system.save_system_state()
    
    print(f"\n✅ SISTEMA COMPLETO Y OPERATIVO")
    print(f"   • {performance['total_agents']} agentes especializados")
    print(f"   • {len(opportunities)} oportunidades detectadas")
    print(f"   • Cobertura: {len(performance['sector_distribution'])} sectores")
    
    return system, signals, opportunities

if __name__ == "__main__":
    demo_expert_system()