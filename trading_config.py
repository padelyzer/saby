#!/usr/bin/env python3
"""
Configuración central del sistema de trading
Todos los módulos deben usar esta configuración para mantener consistencia
"""

# ===========================================
# SÍMBOLOS A ANALIZAR (BINANCE)
# ===========================================
# Usamos solo formato Binance para consistencia
TRADING_SYMBOLS = [
    'DOGEUSDT',  # Dogecoin
    'ADAUSDT',   # Cardano
    'AVAXUSDT',  # Avalanche
    'SOLUSDT',   # Solana
    'XRPUSDT',   # Ripple
    'LINKUSDT',  # Chainlink
    'DOTUSDT',   # Polkadot
    'BNBUSDT'    # Binance Coin (reemplaza a PEPE que no está disponible)
]

# Alias para compatibilidad
BINANCE_SYMBOLS = TRADING_SYMBOLS

# Mapeo para mantener compatibilidad (si es necesario)
SYMBOL_MAPPING = {
    'DOGEUSDT': 'DOGEUSDT',
    'ADAUSDT': 'ADAUSDT',
    'AVAXUSDT': 'AVAXUSDT',
    'SOLUSDT': 'SOLUSDT',
    'XRPUSDT': 'XRPUSDT',
    'LINKUSDT': 'LINKUSDT',
    'DOTUSDT': 'DOTUSDT',
    'BNBUSDT': 'BNBUSDT'
}

# ===========================================
# FILÓSOFOS DEL SISTEMA
# ===========================================
PHILOSOPHERS = [
    'Socrates',
    'Aristoteles',
    'Platon',
    'Nietzsche',
    'Kant',
    'Descartes',
    'Confucio',
    'SunTzu'
]

# ===========================================
# CONFIGURACIÓN DE TRADING
# ===========================================
DEFAULT_CONFIG = {
    'initial_capital': 10000.0,
    'risk_level': 'balanced',  # conservative, balanced, aggressive
    'max_positions': 5,
    'scan_interval': 300,  # 5 minutos
    'consensus_threshold': 0.65,  # 65% de acuerdo mínimo
}

# ===========================================
# NIVELES DE RIESGO
# ===========================================
RISK_LEVELS = {
    'conservative': {
        'max_position_size': 0.015,  # 1.5% del capital
        'take_profit_base': 0.025,   # 2.5%
        'stop_loss_base': 0.015,      # 1.5%
        'consensus_required': 0.75    # 75% acuerdo
    },
    'balanced': {
        'max_position_size': 0.025,  # 2.5% del capital
        'take_profit_base': 0.040,   # 4%
        'stop_loss_base': 0.020,      # 2%
        'consensus_required': 0.65    # 65% acuerdo
    },
    'aggressive': {
        'max_position_size': 0.040,  # 4% del capital
        'take_profit_base': 0.060,   # 6%
        'stop_loss_base': 0.025,      # 2.5%
        'consensus_required': 0.55    # 55% acuerdo
    }
}

# ===========================================
# CLASIFICACIÓN DE ACTIVOS POR TIPO
# ===========================================
ASSET_TYPES = {
    'LARGE_CAP': {
        'symbols': ['BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT'],
        'strategies': ['momentum', 'mean_reversion', 'trend_following'],
        'volatility': 'medium',
        'volume_threshold': 1.5,  # Multiplicador de volume promedio
        'breakout_confirmation': True
    },
    'UTILITY': {
        'symbols': ['LINKUSDT', 'DOTUSDT', 'AVAXUSDT'],
        'strategies': ['mean_reversion', 'volume_breakout', 'trend_following'],
        'volatility': 'high',
        'volume_threshold': 2.0,
        'breakout_confirmation': True
    },
    'MEME': {
        'symbols': ['DOGEUSDT'],
        'strategies': ['momentum', 'volume_breakout'],
        'volatility': 'extreme',
        'volume_threshold': 3.0,
        'breakout_confirmation': False  # Más agresivo, menos confirmación
    }
}

