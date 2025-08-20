#!/usr/bin/env python3
"""
Sistema de Filtrado y Consenso Filosófico
Resuelve conflictos entre señales contradictorias
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np

@dataclass
class ConflictResolution:
    """Resolución de conflictos entre filósofos"""
    timestamp: datetime
    symbol: str
    philosophers_buy: List[str]
    philosophers_sell: List[str]
    resolution: str  # BUY, SELL, WAIT
    confidence: float
    reasoning: str

class PhilosophicalConsensus:
    """Sistema de consenso y filtrado para señales filosóficas"""
    
    def __init__(self):
        self.conflict_window = 300  # 5 minutos para detectar conflictos
        self.min_consensus = 0.6  # 60% de acuerdo mínimo
        self.confidence_threshold = 0.7  # 70% mínimo de confianza
        
        # Pesos por filósofo según condiciones de mercado
        self.philosopher_weights = {
            'TRENDING': {
                'Aristoteles': 1.2,  # Lógica de tendencia
                'Platon': 0.8,       # Patrones ideales
                'Socrates': 0.5,     # Ranging, menos peso
                'Nietzsche': 0.7,    # Contrarian
                'Kant': 1.0,         # Reglas estrictas
                'Descartes': 1.1,    # Confirmaciones
                'Confucio': 0.6,     # Equilibrio
                'SunTzu': 1.0        # Timing
            },
            'RANGING': {
                'Socrates': 1.3,     # Experto en rangos
                'Confucio': 1.2,     # Busca equilibrio
                'Aristoteles': 0.7,
                'Platon': 0.9,
                'Nietzsche': 0.8,
                'Kant': 1.0,
                'Descartes': 1.0,
                'SunTzu': 0.9
            },
            'VOLATILE': {
                'SunTzu': 1.3,       # Estrategia de guerra
                'Nietzsche': 1.2,    # Abraza el caos
                'Descartes': 1.1,    # Duda y confirmación
                'Kant': 1.0,         # Reglas estrictas
                'Aristoteles': 0.8,
                'Platon': 0.7,
                'Socrates': 0.6,
                'Confucio': 0.5
            }
        }
    
    def detect_market_regime(self, df: pd.DataFrame) -> str:
        """Detecta el régimen actual del mercado"""
        
        # Calcular ATR para volatilidad
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        atr = ranges.max(axis=1).rolling(14).mean()
        
        current_atr = atr.iloc[-1]
        avg_atr = atr.rolling(50).mean().iloc[-1]
        volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1
        
        # EMAs para tendencia
        ema_20 = df['Close'].ewm(span=20).mean()
        ema_50 = df['Close'].ewm(span=50).mean()
        
        # Determinar régimen
        if volatility_ratio > 1.5:
            return 'VOLATILE'
        elif abs(ema_20.iloc[-1] - ema_50.iloc[-1]) / ema_50.iloc[-1] > 0.02:
            return 'TRENDING'
        else:
            return 'RANGING'
    
    def check_signal_conflicts(self, signals: List[Dict], time_window: int = None) -> List[List[Dict]]:
        """Agrupa señales que están en conflicto temporal"""
        
        if time_window is None:
            time_window = self.conflict_window
        
        conflicts = []
        processed = set()
        
        for i, signal1 in enumerate(signals):
            if i in processed:
                continue
                
            conflict_group = [signal1]
            processed.add(i)
            
            for j, signal2 in enumerate(signals[i+1:], i+1):
                if j in processed:
                    continue
                    
                # Verificar si están en la ventana de tiempo
                time1 = datetime.fromisoformat(signal1['timestamp'])
                time2 = datetime.fromisoformat(signal2['timestamp'])
                
                if abs((time2 - time1).total_seconds()) <= time_window:
                    # Mismo símbolo pero acción opuesta
                    if (signal1['symbol'] == signal2['symbol'] and 
                        signal1['action'] != signal2['action']):
                        conflict_group.append(signal2)
                        processed.add(j)
            
            if len(conflict_group) > 1:
                conflicts.append(conflict_group)
        
        return conflicts
    
    def resolve_conflict(self, conflicting_signals: List[Dict], market_regime: str) -> ConflictResolution:
        """Resuelve conflictos entre señales usando consenso ponderado"""
        
        symbol = conflicting_signals[0]['symbol']
        
        # Separar señales por tipo
        buy_signals = []
        sell_signals = []
        
        for signal in conflicting_signals:
            if 'BUY' in signal['action']:
                buy_signals.append(signal)
            else:
                sell_signals.append(signal)
        
        # Calcular puntaje ponderado
        weights = self.philosopher_weights[market_regime]
        
        buy_score = 0
        sell_score = 0
        
        for signal in buy_signals:
            philosopher = signal.get('philosopher', 'Unknown')
            confidence = signal.get('confidence', 0.5)
            weight = weights.get(philosopher, 1.0)
            buy_score += confidence * weight
        
        for signal in sell_signals:
            philosopher = signal.get('philosopher', 'Unknown')
            confidence = signal.get('confidence', 0.5)
            weight = weights.get(philosopher, 1.0)
            sell_score += confidence * weight
        
        # Normalizar scores
        total_score = buy_score + sell_score
        if total_score > 0:
            buy_probability = buy_score / total_score
            sell_probability = sell_score / total_score
        else:
            buy_probability = 0.5
            sell_probability = 0.5
        
        # Resolver conflicto
        if buy_probability > self.min_consensus:
            resolution = 'BUY'
            confidence = buy_probability
            reasoning = f"Consenso BUY: {buy_probability:.1%} vs SELL: {sell_probability:.1%}"
        elif sell_probability > self.min_consensus:
            resolution = 'SELL'
            confidence = sell_probability
            reasoning = f"Consenso SELL: {sell_probability:.1%} vs BUY: {buy_probability:.1%}"
        else:
            resolution = 'WAIT'
            confidence = max(buy_probability, sell_probability)
            reasoning = f"No hay consenso claro. BUY: {buy_probability:.1%}, SELL: {sell_probability:.1%}"
        
        return ConflictResolution(
            timestamp=datetime.now(),
            symbol=symbol,
            philosophers_buy=[s.get('philosopher', 'Unknown') for s in buy_signals],
            philosophers_sell=[s.get('philosopher', 'Unknown') for s in sell_signals],
            resolution=resolution,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def filter_signals(self, signals: List[Dict], market_data: pd.DataFrame) -> List[Dict]:
        """Filtra y resuelve conflictos en las señales"""
        
        # Detectar régimen de mercado
        market_regime = self.detect_market_regime(market_data)
        print(f"📊 Régimen de mercado detectado: {market_regime}")
        
        # Detectar conflictos
        conflicts = self.check_signal_conflicts(signals)
        
        if conflicts:
            print(f"\n⚠️ Detectados {len(conflicts)} grupos de señales en conflicto")
            
            filtered_signals = []
            conflicted_indices = set()
            
            # Resolver cada conflicto
            for conflict_group in conflicts:
                resolution = self.resolve_conflict(conflict_group, market_regime)
                
                print(f"\n🔧 Conflicto en {resolution.symbol}:")
                print(f"   BUY: {', '.join(resolution.philosophers_buy)}")
                print(f"   SELL: {', '.join(resolution.philosophers_sell)}")
                print(f"   ✅ Resolución: {resolution.resolution} ({resolution.confidence:.1%})")
                print(f"   Razón: {resolution.reasoning}")
                
                # Agregar índices al conjunto de conflictos
                for signal in conflict_group:
                    idx = signals.index(signal)
                    conflicted_indices.add(idx)
                
                # Si hay resolución clara, crear señal consensuada
                if resolution.resolution != 'WAIT' and resolution.confidence >= self.confidence_threshold:
                    # Tomar la mejor señal del lado ganador
                    if resolution.resolution == 'BUY':
                        best_signal = max([s for s in conflict_group if 'BUY' in s['action']], 
                                        key=lambda x: x.get('confidence', 0))
                    else:
                        best_signal = max([s for s in conflict_group if 'SELL' in s['action']], 
                                        key=lambda x: x.get('confidence', 0))
                    
                    # Ajustar confianza con el consenso
                    best_signal['confidence'] = resolution.confidence
                    best_signal['consensus'] = True
                    best_signal['consensus_reasoning'] = resolution.reasoning
                    filtered_signals.append(best_signal)
            
            # Agregar señales no conflictivas
            for i, signal in enumerate(signals):
                if i not in conflicted_indices:
                    # Validar confianza mínima
                    if signal.get('confidence', 0) >= self.confidence_threshold:
                        filtered_signals.append(signal)
            
            return filtered_signals
        else:
            print("✅ No hay conflictos entre señales")
            # Solo filtrar por confianza
            return [s for s in signals if s.get('confidence', 0) >= self.confidence_threshold]
    
    def add_technical_validation(self, signal: Dict, market_data: pd.DataFrame) -> Dict:
        """Añade validación técnica adicional a la señal"""
        
        current_price = market_data['Close'].iloc[-1]
        
        # Calcular RSI
        delta = market_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Validación técnica
        technical_score = 0
        validations = []
        
        if 'BUY' in signal['action']:
            if current_rsi < 40:
                technical_score += 0.3
                validations.append("RSI favorable para compra")
            elif current_rsi < 30:
                technical_score += 0.5
                validations.append("RSI en sobreventa extrema")
            
            # EMA validation
            ema_9 = market_data['Close'].ewm(span=9).mean().iloc[-1]
            if current_price > ema_9:
                technical_score += 0.2
                validations.append("Precio sobre EMA9")
        
        else:  # SELL
            if current_rsi > 60:
                technical_score += 0.3
                validations.append("RSI favorable para venta")
            elif current_rsi > 70:
                technical_score += 0.5
                validations.append("RSI en sobrecompra extrema")
            
            ema_9 = market_data['Close'].ewm(span=9).mean().iloc[-1]
            if current_price < ema_9:
                technical_score += 0.2
                validations.append("Precio bajo EMA9")
        
        # Ajustar confianza con validación técnica
        original_confidence = signal.get('confidence', 0.5)
        adjusted_confidence = original_confidence * (1 + technical_score * 0.3)
        adjusted_confidence = min(adjusted_confidence, 0.95)  # Cap at 95%
        
        signal['original_confidence'] = original_confidence
        signal['confidence'] = adjusted_confidence
        signal['technical_validations'] = validations
        signal['technical_score'] = technical_score
        
        return signal


def main():
    """Función de prueba del sistema de consenso"""
    
    # Simular señales conflictivas (como las del screenshot)
    test_signals = [
        {
            'timestamp': '2025-08-18T01:42:00',
            'philosopher': 'Aristoteles',
            'symbol': 'DOGE',
            'action': 'BUY',
            'entry_price': 0.22,
            'confidence': 0.825
        },
        {
            'timestamp': '2025-08-18T01:48:00',
            'philosopher': 'Platon',
            'symbol': 'DOGE',
            'action': 'SELL',
            'entry_price': 0.22,
            'confidence': 0.775
        },
        {
            'timestamp': '2025-08-18T01:57:00',
            'philosopher': 'Socrates',
            'symbol': 'DOGE',
            'action': 'BUY',
            'entry_price': 0.22,
            'confidence': 0.65
        }
    ]
    
    # Crear datos de mercado simulados
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
    market_data = pd.DataFrame({
        'Date': dates,
        'Open': np.random.randn(100).cumsum() + 0.22,
        'High': np.random.randn(100).cumsum() + 0.23,
        'Low': np.random.randn(100).cumsum() + 0.21,
        'Close': np.random.randn(100).cumsum() + 0.22,
        'Volume': np.random.randint(1000000, 10000000, 100)
    })
    
    # Sistema de consenso
    consensus = PhilosophicalConsensus()
    
    print("=" * 70)
    print(" SISTEMA DE CONSENSO FILOSÓFICO ".center(70))
    print("=" * 70)
    
    # Filtrar señales
    filtered = consensus.filter_signals(test_signals, market_data)
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"Señales originales: {len(test_signals)}")
    print(f"Señales filtradas: {len(filtered)}")
    
    for signal in filtered:
        print(f"\n✅ Señal aprobada:")
        print(f"   Filósofo: {signal.get('philosopher')}")
        print(f"   Acción: {signal['action']}")
        print(f"   Confianza: {signal['confidence']:.1%}")
        if signal.get('consensus'):
            print(f"   📌 {signal['consensus_reasoning']}")


if __name__ == "__main__":
    main()