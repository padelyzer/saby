#!/usr/bin/env python3
"""
Sistema de Scoring Empírico V2.0
Basado en análisis de componentes efectivos
"""

import pandas as pd
import numpy as np

class ScoringEmpiricoV2:
    """
    Nuevo sistema de scoring basado en evidencia empírica
    """
    
    def __init__(self):
        # Configuración con RSI Divergence optimizado (80% base + 20% divergence)
        self.config = {
            # Componentes base rebalanceados (80% del score total)
            'rsi_weight': 0.45,          # 45% del score (reducido para divergence)
            'price_action_weight': 0.20, # 20% - acción del precio (aumentado)
            'momentum_weight': 0.10,     # 10% - momentum real (reducido)
            'risk_structure_weight': 0.05, # 5% - estructura de riesgo
            
            # RSI Divergence como componente principal (20% del score total)
            'rsi_divergence_weight': 0.20,  # 20% - RSI Divergence optimizado
            'rsi_divergence_enabled': True,  # HABILITADO
            
            # Liquidez deshabilitada (era contraproducente)
            'liquidity_weight': 0.00,    # 0% - DESHABILITADO
            'liquidity_enabled': False,  # DESHABILITADO
            
            # Penalizaciones por componentes contraproducentes
            'volume_penalty': True,      # Penalizar volumen muy alto
            'macd_penalty': True,        # Penalizar MACD contraproducente
            
            # Thresholds empíricos
            'min_empirical_score': 6.0,  # Score mínimo más realista
            'min_liquidity_score': 0.6, # Score mínimo de liquidez para validar
            'max_score': 10.0
        }
        
        # Importar validador de liquidez
        if self.config['liquidity_enabled']:
            from liquidez_validator import LiquidezValidator
            self.liquidity_validator = LiquidezValidator()
    
    def calculate_empirical_score_long(self, df, current, prev=None):
        """Calcula score empírico para señales LONG"""
        
        if prev is None and len(df) > 1:
            prev = df.iloc[-2]
        elif prev is None:
            prev = current
        
        score = 0.0
        details = {}
        
        # 1. COMPONENTE RSI (60% del score - máximo 6.0 puntos)
        rsi_score = self._calculate_rsi_score_long(current['RSI'])
        score += rsi_score * self.config['rsi_weight'] * 10
        details['rsi_component'] = rsi_score * self.config['rsi_weight'] * 10
        
        # 2. ACCIÓN DEL PRECIO (20% del score - máximo 2.0 puntos)
        price_action_score = self._calculate_price_action_score_long(df, current, prev)
        score += price_action_score * self.config['price_action_weight'] * 10
        details['price_action_component'] = price_action_score * self.config['price_action_weight'] * 10
        
        # 3. MOMENTUM REAL (15% del score - máximo 1.5 puntos)
        momentum_score = self._calculate_momentum_score_long(df, current)
        score += momentum_score * self.config['momentum_weight'] * 10
        details['momentum_component'] = momentum_score * self.config['momentum_weight'] * 10
        
        # 4. ESTRUCTURA DE RIESGO (5% del score - máximo 0.5 puntos)
        risk_score = self._calculate_risk_structure_score(current)
        score += risk_score * self.config['risk_structure_weight'] * 10
        details['risk_component'] = risk_score * self.config['risk_structure_weight'] * 10
        
        # 5. RSI DIVERGENCE OPTIMIZADO (20% del score total - NUEVO)
        from rsi_divergence_optimizado import RSIDivergenceOptimizado
        rsi_div_system = RSIDivergenceOptimizado()
        
        divergence_score, divergence_details = rsi_div_system.get_rsi_divergence_score(df, current, 'LONG')
        score += divergence_score * 2.0  # 2.0 para que sea 20% del score total
        details['rsi_divergence_component'] = divergence_score * 2.0
        details['rsi_divergence_details'] = divergence_details
        
        # 6. PENALIZACIONES por componentes contraproducentes
        penalties = self._calculate_penalties_long(current, prev)
        score += penalties
        details['penalties'] = penalties
        
        # Normalizar y limitar
        final_score = max(0, min(score, self.config['max_score']))
        details['final_score'] = final_score
        
        return final_score, details
    
    def calculate_empirical_score_short(self, df, current, prev=None):
        """Calcula score empírico para señales SHORT"""
        
        if prev is None and len(df) > 1:
            prev = df.iloc[-2]
        elif prev is None:
            prev = current
        
        score = 0.0
        details = {}
        
        # 1. COMPONENTE RSI para SHORT (60% del score)
        rsi_score = self._calculate_rsi_score_short(current['RSI'])
        score += rsi_score * self.config['rsi_weight'] * 10
        details['rsi_component'] = rsi_score * self.config['rsi_weight'] * 10
        
        # 2. ACCIÓN DEL PRECIO para SHORT (20% del score)
        price_action_score = self._calculate_price_action_score_short(df, current, prev)
        score += price_action_score * self.config['price_action_weight'] * 10
        details['price_action_component'] = price_action_score * self.config['price_action_weight'] * 10
        
        # 3. MOMENTUM REAL para SHORT (15% del score)
        momentum_score = self._calculate_momentum_score_short(df, current)
        score += momentum_score * self.config['momentum_weight'] * 10
        details['momentum_component'] = momentum_score * self.config['momentum_weight'] * 10
        
        # 4. ESTRUCTURA DE RIESGO (5% del score)
        risk_score = self._calculate_risk_structure_score(current)
        score += risk_score * self.config['risk_structure_weight'] * 10
        details['risk_component'] = risk_score * self.config['risk_structure_weight'] * 10
        
        # 5. RSI DIVERGENCE OPTIMIZADO para SHORT (20% del score total)
        from rsi_divergence_optimizado import RSIDivergenceOptimizado
        rsi_div_system = RSIDivergenceOptimizado()
        
        divergence_score, divergence_details = rsi_div_system.get_rsi_divergence_score(df, current, 'SHORT')
        score += divergence_score * 2.0  # 2.0 para que sea 20% del score total
        details['rsi_divergence_component'] = divergence_score * 2.0
        details['rsi_divergence_details'] = divergence_details
        
        # 6. PENALIZACIONES
        penalties = self._calculate_penalties_short(current, prev)
        score += penalties
        details['penalties'] = penalties
        
        final_score = max(0, min(score, self.config['max_score']))
        details['final_score'] = final_score
        
        return final_score, details
    
    def _calculate_rsi_score_long(self, rsi):
        """RSI score para LONG (basado en datos empíricos)"""
        
        if rsi <= 20:
            return 1.0  # RSI extremo: 66.7% WR empírico
        elif rsi <= 30:
            return 0.9  # RSI muy oversold: 75% WR empírico
        elif rsi <= 40:
            return 0.7  # RSI oversold: 55.9% WR empírico
        elif rsi <= 50:
            return 0.4  # RSI neutral bajo: predicción moderada
        elif rsi <= 60:
            return 0.2  # RSI neutral alto: 35.4% WR empírico
        else:
            return 0.0  # RSI overbought: no favorable para LONG
    
    def _calculate_rsi_score_short(self, rsi):
        """RSI score para SHORT (invertido)"""
        
        if rsi >= 80:
            return 1.0  # RSI extremo overbought
        elif rsi >= 70:
            return 0.9  # RSI muy overbought
        elif rsi >= 60:
            return 0.7  # RSI overbought
        elif rsi >= 50:
            return 0.4  # RSI neutral alto
        elif rsi >= 40:
            return 0.2  # RSI neutral bajo
        else:
            return 0.0  # RSI oversold: no favorable para SHORT
    
    def _calculate_price_action_score_long(self, df, current, prev):
        """Nuevo componente: Acción del precio para LONG"""
        
        score = 0.0
        
        # 1. Confirmación de dirección (30% de este componente)
        if current['Close'] > prev['Close']:
            score += 0.3
        
        # 2. Posición en rango reciente (40% de este componente)
        recent_high = df['High'].rolling(20).max().iloc[-1]
        recent_low = df['Low'].rolling(20).min().iloc[-1]
        
        if recent_high > recent_low:
            position_in_range = (current['Close'] - recent_low) / (recent_high - recent_low)
            if position_in_range < 0.3:  # En tercio inferior del rango
                score += 0.4
            elif position_in_range < 0.5:  # En medio-bajo del rango
                score += 0.2
        
        # 3. Patrón de velas (30% de este componente)
        candle_body = abs(current['Close'] - current['Open'])
        candle_range = current['High'] - current['Low']
        
        if candle_range > 0:
            body_ratio = candle_body / candle_range
            if body_ratio > 0.6 and current['Close'] > current['Open']:  # Vela alcista fuerte
                score += 0.3
            elif current['Close'] > current['Open']:  # Vela alcista
                score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_price_action_score_short(self, df, current, prev):
        """Acción del precio para SHORT"""
        
        score = 0.0
        
        # 1. Confirmación de dirección bajista
        if current['Close'] < prev['Close']:
            score += 0.3
        
        # 2. Posición en rango reciente (favorece parte alta)
        recent_high = df['High'].rolling(20).max().iloc[-1]
        recent_low = df['Low'].rolling(20).min().iloc[-1]
        
        if recent_high > recent_low:
            position_in_range = (current['Close'] - recent_low) / (recent_high - recent_low)
            if position_in_range > 0.7:  # En tercio superior del rango
                score += 0.4
            elif position_in_range > 0.5:  # En medio-alto del rango
                score += 0.2
        
        # 3. Patrón de velas bajistas
        candle_body = abs(current['Close'] - current['Open'])
        candle_range = current['High'] - current['Low']
        
        if candle_range > 0:
            body_ratio = candle_body / candle_range
            if body_ratio > 0.6 and current['Close'] < current['Open']:  # Vela bajista fuerte
                score += 0.3
            elif current['Close'] < current['Open']:  # Vela bajista
                score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_momentum_score_long(self, df, current):
        """Momentum real para LONG"""
        
        score = 0.0
        
        # 1. Momentum de precio (3 períodos)
        if len(df) >= 4:
            price_momentum = (current['Close'] - df.iloc[-4]['Close']) / df.iloc[-4]['Close']
            if price_momentum > 0.02:  # +2% en 3 períodos
                score += 0.4
            elif price_momentum > 0:
                score += 0.2
        
        # 2. Momentum de volumen CONTROLADO (usar volumen bajo-moderado)
        if current['Volume_Ratio'] <= 2.0:  # Volumen controlado es mejor
            score += 0.3
        elif current['Volume_Ratio'] <= 1.5:  # Volumen muy controlado
            score += 0.4
        # No sumar puntos por volumen alto (es contraproducente)
        
        # 3. Consistencia de dirección
        if len(df) >= 3:
            closes = df['Close'].tail(3).values
            if closes[1] > closes[0] and closes[2] > closes[1]:  # 3 períodos consecutivos alcistas
                score += 0.3
            elif closes[2] > closes[0]:  # Dirección general alcista
                score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_momentum_score_short(self, df, current):
        """Momentum real para SHORT"""
        
        score = 0.0
        
        # 1. Momentum de precio bajista
        if len(df) >= 4:
            price_momentum = (df.iloc[-4]['Close'] - current['Close']) / df.iloc[-4]['Close']
            if price_momentum > 0.02:  # -2% en 3 períodos
                score += 0.4
            elif price_momentum > 0:
                score += 0.2
        
        # 2. Momentum de volumen CONTROLADO
        if current['Volume_Ratio'] <= 2.0:
            score += 0.3
        elif current['Volume_Ratio'] <= 1.5:
            score += 0.4
        
        # 3. Consistencia de dirección bajista
        if len(df) >= 3:
            closes = df['Close'].tail(3).values
            if closes[1] < closes[0] and closes[2] < closes[1]:  # 3 períodos consecutivos bajistas
                score += 0.3
            elif closes[2] < closes[0]:  # Dirección general bajista
                score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_risk_structure_score(self, current):
        """Estructura de riesgo favorable"""
        
        score = 0.0
        
        # 1. Volatilidad moderada (no demasiado alta)
        try:
            atr_pct = current['ATR'] / current['Close']
            if 0.015 <= atr_pct <= 0.04:  # Volatilidad óptima 1.5-4%
                score += 0.6
            elif 0.01 <= atr_pct <= 0.06:  # Volatilidad aceptable
                score += 0.3
            # Penalizar volatilidad extrema
            elif atr_pct > 0.08:
                score -= 0.2
        except:
            pass
        
        # 2. Relación High-Low saludable
        try:
            daily_range = (current['High'] - current['Low']) / current['Close']
            if 0.01 <= daily_range <= 0.05:  # Rango saludable 1-5%
                score += 0.4
        except:
            pass
        
        return max(0, min(score, 1.0))
    
    def _calculate_penalties_long(self, current, prev):
        """Penalizaciones por componentes contraproducentes en LONG"""
        
        penalty = 0.0
        
        # 1. PENALIZACIÓN POR VOLUMEN EXCESIVO (empíricamente contraproducente)
        if self.config['volume_penalty']:
            if current['Volume_Ratio'] >= 4.0:  # Volumen muy alto
                penalty -= 1.0  # Penalización fuerte
            elif current['Volume_Ratio'] >= 3.0:  # Volumen alto
                penalty -= 0.5  # Penalización moderada
        
        # 2. PENALIZACIÓN POR MACD CONTRAPRODUCENTE
        if self.config['macd_penalty']:
            try:
                # MACD muy positivo puede ser contraproducente
                if current['MACD'] > current['MACD_Signal'] * 1.5:
                    penalty -= 0.3
            except:
                pass
        
        return penalty
    
    def _calculate_penalties_short(self, current, prev):
        """Penalizaciones por componentes contraproducentes en SHORT"""
        
        penalty = 0.0
        
        # 1. PENALIZACIÓN POR VOLUMEN EXCESIVO
        if self.config['volume_penalty']:
            if current['Volume_Ratio'] >= 4.0:
                penalty -= 1.0
            elif current['Volume_Ratio'] >= 3.0:
                penalty -= 0.5
        
        # 2. PENALIZACIÓN POR MACD CONTRAPRODUCENTE
        if self.config['macd_penalty']:
            try:
                # MACD muy negativo puede ser contraproducente
                if current['MACD'] < current['MACD_Signal'] * 1.5:
                    penalty -= 0.3
            except:
                pass
        
        return penalty
    
    def get_leverage_empirical(self, score):
        """Leverage basado en score empírico"""
        
        if score >= 8.5:
            return 6  # Leverage alto solo para scores excelentes
        elif score >= 7.5:
            return 4  # Leverage moderado-alto
        elif score >= 6.5:
            return 3  # Leverage moderado
        elif score >= 6.0:
            return 2  # Leverage bajo
        else:
            return 1  # Sin leverage para scores bajos
    
    def validate_empirical_signal(self, score, score_details=None):
        """Valida si la señal cumple criterios empíricos + liquidez"""
        
        # Validación básica de score
        if score < self.config['min_empirical_score']:
            return False, "Score insuficiente"
        
        # Validación adicional de liquidez si está habilitada
        if self.config['liquidity_enabled'] and score_details:
            liquidity_details = score_details.get('liquidity_details')
            if liquidity_details:
                liquidity_score = liquidity_details['total_score']
                
                # Rechazar señales con liquidez muy baja
                if liquidity_score < self.config['min_liquidity_score']:
                    return False, f"Liquidez insuficiente: {liquidity_score:.2f}"
                
                # Rechazar señales incoherentes con liquidez
                if not liquidity_details['is_coherent']:
                    return False, "Liquidez incoherente con dirección"
        
        return True, "Señal validada"
    
    def get_signal_quality_rating(self, score, score_details=None):
        """Obtiene rating de calidad de señal incluyendo liquidez"""
        
        base_rating = ""
        if score >= 8.5:
            base_rating = "EXCELENTE"
        elif score >= 7.5:
            base_rating = "MUY BUENA"
        elif score >= 6.5:
            base_rating = "BUENA"
        elif score >= 6.0:
            base_rating = "ACEPTABLE"
        else:
            base_rating = "INSUFICIENTE"
        
        # Ajustar rating por liquidez
        if self.config['liquidity_enabled'] and score_details:
            liquidity_details = score_details.get('liquidity_details')
            if liquidity_details:
                liquidity_score = liquidity_details['total_score']
                
                if liquidity_score >= 0.8:
                    return f"{base_rating} + LIQUIDEZ EXCELENTE"
                elif liquidity_score >= 0.7:
                    return f"{base_rating} + LIQUIDEZ BUENA"
                elif liquidity_score >= 0.6:
                    return f"{base_rating} + LIQUIDEZ ACEPTABLE"
                else:
                    return f"{base_rating} - LIQUIDEZ POBRE"
        
        return base_rating

# Ejemplo de uso
def demo_scoring_v2():
    """Demostración del nuevo sistema"""
    
    print('🚀 SISTEMA DE SCORING EMPÍRICO V2.0')
    print('='*60)
    print('Basado en análisis de componentes efectivos:')
    print('• RSI: 60% del score (único componente confiable)')
    print('• Price Action: 20% (nuevo)')
    print('• Momentum: 15% (redefinido)')
    print('• Risk Structure: 5% (nuevo)')
    print('• Penalizaciones por volumen alto y MACD contraproducente')
    print('='*60)

if __name__ == "__main__":
    demo_scoring_v2()