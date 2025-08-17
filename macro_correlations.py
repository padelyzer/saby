#!/usr/bin/env python3
"""
Macro Correlations Analysis
Implementa análisis de correlaciones macroeconómicas (DXY, SPY, VIX, US10Y)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class MacroCorrelationAnalyzer:
    """
    Analizador de correlaciones macroeconómicas para crypto
    Monitorea DXY, SPY, VIX, US10Y y su impacto en BTC/crypto
    """
    
    def __init__(self):
        # Símbolos macro principales
        self.macro_symbols = {
            'DXY': 'DX-Y.NYB',      # Dollar Index
            'SPY': 'SPY',           # S&P 500 ETF
            'VIX': '^VIX',          # Volatility Index
            'US10Y': '^TNX',        # 10-Year Treasury
            'GOLD': 'GC=F',         # Gold Futures
            'CRUDE': 'CL=F'         # Crude Oil
        }
        
        # Configuración de correlaciones esperadas con BTC
        self.expected_correlations = {
            'DXY': -0.6,    # Negativa fuerte
            'SPY': 0.6,     # Positiva fuerte (risk-on)
            'VIX': -0.4,    # Negativa moderada (risk-off)
            'US10Y': -0.3,  # Negativa (rate sensitivity)
            'GOLD': 0.2,    # Positiva débil (inflation hedge)
            'CRUDE': 0.3    # Positiva moderada (risk assets)
        }
        
        # Regímenes macro
        self.macro_regimes = {
            'RISK_ON': {
                'description': 'Risk-on environment',
                'characteristics': ['SPY up', 'DXY down', 'VIX low'],
                'btc_impact': 'BULLISH',
                'weight_multiplier': 1.2
            },
            'RISK_OFF': {
                'description': 'Risk-off environment', 
                'characteristics': ['SPY down', 'DXY up', 'VIX high'],
                'btc_impact': 'BEARISH',
                'weight_multiplier': 0.8
            },
            'INFLATION_HEDGE': {
                'description': 'Inflation concerns',
                'characteristics': ['DXY down', 'GOLD up', 'US10Y up'],
                'btc_impact': 'BULLISH',
                'weight_multiplier': 1.1
            },
            'RATE_HIKE_FEAR': {
                'description': 'Interest rate concerns',
                'characteristics': ['US10Y up sharp', 'SPY down', 'DXY up'],
                'btc_impact': 'BEARISH',
                'weight_multiplier': 0.7
            },
            'NEUTRAL': {
                'description': 'No clear macro regime',
                'characteristics': ['Mixed signals'],
                'btc_impact': 'NEUTRAL',
                'weight_multiplier': 1.0
            }
        }
        
        # Cache para datos macro
        self.macro_cache = {}
        self.cache_duration = 1800  # 30 minutos
        
    def get_macro_analysis(self, crypto_symbol='BTC-USD', lookback_days=30):
        """Obtiene análisis macro completo"""
        
        print(f"🌍 Analizando correlaciones macro para {crypto_symbol}...")
        
        try:
            # Obtener datos macro
            macro_data = self._fetch_macro_data(lookback_days)
            
            # Obtener datos crypto
            crypto_data = self._fetch_crypto_data(crypto_symbol, lookback_days)
            
            # Calcular correlaciones actuales
            correlations = self._calculate_correlations(crypto_data, macro_data)
            
            # Detectar régimen macro actual
            current_regime = self._detect_macro_regime(macro_data)
            
            # Calcular score macro
            macro_score = self._calculate_macro_score(correlations, current_regime)
            
            # Generar insights
            insights = self._generate_macro_insights(correlations, current_regime, macro_score)
            
            return {
                'macro_score': macro_score,
                'regime': current_regime,
                'correlations': correlations,
                'insights': insights,
                'timestamp': datetime.now(),
                'symbol': crypto_symbol
            }
            
        except Exception as e:
            print(f"⚠️ Error en análisis macro: {e}")
            return self._get_fallback_macro_analysis(crypto_symbol)
    
    def _fetch_macro_data(self, days):
        """Obtiene datos de instrumentos macro"""
        
        macro_data = {}
        
        for name, symbol in self.macro_symbols.items():
            try:
                # Verificar cache
                cache_key = f"{symbol}_{days}"
                if self._is_cache_valid(cache_key):
                    macro_data[name] = self.macro_cache[cache_key]
                    continue
                
                # Obtener datos frescos
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=f"{days}d")
                
                if len(data) > 0:
                    macro_data[name] = data['Close']
                    self.macro_cache[cache_key] = data['Close']
                else:
                    print(f"⚠️ No data for {name} ({symbol})")
                    
            except Exception as e:
                print(f"⚠️ Error fetching {name}: {e}")
                # Generar datos sintéticos como fallback
                macro_data[name] = self._generate_synthetic_macro_data(name, days)
        
        return macro_data
    
    def _fetch_crypto_data(self, symbol, days):
        """Obtiene datos de crypto"""
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f"{days}d")
            return data['Close']
        except Exception as e:
            print(f"⚠️ Error fetching crypto data: {e}")
            return pd.Series([])
    
    def _calculate_correlations(self, crypto_data, macro_data):
        """Calcula correlaciones entre crypto y macro assets"""
        
        correlations = {}
        
        if len(crypto_data) == 0:
            return {name: 0.0 for name in macro_data.keys()}
        
        # Calcular returns para correlaciones
        crypto_returns = crypto_data.pct_change().dropna()
        
        for name, macro_series in macro_data.items():
            try:
                if len(macro_series) > 0:
                    # Alinear índices
                    common_index = crypto_returns.index.intersection(macro_series.index)
                    
                    if len(common_index) > 10:  # Mínimo 10 puntos
                        macro_returns = macro_series.pct_change().dropna()
                        
                        # Calcular correlación en período común
                        crypto_aligned = crypto_returns.loc[common_index]
                        macro_aligned = macro_returns.loc[common_index]
                        
                        correlation = crypto_aligned.corr(macro_aligned)
                        correlations[name] = float(correlation) if not np.isnan(correlation) else 0.0
                    else:
                        correlations[name] = 0.0
                else:
                    correlations[name] = 0.0
                    
            except Exception as e:
                print(f"⚠️ Error calculating correlation for {name}: {e}")
                correlations[name] = 0.0
        
        return correlations
    
    def _detect_macro_regime(self, macro_data):
        """Detecta régimen macroeconómico actual"""
        
        try:
            # Calcular cambios recientes (últimos 5 días)
            changes = {}
            
            for name, series in macro_data.items():
                if len(series) >= 5:
                    recent_change = (series.iloc[-1] - series.iloc[-5]) / series.iloc[-5]
                    changes[name] = recent_change
                else:
                    changes[name] = 0.0
            
            # Lógica de detección de régimen
            dxy_change = changes.get('DXY', 0)
            spy_change = changes.get('SPY', 0)
            vix_change = changes.get('VIX', 0)
            us10y_change = changes.get('US10Y', 0)
            gold_change = changes.get('GOLD', 0)
            
            # Risk-On: SPY up, DXY down, VIX down
            if spy_change > 0.02 and dxy_change < -0.01 and vix_change < -0.1:
                return 'RISK_ON'
            
            # Risk-Off: SPY down, DXY up, VIX up
            elif spy_change < -0.02 and dxy_change > 0.01 and vix_change > 0.1:
                return 'RISK_OFF'
            
            # Inflation Hedge: DXY down, Gold up
            elif dxy_change < -0.015 and gold_change > 0.02:
                return 'INFLATION_HEDGE'
            
            # Rate Hike Fear: US10Y up sharp, SPY down
            elif us10y_change > 0.05 and spy_change < -0.01:
                return 'RATE_HIKE_FEAR'
            
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            print(f"⚠️ Error detecting macro regime: {e}")
            return 'NEUTRAL'
    
    def _calculate_macro_score(self, correlations, regime):
        """Calcula score macro (0-1)"""
        
        try:
            # Score base por correlaciones
            correlation_score = 0.5  # Neutral baseline
            
            # Evaluar cada correlación vs expectativa
            correlation_alignment = 0
            total_weight = 0
            
            for name, actual_corr in correlations.items():
                expected_corr = self.expected_correlations.get(name, 0)
                
                # Calcular qué tan cerca está la correlación actual de la esperada
                if expected_corr != 0:
                    alignment = 1 - abs(actual_corr - expected_corr) / abs(expected_corr)
                    alignment = max(0, alignment)  # No negative
                    
                    # Peso por importancia (DXY y SPY más importantes)
                    if name in ['DXY', 'SPY']:
                        weight = 0.3
                    elif name == 'VIX':
                        weight = 0.2
                    else:
                        weight = 0.1
                    
                    correlation_alignment += alignment * weight
                    total_weight += weight
            
            if total_weight > 0:
                correlation_score = correlation_alignment / total_weight
            
            # Ajustar por régimen actual
            regime_info = self.macro_regimes.get(regime, self.macro_regimes['NEUTRAL'])
            regime_multiplier = regime_info['weight_multiplier']
            
            # Ajustar score según si el régimen es bullish/bearish para crypto
            if regime_info['btc_impact'] == 'BULLISH':
                final_score = min(1.0, correlation_score * regime_multiplier)
            elif regime_info['btc_impact'] == 'BEARISH':
                final_score = max(0.0, correlation_score * regime_multiplier)
            else:
                final_score = correlation_score
            
            return final_score
            
        except Exception as e:
            print(f"⚠️ Error calculating macro score: {e}")
            return 0.5
    
    def _generate_macro_insights(self, correlations, regime, score):
        """Genera insights de análisis macro"""
        
        insights = {
            'regime_analysis': self.macro_regimes[regime],
            'correlation_analysis': {},
            'trading_implications': [],
            'risk_factors': []
        }
        
        # Análisis de correlaciones
        for name, corr in correlations.items():
            expected = self.expected_correlations.get(name, 0)
            
            if abs(corr - expected) > 0.3:
                insights['correlation_analysis'][name] = {
                    'actual': corr,
                    'expected': expected,
                    'status': 'UNUSUAL' if abs(corr - expected) > 0.5 else 'DIFFERENT',
                    'implication': self._get_correlation_implication(name, corr, expected)
                }
        
        # Implicaciones de trading
        if score >= 0.7:
            insights['trading_implications'].append("Macro environment supports crypto longs")
            insights['trading_implications'].append("Consider increasing position sizes")
        elif score <= 0.3:
            insights['trading_implications'].append("Macro headwinds for crypto")
            insights['trading_implications'].append("Consider reducing exposure")
        
        # Factores de riesgo
        if regime == 'RISK_OFF':
            insights['risk_factors'].append("Risk-off environment may cause crypto correlation with stocks")
        if regime == 'RATE_HIKE_FEAR':
            insights['risk_factors'].append("Rising rates typically negative for crypto")
        
        return insights
    
    def _get_correlation_implication(self, asset, actual, expected):
        """Obtiene implicación de correlación inusual"""
        
        if asset == 'DXY':
            if actual > expected + 0.3:
                return "Stronger positive correlation with USD - unusual for crypto"
            elif actual < expected - 0.3:
                return "Weaker negative correlation with USD - crypto showing independence"
        
        elif asset == 'SPY':
            if actual < expected - 0.3:
                return "Crypto decoupling from stocks - potential safe haven behavior"
            elif actual > expected + 0.3:
                return "Crypto highly correlated with stocks - risk asset behavior"
        
        return "Correlation deviation from historical norms"
    
    def _generate_synthetic_macro_data(self, asset_name, days):
        """Genera datos sintéticos para testing"""
        
        # Valores base típicos
        base_values = {
            'DXY': 103.5,
            'SPY': 450.0,
            'VIX': 18.0,
            'US10Y': 4.5,
            'GOLD': 2000.0,
            'CRUDE': 80.0
        }
        
        base_value = base_values.get(asset_name, 100.0)
        
        # Generar serie de tiempo sintética
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Random walk con drift
        returns = np.random.normal(0, 0.02, days)  # 2% daily volatility
        returns[0] = 0
        
        # Cumulative returns
        cumulative_returns = np.cumsum(returns)
        prices = base_value * np.exp(cumulative_returns)
        
        return pd.Series(prices, index=dates)
    
    def _is_cache_valid(self, cache_key):
        """Verifica si cache es válido"""
        if cache_key not in self.macro_cache:
            return False
        
        # Por simplicidad, siempre refrescar
        return False
    
    def _get_fallback_macro_analysis(self, symbol):
        """Análisis de fallback cuando hay errores"""
        
        return {
            'macro_score': 0.5,
            'regime': 'NEUTRAL',
            'correlations': {name: 0.0 for name in self.macro_symbols.keys()},
            'insights': {
                'regime_analysis': self.macro_regimes['NEUTRAL'],
                'correlation_analysis': {},
                'trading_implications': ['Using neutral macro assumptions'],
                'risk_factors': ['Macro data unavailable']
            },
            'timestamp': datetime.now(),
            'symbol': symbol,
            'source': 'fallback'
        }
    
    def get_trading_adjustment(self, base_score, symbol='BTC-USD'):
        """Obtiene ajuste de trading basado en macro"""
        
        macro_analysis = self.get_macro_analysis(symbol)
        macro_score = macro_analysis['macro_score']
        regime = macro_analysis['regime']
        
        # Calcular factor de ajuste
        regime_info = self.macro_regimes[regime]
        
        if regime_info['btc_impact'] == 'BULLISH':
            if macro_score >= 0.7:
                adjustment_factor = 1.15  # +15%
            else:
                adjustment_factor = 1.05  # +5%
        elif regime_info['btc_impact'] == 'BEARISH':
            if macro_score <= 0.3:
                adjustment_factor = 0.85  # -15%
            else:
                adjustment_factor = 0.95  # -5%
        else:
            adjustment_factor = 1.0  # Neutral
        
        adjusted_score = base_score * adjustment_factor
        
        return adjusted_score, {
            'original_score': base_score,
            'macro_score': macro_score,
            'regime': regime,
            'adjustment_factor': adjustment_factor,
            'adjusted_score': adjusted_score,
            'regime_impact': regime_info['btc_impact'],
            'macro_analysis': macro_analysis
        }
    
    def print_macro_analysis(self, symbol='BTC-USD'):
        """Imprime análisis macro detallado"""
        
        print(f"🌍 ANÁLISIS MACRO - {symbol}")
        print("="*60)
        
        analysis = self.get_macro_analysis(symbol)
        
        print(f"📊 SCORE MACRO: {analysis['macro_score']:.3f}")
        print(f"🏛️ RÉGIMEN: {analysis['regime']}")
        print(f"📅 Timestamp: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Régimen analysis
        regime_info = analysis['insights']['regime_analysis']
        print(f"\n🎯 ANÁLISIS DE RÉGIMEN:")
        print(f"• Descripción: {regime_info['description']}")
        print(f"• Impacto BTC: {regime_info['btc_impact']}")
        print(f"• Multiplicador: {regime_info['weight_multiplier']:.2f}")
        
        # Correlaciones
        print(f"\n📊 CORRELACIONES vs EXPECTATIVAS:")
        correlations = analysis['correlations']
        
        for name, actual in correlations.items():
            expected = self.expected_correlations.get(name, 0)
            diff = actual - expected
            status = "✅" if abs(diff) <= 0.2 else "⚠️" if abs(diff) <= 0.4 else "🔴"
            
            print(f"• {name}: {actual:+.2f} (exp: {expected:+.2f}) {status}")
        
        # Trading implications
        print(f"\n💡 IMPLICACIONES DE TRADING:")
        for implication in analysis['insights']['trading_implications']:
            print(f"• {implication}")
        
        # Risk factors
        if analysis['insights']['risk_factors']:
            print(f"\n⚠️ FACTORES DE RIESGO:")
            for risk in analysis['insights']['risk_factors']:
                print(f"• {risk}")
        
        return analysis

def demo_macro_analysis():
    """Demo del análisis macro"""
    
    analyzer = MacroCorrelationAnalyzer()
    
    print("🌍 MACRO CORRELATIONS DEMO")
    print("="*60)
    print("Analizando correlaciones con DXY, SPY, VIX, US10Y...")
    print("="*60)
    
    # Análisis para BTC
    analysis = analyzer.print_macro_analysis('BTC-USD')
    
    print("\n" + "="*60)
    
    # Test de ajuste
    base_score = 7.2
    adjusted_score, adjustment_details = analyzer.get_trading_adjustment(base_score, 'BTC-USD')
    
    print(f"🎯 AJUSTE MACRO TESTING:")
    print(f"• Score Base: {base_score}")
    print(f"• Score Ajustado: {adjusted_score:.2f}")
    print(f"• Factor Ajuste: {adjustment_details['adjustment_factor']:.2f}")
    print(f"• Régimen: {adjustment_details['regime']}")
    print(f"• Impacto: {adjustment_details['regime_impact']}")
    
    return analyzer

if __name__ == "__main__":
    demo_macro_analysis()