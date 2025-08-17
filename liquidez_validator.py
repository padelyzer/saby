#!/usr/bin/env python3
"""
Validador de Liquidez para Señales de Trading
Análisis de pools de liquidez y coherencia con movimiento de precio
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class LiquidezValidator:
    """
    Validador de liquidez y coherencia de señales
    """
    
    def __init__(self):
        self.config = {
            # Thresholds de liquidez
            'min_avg_volume_usd': 10_000_000,    # $10M volumen promedio mínimo
            'volume_spike_threshold': 2.0,        # 2x volumen normal = spike
            'volume_consistency_periods': 5,      # Períodos para validar consistencia
            
            # Análisis de profundidad (simulado con precio)
            'price_impact_threshold': 0.005,      # 0.5% impacto máximo aceptable
            'spread_consistency_weight': 0.15,    # 15% del score de liquidez
            
            # Validación de coherencia
            'coherence_weight': 0.20,            # 20% del score total de señal
            'min_coherence_score': 0.6,          # Score mínimo de coherencia
        }
    
    def analyze_liquidity_coherence(self, df, signal_type, entry_price):
        """
        Analiza coherencia entre liquidez y dirección de señal
        """
        
        if len(df) < 10:
            return None
        
        current = df.iloc[-1]
        
        # 1. Análisis de volumen y liquidez
        liquidity_score = self._analyze_volume_patterns(df, signal_type)
        
        # 2. Análisis de impacto de precio
        price_impact_score = self._analyze_price_impact(df, entry_price)
        
        # 3. Análisis de coherencia direccional
        directional_coherence = self._analyze_directional_coherence(df, signal_type)
        
        # 4. Consistencia temporal
        temporal_consistency = self._analyze_temporal_consistency(df, signal_type)
        
        # 5. Score consolidado de liquidez
        total_liquidity_score = (
            liquidity_score * 0.30 +
            price_impact_score * 0.25 +
            directional_coherence * 0.30 +
            temporal_consistency * 0.15
        )
        
        # Detalles para debugging
        details = {
            'liquidity_score': liquidity_score,
            'price_impact_score': price_impact_score,
            'directional_coherence': directional_coherence,
            'temporal_consistency': temporal_consistency,
            'total_score': total_liquidity_score,
            'is_coherent': total_liquidity_score >= self.config['min_coherence_score']
        }
        
        return total_liquidity_score, details
    
    def _analyze_volume_patterns(self, df, signal_type):
        """Analiza patrones de volumen para validar liquidez"""
        
        if len(df) < 5:
            return 0.5  # Score neutral por falta de datos
        
        score = 0.0
        
        # 1. Volumen promedio en USD (estimado)
        recent_volume = df['Volume'].tail(5).mean()
        avg_price = df['Close'].tail(5).mean()
        volume_usd_estimated = recent_volume * avg_price
        
        if volume_usd_estimated >= self.config['min_avg_volume_usd']:
            score += 0.3  # Liquidez suficiente
        elif volume_usd_estimated >= self.config['min_avg_volume_usd'] * 0.5:
            score += 0.15  # Liquidez moderada
        
        # 2. Consistencia de volumen (no spikes extremos que indiquen manipulación)
        volume_ratio = df['Volume_Ratio'].iloc[-1]
        
        if signal_type == 'LONG':
            # Para LONG, preferimos volumen moderado creciente
            if 1.2 <= volume_ratio <= 2.5:
                score += 0.25  # Volumen óptimo para LONG
            elif 1.0 <= volume_ratio <= 3.0:
                score += 0.15  # Volumen aceptable
            else:
                score -= 0.1   # Volumen problemático (muy alto o muy bajo)
        
        else:  # SHORT
            # Para SHORT, aceptamos volumen más alto (ventas)
            if 1.5 <= volume_ratio <= 3.0:
                score += 0.25  # Volumen óptimo para SHORT
            elif 1.0 <= volume_ratio <= 4.0:
                score += 0.15  # Volumen aceptable
            else:
                score -= 0.1   # Volumen problemático
        
        # 3. Progresión del volumen (coherencia con dirección)
        volume_trend = self._calculate_volume_trend(df, signal_type)
        score += volume_trend * 0.25
        
        # 4. Distribución temporal del volumen
        volume_distribution = self._analyze_volume_distribution(df)
        score += volume_distribution * 0.2
        
        return max(0, min(score, 1.0))
    
    def _calculate_volume_trend(self, df, signal_type):
        """Calcula tendencia de volumen coherente con señal"""
        
        if len(df) < 3:
            return 0
        
        # Volumen en últimos 3 períodos
        recent_volumes = df['Volume'].tail(3).values
        
        if signal_type == 'LONG':
            # Para LONG, volumen gradualmente creciente es positivo
            if recent_volumes[2] > recent_volumes[1] > recent_volumes[0]:
                return 0.8  # Volumen creciente gradual
            elif recent_volumes[2] > recent_volumes[0]:
                return 0.4  # Volumen generalmente creciente
            else:
                return 0.0  # Volumen decreciente (negativo para LONG)
        
        else:  # SHORT
            # Para SHORT, volumen alto reciente es coherente
            if recent_volumes[2] > recent_volumes[1]:
                return 0.6  # Volumen reciente alto
            elif recent_volumes[2] > np.mean(recent_volumes):
                return 0.3  # Volumen sobre promedio
            else:
                return 0.0  # Volumen bajo (menos coherente para SHORT)
    
    def _analyze_volume_distribution(self, df):
        """Analiza distribución temporal del volumen"""
        
        if len(df) < 10:
            return 0.5
        
        # Volumen en diferentes momentos del día (si tenemos datos horarios)
        volumes = df['Volume'].tail(10)
        
        # Coeficiente de variación del volumen
        vol_cv = volumes.std() / volumes.mean() if volumes.mean() > 0 else 2.0
        
        # Distribución saludable: no demasiado errática
        if 0.3 <= vol_cv <= 1.0:
            return 0.8  # Distribución saludable
        elif 0.2 <= vol_cv <= 1.5:
            return 0.5  # Distribución aceptable
        else:
            return 0.2  # Distribución problemática (muy errática o muy plana)
    
    def _analyze_price_impact(self, df, entry_price):
        """Analiza impacto de precio y profundidad simulada"""
        
        if len(df) < 3:
            return 0.5
        
        score = 0.0
        current = df.iloc[-1]
        
        # 1. Spread implícito (High-Low como proxy del spread)
        daily_range = (current['High'] - current['Low']) / current['Close']
        
        if daily_range <= 0.02:  # Spread bajo (2%)
            score += 0.4
        elif daily_range <= 0.05:  # Spread moderado (5%)
            score += 0.2
        else:
            score += 0.0  # Spread alto (poca liquidez)
        
        # 2. Estabilidad de precio alrededor del entry
        price_stability = self._calculate_price_stability(df, entry_price)
        score += price_stability * 0.3
        
        # 3. Ausencia de gaps extremos
        gap_analysis = self._analyze_price_gaps(df)
        score += gap_analysis * 0.3
        
        return max(0, min(score, 1.0))
    
    def _calculate_price_stability(self, df, entry_price):
        """Calcula estabilidad de precio como proxy de profundidad"""
        
        if len(df) < 5:
            return 0.5
        
        # Variación de precios recientes alrededor del entry
        recent_prices = df['Close'].tail(5)
        price_deviations = abs(recent_prices - entry_price) / entry_price
        
        avg_deviation = price_deviations.mean()
        
        if avg_deviation <= 0.01:  # Desviación ≤ 1%
            return 0.8  # Muy estable
        elif avg_deviation <= 0.03:  # Desviación ≤ 3%
            return 0.5  # Moderadamente estable
        else:
            return 0.2  # Inestable
    
    def _analyze_price_gaps(self, df):
        """Analiza gaps de precio como indicador de liquidez"""
        
        if len(df) < 3:
            return 0.5
        
        # Calcular gaps entre períodos
        opens = df['Open'].tail(3)
        prev_closes = df['Close'].tail(3).shift(1)
        
        gaps = abs(opens - prev_closes) / prev_closes
        gaps = gaps.dropna()
        
        if len(gaps) == 0:
            return 0.5
        
        max_gap = gaps.max()
        
        if max_gap <= 0.005:  # Gap ≤ 0.5%
            return 0.8  # Liquidez buena
        elif max_gap <= 0.02:  # Gap ≤ 2%
            return 0.5  # Liquidez moderada
        else:
            return 0.2  # Liquidez pobre
    
    def _analyze_directional_coherence(self, df, signal_type):
        """Analiza coherencia entre flujo de volumen y dirección"""
        
        if len(df) < 5:
            return 0.5
        
        score = 0.0
        
        # 1. Análisis de volumen vs movimiento de precio
        price_change = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
        volume_change = (df['Volume'].iloc[-1] - df['Volume'].iloc[-5]) / df['Volume'].iloc[-5]
        
        if signal_type == 'LONG':
            # Para LONG: precio subiendo + volumen subiendo = coherente
            if price_change > 0 and volume_change > 0:
                score += 0.4  # Muy coherente
            elif price_change > 0:
                score += 0.2  # Moderadamente coherente
            elif price_change < -0.01:  # Precio bajando fuerte
                score -= 0.2  # Incoherente
        
        else:  # SHORT
            # Para SHORT: precio bajando + volumen alto = coherente
            if price_change < 0 and volume_change > 0:
                score += 0.4  # Muy coherente
            elif price_change < 0:
                score += 0.2  # Moderadamente coherente
            elif price_change > 0.01:  # Precio subiendo fuerte
                score -= 0.2  # Incoherente
        
        # 2. Coherencia de patrones intraday
        intraday_coherence = self._analyze_intraday_patterns(df, signal_type)
        score += intraday_coherence * 0.3
        
        # 3. Momentum vs volumen
        momentum_coherence = self._analyze_momentum_volume_coherence(df, signal_type)
        score += momentum_coherence * 0.3
        
        return max(0, min(score, 1.0))
    
    def _analyze_intraday_patterns(self, df, signal_type):
        """Analiza patrones intraday de coherencia"""
        
        if len(df) < 3:
            return 0.5
        
        # Análisis de velas: body vs shadows
        recent_candles = df.tail(3)
        
        coherent_candles = 0
        for _, candle in recent_candles.iterrows():
            body = abs(candle['Close'] - candle['Open'])
            total_range = candle['High'] - candle['Low']
            
            if total_range > 0:
                body_ratio = body / total_range
                
                if signal_type == 'LONG':
                    # Para LONG: velas alcistas con body fuerte
                    if candle['Close'] > candle['Open'] and body_ratio > 0.5:
                        coherent_candles += 1
                    elif candle['Close'] > candle['Open']:
                        coherent_candles += 0.5
                
                else:  # SHORT
                    # Para SHORT: velas bajistas con body fuerte
                    if candle['Close'] < candle['Open'] and body_ratio > 0.5:
                        coherent_candles += 1
                    elif candle['Close'] < candle['Open']:
                        coherent_candles += 0.5
        
        return coherent_candles / len(recent_candles)
    
    def _analyze_momentum_volume_coherence(self, df, signal_type):
        """Analiza coherencia entre momentum y volumen"""
        
        if len(df) < 5:
            return 0.5
        
        # Calcular momentum de precio
        price_momentum = (df['Close'].iloc[-1] - df['Close'].iloc[-3]) / df['Close'].iloc[-3]
        
        # Calcular momentum de volumen
        volume_momentum = (df['Volume'].tail(2).mean() - df['Volume'].tail(5).head(3).mean()) / df['Volume'].tail(5).head(3).mean()
        
        if signal_type == 'LONG':
            # Para LONG: momentum positivo + volumen creciente
            if price_momentum > 0 and volume_momentum > 0:
                return 0.8
            elif price_momentum > 0:
                return 0.5
            else:
                return 0.2
        
        else:  # SHORT
            # Para SHORT: momentum negativo + volumen alto
            if price_momentum < 0 and volume_momentum > 0:
                return 0.8
            elif price_momentum < 0:
                return 0.5
            else:
                return 0.2
    
    def _analyze_temporal_consistency(self, df, signal_type):
        """Analiza consistencia temporal de los patrones"""
        
        if len(df) < 10:
            return 0.5
        
        score = 0.0
        
        # 1. Consistencia de volumen en últimos períodos
        volume_consistency = self._calculate_volume_consistency(df)
        score += volume_consistency * 0.4
        
        # 2. Consistencia de dirección
        direction_consistency = self._calculate_direction_consistency(df, signal_type)
        score += direction_consistency * 0.4
        
        # 3. Ausencia de reversiones bruscas
        reversal_analysis = self._analyze_reversals(df)
        score += reversal_analysis * 0.2
        
        return max(0, min(score, 1.0))
    
    def _calculate_volume_consistency(self, df):
        """Calcula consistencia de volumen"""
        
        volumes = df['Volume'].tail(5)
        vol_mean = volumes.mean()
        vol_std = volumes.std()
        
        if vol_mean > 0:
            cv = vol_std / vol_mean
            # Coeficiente de variación saludable
            if cv <= 0.5:
                return 0.8
            elif cv <= 1.0:
                return 0.5
            else:
                return 0.2
        
        return 0.3
    
    def _calculate_direction_consistency(self, df, signal_type):
        """Calcula consistencia direccional"""
        
        if len(df) < 5:
            return 0.5
        
        price_changes = df['Close'].tail(5).pct_change().dropna()
        
        if signal_type == 'LONG':
            positive_changes = (price_changes > 0).sum()
            consistency = positive_changes / len(price_changes)
        else:  # SHORT
            negative_changes = (price_changes < 0).sum()
            consistency = negative_changes / len(price_changes)
        
        return consistency
    
    def _analyze_reversals(self, df):
        """Analiza reversiones bruscas que indican falta de liquidez"""
        
        if len(df) < 5:
            return 0.5
        
        # Buscar cambios bruscos de dirección
        price_changes = df['Close'].tail(5).pct_change().dropna()
        
        reversals = 0
        for i in range(1, len(price_changes)):
            if abs(price_changes.iloc[i]) > 0.03:  # Cambio > 3%
                if i > 0 and price_changes.iloc[i] * price_changes.iloc[i-1] < 0:  # Cambio de signo
                    reversals += 1
        
        # Menos reversiones = más consistencia
        if reversals == 0:
            return 0.8
        elif reversals <= 1:
            return 0.5
        else:
            return 0.2
    
    def integrate_liquidity_score(self, base_score, liquidity_score, liquidity_details):
        """Integra score de liquidez con score base de la señal"""
        
        if liquidity_details['is_coherent']:
            # Liquidez coherente mejora el score
            bonus = liquidity_score * self.config['coherence_weight'] * 3  # Máximo 0.6 puntos
            integrated_score = base_score + bonus
        else:
            # Liquidez incoherente penaliza el score
            penalty = (1 - liquidity_score) * self.config['coherence_weight'] * 2  # Máximo -0.4 puntos
            integrated_score = base_score - penalty
        
        # Mantener en rango válido
        return max(1.0, min(integrated_score, 10.0))

def demo_liquidez_validator():
    """Demostración del validador de liquidez"""
    
    print('💧 VALIDADOR DE LIQUIDEZ Y COHERENCIA')
    print('='*60)
    print('Componentes del análisis:')
    print('• Patrones de volumen (30%)')
    print('• Impacto de precio (25%)')  
    print('• Coherencia direccional (30%)')
    print('• Consistencia temporal (15%)')
    print('='*60)

if __name__ == "__main__":
    demo_liquidez_validator()