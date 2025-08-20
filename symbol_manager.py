#!/usr/bin/env python3
"""
Symbol Manager - Gestión centralizada de símbolos de trading
"""

from typing import List, Dict, Optional
import json
import os
from datetime import datetime

class SymbolManager:
    """
    Gestor centralizado de símbolos para asegurar consistencia
    en todo el sistema
    """
    
    # Símbolos oficiales del sistema
    ACTIVE_SYMBOLS = [
        "SOLUSDT",   # Solana
        "ADAUSDT",   # Cardano
        "DOGEUSDT",  # Dogecoin
        "XRPUSDT",   # Ripple
        "AVAXUSDT",  # Avalanche
        "LINKUSDT",  # Chainlink
        "DOTUSDT",   # Polkadot
        "PEPEUSDT"   # Pepe
    ]
    
    # Configuración por símbolo
    SYMBOL_CONFIG = {
        "SOLUSDT": {
            "name": "Solana",
            "min_trade_size": 0.1,
            "decimals": 2,
            "category": "L1",
            "risk_level": "medium",
            "max_position_pct": 0.15
        },
        "ADAUSDT": {
            "name": "Cardano",
            "min_trade_size": 10,
            "decimals": 4,
            "category": "L1",
            "risk_level": "medium",
            "max_position_pct": 0.12
        },
        "DOGEUSDT": {
            "name": "Dogecoin",
            "min_trade_size": 100,
            "decimals": 5,
            "category": "MEME",
            "risk_level": "high",
            "max_position_pct": 0.08
        },
        "XRPUSDT": {
            "name": "Ripple",
            "min_trade_size": 10,
            "decimals": 4,
            "category": "PAYMENT",
            "risk_level": "medium",
            "max_position_pct": 0.12
        },
        "AVAXUSDT": {
            "name": "Avalanche",
            "min_trade_size": 0.5,
            "decimals": 2,
            "category": "L1",
            "risk_level": "medium",
            "max_position_pct": 0.10
        },
        "LINKUSDT": {
            "name": "Chainlink",
            "min_trade_size": 1,
            "decimals": 3,
            "category": "ORACLE",
            "risk_level": "low",
            "max_position_pct": 0.15
        },
        "DOTUSDT": {
            "name": "Polkadot",
            "min_trade_size": 1,
            "decimals": 3,
            "category": "L0",
            "risk_level": "medium",
            "max_position_pct": 0.10
        },
        "PEPEUSDT": {
            "name": "Pepe",
            "min_trade_size": 1000000,
            "decimals": 8,
            "category": "MEME",
            "risk_level": "very_high",
            "max_position_pct": 0.05
        }
    }
    
    # Correlaciones conocidas entre símbolos
    CORRELATIONS = {
        ("SOLUSDT", "AVAXUSDT"): 0.75,  # Alta correlación (ambos L1)
        ("ADAUSDT", "DOTUSDT"): 0.70,   # Correlación media-alta
        ("DOGEUSDT", "PEPEUSDT"): 0.65, # Correlación meme coins
        ("LINKUSDT", "XRPUSDT"): 0.45,  # Baja correlación
    }
    
    def __init__(self):
        self.custom_symbols = []
        self.disabled_symbols = []
        self.load_config()
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """Verifica si un símbolo es válido"""
        return symbol in self.ACTIVE_SYMBOLS and symbol not in self.disabled_symbols
    
    def get_active_symbols(self) -> List[str]:
        """Retorna lista de símbolos activos"""
        return [s for s in self.ACTIVE_SYMBOLS if s not in self.disabled_symbols]
    
    def get_symbol_config(self, symbol: str) -> Optional[Dict]:
        """Obtiene configuración de un símbolo"""
        if not self.is_valid_symbol(symbol):
            return None
        return self.SYMBOL_CONFIG.get(symbol, {})
    
    def get_symbol_name(self, symbol: str) -> str:
        """Obtiene nombre legible del símbolo"""
        config = self.get_symbol_config(symbol)
        return config.get('name', symbol) if config else symbol
    
    def get_risk_level(self, symbol: str) -> str:
        """Obtiene nivel de riesgo del símbolo"""
        config = self.get_symbol_config(symbol)
        return config.get('risk_level', 'unknown') if config else 'unknown'
    
    def get_max_position_size(self, symbol: str, total_capital: float) -> float:
        """Calcula tamaño máximo de posición para un símbolo"""
        config = self.get_symbol_config(symbol)
        if config:
            max_pct = config.get('max_position_pct', 0.10)
            return total_capital * max_pct
        return total_capital * 0.05  # 5% por defecto
    
    def get_correlated_symbols(self, symbol: str, threshold: float = 0.6) -> List[Dict]:
        """Obtiene símbolos correlacionados"""
        correlated = []
        
        for (sym1, sym2), correlation in self.CORRELATIONS.items():
            if correlation >= threshold:
                if sym1 == symbol:
                    correlated.append({
                        'symbol': sym2,
                        'correlation': correlation
                    })
                elif sym2 == symbol:
                    correlated.append({
                        'symbol': sym1,
                        'correlation': correlation
                    })
        
        return correlated
    
    def calculate_portfolio_correlation_risk(self, positions: Dict[str, float]) -> float:
        """
        Calcula riesgo de correlación del portfolio
        
        Args:
            positions: Dict con símbolo -> exposición en USD
        
        Returns:
            Score de riesgo de correlación (0-1, donde 1 es máximo riesgo)
        """
        total_exposure = sum(positions.values())
        if total_exposure == 0:
            return 0
        
        correlation_risk = 0
        
        # Verificar exposición por categoría
        category_exposure = {}
        for symbol, exposure in positions.items():
            config = self.get_symbol_config(symbol)
            if config:
                category = config.get('category', 'OTHER')
                category_exposure[category] = category_exposure.get(category, 0) + exposure
        
        # Penalizar concentración en una categoría
        for category, exposure in category_exposure.items():
            concentration = exposure / total_exposure
            if concentration > 0.4:  # Más del 40% en una categoría
                correlation_risk += (concentration - 0.4) * 2
        
        # Verificar correlaciones directas
        symbols = list(positions.keys())
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                correlation = self.get_correlation(sym1, sym2)
                if correlation > 0.6:
                    combined_exposure = (positions[sym1] + positions[sym2]) / total_exposure
                    correlation_risk += correlation * combined_exposure * 0.5
        
        return min(correlation_risk, 1.0)
    
    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Obtiene correlación entre dos símbolos"""
        key1 = (symbol1, symbol2)
        key2 = (symbol2, symbol1)
        
        if key1 in self.CORRELATIONS:
            return self.CORRELATIONS[key1]
        elif key2 in self.CORRELATIONS:
            return self.CORRELATIONS[key2]
        
        # Correlación por categoría si no hay dato específico
        config1 = self.get_symbol_config(symbol1)
        config2 = self.get_symbol_config(symbol2)
        
        if config1 and config2:
            if config1.get('category') == config2.get('category'):
                return 0.6  # Correlación media para misma categoría
        
        return 0.3  # Correlación baja por defecto
    
    def validate_portfolio_allocation(self, allocations: Dict[str, float]) -> Dict:
        """
        Valida y ajusta allocaciones de portfolio
        
        Args:
            allocations: Dict con símbolo -> % de allocación
        
        Returns:
            Dict con allocaciones validadas y warnings
        """
        warnings = []
        adjusted = allocations.copy()
        
        # Verificar suma total
        total = sum(allocations.values())
        if abs(total - 1.0) > 0.01:
            warnings.append(f"Allocación total es {total*100:.1f}%, debe ser 100%")
            # Normalizar
            for symbol in adjusted:
                adjusted[symbol] = adjusted[symbol] / total
        
        # Verificar límites por símbolo
        for symbol, allocation in adjusted.items():
            config = self.get_symbol_config(symbol)
            if config:
                max_pct = config.get('max_position_pct', 0.15)
                if allocation > max_pct:
                    warnings.append(
                        f"{symbol}: Reducido de {allocation*100:.1f}% a {max_pct*100:.1f}% (límite máximo)"
                    )
                    adjusted[symbol] = max_pct
        
        # Verificar concentración por categoría
        category_allocation = {}
        for symbol, allocation in adjusted.items():
            config = self.get_symbol_config(symbol)
            if config:
                category = config.get('category', 'OTHER')
                category_allocation[category] = category_allocation.get(category, 0) + allocation
        
        for category, total_alloc in category_allocation.items():
            if total_alloc > 0.5:  # Máximo 50% por categoría
                warnings.append(
                    f"Categoría {category}: {total_alloc*100:.1f}% de exposición (máximo recomendado: 50%)"
                )
        
        # Re-normalizar si hubo ajustes
        total_adjusted = sum(adjusted.values())
        if abs(total_adjusted - 1.0) > 0.01:
            for symbol in adjusted:
                adjusted[symbol] = adjusted[symbol] / total_adjusted
        
        return {
            'allocations': adjusted,
            'warnings': warnings,
            'valid': len(warnings) == 0
        }
    
    def disable_symbol(self, symbol: str, reason: str = ""):
        """Desactiva temporalmente un símbolo"""
        if symbol in self.ACTIVE_SYMBOLS and symbol not in self.disabled_symbols:
            self.disabled_symbols.append(symbol)
            self.save_config()
            
            # Log
            print(f"⚠️ Símbolo {symbol} desactivado: {reason}")
    
    def enable_symbol(self, symbol: str):
        """Reactiva un símbolo"""
        if symbol in self.disabled_symbols:
            self.disabled_symbols.remove(symbol)
            self.save_config()
            
            print(f"✅ Símbolo {symbol} reactivado")
    
    def save_config(self):
        """Guarda configuración personalizada"""
        config = {
            'disabled_symbols': self.disabled_symbols,
            'custom_symbols': self.custom_symbols,
            'last_update': datetime.now().isoformat()
        }
        
        try:
            with open('symbol_config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error guardando configuración: {e}")
    
    def load_config(self):
        """Carga configuración personalizada"""
        if os.path.exists('symbol_config.json'):
            try:
                with open('symbol_config.json', 'r') as f:
                    config = json.load(f)
                    self.disabled_symbols = config.get('disabled_symbols', [])
                    self.custom_symbols = config.get('custom_symbols', [])
            except Exception as e:
                print(f"Error cargando configuración: {e}")
    
    def get_symbol_stats(self) -> Dict:
        """Obtiene estadísticas de los símbolos"""
        active = self.get_active_symbols()
        
        # Contar por categoría
        categories = {}
        risk_levels = {}
        
        for symbol in active:
            config = self.get_symbol_config(symbol)
            if config:
                cat = config.get('category', 'OTHER')
                categories[cat] = categories.get(cat, 0) + 1
                
                risk = config.get('risk_level', 'unknown')
                risk_levels[risk] = risk_levels.get(risk, 0) + 1
        
        return {
            'total_symbols': len(self.ACTIVE_SYMBOLS),
            'active_symbols': len(active),
            'disabled_symbols': len(self.disabled_symbols),
            'by_category': categories,
            'by_risk_level': risk_levels,
            'categories': list(set(c.get('category', 'OTHER') 
                                 for c in self.SYMBOL_CONFIG.values()))
        }


# Singleton global
symbol_manager = SymbolManager()


if __name__ == "__main__":
    # Test del Symbol Manager
    print("🎯 Testing Symbol Manager...")
    
    # Símbolos activos
    print(f"\n📊 Símbolos activos: {symbol_manager.get_active_symbols()}")
    
    # Configuración de un símbolo
    config = symbol_manager.get_symbol_config("SOLUSDT")
    print(f"\n⚙️ Configuración SOLUSDT: {json.dumps(config, indent=2)}")
    
    # Correlaciones
    correlated = symbol_manager.get_correlated_symbols("SOLUSDT")
    print(f"\n🔗 Símbolos correlacionados con SOLUSDT: {correlated}")
    
    # Validar portfolio
    test_allocation = {
        "SOLUSDT": 0.25,
        "ADAUSDT": 0.20,
        "DOGEUSDT": 0.15,
        "PEPEUSDT": 0.15,  # Mucho para alto riesgo
        "LINKUSDT": 0.25
    }
    
    validation = symbol_manager.validate_portfolio_allocation(test_allocation)
    print(f"\n✅ Validación de portfolio:")
    print(f"Allocaciones ajustadas: {json.dumps(validation['allocations'], indent=2)}")
    print(f"Warnings: {validation['warnings']}")
    
    # Riesgo de correlación
    test_positions = {
        "SOLUSDT": 2500,
        "AVAXUSDT": 2000,  # Alta correlación con SOL
        "DOGEUSDT": 1000,
        "PEPEUSDT": 500    # Correlación con DOGE
    }
    
    correlation_risk = symbol_manager.calculate_portfolio_correlation_risk(test_positions)
    print(f"\n⚠️ Riesgo de correlación del portfolio: {correlation_risk:.2f}")
    
    # Estadísticas
    stats = symbol_manager.get_symbol_stats()
    print(f"\n📈 Estadísticas de símbolos: {json.dumps(stats, indent=2)}")