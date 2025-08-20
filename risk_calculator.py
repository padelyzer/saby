#!/usr/bin/env python3
"""
Risk Calculator - Sistema de cálculo y verificación de riesgo
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

from symbol_manager import symbol_manager
from error_handler import error_handler

class RiskCalculator:
    """
    Calculadora avanzada de riesgo con:
    - Kelly Criterion
    - Value at Risk (VaR)
    - Position sizing
    - Portfolio optimization
    """
    
    def __init__(self):
        self.risk_limits = {
            'max_risk_per_trade': 0.02,      # 2% máximo riesgo por trade
            'max_daily_risk': 0.06,          # 6% máximo riesgo diario
            'max_portfolio_risk': 0.20,      # 20% máximo drawdown aceptable
            'max_leverage': 3,               # Leverage máximo
            'min_risk_reward': 2.0,          # Mínimo R:R ratio
            'max_correlated_exposure': 0.30  # 30% máx en activos correlacionados
        }
    
    def calculate_position_size_kelly(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        capital: float,
        max_risk_pct: float = 0.02
    ) -> float:
        """
        Calcula tamaño de posición usando Kelly Criterion
        
        Kelly % = (p * b - q) / b
        donde:
        p = probabilidad de ganar
        q = probabilidad de perder (1-p)
        b = ratio ganancia/pérdida
        """
        
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return capital * max_risk_pct
        
        # Calcular Kelly percentage
        p = win_rate
        q = 1 - win_rate
        b = abs(avg_win / avg_loss)
        
        kelly_pct = (p * b - q) / b if b > 0 else 0
        
        # Kelly Criterion tiende a ser agresivo, usar fracción
        kelly_fraction = 0.25  # Usar 25% del Kelly
        adjusted_kelly = kelly_pct * kelly_fraction
        
        # Limitar al máximo riesgo permitido
        position_pct = min(adjusted_kelly, max_risk_pct)
        position_pct = max(position_pct, 0)  # No negativo
        
        return capital * position_pct
    
    def calculate_value_at_risk(
        self,
        returns: List[float],
        confidence_level: float = 0.95,
        holding_period: int = 1
    ) -> Dict:
        """
        Calcula Value at Risk (VaR)
        
        Args:
            returns: Lista de retornos históricos
            confidence_level: Nivel de confianza (ej: 0.95 para 95%)
            holding_period: Período de tenencia en días
        """
        
        if not returns or len(returns) < 20:
            return {
                'var_historical': 0,
                'var_parametric': 0,
                'cvar': 0,
                'warning': 'Datos insuficientes para cálculo preciso'
            }
        
        returns_array = np.array(returns)
        
        # VaR Histórico
        var_historical = np.percentile(returns_array, (1 - confidence_level) * 100)
        
        # VaR Paramétrico (asumiendo distribución normal)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        z_score = np.abs(np.percentile(np.random.standard_normal(10000), (1 - confidence_level) * 100))
        var_parametric = mean_return - z_score * std_return * np.sqrt(holding_period)
        
        # CVaR (Conditional VaR) - pérdida esperada más allá del VaR
        losses_beyond_var = returns_array[returns_array <= var_historical]
        cvar = np.mean(losses_beyond_var) if len(losses_beyond_var) > 0 else var_historical
        
        return {
            'var_historical': abs(var_historical),
            'var_parametric': abs(var_parametric),
            'cvar': abs(cvar),
            'confidence_level': confidence_level,
            'holding_period': holding_period,
            'sample_size': len(returns)
        }
    
    def calculate_optimal_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        capital: float,
        symbol: str,
        current_positions: Dict[str, float] = None
    ) -> Dict:
        """
        Calcula tamaño óptimo de posición considerando múltiples factores
        """
        
        # Configuración del símbolo
        symbol_config = symbol_manager.get_symbol_config(symbol)
        if not symbol_config:
            return {
                'success': False,
                'error': f'Símbolo {symbol} no válido'
            }
        
        # Risk per trade
        risk_amount = capital * self.risk_limits['max_risk_per_trade']
        
        # Stop loss distance
        stop_distance = abs(entry_price - stop_loss) / entry_price
        
        if stop_distance == 0:
            return {
                'success': False,
                'error': 'Stop loss inválido (igual al entry)'
            }
        
        # Posición base basada en riesgo
        base_position_value = risk_amount / stop_distance
        
        # Ajustar por límites del símbolo
        max_position_pct = symbol_config.get('max_position_pct', 0.10)
        max_position_value = capital * max_position_pct
        
        # Ajustar por correlación si hay posiciones existentes
        correlation_adjustment = 1.0
        if current_positions:
            correlated = symbol_manager.get_correlated_symbols(symbol, threshold=0.6)
            for corr_symbol in correlated:
                if corr_symbol['symbol'] in current_positions:
                    # Reducir tamaño por correlación
                    correlation_adjustment *= (1 - corr_symbol['correlation'] * 0.3)
        
        # Ajustar por nivel de riesgo del símbolo
        risk_level = symbol_config.get('risk_level', 'medium')
        risk_multipliers = {
            'low': 1.2,
            'medium': 1.0,
            'high': 0.7,
            'very_high': 0.5
        }
        risk_adjustment = risk_multipliers.get(risk_level, 1.0)
        
        # Calcular posición final
        optimal_position_value = min(
            base_position_value * correlation_adjustment * risk_adjustment,
            max_position_value
        )
        
        # Calcular cantidad
        position_size = optimal_position_value / entry_price
        
        # Verificar mínimos
        min_trade_size = symbol_config.get('min_trade_size', 0)
        if position_size < min_trade_size:
            return {
                'success': False,
                'error': f'Posición muy pequeña (mín: {min_trade_size})',
                'suggested_size': min_trade_size
            }
        
        # Calcular métricas de riesgo
        actual_risk = (stop_distance * optimal_position_value) / capital
        risk_reward_ratio = abs((entry_price * 1.03 - entry_price) / (entry_price - stop_loss))  # Asumiendo TP 3%
        
        return {
            'success': True,
            'position_size': position_size,
            'position_value': optimal_position_value,
            'risk_amount': stop_distance * optimal_position_value,
            'risk_percentage': actual_risk * 100,
            'max_loss': stop_distance * optimal_position_value,
            'adjustments': {
                'correlation': correlation_adjustment,
                'risk_level': risk_adjustment
            },
            'risk_reward_ratio': risk_reward_ratio,
            'position_pct_of_capital': (optimal_position_value / capital) * 100
        }
    
    def validate_trade_risk(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        capital: float,
        symbol: str
    ) -> Dict:
        """
        Valida que un trade cumpla con los parámetros de riesgo
        """
        
        validations = []
        warnings = []
        is_valid = True
        
        # Calcular métricas
        position_value = position_size * entry_price
        stop_distance = abs(entry_price - stop_loss) / entry_price
        profit_distance = abs(take_profit - entry_price) / entry_price
        risk_amount = position_value * stop_distance
        risk_pct = risk_amount / capital
        risk_reward = profit_distance / stop_distance if stop_distance > 0 else 0
        
        # Validación 1: Riesgo por trade
        if risk_pct > self.risk_limits['max_risk_per_trade']:
            is_valid = False
            validations.append(
                f"❌ Riesgo excesivo: {risk_pct*100:.2f}% > {self.risk_limits['max_risk_per_trade']*100}% máximo"
            )
        else:
            validations.append(f"✅ Riesgo por trade: {risk_pct*100:.2f}%")
        
        # Validación 2: Risk/Reward ratio
        if risk_reward < self.risk_limits['min_risk_reward']:
            warnings.append(
                f"⚠️ R:R bajo: {risk_reward:.2f} < {self.risk_limits['min_risk_reward']} recomendado"
            )
        else:
            validations.append(f"✅ Risk/Reward: {risk_reward:.2f}")
        
        # Validación 3: Tamaño de posición
        position_pct = position_value / capital
        symbol_config = symbol_manager.get_symbol_config(symbol)
        
        if symbol_config:
            max_position_pct = symbol_config.get('max_position_pct', 0.15)
            if position_pct > max_position_pct:
                warnings.append(
                    f"⚠️ Posición grande: {position_pct*100:.2f}% > {max_position_pct*100}% recomendado para {symbol}"
                )
        
        # Validación 4: Stop loss distance
        if stop_distance > 0.10:  # Más de 10%
            warnings.append(f"⚠️ Stop loss lejano: {stop_distance*100:.2f}%")
        
        # Validación 5: Capital disponible
        if position_value > capital:
            is_valid = False
            validations.append(f"❌ Capital insuficiente: necesitas ${position_value:.2f}")
        
        return {
            'is_valid': is_valid,
            'validations': validations,
            'warnings': warnings,
            'metrics': {
                'position_value': position_value,
                'risk_amount': risk_amount,
                'risk_percentage': risk_pct * 100,
                'risk_reward_ratio': risk_reward,
                'stop_distance_pct': stop_distance * 100,
                'profit_distance_pct': profit_distance * 100,
                'position_pct_of_capital': position_pct * 100
            }
        }
    
    def calculate_portfolio_risk(
        self,
        positions: List[Dict],
        capital: float
    ) -> Dict:
        """
        Calcula riesgo total del portfolio
        
        Args:
            positions: Lista de posiciones con 'symbol', 'size', 'entry_price', 'stop_loss'
        """
        
        if not positions:
            return {
                'total_risk': 0,
                'total_exposure': 0,
                'risk_distribution': {},
                'correlation_risk': 0,
                'warnings': []
            }
        
        total_risk = 0
        total_exposure = 0
        risk_by_symbol = {}
        exposure_by_symbol = {}
        warnings = []
        
        # Calcular riesgo por posición
        for pos in positions:
            symbol = pos['symbol']
            size = pos['size']
            entry = pos['entry_price']
            stop = pos['stop_loss']
            
            position_value = size * entry
            stop_distance = abs(entry - stop) / entry
            risk = position_value * stop_distance
            
            total_risk += risk
            total_exposure += position_value
            risk_by_symbol[symbol] = risk
            exposure_by_symbol[symbol] = position_value
        
        # Calcular porcentajes
        risk_pct = (total_risk / capital) * 100 if capital > 0 else 0
        exposure_pct = (total_exposure / capital) * 100 if capital > 0 else 0
        
        # Verificar límites
        if risk_pct > self.risk_limits['max_daily_risk'] * 100:
            warnings.append(f"⚠️ Riesgo total alto: {risk_pct:.2f}%")
        
        if exposure_pct > 80:
            warnings.append(f"⚠️ Exposición alta: {exposure_pct:.2f}%")
        
        # Calcular riesgo de correlación
        correlation_risk = symbol_manager.calculate_portfolio_correlation_risk(exposure_by_symbol)
        
        if correlation_risk > 0.5:
            warnings.append(f"⚠️ Alto riesgo de correlación: {correlation_risk:.2f}")
        
        # Distribución de riesgo
        risk_distribution = {
            symbol: (risk / total_risk * 100) if total_risk > 0 else 0
            for symbol, risk in risk_by_symbol.items()
        }
        
        # Concentración
        max_concentration = max(risk_distribution.values()) if risk_distribution else 0
        if max_concentration > 40:
            warnings.append(f"⚠️ Concentración de riesgo: {max_concentration:.1f}% en una posición")
        
        return {
            'total_risk': total_risk,
            'total_risk_pct': risk_pct,
            'total_exposure': total_exposure,
            'total_exposure_pct': exposure_pct,
            'risk_distribution': risk_distribution,
            'correlation_risk': correlation_risk,
            'position_count': len(positions),
            'avg_risk_per_position': total_risk / len(positions) if positions else 0,
            'warnings': warnings,
            'risk_score': min(risk_pct / 10 + correlation_risk * 5 + max_concentration / 100, 10)  # Score 0-10
        }
    
    def suggest_position_adjustments(
        self,
        current_positions: List[Dict],
        capital: float,
        target_risk: float = 0.06
    ) -> Dict:
        """
        Sugiere ajustes para optimizar el portfolio
        """
        
        current_risk = self.calculate_portfolio_risk(current_positions, capital)
        suggestions = []
        
        # Si el riesgo es muy alto
        if current_risk['total_risk_pct'] > target_risk * 100:
            reduction_needed = current_risk['total_risk_pct'] - (target_risk * 100)
            suggestions.append(
                f"Reducir riesgo total en {reduction_needed:.1f}% para alcanzar objetivo de {target_risk*100}%"
            )
            
            # Identificar posiciones para reducir
            for pos in current_positions:
                symbol = pos['symbol']
                if symbol in current_risk['risk_distribution']:
                    if current_risk['risk_distribution'][symbol] > 30:
                        suggestions.append(f"Considerar reducir posición en {symbol} (concentración: {current_risk['risk_distribution'][symbol]:.1f}%)")
        
        # Si hay alta correlación
        if current_risk['correlation_risk'] > 0.5:
            suggestions.append("Diversificar en activos menos correlacionados")
            
            # Identificar símbolos correlacionados
            symbols_in_portfolio = [p['symbol'] for p in current_positions]
            for symbol in symbols_in_portfolio:
                correlated = symbol_manager.get_correlated_symbols(symbol, 0.7)
                for corr in correlated:
                    if corr['symbol'] in symbols_in_portfolio:
                        suggestions.append(
                            f"Alta correlación entre {symbol} y {corr['symbol']} ({corr['correlation']:.2f})"
                        )
        
        # Si el riesgo es muy bajo (oportunidad perdida)
        if current_risk['total_risk_pct'] < target_risk * 100 * 0.5:
            suggestions.append(
                f"Riesgo bajo ({current_risk['total_risk_pct']:.1f}%), considerar aumentar posiciones"
            )
        
        return {
            'current_risk_score': current_risk['risk_score'],
            'suggestions': suggestions,
            'optimal_adjustments': self._calculate_optimal_adjustments(current_positions, capital, target_risk)
        }
    
    def _calculate_optimal_adjustments(
        self,
        positions: List[Dict],
        capital: float,
        target_risk: float
    ) -> List[Dict]:
        """Calcula ajustes óptimos para el portfolio"""
        
        adjustments = []
        current_risk = self.calculate_portfolio_risk(positions, capital)
        
        if current_risk['total_risk_pct'] > target_risk * 100:
            # Necesitamos reducir
            scale_factor = (target_risk * 100) / current_risk['total_risk_pct']
            
            for pos in positions:
                new_size = pos['size'] * scale_factor
                adjustments.append({
                    'symbol': pos['symbol'],
                    'current_size': pos['size'],
                    'suggested_size': new_size,
                    'change_pct': (scale_factor - 1) * 100
                })
        
        return adjustments


# Singleton global
risk_calculator = RiskCalculator()


if __name__ == "__main__":
    # Test del Risk Calculator
    print("🧮 Testing Risk Calculator...")
    
    # Test Kelly Criterion
    position_size = risk_calculator.calculate_position_size_kelly(
        win_rate=0.55,
        avg_win=0.03,
        avg_loss=0.01,
        capital=10000
    )
    print(f"\n📊 Kelly Position Size: ${position_size:.2f}")
    
    # Test VaR
    test_returns = np.random.normal(0.001, 0.02, 100).tolist()  # Retornos simulados
    var_result = risk_calculator.calculate_value_at_risk(test_returns)
    print(f"\n📈 Value at Risk (95%): {json.dumps(var_result, indent=2)}")
    
    # Test posición óptima
    optimal = risk_calculator.calculate_optimal_position_size(
        entry_price=234.50,
        stop_loss=228.00,
        capital=10000,
        symbol="SOLUSDT",
        current_positions={"AVAXUSDT": 2000}  # Ya tenemos posición correlacionada
    )
    print(f"\n✅ Posición óptima: {json.dumps(optimal, indent=2)}")
    
    # Test validación de trade
    validation = risk_calculator.validate_trade_risk(
        entry_price=234.50,
        stop_loss=228.00,
        take_profit=248.00,
        position_size=10,
        capital=10000,
        symbol="SOLUSDT"
    )
    print(f"\n🔍 Validación de trade:")
    for v in validation['validations']:
        print(f"  {v}")
    for w in validation['warnings']:
        print(f"  {w}")
    
    # Test riesgo de portfolio
    test_positions = [
        {'symbol': 'SOLUSDT', 'size': 10, 'entry_price': 234.50, 'stop_loss': 228.00},
        {'symbol': 'AVAXUSDT', 'size': 50, 'entry_price': 42.00, 'stop_loss': 40.00},
        {'symbol': 'DOGEUSDT', 'size': 10000, 'entry_price': 0.38, 'stop_loss': 0.36}
    ]
    
    portfolio_risk = risk_calculator.calculate_portfolio_risk(test_positions, 10000)
    print(f"\n💼 Riesgo del Portfolio:")
    print(f"  Riesgo Total: ${portfolio_risk['total_risk']:.2f} ({portfolio_risk['total_risk_pct']:.2f}%)")
    print(f"  Exposición: ${portfolio_risk['total_exposure']:.2f} ({portfolio_risk['total_exposure_pct']:.2f}%)")
    print(f"  Risk Score: {portfolio_risk['risk_score']:.1f}/10")
    
    # Sugerencias
    suggestions = risk_calculator.suggest_position_adjustments(test_positions, 10000)
    print(f"\n💡 Sugerencias:")
    for s in suggestions['suggestions']:
        print(f"  • {s}")