#!/usr/bin/env python3
"""
Fear & Greed Index Integration
Integra el índice de Fear & Greed de crypto para análisis de sentimiento del mercado
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Optional

class FearGreedIndexAnalyzer:
    """
    Analizador del índice Fear & Greed para crypto
    Integra datos de multiple fuentes:
    1. Alternative.me Fear & Greed Index
    2. Análisis de volatilidad
    3. Momentum del mercado
    4. Volumen de trading
    5. Dominancia de Bitcoin
    6. Social media sentiment
    """
    
    def __init__(self):
        # APIs y fuentes de datos
        self.apis = {
            'fear_greed': {
                'base_url': 'https://api.alternative.me/fng/',
                'endpoints': {
                    'current': '',
                    'historical': '?limit={limit}&date_format=world'
                },
                'rate_limit': 300  # 5 minutes between calls
            },
            'crypto_compare': {
                'base_url': 'https://min-api.cryptocompare.com/data',
                'api_key': 'YOUR_CRYPTOCOMPARE_KEY',  # Opcional
                'endpoints': {
                    'social': '/v2/social/coin/histo',
                    'volume': '/v2/histohour'
                }
            }
        }
        
        # Configuración del índice
        self.index_config = {
            # Rangos del Fear & Greed Index
            'ranges': {
                'extreme_fear': {'min': 0, 'max': 25, 'action': 'BUY_OPPORTUNITY'},
                'fear': {'min': 25, 'max': 45, 'action': 'ACCUMULATE'},
                'neutral': {'min': 45, 'max': 55, 'action': 'HOLD'},
                'greed': {'min': 55, 'max': 75, 'action': 'CAUTION'},
                'extreme_greed': {'min': 75, 'max': 100, 'action': 'SELL_SIGNAL'}
            },
            
            # Pesos para componentes del índice
            'components': {
                'official_fg_index': {'weight': 0.4, 'enabled': True},
                'volatility_index': {'weight': 0.2, 'enabled': True},
                'momentum_index': {'weight': 0.15, 'enabled': True},
                'volume_index': {'weight': 0.15, 'enabled': True},
                'dominance_index': {'weight': 0.1, 'enabled': True}
            },
            
            # Configuración de trading
            'trading_adjustments': {
                'extreme_fear': {
                    'position_multiplier': 1.3,    # Aumentar posiciones
                    'entry_aggressiveness': 1.2,   # Más agresivo en entradas
                    'stop_multiplier': 1.1         # Stops más amplios
                },
                'fear': {
                    'position_multiplier': 1.1,
                    'entry_aggressiveness': 1.1,
                    'stop_multiplier': 1.05
                },
                'neutral': {
                    'position_multiplier': 1.0,
                    'entry_aggressiveness': 1.0,
                    'stop_multiplier': 1.0
                },
                'greed': {
                    'position_multiplier': 0.9,
                    'entry_aggressiveness': 0.9,
                    'stop_multiplier': 0.95
                },
                'extreme_greed': {
                    'position_multiplier': 0.7,    # Reducir posiciones
                    'entry_aggressiveness': 0.8,   # Menos agresivo
                    'stop_multiplier': 0.9         # Stops más estrictos
                }
            }
        }
        
        # Cache para datos
        self.cache = {
            'fear_greed_data': None,
            'last_update': None,
            'cache_duration': 3600  # 1 hora
        }
        
    def get_fear_greed_analysis(self, symbol: str = 'BTC') -> Dict:
        """Obtiene análisis completo del Fear & Greed Index"""
        
        print(f"😨😎 Analizando Fear & Greed Index para {symbol}...")
        
        try:
            # Obtener índice oficial
            official_index = self._get_official_fear_greed_index()
            
            # Calcular componentes adicionales
            components = self._calculate_additional_components(symbol)
            
            # Calcular índice compuesto
            composite_index = self._calculate_composite_index(official_index, components)
            
            # Determinar clasificación y acción
            classification = self._classify_fear_greed_level(composite_index)
            
            # Obtener ajustes de trading
            trading_adjustments = self._get_trading_adjustments(classification)
            
            # Análisis histórico
            historical_context = self._get_historical_context(official_index)
            
            # Generar insights
            insights = self._generate_fear_greed_insights(
                composite_index, classification, components, historical_context
            )
            
            return {
                'official_index': official_index,
                'composite_index': composite_index,
                'classification': classification,
                'components': components,
                'trading_adjustments': trading_adjustments,
                'historical_context': historical_context,
                'insights': insights,
                'timestamp': datetime.now(),
                'symbol': symbol
            }
            
        except Exception as e:
            print(f"⚠️ Error en análisis Fear & Greed: {e}")
            return self._get_fallback_analysis(symbol)
    
    def _get_official_fear_greed_index(self) -> Dict:
        """Obtiene el índice oficial de Alternative.me"""
        
        try:
            # Verificar cache
            if self._is_cache_valid():
                return self.cache['fear_greed_data']
            
            # Obtener datos frescos
            url = f"{self.apis['fear_greed']['base_url']}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    latest = data['data'][0]
                    
                    official_data = {
                        'value': int(latest['value']),
                        'value_classification': latest['value_classification'],
                        'timestamp': latest['timestamp'],
                        'time_until_update': latest.get('time_until_update'),
                        'source': 'alternative.me'
                    }
                    
                    # Actualizar cache
                    self.cache['fear_greed_data'] = official_data
                    self.cache['last_update'] = datetime.now()
                    
                    return official_data
            
        except Exception as e:
            print(f"⚠️ Error obteniendo índice oficial: {e}")
        
        # Fallback a simulación
        return self._simulate_fear_greed_index()
    
    def _simulate_fear_greed_index(self) -> Dict:
        """Simula el índice Fear & Greed cuando la API no está disponible"""
        
        try:
            import yfinance as yf
            
            # Obtener datos de BTC para simular sentiment
            ticker = yf.Ticker("BTC-USD")
            data = ticker.history(period="30d")
            
            if len(data) >= 7:
                # Calcular factores de sentiment
                # 1. Price momentum (últimos 7 días)
                price_change_7d = (data['Close'].iloc[-1] / data['Close'].iloc[-7] - 1) * 100
                
                # 2. Volatilidad
                volatility = data['Close'].pct_change().tail(14).std() * 100
                
                # 3. Volume momentum
                recent_volume = data['Volume'].tail(3).mean()
                baseline_volume = data['Volume'].tail(14).mean()
                volume_ratio = recent_volume / baseline_volume if baseline_volume > 0 else 1
                
                # Combinar factores para simular F&G index
                # Base neutral = 50
                simulated_index = 50
                
                # Ajuste por momentum (+/- 30 puntos max)
                momentum_adjustment = max(-30, min(30, price_change_7d * 2))
                simulated_index += momentum_adjustment
                
                # Ajuste por volatilidad (volatilidad alta = más fear)
                if volatility > 5:  # 5% daily volatility
                    volatility_adjustment = -10
                elif volatility < 2:  # 2% daily volatility
                    volatility_adjustment = 5
                else:
                    volatility_adjustment = 0
                simulated_index += volatility_adjustment
                
                # Ajuste por volumen (alto volumen en caída = fear)
                if volume_ratio > 1.5 and price_change_7d < 0:
                    volume_adjustment = -10
                elif volume_ratio < 0.8:
                    volume_adjustment = -5  # Bajo volumen = apatía/fear
                else:
                    volume_adjustment = 0
                simulated_index += volume_adjustment
                
                # Clamp entre 0-100
                simulated_index = max(0, min(100, simulated_index))
                
                # Determinar clasificación
                classification = self._get_classification_by_value(simulated_index)
                
                return {
                    'value': int(simulated_index),
                    'value_classification': classification,
                    'timestamp': str(int(datetime.now().timestamp())),
                    'source': 'simulated',
                    'simulation_factors': {
                        'price_change_7d': price_change_7d,
                        'volatility': volatility,
                        'volume_ratio': volume_ratio
                    }
                }
            
        except Exception as e:
            print(f"Error en simulación: {e}")
        
        # Fallback final
        return {
            'value': 50,
            'value_classification': 'Neutral',
            'timestamp': str(int(datetime.now().timestamp())),
            'source': 'fallback'
        }
    
    def _get_classification_by_value(self, value: int) -> str:
        """Obtiene clasificación por valor numérico"""
        
        for classification, range_data in self.index_config['ranges'].items():
            if range_data['min'] <= value <= range_data['max']:
                return classification.replace('_', ' ').title()
        
        return 'Neutral'
    
    def _calculate_additional_components(self, symbol: str) -> Dict:
        """Calcula componentes adicionales del índice"""
        
        components = {}
        
        try:
            import yfinance as yf
            
            # Obtener datos de mercado
            ticker = yf.Ticker(f"{symbol}-USD")
            data = ticker.history(period="30d", interval="1d")
            
            if len(data) >= 14:
                # 1. Volatility Index
                components['volatility_index'] = self._calculate_volatility_index(data)
                
                # 2. Momentum Index
                components['momentum_index'] = self._calculate_momentum_index(data)
                
                # 3. Volume Index
                components['volume_index'] = self._calculate_volume_index(data)
                
                # 4. Dominance Index (para BTC)
                if symbol == 'BTC':
                    components['dominance_index'] = self._calculate_dominance_index()
            
        except Exception as e:
            print(f"Error calculando componentes: {e}")
            # Valores por defecto
            components = {
                'volatility_index': 50,
                'momentum_index': 50,
                'volume_index': 50,
                'dominance_index': 50
            }
        
        return components
    
    def _calculate_volatility_index(self, data: pd.DataFrame) -> float:
        """Calcula índice de volatilidad (0-100)"""
        
        # Volatilidad realizada (14 días)
        returns = data['Close'].pct_change().dropna()
        volatility = returns.tail(14).std() * np.sqrt(365) * 100  # Anualizada
        
        # Mapear volatilidad a escala 0-100
        # Alta volatilidad = fear (valores bajos)
        # Baja volatilidad = greed/complacencia (valores altos)
        
        # Thresholds típicos para crypto
        low_vol_threshold = 30    # 30% anual
        high_vol_threshold = 100  # 100% anual
        
        if volatility <= low_vol_threshold:
            vol_index = 80  # Baja volatilidad = greed
        elif volatility >= high_vol_threshold:
            vol_index = 20  # Alta volatilidad = fear
        else:
            # Interpolación lineal
            vol_index = 80 - ((volatility - low_vol_threshold) / (high_vol_threshold - low_vol_threshold)) * 60
        
        return max(0, min(100, vol_index))
    
    def _calculate_momentum_index(self, data: pd.DataFrame) -> float:
        """Calcula índice de momentum (0-100)"""
        
        # Múltiples timeframes de momentum
        momentum_1d = (data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100
        momentum_7d = (data['Close'].iloc[-1] / data['Close'].iloc[-8] - 1) * 100 if len(data) >= 8 else 0
        momentum_30d = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
        
        # Pesos para diferentes timeframes
        weighted_momentum = (momentum_1d * 0.2 + momentum_7d * 0.3 + momentum_30d * 0.5)
        
        # Mapear a escala 0-100
        # Momentum positivo fuerte = greed
        # Momentum negativo fuerte = fear
        
        if weighted_momentum >= 20:     # +20% = extreme greed
            momentum_index = 90
        elif weighted_momentum >= 10:  # +10% = greed
            momentum_index = 70
        elif weighted_momentum >= 0:   # Positivo = slight greed
            momentum_index = 60
        elif weighted_momentum >= -10: # -10% = slight fear
            momentum_index = 40
        elif weighted_momentum >= -20: # -20% = fear
            momentum_index = 25
        else:                          # < -20% = extreme fear
            momentum_index = 10
        
        return momentum_index
    
    def _calculate_volume_index(self, data: pd.DataFrame) -> float:
        """Calcula índice de volumen (0-100)"""
        
        # Volume moving averages
        current_volume = data['Volume'].iloc[-1]
        avg_volume_7d = data['Volume'].tail(7).mean()
        avg_volume_30d = data['Volume'].tail(30).mean()
        
        # Ratios de volumen
        volume_ratio_7d = current_volume / avg_volume_7d if avg_volume_7d > 0 else 1
        volume_ratio_30d = avg_volume_7d / avg_volume_30d if avg_volume_30d > 0 else 1
        
        # Correlación volumen-precio
        price_change = data['Close'].pct_change().tail(7)
        volume_change = data['Volume'].pct_change().tail(7)
        
        # Volumen alto en caída = fear (selling pressure)
        # Volumen alto en subida = greed (FOMO)
        # Volumen bajo = apatía/neutral
        
        base_index = 50
        
        # Ajuste por ratio de volumen actual
        if volume_ratio_7d >= 2.0:      # Volumen muy alto
            volume_adjustment = 20 if price_change.iloc[-1] > 0 else -20
        elif volume_ratio_7d >= 1.5:   # Volumen alto
            volume_adjustment = 10 if price_change.iloc[-1] > 0 else -10
        elif volume_ratio_7d <= 0.5:   # Volumen muy bajo
            volume_adjustment = -15     # Apatía = slight fear
        else:
            volume_adjustment = 0
        
        # Ajuste por tendencia de volumen
        if volume_ratio_30d >= 1.3:    # Volumen creciente
            trend_adjustment = 10
        elif volume_ratio_30d <= 0.7:  # Volumen decreciente
            trend_adjustment = -10
        else:
            trend_adjustment = 0
        
        volume_index = base_index + volume_adjustment + trend_adjustment
        return max(0, min(100, volume_index))
    
    def _calculate_dominance_index(self) -> float:
        """Calcula índice de dominancia de Bitcoin"""
        
        try:
            # Simular dominancia basada en datos históricos típicos
            # Dominancia alta = fear (safe haven)
            # Dominancia baja = greed (altseason)
            
            # Valores típicos: 40-70%
            # Simulación basada en tendencia reciente de BTC
            import yfinance as yf
            
            btc_data = yf.Ticker("BTC-USD").history(period="30d")
            eth_data = yf.Ticker("ETH-USD").history(period="30d")
            
            if len(btc_data) >= 7 and len(eth_data) >= 7:
                # Momentum relativo BTC vs ETH como proxy de dominancia
                btc_momentum = (btc_data['Close'].iloc[-1] / btc_data['Close'].iloc[-7] - 1)
                eth_momentum = (eth_data['Close'].iloc[-1] / eth_data['Close'].iloc[-7] - 1)
                
                relative_strength = btc_momentum - eth_momentum
                
                # Simular dominancia
                base_dominance = 55  # Base típica
                
                if relative_strength > 0.1:      # BTC outperforming = higher dominance
                    simulated_dominance = 65
                elif relative_strength > 0.05:
                    simulated_dominance = 60
                elif relative_strength < -0.1:   # ETH outperforming = lower dominance
                    simulated_dominance = 45
                elif relative_strength < -0.05:
                    simulated_dominance = 50
                else:
                    simulated_dominance = base_dominance
                
                # Mapear dominancia a fear/greed
                # Alta dominancia = fear (safe haven behavior)
                # Baja dominancia = greed (risk-on, altseason)
                
                if simulated_dominance >= 65:
                    dominance_index = 30    # High dominance = fear
                elif simulated_dominance >= 55:
                    dominance_index = 45    # Medium dominance = slight fear
                elif simulated_dominance >= 45:
                    dominance_index = 60    # Low dominance = slight greed
                else:
                    dominance_index = 75    # Very low dominance = greed
                
                return dominance_index
            
        except Exception as e:
            print(f"Error calculando dominancia: {e}")
        
        return 50  # Neutral default
    
    def _calculate_composite_index(self, official_index: Dict, components: Dict) -> float:
        """Calcula índice compuesto"""
        
        total_score = 0
        total_weight = 0
        
        # Índice oficial
        if self.index_config['components']['official_fg_index']['enabled']:
            weight = self.index_config['components']['official_fg_index']['weight']
            total_score += official_index['value'] * weight
            total_weight += weight
        
        # Componentes adicionales
        for component_name, component_config in self.index_config['components'].items():
            if component_name != 'official_fg_index' and component_config['enabled']:
                component_key = component_name.replace('_index', '_index')
                if component_key in components:
                    weight = component_config['weight']
                    total_score += components[component_key] * weight
                    total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else official_index['value']
    
    def _classify_fear_greed_level(self, index_value: float) -> str:
        """Clasifica el nivel de fear/greed"""
        
        for level, range_data in self.index_config['ranges'].items():
            if range_data['min'] <= index_value <= range_data['max']:
                return level
        
        return 'neutral'
    
    def _get_trading_adjustments(self, classification: str) -> Dict:
        """Obtiene ajustes de trading basados en clasificación"""
        
        return self.index_config['trading_adjustments'].get(classification, 
                                                           self.index_config['trading_adjustments']['neutral'])
    
    def _get_historical_context(self, official_index: Dict) -> Dict:
        """Obtiene contexto histórico del índice"""
        
        # Simulación de contexto histórico
        current_value = official_index['value']
        
        # Estadísticas típicas del F&G index
        historical_stats = {
            'average': 47,      # Promedio histórico
            'min': 6,           # Mínimo histórico
            'max': 95,          # Máximo histórico
            'fear_threshold': 25,
            'greed_threshold': 75
        }
        
        # Percentil actual
        percentile = (current_value - historical_stats['min']) / (historical_stats['max'] - historical_stats['min']) * 100
        
        # Contexto
        if current_value <= historical_stats['fear_threshold']:
            context = "EXTREME_FEAR_TERRITORY"
            opportunity_level = "HIGH"
        elif current_value <= 40:
            context = "FEAR_TERRITORY"
            opportunity_level = "MEDIUM"
        elif current_value <= 60:
            context = "NEUTRAL_TERRITORY"
            opportunity_level = "LOW"
        elif current_value <= historical_stats['greed_threshold']:
            context = "GREED_TERRITORY"
            opportunity_level = "CAUTION"
        else:
            context = "EXTREME_GREED_TERRITORY"
            opportunity_level = "HIGH_RISK"
        
        return {
            'current_percentile': percentile,
            'historical_average': historical_stats['average'],
            'distance_from_average': current_value - historical_stats['average'],
            'context': context,
            'opportunity_level': opportunity_level,
            'days_since_extreme_fear': 30,  # Simulado
            'days_since_extreme_greed': 45  # Simulado
        }
    
    def _generate_fear_greed_insights(self, composite_index: float, classification: str, 
                                     components: Dict, historical_context: Dict) -> Dict:
        """Genera insights del análisis"""
        
        insights = {
            'market_sentiment': self._get_sentiment_description(composite_index),
            'trading_opportunities': [],
            'risk_factors': [],
            'timing_analysis': {},
            'component_analysis': {}
        }
        
        # Oportunidades de trading
        if classification in ['extreme_fear', 'fear']:
            insights['trading_opportunities'].extend([
                "Consider increasing DCA amounts",
                "Look for high-quality dips to buy",
                "Consider longer time horizons for entries"
            ])
        elif classification in ['extreme_greed', 'greed']:
            insights['trading_opportunities'].extend([
                "Consider taking profits on existing positions",
                "Be more selective with new entries",
                "Consider reducing position sizes"
            ])
        
        # Factores de riesgo
        if classification == 'extreme_greed':
            insights['risk_factors'].extend([
                "Market may be overextended",
                "Higher probability of correction",
                "Elevated volatility risk"
            ])
        elif classification == 'extreme_fear':
            insights['risk_factors'].extend([
                "Potential for further downside",
                "Lower liquidity conditions",
                "Margin call cascades possible"
            ])
        
        # Análisis de timing
        insights['timing_analysis'] = {
            'short_term': self._get_timing_analysis(composite_index, 'short'),
            'medium_term': self._get_timing_analysis(composite_index, 'medium'),
            'long_term': self._get_timing_analysis(composite_index, 'long')
        }
        
        # Análisis de componentes
        for component, value in components.items():
            insights['component_analysis'][component] = {
                'value': value,
                'interpretation': self._interpret_component(component, value)
            }
        
        return insights
    
    def _get_sentiment_description(self, index_value: float) -> str:
        """Obtiene descripción del sentiment"""
        
        if index_value <= 25:
            return "Market in extreme fear - potential buying opportunity"
        elif index_value <= 45:
            return "Market showing fear - cautious optimism warranted"
        elif index_value <= 55:
            return "Market sentiment neutral - no clear directional bias"
        elif index_value <= 75:
            return "Market showing greed - exercise caution"
        else:
            return "Market in extreme greed - high risk of correction"
    
    def _get_timing_analysis(self, index_value: float, timeframe: str) -> str:
        """Obtiene análisis de timing"""
        
        if timeframe == 'short':
            if index_value <= 25:
                return "Excellent short-term buying opportunity"
            elif index_value >= 75:
                return "Consider short-term profit taking"
            else:
                return "Neutral short-term outlook"
        
        elif timeframe == 'medium':
            if index_value <= 35:
                return "Strong medium-term accumulation period"
            elif index_value >= 65:
                return "Medium-term distribution may be prudent"
            else:
                return "Neutral medium-term outlook"
        
        else:  # long-term
            if index_value <= 40:
                return "Excellent long-term entry conditions"
            elif index_value >= 70:
                return "Long-term holders might consider partial profit taking"
            else:
                return "Neutral long-term outlook"
    
    def _interpret_component(self, component: str, value: float) -> str:
        """Interpreta valor de componente individual"""
        
        if 'volatility' in component:
            if value <= 30:
                return "High volatility indicates fear"
            elif value >= 70:
                return "Low volatility suggests complacency"
            else:
                return "Normal volatility levels"
        
        elif 'momentum' in component:
            if value <= 30:
                return "Negative momentum driving fear"
            elif value >= 70:
                return "Strong momentum fueling greed"
            else:
                return "Neutral momentum"
        
        elif 'volume' in component:
            if value <= 30:
                return "Volume patterns suggest fear/selling"
            elif value >= 70:
                return "Volume patterns suggest greed/FOMO"
            else:
                return "Normal volume patterns"
        
        elif 'dominance' in component:
            if value <= 30:
                return "High BTC dominance indicates flight to safety"
            elif value >= 70:
                return "Low BTC dominance suggests risk-on behavior"
            else:
                return "Normal BTC dominance levels"
        
        return "Neutral reading"
    
    def _is_cache_valid(self) -> bool:
        """Verifica si el cache es válido"""
        
        if not self.cache.get('last_update') or not self.cache.get('fear_greed_data'):
            return False
        
        time_since_update = datetime.now() - self.cache['last_update']
        return time_since_update.total_seconds() < self.cache['cache_duration']
    
    def _get_fallback_analysis(self, symbol: str) -> Dict:
        """Análisis de fallback cuando hay errores"""
        
        return {
            'official_index': {'value': 50, 'value_classification': 'Neutral', 'source': 'fallback'},
            'composite_index': 50,
            'classification': 'neutral',
            'components': {'volatility_index': 50, 'momentum_index': 50, 'volume_index': 50, 'dominance_index': 50},
            'trading_adjustments': self.index_config['trading_adjustments']['neutral'],
            'historical_context': {'context': 'NEUTRAL_TERRITORY', 'opportunity_level': 'UNKNOWN'},
            'insights': {
                'market_sentiment': 'Unable to determine sentiment',
                'trading_opportunities': ['Use normal trading strategy'],
                'risk_factors': ['Data unavailable - exercise caution']
            },
            'timestamp': datetime.now(),
            'symbol': symbol,
            'source': 'fallback'
        }
    
    def get_trading_signal_adjustment(self, base_score: float, base_position_size: float) -> Dict:
        """Ajusta señal de trading basada en Fear & Greed"""
        
        fg_analysis = self.get_fear_greed_analysis()
        classification = fg_analysis['classification']
        adjustments = fg_analysis['trading_adjustments']
        
        # Aplicar ajustes
        adjusted_score = base_score * adjustments['entry_aggressiveness']
        adjusted_position = base_position_size * adjustments['position_multiplier']
        
        return {
            'original_score': base_score,
            'adjusted_score': adjusted_score,
            'original_position_size': base_position_size,
            'adjusted_position_size': adjusted_position,
            'fear_greed_index': fg_analysis['composite_index'],
            'classification': classification,
            'adjustment_reason': f"Fear & Greed: {classification}",
            'fg_analysis': fg_analysis
        }
    
    def print_fear_greed_analysis(self, symbol: str = 'BTC'):
        """Imprime análisis detallado del Fear & Greed Index"""
        
        print(f"😨😎 FEAR & GREED INDEX ANALYSIS - {symbol}")
        print("="*70)
        
        analysis = self.get_fear_greed_analysis(symbol)
        
        # Índices principales
        official_value = analysis['official_index']['value']
        composite_value = analysis['composite_index']
        classification = analysis['classification'].replace('_', ' ').upper()
        
        print(f"📊 ÍNDICE OFICIAL: {official_value}")
        print(f"📈 ÍNDICE COMPUESTO: {composite_value:.1f}")
        print(f"🎯 CLASIFICACIÓN: {classification}")
        print(f"📅 Timestamp: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Componentes
        print(f"\n📋 COMPONENTES DEL ÍNDICE:")
        components = analysis['components']
        for component, value in components.items():
            if isinstance(value, (int, float)):
                status = "🟢" if value >= 60 else "🟡" if value >= 40 else "🔴"
                print(f"• {component.replace('_', ' ').title()}: {value:.1f} {status}")
        
        # Contexto histórico
        historical = analysis['historical_context']
        print(f"\n📚 CONTEXTO HISTÓRICO:")
        print(f"• Percentil actual: {historical['current_percentile']:.1f}%")
        print(f"• Distancia del promedio: {historical['distance_from_average']:+.1f}")
        print(f"• Contexto: {historical['context']}")
        print(f"• Nivel de oportunidad: {historical['opportunity_level']}")
        
        # Ajustes de trading
        adjustments = analysis['trading_adjustments']
        print(f"\n⚙️ AJUSTES DE TRADING:")
        print(f"• Multiplicador de posición: {adjustments['position_multiplier']:.2f}x")
        print(f"• Agresividad de entrada: {adjustments['entry_aggressiveness']:.2f}x")
        print(f"• Multiplicador de stops: {adjustments['stop_multiplier']:.2f}x")
        
        # Insights principales
        insights = analysis['insights']
        print(f"\n💡 INSIGHTS:")
        print(f"📊 {insights['market_sentiment']}")
        
        if insights['trading_opportunities']:
            print(f"\n🎯 OPORTUNIDADES:")
            for opportunity in insights['trading_opportunities']:
                print(f"• {opportunity}")
        
        if insights['risk_factors']:
            print(f"\n⚠️ FACTORES DE RIESGO:")
            for risk in insights['risk_factors']:
                print(f"• {risk}")
        
        # Análisis de timing
        timing = insights['timing_analysis']
        print(f"\n⏰ ANÁLISIS DE TIMING:")
        print(f"• Corto plazo: {timing['short_term']}")
        print(f"• Mediano plazo: {timing['medium_term']}")
        print(f"• Largo plazo: {timing['long_term']}")
        
        return analysis

def demo_fear_greed_analysis():
    """Demo del análisis Fear & Greed"""
    
    fg_analyzer = FearGreedIndexAnalyzer()
    
    print("😨😎 FEAR & GREED INDEX DEMO")
    print("="*70)
    print("Nota: Usando simulación inteligente cuando APIs no están disponibles")
    print("="*70)
    
    # Análisis principal
    analysis = fg_analyzer.print_fear_greed_analysis('BTC')
    
    print("\n" + "="*70)
    
    # Test de ajustes de trading
    print("🎯 TESTING AJUSTES DE TRADING:")
    
    base_score = 7.2
    base_position = 1000
    
    adjustment = fg_analyzer.get_trading_signal_adjustment(base_score, base_position)
    
    print(f"• Score base: {adjustment['original_score']}")
    print(f"• Score ajustado: {adjustment['adjusted_score']:.2f}")
    print(f"• Posición base: ${adjustment['original_position_size']:,}")
    print(f"• Posición ajustada: ${adjustment['adjusted_position_size']:,.0f}")
    print(f"• Razón: {adjustment['adjustment_reason']}")
    
    return fg_analyzer

if __name__ == "__main__":
    demo_fear_greed_analysis()