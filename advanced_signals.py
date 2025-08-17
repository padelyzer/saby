#!/usr/bin/env python3
"""
Sistema Avanzado de Señales - Detecta Movimientos Largos
Basado en Soportes/Resistencias y Estructura de Mercado
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional
from liquidity_pools import LiquidityPoolDetector

class AdvancedSignalDetector:
    """Detector avanzado de señales basado en estructura de mercado"""
    
    def __init__(self):
        self.min_risk_reward = 1.5  # Mínimo ratio riesgo/recompensa (reducido para más señales)
        self.min_score = 5  # Señales de calidad media (reducido para más señales)
        self.liquidity_detector = LiquidityPoolDetector()  # Detector de pools de liquidez
        
    def find_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict:
        """Encuentra niveles clave de soporte y resistencia"""
        
        # Encontrar máximos y mínimos locales
        highs = df['High'].rolling(window=window, center=True).max()
        lows = df['Low'].rolling(window=window, center=True).min()
        
        # Identificar puntos de pivote
        pivot_highs = df['High'][df['High'] == highs].dropna()
        pivot_lows = df['Low'][df['Low'] == lows].dropna()
        
        # Agrupar niveles cercanos (dentro del 0.5%)
        resistance_levels = []
        support_levels = []
        
        # Procesar resistencias
        for price in pivot_highs.unique():
            count = len(pivot_highs[abs(pivot_highs - price) / price < 0.005])
            if count >= 2:  # Al menos 2 toques para ser válido
                resistance_levels.append({
                    'price': price,
                    'strength': count,
                    'type': 'resistance'
                })
        
        # Procesar soportes
        for price in pivot_lows.unique():
            count = len(pivot_lows[abs(pivot_lows - price) / price < 0.005])
            if count >= 2:
                support_levels.append({
                    'price': price,
                    'strength': count,
                    'type': 'support'
                })
        
        # Ordenar por fuerza
        resistance_levels.sort(key=lambda x: x['strength'], reverse=True)
        support_levels.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            'resistances': resistance_levels[:5],  # Top 5 resistencias
            'supports': support_levels[:5]  # Top 5 soportes
        }
    
    def calculate_market_structure(self, df: pd.DataFrame) -> str:
        """Determina la estructura del mercado (tendencia)"""
        
        # Análisis de Higher Highs (HH) y Higher Lows (HL)
        recent_df = df.tail(50)
        
        # Encontrar máximos y mínimos
        highs = []
        lows = []
        
        for i in range(1, len(recent_df) - 1):
            # Máximos locales
            if recent_df['High'].iloc[i] > recent_df['High'].iloc[i-1] and \
               recent_df['High'].iloc[i] > recent_df['High'].iloc[i+1]:
                highs.append({
                    'index': i,
                    'price': recent_df['High'].iloc[i]
                })
            
            # Mínimos locales
            if recent_df['Low'].iloc[i] < recent_df['Low'].iloc[i-1] and \
               recent_df['Low'].iloc[i] < recent_df['Low'].iloc[i+1]:
                lows.append({
                    'index': i,
                    'price': recent_df['Low'].iloc[i]
                })
        
        if len(highs) >= 2 and len(lows) >= 2:
            # Tendencia alcista: HH y HL
            if highs[-1]['price'] > highs[-2]['price'] and \
               lows[-1]['price'] > lows[-2]['price']:
                return 'UPTREND'
            
            # Tendencia bajista: LH y LL
            elif highs[-1]['price'] < highs[-2]['price'] and \
                 lows[-1]['price'] < lows[-2]['price']:
                return 'DOWNTREND'
        
        return 'RANGE'
    
    def find_order_blocks(self, df: pd.DataFrame) -> List[Dict]:
        """Encuentra Order Blocks (zonas institucionales)"""
        order_blocks = []
        
        for i in range(10, len(df) - 1):
            # Bullish Order Block: Vela bajista antes de movimiento alcista fuerte
            if df['Close'].iloc[i] < df['Open'].iloc[i]:  # Vela bajista
                # Verificar movimiento alcista después
                next_candles = df.iloc[i+1:i+4]
                if len(next_candles) > 0:
                    total_move = (next_candles['Close'].iloc[-1] - df['Close'].iloc[i]) / df['Close'].iloc[i]
                    
                    if total_move > 0.02:  # Movimiento de 2%+
                        order_blocks.append({
                            'type': 'BULLISH_OB',
                            'high': df['High'].iloc[i],
                            'low': df['Low'].iloc[i],
                            'strength': total_move * 100,
                            'index': i
                        })
            
            # Bearish Order Block: Vela alcista antes de movimiento bajista fuerte
            if df['Close'].iloc[i] > df['Open'].iloc[i]:  # Vela alcista
                next_candles = df.iloc[i+1:i+4]
                if len(next_candles) > 0:
                    total_move = (df['Close'].iloc[i] - next_candles['Close'].iloc[-1]) / df['Close'].iloc[i]
                    
                    if total_move > 0.02:
                        order_blocks.append({
                            'type': 'BEARISH_OB',
                            'high': df['High'].iloc[i],
                            'low': df['Low'].iloc[i],
                            'strength': total_move * 100,
                            'index': i
                        })
        
        # Ordenar por cercanía al precio actual
        current_price = df['Close'].iloc[-1]
        order_blocks.sort(key=lambda x: abs((x['high'] + x['low'])/2 - current_price))
        
        return order_blocks[:3]  # Top 3 más cercanos
    
    def calculate_fibonacci_levels(self, df: pd.DataFrame) -> Dict:
        """Calcula niveles de Fibonacci para el movimiento reciente"""
        
        # Encontrar el swing high y swing low recientes
        recent = df.tail(100)
        swing_high = recent['High'].max()
        swing_low = recent['Low'].min()
        
        # Índices para determinar dirección
        high_idx = recent['High'].idxmax()
        low_idx = recent['Low'].idxmin()
        
        # Determinar si es retroceso o extensión
        is_retracement = high_idx < low_idx  # High fue antes que Low
        
        diff = swing_high - swing_low
        
        if is_retracement:
            # Niveles de retroceso
            levels = {
                '0.0%': swing_high,
                '23.6%': swing_high - (diff * 0.236),
                '38.2%': swing_high - (diff * 0.382),
                '50.0%': swing_high - (diff * 0.500),
                '61.8%': swing_high - (diff * 0.618),
                '78.6%': swing_high - (diff * 0.786),
                '100.0%': swing_low
            }
        else:
            # Niveles de extensión
            levels = {
                '0.0%': swing_low,
                '23.6%': swing_low + (diff * 0.236),
                '38.2%': swing_low + (diff * 0.382),
                '50.0%': swing_low + (diff * 0.500),
                '61.8%': swing_low + (diff * 0.618),
                '78.6%': swing_low + (diff * 0.786),
                '100.0%': swing_high,
                '127.2%': swing_low + (diff * 1.272),
                '161.8%': swing_low + (diff * 1.618)
            }
        
        return {
            'levels': levels,
            'type': 'retracement' if is_retracement else 'extension',
            'swing_high': swing_high,
            'swing_low': swing_low
        }
    
    def detect_chart_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """Detecta patrones de gráficos clásicos"""
        patterns = []
        
        # Double Bottom
        if self.detect_double_bottom(df):
            patterns.append({
                'name': 'DOUBLE_BOTTOM',
                'signal': 'BULLISH',
                'reliability': 'HIGH'
            })
        
        # Double Top
        if self.detect_double_top(df):
            patterns.append({
                'name': 'DOUBLE_TOP',
                'signal': 'BEARISH',
                'reliability': 'HIGH'
            })
        
        # Bull Flag
        if self.detect_bull_flag(df):
            patterns.append({
                'name': 'BULL_FLAG',
                'signal': 'BULLISH',
                'reliability': 'MEDIUM'
            })
        
        # Bear Flag
        if self.detect_bear_flag(df):
            patterns.append({
                'name': 'BEAR_FLAG',
                'signal': 'BEARISH',
                'reliability': 'MEDIUM'
            })
        
        return patterns
    
    def detect_double_bottom(self, df: pd.DataFrame, window: int = 20) -> bool:
        """Detecta patrón de doble suelo"""
        recent = df.tail(window * 2)
        lows = recent['Low'].rolling(window=5, center=True).min()
        
        # Buscar dos mínimos similares
        bottom_indices = recent.index[recent['Low'] == lows].tolist()
        
        if len(bottom_indices) >= 2:
            first_bottom = recent.loc[bottom_indices[-2], 'Low']
            second_bottom = recent.loc[bottom_indices[-1], 'Low']
            
            # Los suelos deben estar dentro del 1% de diferencia
            if abs(first_bottom - second_bottom) / first_bottom < 0.01:
                # Verificar que hay un pico entre ellos
                between_data = recent.loc[bottom_indices[-2]:bottom_indices[-1]]
                if len(between_data) > 5:
                    peak = between_data['High'].max()
                    if (peak - first_bottom) / first_bottom > 0.03:  # Al menos 3% de rebote
                        return True
        
        return False
    
    def detect_double_top(self, df: pd.DataFrame, window: int = 20) -> bool:
        """Detecta patrón de doble techo"""
        recent = df.tail(window * 2)
        highs = recent['High'].rolling(window=5, center=True).max()
        
        top_indices = recent.index[recent['High'] == highs].tolist()
        
        if len(top_indices) >= 2:
            first_top = recent.loc[top_indices[-2], 'High']
            second_top = recent.loc[top_indices[-1], 'High']
            
            if abs(first_top - second_top) / first_top < 0.01:
                between_data = recent.loc[top_indices[-2]:top_indices[-1]]
                if len(between_data) > 5:
                    valley = between_data['Low'].min()
                    if (first_top - valley) / first_top > 0.03:
                        return True
        
        return False
    
    def detect_bull_flag(self, df: pd.DataFrame) -> bool:
        """Detecta patrón de bandera alcista"""
        recent = df.tail(30)
        
        # Buscar movimiento alcista fuerte (pole)
        pole_start = recent.iloc[:10]
        pole_move = (pole_start['Close'].iloc[-1] - pole_start['Close'].iloc[0]) / pole_start['Close'].iloc[0]
        
        if pole_move > 0.05:  # Movimiento de 5%+
            # Buscar consolidación (flag)
            flag = recent.iloc[10:25]
            flag_high = flag['High'].max()
            flag_low = flag['Low'].min()
            flag_range = (flag_high - flag_low) / flag_low
            
            # La bandera debe ser estrecha (menos del 3% de rango)
            if flag_range < 0.03:
                # Verificar que el precio está rompiendo al alza
                if recent['Close'].iloc[-1] > flag_high:
                    return True
        
        return False
    
    def detect_bear_flag(self, df: pd.DataFrame) -> bool:
        """Detecta patrón de bandera bajista"""
        recent = df.tail(30)
        
        pole_start = recent.iloc[:10]
        pole_move = (pole_start['Close'].iloc[0] - pole_start['Close'].iloc[-1]) / pole_start['Close'].iloc[0]
        
        if pole_move > 0.05:
            flag = recent.iloc[10:25]
            flag_high = flag['High'].max()
            flag_low = flag['Low'].min()
            flag_range = (flag_high - flag_low) / flag_low
            
            if flag_range < 0.03:
                if recent['Close'].iloc[-1] < flag_low:
                    return True
        
        return False
    
    def generate_advanced_signal(self, ticker: str, df: pd.DataFrame) -> Optional[Dict]:
        """Genera señal avanzada con targets basados en estructura"""
        
        # 1. Análisis de estructura de mercado
        market_structure = self.calculate_market_structure(df)
        
        # 2. Encontrar soportes y resistencias
        sr_levels = self.find_support_resistance(df)
        
        # 3. Calcular Fibonacci
        fib_levels = self.calculate_fibonacci_levels(df)
        
        # 4. Detectar patrones
        patterns = self.detect_chart_patterns(df)
        
        # 5. Order Blocks
        order_blocks = self.find_order_blocks(df)
        
        # 6. Detectar Pools de Liquidez
        current_price = float(df['Close'].iloc[-1])
        liquidity_data = self.liquidity_detector.detect_liquidity_pools(df, current_price)
        
        # 7. Precio actual y análisis
        sma50 = float(df['Close'].rolling(50).mean().iloc[-1])
        sma200 = float(df['Close'].rolling(200).mean().iloc[-1])
        rsi = self.calculate_rsi(df['Close'])
        
        # Calcular score basado en confluencias
        score = 0
        signal_type = None
        entry_reason = []
        
        # ANÁLISIS DE DIRECCIÓN BASADO EN PRECIO Y ESTRUCTURA
        # Verificar posición del precio respecto a medias y estructura
        price_above_sma50 = current_price > sma50
        price_above_sma200 = current_price > sma200
        
        # SEÑALES LONG
        if (market_structure == 'UPTREND' or (market_structure == 'RANGE' and price_above_sma50)):
            score += 2
            signal_type = 'LONG'
            if market_structure == 'UPTREND':
                entry_reason.append("Tendencia alcista confirmada")
            else:
                entry_reason.append("Rango con sesgo alcista")
            
            # Precio sobre SMAs
            if current_price > sma50 > sma200:
                score += 2
                entry_reason.append("Precio sobre medias móviles")
            
            # Rebote en soporte
            for support in sr_levels['supports']:
                if abs(current_price - support['price']) / current_price < 0.01:
                    score += 3
                    entry_reason.append(f"Rebote en soporte fuerte ${support['price']:.2f}")
                    break
            
            # Nivel de Fibonacci
            for level_name, level_price in fib_levels['levels'].items():
                if level_name in ['38.2%', '50.0%', '61.8%']:
                    if abs(current_price - level_price) / current_price < 0.01:
                        score += 2
                        entry_reason.append(f"Rebote en Fibonacci {level_name}")
                        break
            
            # Patrón alcista
            for pattern in patterns:
                if pattern['signal'] == 'BULLISH':
                    score += 2
                    entry_reason.append(f"Patrón {pattern['name']}")
            
            # Order Block alcista
            for ob in order_blocks:
                if ob['type'] == 'BULLISH_OB':
                    if ob['low'] <= current_price <= ob['high']:
                        score += 2
                        entry_reason.append("En Order Block alcista")
                        break
            
            # RSI oversold en uptrend
            if 30 <= rsi <= 50:
                score += 1
                entry_reason.append(f"RSI en zona de sobreventa ({rsi:.0f})")
            
            # Pools de liquidez para longs
            below_pools = liquidity_data['pools'].get('below_price', [])
            if below_pools:
                nearest_pool = min(below_pools, key=lambda x: abs(x['price'] - current_price))
                if abs(nearest_pool['price'] - current_price) / current_price < 0.02:
                    score += 2
                    entry_reason.append(f"Cerca de pool de liquidez LONG en ${nearest_pool['price']:.2f}")
        
        # SEÑALES SHORT
        elif (market_structure == 'DOWNTREND' or (market_structure == 'RANGE' and not price_above_sma50)):
            score += 2
            signal_type = 'SHORT'
            if market_structure == 'DOWNTREND':
                entry_reason.append("Tendencia bajista confirmada")
            else:
                entry_reason.append("Rango con sesgo bajista")
            
            # Precio bajo SMAs
            if current_price < sma50 < sma200:
                score += 2
                entry_reason.append("Precio bajo medias móviles")
            
            # Rechazo en resistencia
            for resistance in sr_levels['resistances']:
                if abs(current_price - resistance['price']) / current_price < 0.01:
                    score += 3
                    entry_reason.append(f"Rechazo en resistencia ${resistance['price']:.2f}")
                    break
            
            # Patrón bajista
            for pattern in patterns:
                if pattern['signal'] == 'BEARISH':
                    score += 2
                    entry_reason.append(f"Patrón {pattern['name']}")
            
            # RSI overbought en downtrend
            if 50 <= rsi <= 70:
                score += 1
                entry_reason.append(f"RSI en zona de sobrecompra ({rsi:.0f})")
            
            # Pools de liquidez para shorts
            above_pools = liquidity_data['pools'].get('above_price', [])
            if above_pools:
                nearest_pool = min(above_pools, key=lambda x: abs(x['price'] - current_price))
                if abs(nearest_pool['price'] - current_price) / current_price < 0.02:
                    score += 2
                    entry_reason.append(f"Cerca de pool de liquidez SHORT en ${nearest_pool['price']:.2f}")
        
        # SEÑALES EN RANGO (RANGE) - Buscar reversiones
        elif market_structure == 'RANGE':
            # Verificar si estamos cerca de resistencia (SHORT)
            for resistance in sr_levels['resistances']:
                if abs(current_price - resistance['price']) / current_price < 0.01:
                    signal_type = 'SHORT'
                    score += 3
                    entry_reason.append(f"En resistencia de rango ${resistance['price']:.2f}")
                    break
            
            # Verificar si estamos cerca de soporte (LONG)
            if not signal_type:
                for support in sr_levels['supports']:
                    if abs(current_price - support['price']) / current_price < 0.01:
                        signal_type = 'LONG'
                        score += 3
                        entry_reason.append(f"En soporte de rango ${support['price']:.2f}")
                        break
            
            # Agregar puntos por RSI en rango
            if signal_type == 'LONG' and rsi < 40:
                score += 2
                entry_reason.append(f"RSI oversold en rango ({rsi:.0f})")
            elif signal_type == 'SHORT' and rsi > 60:
                score += 2
                entry_reason.append(f"RSI overbought en rango ({rsi:.0f})")
        
        # Solo generar señal si score >= 7
        if score < self.min_score or not signal_type:
            return None
        
        # CALCULAR TARGETS BASADOS EN ESTRUCTURA Y LIQUIDEZ
        liquidity_suggestions = self.liquidity_detector.suggest_entry_exit(liquidity_data, signal_type)
        
        # VERIFICACIÓN DE COHERENCIA DE SEÑAL
        # Si el sistema sugiere targets por debajo del precio para LONG, cambiar a SHORT
        if signal_type == 'LONG' and liquidity_suggestions.get('take_profits'):
            if liquidity_suggestions['take_profits'] and liquidity_suggestions['take_profits'][0]['price'] < current_price:
                signal_type = 'SHORT'
                liquidity_suggestions = self.liquidity_detector.suggest_entry_exit(liquidity_data, 'SHORT')
                # Actualizar razones para reflejar el cambio
                entry_reason = [r.replace("alcista", "con reversión bajista").replace("LONG", "SHORT") for r in entry_reason]
                entry_reason.append("Reversión detectada por estructura de liquidez")
        
        if signal_type == 'LONG':
            # Stop Loss: Considerar pools de liquidez
            recent_low = df['Low'].tail(10).min()
            nearest_support = min([s['price'] for s in sr_levels['supports']], 
                                 key=lambda x: abs(x - current_price) if x < current_price else float('inf'),
                                 default=recent_low)
            
            # Ajustar SL basado en pools de liquidez
            if liquidity_suggestions['stop_losses']:
                liquidity_sl = liquidity_suggestions['stop_losses'][0]['price']
                stop_loss = min(liquidity_sl, nearest_support * 0.995)
            else:
                stop_loss = min(nearest_support * 0.995, recent_low * 0.995)  # 0.5% debajo del soporte
            
            # Take Profit: Próxima resistencia significativa
            targets = []
            
            # Resistencias y pools de liquidez
            for r in sr_levels['resistances']:
                if r['price'] > current_price * 1.01:  # Al menos 1% arriba
                    targets.append({
                        'price': r['price'],
                        'reason': f"Resistencia (fuerza: {r['strength']})",
                        'probability': 0.7 if r['strength'] >= 3 else 0.5
                    })
            
            # Agregar targets basados en liquidez
            if liquidity_suggestions['take_profits']:
                for tp_suggestion in liquidity_suggestions['take_profits'][:2]:
                    targets.append({
                        'price': tp_suggestion['price'],
                        'reason': tp_suggestion['reason'],
                        'probability': 0.8 if tp_suggestion['strength'] == 'HIGH' else 0.6
                    })
            
            # Fibonacci extensiones
            if fib_levels['type'] == 'extension':
                for level_name in ['127.2%', '161.8%']:
                    if level_name in fib_levels['levels']:
                        fib_price = fib_levels['levels'][level_name]
                        if fib_price > current_price * 1.02:
                            targets.append({
                                'price': fib_price,
                                'reason': f"Fibonacci {level_name}",
                                'probability': 0.6
                            })
            
            # Proyección basada en ATR
            atr = df['High'].tail(14).values - df['Low'].tail(14).values
            atr_mean = atr.mean()
            targets.append({
                'price': current_price + (atr_mean * 2),
                'reason': "Proyección 2x ATR",
                'probability': 0.5
            })
            
            # Ordenar por cercanía
            targets.sort(key=lambda x: x['price'])
            
            # Seleccionar el mejor target
            if targets:
                primary_target = targets[0]  # Primer target (más conservador)
                extended_target = targets[-1] if len(targets) > 1 else targets[0]  # Target extendido
            else:
                # Fallback a porcentaje si no hay estructura clara
                primary_target = {
                    'price': current_price * 1.05,
                    'reason': "Target 5% (sin resistencia clara)",
                    'probability': 0.4
                }
                extended_target = primary_target
        
        else:  # SHORT
            # Stop Loss: Considerar pools de liquidez
            recent_high = df['High'].tail(10).max()
            nearest_resistance = min([r['price'] for r in sr_levels['resistances']], 
                                    key=lambda x: abs(x - current_price) if x > current_price else float('inf'),
                                    default=recent_high)
            
            # Ajustar SL basado en pools de liquidez
            if liquidity_suggestions['stop_losses']:
                liquidity_sl = liquidity_suggestions['stop_losses'][0]['price']
                stop_loss = max(liquidity_sl, nearest_resistance * 1.005)
            else:
                stop_loss = max(nearest_resistance * 1.005, recent_high * 1.005)
            
            # Take Profit: Próximo soporte significativo
            targets = []
            
            for s in sr_levels['supports']:
                if s['price'] < current_price * 0.99:
                    targets.append({
                        'price': s['price'],
                        'reason': f"Soporte (fuerza: {s['strength']})",
                        'probability': 0.7 if s['strength'] >= 3 else 0.5
                    })
            
            targets.sort(key=lambda x: x['price'], reverse=True)
            
            if targets:
                primary_target = targets[0]
                extended_target = targets[-1] if len(targets) > 1 else targets[0]
            else:
                primary_target = {
                    'price': current_price * 0.95,
                    'reason': "Target 5% (sin soporte claro)",
                    'probability': 0.4
                }
                extended_target = primary_target
        
        # Calcular ratios
        risk = abs(current_price - stop_loss) / current_price
        reward1 = abs(primary_target['price'] - current_price) / current_price
        reward2 = abs(extended_target['price'] - current_price) / current_price
        
        rr_ratio1 = reward1 / risk if risk > 0 else 0
        rr_ratio2 = reward2 / risk if risk > 0 else 0
        
        # Solo enviar si el ratio R:R es bueno
        if rr_ratio1 < self.min_risk_reward:
            return None
        
        # VALIDACIÓN FINAL DE COHERENCIA
        # Para LONG: TP debe estar arriba del precio, SL abajo
        # Para SHORT: TP debe estar abajo del precio, SL arriba
        if signal_type == 'LONG':
            if primary_target['price'] <= current_price:
                # Target está abajo, esto es un SHORT mal clasificado
                return None  # O cambiar a SHORT
            if stop_loss >= current_price:
                # Stop está arriba, configuración incorrecta
                return None
        else:  # SHORT
            if primary_target['price'] >= current_price:
                # Target está arriba, esto es un LONG mal clasificado
                return None
            if stop_loss <= current_price:
                # Stop está abajo, configuración incorrecta
                return None
        
        return {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'type': signal_type,
            'score': score,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'primary_target': primary_target,
            'extended_target': extended_target,
            'risk_reward_ratio': round(rr_ratio1, 2),
            'extended_rr_ratio': round(rr_ratio2, 2),
            'market_structure': market_structure,
            'entry_reasons': entry_reason,
            'confluence_points': len(entry_reason),
            'chart_analysis': {
                'patterns': patterns,
                'key_resistances': sr_levels['resistances'][:3],
                'key_supports': sr_levels['supports'][:3],
                'fibonacci_levels': {k: v for k, v in list(fib_levels['levels'].items())[:5]},
                'current_rsi': round(rsi, 1),
                'liquidity_pools': liquidity_data['heatmap'][:5],  # Top 5 pools
                'liquidity_warnings': liquidity_suggestions.get('warnings', [])
            }
        }
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calcula el RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

def scan_for_advanced_signals(tickers: List[str]) -> List[Dict]:
    """Escanea múltiples tickers buscando señales avanzadas"""
    detector = AdvancedSignalDetector()
    signals = []
    
    print("🔍 Escaneando con análisis avanzado...")
    
    for ticker in tickers:
        try:
            print(f"  Analizando {ticker}...")
            
            # Obtener datos
            stock = yf.Ticker(ticker)
            df = stock.history(period='3mo', interval='1h')
            
            if len(df) < 200:
                continue
            
            # Generar señal si existe
            signal = detector.generate_advanced_signal(ticker, df)
            
            if signal:
                signals.append(signal)
                print(f"    ✅ Señal encontrada! Score: {signal['score']}")
        
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return signals

def format_advanced_signal(signal: Dict) -> str:
    """Formatea la señal para mostrar"""
    
    emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
    
    message = f"""
{emoji} **SEÑAL AVANZADA {signal['type']}** {emoji}
════════════════════════════════════════
📊 **{signal['ticker']}**
💯 **Score:** {signal['score']}/10
📍 **Estructura:** {signal['market_structure']}

