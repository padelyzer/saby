#!/usr/bin/env python3
"""
Sistema de Confirmaciones Modulares
Probando diferentes indicadores para mejorar precisión
"""

import pandas as pd
import numpy as np

class ConfirmacionesModulares:
    """
    Sistema modular para probar diferentes confirmaciones
    """
    
    def __init__(self, confirmacion_type='orderblocks'):
        self.confirmacion_type = confirmacion_type
        
        # Configuración por tipo de confirmación
        self.config = {
            'confirmacion_weight': 0.15,  # 15% del score total
            'min_confirmacion_score': 0.6,  # Threshold mínimo
        }
    
    def get_confirmacion_score(self, df, current, signal_type):
        """Obtiene score de confirmación según el tipo configurado"""
        
        if self.confirmacion_type == 'orderblocks':
            return self._order_blocks_confirmation(df, current, signal_type)
        elif self.confirmacion_type == 'fibonacci':
            return self._fibonacci_confirmation(df, current, signal_type)
        elif self.confirmacion_type == 'orderflow':
            return self._order_flow_confirmation(df, current, signal_type)
        elif self.confirmacion_type == 'rsi_divergence':
            return self._rsi_divergence_confirmation(df, current, signal_type)
        elif self.confirmacion_type == 'multitimeframe':
            return self._multitimeframe_confirmation(df, current, signal_type)
        else:
            return 0.5, {'type': 'none', 'score': 0.5}
    
    def _order_blocks_confirmation(self, df, current, signal_type):
        """Confirmación usando Order Blocks (Smart Money Concepts)"""
        
        if len(df) < 20:
            return 0.5, {'type': 'orderblocks', 'score': 0.5, 'reason': 'insufficient_data'}
        
        score = 0.0
        details = {'type': 'orderblocks', 'blocks_found': [], 'interactions': []}
        
        # 1. Identificar Order Blocks (zonas de alta actividad institucional)
        order_blocks = self._identify_order_blocks(df)
        details['blocks_found'] = len(order_blocks)
        
        if not order_blocks:
            return 0.3, details
        
        current_price = current['Close']
        
        # 2. Evaluar interacción con Order Blocks
        for block in order_blocks:
            distance_to_block = abs(current_price - block['price']) / current_price
            
            # Si estamos cerca de un order block relevante
            if distance_to_block <= 0.02:  # Dentro del 2%
                
                if signal_type == 'LONG':
                    # Para LONG: buscar soporte en order block bajista (inversión)
                    if block['type'] == 'bearish' and current_price >= block['low']:
                        score += 0.4  # Rebote desde zona de demanda
                        details['interactions'].append(f"Support at {block['price']:.4f}")
                        
                        # Bonus por fortaleza del block
                        if block['strength'] >= 0.8:
                            score += 0.2
                        elif block['strength'] >= 0.6:
                            score += 0.1
                
                elif signal_type == 'SHORT':
                    # Para SHORT: buscar resistencia en order block alcista
                    if block['type'] == 'bullish' and current_price <= block['high']:
                        score += 0.4  # Rechazo desde zona de oferta
                        details['interactions'].append(f"Resistance at {block['price']:.4f}")
                        
                        if block['strength'] >= 0.8:
                            score += 0.2
                        elif block['strength'] >= 0.6:
                            score += 0.1
        
        # 3. Evaluar contexto de mercado
        market_structure = self._analyze_market_structure(df)
        if signal_type == 'LONG' and market_structure == 'bullish_structure':
            score += 0.2
        elif signal_type == 'SHORT' and market_structure == 'bearish_structure':
            score += 0.2
        
        # 4. Timing de entrada
        timing_score = self._evaluate_entry_timing(df, current, signal_type)
        score += timing_score * 0.2
        
        final_score = min(score, 1.0)
        details['score'] = final_score
        
        return final_score, details
    
    def _identify_order_blocks(self, df):
        """Identifica Order Blocks en el gráfico"""
        
        blocks = []
        
        # Buscar zonas de alto volumen y reversión
        for i in range(10, len(df) - 5):
            current_bar = df.iloc[i]
            
            # Identificar posibles order blocks por cambio de estructura
            high_volume = current_bar['Volume'] > df['Volume'].rolling(20).mean().iloc[i] * 1.5
            
            if high_volume:
                # Analizar comportamiento después del volumen alto
                future_bars = df.iloc[i+1:i+6]
                
                if len(future_bars) >= 3:
                    # Order Block Alcista: Volumen alto seguido de movimiento alcista
                    if (future_bars['Close'].iloc[-1] > current_bar['Close'] and
                        future_bars['Close'].min() >= current_bar['Low'] * 0.998):
                        
                        strength = self._calculate_block_strength(df, i, 'bullish')
                        blocks.append({
                            'type': 'bullish',
                            'price': current_bar['Close'],
                            'high': current_bar['High'],
                            'low': current_bar['Low'],
                            'index': i,
                            'strength': strength,
                            'volume': current_bar['Volume']
                        })
                    
                    # Order Block Bajista: Volumen alto seguido de movimiento bajista
                    elif (future_bars['Close'].iloc[-1] < current_bar['Close'] and
                          future_bars['Close'].max() <= current_bar['High'] * 1.002):
                        
                        strength = self._calculate_block_strength(df, i, 'bearish')
                        blocks.append({
                            'type': 'bearish',
                            'price': current_bar['Close'],
                            'high': current_bar['High'],
                            'low': current_bar['Low'],
                            'index': i,
                            'strength': strength,
                            'volume': current_bar['Volume']
                        })
        
        # Mantener solo los blocks más recientes y fuertes
        blocks = sorted(blocks, key=lambda x: (x['strength'], x['index']), reverse=True)
        return blocks[:5]  # Top 5 blocks
    
    def _calculate_block_strength(self, df, block_index, block_type):
        """Calcula la fortaleza de un order block"""
        
        if block_index >= len(df) - 5:
            return 0.3
        
        strength = 0.0
        block_bar = df.iloc[block_index]
        
        # 1. Fortaleza por volumen
        avg_volume = df['Volume'].rolling(20).mean().iloc[block_index]
        volume_ratio = block_bar['Volume'] / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio >= 3.0:
            strength += 0.4
        elif volume_ratio >= 2.0:
            strength += 0.25
        elif volume_ratio >= 1.5:
            strength += 0.1
        
        # 2. Fortaleza por reacción del precio
        future_bars = df.iloc[block_index+1:block_index+6]
        if len(future_bars) >= 3:
            price_reaction = abs(future_bars['Close'].iloc[-1] - block_bar['Close']) / block_bar['Close']
            
            if price_reaction >= 0.03:  # Reacción fuerte 3%+
                strength += 0.3
            elif price_reaction >= 0.015:  # Reacción moderada 1.5%+
                strength += 0.2
            elif price_reaction >= 0.005:  # Reacción débil 0.5%+
                strength += 0.1
        
        # 3. Fortaleza por posición en la estructura
        if self._is_structure_break(df, block_index, block_type):
            strength += 0.3
        
        return min(strength, 1.0)
    
    def _is_structure_break(self, df, index, block_type):
        """Verifica si hay ruptura de estructura"""
        
        if index < 10 or index >= len(df) - 3:
            return False
        
        # Analizar highs y lows recientes
        recent_highs = df['High'].iloc[index-10:index].max()
        recent_lows = df['Low'].iloc[index-10:index].min()
        current_bar = df.iloc[index]
        
        if block_type == 'bullish':
            # Ruptura alcista: nuevo high después de consolidación
            return current_bar['High'] > recent_highs * 1.001
        else:
            # Ruptura bajista: nuevo low después de consolidación
            return current_bar['Low'] < recent_lows * 0.999
    
    def _analyze_market_structure(self, df):
        """Analiza estructura de mercado (Higher Highs/Lower Lows)"""
        
        if len(df) < 20:
            return 'neutral'
        
        # Analizar últimos 20 períodos
        recent_data = df.tail(20)
        
        # Identificar swings
        highs = recent_data['High'].rolling(3, center=True).max()
        lows = recent_data['Low'].rolling(3, center=True).min()
        
        # Contar Higher Highs y Lower Lows
        hh_count = 0  # Higher Highs
        ll_count = 0  # Lower Lows
        
        for i in range(3, len(recent_data) - 3):
            current_high = recent_data['High'].iloc[i]
            current_low = recent_data['Low'].iloc[i]
            
            prev_high = recent_data['High'].iloc[i-3:i].max()
            prev_low = recent_data['Low'].iloc[i-3:i].min()
            
            if current_high > prev_high:
                hh_count += 1
            if current_low < prev_low:
                ll_count += 1
        
        if hh_count > ll_count + 1:
            return 'bullish_structure'
        elif ll_count > hh_count + 1:
            return 'bearish_structure'
        else:
            return 'neutral'
    
    def _evaluate_entry_timing(self, df, current, signal_type):
        """Evalúa timing de entrada"""
        
        score = 0.0
        
        # 1. Momentum reciente
        if len(df) >= 3:
            recent_momentum = (current['Close'] - df.iloc[-3]['Close']) / df.iloc[-3]['Close']
            
            if signal_type == 'LONG':
                if 0.005 <= recent_momentum <= 0.02:  # Momentum moderado alcista
                    score += 0.5
                elif recent_momentum > 0:
                    score += 0.3
            else:  # SHORT
                if -0.02 <= recent_momentum <= -0.005:  # Momentum moderado bajista
                    score += 0.5
                elif recent_momentum < 0:
                    score += 0.3
        
        # 2. Posición relativa en la vela
        if signal_type == 'LONG':
            # Para LONG: mejor entrada cerca del low de la vela
            position_in_candle = (current['Close'] - current['Low']) / (current['High'] - current['Low'])
            if position_in_candle <= 0.3:  # Cerca del low
                score += 0.5
            elif position_in_candle <= 0.5:
                score += 0.3
        else:  # SHORT
            # Para SHORT: mejor entrada cerca del high de la vela
            position_in_candle = (current['High'] - current['Close']) / (current['High'] - current['Low'])
            if position_in_candle <= 0.3:  # Cerca del high
                score += 0.5
            elif position_in_candle <= 0.5:
                score += 0.3
        
        return score
    
    def _fibonacci_confirmation(self, df, current, signal_type):
        """Confirmación usando niveles de Fibonacci"""
        
        if len(df) < 30:
            return 0.5, {'type': 'fibonacci', 'score': 0.5}
        
        score = 0.0
        details = {'type': 'fibonacci', 'levels': [], 'retracements': []}
        
        # Encontrar swing high y swing low recientes
        swing_high, swing_low = self._find_recent_swing(df)
        
        if swing_high is None or swing_low is None:
            return 0.4, details
        
        # Calcular niveles de Fibonacci
        fib_levels = self._calculate_fibonacci_levels(swing_high, swing_low)
        details['levels'] = fib_levels
        
        current_price = current['Close']
        
        # Evaluar proximidad a niveles clave
        for level_name, level_price in fib_levels.items():
            distance = abs(current_price - level_price) / current_price
            
            if distance <= 0.01:  # Dentro del 1%
                if signal_type == 'LONG':
                    # Para LONG: rebote desde niveles de soporte (50%, 61.8%)
                    if level_name in ['50.0%', '61.8%'] and current_price >= level_price:
                        score += 0.6
                        details['retracements'].append(f"Support at {level_name}")
                    elif level_name in ['38.2%', '23.6%'] and current_price >= level_price:
                        score += 0.4
                        details['retracements'].append(f"Weak support at {level_name}")
                
                elif signal_type == 'SHORT':
                    # Para SHORT: rechazo desde niveles de resistencia
                    if level_name in ['50.0%', '61.8%'] and current_price <= level_price:
                        score += 0.6
                        details['retracements'].append(f"Resistance at {level_name}")
                    elif level_name in ['38.2%', '23.6%'] and current_price <= level_price:
                        score += 0.4
                        details['retracements'].append(f"Weak resistance at {level_name}")
        
        final_score = min(score, 1.0)
        details['score'] = final_score
        
        return final_score, details
    
    def _find_recent_swing(self, df):
        """Encuentra swing high y swing low recientes"""
        
        # Buscar en los últimos 50 períodos
        recent_data = df.tail(50)
        
        # Encontrar el high y low más significativos
        swing_high_idx = recent_data['High'].idxmax()
        swing_low_idx = recent_data['Low'].idxmin()
        
        swing_high = recent_data.loc[swing_high_idx, 'High']
        swing_low = recent_data.loc[swing_low_idx, 'Low']
        
        return swing_high, swing_low
    
    def _calculate_fibonacci_levels(self, swing_high, swing_low):
        """Calcula niveles de retroceso de Fibonacci"""
        
        diff = swing_high - swing_low
        
        levels = {
            '0.0%': swing_low,
            '23.6%': swing_low + (diff * 0.236),
            '38.2%': swing_low + (diff * 0.382),
            '50.0%': swing_low + (diff * 0.500),
            '61.8%': swing_low + (diff * 0.618),
            '78.6%': swing_low + (diff * 0.786),
            '100.0%': swing_high
        }
        
        return levels
    
    def _order_flow_confirmation(self, df, current, signal_type):
        """Confirmación usando Order Flow básico"""
        
        score = 0.0
        details = {'type': 'orderflow', 'flow_direction': 'neutral'}
        
        if len(df) < 5:
            return 0.5, details
        
        # Análisis básico de order flow usando precio y volumen
        recent_bars = df.tail(5)
        
        # 1. Direccionalidad del flujo
        buying_pressure = 0
        selling_pressure = 0
        
        for _, bar in recent_bars.iterrows():
            # Estimar buying/selling pressure
            close_position = (bar['Close'] - bar['Low']) / (bar['High'] - bar['Low']) if bar['High'] != bar['Low'] else 0.5
            
            if close_position > 0.6:  # Cierre en zona alta
                buying_pressure += bar['Volume'] * close_position
            elif close_position < 0.4:  # Cierre en zona baja
                selling_pressure += bar['Volume'] * (1 - close_position)
        
        # 2. Evaluar coherencia con signal_type
        total_pressure = buying_pressure + selling_pressure
        if total_pressure > 0:
            net_buying = buying_pressure / total_pressure
            
            if signal_type == 'LONG':
                if net_buying >= 0.65:  # Flujo comprador dominante
                    score += 0.7
                    details['flow_direction'] = 'bullish'
                elif net_buying >= 0.55:
                    score += 0.4
                    details['flow_direction'] = 'slightly_bullish'
            
            elif signal_type == 'SHORT':
                if net_buying <= 0.35:  # Flujo vendedor dominante
                    score += 0.7
                    details['flow_direction'] = 'bearish'
                elif net_buying <= 0.45:
                    score += 0.4
                    details['flow_direction'] = 'slightly_bearish'
        
        # 3. Momentum del flujo
        current_pressure = (current['Close'] - current['Low']) / (current['High'] - current['Low']) if current['High'] != current['Low'] else 0.5
        
        if signal_type == 'LONG' and current_pressure > 0.7:
            score += 0.3
        elif signal_type == 'SHORT' and current_pressure < 0.3:
            score += 0.3
        
        final_score = min(score, 1.0)
        details['score'] = final_score
        
        return final_score, details
    
    def _rsi_divergence_confirmation(self, df, current, signal_type):
        """Confirmación usando divergencias RSI"""
        
        score = 0.0
        details = {'type': 'rsi_divergence', 'divergence_found': False}
        
        if len(df) < 20:
            return 0.5, details
        
        # Buscar divergencias en los últimos 15 períodos
        recent_data = df.tail(15)
        
        # Encontrar peaks y troughs
        price_peaks = []
        rsi_peaks = []
        
        for i in range(2, len(recent_data) - 2):
            # Peak en precio
            if (recent_data.iloc[i]['High'] > recent_data.iloc[i-1]['High'] and 
                recent_data.iloc[i]['High'] > recent_data.iloc[i+1]['High']):
                price_peaks.append((i, recent_data.iloc[i]['High'], recent_data.iloc[i]['RSI']))
            
            # Trough en precio
            if (recent_data.iloc[i]['Low'] < recent_data.iloc[i-1]['Low'] and 
                recent_data.iloc[i]['Low'] < recent_data.iloc[i+1]['Low']):
                rsi_peaks.append((i, recent_data.iloc[i]['Low'], recent_data.iloc[i]['RSI']))
        
        # Buscar divergencias
        if len(price_peaks) >= 2:
            # Divergencia bajista para SHORT
            if signal_type == 'SHORT':
                last_peak = price_peaks[-1]
                prev_peak = price_peaks[-2]
                
                if (last_peak[1] > prev_peak[1] and  # Higher High en precio
                    last_peak[2] < prev_peak[2]):    # Lower High en RSI
                    score += 0.8
                    details['divergence_found'] = True
                    details['divergence_type'] = 'bearish'
        
        if len(rsi_peaks) >= 2:
            # Divergencia alcista para LONG
            if signal_type == 'LONG':
                last_trough = rsi_peaks[-1]
                prev_trough = rsi_peaks[-2]
                
                if (last_trough[1] < prev_trough[1] and  # Lower Low en precio
                    last_trough[2] > prev_trough[2]):    # Higher Low en RSI
                    score += 0.8
                    details['divergence_found'] = True
                    details['divergence_type'] = 'bullish'
        
        final_score = min(score, 1.0)
        details['score'] = final_score
        
        return final_score, details
    
    def _multitimeframe_confirmation(self, df, current, signal_type):
        """Confirmación multi-timeframe simplificada"""
        
        score = 0.0
        details = {'type': 'multitimeframe', 'timeframes': {}}
        
        if len(df) < 50:
            return 0.5, details
        
        # Simular diferentes timeframes usando diferentes períodos
        timeframes = {
            'short': 5,   # 5 períodos (corto plazo)
            'medium': 15, # 15 períodos (medio plazo)
            'long': 30    # 30 períodos (largo plazo)
        }
        
        confirmations = 0
        total_timeframes = len(timeframes)
        
        for tf_name, periods in timeframes.items():
            if len(df) >= periods:
                # Analizar tendencia en este timeframe
                tf_data = df.tail(periods)
                trend = self._analyze_trend(tf_data)
                
                details['timeframes'][tf_name] = trend
                
                # Contar confirmaciones
                if signal_type == 'LONG' and trend in ['bullish', 'slightly_bullish']:
                    confirmations += 1
                elif signal_type == 'SHORT' and trend in ['bearish', 'slightly_bearish']:
                    confirmations += 1
        
        # Score basado en confirmaciones
        confirmation_ratio = confirmations / total_timeframes
        score = confirmation_ratio
        
        # Bonus por unanimidad
        if confirmation_ratio >= 0.8:
            score += 0.2
        
        final_score = min(score, 1.0)
        details['score'] = final_score
        details['confirmation_ratio'] = confirmation_ratio
        
        return final_score, details
    
    def _analyze_trend(self, df):
        """Analiza tendencia de un DataFrame"""
        
        if len(df) < 3:
            return 'neutral'
        
        # Comparar inicio vs final
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        change_pct = (end_price - start_price) / start_price
        
        # Analizar EMAs si disponibles
        if 'EMA_21' in df.columns and not df['EMA_21'].isna().all():
            ema_slope = (df['EMA_21'].iloc[-1] - df['EMA_21'].iloc[0]) / df['EMA_21'].iloc[0]
            
            if change_pct > 0.02 and ema_slope > 0.01:
                return 'bullish'
            elif change_pct > 0.005 and ema_slope > 0:
                return 'slightly_bullish'
            elif change_pct < -0.02 and ema_slope < -0.01:
                return 'bearish'
            elif change_pct < -0.005 and ema_slope < 0:
                return 'slightly_bearish'
        else:
            # Solo usar precio
            if change_pct > 0.015:
                return 'bullish'
            elif change_pct > 0.005:
                return 'slightly_bullish'
            elif change_pct < -0.015:
                return 'bearish'
            elif change_pct < -0.005:
                return 'slightly_bearish'
        
        return 'neutral'

def demo_confirmaciones():
    """Demo del sistema de confirmaciones"""
    
    print('🔧 SISTEMA DE CONFIRMACIONES MODULARES')
    print('='*60)
    print('Opciones disponibles:')
    print('1. Order Blocks (Smart Money Concepts)')
    print('2. Fibonacci Retracements')
    print('3. Order Flow básico')
    print('4. RSI Divergences')
    print('5. Multi-timeframe simple')
    print('='*60)

if __name__ == "__main__":
    demo_confirmaciones()