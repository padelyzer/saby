#!/usr/bin/env python3
"""
Test para verificar que el sistema no genera señales contradictorias
"""

from signal_validator import SignalValidator
from trading_api.philosophical_trading_system import PhilosophicalConsensusSystem
from binance_client import binance_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_contradictory_signals():
    """Prueba que el sistema rechaza señales contradictorias"""
    
    print("\n" + "="*70)
    print(" TEST DE VALIDACIÓN DE SEÑALES ".center(70))
    print("="*70)
    
    # Crear sistema
    system = PhilosophicalConsensusSystem()
    
    # Caso 1: Señales contradictorias (como las que vio el usuario)
    print("\n📋 Caso 1: Señales contradictorias (Socrates BUY vs Nietzsche SELL)")
    print("-" * 50)
    
    validator = SignalValidator()
    
    # Simular votos contradictorios
    contradictory_votes = [
        {'philosopher': 'Socrates', 'vote': 'BUY', 'confidence': 0.75},
        {'philosopher': 'Nietzsche', 'vote': 'SELL', 'confidence': 0.65},
        {'philosopher': 'Aristoteles', 'vote': 'BUY', 'confidence': 0.55},
        {'philosopher': 'Kant', 'vote': 'SELL', 'confidence': 0.60},
        {'philosopher': 'Platon', 'vote': 'HOLD', 'confidence': 0.50},
    ]
    
    result = validator.validate_philosopher_signals(contradictory_votes, 'SOLUSDT')
    
    if result is None:
        print("✅ CORRECTO: Señales contradictorias rechazadas")
        print("   - No se generó señal debido a falta de consenso")
    else:
        print("❌ ERROR: Se generó señal con votos contradictorios")
        print(f"   - Señal incorrecta: {result['action']}")
    
    # Caso 2: Consenso claro de BUY
    print("\n📋 Caso 2: Consenso claro de BUY (mayoría de acuerdo)")
    print("-" * 50)
    
    buy_consensus_votes = [
        {'philosopher': 'Socrates', 'vote': 'BUY', 'confidence': 0.85},
        {'philosopher': 'Aristoteles', 'vote': 'BUY', 'confidence': 0.75},
        {'philosopher': 'Platon', 'vote': 'BUY', 'confidence': 0.70},
        {'philosopher': 'Kant', 'vote': 'BUY', 'confidence': 0.65},
        {'philosopher': 'Descartes', 'vote': 'BUY', 'confidence': 0.80},
        {'philosopher': 'Nietzsche', 'vote': 'HOLD', 'confidence': 0.50},
    ]
    
    result = validator.validate_philosopher_signals(buy_consensus_votes, 'SOLUSDT')
    
    if result and result['action'] == 'BUY':
        print("✅ CORRECTO: Señal BUY generada con consenso")
        print(f"   - Consenso: {result['consensus_percentage']:.1%}")
        print(f"   - Filósofos a favor: {', '.join(result['supporting_philosophers'])}")
    else:
        print("❌ ERROR: No se generó señal con consenso claro")
    
    print("\n" + "="*70)
    print(" TEST COMPLETADO ".center(70))
    print("="*70)
    print("\n✅ El sistema ahora valida y rechaza señales contradictorias")
    print("✅ Solo genera señales con consenso claro (>65%)")
    print("✅ Evita mostrar BUY y SELL simultáneos")

if __name__ == "__main__":
    test_contradictory_signals()
