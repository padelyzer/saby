#!/usr/bin/env python3
"""
Sistema de Scoring Optimizado V3.0
Factores ajustados + Indicador de confirmación multi-timeframe
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class ScoringOptimizadoV3:
    """
    Sistema optimizado basado en evidencia empírica + confirmación multi-timeframe
    """
    
    def __init__(self):
        # Configuración optimizada basada en resultados empíricos
        self.config = {
            # RSI es MUY efectivo - aumentamos su peso
            'rsi_weight': 0.65,          # 65% (era 51% - AUMENTO)
            
            # Price action moderadamente efectivo
            'price_action_weight': 0.15, # 15% (era 17% - ligera reducción)
            
            # Momentum redefinido sin volumen contraproducente
            'momentum_weight': 0.08,     # 8% (era 12% - reducción)
            
            # Risk structure básico
            'risk_structure_weight': 0.02, # 2% (era 5% - reducción)
            
            # Liquidez efectiva pero se optimiza
            'liquidity_weight': 0.10,    # 10% (era 15% - reducción por eficiencia)
            
            # NUEVO: Confirmación multi-timeframe
            'confirmation_weight': 0.10, # 10% - NUEVO COMPONENTE
            'confirmation_enabled': True,
            
            # Thresholds optimizados
            'min_empirical_score': 5.8,  # Reducido de 6.0 para más trades
            'min_liquidity_score': 0.55, # Reducido de 0.6 para menos restricción
            'min_confirmation_score': 0.6, # Threshold para confirmación
            'max_score': 10.0,
            
            # Configuración de liquidez optimizada
            'liquidity_enabled': True,
            'volume_penalty': True,
            'macd_penalty': False,       # DESACTIVADO (era contraproducente)
        }
        
        # Importar validadores
        if self.config['liquidity_enabled']:
            from liquidez_validator import LiquidezValidator
            self.liquidity_validator = LiquidezValidator()
    
    def calculate_optimized_score_long(self, df, current, prev=None):
        """Calcula score optimizado para señales LONG"""
        
        if prev is None and len(df) > 1:
            prev = df.iloc[-2]
        elif prev is None:
            prev = current
        
        score = 0.0
        details = {}
        
        # 1. COMPONENTE RSI POTENCIADO (65% del score - máximo 6.5 puntos)
        rsi_score = self._calculate_rsi_score_enhanced_long(current['RSI'])
        score += rsi_score * self.config['rsi_weight'] * 10
        details['rsi_component'] = rsi_score * self.config['rsi_weight'] * 10
        
        # 2. PRICE ACTION REFINADO (15% del score)
        price_action_score = self._calculate_price_action_refined_long(df, current, prev)
        score += price_action_score * self.config['price_action_weight'] * 10
        details['price_action_component'] = price_action_score * self.config['price_action_weight'] * 10
        
        # 3. MOMENTUM OPTIMIZADO (8% del score)
        momentum_score = self._calculate_momentum_optimized_long(df, current)
        score += momentum_score * self.config['momentum_weight'] * 10
        details['momentum_component'] = momentum_score * self.config['momentum_weight'] * 10
        
        # 4. RISK STRUCTURE BÁSICO (2% del score)
        risk_score = self._calculate_risk_structure_basic(current)
        score += risk_score * self.config['risk_structure_weight'] * 10
        details['risk_component'] = risk_score * self.config['risk_structure_weight'] * 10
        
        # 5. LIQUIDEZ OPTIMIZADA (10% del score)
        if self.config['liquidity_enabled']:
            liquidity_score, liquidity_details = self.liquidity_validator.analyze_liquidity_coherence(
                df, 'LONG', current['Close']
            )
            if liquidity_score:
                score += liquidity_score * self.config['liquidity_weight'] * 10
                details['liquidity_component'] = liquidity_score * self.config['liquidity_weight'] * 10
                details['liquidity_details'] = liquidity_details
            else:
                details['liquidity_component'] = 0
                details['liquidity_details'] = None
        
        # 6. CONFIRMACIÓN MULTI-TIMEFRAME (10% del score - NUEVO)
        if self.config['confirmation_enabled']:
            confirmation_score = self._calculate_multitimeframe_confirmation_long(df, current)
            score += confirmation_score * self.config['confirmation_weight'] * 10
            details['confirmation_component'] = confirmation_score * self.config['confirmation_weight'] * 10
        
        # 7. PENALIZACIONES OPTIMIZADAS
        penalties = self._calculate_penalties_optimized_long(current, prev)
        score += penalties
        details['penalties'] = penalties
        
        # Normalizar y limitar
        final_score = max(0, min(score, self.config['max_score']))
        details['final_score'] = final_score
        
        return final_score, details
    
    def calculate_optimized_score_short(self, df, current, prev=None):
        """Calcula score optimizado para señales SHORT"""
        
        if prev is None and len(df) > 1:
            prev = df.iloc[-2]
        elif prev is None:
            prev = current
        
        score = 0.0
        details = {}
        
        # 1. RSI POTENCIADO para SHORT (65%)
        rsi_score = self._calculate_rsi_score_enhanced_short(current['RSI'])
        score += rsi_score * self.config['rsi_weight'] * 10
        details['rsi_component'] = rsi_score * self.config['rsi_weight'] * 10
        
        # 2. PRICE ACTION para SHORT (15%)
        price_action_score = self._calculate_price_action_refined_short(df, current, prev)
        score += price_action_score * self.config['price_action_weight'] * 10
        details['price_action_component'] = price_action_score * self.config['price_action_weight'] * 10
        
        # 3. MOMENTUM OPTIMIZADO para SHORT (8%)
        momentum_score = self._calculate_momentum_optimized_short(df, current)
        score += momentum_score * self.config['momentum_weight'] * 10
        details['momentum_component'] = momentum_score * self.config['momentum_weight'] * 10
        
        # 4. RISK STRUCTURE (2%)
        risk_score = self._calculate_risk_structure_basic(current)
        score += risk_score * self.config['risk_structure_weight'] * 10
        details['risk_component'] = risk_score * self.config['risk_structure_weight'] * 10
        
        # 5. LIQUIDEZ (10%)
        if self.config['liquidity_enabled']:
            liquidity_score, liquidity_details = self.liquidity_validator.analyze_liquidity_coherence(
                df, 'SHORT', current['Close']
            )
            if liquidity_score:
                score += liquidity_score * self.config['liquidity_weight'] * 10
                details['liquidity_component'] = liquidity_score * self.config['liquidity_weight'] * 10
                details['liquidity_details'] = liquidity_details
            else:
                details['liquidity_component'] = 0
                details['liquidity_details'] = None
        
        # 6. CONFIRMACIÓN MULTI-TIMEFRAME para SHORT (10%)
        if self.config['confirmation_enabled']:
            confirmation_score = self._calculate_multitimeframe_confirmation_short(df, current)
            score += confirmation_score * self.config['confirmation_weight'] * 10
            details['confirmation_component'] = confirmation_score * self.config['confirmation_weight'] * 10
        
        # 7. PENALIZACIONES
        penalties = self._calculate_penalties_optimized_short(current, prev)
        score += penalties
        details['penalties'] = penalties
        
        final_score = max(0, min(score, self.config['max_score']))
        details['final_score'] = final_score
        
        return final_score, details
    
    def _calculate_rsi_score_enhanced_long(self, rsi):
        """RSI score mejorado para LONG (más granular)"""
        
        # Basado en datos empíricos: RSI <30 tiene 75% WR
        if rsi <= 18:
            return 1.0    # RSI extremo: máxima confianza
        elif rsi <= 25:
            return 0.95   # RSI muy oversold: alta confianza
        elif rsi <= 32:
            return 0.85   # RSI oversold: buena confianza
        elif rsi <= 38:
            return 0.65   # RSI bajo-moderado: confianza moderada
        elif rsi <= 45:
            return 0.45   # RSI neutral-bajo: confianza baja
        elif rsi <= 55:
            return 0.25   # RSI neutral: muy baja confianza
        else:
            return 0.0    # RSI alto: no favorable para LONG
    
    def _calculate_rsi_score_enhanced_short(self, rsi):
        """RSI score mejorado para SHORT"""
        
        if rsi >= 82:
            return 1.0    # RSI extremo overbought
        elif rsi >= 75:
            return 0.95   # RSI muy overbought
        elif rsi >= 68:
            return 0.85   # RSI overbought
        elif rsi >= 62:
            return 0.65   # RSI alto-moderado
        elif rsi >= 55:
            return 0.45   # RSI neutral-alto
        elif rsi >= 45:
            return 0.25   # RSI neutral
        else:
            return 0.0    # RSI bajo: no favorable para SHORT
    
    def _calculate_price_action_refined_long(self, df, current, prev):
        """Price action refinado para LONG"""
        
        score = 0.0
        
        # 1. Momentum de vela actual (40%)
        if current['Close'] > current['Open']:
            body_strength = (current['Close'] - current['Open']) / current['Open']
            if body_strength >= 0.02:  # Vela alcista fuerte ≥2%
                score += 0.4
            elif body_strength >= 0.01:  # Vela alcista moderada ≥1%
                score += 0.25
            else:  # Vela alcista débil
                score += 0.1
        
        # 2. Secuencia de velas (30%)
        if len(df) >= 3:
            last_3_closes = df['Close'].tail(3).values
            if last_3_closes[2] > last_3_closes[1] > last_3_closes[0]:  # 3 velas alcistas
                score += 0.3
            elif last_3_closes[2] > last_3_closes[0]:  # Tendencia general alcista
                score += 0.15
        
        # 3. Posición en rango reciente optimizada (30%)
        if len(df) >= 14:
            recent_high = df['High'].rolling(14).max().iloc[-1]
            recent_low = df['Low'].rolling(14).min().iloc[-1]
            
            if recent_high > recent_low:
                position = (current['Close'] - recent_low) / (recent_high - recent_low)
                if position <= 0.25:  # En cuarto inferior (rebote desde soporte)
                    score += 0.3
                elif position <= 0.4:  # En zona baja-media
                    score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_price_action_refined_short(self, df, current, prev):
        """Price action refinado para SHORT"""
        
        score = 0.0
        
        # 1. Momentum de vela bajista
        if current['Close'] < current['Open']:
            body_strength = (current['Open'] - current['Close']) / current['Open']
            if body_strength >= 0.02:  # Vela bajista fuerte
                score += 0.4
            elif body_strength >= 0.01:  # Vela bajista moderada
                score += 0.25
            else:  # Vela bajista débil
                score += 0.1
        
        # 2. Secuencia bajista
        if len(df) >= 3:
            last_3_closes = df['Close'].tail(3).values
            if last_3_closes[2] < last_3_closes[1] < last_3_closes[0]:  # 3 velas bajistas
                score += 0.3
            elif last_3_closes[2] < last_3_closes[0]:  # Tendencia general bajista
                score += 0.15
        
        # 3. Posición alta en rango (cerca de resistencia)
        if len(df) >= 14:
            recent_high = df['High'].rolling(14).max().iloc[-1]
            recent_low = df['Low'].rolling(14).min().iloc[-1]
            
            if recent_high > recent_low:
                position = (current['Close'] - recent_low) / (recent_high - recent_low)
                if position >= 0.75:  # En cuarto superior (cerca de resistencia)
                    score += 0.3
                elif position >= 0.6:  # En zona alta-media
                    score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_momentum_optimized_long(self, df, current):
        """Momentum optimizado sin volumen contraproducente"""
        
        score = 0.0
        
        # 1. Momentum de precio puro (60%)
        if len(df) >= 5:
            price_change = (current['Close'] - df.iloc[-5]['Close']) / df.iloc[-5]['Close']
            if price_change >= 0.03:  # +3% en 5 períodos
                score += 0.6
            elif price_change >= 0.015:  # +1.5%
                score += 0.4
            elif price_change >= 0.005:  # +0.5%
                score += 0.2
        
        # 2. Aceleración del momentum (40%)
        if len(df) >= 7:
            momentum_recent = (current['Close'] - df.iloc[-3]['Close']) / df.iloc[-3]['Close']
            momentum_older = (df.iloc[-3]['Close'] - df.iloc[-7]['Close']) / df.iloc[-7]['Close']
            
            if momentum_recent > momentum_older and momentum_recent > 0:  # Acelerando al alza
                score += 0.4
            elif momentum_recent > 0:  # Al menos positivo
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_momentum_optimized_short(self, df, current):
        """Momentum optimizado para SHORT"""
        
        score = 0.0
        
        # 1. Momentum bajista
        if len(df) >= 5:
            price_change = (df.iloc[-5]['Close'] - current['Close']) / df.iloc[-5]['Close']
            if price_change >= 0.03:  # -3% en 5 períodos
                score += 0.6
            elif price_change >= 0.015:  # -1.5%
                score += 0.4
            elif price_change >= 0.005:  # -0.5%
                score += 0.2
        
        # 2. Aceleración bajista
        if len(df) >= 7:
            momentum_recent = (df.iloc[-3]['Close'] - current['Close']) / df.iloc[-3]['Close']
            momentum_older = (df.iloc[-7]['Close'] - df.iloc[-3]['Close']) / df.iloc[-7]['Close']
            
            if momentum_recent > momentum_older and momentum_recent > 0:  # Acelerando a la baja
                score += 0.4
            elif momentum_recent > 0:  # Al menos bajista
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_multitimeframe_confirmation_long(self, df, current):
        """NUEVO: Confirmación multi-timeframe para LONG"""
        
        score = 0.0
        
        # 1. Confirmación de tendencia en timeframe mayor (simulado con SMA larga)
        if len(df) >= 50:
            sma_50 = df['Close'].rolling(50).mean().iloc[-1]
            if current['Close'] > sma_50:
                trend_strength = (current['Close'] - sma_50) / sma_50
                if trend_strength >= 0.05:  # 5% sobre SMA50
                    score += 0.4
                elif trend_strength >= 0.02:  # 2% sobre SMA50
                    score += 0.25
                elif trend_strength > 0:  # Sobre SMA50
                    score += 0.1
        
        # 2. Momentum multi-timeframe (usando diferentes períodos)
        momentum_scores = []
        
        # Momentum corto plazo (3 períodos)
        if len(df) >= 4:
            short_momentum = (current['Close'] - df.iloc[-4]['Close']) / df.iloc[-4]['Close']
            momentum_scores.append(1 if short_momentum > 0.01 else 0)
        
        # Momentum medio plazo (8 períodos)
        if len(df) >= 9:
            medium_momentum = (current['Close'] - df.iloc[-9]['Close']) / df.iloc[-9]['Close']
            momentum_scores.append(1 if medium_momentum > 0.02 else 0)
        
        # Momentum largo plazo (21 períodos)
        if len(df) >= 22:
            long_momentum = (current['Close'] - df.iloc[-22]['Close']) / df.iloc[-22]['Close']
            momentum_scores.append(1 if long_momentum > 0.03 else 0)
        
        # Confirmación: más timeframes positivos = mejor score
        if momentum_scores:
            confirmation_ratio = sum(momentum_scores) / len(momentum_scores)
            score += confirmation_ratio * 0.4
        
        # 3. Divergencia RSI (señal de fortaleza)
        if len(df) >= 14:
            # RSI debería estar subiendo en LONG
            current_rsi = current['RSI']
            prev_rsi = df.iloc[-5]['RSI'] if len(df) >= 5 else current_rsi
            
            if current_rsi > prev_rsi and current_rsi < 70:  # RSI subiendo pero no overbought
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_multitimeframe_confirmation_short(self, df, current):
        """Confirmación multi-timeframe para SHORT"""
        
        score = 0.0
        
        # 1. Confirmación de tendencia bajista
        if len(df) >= 50:
            sma_50 = df['Close'].rolling(50).mean().iloc[-1]
            if current['Close'] < sma_50:
                trend_strength = (sma_50 - current['Close']) / sma_50
                if trend_strength >= 0.05:  # 5% bajo SMA50
                    score += 0.4
                elif trend_strength >= 0.02:  # 2% bajo SMA50
                    score += 0.25
                elif trend_strength > 0:  # Bajo SMA50
                    score += 0.1
        
        # 2. Momentum multi-timeframe bajista
        momentum_scores = []
        
        if len(df) >= 4:
            short_momentum = (df.iloc[-4]['Close'] - current['Close']) / df.iloc[-4]['Close']
            momentum_scores.append(1 if short_momentum > 0.01 else 0)
        
        if len(df) >= 9:
            medium_momentum = (df.iloc[-9]['Close'] - current['Close']) / df.iloc[-9]['Close']
            momentum_scores.append(1 if medium_momentum > 0.02 else 0)
        
        if len(df) >= 22:
            long_momentum = (df.iloc[-22]['Close'] - current['Close']) / df.iloc[-22]['Close']
            momentum_scores.append(1 if long_momentum > 0.03 else 0)
        
        if momentum_scores:
            confirmation_ratio = sum(momentum_scores) / len(momentum_scores)
            score += confirmation_ratio * 0.4
        
        # 3. RSI bajista
        if len(df) >= 14:
            current_rsi = current['RSI']
            prev_rsi = df.iloc[-5]['RSI'] if len(df) >= 5 else current_rsi
            
            if current_rsi < prev_rsi and current_rsi > 30:  # RSI bajando pero no oversold
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_risk_structure_basic(self, current):
        """Risk structure básico optimizado"""
        
        score = 0.0
        
        try:
            atr_pct = current['ATR'] / current['Close']
            if 0.01 <= atr_pct <= 0.04:  # Volatilidad óptima 1-4%
                score += 1.0
            elif 0.005 <= atr_pct <= 0.06:  # Volatilidad aceptable
                score += 0.5
        except:
            score = 0.3  # Score neutral si no hay ATR
        
        return score
    
    def _calculate_penalties_optimized_long(self, current, prev):
        """Penalizaciones optimizadas para LONG"""
        
        penalty = 0.0
        
        # 1. Penalización por volumen excesivo (confirmado como contraproducente)
        if self.config['volume_penalty']:
            if current['Volume_Ratio'] >= 5.0:  # Volumen muy extremo
                penalty -= 1.5
            elif current['Volume_Ratio'] >= 3.5:  # Volumen muy alto
                penalty -= 0.8
            elif current['Volume_Ratio'] >= 2.5:  # Volumen alto
                penalty -= 0.3
        
        return penalty
    
    def _calculate_penalties_optimized_short(self, current, prev):
        """Penalizaciones optimizadas para SHORT"""
        
        penalty = 0.0
        
        # Para SHORT toleramos un poco más de volumen
        if self.config['volume_penalty']:
            if current['Volume_Ratio'] >= 6.0:  # Volumen muy extremo
                penalty -= 1.5
            elif current['Volume_Ratio'] >= 4.0:  # Volumen muy alto
                penalty -= 0.8
            elif current['Volume_Ratio'] >= 3.0:  # Volumen alto
                penalty -= 0.3
        
        return penalty
    
    def get_leverage_optimized(self, score):
        """Sistema de leverage optimizado"""
        
        # Basado en evidencia: leverage 3x tiene 80% WR
        if score >= 8.5:
            return 6  # Leverage máximo para scores excelentes
        elif score >= 7.5:
            return 4  # Leverage alto
        elif score >= 6.8:
            return 3  # Leverage óptimo (sweet spot empírico)
        elif score >= 6.0:
            return 2  # Leverage moderado
        elif score >= 5.8:
            return 1  # Sin leverage
        else:
            return 1  # Señal demasiado débil
    
    def validate_optimized_signal(self, score, score_details=None):
        """Validación optimizada"""
        
        if score < self.config['min_empirical_score']:
            return False, f"Score insuficiente: {score:.1f}"
        
        # Validación de confirmación multi-timeframe
        if self.config['confirmation_enabled'] and score_details:
            confirmation_score = score_details.get('confirmation_component', 0) / 10 / self.config['confirmation_weight']
            if confirmation_score < self.config['min_confirmation_score']:
                return False, f"Confirmación insuficiente: {confirmation_score:.2f}"
        
        # Validación de liquidez optimizada
        if self.config['liquidity_enabled'] and score_details:
            liquidity_details = score_details.get('liquidity_details')
            if liquidity_details:
                if liquidity_details['total_score'] < self.config['min_liquidity_score']:
                    return False, f"Liquidez insuficiente: {liquidity_details['total_score']:.2f}"
        
        return True, "Señal validada"

def demo_scoring_v3():
    """Demo del sistema optimizado"""
    
    print('🚀 SISTEMA DE SCORING OPTIMIZADO V3.0')
    print('='*70)
    print('Optimizaciones realizadas:')
    print('• RSI: 65% del score (potenciado por ser más confiable)')
    print('• Price Action: 15% (refinado)')
    print('• Momentum: 8% (optimizado sin volumen contraproducente)')
    print('• Risk Structure: 2% (básico)')
    print('• Liquidez: 10% (optimizada)')
    print('• CONFIRMACIÓN MULTI-TIMEFRAME: 10% (NUEVO)')
    print('• MACD penalty: DESACTIVADO (era contraproducente)')
    print('• Thresholds relajados para más trades de calidad')
    print('='*70)

if __name__ == "__main__":
    demo_scoring_v3()