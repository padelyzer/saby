#!/usr/bin/env python3
"""
Dynamic Trailing Stops System
Sistema de trailing stops dinámicos basado en volatilidad y momentum
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class DynamicTrailingStops:
    """
    Sistema de trailing stops dinámicos que se ajusta automáticamente
    basado en:
    1. Volatilidad del mercado (ATR)
    2. Momentum de precio
    3. Estructura de mercado
    4. Score de la señal original
    """
    
    def __init__(self):
        # Configuración de trailing stops
        self.trailing_config = {
            # ATR-based stops
            'atr_based': {
                'enabled': True,
                'atr_period': 14,
                'atr_multiplier_min': 1.5,  # Minimum ATR multiplier
                'atr_multiplier_max': 3.0,  # Maximum ATR multiplier
                'atr_sensitivity': 0.8      # How sensitive to volatility changes
            },
            
            # Momentum-based adjustments
            'momentum_based': {
                'enabled': True,
                'momentum_period': 10,
                'acceleration_threshold': 0.02,  # 2% acceleration
                'tighten_factor': 0.8,          # Tighten stops when momentum slows
                'extend_factor': 1.2             # Extend stops when momentum accelerates
            },
            
            # Structure-based stops
            'structure_based': {
                'enabled': True,
                'swing_periods': 20,
                'support_resistance_buffer': 0.005,  # 0.5% buffer
                'break_retest_logic': True
            },
            
            # Score-based configuration
            'score_based': {
                'high_score_threshold': 8.0,    # Signals > 8.0 get looser stops
                'low_score_threshold': 6.0,     # Signals < 6.0 get tighter stops
                'score_adjustment_factor': 0.2  # 20% adjustment per score tier
            },
            
            # Time-based adjustments
            'time_based': {
                'enabled': True,
                'initial_tight_period': 4,      # First 4 periods tight stops
                'mature_trade_period': 20,      # After 20 periods, different logic
                'weekend_adjustment': 0.9       # Tighter stops on weekends
            }
        }
        
        # Tipos de trailing stops disponibles
        self.stop_types = {
            'ATR_TRAILING': 'ATR-based dynamic trailing stop',
            'MOMENTUM_TRAILING': 'Momentum-based trailing stop',
            'STRUCTURE_TRAILING': 'Support/Resistance based stop',
            'HYBRID_TRAILING': 'Combination of multiple methods',
            'PARABOLIC_SAR': 'Parabolic SAR style trailing'
        }
        
        # Estado de posiciones activas
        self.active_positions = {}
        
    def initialize_trailing_stop(self, symbol: str, position_data: Dict) -> Dict:
        """Inicializa trailing stop para nueva posición"""
        
        try:
            # Obtener datos de mercado
            market_data = self._fetch_market_data(symbol)
            if market_data is None or len(market_data) < 30:
                return self._get_fallback_stop(position_data)
            
            # Calcular indicadores necesarios
            market_data = self._add_trailing_indicators(market_data)
            
            # Determinar configuración inicial de trailing stop
            initial_config = self._calculate_initial_stop_config(position_data, market_data)
            
            # Configurar trailing stop
            trailing_stop = {
                'symbol': symbol,
                'position_id': position_data.get('id', 'unknown'),
                'position_type': position_data['type'],  # LONG/SHORT
                'entry_price': position_data['entry_price'],
                'entry_time': position_data.get('entry_time', datetime.now()),
                'signal_score': position_data.get('signal_score', 6.0),
                
                # Configuración del trailing stop
                'stop_type': initial_config['stop_type'],
                'initial_stop': initial_config['initial_stop'],
                'current_stop': initial_config['initial_stop'],
                'best_price': position_data['entry_price'],
                'trail_distance': initial_config['trail_distance'],
                'trail_distance_pct': initial_config['trail_distance_pct'],
                
                # Parámetros dinámicos
                'atr_multiplier': initial_config['atr_multiplier'],
                'momentum_factor': 1.0,
                'structure_level': None,
                'volatility_regime': initial_config['volatility_regime'],
                
                # Historial
                'stop_history': [initial_config['initial_stop']],
                'price_history': [position_data['entry_price']],
                'adjustment_log': [],
                
                # Estado
                'periods_held': 0,
                'last_update': datetime.now(),
                'triggered': False,
                'trigger_reason': None
            }
            
            # Guardar en posiciones activas
            self.active_positions[symbol] = trailing_stop
            
            print(f"🎯 Trailing stop inicializado para {symbol}")
            print(f"   • Tipo: {initial_config['stop_type']}")
            print(f"   • Stop inicial: ${initial_config['initial_stop']:.2f}")
            print(f"   • Distancia: {initial_config['trail_distance_pct']:.2f}%")
            print(f"   • ATR Multiplier: {initial_config['atr_multiplier']:.2f}")
            
            return trailing_stop
            
        except Exception as e:
            print(f"⚠️ Error inicializando trailing stop: {e}")
            return self._get_fallback_stop(position_data)
    
    def update_trailing_stop(self, symbol: str, current_price: float) -> Dict:
        """Actualiza trailing stop con nuevo precio"""
        
        if symbol not in self.active_positions:
            return {'error': 'No trailing stop active for symbol'}
        
        try:
            position = self.active_positions[symbol]
            
            # Obtener datos actualizados
            market_data = self._fetch_market_data(symbol, periods=50)
            if market_data is None:
                return {'error': 'Cannot fetch market data'}
            
            market_data = self._add_trailing_indicators(market_data)
            current_indicators = market_data.iloc[-1]
            
            # Actualizar historial
            position['price_history'].append(current_price)
            position['periods_held'] += 1
            position['last_update'] = datetime.now()
            
            # Actualizar mejor precio
            if position['position_type'] == 'LONG':
                if current_price > position['best_price']:
                    position['best_price'] = current_price
            else:  # SHORT
                if current_price < position['best_price']:
                    position['best_price'] = current_price
            
            # Calcular nuevo trailing stop
            new_stop_data = self._calculate_dynamic_stop(position, current_price, current_indicators)
            
            # Actualizar stop si es favorable
            stop_updated = self._update_stop_level(position, new_stop_data)
            
            # Verificar si stop fue activado
            triggered = self._check_stop_trigger(position, current_price)
            
            # Log de actualizaciones
            if stop_updated or triggered:
                log_entry = {
                    'timestamp': datetime.now(),
                    'price': current_price,
                    'old_stop': position['current_stop'],
                    'new_stop': new_stop_data['stop_price'],
                    'reason': new_stop_data['reason'],
                    'triggered': triggered
                }
                position['adjustment_log'].append(log_entry)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'current_stop': position['current_stop'],
                'best_price': position['best_price'],
                'stop_updated': stop_updated,
                'triggered': triggered,
                'trigger_reason': position.get('trigger_reason'),
                'trail_distance_pct': position['trail_distance_pct'],
                'unrealized_pnl_pct': self._calculate_unrealized_pnl_pct(position, current_price),
                'stop_efficiency': self._calculate_stop_efficiency(position, current_price)
            }
            
        except Exception as e:
            return {'error': f'Error updating trailing stop: {e}'}
    
    def _fetch_market_data(self, symbol: str, periods: int = 100) -> Optional[pd.DataFrame]:
        """Obtiene datos de mercado"""
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="30d", interval="1h")
            
            if len(data) == 0:
                return None
                
            return data.tail(periods)
            
        except Exception as e:
            print(f"⚠️ Error obteniendo datos para {symbol}: {e}")
            return None
    
    def _add_trailing_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade indicadores para trailing stops"""
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(self.trailing_config['atr_based']['atr_period']).mean()
        
        # Momentum indicators
        df['Price_Momentum'] = df['Close'].pct_change(self.trailing_config['momentum_based']['momentum_period'])
        df['Momentum_MA'] = df['Price_Momentum'].rolling(5).mean()
        
        # Volatility regime
        df['Volatility_Regime'] = 'NORMAL'
        atr_ma = df['ATR'].rolling(20).mean()
        high_vol_threshold = atr_ma * 1.5
        low_vol_threshold = atr_ma * 0.7
        
        df.loc[df['ATR'] > high_vol_threshold, 'Volatility_Regime'] = 'HIGH'
        df.loc[df['ATR'] < low_vol_threshold, 'Volatility_Regime'] = 'LOW'
        
        # Support/Resistance levels
        df['Swing_High'] = df['High'].rolling(window=5, center=True).max() == df['High']
        df['Swing_Low'] = df['Low'].rolling(window=5, center=True).min() == df['Low']
        
        return df
    
    def _calculate_initial_stop_config(self, position_data: Dict, market_data: pd.DataFrame) -> Dict:
        """Calcula configuración inicial del trailing stop"""
        
        current_indicators = market_data.iloc[-1]
        position_type = position_data['type']
        entry_price = position_data['entry_price']
        signal_score = position_data.get('signal_score', 6.0)
        
        # Determinar tipo de stop basado en condiciones
        stop_type = self._determine_optimal_stop_type(market_data, position_data)
        
        # Calcular ATR multiplier basado en score y volatilidad
        base_atr_multiplier = self.trailing_config['atr_based']['atr_multiplier_min']
        
        # Ajustar por score de señal
        if signal_score >= self.trailing_config['score_based']['high_score_threshold']:
            # Señales de alta calidad = stops más amplios
            score_adjustment = 1 + self.trailing_config['score_based']['score_adjustment_factor']
        elif signal_score <= self.trailing_config['score_based']['low_score_threshold']:
            # Señales de baja calidad = stops más estrictos
            score_adjustment = 1 - self.trailing_config['score_based']['score_adjustment_factor']
        else:
            score_adjustment = 1.0
        
        # Ajustar por volatilidad
        volatility_regime = current_indicators['Volatility_Regime']
        if volatility_regime == 'HIGH':
            volatility_adjustment = 1.3
        elif volatility_regime == 'LOW':
            volatility_adjustment = 0.8
        else:
            volatility_adjustment = 1.0
        
        atr_multiplier = base_atr_multiplier * score_adjustment * volatility_adjustment
        atr_multiplier = np.clip(atr_multiplier, 
                               self.trailing_config['atr_based']['atr_multiplier_min'],
                               self.trailing_config['atr_based']['atr_multiplier_max'])
        
        # Calcular distancia del trailing stop
        atr_value = current_indicators['ATR']
        trail_distance = atr_value * atr_multiplier
        trail_distance_pct = (trail_distance / entry_price) * 100
        
        # Calcular stop inicial
        if position_type == 'LONG':
            initial_stop = entry_price - trail_distance
        else:  # SHORT
            initial_stop = entry_price + trail_distance
        
        return {
            'stop_type': stop_type,
            'initial_stop': initial_stop,
            'trail_distance': trail_distance,
            'trail_distance_pct': trail_distance_pct,
            'atr_multiplier': atr_multiplier,
            'volatility_regime': volatility_regime
        }
    
    def _determine_optimal_stop_type(self, market_data: pd.DataFrame, position_data: Dict) -> str:
        """Determina el tipo óptimo de trailing stop"""
        
        # Analizar condiciones de mercado
        recent_data = market_data.tail(20)
        volatility = recent_data['ATR'].iloc[-1] / recent_data['Close'].iloc[-1]
        momentum = abs(recent_data['Price_Momentum'].iloc[-1])
        
        # Lógica de selección
        if volatility > 0.05:  # Alta volatilidad
            if momentum > 0.03:  # Alto momentum
                return 'MOMENTUM_TRAILING'
            else:
                return 'ATR_TRAILING'
        elif volatility < 0.02:  # Baja volatilidad
            return 'STRUCTURE_TRAILING'
        else:
            # Condiciones normales - usar híbrido
            return 'HYBRID_TRAILING'
    
    def _calculate_dynamic_stop(self, position: Dict, current_price: float, indicators: pd.Series) -> Dict:
        """Calcula nuevo nivel de trailing stop dinámicamente"""
        
        position_type = position['position_type']
        stop_type = position['stop_type']
        
        if stop_type == 'ATR_TRAILING':
            return self._calculate_atr_stop(position, current_price, indicators)
        elif stop_type == 'MOMENTUM_TRAILING':
            return self._calculate_momentum_stop(position, current_price, indicators)
        elif stop_type == 'STRUCTURE_TRAILING':
            return self._calculate_structure_stop(position, current_price, indicators)
        elif stop_type == 'HYBRID_TRAILING':
            return self._calculate_hybrid_stop(position, current_price, indicators)
        else:
            return self._calculate_atr_stop(position, current_price, indicators)
    
    def _calculate_atr_stop(self, position: Dict, current_price: float, indicators: pd.Series) -> Dict:
        """Calcula stop basado en ATR"""
        
        # Ajustar ATR multiplier dinámicamente
        current_atr = indicators['ATR']
        volatility_regime = indicators['Volatility_Regime']
        
        # Ajuste por momentum
        momentum_adjustment = 1.0
        if abs(indicators['Price_Momentum']) > self.trailing_config['momentum_based']['acceleration_threshold']:
            # Alto momentum = stops más amplios
            momentum_adjustment = self.trailing_config['momentum_based']['extend_factor']
        
        # Ajuste por tiempo en posición
        time_adjustment = self._get_time_adjustment(position)
        
        # ATR multiplier dinámico
        dynamic_atr_multiplier = position['atr_multiplier'] * momentum_adjustment * time_adjustment
        trail_distance = current_atr * dynamic_atr_multiplier
        
        # Calcular nuevo stop
        if position['position_type'] == 'LONG':
            new_stop = position['best_price'] - trail_distance
        else:
            new_stop = position['best_price'] + trail_distance
        
        return {
            'stop_price': new_stop,
            'trail_distance': trail_distance,
            'trail_distance_pct': (trail_distance / current_price) * 100,
            'method': 'ATR_DYNAMIC',
            'reason': f'ATR-based (mult: {dynamic_atr_multiplier:.2f})',
            'confidence': 0.8
        }
    
    def _calculate_momentum_stop(self, position: Dict, current_price: float, indicators: pd.Series) -> Dict:
        """Calcula stop basado en momentum"""
        
        momentum = indicators['Price_Momentum']
        momentum_ma = indicators['Momentum_MA']
        
        # Distancia base
        base_distance = position['trail_distance']
        
        # Ajuste por momentum
        if momentum > momentum_ma:
            # Momentum acelerando = stops más amplios
            momentum_factor = self.trailing_config['momentum_based']['extend_factor']
        else:
            # Momentum desacelerando = stops más estrictos
            momentum_factor = self.trailing_config['momentum_based']['tighten_factor']
        
        dynamic_distance = base_distance * momentum_factor
        
        # Calcular nuevo stop
        if position['position_type'] == 'LONG':
            new_stop = position['best_price'] - dynamic_distance
        else:
            new_stop = position['best_price'] + dynamic_distance
        
        return {
            'stop_price': new_stop,
            'trail_distance': dynamic_distance,
            'trail_distance_pct': (dynamic_distance / current_price) * 100,
            'method': 'MOMENTUM_DYNAMIC',
            'reason': f'Momentum-based (factor: {momentum_factor:.2f})',
            'confidence': 0.7
        }
    
    def _calculate_structure_stop(self, position: Dict, current_price: float, indicators: pd.Series) -> Dict:
        """Calcula stop basado en estructura de mercado"""
        
        # Usar distancia ATR como fallback
        atr_distance = indicators['ATR'] * position['atr_multiplier']
        
        # TODO: Implementar lógica de soporte/resistencia real
        # Por ahora usar ATR con buffer de estructura
        structure_buffer = self.trailing_config['structure_based']['support_resistance_buffer']
        structure_distance = atr_distance * (1 + structure_buffer)
        
        if position['position_type'] == 'LONG':
            new_stop = position['best_price'] - structure_distance
        else:
            new_stop = position['best_price'] + structure_distance
        
        return {
            'stop_price': new_stop,
            'trail_distance': structure_distance,
            'trail_distance_pct': (structure_distance / current_price) * 100,
            'method': 'STRUCTURE_BASED',
            'reason': 'Structure-based with buffer',
            'confidence': 0.6
        }
    
    def _calculate_hybrid_stop(self, position: Dict, current_price: float, indicators: pd.Series) -> Dict:
        """Calcula stop híbrido combinando métodos"""
        
        # Obtener stops de diferentes métodos
        atr_stop = self._calculate_atr_stop(position, current_price, indicators)
        momentum_stop = self._calculate_momentum_stop(position, current_price, indicators)
        
        # Combinar usando pesos
        atr_weight = 0.6
        momentum_weight = 0.4
        
        combined_stop = (atr_stop['stop_price'] * atr_weight + 
                        momentum_stop['stop_price'] * momentum_weight)
        
        combined_distance = abs(combined_stop - position['best_price'])
        
        return {
            'stop_price': combined_stop,
            'trail_distance': combined_distance,
            'trail_distance_pct': (combined_distance / current_price) * 100,
            'method': 'HYBRID',
            'reason': f'Hybrid ATR({atr_weight:.0%}) + Momentum({momentum_weight:.0%})',
            'confidence': 0.9
        }
    
    def _get_time_adjustment(self, position: Dict) -> float:
        """Obtiene ajuste basado en tiempo en posición"""
        
        periods_held = position['periods_held']
        
        if periods_held <= self.trailing_config['time_based']['initial_tight_period']:
            # Primeros períodos = stops más estrictos
            return 0.9
        elif periods_held >= self.trailing_config['time_based']['mature_trade_period']:
            # Trades maduros = stops más amplios
            return 1.1
        else:
            return 1.0
    
    def _update_stop_level(self, position: Dict, new_stop_data: Dict) -> bool:
        """Actualiza nivel de stop si es favorable"""
        
        new_stop = new_stop_data['stop_price']
        current_stop = position['current_stop']
        position_type = position['position_type']
        
        # Solo actualizar si el nuevo stop es más favorable
        if position_type == 'LONG':
            # Para LONG, stop más alto es mejor
            if new_stop > current_stop:
                position['current_stop'] = new_stop
                position['trail_distance'] = new_stop_data['trail_distance']
                position['trail_distance_pct'] = new_stop_data['trail_distance_pct']
                position['stop_history'].append(new_stop)
                return True
        else:  # SHORT
            # Para SHORT, stop más bajo es mejor
            if new_stop < current_stop:
                position['current_stop'] = new_stop
                position['trail_distance'] = new_stop_data['trail_distance']
                position['trail_distance_pct'] = new_stop_data['trail_distance_pct']
                position['stop_history'].append(new_stop)
                return True
        
        return False
    
    def _check_stop_trigger(self, position: Dict, current_price: float) -> bool:
        """Verifica si el trailing stop fue activado"""
        
        current_stop = position['current_stop']
        position_type = position['position_type']
        
        if position_type == 'LONG':
            if current_price <= current_stop:
                position['triggered'] = True
                position['trigger_reason'] = f'Price {current_price:.2f} <= Stop {current_stop:.2f}'
                return True
        else:  # SHORT
            if current_price >= current_stop:
                position['triggered'] = True
                position['trigger_reason'] = f'Price {current_price:.2f} >= Stop {current_stop:.2f}'
                return True
        
        return False
    
    def _calculate_unrealized_pnl_pct(self, position: Dict, current_price: float) -> float:
        """Calcula P&L no realizado en porcentaje"""
        
        entry_price = position['entry_price']
        position_type = position['position_type']
        
        if position_type == 'LONG':
            return ((current_price / entry_price) - 1) * 100
        else:  # SHORT
            return ((entry_price / current_price) - 1) * 100
    
    def _calculate_stop_efficiency(self, position: Dict, current_price: float) -> float:
        """Calcula eficiencia del trailing stop (0-1)"""
        
        best_price = position['best_price']
        current_stop = position['current_stop']
        entry_price = position['entry_price']
        position_type = position['position_type']
        
        if position_type == 'LONG':
            max_gain = best_price - entry_price
            protected_gain = current_stop - entry_price
        else:  # SHORT
            max_gain = entry_price - best_price
            protected_gain = entry_price - current_stop
        
        if max_gain <= 0:
            return 0.0
        
        efficiency = protected_gain / max_gain
        return max(0.0, min(1.0, efficiency))
    
    def _get_fallback_stop(self, position_data: Dict) -> Dict:
        """Stop de fallback cuando hay errores"""
        
        entry_price = position_data['entry_price']
        position_type = position_data['type']
        
        # Stop loss fijo del 5%
        stop_distance_pct = 5.0
        
        if position_type == 'LONG':
            initial_stop = entry_price * (1 - stop_distance_pct / 100)
        else:
            initial_stop = entry_price * (1 + stop_distance_pct / 100)
        
        return {
            'symbol': position_data.get('symbol', 'UNKNOWN'),
            'position_id': position_data.get('id', 'unknown'),
            'position_type': position_type,
            'entry_price': entry_price,
            'stop_type': 'FALLBACK_FIXED',
            'initial_stop': initial_stop,
            'current_stop': initial_stop,
            'best_price': entry_price,
            'trail_distance_pct': stop_distance_pct,
            'source': 'fallback'
        }
    
    def remove_position(self, symbol: str) -> bool:
        """Remueve posición del tracking"""
        
        if symbol in self.active_positions:
            del self.active_positions[symbol]
            return True
        return False
    
    def get_position_status(self, symbol: str) -> Optional[Dict]:
        """Obtiene estado de trailing stop para símbolo"""
        
        return self.active_positions.get(symbol)
    
    def print_trailing_analysis(self, symbol: str, current_price: float):
        """Imprime análisis detallado del trailing stop"""
        
        if symbol not in self.active_positions:
            print(f"❌ No hay trailing stop activo para {symbol}")
            return
        
        position = self.active_positions[symbol]
        
        print(f"📊 TRAILING STOP ANALYSIS - {symbol}")
        print("="*60)
        print(f"💰 Precio actual: ${current_price:.2f}")
        print(f"🎯 Stop actual: ${position['current_stop']:.2f}")
        print(f"🏆 Mejor precio: ${position['best_price']:.2f}")
        print(f"📈 Entry: ${position['entry_price']:.2f}")
        
        # P&L
        unrealized_pnl_pct = self._calculate_unrealized_pnl_pct(position, current_price)
        pnl_color = "🟢" if unrealized_pnl_pct > 0 else "🔴"
        print(f"{pnl_color} P&L no realizado: {unrealized_pnl_pct:+.2f}%")
        
        # Eficiencia del stop
        efficiency = self._calculate_stop_efficiency(position, current_price)
        print(f"⚡ Eficiencia del stop: {efficiency:.1%}")
        
        # Configuración
        print(f"\n🔧 CONFIGURACIÓN:")
        print(f"• Tipo: {position['stop_type']}")
        print(f"• Distancia actual: {position['trail_distance_pct']:.2f}%")
        print(f"• Períodos sostenido: {position['periods_held']}")
        print(f"• ATR Multiplier: {position['atr_multiplier']:.2f}")
        
        # Estado
        print(f"\n📊 ESTADO:")
        print(f"• Activado: {'✅' if position['triggered'] else '❌'}")
        if position['triggered']:
            print(f"• Razón: {position['trigger_reason']}")
        
        # Últimos ajustes
        if position['adjustment_log']:
            last_adjustment = position['adjustment_log'][-1]
            print(f"\n🔄 ÚLTIMO AJUSTE:")
            print(f"• Timestamp: {last_adjustment['timestamp'].strftime('%H:%M:%S')}")
            print(f"• Razón: {last_adjustment['reason']}")
            print(f"• Stop anterior: ${last_adjustment['old_stop']:.2f}")
            print(f"• Stop nuevo: ${last_adjustment['new_stop']:.2f}")

