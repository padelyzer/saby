#!/usr/bin/env python3
"""
Market Regime Detector
Detecta automáticamente el régimen de mercado (Lateral, Bearish, Bullish, Altseason)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class MarketRegimeDetector:
    """
    Detector automático de régimen de mercado
    """
    
    def __init__(self):
        self.regimes = {
            'BULLISH': {
                'description': 'Mercado alcista fuerte',
                'characteristics': ['Tendencia alcista sostenida', 'Volumen creciente', 'RSI > 50'],
                'optimal_leverage': (3, 5),
                'risk_tolerance': 'MODERADO'
            },
            'ALTSEASON': {
                'description': 'Temporada de altcoins',
                'characteristics': ['BTC dominance bajando', 'Altcoins outperforming BTC', 'Alto volumen en alts'],
                'optimal_leverage': (5, 8),
                'risk_tolerance': 'ALTO'
            },
            'LATERAL': {
                'description': 'Mercado lateral/consolidación',
                'characteristics': ['Precio en rango', 'Volatilidad moderada', 'Volumen bajo'],
                'optimal_leverage': (2, 3),
                'risk_tolerance': 'BAJO'
            },
            'BEARISH': {
                'description': 'Mercado bajista',
                'characteristics': ['Tendencia bajista', 'Volumen en ventas', 'RSI < 50'],
                'optimal_leverage': (1, 2),
                'risk_tolerance': 'MUY_BAJO'
            }
        }
        
        # Configuraciones específicas por régimen
        self.regime_configs = {
            'BULLISH': {
                'rsi_bullish_threshold': 45,  # Más agresivo en bull market
                'volume_weight': 0.15,        # Volumen más importante
                'momentum_weight': 0.20,      # Momentum crucial
                'min_score_threshold': 5.5,   # Threshold más bajo
                'max_leverage': 5
            },
            'ALTSEASON': {
                'rsi_bullish_threshold': 40,  # Muy agresivo
                'volume_weight': 0.25,        # Volumen crítico
                'momentum_weight': 0.25,      # Momentum máximo
                'min_score_threshold': 5.0,   # Threshold muy bajo
                'max_leverage': 8,
                'alt_multiplier': 1.3         # Bonus para altcoins
            },
            'LATERAL': {
                'rsi_bullish_threshold': 35,  # Más conservador
                'volume_weight': 0.05,        # Volumen menos relevante
                'momentum_weight': 0.10,      # Momentum reducido
                'min_score_threshold': 6.5,   # Threshold alto
                'max_leverage': 3,
                'range_bonus': True           # Bonus por trading en rango
            },
            'BEARISH': {
                'rsi_bullish_threshold': 25,  # Muy conservador
                'volume_weight': 0.05,        # Volumen irrelevante
                'momentum_weight': 0.05,      # Momentum irrelevante
                'min_score_threshold': 7.5,   # Threshold muy alto
                'max_leverage': 2,
                'short_bias': True            # Preferencia por shorts
            }
        }
    
    def detect_current_regime(self, btc_data=None, alt_data=None):
        """Detecta el régimen actual del mercado"""
        
        if btc_data is None:
            btc_data = self._fetch_btc_data()
        
        if alt_data is None:
            alt_data = self._fetch_alt_data()
        
        # Análisis multifactorial
        regime_scores = {
            'BULLISH': 0,
            'ALTSEASON': 0,
            'LATERAL': 0,
            'BEARISH': 0
        }
        
        # 1. Análisis de tendencia BTC (40% del score)
        btc_trend = self._analyze_btc_trend(btc_data)
        regime_scores.update(btc_trend)
        
        # 2. Análisis de dominancia BTC (30% del score)
        dominance_analysis = self._analyze_btc_dominance()
        for regime in regime_scores:
            regime_scores[regime] += dominance_analysis.get(regime, 0) * 0.3
        
        # 3. Análisis de performance altcoins (20% del score)
        alt_performance = self._analyze_alt_performance(alt_data)
        for regime in regime_scores:
            regime_scores[regime] += alt_performance.get(regime, 0) * 0.2
        
        # 4. Análisis de volatilidad (10% del score)
        volatility_analysis = self._analyze_volatility(btc_data)
        for regime in regime_scores:
            regime_scores[regime] += volatility_analysis.get(regime, 0) * 0.1
        
        # Determinar régimen dominante
        current_regime = max(regime_scores, key=regime_scores.get)
        confidence = regime_scores[current_regime]
        
        return {
            'regime': current_regime,
            'confidence': confidence,
            'scores': regime_scores,
            'description': self.regimes[current_regime]['description'],
            'config': self.regime_configs[current_regime]
        }
    
    def _fetch_btc_data(self, days=30):
        """Obtiene datos de BTC"""
        try:
            btc = yf.download('BTC-USD', period=f'{days}d', interval='1d')
            return btc
        except Exception as e:
            print(f"Error obteniendo datos BTC: {e}")
            return None
    
    def _fetch_alt_data(self, days=30):
        """Obtiene datos de principales altcoins"""
        alts = ['ETH-USD', 'SOL-USD', 'ADA-USD', 'DOT-USD', 'MATIC-USD']
        alt_data = {}
        
        for alt in alts:
            try:
                data = yf.download(alt, period=f'{days}d', interval='1d')
                if len(data) > 0:
                    alt_data[alt] = data
            except:
                continue
        
        return alt_data
    
    def _analyze_btc_trend(self, btc_data):
        """Analiza la tendencia de BTC"""
        if btc_data is None or len(btc_data) < 20:
            return {'LATERAL': 0.4, 'BULLISH': 0.2, 'BEARISH': 0.2, 'ALTSEASON': 0.2}
        
        # Calcular EMAs
        btc_data['EMA_20'] = btc_data['Close'].ewm(span=20).mean()
        btc_data['EMA_50'] = btc_data['Close'].ewm(span=50).mean()
        
        current_price = float(btc_data['Close'].iloc[-1])
        ema_20 = float(btc_data['EMA_20'].iloc[-1])
        ema_50 = float(btc_data['EMA_50'].iloc[-1])
        
        # Cambio de precio en diferentes períodos
        price_change_7d = (current_price - float(btc_data['Close'].iloc[-7])) / float(btc_data['Close'].iloc[-7])
        price_change_30d = (current_price - float(btc_data['Close'].iloc[-30])) / float(btc_data['Close'].iloc[-30]) if len(btc_data) >= 30 else 0
        
        scores = {'BULLISH': 0, 'ALTSEASON': 0, 'LATERAL': 0, 'BEARISH': 0}
        
        # Análisis de tendencia
        if current_price > ema_20 > ema_50:
            if price_change_7d > 0.1:  # +10% en 7 días
                scores['BULLISH'] += 0.6
                scores['ALTSEASON'] += 0.4  # Bull market puede llevar a altseason
            else:
                scores['BULLISH'] += 0.4
                scores['ALTSEASON'] += 0.3
        elif current_price < ema_20 < ema_50:
            if price_change_7d < -0.1:  # -10% en 7 días
                scores['BEARISH'] += 0.6
            else:
                scores['BEARISH'] += 0.4
                scores['LATERAL'] += 0.2
        else:
            scores['LATERAL'] += 0.4
            scores['ALTSEASON'] += 0.2  # Consolidación BTC puede beneficiar alts
        
        # Análisis de volatilidad
        volatility = float(btc_data['Close'].pct_change().std() * np.sqrt(365))
        if volatility > 0.8:  # Alta volatilidad
            scores['BULLISH'] += 0.1 if price_change_7d > 0 else 0
            scores['BEARISH'] += 0.1 if price_change_7d < 0 else 0
            scores['ALTSEASON'] += 0.1
        else:  # Baja volatilidad
            scores['LATERAL'] += 0.2
        
        return scores
    
    def _analyze_btc_dominance(self):
        """Analiza la dominancia de BTC (simulado - en producción usar datos reales)"""
        # Por ahora simulamos - en producción obtener de CoinGecko API
        # Dominancia BTC actual aprox 50-55%
        
        # Simulación basada en patrones conocidos
        import random
        simulated_dominance = random.uniform(50, 55)  # En producción: obtener dato real
        
        scores = {'BULLISH': 0, 'ALTSEASON': 0, 'LATERAL': 0, 'BEARISH': 0}
        
        if simulated_dominance < 45:  # Dominancia muy baja
            scores['ALTSEASON'] += 0.8
            scores['BULLISH'] += 0.2
        elif simulated_dominance < 50:  # Dominancia baja
            scores['ALTSEASON'] += 0.6
            scores['BULLISH'] += 0.3
            scores['LATERAL'] += 0.1
        elif simulated_dominance < 55:  # Dominancia moderada
            scores['LATERAL'] += 0.4
            scores['BULLISH'] += 0.3
            scores['ALTSEASON'] += 0.2
            scores['BEARISH'] += 0.1
        else:  # Dominancia alta
            scores['BEARISH'] += 0.5
            scores['LATERAL'] += 0.3
            scores['BULLISH'] += 0.2
        
        return scores
    
    def _analyze_alt_performance(self, alt_data):
        """Analiza el performance de altcoins vs BTC"""
        if not alt_data:
            return {'LATERAL': 0.3, 'BULLISH': 0.3, 'BEARISH': 0.2, 'ALTSEASON': 0.2}
        
        scores = {'BULLISH': 0, 'ALTSEASON': 0, 'LATERAL': 0, 'BEARISH': 0}
        
        # Obtener datos BTC para comparación
        btc_data = self._fetch_btc_data(7)
        if btc_data is None:
            return scores
        
        btc_change_7d = float((btc_data['Close'].iloc[-1] - btc_data['Close'].iloc[-7]) / btc_data['Close'].iloc[-7])
        
        outperforming_alts = 0
        total_alts = 0
        avg_alt_performance = 0
        
        for alt_symbol, alt_df in alt_data.items():
            if len(alt_df) >= 7:
                alt_change_7d = float((alt_df['Close'].iloc[-1] - alt_df['Close'].iloc[-7]) / alt_df['Close'].iloc[-7])
                avg_alt_performance += alt_change_7d
                total_alts += 1
                
                if alt_change_7d > btc_change_7d:
                    outperforming_alts += 1
        
        if total_alts > 0:
            outperformance_ratio = outperforming_alts / total_alts
            avg_alt_performance /= total_alts
            
            if outperformance_ratio > 0.7:  # >70% alts outperforming BTC
                scores['ALTSEASON'] += 0.8
                scores['BULLISH'] += 0.2
            elif outperformance_ratio > 0.5:  # >50% alts outperforming
                scores['ALTSEASON'] += 0.5
                scores['BULLISH'] += 0.3
                scores['LATERAL'] += 0.2
            elif outperformance_ratio > 0.3:  # >30% outperforming
                scores['BULLISH'] += 0.4
                scores['LATERAL'] += 0.3
                scores['ALTSEASON'] += 0.2
                scores['BEARISH'] += 0.1
            else:  # Pocas alts outperforming
                scores['BEARISH'] += 0.5
                scores['LATERAL'] += 0.3
                scores['BULLISH'] += 0.2
        
        return scores
    
    def _analyze_volatility(self, btc_data):
        """Analiza patrones de volatilidad"""
        if btc_data is None or len(btc_data) < 10:
            return {'LATERAL': 0.4, 'BULLISH': 0.2, 'BEARISH': 0.2, 'ALTSEASON': 0.2}
        
        # Calcular volatilidad rolling
        returns = btc_data['Close'].pct_change()
        volatility_7d = float(returns.tail(7).std() * np.sqrt(365))
        volatility_30d = float(returns.tail(30).std() * np.sqrt(365)) if len(returns) >= 30 else volatility_7d
        
        scores = {'BULLISH': 0, 'ALTSEASON': 0, 'LATERAL': 0, 'BEARISH': 0}
        
        if volatility_7d > 1.2:  # Volatilidad muy alta
            scores['BEARISH'] += 0.4
            scores['ALTSEASON'] += 0.3
            scores['BULLISH'] += 0.2
            scores['LATERAL'] += 0.1
        elif volatility_7d > 0.8:  # Volatilidad alta
            scores['BULLISH'] += 0.3
            scores['ALTSEASON'] += 0.3
            scores['BEARISH'] += 0.2
            scores['LATERAL'] += 0.2
        elif volatility_7d > 0.4:  # Volatilidad moderada
            scores['BULLISH'] += 0.4
            scores['LATERAL'] += 0.3
            scores['ALTSEASON'] += 0.2
            scores['BEARISH'] += 0.1
        else:  # Volatilidad baja
            scores['LATERAL'] += 0.6
            scores['BULLISH'] += 0.2
            scores['BEARISH'] += 0.1
            scores['ALTSEASON'] += 0.1
        
        return scores
    
    def get_optimal_config_for_regime(self, regime):
        """Obtiene configuración óptima para el régimen específico"""
        return self.regime_configs.get(regime, self.regime_configs['LATERAL'])
    
    def print_regime_analysis(self, analysis):
        """Imprime análisis detallado del régimen"""
        print(f'🔍 ANÁLISIS DE RÉGIMEN DE MERCADO')
        print('='*60)
        print(f'📊 RÉGIMEN ACTUAL: {analysis["regime"]}')
        print(f'📈 DESCRIPCIÓN: {analysis["description"]}')
        print(f'🎯 CONFIANZA: {analysis["confidence"]:.1%}')
        print()
        
        print(f'📋 SCORES POR RÉGIMEN:')
        for regime, score in sorted(analysis['scores'].items(), key=lambda x: x[1], reverse=True):
            print(f'• {regime}: {score:.1%}')
        print()
        
        print(f'⚙️ CONFIGURACIÓN RECOMENDADA:')
        config = analysis['config']
        print(f'• RSI Threshold: {config.get("rsi_bullish_threshold", "N/A")}')
        print(f'• Score Mínimo: {config.get("min_score_threshold", "N/A")}')
        print(f'• Leverage Máximo: {config.get("max_leverage", "N/A")}x')
        print(f'• Peso Volumen: {config.get("volume_weight", 0)*100:.0f}%')
        print(f'• Peso Momentum: {config.get("momentum_weight", 0)*100:.0f}%')
        
        # Características específicas
        if 'alt_multiplier' in config:
            print(f'• Bonus Altcoins: {config["alt_multiplier"]:.1f}x')
        if config.get('range_bonus'):
            print(f'• Bonus Trading Rango: ✅')
        if config.get('short_bias'):
            print(f'• Preferencia Shorts: ✅')

def demo_market_regime():
    """Demo del detector de régimen"""
    
    detector = MarketRegimeDetector()
    
    print('🚀 MARKET REGIME DETECTOR')
    print('='*60)
    print('Analizando condiciones actuales del mercado...')
    print()
    
    # Detectar régimen actual
    analysis = detector.detect_current_regime()
    
    # Mostrar análisis
    detector.print_regime_analysis(analysis)
    
    return analysis

if __name__ == "__main__":
    demo_market_regime()