#!/usr/bin/env python3
"""
Validador de señales para evitar contradicciones
Asegura coherencia en las señales filosóficas
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalValidator:
    """Valida y filtra señales para evitar contradicciones"""
    
    def __init__(self, consensus_threshold: float = 0.65):
        self.consensus_threshold = consensus_threshold
        self.active_signals = {}  # Mapa de símbolo -> señal activa
        self.signal_history = {}
        self.lockout_period = 900  # 15 minutos entre señales opuestas
        
    def validate_philosopher_signals(self, philosophers_votes: List[Dict], symbol: str) -> Optional[Dict]:
        """
        Valida las votaciones de los filósofos y retorna una señal coherente
        
        Args:
            philosophers_votes: Lista de votos de cada filósofo
            symbol: Símbolo del activo
            
        Returns:
            Señal validada o None si no hay consenso
        """
        
        # Contar votos
        buy_votes = []
        sell_votes = []
        hold_votes = []
        
        for vote in philosophers_votes:
            if vote.get('vote') == 'BUY':
                buy_votes.append(vote)
            elif vote.get('vote') == 'SELL':
                sell_votes.append(vote)
            else:
                hold_votes.append(vote)
        
        total_votes = len(philosophers_votes)
        buy_percentage = len(buy_votes) / total_votes
        sell_percentage = len(sell_votes) / total_votes
        
        logger.info(f"📊 Votación para {symbol}:")
        logger.info(f"   BUY: {len(buy_votes)}/{total_votes} ({buy_percentage:.1%})")
        logger.info(f"   SELL: {len(sell_votes)}/{total_votes} ({sell_percentage:.1%})")
        logger.info(f"   HOLD: {len(hold_votes)}/{total_votes}")
        
        # REGLA 1: Necesitamos consenso mínimo
        if buy_percentage < self.consensus_threshold and sell_percentage < self.consensus_threshold:
            logger.warning(f"❌ Sin consenso suficiente (mínimo {self.consensus_threshold:.0%})")
            return None
        
        # REGLA 2: No permitir señales opuestas simultáneas
        if buy_percentage > 0.3 and sell_percentage > 0.3:
            logger.warning(f"⚠️ Señales contradictorias - BUY: {buy_percentage:.1%}, SELL: {sell_percentage:.1%}")
            return None
        
        # REGLA 3: Verificar contra señal activa para este símbolo
        if symbol in self.active_signals:
            active_signal = self.active_signals[symbol]
            time_since_last = datetime.now() - active_signal['timestamp']
            if time_since_last.total_seconds() < self.lockout_period:
                # Si hay una señal activa reciente, no generar señal opuesta
                if (active_signal['action'] == 'BUY' and sell_percentage > buy_percentage) or \
                   (active_signal['action'] == 'SELL' and buy_percentage > sell_percentage):
                    logger.warning(f"🔒 Bloqueando señal opuesta para {symbol} (esperando {self.lockout_period/60:.0f} min)")
                    return None
        
        # Determinar acción ganadora
        if buy_percentage >= self.consensus_threshold:
            action = 'BUY'
            supporting_philosophers = [v['philosopher'] for v in buy_votes]
            confidence = buy_percentage
            avg_confidence = sum([v.get('confidence', 0.5) for v in buy_votes]) / len(buy_votes)
            
        elif sell_percentage >= self.consensus_threshold:
            action = 'SELL'
            supporting_philosophers = [v['philosopher'] for v in sell_votes]
            confidence = sell_percentage
            avg_confidence = sum([v.get('confidence', 0.5) for v in sell_votes]) / len(sell_votes)
        else:
            return None
        
        # Crear señal validada
        validated_signal = {
            'symbol': symbol,
            'action': action,
            'timestamp': datetime.now(),
            'consensus_percentage': confidence,
            'philosopher_confidence': avg_confidence,
            'supporting_philosophers': supporting_philosophers,
            'opposing_philosophers': [v['philosopher'] for v in (sell_votes if action == 'BUY' else buy_votes)],
            'total_philosophers': total_votes,
            'is_unanimous': confidence == 1.0,
            'is_strong_consensus': confidence >= 0.75
        }
        
        # Actualizar señal activa para este símbolo
        self.active_signals[symbol] = validated_signal
        
        # Actualizar historial por símbolo
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []
        self.signal_history[symbol].append(validated_signal)
        
        logger.info(f"✅ Señal validada: {action} con {confidence:.1%} de consenso")
        logger.info(f"   Filósofos a favor: {', '.join(supporting_philosophers)}")
        
        return validated_signal
    
    def check_signal_coherence(self, new_signal: Dict) -> bool:
        """
        Verifica que una nueva señal sea coherente con el historial
        
        Args:
            new_signal: Nueva señal a validar
            
        Returns:
            True si la señal es coherente, False si debe ser rechazada
        """
        
        symbol = new_signal.get('symbol')
        
        if symbol not in self.signal_history or not self.signal_history[symbol]:
            return True
        
        # Obtener últimas señales del mismo símbolo
        last_signals = self.signal_history[symbol][-5:]
        
        if not last_signals:
            return True
        
        last_signal = last_signals[-1]
        time_diff = new_signal['timestamp'] - last_signal['timestamp']
        
        # No permitir cambios muy rápidos de dirección
        if time_diff.total_seconds() < 300:  # 5 minutos
            if last_signal['action'] != new_signal['action']:
                logger.warning(f"🚫 Cambio de dirección muy rápido rechazado")
                return False
        
        # Si hay 3 señales seguidas en la misma dirección, ser más estricto con cambios
        if len(last_signals) >= 3:
            same_direction = all(s['action'] == last_signals[0]['action'] for s in last_signals[-3:])
            if same_direction and new_signal['action'] != last_signals[0]['action']:
                if new_signal['consensus_percentage'] < 0.8:
                    logger.warning(f"🚫 Cambio de tendencia requiere mayor consenso (80%)")
                    return False
        
        return True
    
    def get_current_bias(self, symbol: str) -> Dict:
        """
        Obtiene el sesgo actual del mercado según las señales históricas
        
        Returns:
            Diccionario con información del sesgo actual
        """
        if symbol not in self.signal_history:
            return {'bias': 'NEUTRAL', 'strength': 0}
            
        symbol_signals = self.signal_history[symbol][-10:]
        
        if not symbol_signals:
            return {'bias': 'NEUTRAL', 'strength': 0}
        
        buy_count = sum(1 for s in symbol_signals if s['action'] == 'BUY')
        sell_count = sum(1 for s in symbol_signals if s['action'] == 'SELL')
        
        if buy_count > sell_count * 1.5:
            return {'bias': 'BULLISH', 'strength': buy_count / len(symbol_signals)}
        elif sell_count > buy_count * 1.5:
            return {'bias': 'BEARISH', 'strength': sell_count / len(symbol_signals)}
        else:
            return {'bias': 'NEUTRAL', 'strength': 0.5}


# Singleton global para usar en el sistema
signal_validator = SignalValidator(consensus_threshold=0.65)

if __name__ == "__main__":
    # Test del validador
    validator = SignalValidator()
    
    # Caso 1: Consenso claro de BUY
    votes1 = [
        {'philosopher': 'Socrates', 'vote': 'BUY', 'confidence': 0.8},
        {'philosopher': 'Aristoteles', 'vote': 'BUY', 'confidence': 0.7},
        {'philosopher': 'Platon', 'vote': 'BUY', 'confidence': 0.75},
        {'philosopher': 'Nietzsche', 'vote': 'HOLD', 'confidence': 0.5},
    ]
    
    signal1 = validator.validate_philosopher_signals(votes1, 'SOLUSDT')
    print(f"\nSeñal 1: {signal1}")
    
    # Caso 2: Señales contradictorias (debe rechazarse)
    votes2 = [
        {'philosopher': 'Socrates', 'vote': 'BUY', 'confidence': 0.8},
        {'philosopher': 'Aristoteles', 'vote': 'SELL', 'confidence': 0.7},
        {'philosopher': 'Platon', 'vote': 'BUY', 'confidence': 0.6},
        {'philosopher': 'Nietzsche', 'vote': 'SELL', 'confidence': 0.8},
    ]
    
    signal2 = validator.validate_philosopher_signals(votes2, 'SOLUSDT')
    print(f"\nSeñal 2 (contradictoria): {signal2}")
    
    # Caso 3: Consenso de SELL
    votes3 = [
        {'philosopher': 'Socrates', 'vote': 'SELL', 'confidence': 0.9},
        {'philosopher': 'Aristoteles', 'vote': 'SELL', 'confidence': 0.8},
        {'philosopher': 'Platon', 'vote': 'SELL', 'confidence': 0.7},
        {'philosopher': 'Nietzsche', 'vote': 'HOLD', 'confidence': 0.5},
    ]
    
    signal3 = validator.validate_philosopher_signals(votes3, 'SOLUSDT')
    print(f"\nSeñal 3: {signal3}")