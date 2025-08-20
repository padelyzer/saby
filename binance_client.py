#!/usr/bin/env python3
"""
Cliente de Binance para obtener datos de mercado
No requiere API keys para datos públicos
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

class BinanceClient:
    """Cliente para obtener datos de Binance sin API keys"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        
    def get_ticker_price(self, symbol: str) -> Dict:
        """Obtiene precio actual y estadísticas 24h"""
        try:
            endpoint = f"{self.base_url}/api/v3/ticker/24hr"
            response = self.session.get(endpoint, params={"symbol": symbol})
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': data['symbol'],
                    'current_price': float(data['lastPrice']),
                    'price_change_24h': float(data['priceChange']),
                    'price_change_percent_24h': float(data['priceChangePercent']),
                    'volume_24h': float(data['volume']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice']),
                    'bid': float(data['bidPrice']),
                    'ask': float(data['askPrice'])
                }
            return None
        except Exception as e:
            print(f"Error obteniendo ticker {symbol}: {e}")
            return None
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        Obtiene datos históricos OHLCV
        interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.
        """
        try:
            endpoint = f"{self.base_url}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = self.session.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'Open', 'High', 'Low', 'Close', 
                    'Volume', 'close_time', 'quote_volume', 
                    'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
                
                # Convertir a tipos correctos
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['Open'] = df['Open'].astype(float)
                df['High'] = df['High'].astype(float)
                df['Low'] = df['Low'].astype(float)
                df['Close'] = df['Close'].astype(float)
                df['Volume'] = df['Volume'].astype(float)
                
                df.set_index('timestamp', inplace=True)
                
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error obteniendo klines {symbol}: {e}")
            return pd.DataFrame()
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Obtiene el libro de órdenes"""
        try:
            endpoint = f"{self.base_url}/api/v3/depth"
            params = {
                'symbol': symbol,
                'limit': limit
            }
            
            response = self.session.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'bids': [[float(p), float(q)] for p, q in data['bids']],
                    'asks': [[float(p), float(q)] for p, q in data['asks']],
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            print(f"Error obteniendo orderbook {symbol}: {e}")
            return None
    
    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Obtiene trades recientes"""
        try:
            endpoint = f"{self.base_url}/api/v3/trades"
            params = {
                'symbol': symbol,
                'limit': limit
            }
            
            response = self.session.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return [{
                    'price': float(t['price']),
                    'quantity': float(t['qty']),
                    'time': pd.to_datetime(t['time'], unit='ms'),
                    'is_buyer': t['isBuyerMaker']
                } for t in data]
            
            return []
            
        except Exception as e:
            print(f"Error obteniendo trades {symbol}: {e}")
            return []
    
    def get_exchange_info(self, symbol: str = None) -> Dict:
        """Obtiene información del exchange"""
        try:
            endpoint = f"{self.base_url}/api/v3/exchangeInfo"
            params = {'symbol': symbol} if symbol else {}
            
            response = self.session.get(endpoint, params=params)
            
            if response.status_code == 200:
                return response.json()
            
            return {}
            
        except Exception as e:
            print(f"Error obteniendo exchange info: {e}")
            return {}
    
    def get_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Obtiene datos en múltiples timeframes para análisis"""
        timeframes = {
            '15m': 100,  # 15 minutos x 100 = 25 horas
            '1h': 100,   # 1 hora x 100 = 4 días
            '4h': 100,   # 4 horas x 100 = 16 días
            '1d': 100    # 1 día x 100 = 100 días
        }
        
        data = {}
        for tf, limit in timeframes.items():
            df = self.get_klines(symbol, tf, limit)
            if not df.empty:
                data[tf] = df
            time.sleep(0.1)  # Evitar rate limits
        
        return data
    
    def test_connection(self) -> bool:
        """Prueba la conexión con Binance"""
        try:
            endpoint = f"{self.base_url}/api/v3/ping"
            response = self.session.get(endpoint)
            return response.status_code == 200
        except:
            return False

# Singleton para reutilizar la conexión
binance_client = BinanceClient()

if __name__ == "__main__":
    # Test del cliente
    client = BinanceClient()
    
    print("Probando conexión con Binance...")
    if client.test_connection():
        print("✅ Conexión exitosa")
        
        # Probar con un símbolo
        symbol = "SOLUSDT"
        print(f"\nObteniendo datos de {symbol}...")
        
        # Precio actual
        ticker = client.get_ticker_price(symbol)
        if ticker:
            print(f"Precio actual: ${ticker['current_price']:.2f}")
            print(f"Cambio 24h: {ticker['price_change_percent_24h']:.2f}%")
        
        # Datos históricos
        df = client.get_klines(symbol, '1h', 10)
        if not df.empty:
            print(f"\nÚltimas 10 velas horarias:")
            print(df.tail())
    else:
        print("❌ No se pudo conectar con Binance")