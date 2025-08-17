#!/usr/bin/env python3
"""
Sistema Conservador Final
Basado en V2 + Liquidez (57.1% WR) con ajustes mínimos
"""

import pandas as pd
import numpy as np

class SistemaConservadorFinal:
    """
    Sistema conservador basado en la versión que funcionaba
    """
    
    def __init__(self):
        # Configuración conservadora basada en V2 + Liquidez que funcionaba
        self.config = {
            # Mantener pesos que funcionaron (V2 + Liquidez)
            'rsi_weight': 0.55,          # 55% (ligero aumento de 51%)
            'price_action_weight': 0.18, # 18% (ligero aumento de 17%)
            'momentum_weight': 0.12,     # 12% (mantener)
            'risk_structure_weight': 0.05, # 5% (mantener)
            'liquidity_weight': 0.10,    # 10% (reducido de 15% para eficiencia)
            
            # Thresholds conservadores
            'min_empirical_score': 5.9,  # Ligero ajuste de 6.0
            'min_liquidity_score': 0.58, # Ligero relajamiento de 0.6
            'max_score': 10.0,
            
            # Configuración de liquidez (mantener lo que funcionaba)
            'liquidity_enabled': True,
            'volume_penalty': True,      # Mantener (era efectivo)
            'macd_penalty': False,       # Mantener desactivado
        }
        
        # Importar validador de liquidez
        if self.config['liquidity_enabled']:
            from liquidez_validator import LiquidezValidator
            self.liquidity_validator = LiquidezValidator()
    
    def calculate_conservative_score_long(self, df, current, prev=None):
        """Score conservador para LONG"""
        
        if prev is None and len(df) > 1:
            prev = df.iloc[-2]
        elif prev is None:
            prev = current
        
        score = 0.0
        details = {}
        
        # 1. RSI mejorado pero conservador (55%)
        rsi_score = self._calculate_rsi_conservative_long(current['RSI'])
        score += rsi_score * self.config['rsi_weight'] * 10
        details['rsi_component'] = rsi_score * self.config['rsi_weight'] * 10
        
        # 2. Price Action (mantener V2 con ligeras mejoras)
        price_action_score = self._calculate_price_action_conservative_long(df, current, prev)
        score += price_action_score * self.config['price_action_weight'] * 10
        details['price_action_component'] = price_action_score * self.config['price_action_weight'] * 10
        
        # 3. Momentum (mantener V2)
        momentum_score = self._calculate_momentum_conservative_long(df, current)
        score += momentum_score * self.config['momentum_weight'] * 10
        details['momentum_component'] = momentum_score * self.config['momentum_weight'] * 10
        
        # 4. Risk Structure (mantener)
        risk_score = self._calculate_risk_structure_score(current)
        score += risk_score * self.config['risk_structure_weight'] * 10
        details['risk_component'] = risk_score * self.config['risk_structure_weight'] * 10
        
        # 5. Liquidez (mantener pero optimizada)
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
        
        # 6. Penalizaciones (mantener lo que funcionaba)
        penalties = self._calculate_penalties_conservative_long(current, prev)
        score += penalties
        details['penalties'] = penalties
        
        final_score = max(0, min(score, self.config['max_score']))
        details['final_score'] = final_score
        
        return final_score, details
    
    def calculate_conservative_score_short(self, df, current, prev=None):
        """Score conservador para SHORT"""
        
        if prev is None and len(df) > 1:
            prev = df.iloc[-2]
        elif prev is None:
            prev = current
        
        score = 0.0
        details = {}
        
        # 1. RSI para SHORT
        rsi_score = self._calculate_rsi_conservative_short(current['RSI'])
        score += rsi_score * self.config['rsi_weight'] * 10
        details['rsi_component'] = rsi_score * self.config['rsi_weight'] * 10
        
        # 2. Price Action para SHORT
        price_action_score = self._calculate_price_action_conservative_short(df, current, prev)
        score += price_action_score * self.config['price_action_weight'] * 10
        details['price_action_component'] = price_action_score * self.config['price_action_weight'] * 10
        
        # 3. Momentum para SHORT
        momentum_score = self._calculate_momentum_conservative_short(df, current)
        score += momentum_score * self.config['momentum_weight'] * 10
        details['momentum_component'] = momentum_score * self.config['momentum_weight'] * 10
        
        # 4. Risk Structure
        risk_score = self._calculate_risk_structure_score(current)
        score += risk_score * self.config['risk_structure_weight'] * 10
        details['risk_component'] = risk_score * self.config['risk_structure_weight'] * 10
        
        # 5. Liquidez
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
        
        # 6. Penalizaciones
        penalties = self._calculate_penalties_conservative_short(current, prev)
        score += penalties
        details['penalties'] = penalties
        
        final_score = max(0, min(score, self.config['max_score']))
        details['final_score'] = final_score
        
        return final_score, details
    
    def _calculate_rsi_conservative_long(self, rsi):
        """RSI conservador mejorado para LONG"""
        
        # Basado en datos empíricos pero más granular
        if rsi <= 20:
            return 1.0    # RSI extremo: 66.7% WR empírico
        elif rsi <= 28:
            return 0.9    # RSI muy oversold: 75% WR empírico
        elif rsi <= 35:
            return 0.8    # RSI oversold: 55.9% WR empírico
        elif rsi <= 42:
            return 0.6    # RSI bajo-moderado
        elif rsi <= 50:
            return 0.3    # RSI neutral bajo
        elif rsi <= 60:
            return 0.1    # RSI neutral alto: 35.4% WR empírico
        else:
            return 0.0    # RSI overbought: no favorable
    
    def _calculate_rsi_conservative_short(self, rsi):
        """RSI conservador para SHORT"""
        
        if rsi >= 80:
            return 1.0    # RSI extremo overbought
        elif rsi >= 72:
            return 0.9    # RSI muy overbought
        elif rsi >= 65:
            return 0.8    # RSI overbought
        elif rsi >= 58:
            return 0.6    # RSI alto-moderado
        elif rsi >= 50:
            return 0.3    # RSI neutral alto
        elif rsi >= 40:
            return 0.1    # RSI neutral bajo
        else:
            return 0.0    # RSI bajo: no favorable para SHORT
    
    def _calculate_price_action_conservative_long(self, df, current, prev):
        """Price action conservador (V2 mejorado)"""
        
        score = 0.0
        
        # 1. Dirección de vela (30%)
        if current['Close'] > current['Open']:
            body_pct = (current['Close'] - current['Open']) / current['Open']
            if body_pct >= 0.015:  # Vela alcista ≥1.5%
                score += 0.3
            elif body_pct >= 0.007:  # Vela alcista ≥0.7%
                score += 0.2
            else:
                score += 0.1
        
        # 2. Secuencia (30%)
        if current['Close'] > prev['Close']:
            score += 0.2
            if len(df) >= 3 and df.iloc[-3]['Close'] < prev['Close']:  # Recuperación
                score += 0.1
        
        # 3. Posición en rango (40%)
        if len(df) >= 20:
            recent_high = df['High'].rolling(20).max().iloc[-1]
            recent_low = df['Low'].rolling(20).min().iloc[-1]
            
            if recent_high > recent_low:
                position = (current['Close'] - recent_low) / (recent_high - recent_low)
                if position <= 0.3:  # Zona baja
                    score += 0.4
                elif position <= 0.5:  # Zona baja-media
                    score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_price_action_conservative_short(self, df, current, prev):
        """Price action conservador para SHORT"""
        
        score = 0.0
        
        # 1. Dirección bajista
        if current['Close'] < current['Open']:
            body_pct = (current['Open'] - current['Close']) / current['Open']
            if body_pct >= 0.015:
                score += 0.3
            elif body_pct >= 0.007:
                score += 0.2
            else:
                score += 0.1
        
        # 2. Secuencia bajista
        if current['Close'] < prev['Close']:
            score += 0.2
            if len(df) >= 3 and df.iloc[-3]['Close'] > prev['Close']:  # Reversión
                score += 0.1
        
        # 3. Posición alta en rango
        if len(df) >= 20:
            recent_high = df['High'].rolling(20).max().iloc[-1]
            recent_low = df['Low'].rolling(20).min().iloc[-1]
            
            if recent_high > recent_low:
                position = (current['Close'] - recent_low) / (recent_high - recent_low)
                if position >= 0.7:  # Zona alta
                    score += 0.4
                elif position >= 0.5:  # Zona alta-media
                    score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_momentum_conservative_long(self, df, current):
        """Momentum conservador (mantener V2)"""
        
        score = 0.0
        
        # 1. Momentum de precio (60%)
        if len(df) >= 4:
            price_momentum = (current['Close'] - df.iloc[-4]['Close']) / df.iloc[-4]['Close']
            if price_momentum > 0.02:
                score += 0.4
            elif price_momentum > 0:
                score += 0.2
        
        # 2. Volumen controlado (40%) - evitar volumen contraproducente
        if current['Volume_Ratio'] <= 2.0:
            score += 0.3
        elif current['Volume_Ratio'] <= 1.5:
            score += 0.4
        
        # 3. Consistencia
        if len(df) >= 3:
            closes = df['Close'].tail(3).values
            if closes[2] > closes[0]:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_momentum_conservative_short(self, df, current):
        """Momentum conservador para SHORT"""
        
        score = 0.0
        
        if len(df) >= 4:
            price_momentum = (df.iloc[-4]['Close'] - current['Close']) / df.iloc[-4]['Close']
            if price_momentum > 0.02:
                score += 0.4
            elif price_momentum > 0:
                score += 0.2
        
        if current['Volume_Ratio'] <= 2.0:
            score += 0.3
        elif current['Volume_Ratio'] <= 1.5:
            score += 0.4
        
        if len(df) >= 3:
            closes = df['Close'].tail(3).values
            if closes[2] < closes[0]:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_risk_structure_score(self, current):
        """Risk structure (mantener de V2)"""
        
        score = 0.0
        
        try:
            atr_pct = current['ATR'] / current['Close']
            if 0.015 <= atr_pct <= 0.04:
                score += 0.6
            elif 0.01 <= atr_pct <= 0.06:
                score += 0.3
            elif atr_pct > 0.08:
                score -= 0.2
        except:
            pass
        
        try:
            daily_range = (current['High'] - current['Low']) / current['Close']
            if 0.01 <= daily_range <= 0.05:
                score += 0.4
        except:
            pass
        
        return max(0, min(score, 1.0))
    
    def _calculate_penalties_conservative_long(self, current, prev):
        """Penalizaciones conservadoras"""
        
        penalty = 0.0
        
        # Mantener penalización por volumen excesivo (comprobadamente efectivo)
        if self.config['volume_penalty']:
            if current['Volume_Ratio'] >= 4.0:
                penalty -= 1.0
            elif current['Volume_Ratio'] >= 3.0:
                penalty -= 0.5
        
        return penalty
    
    def _calculate_penalties_conservative_short(self, current, prev):
        """Penalizaciones conservadoras para SHORT"""
        
        penalty = 0.0
        
        if self.config['volume_penalty']:
            if current['Volume_Ratio'] >= 4.5:
                penalty -= 1.0
            elif current['Volume_Ratio'] >= 3.5:
                penalty -= 0.5
        
        return penalty
    
    def get_leverage_conservative(self, score):
        """Leverage conservador basado en evidencia"""
        
        # Mantener el esquema que mostró 80% WR en 3x
        if score >= 8.0:
            return 4  # Leverage alto pero conservador
        elif score >= 7.0:
            return 3  # Sweet spot empírico
        elif score >= 6.2:
            return 2  # Leverage moderado
        elif score >= 5.9:
            return 1  # Sin leverage
        else:
            return 1
    
    def validate_conservative_signal(self, score, score_details=None):
        """Validación conservadora"""
        
        if score < self.config['min_empirical_score']:
            return False, f"Score insuficiente: {score:.1f}"
        
        if self.config['liquidity_enabled'] and score_details:
            liquidity_details = score_details.get('liquidity_details')
            if liquidity_details and liquidity_details['total_score'] < self.config['min_liquidity_score']:
                return False, f"Liquidez insuficiente: {liquidity_details['total_score']:.2f}"
        
        return True, "Señal validada"

def demo_conservador():
    print('🛡️ SISTEMA CONSERVADOR FINAL')
    print('='*60)
    print('Basado en V2 + Liquidez (57.1% WR) con ajustes mínimos')
    print('• RSI: 55% (ligero aumento)')
    print('• Price Action: 18% (mejorado conservadoramente)')
    print('• Momentum: 12% (sin volumen contraproducente)')
    print('• Risk Structure: 5% (mantener)')
    print('• Liquidez: 10% (optimizada)')
    print('• Score mínimo: 5.9 (ligero ajuste)')
    print('='*60)

if __name__ == "__main__":
    demo_conservador()