def demo_trailing_stops():
    """Demo del sistema de trailing stops"""
    
    trailing_system = DynamicTrailingStops()
    
    print("🎯 DYNAMIC TRAILING STOPS DEMO")
    print("="*70)
    
    # Simular posición
    position_data = {
        'id': 'demo_001',
        'symbol': 'BTC-USD',
        'type': 'LONG',
        'entry_price': 45000.0,
        'entry_time': datetime.now(),
        'signal_score': 7.5
    }
    
    print(f"📊 Simulando posición LONG BTC a ${position_data['entry_price']:,}")
    
    # Inicializar trailing stop
    trailing_stop = trailing_system.initialize_trailing_stop('BTC-USD', position_data)
    
    # Simular actualizaciones de precio
    price_scenarios = [
        45500,  # +1.1%
        46000,  # +2.2%
        47000,  # +4.4%
        46500,  # -1.1% from peak
        46800,  # +0.6% recovery
        45800,  # -2.1% pullback
    ]
    
    print(f"\n🔄 SIMULANDO ACTUALIZACIONES DE PRECIO:")
    for i, price in enumerate(price_scenarios):
        print(f"\n--- Actualización {i+1}: ${price:,} ---")
        
        update_result = trailing_system.update_trailing_stop('BTC-USD', price)
        
        if 'error' not in update_result:
            print(f"Stop: ${update_result['current_stop']:.2f} | "
                  f"P&L: {update_result['unrealized_pnl_pct']:+.1f}% | "
                  f"Eficiencia: {update_result['stop_efficiency']:.1%}")
            
            if update_result['stop_updated']:
                print("✅ Stop actualizado")
            
            if update_result['triggered']:
                print(f"🚨 STOP ACTIVADO: {update_result['trigger_reason']}")
                break
        else:
            print(f"❌ Error: {update_result['error']}")
    
    # Análisis final
    print(f"\n📊 ANÁLISIS FINAL:")
    trailing_system.print_trailing_analysis('BTC-USD', price_scenarios[-1])
    
    return trailing_system

if __name__ == "__main__":
    demo_trailing_stops()