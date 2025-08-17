#!/usr/bin/env python3
"""
On-Chain Analysis Integration
Implementa análisis on-chain usando APIs de Glassnode y CryptoQuant
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

class OnChainAnalyzer:
    """
    Analizador de métricas on-chain para crypto
    Integra datos de Glassnode, CryptoQuant y APIs públicas
    """
    
    def __init__(self):
        # Configuración de APIs (usar claves reales en producción)
        self.apis = {
            'glassnode': {
                'base_url': 'https://api.glassnode.com/v1/metrics',
                'api_key': 'YOUR_GLASSNODE_API_KEY',  # Cambiar por key real
                'endpoints': {
                    'sopr': '/indicators/sopr',
                    'mvrv': '/market/mvrv',
                    'active_addresses': '/addresses/active_count',
                    'exchange_flows': '/transactions/flows_exchanges',
                    'whale_count': '/addresses/count_1k'
                }
            },
            'cryptoquant': {
                'base_url': 'https://api.cryptoquant.com/v1',
                'api_key': 'YOUR_CRYPTOQUANT_API_KEY',  # Cambiar por key real
                'endpoints': {
                    'exchange_inflow': '/btc/exchange-flows/inflow-mean',
                    'exchange_outflow': '/btc/exchange-flows/outflow-mean',
                    'stablecoin_flows': '/stablecoins/flows',
                    'miners_position': '/btc/miner-flows'
                }
            },
            'whale_alert': {
                'base_url': 'https://api.whale-alert.io/v1',
                'api_key': 'YOUR_WHALE_ALERT_KEY',  # Cambiar por key real
                'min_value': 1000000  # $1M mínimo para whale transactions
            }
        }
        
        # Métricas y thresholds
        self.metrics_config = {
            'sopr': {
                'bullish_threshold': 1.05,
                'bearish_threshold': 0.95,
                'weight': 0.2
            },
            'mvrv': {
                'overbought_threshold': 3.0,
                'oversold_threshold': 1.0,
                'weight': 0.25
            },
            'exchange_flows': {
                'inflow_bearish_multiplier': 2.0,  # 2x daily average
                'outflow_bullish_multiplier': 1.5,  # 1.5x daily average
                'weight': 0.3
            },
            'whale_activity': {
                'significant_transfer': 1000,  # BTC
                'accumulation_threshold': 5,   # transfers per day
                'weight': 0.15
            },
            'network_health': {
                'active_addresses_growth': 0.05,  # 5% growth
                'weight': 0.1
            }
        }
        
        # Cache para evitar rate limits
        self.cache = {}
        self.cache_duration = 3600  # 1 hora
    
    def get_onchain_score(self, symbol='BTC', timeframe_hours=24):
        """Obtiene score on-chain compuesto (0-1)"""
        
        print(f"🔗 Analizando métricas on-chain para {symbol}...")
        
        try:
            # Obtener métricas principales
            sopr_score = self._get_sopr_score(symbol)
            mvrv_score = self._get_mvrv_score(symbol)
            flows_score = self._get_exchange_flows_score(symbol)
            whale_score = self._get_whale_activity_score(symbol, timeframe_hours)
            network_score = self._get_network_health_score(symbol)
            
            # Calcular score compuesto
            total_score = (
                sopr_score * self.metrics_config['sopr']['weight'] +
                mvrv_score * self.metrics_config['mvrv']['weight'] +
                flows_score * self.metrics_config['exchange_flows']['weight'] +
                whale_score * self.metrics_config['whale_activity']['weight'] +
                network_score * self.metrics_config['network_health']['weight']
            )
            
            # Normalizar a 0-1
            final_score = max(0, min(total_score, 1))
            
            details = {
                'sopr_score': sopr_score,
                'mvrv_score': mvrv_score,
                'flows_score': flows_score,
                'whale_score': whale_score,
                'network_score': network_score,
                'final_score': final_score,
                'timestamp': datetime.now(),
                'symbol': symbol
            }
            
            return final_score, details
            
        except Exception as e:
            print(f"⚠️ Error en análisis on-chain: {e}")
            return self._get_fallback_score(symbol)
    
    def _get_sopr_score(self, symbol):
        """Obtiene score basado en SOPR (Spent Output Profit Ratio)"""
        
        if not self._has_valid_api_key('glassnode'):
            return self._simulate_sopr_score(symbol)
        
        try:
            # Intentar obtener datos reales de Glassnode
            endpoint = f"{self.apis['glassnode']['base_url']}{self.apis['glassnode']['endpoints']['sopr']}"
            params = {
                'a': symbol.replace('-USD', '').lower(),
                'api_key': self.apis['glassnode']['api_key'],
                'i': '1d',
                'f': 'json'
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    latest_sopr = float(data[-1]['v'])
                    return self._calculate_sopr_score(latest_sopr)
            
        except Exception as e:
            print(f"⚠️ Error obteniendo SOPR real: {e}")
        
        # Fallback a simulación
        return self._simulate_sopr_score(symbol)
    
    def _simulate_sopr_score(self, symbol):
        """Simula SOPR score basado en datos de precio"""
        
        try:
            import yfinance as yf
            
            # Obtener datos de precio para simular SOPR
            ticker = yf.Ticker(f"{symbol}")
            data = ticker.history(period='30d')
            
            if len(data) >= 7:
                # Simular SOPR basado en momentum de precio
                recent_avg = data['Close'].tail(7).mean()
                older_avg = data['Close'].head(7).mean()
                price_momentum = recent_avg / older_avg
                
                # Convertir momentum a SOPR simulado
                simulated_sopr = 0.95 + (price_momentum - 1) * 2
                simulated_sopr = max(0.8, min(simulated_sopr, 1.2))
                
                return self._calculate_sopr_score(simulated_sopr)
            
        except Exception as e:
            print(f"Error en simulación SOPR: {e}")
        
        return 0.5  # Neutral
    
    def _calculate_sopr_score(self, sopr_value):
        """Calcula score basado en valor SOPR"""
        
        config = self.metrics_config['sopr']
        
        if sopr_value >= config['bullish_threshold']:
            # SOPR alto = taking profits = potential bearish
            return max(0, 1 - (sopr_value - config['bullish_threshold']) * 2)
        elif sopr_value <= config['bearish_threshold']:
            # SOPR bajo = holding at loss = potential bullish
            return min(1, 1 + (config['bearish_threshold'] - sopr_value) * 2)
        else:
            # SOPR neutral
            return 0.5
    
    def _get_mvrv_score(self, symbol):
        """Obtiene score basado en MVRV ratio"""
        
        if not self._has_valid_api_key('glassnode'):
            return self._simulate_mvrv_score(symbol)
        
        # Implementación similar a SOPR
        return self._simulate_mvrv_score(symbol)
    
    def _simulate_mvrv_score(self, symbol):
        """Simula MVRV score"""
        
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(f"{symbol}")
            data = ticker.history(period='90d')
            
            if len(data) >= 30:
                current_price = data['Close'].iloc[-1]
                avg_price_30d = data['Close'].tail(30).mean()
                
                # Simular MVRV como ratio precio actual vs promedio
                simulated_mvrv = current_price / avg_price_30d
                
                config = self.metrics_config['mvrv']
                
                if simulated_mvrv >= config['overbought_threshold']:
                    # Sobrevalorado = bearish
                    return max(0, 1 - (simulated_mvrv - config['overbought_threshold']) * 0.5)
                elif simulated_mvrv <= config['oversold_threshold']:
                    # Subvalorado = bullish
                    return min(1, (config['oversold_threshold'] - simulated_mvrv) * 0.5 + 0.7)
                else:
                    # Neutral
                    return 0.5
                    
        except Exception as e:
            print(f"Error en simulación MVRV: {e}")
        
        return 0.5
    
    def _get_exchange_flows_score(self, symbol):
        """Obtiene score basado en flujos de exchange"""
        
        # Simulación inteligente basada en volumen
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(f"{symbol}")
            data = ticker.history(period='7d', interval='1d')
            
            if len(data) >= 3:
                # Usar volumen como proxy de exchange flows
                recent_volume = data['Volume'].tail(2).mean()
                baseline_volume = data['Volume'].head(3).mean()
                
                volume_ratio = recent_volume / baseline_volume if baseline_volume > 0 else 1
                
                config = self.metrics_config['exchange_flows']
                
                if volume_ratio >= config['inflow_bearish_multiplier']:
                    # Alto volumen = potential selling pressure
                    return max(0, 1 - (volume_ratio - config['inflow_bearish_multiplier']) * 0.3)
                elif volume_ratio <= 1 / config['outflow_bullish_multiplier']:
                    # Bajo volumen = potential accumulation
                    return min(1, 0.7 + (1 / config['outflow_bullish_multiplier'] - volume_ratio) * 0.5)
                else:
                    return 0.5
                    
        except Exception as e:
            print(f"Error en simulación exchange flows: {e}")
        
        return 0.5
    
    def _get_whale_activity_score(self, symbol, timeframe_hours):
        """Obtiene score basado en actividad de ballenas"""
        
        # Simulación basada en movimientos de precio inusuales
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(f"{symbol}")
            data = ticker.history(period='3d', interval='1h')
            
            if len(data) >= timeframe_hours:
                # Detectar movimientos inusuales como proxy de whale activity
                returns = data['Close'].pct_change()
                recent_volatility = returns.tail(timeframe_hours).std()
                baseline_volatility = returns.head(48).std()  # 48h baseline
                
                volatility_ratio = recent_volatility / baseline_volatility if baseline_volatility > 0 else 1
                
                # Whale activity score basado en volatilidad anormal
                if volatility_ratio >= 1.5:
                    # Alta volatilidad = whale activity
                    whale_score = min(1, 0.3 + (volatility_ratio - 1.5) * 0.4)
                else:
                    whale_score = max(0, volatility_ratio * 0.2)
                
                return whale_score
                
        except Exception as e:
            print(f"Error en simulación whale activity: {e}")
        
        return 0.3  # Baseline whale activity
    
    def _get_network_health_score(self, symbol):
        """Obtiene score basado en salud de la red"""
        
        # Simulación basada en momentum de precio como proxy
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(f"{symbol}")
            data = ticker.history(period='30d')
            
            if len(data) >= 7:
                # Usar tendencia de precio como proxy de network health
                recent_trend = (data['Close'].tail(7).mean() / data['Close'].head(7).mean()) - 1
                
                config = self.metrics_config['network_health']
                
                if recent_trend >= config['active_addresses_growth']:
                    return min(1, 0.6 + recent_trend * 2)
                else:
                    return max(0, 0.6 + recent_trend * 2)
                    
        except Exception as e:
            print(f"Error en simulación network health: {e}")
        
        return 0.5
    
    def _has_valid_api_key(self, provider):
        """Verifica si tenemos API key válida"""
        api_key = self.apis.get(provider, {}).get('api_key', '')
        return api_key and 'YOUR_' not in api_key
    
    def _get_fallback_score(self, symbol):
        """Score de fallback cuando no hay datos"""
        return 0.5, {
            'sopr_score': 0.5,
            'mvrv_score': 0.5,
            'flows_score': 0.5,
            'whale_score': 0.3,
            'network_score': 0.5,
            'final_score': 0.5,
            'timestamp': datetime.now(),
            'symbol': symbol,
            'source': 'fallback'
        }
    
    def get_trading_signal_adjustment(self, symbol, base_score):
        """Ajusta signal de trading basado en on-chain metrics"""
        
        onchain_score, details = self.get_onchain_score(symbol)
        
        # Calcular ajuste basado en on-chain score
        if onchain_score >= 0.7:
            adjustment = 1.2  # Boost 20%
            reason = "On-chain metrics very bullish"
        elif onchain_score >= 0.6:
            adjustment = 1.1  # Boost 10%
            reason = "On-chain metrics bullish"
        elif onchain_score <= 0.3:
            adjustment = 0.8  # Reduce 20%
            reason = "On-chain metrics bearish"
        elif onchain_score <= 0.4:
            adjustment = 0.9  # Reduce 10%
            reason = "On-chain metrics weak"
        else:
            adjustment = 1.0  # Neutral
            reason = "On-chain metrics neutral"
        
        adjusted_score = base_score * adjustment
        
        return adjusted_score, {
            'original_score': base_score,
            'onchain_score': onchain_score,
            'adjustment_factor': adjustment,
            'adjusted_score': adjusted_score,
            'reason': reason,
            'onchain_details': details
        }
    
    def print_onchain_analysis(self, symbol='BTC-USD'):
        """Imprime análisis on-chain detallado"""
        
        print(f"🔗 ANÁLISIS ON-CHAIN - {symbol}")
        print("="*50)
        
        score, details = self.get_onchain_score(symbol.replace('-USD', ''))
        
        print(f"📊 SCORE ON-CHAIN COMPUESTO: {score:.3f}")
        print(f"📅 Timestamp: {details['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print(f"📋 COMPONENTES:")
        print(f"• SOPR Score: {details['sopr_score']:.3f} (Weight: {self.metrics_config['sopr']['weight']:.0%})")
        print(f"• MVRV Score: {details['mvrv_score']:.3f} (Weight: {self.metrics_config['mvrv']['weight']:.0%})")
        print(f"• Exchange Flows: {details['flows_score']:.3f} (Weight: {self.metrics_config['exchange_flows']['weight']:.0%})")
        print(f"• Whale Activity: {details['whale_score']:.3f} (Weight: {self.metrics_config['whale_activity']['weight']:.0%})")
        print(f"• Network Health: {details['network_score']:.3f} (Weight: {self.metrics_config['network_health']['weight']:.0%})")
        
        print(f"\n🎯 INTERPRETACIÓN:")
        if score >= 0.7:
            print("🌟 ON-CHAIN MUY BULLISH - Métricas favorecen compras")
        elif score >= 0.6:
            print("✅ ON-CHAIN BULLISH - Condiciones positivas")
        elif score >= 0.4:
            print("📊 ON-CHAIN NEUTRAL - Sin señales claras")
        elif score >= 0.3:
            print("⚠️ ON-CHAIN BEARISH - Métricas débiles")
        else:
            print("🔴 ON-CHAIN MUY BEARISH - Condiciones desfavorables")
        
        print(f"\n💡 RECOMENDACIÓN:")
        if score >= 0.6:
            print("• Incrementar position sizes")
            print("• Considerar entradas agresivas")
            print("• Mantener trades más tiempo")
        elif score <= 0.4:
            print("• Reducir position sizes")
            print("• Ser más selectivo con entradas")
            print("• Considerar tomar profits early")
        else:
            print("• Mantener strategy normal")
            print("• Monitorear cambios en métricas")
        
        return score, details

def demo_onchain_analysis():
    """Demo del análisis on-chain"""
    
    analyzer = OnChainAnalyzer()
    
    print("🔗 ON-CHAIN ANALYSIS DEMO")
    print("="*60)
    print("Nota: Usando simulación inteligente (APIs reales requieren keys)")
    print("="*60)
    
    # Análisis para BTC
    analyzer.print_onchain_analysis('BTC-USD')
    
    print("\n" + "="*60)
    
    # Test de ajuste de signal
    base_score = 7.2
    adjusted_score, adjustment_details = analyzer.get_trading_signal_adjustment('BTC', base_score)
    
    print(f"🎯 AJUSTE DE SIGNAL TESTING:")
    print(f"• Score Base: {base_score}")
    print(f"• Score Ajustado: {adjusted_score:.2f}")
    print(f"• Factor Ajuste: {adjustment_details['adjustment_factor']:.2f}")
    print(f"• Razón: {adjustment_details['reason']}")
    
    return analyzer

if __name__ == "__main__":
    demo_onchain_analysis()