#!/usr/bin/env python3
"""
Entry Signals Optimizer
Optimiza señales de entrada para mejorar Win Rate del 45.6% al objetivo 60%+
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class EntrySignalsOptimizer:
    """
    Optimizador de señales de entrada basado en:
    1. Market Structure Analysis
    2. Volume Profile Confirmation
    3. Multi-timeframe Confirmation
    4. Smart Money Concepts
    """
    
    def __init__(self):
        # Configuración de optimización
        self.optimization_config = {
            # Market Structure
            'market_structure': {
                'enabled': True,
                'weight': 0.25,
                'lookback_periods': 50,
                'structure_confirmation': True
            },
            
            # Volume Profile
            'volume_profile': {
                'enabled': True,
                'weight': 0.20,
                'volume_threshold': 1.5,  # 1.5x average
                'profile_confirmation': True
            },
            
            # Multi-timeframe
            'multi_timeframe': {
                'enabled': True,
                'weight': 0.20,
                'timeframes': ['1h', '4h', '1d'],
                'alignment_required': 2  # 2 out of 3 timeframes
            },
            
            # Smart Money Concepts
            'smart_money': {
                'enabled': True,
                'weight': 0.15,
                'order_blocks': True,
                'liquidity_sweeps': True,
                'fair_value_gaps': True
            },
            
            # Enhanced Filters
            'enhanced_filters': {
                'enabled': True,
                'weight': 0.20,
                'trend_filter': True,
                'volatility_filter': True,
                'time_filter': True
            }
        }
        
        # Thresholds para mejora de Win Rate
        self.win_rate_targets = {
            'current': 45.6,
            'target': 60.0,
            'aggressive_target': 65.0
        }
        
    def optimize_entry_signal(self, df, current, prev, original_signal_type, original_score):
        """Optimiza señal de entrada original"""
        
        if original_signal_type is None:
            return None, original_score, "No original signal"
        
        try:
            # Análisis de componentes de optimización
            optimizations = {}
            
            # 1. Market Structure Analysis
            if self.optimization_config['market_structure']['enabled']:
                optimizations['market_structure'] = self._analyze_market_structure(df, current, original_signal_type)
            
            # 2. Volume Profile Confirmation
            if self.optimization_config['volume_profile']['enabled']:
                optimizations['volume_profile'] = self._analyze_volume_profile(df, current, original_signal_type)
            
            # 3. Multi-timeframe Confirmation
            if self.optimization_config['multi_timeframe']['enabled']:
                optimizations['multi_timeframe'] = self._analyze_multi_timeframe(df, current, original_signal_type)
            
            # 4. Smart Money Concepts
            if self.optimization_config['smart_money']['enabled']:
                optimizations['smart_money'] = self._analyze_smart_money(df, current, original_signal_type)
            
            # 5. Enhanced Filters
            if self.optimization_config['enhanced_filters']['enabled']:
                optimizations['enhanced_filters'] = self._apply_enhanced_filters(df, current, original_signal_type)
            
            # Calcular score optimizado
            optimized_score, optimization_details = self._calculate_optimized_score(
                original_score, optimizations
            )
            
            # Determinar si mantener, mejorar o rechazar señal
            decision = self._make_optimization_decision(optimizations, optimized_score)
            
            return decision, optimized_score, optimization_details
            
        except Exception as e:
            print(f"⚠️ Error in entry optimization: {e}")
            return original_signal_type, original_score, f"Optimization error: {e}"
    
    def _analyze_market_structure(self, df, current, signal_type):
        """Analiza estructura de mercado"""
        
        try:
            analysis = {
                'score': 0.5,
                'confirmation': False,
                'details': {}
            }
            
            if len(df) < 50:
                analysis['details']['reason'] = 'Insufficient data'
                return analysis
            
            # Identificar Higher Highs/Higher Lows para uptrend
            # Lower Highs/Lower Lows para downtrend
            
            # Últimos 20 períodos para estructura reciente
            recent_data = df.tail(20)
            
            highs = recent_data['High'].values
            lows = recent_data['Low'].values
            closes = recent_data['Close'].values
            
            # Encontrar swing highs y lows
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(highs) - 2):
                # Swing high: high[i] > high[i-1] and high[i] > high[i+1]
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    swing_highs.append((i, highs[i]))
                
                # Swing low: low[i] < low[i-1] and low[i] < low[i+1]
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    swing_lows.append((i, lows[i]))
            
            # Analizar estructura según tipo de señal
            if signal_type == 'LONG':
                # Para LONG: buscamos Higher Lows (estructura alcista)
                if len(swing_lows) >= 2:
                    last_two_lows = swing_lows[-2:]
                    if last_two_lows[1][1] > last_two_lows[0][1]:  # Higher Low
                        analysis['score'] = 0.8
                        analysis['confirmation'] = True
                        analysis['details']['structure'] = 'Higher Low confirmed'
                    else:
                        analysis['score'] = 0.3
                        analysis['details']['structure'] = 'Lower Low - bearish structure'
                
            elif signal_type == 'SHORT':
                # Para SHORT: buscamos Lower Highs (estructura bajista)
                if len(swing_highs) >= 2:
                    last_two_highs = swing_highs[-2:]
                    if last_two_highs[1][1] < last_two_highs[0][1]:  # Lower High
                        analysis['score'] = 0.8
                        analysis['confirmation'] = True
                        analysis['details']['structure'] = 'Lower High confirmed'
                    else:
                        analysis['score'] = 0.3
                        analysis['details']['structure'] = 'Higher High - bullish structure'
            
            # Verificar confirmación de cierre
            if len(closes) >= 3:
                recent_trend = closes[-1] - closes[-3]
                if signal_type == 'LONG' and recent_trend > 0:
                    analysis['score'] = min(1.0, analysis['score'] + 0.1)
                elif signal_type == 'SHORT' and recent_trend < 0:
                    analysis['score'] = min(1.0, analysis['score'] + 0.1)
            
            return analysis
            
        except Exception as e:
            return {'score': 0.5, 'confirmation': False, 'details': {'error': str(e)}}
    
    def _analyze_volume_profile(self, df, current, signal_type):
        """Analiza perfil de volumen"""
        
        try:
            analysis = {
                'score': 0.5,
                'confirmation': False,
                'details': {}
            }
            
            if len(df) < 10:
                return analysis
            
            # Analizar volumen en breakouts/reversals
            recent_volume = df['Volume'].tail(3).mean()
            baseline_volume = df['Volume'].tail(20).mean()
            
            volume_ratio = recent_volume / baseline_volume if baseline_volume > 0 else 1
            
            # Volumen en dirección de la señal
            if signal_type in ['LONG', 'SHORT']:
                # Verificar si hay confirmación de volumen
                if volume_ratio >= self.optimization_config['volume_profile']['volume_threshold']:
                    # Alto volumen - bueno para breakouts
                    analysis['score'] = 0.8
                    analysis['confirmation'] = True
                    analysis['details']['volume_confirmation'] = f'High volume: {volume_ratio:.2f}x'
                elif volume_ratio >= 1.2:
                    # Volumen moderado - aceptable
                    analysis['score'] = 0.6
                    analysis['details']['volume_confirmation'] = f'Moderate volume: {volume_ratio:.2f}x'
                else:
                    # Volumen bajo - señal débil
                    analysis['score'] = 0.3
                    analysis['details']['volume_confirmation'] = f'Low volume: {volume_ratio:.2f}x'
            
            # Verificar distribución del volumen
            volume_trend = self._analyze_volume_trend(df.tail(10))
            analysis['details']['volume_trend'] = volume_trend
            
            if volume_trend == 'increasing' and signal_type == 'LONG':
                analysis['score'] = min(1.0, analysis['score'] + 0.15)
            elif volume_trend == 'increasing' and signal_type == 'SHORT':
                analysis['score'] = min(1.0, analysis['score'] + 0.15)
            
            return analysis
            
        except Exception as e:
            return {'score': 0.5, 'confirmation': False, 'details': {'error': str(e)}}
    
    def _analyze_volume_trend(self, volume_data):
        """Analiza tendencia del volumen"""
        
        if len(volume_data) < 5:
            return 'unknown'
        
        recent_avg = volume_data['Volume'].tail(3).mean()
        older_avg = volume_data['Volume'].head(3).mean()
        
        if recent_avg > older_avg * 1.2:
            return 'increasing'
        elif recent_avg < older_avg * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _analyze_multi_timeframe(self, df, current, signal_type):
        """Analiza confirmación multi-timeframe (simulada)"""
        
        try:
            analysis = {
                'score': 0.5,
                'confirmation': False,
                'details': {'timeframes': {}}
            }
            
            # Simular análisis de múltiples timeframes
            # En implementación real, se obtendrían datos de 1h, 4h, 1d
            
            timeframes = ['1h', '4h', '1d']
            confirmations = 0
            
            for tf in timeframes:
                # Simular confirmación basada en datos actuales
                tf_confirmation = self._simulate_timeframe_confirmation(df, signal_type, tf)
                analysis['details']['timeframes'][tf] = tf_confirmation
                
                if tf_confirmation['aligned']:
                    confirmations += 1
            
            # Evaluar alineación
            required_confirmations = self.optimization_config['multi_timeframe']['alignment_required']
            
            if confirmations >= required_confirmations:
                analysis['score'] = 0.8
                analysis['confirmation'] = True
                analysis['details']['alignment'] = f'{confirmations}/{len(timeframes)} timeframes aligned'
            elif confirmations >= 1:
                analysis['score'] = 0.6
                analysis['details']['alignment'] = f'{confirmations}/{len(timeframes)} timeframes aligned'
            else:
                analysis['score'] = 0.2
                analysis['details']['alignment'] = 'No timeframe alignment'
            
            return analysis
            
        except Exception as e:
            return {'score': 0.5, 'confirmation': False, 'details': {'error': str(e)}}
    
    def _simulate_timeframe_confirmation(self, df, signal_type, timeframe):
        """Simula confirmación de timeframe específico"""
        
        # Simulación basada en tendencias de diferentes períodos
        if timeframe == '1h':
            period = 3  # Últimas 3 períodos
        elif timeframe == '4h':
            period = 12  # Últimas 12 períodos (4h en datos 1h)
        else:  # 1d
            period = 24  # Últimas 24 períodos
        
        if len(df) < period:
            return {'aligned': False, 'reason': 'Insufficient data'}
        
        # Analizar tendencia en el período
        recent_data = df.tail(period)
        trend_direction = recent_data['Close'].iloc[-1] - recent_data['Close'].iloc[0]
        
        aligned = False
        if signal_type == 'LONG' and trend_direction > 0:
            aligned = True
        elif signal_type == 'SHORT' and trend_direction < 0:
            aligned = True
        
        return {
            'aligned': aligned,
            'trend_direction': 'up' if trend_direction > 0 else 'down',
            'strength': abs(trend_direction) / recent_data['Close'].iloc[0]
        }
    
    def _analyze_smart_money(self, df, current, signal_type):
        """Analiza conceptos de Smart Money"""
        
        try:
            analysis = {
                'score': 0.5,
                'confirmation': False,
                'details': {}
            }
            
            # 1. Order Blocks (zonas de acumulación/distribución)
            order_blocks = self._identify_order_blocks(df)
            analysis['details']['order_blocks'] = order_blocks
            
            # 2. Liquidity Sweeps (barridas de liquidez)
            liquidity_sweeps = self._identify_liquidity_sweeps(df)
            analysis['details']['liquidity_sweeps'] = liquidity_sweeps
            
            # 3. Fair Value Gaps (gaps de valor justo)
            fair_value_gaps = self._identify_fair_value_gaps(df)
            analysis['details']['fair_value_gaps'] = fair_value_gaps
            
            # Evaluar confirmación de Smart Money
            smart_money_score = 0
            confirmations = 0
            
            # Order blocks confirmation
            if order_blocks.get('relevant_block'):
                smart_money_score += 0.4
                confirmations += 1
            
            # Liquidity sweeps confirmation
            if liquidity_sweeps.get('recent_sweep'):
                smart_money_score += 0.3
                confirmations += 1
            
            # Fair value gaps confirmation
            if fair_value_gaps.get('active_gap'):
                smart_money_score += 0.3
                confirmations += 1
            
            analysis['score'] = smart_money_score
            analysis['confirmation'] = confirmations >= 2
            analysis['details']['confirmations'] = confirmations
            
            return analysis
            
        except Exception as e:
            return {'score': 0.5, 'confirmation': False, 'details': {'error': str(e)}}
    
    def _identify_order_blocks(self, df):
        """Identifica order blocks"""
        
        if len(df) < 20:
            return {'relevant_block': False}
        
        # Simplificado: buscar zonas de alta actividad (high volume + consolidation)
        recent_data = df.tail(20)
        
        # Identificar zonas de consolidación con alto volumen
        volume_threshold = recent_data['Volume'].quantile(0.8)
        price_range_threshold = recent_data['Close'].std() * 0.5
        
        order_blocks = []
        
        for i in range(5, len(recent_data) - 5):
            window = recent_data.iloc[i-2:i+3]
            
            # Criterios para order block
            high_volume = window['Volume'].mean() >= volume_threshold
            price_consolidation = window['High'].max() - window['Low'].min() <= price_range_threshold
            
            if high_volume and price_consolidation:
                order_blocks.append({
                    'index': i,
                    'price_level': window['Close'].mean(),
                    'volume': window['Volume'].mean()
                })
        
        return {
            'relevant_block': len(order_blocks) > 0,
            'blocks_count': len(order_blocks),
            'latest_block': order_blocks[-1] if order_blocks else None
        }
    
    def _identify_liquidity_sweeps(self, df):
        """Identifica barridas de liquidez"""
        
        if len(df) < 10:
            return {'recent_sweep': False}
        
        recent_data = df.tail(10)
        
        # Buscar movimientos que rompen high/low recientes y luego revierten
        sweeps = []
        
        for i in range(3, len(recent_data) - 1):
            current_candle = recent_data.iloc[i]
            prev_data = recent_data.iloc[i-3:i]
            
            # Liquidity sweep alcista (rompe high y revierte)
            prev_high = prev_data['High'].max()
            if (current_candle['High'] > prev_high and 
                current_candle['Close'] < current_candle['Open']):
                sweeps.append({'type': 'bullish_sweep', 'index': i})
            
            # Liquidity sweep bajista (rompe low y revierte)
            prev_low = prev_data['Low'].min()
            if (current_candle['Low'] < prev_low and 
                current_candle['Close'] > current_candle['Open']):
                sweeps.append({'type': 'bearish_sweep', 'index': i})
        
        return {
            'recent_sweep': len(sweeps) > 0,
            'sweeps_count': len(sweeps),
            'latest_sweep': sweeps[-1] if sweeps else None
        }
    
    def _identify_fair_value_gaps(self, df):
        """Identifica Fair Value Gaps"""
        
        if len(df) < 5:
            return {'active_gap': False}
        
        recent_data = df.tail(10)
        gaps = []
        
        for i in range(1, len(recent_data) - 1):
            prev_candle = recent_data.iloc[i-1]
            current_candle = recent_data.iloc[i]
            next_candle = recent_data.iloc[i+1]
            
            # Bullish FVG: prev_high < next_low
            if prev_candle['High'] < next_candle['Low']:
                gaps.append({
                    'type': 'bullish_fvg',
                    'top': next_candle['Low'],
                    'bottom': prev_candle['High'],
                    'index': i
                })
            
            # Bearish FVG: prev_low > next_high
            elif prev_candle['Low'] > next_candle['High']:
                gaps.append({
                    'type': 'bearish_fvg',
                    'top': prev_candle['Low'],
                    'bottom': next_candle['High'],
                    'index': i
                })
        
        return {
            'active_gap': len(gaps) > 0,
            'gaps_count': len(gaps),
            'latest_gap': gaps[-1] if gaps else None
        }
    
    def _apply_enhanced_filters(self, df, current, signal_type):
        """Aplica filtros mejorados"""
        
        try:
            analysis = {
                'score': 0.5,
                'confirmation': False,
                'details': {}
            }
            
            filters_passed = 0
            total_filters = 0
            
            # 1. Trend Filter
            if self.optimization_config['enhanced_filters']['trend_filter']:
                trend_confirmation = self._check_trend_filter(df, current, signal_type)
                analysis['details']['trend_filter'] = trend_confirmation
                if trend_confirmation:
                    filters_passed += 1
                total_filters += 1
            
            # 2. Volatility Filter
            if self.optimization_config['enhanced_filters']['volatility_filter']:
                volatility_confirmation = self._check_volatility_filter(df, current)
                analysis['details']['volatility_filter'] = volatility_confirmation
                if volatility_confirmation:
                    filters_passed += 1
                total_filters += 1
            
            # 3. Time Filter
            if self.optimization_config['enhanced_filters']['time_filter']:
                time_confirmation = self._check_time_filter()
                analysis['details']['time_filter'] = time_confirmation
                if time_confirmation:
                    filters_passed += 1
                total_filters += 1
            
            # Calcular score basado en filtros pasados
            if total_filters > 0:
                filter_ratio = filters_passed / total_filters
                analysis['score'] = filter_ratio
                analysis['confirmation'] = filter_ratio >= 0.67  # 2/3 filtros
                analysis['details']['filters_passed'] = f'{filters_passed}/{total_filters}'
            
            return analysis
            
        except Exception as e:
            return {'score': 0.5, 'confirmation': False, 'details': {'error': str(e)}}
    
    def _check_trend_filter(self, df, current, signal_type):
        """Verifica filtro de tendencia"""
        
        if len(df) < 20:
            return False
        
        # EMAs para determinar tendencia
        ema_20 = df['Close'].ewm(span=20).mean().iloc[-1]
        ema_50 = df['Close'].ewm(span=50).mean().iloc[-1] if len(df) >= 50 else ema_20
        
        current_price = current['Close']
        
        # Para LONG: precio > EMA20 > EMA50
        if signal_type == 'LONG':
            return current_price > ema_20 and ema_20 > ema_50
        
        # Para SHORT: precio < EMA20 < EMA50
        elif signal_type == 'SHORT':
            return current_price < ema_20 and ema_20 < ema_50
        
        return False
    
    def _check_volatility_filter(self, df, current):
        """Verifica filtro de volatilidad"""
        
        if len(df) < 14:
            return True  # Default pass si no hay datos suficientes
        
        # ATR para medir volatilidad
        try:
            atr = current.get('ATR', 0)
            if atr == 0:
                return True
            
            # Volatilidad óptima: ni muy alta ni muy baja
            atr_pct = atr / current['Close']
            
            # Rango óptimo: 1.5% - 6% de volatilidad diaria
            return 0.015 <= atr_pct <= 0.06
            
        except:
            return True
    
    def _check_time_filter(self):
        """Verifica filtro de tiempo (horarios de mayor liquidez)"""
        
        now = datetime.now()
        hour = now.hour
        
        # Horarios de alta liquidez en crypto (24/7 pero con picos)
        # 8-12 (Asia), 14-18 (Europa), 20-24 (US)
        high_liquidity_hours = list(range(8, 12)) + list(range(14, 18)) + list(range(20, 24))
        
        return hour in high_liquidity_hours
    
    def _calculate_optimized_score(self, original_score, optimizations):
        """Calcula score optimizado"""
        
        try:
            # Score base
            optimized_score = original_score
            optimization_details = {
                'original_score': original_score,
                'optimizations': {},
                'total_adjustment': 0
            }
            
            # Aplicar cada optimización
            total_adjustment = 0
            
            for component, analysis in optimizations.items():
                if analysis and 'score' in analysis:
                    weight = self.optimization_config.get(component, {}).get('weight', 0.1)
                    component_score = analysis['score']
                    
                    # Ajuste basado en score del componente
                    if component_score >= 0.8:
                        adjustment = weight * 0.5  # +5% por componente excelente
                    elif component_score >= 0.6:
                        adjustment = weight * 0.2  # +2% por componente bueno
                    elif component_score <= 0.3:
                        adjustment = -weight * 0.3  # -3% por componente malo
                    else:
                        adjustment = 0  # Neutral
                    
                    total_adjustment += adjustment
                    
                    optimization_details['optimizations'][component] = {
                        'score': component_score,
                        'weight': weight,
                        'adjustment': adjustment,
                        'confirmation': analysis.get('confirmation', False)
                    }
            
            # Aplicar ajuste total
            optimized_score = original_score * (1 + total_adjustment)
            optimized_score = max(0, min(optimized_score, 10.0))  # Clamp 0-10
            
            optimization_details['total_adjustment'] = total_adjustment
            optimization_details['optimized_score'] = optimized_score
            
            return optimized_score, optimization_details
            
        except Exception as e:
            return original_score, {'error': str(e)}
    
    def _make_optimization_decision(self, optimizations, optimized_score):
        """Toma decisión final sobre la señal"""
        
        # Contar confirmaciones
        confirmations = 0
        total_components = 0
        
        for component, analysis in optimizations.items():
            if analysis and 'confirmation' in analysis:
                total_components += 1
                if analysis['confirmation']:
                    confirmations += 1
        
        confirmation_ratio = confirmations / total_components if total_components > 0 else 0
        
        # Lógica de decisión
        if optimized_score >= 8.0 and confirmation_ratio >= 0.6:
            return 'ENHANCED'  # Señal mejorada
        elif optimized_score >= 6.5 and confirmation_ratio >= 0.5:
            return 'CONFIRMED'  # Señal confirmada
        elif optimized_score < 5.0 or confirmation_ratio < 0.3:
            return 'REJECTED'  # Señal rechazada
        else:
            return 'STANDARD'  # Señal estándar (sin cambios)
    
    def print_optimization_analysis(self, df, current, prev, signal_type, original_score):
        """Imprime análisis completo de optimización"""
        
        print(f"🎯 ENTRY SIGNALS OPTIMIZER")
        print("="*60)
        print(f"Original Signal: {signal_type}, Score: {original_score}")
        print("="*60)
        
        decision, optimized_score, details = self.optimize_entry_signal(
            df, current, prev, signal_type, original_score
        )
        
        print(f"📊 RESULTADO DE OPTIMIZACIÓN:")
        print(f"• Decisión: {decision}")
        print(f"• Score Original: {original_score}")
        print(f"• Score Optimizado: {optimized_score:.2f}")
        print(f"• Mejora: {((optimized_score/original_score - 1) * 100):+.1f}%")
        
        if isinstance(details, dict) and 'optimizations' in details:
            print(f"\n📋 ANÁLISIS POR COMPONENTE:")
            
            for component, analysis in details['optimizations'].items():
                score = analysis['score']
                confirmation = "✅" if analysis['confirmation'] else "❌"
                adjustment = analysis['adjustment']
                
                print(f"• {component.replace('_', ' ').title()}:")
                print(f"  Score: {score:.2f}, Confirmación: {confirmation}, Ajuste: {adjustment:+.3f}")
        
        return decision, optimized_score, details

def demo_entry_optimizer():
    """Demo del optimizador de señales"""
    
    optimizer = EntrySignalsOptimizer()
    
    print("🎯 ENTRY SIGNALS OPTIMIZER DEMO")
    print("="*70)
    print("Optimizando señales para mejorar Win Rate del 45.6% al 60%+")
    print("="*70)
    
    # Obtener datos de prueba
    try:
        import yfinance as yf
        ticker = yf.Ticker("BTC-USD")
        data = ticker.history(period="30d", interval="1h")
        
        # Añadir indicadores básicos
        data['RSI'] = 50  # Simplificado
        data['ATR'] = data['High'] - data['Low']
        
        if len(data) >= 50:
            current = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Test con señal LONG
            print("🔍 TESTING SEÑAL LONG:")
            decision, score, details = optimizer.print_optimization_analysis(
                data, current, prev, 'LONG', 7.2
            )
            
            print(f"\n" + "="*70)
            
            # Test con señal SHORT
            print("🔍 TESTING SEÑAL SHORT:")
            decision, score, details = optimizer.print_optimization_analysis(
                data, current, prev, 'SHORT', 6.8
            )
        
        else:
            print("⚠️ Datos insuficientes para demo completo")
            
    except Exception as e:
        print(f"⚠️ Error en demo: {e}")
    
    return optimizer

if __name__ == "__main__":
    demo_entry_optimizer()