# ===========================================
# CONFIGURACIÓN DE ESTRATEGIAS POR ACTIVO
# ===========================================
STRATEGY_CONFIG = {
    'momentum': {
        'LARGE_CAP': {
            'rsi_buy': 30, 'rsi_sell': 70,
            'volume_multiplier': 1.5,
            'take_profit': 0.03, 'stop_loss': 0.02
        },
        'UTILITY': {
            'rsi_buy': 25, 'rsi_sell': 75,
            'volume_multiplier': 2.0,
            'take_profit': 0.04, 'stop_loss': 0.025
        },
        'MEME': {
            'rsi_buy': 20, 'rsi_sell': 80,
            'volume_multiplier': 3.0,
            'take_profit': 0.08, 'stop_loss': 0.04
        }
    },
    'mean_reversion': {
        'LARGE_CAP': {
            'bb_std': 2.0, 'rsi_oversold': 35, 'rsi_overbought': 65,
            'take_profit': 0.025, 'stop_loss': 0.015
        },
        'UTILITY': {
            'bb_std': 2.2, 'rsi_oversold': 30, 'rsi_overbought': 70,
            'take_profit': 0.035, 'stop_loss': 0.02
        },
        'MEME': {  # NO recomendado para meme coins
            'bb_std': 2.5, 'rsi_oversold': 25, 'rsi_overbought': 75,
            'take_profit': 0.05, 'stop_loss': 0.03
        }
    },
    'trend_following': {
        'LARGE_CAP': {
            'ema_fast': 9, 'ema_medium': 20, 'ema_slow': 50,
            'volume_multiplier': 1.3,
            'take_profit': 0.04, 'stop_loss': 0.025
        },
        'UTILITY': {
            'ema_fast': 12, 'ema_medium': 26, 'ema_slow': 50,
            'volume_multiplier': 1.8,
            'take_profit': 0.05, 'stop_loss': 0.03
        },
        'MEME': {
            'ema_fast': 5, 'ema_medium': 13, 'ema_slow': 21,
            'volume_multiplier': 2.5,
            'take_profit': 0.1, 'stop_loss': 0.05
        }
    },
    'volume_breakout': {
        'LARGE_CAP': {
            'volume_spike': 2.0,  # 2x volumen promedio
            'price_breakout': 0.02,  # 2% arriba de resistencia
            'confirmation_periods': 3,
            'take_profit': 0.04, 'stop_loss': 0.025
        },
        'UTILITY': {
            'volume_spike': 2.5,
            'price_breakout': 0.025,
            'confirmation_periods': 2,
            'take_profit': 0.05, 'stop_loss': 0.03
        },
        'MEME': {
            'volume_spike': 4.0,  # Necesita mucho volumen
            'price_breakout': 0.05,  # 5% breakout
            'confirmation_periods': 1,  # Más agresivo
            'take_profit': 0.12, 'stop_loss': 0.06
        }
    }
}

# ===========================================
# INFORMACIÓN DE SÍMBOLOS PARA UI
# ===========================================
SYMBOL_INFO = {
    "DOGEUSDT": {"name": "Dogecoin", "description": "Criptomoneda meme con alta volatilidad", "type": "MEME"},
    "ADAUSDT": {"name": "Cardano", "description": "Blockchain de tercera generación", "type": "LARGE_CAP"},
    "AVAXUSDT": {"name": "Avalanche", "description": "Plataforma de contratos inteligentes escalable", "type": "UTILITY"},
    "SOLUSDT": {"name": "Solana", "description": "Blockchain de alto rendimiento", "type": "LARGE_CAP"},
    "XRPUSDT": {"name": "Ripple", "description": "Sistema de pagos globales", "type": "LARGE_CAP"},
    "LINKUSDT": {"name": "Chainlink", "description": "Red de oráculos descentralizados", "type": "UTILITY"},
    "DOTUSDT": {"name": "Polkadot", "description": "Protocolo de interoperabilidad", "type": "UTILITY"},
    "BNBUSDT": {"name": "Binance Coin", "description": "Token nativo del exchange Binance", "type": "LARGE_CAP"}
}

def get_symbol(symbol: str) -> str:
    """Retorna el símbolo en formato Binance"""
    return symbol if symbol in TRADING_SYMBOLS else None

def is_valid_symbol(symbol: str) -> bool:
    """Verifica si un símbolo está en la lista permitida"""
    return symbol in TRADING_SYMBOLS or symbol in BINANCE_SYMBOLS

def get_asset_type(symbol: str) -> str:
    """Retorna el tipo de activo para un símbolo"""
    for asset_type, config in ASSET_TYPES.items():
        if symbol in config['symbols']:
            return asset_type
    return 'UNKNOWN'

def get_strategy_config(strategy: str, symbol: str) -> dict:
    """Obtiene configuración específica de estrategia para un símbolo"""
    asset_type = get_asset_type(symbol)
    return STRATEGY_CONFIG.get(strategy, {}).get(asset_type, {})

def get_recommended_strategies(symbol: str) -> list:
    """Retorna estrategias recomendadas para un símbolo"""
    asset_type = get_asset_type(symbol)
    return ASSET_TYPES.get(asset_type, {}).get('strategies', [])

# ===========================================
# CONFIGURACIÓN DE DECIMALES POR SÍMBOLO
# ===========================================
SYMBOL_DECIMALS = {
    'DOGEUSDT': 5,
    'PEPEUSDT': 8,
    'ADAUSDT': 4,
    'XRPUSDT': 4,
    'SOLUSDT': 2,
    'AVAXUSDT': 2,
    'LINKUSDT': 3,
    'DOTUSDT': 3,
    'BNBUSDT': 2
}

def get_asset_config(symbol: str) -> dict:
    """Retorna configuración completa del activo"""
    asset_type = get_asset_type(symbol)
    return ASSET_TYPES.get(asset_type, {})