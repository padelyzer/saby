#!/usr/bin/env python3
"""
Bollinger Bands Squeeze Strategy
Implementa estrategia de Bollinger Bands Squeeze para mejorar timing de entries
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class BollingerSqueezeStrategy:
    """
    Estrategia de Bollinger Bands Squeeze para crypto trading
    
    Conceptos clave:
    1. BB Squeeze: Baja volatilidad precede alta volatilidad
    2. Breakouts: Expansión de bandas = momentum
    3. Mean Reversion: Precio en bandas extremas = reversión
    4. %B Oscillator: Posición relativa en las bandas
    """
    
    def __init__(self):
        # Configuración de Bollinger Bands
        self.bb_config = {
            'period': 20,           # Período para SMA
            'std_dev': 2.0,         # Desviaciones estándar
            'squeeze_period': 20,   # Períodos para detectar squeeze
            'squeeze_threshold': 0.1, # Threshold para squeeze detection
            
            # Configuración para crypto (más sensible)
            'crypto_period': 14,    # Período más corto para crypto
            'crypto_std_dev': 1.8,  # Std dev más sensible
            
            # %B levels
            'overbought_level': 0.8,   # %B > 0.8 = overbought
            'oversold_level': 0.2,     # %B < 0.2 = oversold
            'middle_upper': 0.6,       # Upper middle
            'middle_lower': 0.4        # Lower middle
        }
        
        # Estrategias disponibles
        self.strategies = {
            'SQUEEZE_BREAKOUT': {
                'description': 'Trade breakouts after squeeze',
                'entry_condition': 'squeeze_breakout',
                'min_squeeze_periods': 10,
                'breakout_threshold': 0.02,  # 2% breakout
                'weight': 0.4
            },
            'MEAN_REVERSION': {
                'description': 'Trade reversions at band extremes',
                'entry_condition': 'band_touch',
                'reversion_threshold': 0.95,  # 95% de la banda
                'weight': 0.3
            },
            'TREND_FOLLOWING': {
                'description': 'Follow trends with BB confirmation',
                'entry_condition': 'trend_confirmation',
                'trend_strength_min': 0.6,
                'weight': 0.3
            }
        }
        
    def analyze_bollinger_signal(self, df, current, signal_type):
        """Analiza señales de Bollinger Bands"""
        
        try:
            # Calcular Bollinger Bands
            bb_data = self._calculate_bollinger_bands(df)
            
            if bb_data is None or len(bb_data) < self.bb_config['period']:
                return 0.5, {'error': 'Insufficient data for BB analysis'}
            
            # Análisis por estrategia
            strategies_analysis = {}
            
            # 1. Squeeze Breakout Analysis
            squeeze_analysis = self._analyze_squeeze_breakout(bb_data, signal_type)
            strategies_analysis['squeeze_breakout'] = squeeze_analysis
            
            # 2. Mean Reversion Analysis
            reversion_analysis = self._analyze_mean_reversion(bb_data, current, signal_type)
            strategies_analysis['mean_reversion'] = reversion_analysis
            
            # 3. Trend Following Analysis
            trend_analysis = self._analyze_trend_following(bb_data, current, signal_type)
            strategies_analysis['trend_following'] = trend_analysis
            
            # Calcular score compuesto
            composite_score = self._calculate_composite_bb_score(strategies_analysis)
            
            # Detalles completos
            details = {
                'bb_data': bb_data.tail(1).to_dict('records')[0] if len(bb_data) > 0 else {},
                'strategies': strategies_analysis,
                'composite_score': composite_score,
                'current_bb_state': self._get_bb_state(bb_data, current),
                'timestamp': datetime.now()
            }
            
            return composite_score, details
            
        except Exception as e:
            return 0.5, {'error': f'BB analysis error: {e}'}
    
    def _calculate_bollinger_bands(self, df):
        """Calcula Bollinger Bands y métricas relacionadas"""
        
        if len(df) < self.bb_config['period']:
            return None
        
        # Usar configuración optimizada para crypto
        period = self.bb_config['crypto_period']
        std_dev = self.bb_config['crypto_std_dev']
        
        # Cálculos básicos
        df_bb = df.copy()
        df_bb['BB_Middle'] = df_bb['Close'].rolling(period).mean()
        bb_std = df_bb['Close'].rolling(period).std()
        df_bb['BB_Upper'] = df_bb['BB_Middle'] + (bb_std * std_dev)
        df_bb['BB_Lower'] = df_bb['BB_Middle'] - (bb_std * std_dev)
        
        # %B (posición relativa en las bandas)
        df_bb['BB_PercentB'] = (df_bb['Close'] - df_bb['BB_Lower']) / (df_bb['BB_Upper'] - df_bb['BB_Lower'])
        
        # Bandwidth (ancho de las bandas)
        df_bb['BB_Bandwidth'] = (df_bb['BB_Upper'] - df_bb['BB_Lower']) / df_bb['BB_Middle']
        
        # Squeeze detection
        df_bb['BB_Squeeze'] = df_bb['BB_Bandwidth'] < self.bb_config['squeeze_threshold']
        
        # Position relative to bands
        df_bb['BB_Position'] = 'MIDDLE'
        df_bb.loc[df_bb['Close'] > df_bb['BB_Upper'], 'BB_Position'] = 'ABOVE_UPPER'
        df_bb.loc[df_bb['Close'] < df_bb['BB_Lower'], 'BB_Position'] = 'BELOW_LOWER'
        df_bb.loc[df_bb['BB_PercentB'] > 0.8, 'BB_Position'] = 'NEAR_UPPER'
        df_bb.loc[df_bb['BB_PercentB'] < 0.2, 'BB_Position'] = 'NEAR_LOWER'
        
        # Bandwidth trend
        df_bb['BB_Bandwidth_MA'] = df_bb['BB_Bandwidth'].rolling(5).mean()
        df_bb['BB_Expanding'] = df_bb['BB_Bandwidth'] > df_bb['BB_Bandwidth_MA']
        
        return df_bb
    
    def _analyze_squeeze_breakout(self, bb_data, signal_type):
        """Analiza estrategia de squeeze breakout"""
        
        analysis = {
            'score': 0.5,
            'confidence': 'LOW',
            'signals': [],
            'details': {}
        }
        
        try:
            recent_data = bb_data.tail(20)
            current = recent_data.iloc[-1]
            
            # Detectar squeeze reciente
            squeeze_periods = recent_data['BB_Squeeze'].sum()
            is_currently_squeezed = current['BB_Squeeze']
            
            # Estado de squeeze
            min_squeeze = self.strategies['SQUEEZE_BREAKOUT']['min_squeeze_periods']
            
            if squeeze_periods >= min_squeeze:
                analysis['details']['squeeze_detected'] = True
                analysis['details']['squeeze_periods'] = int(squeeze_periods)
                
                # Verificar si estamos saliendo del squeeze
                if not is_currently_squeezed and recent_data['BB_Squeeze'].iloc[-2]:
                    # Posible breakout
                    price_change = (current['Close'] - recent_data['Close'].iloc[-5]) / recent_data['Close'].iloc[-5]
                    breakout_threshold = self.strategies['SQUEEZE_BREAKOUT']['breakout_threshold']
                    
                    if abs(price_change) >= breakout_threshold:
                        # Breakout confirmado
                        breakout_direction = 'UP' if price_change > 0 else 'DOWN'
                        
                        if ((signal_type == 'LONG' and breakout_direction == 'UP') or
                            (signal_type == 'SHORT' and breakout_direction == 'DOWN')):
                            
                            analysis['score'] = 0.8
                            analysis['confidence'] = 'HIGH'
                            analysis['signals'].append(f'SQUEEZE_BREAKOUT_{breakout_direction}')
                            analysis['details']['breakout_strength'] = abs(price_change)
                        else:
                            analysis['score'] = 0.2  # Breakout en dirección opuesta
                    
                elif is_currently_squeezed:
                    # Aún en squeeze - preparar para breakout
                    analysis['score'] = 0.6
                    analysis['confidence'] = 'MEDIUM'
                    analysis['signals'].append('SQUEEZE_BUILDING')
                    analysis['details']['squeeze_building'] = True
            
            else:
                analysis['details']['squeeze_detected'] = False
                analysis['details']['squeeze_periods'] = int(squeeze_periods)
            
            # Bandwidth trend analysis
            if current['BB_Expanding']:
                analysis['details']['bandwidth_expanding'] = True
                if analysis['score'] > 0.5:
                    analysis['score'] = min(1.0, analysis['score'] + 0.1)
            
            return analysis
            
        except Exception as e:
            analysis['details']['error'] = str(e)
            return analysis
    
    def _analyze_mean_reversion(self, bb_data, current, signal_type):
        """Analiza estrategia de mean reversion"""
        
        analysis = {
            'score': 0.5,
            'confidence': 'LOW',
            'signals': [],
            'details': {}
        }
        
        try:
            recent_data = bb_data.tail(10)
            current_bb = recent_data.iloc[-1]
            
            # %B analysis
            percent_b = current_bb['BB_PercentB']
            position = current_bb['BB_Position']
            
            analysis['details']['percent_b'] = percent_b
            analysis['details']['bb_position'] = position
            
            # Mean reversion conditions
            reversion_threshold = self.strategies['MEAN_REVERSION']['reversion_threshold']
            
            # Para LONG: buscar condiciones oversold
            if signal_type == 'LONG':
                if percent_b <= self.bb_config['oversold_level']:
                    # Muy oversold
                    analysis['score'] = 0.8
                    analysis['confidence'] = 'HIGH'
                    analysis['signals'].append('OVERSOLD_REVERSION')
                    analysis['details']['reversion_type'] = 'OVERSOLD'
                    
                elif position == 'BELOW_LOWER':
                    # Precio por debajo de banda inferior
                    analysis['score'] = 0.7
                    analysis['confidence'] = 'MEDIUM'
                    analysis['signals'].append('BELOW_LOWER_BAND')
                
                elif percent_b <= self.bb_config['middle_lower']:
                    # En zona baja
                    analysis['score'] = 0.6
                    analysis['confidence'] = 'MEDIUM'
                    analysis['signals'].append('LOWER_ZONE')
            
            # Para SHORT: buscar condiciones overbought
            elif signal_type == 'SHORT':
                if percent_b >= self.bb_config['overbought_level']:
                    # Muy overbought
                    analysis['score'] = 0.8
                    analysis['confidence'] = 'HIGH'
                    analysis['signals'].append('OVERBOUGHT_REVERSION')
                    analysis['details']['reversion_type'] = 'OVERBOUGHT'
                    
                elif position == 'ABOVE_UPPER':
                    # Precio por encima de banda superior
                    analysis['score'] = 0.7
                    analysis['confidence'] = 'MEDIUM'
                    analysis['signals'].append('ABOVE_UPPER_BAND')
                
                elif percent_b >= self.bb_config['middle_upper']:
                    # En zona alta
                    analysis['score'] = 0.6
                    analysis['confidence'] = 'MEDIUM'
                    analysis['signals'].append('UPPER_ZONE')
            
            # Verificar momentum de reversión
            if len(recent_data) >= 3:
                recent_percent_b = recent_data['BB_PercentB'].tail(3).values
                
                # Para LONG: %B subiendo desde zona baja
                if (signal_type == 'LONG' and percent_b < 0.5 and 
                    recent_percent_b[-1] > recent_percent_b[-2] > recent_percent_b[-3]):
                    analysis['score'] = min(1.0, analysis['score'] + 0.15)
                    analysis['details']['momentum_reversal'] = True
                
                # Para SHORT: %B bajando desde zona alta
                elif (signal_type == 'SHORT' and percent_b > 0.5 and 
                      recent_percent_b[-1] < recent_percent_b[-2] < recent_percent_b[-3]):
                    analysis['score'] = min(1.0, analysis['score'] + 0.15)
                    analysis['details']['momentum_reversal'] = True
            
            return analysis
            
        except Exception as e:
            analysis['details']['error'] = str(e)
            return analysis
    
    def _analyze_trend_following(self, bb_data, current, signal_type):
        """Analiza estrategia de trend following con BB"""
        
        analysis = {
            'score': 0.5,
            'confidence': 'LOW',
            'signals': [],
            'details': {}
        }
        
        try:
            recent_data = bb_data.tail(20)
            current_bb = recent_data.iloc[-1]
            
            # Trend analysis usando BB Middle como referencia
            bb_middle = current_bb['BB_Middle']
            current_price = current_bb['Close']
            percent_b = current_bb['BB_PercentB']
            
            # Trend direction
            bb_middle_trend = recent_data['BB_Middle'].tail(10)
            trend_slope = (bb_middle_trend.iloc[-1] - bb_middle_trend.iloc[-5]) / bb_middle_trend.iloc[-5]
            
            analysis['details']['trend_slope'] = trend_slope
            analysis['details']['price_vs_middle'] = (current_price / bb_middle - 1)
            
            # Para LONG: tendencia alcista
            if signal_type == 'LONG':
                # Precio por encima de BB Middle
                if current_price > bb_middle:
                    analysis['score'] += 0.2
                    analysis['signals'].append('ABOVE_BB_MIDDLE')
                
                # BB Middle en tendencia alcista
                if trend_slope > 0.01:  # 1% slope upward
                    analysis['score'] += 0.3
                    analysis['confidence'] = 'MEDIUM'
                    analysis['signals'].append('BB_MIDDLE_UPTREND')
                
                # %B en zona de tendencia alcista (0.5-0.8)
                if 0.5 <= percent_b <= 0.8:
                    analysis['score'] += 0.2
                    analysis['signals'].append('BULLISH_BB_ZONE')
                
                # Bandas expandiéndose en uptrend
                if current_bb['BB_Expanding'] and trend_slope > 0:
                    analysis['score'] += 0.15
                    analysis['signals'].append('EXPANDING_UPTREND')
            
            # Para SHORT: tendencia bajista
            elif signal_type == 'SHORT':
                # Precio por debajo de BB Middle
                if current_price < bb_middle:
                    analysis['score'] += 0.2
                    analysis['signals'].append('BELOW_BB_MIDDLE')
                
                # BB Middle en tendencia bajista
                if trend_slope < -0.01:  # 1% slope downward
                    analysis['score'] += 0.3
                    analysis['confidence'] = 'MEDIUM'
                    analysis['signals'].append('BB_MIDDLE_DOWNTREND')
                
                # %B en zona de tendencia bajista (0.2-0.5)
                if 0.2 <= percent_b <= 0.5:
                    analysis['score'] += 0.2
                    analysis['signals'].append('BEARISH_BB_ZONE')
                
                # Bandas expandiéndose en downtrend
                if current_bb['BB_Expanding'] and trend_slope < 0:
                    analysis['score'] += 0.15
                    analysis['signals'].append('EXPANDING_DOWNTREND')
            
            # Ajustar confidence basado en score
            if analysis['score'] >= 0.8:
                analysis['confidence'] = 'HIGH'
            elif analysis['score'] >= 0.6:
                analysis['confidence'] = 'MEDIUM'
            
            # Normalizar score
            analysis['score'] = min(1.0, analysis['score'])
            
            return analysis
            
        except Exception as e:
            analysis['details']['error'] = str(e)
            return analysis
    
    def _calculate_composite_bb_score(self, strategies_analysis):
        """Calcula score compuesto de todas las estrategias BB"""
        
        total_score = 0
        total_weight = 0
        
        for strategy_name, strategy_config in self.strategies.items():
            weight = strategy_config['weight']
            
            # Mapear nombres
            analysis_key = strategy_name.lower()
            if 'squeeze' in analysis_key:
                analysis_key = 'squeeze_breakout'
            elif 'reversion' in analysis_key:
                analysis_key = 'mean_reversion'
            elif 'trend' in analysis_key:
                analysis_key = 'trend_following'
            
            if analysis_key in strategies_analysis:
                analysis = strategies_analysis[analysis_key]
                score = analysis.get('score', 0.5)
                
                # Aplicar peso
                total_score += score * weight
                total_weight += weight
        
        # Score promedio ponderado
        composite_score = total_score / total_weight if total_weight > 0 else 0.5
        
        return composite_score
    
    def _get_bb_state(self, bb_data, current):
        """Obtiene estado actual de BB"""
        
        if len(bb_data) == 0:
            return 'UNKNOWN'
        
        latest = bb_data.iloc[-1]
        
        state = {
            'position': latest.get('BB_Position', 'MIDDLE'),
            'percent_b': latest.get('BB_PercentB', 0.5),
            'squeeze': latest.get('BB_Squeeze', False),
            'expanding': latest.get('BB_Expanding', False),
            'bandwidth': latest.get('BB_Bandwidth', 0),
            'price_vs_middle': (current['Close'] / latest.get('BB_Middle', current['Close']) - 1) if 'BB_Middle' in latest else 0
        }
        
        return state
    
    def print_bb_analysis(self, df, current, signal_type):
        """Imprime análisis detallado de Bollinger Bands"""
        
        print(f"📊 BOLLINGER BANDS ANALYSIS - {signal_type}")
        print("="*60)
        
        score, details = self.analyze_bollinger_signal(df, current, signal_type)
        
        print(f"🎯 BB COMPOSITE SCORE: {score:.3f}")
        
        if 'error' in details:
            print(f"❌ Error: {details['error']}")
            return score, details
        
        # Estado actual de BB
        bb_state = details.get('current_bb_state', {})
        print(f"\n📊 ESTADO ACTUAL BB:")
        print(f"• Posición: {bb_state.get('position', 'N/A')}")
        print(f"• %B: {bb_state.get('percent_b', 0):.3f}")
        print(f"• Squeeze: {'✅' if bb_state.get('squeeze') else '❌'}")
        print(f"• Expanding: {'✅' if bb_state.get('expanding') else '❌'}")
        print(f"• Bandwidth: {bb_state.get('bandwidth', 0):.4f}")
        
        # Análisis por estrategia
        strategies = details.get('strategies', {})
        
        print(f"\n📋 ANÁLISIS POR ESTRATEGIA:")
        for strategy_name, analysis in strategies.items():
            score_val = analysis.get('score', 0)
            confidence = analysis.get('confidence', 'LOW')
            signals = analysis.get('signals', [])
            
            status = "🟢" if score_val >= 0.7 else "🟡" if score_val >= 0.5 else "🔴"
            
            print(f"\n• {strategy_name.replace('_', ' ').title()}: {status}")
            print(f"  Score: {score_val:.3f} | Confidence: {confidence}")
            
            if signals:
                print(f"  Signals: {', '.join(signals)}")
            
            # Detalles específicos
            strategy_details = analysis.get('details', {})
            for key, value in strategy_details.items():
                if key != 'error' and isinstance(value, (int, float, bool)):
                    print(f"  {key}: {value}")
        
        print(f"\n💡 RECOMENDACIÓN BB:")
        if score >= 0.7:
            print(f"✅ Condiciones BB favorables para {signal_type}")
        elif score >= 0.5:
            print(f"📊 Condiciones BB neutrales")
        else:
            print(f"⚠️ Condiciones BB desfavorables")
        
        return score, details

def demo_bollinger_squeeze():
    """Demo de la estrategia Bollinger Squeeze"""
    
    bb_strategy = BollingerSqueezeStrategy()
    
    print("📊 BOLLINGER BANDS SQUEEZE STRATEGY DEMO")
    print("="*70)
    
    # Obtener datos de prueba
    try:
        import yfinance as yf
        ticker = yf.Ticker("BTC-USD")
        data = ticker.history(period="60d", interval="1h")
        
        if len(data) >= 50:
            current = data.iloc[-1]
            
            # Test para LONG
            print("🔍 TESTING BB ANALYSIS - LONG:")
            score_long, details_long = bb_strategy.print_bb_analysis(data, current, 'LONG')
            
            print(f"\n" + "="*70)
            
            # Test para SHORT
            print("🔍 TESTING BB ANALYSIS - SHORT:")
            score_short, details_short = bb_strategy.print_bb_analysis(data, current, 'SHORT')
            
            print(f"\n📈 COMPARACIÓN:")
            print(f"• LONG Score: {score_long:.3f}")
            print(f"• SHORT Score: {score_short:.3f}")
            print(f"• Mejor dirección: {'LONG' if score_long > score_short else 'SHORT'}")
        
        else:
            print("⚠️ Datos insuficientes para demo completo")
    
    except Exception as e:
        print(f"⚠️ Error en demo: {e}")
    
    return bb_strategy

if __name__ == "__main__":
    demo_bollinger_squeeze()