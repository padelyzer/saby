#!/usr/bin/env python3
"""
Volume-Based Position Sizing System
Sistema de dimensionamiento de posiciones basado en análisis de volumen
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class VolumeBasedPositionSizing:
    """
    Sistema de position sizing basado en:
    1. Volumen relativo y patrones de volumen
    2. Liquidez del mercado
    3. Volatilidad ajustada por volumen
    4. Profile de volumen (VPOC, VAH, VAL)
    5. Institutional volume flows
    """
    
    def __init__(self, base_capital: float = 10000):
        self.base_capital = base_capital
        
        # Configuración de volume analysis
        self.volume_config = {
            # Volume Relative Analysis
            'relative_volume': {
                'enabled': True,
                'lookback_periods': 20,
                'high_volume_multiplier': 2.0,    # 2x average volume
                'low_volume_multiplier': 0.5,     # 0.5x average volume
                'weight': 0.3
            },
            
            # Volume Profile Analysis
            'volume_profile': {
                'enabled': True,
                'profile_periods': 50,
                'poc_proximity_threshold': 0.02,   # 2% from VPOC
                'high_volume_nodes': 0.8,          # Top 80% volume nodes
                'weight': 0.25
            },
            
            # Liquidity Analysis
            'liquidity': {
                'enabled': True,
                'min_avg_volume_usd': 1000000,     # $1M daily average minimum
                'liquidity_tiers': {
                    'high': 50000000,    # $50M+ = high liquidity
                    'medium': 10000000,  # $10M+ = medium liquidity
                    'low': 1000000       # $1M+ = low liquidity
                },
                'weight': 0.2
            },
            
            # Volume Trend Analysis
            'volume_trend': {
                'enabled': True,
                'trend_periods': 10,
                'accumulation_threshold': 1.2,     # 20% volume increase
                'distribution_threshold': 0.8,     # 20% volume decrease
                'weight': 0.15
            },
            
            # Institutional Flow Analysis
            'institutional_flows': {
                'enabled': True,
                'large_trade_threshold': 100000,   # $100k+ trades
                'flow_analysis_periods': 24,       # 24 periods
                'weight': 0.1
            }
        }
        
        # Position sizing configuration
        self.sizing_config = {
            'base_position_pct': 0.02,         # 2% base position
            'max_position_pct': 0.10,          # 10% maximum position
            'min_position_pct': 0.005,         # 0.5% minimum position
            'volume_multipliers': {
                'very_high': 1.5,               # 50% larger position
                'high': 1.2,                    # 20% larger position
                'normal': 1.0,                  # Base position
                'low': 0.7,                     # 30% smaller position
                'very_low': 0.4                 # 60% smaller position
            },
            'risk_adjustments': {
                'high_liquidity': 1.2,          # Can size larger in liquid markets
                'medium_liquidity': 1.0,        # Normal sizing
                'low_liquidity': 0.6            # Smaller positions in illiquid markets
            }
        }
        
    def calculate_optimal_position_size(self, symbol: str, signal_data: Dict, 
                                      available_capital: float = None) -> Dict:
        """Calcula tamaño óptimo de posición basado en análisis de volumen"""
        
        if available_capital is None:
            available_capital = self.base_capital
        
        try:
            # Obtener datos de mercado
            market_data = self._fetch_market_data(symbol)
            if market_data is None:
                return self._get_fallback_sizing(signal_data, available_capital)
            
            # Analizar componentes de volumen
            volume_analysis = self._analyze_volume_components(market_data, symbol)
            
            # Calcular score de volumen compuesto
            volume_score = self._calculate_composite_volume_score(volume_analysis)
            
            # Determinar tier de liquidez
            liquidity_tier = self._determine_liquidity_tier(market_data, symbol)
            
            # Calcular tamaño base
            base_size_pct = self._calculate_base_size_percentage(
                signal_data, volume_score, liquidity_tier
            )
            
            # Aplicar ajustes dinámicos
            adjusted_size_pct = self._apply_dynamic_adjustments(
                base_size_pct, volume_analysis, liquidity_tier, signal_data
            )
            
            # Convertir a capital absoluto
            position_capital = available_capital * adjusted_size_pct
            
            # Validar límites
            position_capital = self._validate_position_limits(
                position_capital, available_capital, liquidity_tier
            )
            
            # Calcular métricas adicionales
            sizing_metrics = self._calculate_sizing_metrics(
                position_capital, available_capital, market_data, volume_analysis
            )
            
            return {
                'symbol': symbol,
                'position_capital': position_capital,
                'position_pct': (position_capital / available_capital) * 100,
                'base_size_pct': base_size_pct * 100,
                'adjusted_size_pct': adjusted_size_pct * 100,
                'volume_score': volume_score,
                'liquidity_tier': liquidity_tier,
                'volume_analysis': volume_analysis,
                'sizing_metrics': sizing_metrics,
                'recommendation': self._get_sizing_recommendation(volume_score, liquidity_tier),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"⚠️ Error calculando position size: {e}")
            return self._get_fallback_sizing(signal_data, available_capital)
    
    def _fetch_market_data(self, symbol: str, periods: int = 100) -> Optional[pd.DataFrame]:
        """Obtiene datos de mercado con volumen"""
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="60d", interval="1h")
            
            if len(data) == 0:
                return None
            
            # Añadir métricas de volumen
            data = self._add_volume_indicators(data)
            
            return data.tail(periods)
            
        except Exception as e:
            print(f"⚠️ Error obteniendo datos: {e}")
            return None
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade indicadores de volumen"""
        
        # Volume Moving Averages
        df['Volume_MA_20'] = df['Volume'].rolling(20).mean()
        df['Volume_MA_50'] = df['Volume'].rolling(50).mean()
        
        # Volume Relative Strength
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA_20'].replace(0, 1)
        df['Volume_Ratio'] = df['Volume_Ratio'].fillna(1.0).clip(lower=0.1)
        
        # Price-Volume relationship
        df['PV_Trend'] = (df['Close'].pct_change() * df['Volume_Ratio']).rolling(5).mean()
        
        # Volume-Weighted Average Price (VWAP)
        df['Cumulative_Volume'] = df['Volume'].cumsum()
        df['Cumulative_Price_Volume'] = (df['Close'] * df['Volume']).cumsum()
        df['VWAP'] = df['Cumulative_Price_Volume'] / df['Cumulative_Volume']
        
        # On-Balance Volume (OBV)
        df['Price_Change'] = df['Close'].diff()
        df['OBV'] = (df['Volume'] * np.sign(df['Price_Change'])).cumsum()
        
        # Money Flow Index approximation
        df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['Money_Flow'] = df['Typical_Price'] * df['Volume']
        
        # Volume Profile approximation
        df['Volume_Density'] = df['Volume'] / (df['High'] - df['Low']).replace(0, 1)
        
        return df
    
    def _analyze_volume_components(self, df: pd.DataFrame, symbol: str) -> Dict:
        """Analiza componentes de volumen"""
        
        analysis = {
            'relative_volume': {},
            'volume_profile': {},
            'liquidity': {},
            'volume_trend': {},
            'institutional_flows': {}
        }
        
        current = df.iloc[-1]
        recent_data = df.tail(20)
        
        # 1. Relative Volume Analysis
        if self.volume_config['relative_volume']['enabled']:
            analysis['relative_volume'] = self._analyze_relative_volume(df, current)
        
        # 2. Volume Profile Analysis
        if self.volume_config['volume_profile']['enabled']:
            analysis['volume_profile'] = self._analyze_volume_profile(df)
        
        # 3. Liquidity Analysis
        if self.volume_config['liquidity']['enabled']:
            analysis['liquidity'] = self._analyze_liquidity(df, symbol)
        
        # 4. Volume Trend Analysis
        if self.volume_config['volume_trend']['enabled']:
            analysis['volume_trend'] = self._analyze_volume_trend(recent_data)
        
        # 5. Institutional Flows (simulado)
        if self.volume_config['institutional_flows']['enabled']:
            analysis['institutional_flows'] = self._analyze_institutional_flows(df)
        
        return analysis
    
    def _analyze_relative_volume(self, df: pd.DataFrame, current: pd.Series) -> Dict:
        """Analiza volumen relativo"""
        
        try:
            lookback = self.volume_config['relative_volume']['lookback_periods']
            recent_data = df.tail(lookback)
            
            current_volume = current['Volume']
            avg_volume = recent_data['Volume'].mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Categorizar volumen
            high_mult = self.volume_config['relative_volume']['high_volume_multiplier']
            low_mult = self.volume_config['relative_volume']['low_volume_multiplier']
            
            if volume_ratio >= high_mult:
                volume_category = 'very_high'
                score = 0.9
            elif volume_ratio >= 1.5:
                volume_category = 'high'
                score = 0.7
            elif volume_ratio >= 0.8:
                volume_category = 'normal'
                score = 0.5
            elif volume_ratio >= low_mult:
                volume_category = 'low'
                score = 0.3
            else:
                volume_category = 'very_low'
                score = 0.1
            
            return {
                'current_volume': current_volume,
                'average_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'category': volume_category,
                'score': score
            }
            
        except Exception as e:
            return {'score': 0.5, 'error': str(e)}
    
    def _analyze_volume_profile(self, df: pd.DataFrame) -> Dict:
        """Analiza perfil de volumen"""
        
        try:
            profile_periods = min(len(df), self.volume_config['volume_profile']['profile_periods'])
            profile_data = df.tail(profile_periods)
            
            # Simular análisis de volume profile
            # En implementación real, se calcularían POC, VAH, VAL
            
            current_price = df.iloc[-1]['Close']
            vwap = df.iloc[-1]['VWAP']
            
            # Distancia del precio al VWAP como proxy de POC
            price_vwap_distance = abs(current_price - vwap) / current_price
            
            poc_threshold = self.volume_config['volume_profile']['poc_proximity_threshold']
            
            if price_vwap_distance <= poc_threshold:
                profile_strength = 0.8  # Cerca del POC
            elif price_vwap_distance <= poc_threshold * 2:
                profile_strength = 0.6  # Moderadamente cerca
            else:
                profile_strength = 0.3  # Lejos del POC
            
            # Volume concentration
            volume_std = profile_data['Volume'].std()
            volume_mean = profile_data['Volume'].mean()
            volume_concentration = 1 - (volume_std / volume_mean) if volume_mean > 0 else 0
            volume_concentration = max(0, min(volume_concentration, 1))
            
            return {
                'current_price': current_price,
                'vwap': vwap,
                'price_vwap_distance': price_vwap_distance,
                'profile_strength': profile_strength,
                'volume_concentration': volume_concentration,
                'score': (profile_strength + volume_concentration) / 2
            }
            
        except Exception as e:
            return {'score': 0.5, 'error': str(e)}
    
    def _analyze_liquidity(self, df: pd.DataFrame, symbol: str) -> Dict:
        """Analiza liquidez del mercado"""
        
        try:
            # Estimar volumen en USD
            avg_price = df['Close'].tail(20).mean()
            avg_volume = df['Volume'].tail(20).mean()
            avg_volume_usd = avg_volume * avg_price
            
            # Determinar tier de liquidez
            tiers = self.volume_config['liquidity']['liquidity_tiers']
            
            if avg_volume_usd >= tiers['high']:
                liquidity_tier = 'high'
                score = 0.9
            elif avg_volume_usd >= tiers['medium']:
                liquidity_tier = 'medium'
                score = 0.6
            elif avg_volume_usd >= tiers['low']:
                liquidity_tier = 'low'
                score = 0.3
            else:
                liquidity_tier = 'very_low'
                score = 0.1
            
            # Calcular spread simulado (basado en volatilidad)
            volatility = df['Close'].pct_change().tail(20).std()
            estimated_spread_pct = volatility * 0.5  # Aproximación
            
            return {
                'avg_volume_usd': avg_volume_usd,
                'liquidity_tier': liquidity_tier,
                'estimated_spread_pct': estimated_spread_pct,
                'score': score
            }
            
        except Exception as e:
            return {'score': 0.5, 'error': str(e)}
    
    def _analyze_volume_trend(self, recent_data: pd.DataFrame) -> Dict:
        """Analiza tendencia de volumen"""
        
        try:
            # Comparar volumen reciente vs anterior
            if len(recent_data) < 10:
                return {'score': 0.5}
            
            recent_volume = recent_data['Volume'].tail(5).mean()
            older_volume = recent_data['Volume'].head(5).mean()
            
            volume_trend_ratio = recent_volume / older_volume if older_volume > 0 else 1
            
            acc_threshold = self.volume_config['volume_trend']['accumulation_threshold']
            dist_threshold = self.volume_config['volume_trend']['distribution_threshold']
            
            if volume_trend_ratio >= acc_threshold:
                trend_type = 'accumulation'
                score = 0.8
            elif volume_trend_ratio <= dist_threshold:
                trend_type = 'distribution'
                score = 0.3
            else:
                trend_type = 'neutral'
                score = 0.5
            
            # Analizar consistencia del trend
            volume_consistency = 1 - recent_data['Volume'].std() / recent_data['Volume'].mean()
            volume_consistency = max(0, min(volume_consistency, 1))
            
            return {
                'recent_volume': recent_volume,
                'older_volume': older_volume,
                'volume_trend_ratio': volume_trend_ratio,
                'trend_type': trend_type,
                'consistency': volume_consistency,
                'score': score * (0.7 + 0.3 * volume_consistency)
            }
            
        except Exception as e:
            return {'score': 0.5, 'error': str(e)}
    
    def _analyze_institutional_flows(self, df: pd.DataFrame) -> Dict:
        """Analiza flujos institucionales (simulado)"""
        
        try:
            # Simular detección de trades institucionales
            # Basado en spikes de volumen + movimientos de precio
            
            price_changes = df['Close'].pct_change().abs()
            volume_spikes = df['Volume_Ratio']
            
            # Detectar posibles trades institucionales
            institutional_threshold = 2.0  # 2x volume + price movement
            
            recent_data = df.tail(24)  # Últimas 24 horas
            institutional_activity = 0
            
            for i in range(len(recent_data)):
                volume_spike = recent_data.iloc[i]['Volume_Ratio']
                price_change = abs(recent_data.iloc[i]['Close'] - recent_data.iloc[i-1]['Close']) / recent_data.iloc[i-1]['Close'] if i > 0 else 0
                
                if volume_spike >= institutional_threshold and price_change >= 0.01:  # 1% price move
                    institutional_activity += 1
            
            # Score basado en actividad institucional
            if institutional_activity >= 3:
                score = 0.8  # Alta actividad institucional
                flow_type = 'high_institutional'
            elif institutional_activity >= 1:
                score = 0.6  # Actividad moderada
                flow_type = 'moderate_institutional'
            else:
                score = 0.4  # Actividad retail
                flow_type = 'retail_dominated'
            
            return {
                'institutional_signals': institutional_activity,
                'flow_type': flow_type,
                'score': score
            }
            
        except Exception as e:
            return {'score': 0.5, 'error': str(e)}
    
    def _calculate_composite_volume_score(self, volume_analysis: Dict) -> float:
        """Calcula score compuesto de volumen"""
        
        total_score = 0
        total_weight = 0
        
        for component, config in self.volume_config.items():
            if config.get('enabled', False) and component in volume_analysis:
                analysis = volume_analysis[component]
                score = analysis.get('score', 0.5)
                weight = config.get('weight', 0.1)
                
                total_score += score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    def _determine_liquidity_tier(self, df: pd.DataFrame, symbol: str) -> str:
        """Determina tier de liquidez"""
        
        liquidity_analysis = self._analyze_liquidity(df, symbol)
        return liquidity_analysis.get('liquidity_tier', 'medium')
    
    def _calculate_base_size_percentage(self, signal_data: Dict, volume_score: float, 
                                       liquidity_tier: str) -> float:
        """Calcula porcentaje base de posición"""
        
        # Tamaño base
        base_pct = self.sizing_config['base_position_pct']
        
        # Ajuste por score de volumen
        volume_multiplier = 1.0
        if volume_score >= 0.8:
            volume_multiplier = self.sizing_config['volume_multipliers']['very_high']
        elif volume_score >= 0.6:
            volume_multiplier = self.sizing_config['volume_multipliers']['high']
        elif volume_score >= 0.4:
            volume_multiplier = self.sizing_config['volume_multipliers']['normal']
        elif volume_score >= 0.2:
            volume_multiplier = self.sizing_config['volume_multipliers']['low']
        else:
            volume_multiplier = self.sizing_config['volume_multipliers']['very_low']
        
        # Ajuste por liquidez
        liquidity_multiplier = self.sizing_config['risk_adjustments'].get(
            f'{liquidity_tier}_liquidity', 1.0
        )
        
        # Ajuste por score de señal
        signal_score = signal_data.get('final_score', signal_data.get('score', 6.0))
        signal_multiplier = 1.0
        
        if signal_score >= 8.0:
            signal_multiplier = 1.3
        elif signal_score >= 7.0:
            signal_multiplier = 1.1
        elif signal_score < 6.0:
            signal_multiplier = 0.8
        
        # Calcular tamaño final
        final_pct = base_pct * volume_multiplier * liquidity_multiplier * signal_multiplier
        
        return final_pct
    
    def _apply_dynamic_adjustments(self, base_size_pct: float, volume_analysis: Dict, 
                                  liquidity_tier: str, signal_data: Dict) -> float:
        """Aplica ajustes dinámicos al tamaño"""
        
        adjusted_pct = base_size_pct
        
        # Ajuste por trend de volumen
        volume_trend = volume_analysis.get('volume_trend', {})
        if volume_trend.get('trend_type') == 'accumulation':
            adjusted_pct *= 1.1  # Aumentar en acumulación
        elif volume_trend.get('trend_type') == 'distribution':
            adjusted_pct *= 0.9  # Reducir en distribución
        
        # Ajuste por perfil de volumen
        volume_profile = volume_analysis.get('volume_profile', {})
        profile_strength = volume_profile.get('profile_strength', 0.5)
        if profile_strength >= 0.7:
            adjusted_pct *= 1.05  # Ligero aumento cerca del POC
        
        # Ajuste por flujos institucionales
        institutional = volume_analysis.get('institutional_flows', {})
        if institutional.get('flow_type') == 'high_institutional':
            adjusted_pct *= 1.1  # Seguir flujos institucionales
        
        return adjusted_pct
    
    def _validate_position_limits(self, position_capital: float, available_capital: float, 
                                 liquidity_tier: str) -> float:
        """Valida y ajusta límites de posición"""
        
        # Límites globales
        max_position = available_capital * self.sizing_config['max_position_pct']
        min_position = available_capital * self.sizing_config['min_position_pct']
        
        # Ajustes por liquidez
        if liquidity_tier == 'very_low':
            max_position *= 0.5  # Reducir máximo en mercados ilíquidos
        elif liquidity_tier == 'low':
            max_position *= 0.7
        
        return max(min_position, min(position_capital, max_position))
    
    def _calculate_sizing_metrics(self, position_capital: float, available_capital: float,
                                 df: pd.DataFrame, volume_analysis: Dict) -> Dict:
        """Calcula métricas adicionales de sizing"""
        
        try:
            # Risk per trade
            avg_atr = df['Close'].rolling(14).std().iloc[-1] * df['Close'].iloc[-1] / 100
            risk_per_trade = avg_atr * 2  # 2 ATR risk aproximado
            risk_pct = (risk_per_trade / position_capital) * 100 if position_capital > 0 else 0
            
            # Position concentration
            position_pct = (position_capital / available_capital) * 100
            
            # Liquidity impact estimate
            avg_volume_usd = volume_analysis.get('liquidity', {}).get('avg_volume_usd', 1000000)
            liquidity_impact = (position_capital / avg_volume_usd) * 100
            
            return {
                'risk_per_trade_usd': risk_per_trade,
                'risk_percentage': risk_pct,
                'position_concentration': position_pct,
                'liquidity_impact_pct': liquidity_impact,
                'kelly_fraction': self._calculate_kelly_fraction(volume_analysis),
                'sharpe_estimate': self._estimate_position_sharpe(df, position_capital)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_kelly_fraction(self, volume_analysis: Dict) -> float:
        """Calcula Kelly fraction aproximado"""
        
        # Simplificado: basado en score de volumen
        volume_score = 0.5
        for component in volume_analysis.values():
            if isinstance(component, dict) and 'score' in component:
                volume_score = max(volume_score, component['score'])
        
        # Kelly aproximado: (probabilidad_ganar * ratio_ganancia - probabilidad_perder) / ratio_ganancia
        win_prob = 0.45 + (volume_score - 0.5) * 0.3  # 45-75% basado en volumen
        win_ratio = 1.5  # 1.5:1 ratio aproximado
        
        kelly = (win_prob * win_ratio - (1 - win_prob)) / win_ratio
        return max(0, min(kelly, 0.25))  # Cap at 25%
    
    def _estimate_position_sharpe(self, df: pd.DataFrame, position_capital: float) -> float:
        """Estima Sharpe ratio de la posición"""
        
        try:
            returns = df['Close'].pct_change().dropna()
            if len(returns) < 10:
                return 0
            
            # Sharpe aproximado
            mean_return = returns.mean() * 252  # Anualizado
            std_return = returns.std() * np.sqrt(252)  # Anualizado
            
            sharpe = mean_return / std_return if std_return > 0 else 0
            return sharpe
            
        except:
            return 0
    
    def _get_sizing_recommendation(self, volume_score: float, liquidity_tier: str) -> str:
        """Obtiene recomendación de sizing"""
        
        if volume_score >= 0.8 and liquidity_tier in ['high', 'medium']:
            return "AGGRESSIVE - High volume + good liquidity support larger position"
        elif volume_score >= 0.6:
            return "MODERATE - Good volume conditions support normal sizing"
        elif volume_score >= 0.4:
            return "CONSERVATIVE - Mixed volume signals suggest smaller position"
        else:
            return "MINIMAL - Weak volume suggests very small position"
    
    def _get_fallback_sizing(self, signal_data: Dict, available_capital: float) -> Dict:
        """Sizing de fallback cuando hay errores"""
        
        base_pct = self.sizing_config['base_position_pct']
        position_capital = available_capital * base_pct
        
        return {
            'position_capital': position_capital,
            'position_pct': base_pct * 100,
            'volume_score': 0.5,
            'liquidity_tier': 'medium',
            'recommendation': 'FALLBACK - Using conservative default sizing',
            'source': 'fallback',
            'timestamp': datetime.now()
        }
    
    def print_sizing_analysis(self, symbol: str, signal_data: Dict, available_capital: float = None):
        """Imprime análisis detallado de position sizing"""
        
        print(f"📊 VOLUME-BASED POSITION SIZING - {symbol}")
        print("="*70)
        
        sizing_result = self.calculate_optimal_position_size(symbol, signal_data, available_capital)
        
        print(f"💰 CAPITAL DISPONIBLE: ${sizing_result.get('available_capital', available_capital or self.base_capital):,.2f}")
        print(f"🎯 POSICIÓN RECOMENDADA: ${sizing_result['position_capital']:,.2f}")
        print(f"📊 PORCENTAJE: {sizing_result['position_pct']:.2f}%")
        print(f"🔄 SCORE VOLUMEN: {sizing_result['volume_score']:.3f}")
        print(f"💧 LIQUIDEZ: {sizing_result['liquidity_tier'].upper()}")
        
        # Análisis por componentes
        volume_analysis = sizing_result.get('volume_analysis', {})
        
        print(f"\n📋 ANÁLISIS POR COMPONENTE:")
        
        for component, analysis in volume_analysis.items():
            if isinstance(analysis, dict) and 'score' in analysis:
                score = analysis['score']
                status = "🟢" if score >= 0.7 else "🟡" if score >= 0.5 else "🔴"
                
                print(f"• {component.replace('_', ' ').title()}: {score:.3f} {status}")
                
                # Detalles específicos
                if component == 'relative_volume':
                    ratio = analysis.get('volume_ratio', 1)
                    category = analysis.get('category', 'normal')
                    print(f"  Ratio: {ratio:.2f}x ({category})")
                
                elif component == 'liquidity':
                    volume_usd = analysis.get('avg_volume_usd', 0)
                    print(f"  Volumen USD: ${volume_usd:,.0f}")
                
                elif component == 'volume_trend':
                    trend_type = analysis.get('trend_type', 'neutral')
                    print(f"  Tendencia: {trend_type}")
        
        # Métricas de riesgo
        sizing_metrics = sizing_result.get('sizing_metrics', {})
        if sizing_metrics and 'error' not in sizing_metrics:
            print(f"\n⚖️ MÉTRICAS DE RIESGO:")
            print(f"• Riesgo por trade: {sizing_metrics.get('risk_percentage', 0):.2f}%")
            print(f"• Concentración: {sizing_metrics.get('position_concentration', 0):.2f}%")
            print(f"• Impacto liquidez: {sizing_metrics.get('liquidity_impact_pct', 0):.2f}%")
            print(f"• Kelly fraction: {sizing_metrics.get('kelly_fraction', 0):.3f}")
        
        # Recomendación
        print(f"\n💡 RECOMENDACIÓN:")
        print(f"📋 {sizing_result['recommendation']}")
        
        return sizing_result

def demo_volume_position_sizing():
    """Demo del sistema de position sizing basado en volumen"""
    
    sizing_system = VolumeBasedPositionSizing(base_capital=50000)
    
    print("📊 VOLUME-BASED POSITION SIZING DEMO")
    print("="*70)
    
    # Simular señal de trading
    signal_data = {
        'symbol': 'BTC-USD',
        'type': 'LONG',
        'final_score': 7.8,
        'entry_price': 45000,
        'timestamp': datetime.now()
    }
    
    print(f"🎯 Analizando sizing para señal {signal_data['type']} {signal_data['symbol']}")
    print(f"📈 Score de señal: {signal_data['final_score']}")
    print(f"💰 Entry price: ${signal_data['entry_price']:,}")
    
    # Calcular position sizing
    sizing_result = sizing_system.print_sizing_analysis(
        signal_data['symbol'], 
        signal_data, 
        available_capital=50000
    )
    
    print(f"\n" + "="*70)
    
    # Test con diferentes scores
    print(f"📊 COMPARACIÓN POR SCORE DE SEÑAL:")
    
    test_scores = [6.0, 7.0, 8.0, 9.0]
    for score in test_scores:
        test_signal = signal_data.copy()
        test_signal['final_score'] = score
        
        result = sizing_system.calculate_optimal_position_size(
            signal_data['symbol'], test_signal, 50000
        )
        
        print(f"• Score {score}: ${result['position_capital']:,.0f} ({result['position_pct']:.1f}%)")
    
    return sizing_system

if __name__ == "__main__":
    demo_volume_position_sizing()