#!/usr/bin/env python3
"""
Cache Manager - Sistema de caché para optimizar rendimiento
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import pickle
import os
from functools import wraps
import threading

class CacheManager:
    """
    Gestor de caché en memoria y disco para optimizar llamadas a APIs
    """
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 300):
        """
        Args:
            cache_dir: Directorio para caché en disco
            default_ttl: Time to live por defecto en segundos
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'expired': 0,
            'errors': 0
        }
        self.lock = threading.Lock()
        
        # Crear directorio de caché si no existe
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Genera una clave única para los argumentos"""
        key_data = f"{args}{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché"""
        with self.lock:
            # Primero buscar en memoria
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if time.time() < entry['expires']:
                    self.cache_stats['hits'] += 1
                    return entry['value']
                else:
                    # Expirado
                    del self.memory_cache[key]
                    self.cache_stats['expired'] += 1
            
            # Buscar en disco
            disk_path = os.path.join(self.cache_dir, f"{key}.cache")
            if os.path.exists(disk_path):
                try:
                    with open(disk_path, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if time.time() < entry['expires']:
                        # Cargar a memoria
                        self.memory_cache[key] = entry
                        self.cache_stats['hits'] += 1
                        return entry['value']
                    else:
                        # Expirado
                        os.remove(disk_path)
                        self.cache_stats['expired'] += 1
                except Exception:
                    self.cache_stats['errors'] += 1
            
            self.cache_stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Guarda un valor en el caché"""
        with self.lock:
            ttl = ttl or self.default_ttl
            entry = {
                'value': value,
                'expires': time.time() + ttl,
                'created': time.time()
            }
            
            # Guardar en memoria
            self.memory_cache[key] = entry
            
            # Guardar en disco si es importante
            if ttl > 60:  # Solo cachear en disco si TTL > 1 minuto
                try:
                    disk_path = os.path.join(self.cache_dir, f"{key}.cache")
                    with open(disk_path, 'wb') as f:
                        pickle.dump(entry, f)
                except Exception:
                    self.cache_stats['errors'] += 1
    
    def delete(self, key: str):
        """Elimina una entrada del caché"""
        with self.lock:
            # Eliminar de memoria
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Eliminar de disco
            disk_path = os.path.join(self.cache_dir, f"{key}.cache")
            if os.path.exists(disk_path):
                try:
                    os.remove(disk_path)
                except Exception:
                    pass
    
    def clear(self):
        """Limpia todo el caché"""
        with self.lock:
            self.memory_cache.clear()
            
            # Limpiar disco
            for file in os.listdir(self.cache_dir):
                if file.endswith('.cache'):
                    try:
                        os.remove(os.path.join(self.cache_dir, file))
                    except Exception:
                        pass
    
    def cleanup_expired(self):
        """Limpia entradas expiradas"""
        with self.lock:
            current_time = time.time()
            
            # Limpiar memoria
            expired_keys = [
                k for k, v in self.memory_cache.items()
                if current_time >= v['expires']
            ]
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Limpiar disco
            for file in os.listdir(self.cache_dir):
                if file.endswith('.cache'):
                    file_path = os.path.join(self.cache_dir, file)
                    try:
                        with open(file_path, 'rb') as f:
                            entry = pickle.load(f)
                        if current_time >= entry['expires']:
                            os.remove(file_path)
                    except Exception:
                        pass
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del caché"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'memory_entries': len(self.memory_cache),
            'disk_entries': len([f for f in os.listdir(self.cache_dir) if f.endswith('.cache')])
        }


# Singleton global
cache_manager = CacheManager()


def cached(ttl: int = 300):
    """
    Decorador para cachear resultados de funciones
    
    Usage:
        @cached(ttl=600)  # Cache por 10 minutos
        def expensive_function(param1, param2):
            return do_expensive_calculation()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de caché
            cache_key = f"{func.__name__}_{cache_manager._generate_key(*args, **kwargs)}"
            
            # Buscar en caché
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Ejecutar función
            result = func(*args, **kwargs)
            
            # Guardar en caché
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class BinanceCache:
    """Caché específico para datos de Binance"""
    
    # TTLs específicos por tipo de dato
    TTL_CONFIG = {
        'ticker': 10,        # 10 segundos para tickers
        'klines_1m': 30,     # 30 segundos para velas de 1m
        'klines_5m': 60,     # 1 minuto para velas de 5m
        'klines_15m': 180,   # 3 minutos para velas de 15m
        'klines_1h': 300,    # 5 minutos para velas de 1h
        'klines_4h': 600,    # 10 minutos para velas de 4h
        'klines_1d': 1800,   # 30 minutos para velas diarias
        'orderbook': 5,      # 5 segundos para order book
        'symbol_info': 3600  # 1 hora para info de símbolo
    }
    
    @staticmethod
    def cache_key(data_type: str, symbol: str, **params) -> str:
        """Genera clave de caché para datos de Binance"""
        params_str = '_'.join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"binance_{data_type}_{symbol}_{params_str}"
    
    @staticmethod
    def get_ttl(data_type: str, interval: str = None) -> int:
        """Obtiene TTL apropiado para el tipo de dato"""
        if data_type == 'klines' and interval:
            key = f"klines_{interval}"
            return BinanceCache.TTL_CONFIG.get(key, 300)
        return BinanceCache.TTL_CONFIG.get(data_type, 300)


class PerformanceMonitor:
    """Monitor de rendimiento para tracking de latencias"""
    
    def __init__(self):
        self.timings = {}
        self.lock = threading.Lock()
    
    def start_timer(self, operation: str) -> float:
        """Inicia un timer para una operación"""
        start_time = time.time()
        with self.lock:
            if operation not in self.timings:
                self.timings[operation] = []
        return start_time
    
    def end_timer(self, operation: str, start_time: float):
        """Finaliza un timer y registra el tiempo"""
        elapsed = time.time() - start_time
        with self.lock:
            if operation in self.timings:
                self.timings[operation].append(elapsed)
                # Mantener solo los últimos 100 timings
                if len(self.timings[operation]) > 100:
                    self.timings[operation].pop(0)
    
    def get_stats(self, operation: str = None) -> Dict:
        """Obtiene estadísticas de rendimiento"""
        with self.lock:
            if operation:
                if operation not in self.timings or not self.timings[operation]:
                    return {}
                
                times = self.timings[operation]
                return {
                    'operation': operation,
                    'count': len(times),
                    'avg_ms': sum(times) / len(times) * 1000,
                    'min_ms': min(times) * 1000,
                    'max_ms': max(times) * 1000,
                    'last_ms': times[-1] * 1000
                }
            else:
                # Todas las operaciones
                stats = {}
                for op, times in self.timings.items():
                    if times:
                        stats[op] = {
                            'count': len(times),
                            'avg_ms': sum(times) / len(times) * 1000,
                            'last_ms': times[-1] * 1000
                        }
                return stats


# Singleton global
performance_monitor = PerformanceMonitor()


if __name__ == "__main__":
    # Test del cache manager
    print("🧪 Testing Cache Manager...")
    
    # Test básico
    cache_manager.set("test_key", {"data": "test_value"}, ttl=5)
    result = cache_manager.get("test_key")
    print(f"Cache get: {result}")
    
    # Test con decorador
    @cached(ttl=10)
    def expensive_calculation(x, y):
        print(f"Calculando {x} + {y}...")
        time.sleep(1)  # Simular operación costosa
        return x + y
    
    # Primera llamada (miss)
    start = time.time()
    result1 = expensive_calculation(5, 3)
    print(f"Resultado 1: {result1} (tiempo: {time.time() - start:.3f}s)")
    
    # Segunda llamada (hit)
    start = time.time()
    result2 = expensive_calculation(5, 3)
    print(f"Resultado 2: {result2} (tiempo: {time.time() - start:.3f}s)")
    
    # Estadísticas
    print(f"\n📊 Estadísticas de caché:")
    print(json.dumps(cache_manager.get_stats(), indent=2))
    
    # Test Binance cache
    print(f"\n🔑 Binance cache key: {BinanceCache.cache_key('ticker', 'BTCUSDT')}")
    print(f"TTL para klines 1h: {BinanceCache.get_ttl('klines', '1h')}s")
    
    # Test performance monitor
    print("\n⚡ Testing Performance Monitor...")
    
    for i in range(3):
        start_time = performance_monitor.start_timer("test_operation")
        time.sleep(0.1 * (i + 1))  # Simular diferentes latencias
        performance_monitor.end_timer("test_operation", start_time)
    
    print(json.dumps(performance_monitor.get_stats(), indent=2))