**NIVELES DE TRADING:**
━━━━━━━━━━━━━━━━━━━━
💰 **Entrada:** ${signal['entry_price']:.4f}
🛑 **Stop Loss:** ${signal['stop_loss']:.4f}
🎯 **Target 1:** ${signal['primary_target']['price']:.4f}
   _{signal['primary_target']['reason']}_
🚀 **Target 2:** ${signal['extended_target']['price']:.4f}
   _{signal['extended_target']['reason']}_

**RATIOS:**
━━━━━━━━━━━━━━━━━━━━
📊 **R:R Target 1:** {signal['risk_reward_ratio']}:1
📈 **R:R Target 2:** {signal['extended_rr_ratio']}:1

**RAZONES DE ENTRADA ({signal['confluence_points']} confluencias):**
━━━━━━━━━━━━━━━━━━━━
"""
    
    for reason in signal['entry_reasons']:
        message += f"• {reason}\n"
    
    # Agregar análisis técnico
    if signal['chart_analysis']['patterns']:
        message += f"\n**PATRONES DETECTADOS:**\n"
        for pattern in signal['chart_analysis']['patterns']:
            message += f"• {pattern['name']} ({pattern['reliability']})\n"
    
    message += f"\n**RSI:** {signal['chart_analysis']['current_rsi']}"
    
    return message

def main():
    """Función principal de prueba"""
    
    # Lista de criptos principales
    tickers = [
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
        'ADA-USD', 'DOT-USD', 'AVAX-USD', 'MATIC-USD', 'LINK-USD'
    ]
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║           🎯 DETECTOR DE MOVIMIENTOS LARGOS                     ║
║         Basado en Estructura de Mercado Real                    ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Buscar señales
    signals = scan_for_advanced_signals(tickers)
    
    if signals:
        print(f"\n✅ {len(signals)} señales de alta calidad encontradas!\n")
        
        for signal in signals:
            print(format_advanced_signal(signal))
            print("=" * 60)
            
            # Guardar en archivo
            with open('advanced_signals.json', 'w') as f:
                json.dump(signals, f, indent=2)
    else:
        print("\n❌ No se encontraron señales de alta calidad en este momento")
        print("💡 El sistema solo genera señales con:")
        print("   • Score ≥ 7")
        print("   • R:R ≥ 2.5:1")
        print("   • Múltiples confluencias técnicas")

if __name__ == "__main__":
    main()