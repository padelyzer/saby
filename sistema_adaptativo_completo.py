#!/usr/bin/env python3
"""
Sistema de Trading Adaptativo Completo
Integra régimen de mercado + sentiment + configuraciones dinámicas
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from market_regime_detector import MarketRegimeDetector
from twitter_sentiment_scraper import TwitterSentimentScraper
from scoring_empirico_v2 import ScoringEmpiricoV2

class SistemaAdaptativoCompleto:
    """
    Sistema de trading que se adapta automáticamente a:
    1. Régimen de mercado (Bullish, Bearish, Lateral, Altseason)
    2. Sentiment de Twitter/X
    3. Configuraciones dinámicas por condición
    """
    
    def __init__(self):
        # Inicializar componentes
        self.market_detector = MarketRegimeDetector()
        self.sentiment_scraper = TwitterSentimentScraper()
        self.base_scoring = ScoringEmpiricoV2()
        
        # Estado actual del sistema
        self.current_regime = None
        self.current_sentiment = {}
        self.adaptive_config = {}
        self.last_regime_update = None
        self.last_sentiment_update = {}
        
        # Configuraciones adaptativas avanzadas
        self.regime_multipliers = {
            'BULLISH': {
                'leverage_multiplier': 1.2,
                'score_threshold_adjustment': -0.5,
                'volume_importance': 1.3,
                'momentum_importance': 1.4,
                'risk_tolerance': 1.1
            },
            'ALTSEASON': {
                'leverage_multiplier': 1.5,
                'score_threshold_adjustment': -1.0,
                'volume_importance': 1.5,
                'momentum_importance': 1.6,
                'risk_tolerance': 1.3,
                'altcoin_bonus': 1.2
            },
            'LATERAL': {
                'leverage_multiplier': 0.8,
                'score_threshold_adjustment': +1.0,
                'volume_importance': 0.7,
                'momentum_importance': 0.6,
                'risk_tolerance': 0.8,
                'range_trading_bonus': 1.1
            },
            'BEARISH': {
                'leverage_multiplier': 0.6,
                'score_threshold_adjustment': +2.0,
                'volume_importance': 0.5,
                'momentum_importance': 0.4,
                'risk_tolerance': 0.5,
                'short_preference': 1.3
            }
        }
        
        # Configuración de sentiment
        self.sentiment_weights = {
            'MUY_BULLISH': 1.3,
            'BULLISH': 1.1,
            'NEUTRAL': 1.0,
            'BEARISH': 0.9,
            'MUY_BEARISH': 0.7
        }
    
    def update_market_conditions(self, symbol='BTC'):
        """Actualiza condiciones de mercado y sentiment"""
        
        # Actualizar régimen de mercado (cada 4 horas)
        if self._should_update_regime():
            print(f"🔄 Actualizando análisis de régimen de mercado...")
            regime_analysis = self.market_detector.detect_current_regime()
            self.current_regime = regime_analysis
            self.last_regime_update = datetime.now()
            
            print(f"📊 Régimen detectado: {regime_analysis['regime']} ({regime_analysis['confidence']:.1%})")
        
        # Actualizar sentiment (cada 30 minutos)
        if self._should_update_sentiment(symbol):
            print(f"🐦 Actualizando sentiment para {symbol}...")
            sentiment_data = self.sentiment_scraper.get_sentiment_score_for_trading(symbol)
            self.current_sentiment[symbol] = sentiment_data
            self.last_sentiment_update[symbol] = datetime.now()
            
            print(f"💭 Sentiment {symbol}: {sentiment_data['category']} (Score: {sentiment_data['trading_score']:.3f})")
        
        # Generar configuración adaptativa
        self._generate_adaptive_config(symbol)
    
    def calculate_adaptive_score(self, df, current, prev, symbol, signal_type='LONG'):
        """Calcula score adaptativo considerando régimen + sentiment"""
        
        # Asegurar que tenemos condiciones actualizadas
        self.update_market_conditions(symbol)
        
        # Obtener score base del sistema empírico
        if signal_type == 'LONG':
            base_score, base_details = self.base_scoring.calculate_empirical_score_long(df, current, prev)
        else:
            base_score, base_details = self.base_scoring.calculate_empirical_score_short(df, current, prev)
        
        # Aplicar adaptaciones
        adapted_score = self._apply_regime_adaptations(base_score, base_details, signal_type)
        adapted_score = self._apply_sentiment_adaptations(adapted_score, symbol, signal_type)
        adapted_score = self._apply_symbol_specific_adaptations(adapted_score, symbol, signal_type)
        
        # Limitar score final
        final_score = max(0, min(adapted_score, 10.0))
        
        # Generar detalles extendidos
        extended_details = base_details.copy()
        extended_details.update({
            'regime_info': self.current_regime,
            'sentiment_info': self.current_sentiment.get(symbol, {}),
            'adaptive_config': self.adaptive_config,
            'base_score': base_score,
            'final_adapted_score': final_score,
            'regime_adjustment': adapted_score - base_score,
            'sentiment_category': self.current_sentiment.get(symbol, {}).get('category', 'NEUTRAL')
        })
        
        return final_score, extended_details
    
    def _apply_regime_adaptations(self, score, details, signal_type):
        """Aplica adaptaciones basadas en régimen de mercado"""
        
        if not self.current_regime:
            return score
        
        regime = self.current_regime['regime']
        multipliers = self.regime_multipliers.get(regime, {})
        
        adapted_score = score
        
        # Ajuste por tolerancia al riesgo del régimen
        risk_tolerance = multipliers.get('risk_tolerance', 1.0)
        adapted_score *= risk_tolerance
        
        # Ajuste específico por tipo de mercado
        if regime == 'ALTSEASON' and signal_type == 'LONG':
            # En altseason, favorecer longs
            adapted_score *= multipliers.get('altcoin_bonus', 1.0)
        
        elif regime == 'BEARISH':
            if signal_type == 'SHORT':
                # En bear market, favorecer shorts
                adapted_score *= multipliers.get('short_preference', 1.0)
            else:
                # Penalizar longs en bear market
                adapted_score *= 0.8
        
        elif regime == 'LATERAL':
            # En mercado lateral, ajustar por posición en rango
            if 'range_trading_bonus' in multipliers:
                # Verificar si estamos cerca de soportes/resistencias
                range_bonus = self._calculate_range_position_bonus(details)
                adapted_score *= (1 + range_bonus * 0.1)
        
        # Ajuste por confianza en el régimen
        regime_confidence = self.current_regime.get('confidence', 0.5)
        confidence_factor = 0.5 + (regime_confidence * 0.5)  # 0.5 a 1.0
        
        return adapted_score * confidence_factor
    
    def _apply_sentiment_adaptations(self, score, symbol, signal_type):
        """Aplica adaptaciones basadas en sentiment"""
        
        sentiment_data = self.current_sentiment.get(symbol)
        if not sentiment_data:
            return score
        
        sentiment_category = sentiment_data['category']
        sentiment_score = sentiment_data['trading_score']  # 0-1
        confidence = sentiment_data['confidence']
        
        # Obtener peso del sentiment
        sentiment_weight = self.sentiment_weights.get(sentiment_category, 1.0)
        
        # Aplicar sentiment según tipo de señal
        if signal_type == 'LONG':
            if sentiment_category in ['MUY_BULLISH', 'BULLISH']:
                # Sentiment positivo favorece longs
                sentiment_adjustment = sentiment_weight
            elif sentiment_category in ['MUY_BEARISH', 'BEARISH']:
                # Sentiment negativo perjudica longs
                sentiment_adjustment = sentiment_weight
            else:
                sentiment_adjustment = 1.0
        else:  # SHORT
            if sentiment_category in ['MUY_BEARISH', 'BEARISH']:
                # Sentiment negativo favorece shorts
                sentiment_adjustment = 2.0 - sentiment_weight  # Invertir para shorts
            elif sentiment_category in ['MUY_BULLISH', 'BULLISH']:
                # Sentiment positivo perjudica shorts
                sentiment_adjustment = 2.0 - sentiment_weight
            else:
                sentiment_adjustment = 1.0
        
        # Modular por confianza del sentiment
        confidence_modulated_adjustment = 1.0 + (sentiment_adjustment - 1.0) * confidence
        
        return score * confidence_modulated_adjustment
    
    def _apply_symbol_specific_adaptations(self, score, symbol, signal_type):
        """Aplica adaptaciones específicas por símbolo"""
        
        # Adaptaciones para altcoins en diferentes regímenes
        if symbol != 'BTC' and self.current_regime:
            regime = self.current_regime['regime']
            
            if regime == 'ALTSEASON':
                # Bonus significativo para altcoins en altseason
                score *= 1.2
            elif regime == 'BEARISH':
                # Penalización para altcoins en bear market
                score *= 0.8
            elif regime == 'LATERAL':
                # Neutral para altcoins en lateral
                score *= 0.95
        
        # Adaptaciones específicas por volatilidad del símbolo
        volatility_bonus = self._calculate_volatility_bonus(symbol)
        score *= volatility_bonus
        
        return score
    
    def _calculate_range_position_bonus(self, details):
        """Calcula bonus por posición en rango para mercado lateral"""
        
        # Simplificado - en producción usar análisis más sofisticado
        try:
            rsi = details.get('rsi_component', 0)
            if rsi > 2.0:  # RSI muy oversold
                return 0.3  # Bonus por estar cerca del soporte
            elif rsi < -2.0:  # RSI muy overbought
                return 0.3  # Bonus por estar cerca de resistencia
            else:
                return 0.0
        except:
            return 0.0
    
    def _calculate_volatility_bonus(self, symbol):
        """Calcula bonus por volatilidad específica del símbolo"""
        
        # Volatilidades típicas (se pueden actualizar dinámicamente)
        volatility_factors = {
            'BTC': 1.0,   # Baseline
            'ETH': 1.05,  # Ligeramente más volátil
            'SOL': 1.15,  # Más volátil
            'BNB': 1.08,
            'XRP': 1.12,
            'ADA': 1.10,
            'DOT': 1.13,
            'MATIC': 1.18,
            'AVAX': 1.16,
            'LINK': 1.14
        }
        
        return volatility_factors.get(symbol, 1.1)  # Default para altcoins
    
    def get_adaptive_leverage(self, score, symbol):
        """Calcula leverage adaptativo"""
        
        # Leverage base del sistema empírico
        base_leverage = self.base_scoring.get_leverage_empirical(score)
        
        # Aplicar multiplicador de régimen
        if self.current_regime:
            regime = self.current_regime['regime']
            regime_multiplier = self.regime_multipliers.get(regime, {}).get('leverage_multiplier', 1.0)
            adapted_leverage = base_leverage * regime_multiplier
        else:
            adapted_leverage = base_leverage
        
        # Aplicar ajuste por sentiment
        sentiment_data = self.current_sentiment.get(symbol)
        if sentiment_data:
            sentiment_category = sentiment_data['category']
            if sentiment_category == 'MUY_BULLISH':
                adapted_leverage *= 1.1
            elif sentiment_category == 'MUY_BEARISH':
                adapted_leverage *= 0.8
        
        # Limitar leverage según configuración
        max_leverage = self.adaptive_config.get('max_leverage', 5)
        final_leverage = max(1, min(int(adapted_leverage), max_leverage))
        
        return final_leverage
    
    def get_adaptive_threshold(self, symbol):
        """Obtiene threshold mínimo adaptativo"""
        
        base_threshold = 6.0  # Threshold base del sistema empírico
        
        # Ajuste por régimen
        if self.current_regime:
            regime = self.current_regime['regime']
            regime_adjustment = self.regime_multipliers.get(regime, {}).get('score_threshold_adjustment', 0)
            adapted_threshold = base_threshold + regime_adjustment
        else:
            adapted_threshold = base_threshold
        
        # Ajuste por sentiment
        sentiment_data = self.current_sentiment.get(symbol)
        if sentiment_data:
            sentiment_category = sentiment_data['category']
            if sentiment_category == 'MUY_BULLISH':
                adapted_threshold -= 0.5  # Más permisivo en sentiment muy bullish
            elif sentiment_category == 'MUY_BEARISH':
                adapted_threshold += 1.0  # Más restrictivo en sentiment bearish
        
        return max(4.0, min(adapted_threshold, 8.0))  # Límites razonables
    
    def _should_update_regime(self):
        """Verifica si necesitamos actualizar el régimen"""
        if not self.last_regime_update:
            return True
        
        hours_since_update = (datetime.now() - self.last_regime_update).total_seconds() / 3600
        return hours_since_update >= 4  # Actualizar cada 4 horas
    
    def _should_update_sentiment(self, symbol):
        """Verifica si necesitamos actualizar el sentiment"""
        if symbol not in self.last_sentiment_update:
            return True
        
        minutes_since_update = (datetime.now() - self.last_sentiment_update[symbol]).total_seconds() / 60
        return minutes_since_update >= 30  # Actualizar cada 30 minutos
    
    def _generate_adaptive_config(self, symbol):
        """Genera configuración adaptativa actual"""
        
        config = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'regime': self.current_regime['regime'] if self.current_regime else 'UNKNOWN',
            'regime_confidence': self.current_regime['confidence'] if self.current_regime else 0.5,
            'sentiment_category': self.current_sentiment.get(symbol, {}).get('category', 'NEUTRAL'),
            'sentiment_score': self.current_sentiment.get(symbol, {}).get('trading_score', 0.5),
            'adaptive_threshold': self.get_adaptive_threshold(symbol),
            'max_leverage': self.regime_multipliers.get(self.current_regime['regime'] if self.current_regime else 'LATERAL', {}).get('leverage_multiplier', 1.0) * 5
        }
        
        self.adaptive_config = config
        return config
    
    def print_adaptive_status(self, symbol='BTC'):
        """Imprime estado actual del sistema adaptativo"""
        
        print(f"🚀 SISTEMA ADAPTATIVO - STATUS ACTUAL")
        print("="*60)
        
        # Régimen de mercado
        if self.current_regime:
            regime = self.current_regime
            print(f"📊 RÉGIMEN DE MERCADO:")
            print(f"• Tipo: {regime['regime']}")
            print(f"• Confianza: {regime['confidence']:.1%}")
            print(f"• Descripción: {regime['description']}")
        
        # Sentiment
        sentiment_data = self.current_sentiment.get(symbol)
        if sentiment_data:
            print(f"\\n💭 SENTIMENT {symbol}:")
            print(f"• Categoría: {sentiment_data['category']}")
            print(f"• Score: {sentiment_data['trading_score']:.3f}")
            print(f"• Confianza: {sentiment_data['confidence']:.1%}")
            print(f"• Keywords: {', '.join(sentiment_data['trending_keywords'])}")
        
        # Configuración adaptativa
        if self.adaptive_config:
            config = self.adaptive_config
            print(f"\\n⚙️ CONFIGURACIÓN ADAPTATIVA:")
            print(f"• Threshold mínimo: {config['adaptive_threshold']:.1f}")
            print(f"• Leverage máximo: {config['max_leverage']:.0f}x")
            print(f"• Última actualización: {config['timestamp'].strftime('%H:%M:%S')}")
        
        print("="*60)

def demo_sistema_adaptativo():
    """Demo del sistema adaptativo completo"""
    
    sistema = SistemaAdaptativoCompleto()
    
    print("🌟 SISTEMA DE TRADING ADAPTATIVO COMPLETO")
    print("="*70)
    print("Características:")
    print("• Detección automática de régimen de mercado")
    print("• Análisis de sentiment en tiempo real")
    print("• Configuraciones dinámicas por condición")
    print("• Leverage y thresholds adaptativos")
    print("• Optimización específica para altseason")
    print("="*70)
    
    # Demostrar para diferentes símbolos
    symbols = ['BTC', 'ETH', 'SOL']
    
    for symbol in symbols:
        print(f"\\n🔍 ANÁLISIS PARA {symbol}:")
        print("-" * 40)
        
        # Actualizar condiciones
        sistema.update_market_conditions(symbol)
        
        # Mostrar configuración
        threshold = sistema.get_adaptive_threshold(symbol)
        print(f"• Threshold adaptativo: {threshold:.1f}")
        
        # Simular score y leverage
        sample_score = 7.2
        leverage = sistema.get_adaptive_leverage(sample_score, symbol)
        print(f"• Leverage para score {sample_score}: {leverage}x")
    
    print(f"\\n📋 STATUS DETALLADO:")
    sistema.print_adaptive_status('BTC')
    
    return sistema

if __name__ == "__main__":
    demo_sistema_adaptativo()