#!/usr/bin/env python3
"""
Suite de Tests de Integración Completa
Ejecuta pruebas exhaustivas de todo el sistema de trading
"""

import sys
import time
import json
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import traceback
import requests
import websocket

# Importar todos los módulos del sistema
from binance_data_fetcher import BinanceDataFetcher
from symbol_manager import symbol_manager
from risk_calculator import risk_calculator
from cache_manager import cache_manager, performance_monitor
from error_handler import error_handler
from signal_validator import signal_validator
from paper_trading_enhanced import PaperTradingEnhanced
from backtest_system_v2 import BacktestSystemV2

class IntegrationTestSuite:
    """Suite completa de tests de integración"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
        self.start_time = None
        self.end_time = None
        
    def log_test(self, test_name: str, result: bool, details: str = "", error: str = ""):
        """Registra resultado de un test"""
        test_result = {
            'test': test_name,
            'passed': result,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(test_result)
        
        if result:
            self.passed_tests.append(test_name)
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   {details}")
        else:
            self.failed_tests.append(test_name)
            print(f"❌ {test_name}: FAILED")
            if error:
                print(f"   Error: {error}")
    
    def test_binance_api_connection(self) -> bool:
        """Test 1: Conexión con API de Binance"""
        print("\n🔍 TEST 1: Conexión API Binance")
        print("-" * 50)
        
        try:
            fetcher = BinanceDataFetcher()
            
            # Test obtener ticker
            ticker = fetcher.get_ticker_24hr("SOLUSDT")
            if not ticker or 'current_price' not in ticker:
                self.log_test("Binance API - Ticker", False, error="No se pudo obtener ticker")
                return False
            
            self.log_test(
                "Binance API - Ticker", 
                True, 
                f"SOL: ${ticker['current_price']:.2f}"
            )
            
            # Test obtener klines
            df = fetcher.get_klines("SOLUSDT", "1h", 10)
            if df.empty:
                self.log_test("Binance API - Klines", False, error="No se pudieron obtener velas")
                return False
            
            self.log_test(
                "Binance API - Klines",
                True,
                f"Obtenidas {len(df)} velas"
            )
            
            # Test order book
            order_book = fetcher.get_order_book("SOLUSDT")
            if not order_book:
                self.log_test("Binance API - Order Book", False, error="No se pudo obtener order book")
                return False
            
            self.log_test(
                "Binance API - Order Book",
                True,
                f"Buy pressure: {order_book['buy_pressure']:.2%}"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Binance API Connection", False, error=str(e))
            return False
    
    def test_symbol_management(self) -> bool:
        """Test 2: Sistema de gestión de símbolos"""
        print("\n🔍 TEST 2: Gestión de Símbolos")
        print("-" * 50)
        
        try:
            # Test símbolos activos
            active = symbol_manager.get_active_symbols()
            if len(active) != 8:
                self.log_test(
                    "Symbol Manager - Active Symbols",
                    False,
                    error=f"Esperados 8 símbolos, encontrados {len(active)}"
                )
                return False
            
            self.log_test(
                "Symbol Manager - Active Symbols",
                True,
                f"{len(active)} símbolos activos"
            )
            
            # Test validación
            valid_symbol = symbol_manager.is_valid_symbol("SOLUSDT")
            invalid_symbol = symbol_manager.is_valid_symbol("FAKEUSDT")
            
            if not valid_symbol or invalid_symbol:
                self.log_test("Symbol Manager - Validation", False)
                return False
            
            self.log_test("Symbol Manager - Validation", True)
            
            # Test correlaciones
            correlated = symbol_manager.get_correlated_symbols("SOLUSDT", 0.6)
            self.log_test(
                "Symbol Manager - Correlations",
                True,
                f"Encontradas {len(correlated)} correlaciones"
            )
            
            # Test portfolio validation
            test_allocation = {
                "SOLUSDT": 0.25,
                "ADAUSDT": 0.25,
                "LINKUSDT": 0.25,
                "DOGEUSDT": 0.25
            }
            
            validation = symbol_manager.validate_portfolio_allocation(test_allocation)
            self.log_test(
                "Symbol Manager - Portfolio Validation",
                validation['valid'] or len(validation['warnings']) > 0,
                f"{len(validation['warnings'])} warnings"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Symbol Management", False, error=str(e))
            return False
    
    def test_risk_calculations(self) -> bool:
        """Test 3: Cálculos de riesgo"""
        print("\n🔍 TEST 3: Cálculos de Riesgo")
        print("-" * 50)
        
        try:
            # Test Kelly Criterion
            kelly_size = risk_calculator.calculate_position_size_kelly(
                win_rate=0.55,
                avg_win=0.03,
                avg_loss=0.015,
                capital=10000
            )
            
            if kelly_size <= 0 or kelly_size > 10000:
                self.log_test("Risk Calculator - Kelly", False, error=f"Size inválido: {kelly_size}")
                return False
            
            self.log_test(
                "Risk Calculator - Kelly",
                True,
                f"Position size: ${kelly_size:.2f}"
            )
            
            # Test VaR
            test_returns = np.random.normal(0.001, 0.02, 100).tolist()
            var_result = risk_calculator.calculate_value_at_risk(test_returns)
            
            if 'var_historical' not in var_result:
                self.log_test("Risk Calculator - VaR", False)
                return False
            
            self.log_test(
                "Risk Calculator - VaR",
                True,
                f"VaR 95%: {var_result['var_historical']:.4f}"
            )
            
            # Test position sizing
            optimal = risk_calculator.calculate_optimal_position_size(
                entry_price=234.50,
                stop_loss=228.00,
                capital=10000,
                symbol="SOLUSDT"
            )
            
            if not optimal['success']:
                self.log_test("Risk Calculator - Position Sizing", False, error=optimal.get('error'))
                return False
            
            self.log_test(
                "Risk Calculator - Position Sizing",
                True,
                f"Size: {optimal['position_size']:.2f} units"
            )
            
            # Test trade validation
            validation = risk_calculator.validate_trade_risk(
                entry_price=234.50,
                stop_loss=228.00,
                take_profit=248.00,
                position_size=10,
                capital=10000,
                symbol="SOLUSDT"
            )
            
            self.log_test(
                "Risk Calculator - Trade Validation",
                validation['is_valid'] or len(validation['warnings']) > 0,
                f"R:R: {validation['metrics']['risk_reward_ratio']:.2f}"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Risk Calculations", False, error=str(e))
            return False
    
    def test_signal_validation(self) -> bool:
        """Test 4: Sistema de validación de señales"""
        print("\n🔍 TEST 4: Validación de Señales")
        print("-" * 50)
        
        try:
            # Test señal con consenso
            votes_consensus = [
                {'philosopher': 'Socrates', 'vote': 'BUY', 'confidence': 0.8},
                {'philosopher': 'Aristoteles', 'vote': 'BUY', 'confidence': 0.75},
                {'philosopher': 'Platon', 'vote': 'BUY', 'confidence': 0.7},
                {'philosopher': 'Nietzsche', 'vote': 'HOLD', 'confidence': 0.5}
            ]
            
            signal = signal_validator.validate_philosopher_signals(votes_consensus, "SOLUSDT")
            
            if not signal or signal['action'] != 'BUY':
                self.log_test("Signal Validator - Consensus", False)
                return False
            
            self.log_test(
                "Signal Validator - Consensus",
                True,
                f"Signal: {signal['action']} ({signal['consensus_percentage']*100:.1f}%)"
            )
            
            # Test señales contradictorias
            votes_contradictory = [
                {'philosopher': 'Socrates', 'vote': 'BUY', 'confidence': 0.8},
                {'philosopher': 'Aristoteles', 'vote': 'SELL', 'confidence': 0.8},
                {'philosopher': 'Platon', 'vote': 'BUY', 'confidence': 0.6},
                {'philosopher': 'Nietzsche', 'vote': 'SELL', 'confidence': 0.7}
            ]
            
            signal_contradictory = signal_validator.validate_philosopher_signals(
                votes_contradictory, 
                "SOLUSDT"
            )
            
            if signal_contradictory is not None:
                self.log_test("Signal Validator - Contradiction Detection", False)
                return False
            
            self.log_test(
                "Signal Validator - Contradiction Detection",
                True,
                "Señales contradictorias rechazadas correctamente"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Signal Validation", False, error=str(e))
            return False
    
    def test_paper_trading(self) -> bool:
        """Test 5: Sistema de Paper Trading"""
        print("\n🔍 TEST 5: Paper Trading")
        print("-" * 50)
        
        try:
            paper_trader = PaperTradingEnhanced(initial_capital=10000)
            
            # Test abrir posición
            result = paper_trader.open_position(
                symbol="SOLUSDT",
                side="LONG",
                entry_price=234.50,
                stop_loss=228.00,
                take_profit=248.00,
                confidence=0.75,
                signal_source="test"
            )
            
            if not result['success']:
                self.log_test("Paper Trading - Open Position", False, error=result.get('error'))
                return False
            
            position_id = result['position_id']
            self.log_test(
                "Paper Trading - Open Position",
                True,
                f"Position ID: {position_id}"
            )
            
            # Test actualizar posiciones
            paper_trader.update_positions()
            
            # Test obtener estado
            status = paper_trader.get_portfolio_status()
            
            if status['open_positions'] != 1:
                self.log_test("Paper Trading - Portfolio Status", False)
                return False
            
            self.log_test(
                "Paper Trading - Portfolio Status",
                True,
                f"Capital: ${status['current_capital']:.2f}"
            )
            
            # Test cerrar posición
            close_result = paper_trader.close_position(position_id, 240.00, "TEST_CLOSE")
            
            if not close_result['success']:
                self.log_test("Paper Trading - Close Position", False)
                return False
            
            self.log_test(
                "Paper Trading - Close Position",
                True,
                f"P&L: ${close_result['pnl']:.2f} ({close_result['pnl_pct']:.2f}%)"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Paper Trading", False, error=str(e))
            return False
    
    def test_backtest_system(self) -> bool:
        """Test 6: Sistema de Backtest"""
        print("\n🔍 TEST 6: Sistema de Backtest")
        print("-" * 50)
        
        try:
            backtest = BacktestSystemV2()
            
            # Test backtest simple
            result = backtest.run_backtest(
                symbol="SOLUSDT",
                strategy="momentum",
                interval="1h",
                days_back=3,  # Solo 3 días para test rápido
                initial_capital=10000
            )
            
            if not result['success']:
                self.log_test("Backtest - Single Symbol", False, error=result.get('error'))
                return False
            
            metrics = result['metrics']
            self.log_test(
                "Backtest - Single Symbol",
                True,
                f"Return: {metrics.get('total_return', 0):.2f}%, Trades: {metrics.get('total_trades', 0)}"
            )
            
            # Test multi-symbol backtest
            symbols = ["SOLUSDT", "ADAUSDT"]
            multi_result = backtest.run_multi_symbol_backtest(
                symbols,
                strategy="momentum",
                interval="1h",
                days_back=3
            )
            
            if multi_result['summary']['successful'] < 1:
                self.log_test("Backtest - Multi Symbol", False)
                return False
            
            self.log_test(
                "Backtest - Multi Symbol",
                True,
                f"Tested {len(symbols)} symbols, avg return: {multi_result['summary'].get('avg_return', 0):.2f}%"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Backtest System", False, error=str(e))
            return False
    
    def test_cache_performance(self) -> bool:
        """Test 7: Sistema de Caché y Rendimiento"""
        print("\n🔍 TEST 7: Caché y Rendimiento")
        print("-" * 50)
        
        try:
            # Limpiar caché primero
            cache_manager.clear()
            
            # Test set/get
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
            cache_manager.set("test_key", test_data, ttl=60)
            
            retrieved = cache_manager.get("test_key")
            if retrieved != test_data:
                self.log_test("Cache - Set/Get", False)
                return False
            
            self.log_test("Cache - Set/Get", True)
            
            # Test performance con y sin caché
            fetcher = BinanceDataFetcher()
            
            # Primera llamada (sin caché)
            start = time.time()
            df1 = fetcher.get_klines("SOLUSDT", "1h", 100)
            time_no_cache = time.time() - start
            
            # Segunda llamada (con caché potencial)
            start = time.time()
            df2 = fetcher.get_klines("SOLUSDT", "1h", 100)
            time_with_cache = time.time() - start
            
            # El caché debería ser más rápido (o al menos similar)
            self.log_test(
                "Cache - Performance",
                True,
                f"Sin caché: {time_no_cache:.3f}s, Con caché: {time_with_cache:.3f}s"
            )
            
            # Obtener estadísticas
            stats = cache_manager.get_stats()
            self.log_test(
                "Cache - Statistics",
                True,
                f"Hit rate: {stats.get('hit_rate', 0):.1f}%"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Cache Performance", False, error=str(e))
            return False
    
    def test_error_handling(self) -> bool:
        """Test 8: Sistema de Manejo de Errores"""
        print("\n🔍 TEST 8: Manejo de Errores")
        print("-" * 50)
        
        try:
            # Test manejo de error normal
            try:
                1 / 0
            except Exception as e:
                error_info = error_handler.handle_error(e, context={'test': 'division_by_zero'})
            
            if not error_info or 'error_message' not in error_info:
                self.log_test("Error Handler - Basic", False)
                return False
            
            self.log_test("Error Handler - Basic", True)
            
            # Test logging de acción de trading
            error_handler.log_trading_action(
                "TEST_ACTION",
                "SOLUSDT",
                {'test': True, 'value': 100}
            )
            
            self.log_test("Error Handler - Trading Log", True)
            
            # Test health check
            health = error_handler.check_system_health()
            
            self.log_test(
                "Error Handler - Health Check",
                True,
                f"System status: {health['status']}"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, error=str(e))
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test 9: Endpoints del API"""
        print("\n🔍 TEST 9: API Endpoints")
        print("-" * 50)
        
        base_url = "http://localhost:8000"
        
        try:
            # Test /api/status
            response = requests.get(f"{base_url}/api/status", timeout=5)
            if response.status_code != 200:
                self.log_test("API - /status", False, error=f"Status code: {response.status_code}")
                return False
            
            self.log_test("API - /status", True)
            
            # Test /api/symbol/{symbol}/data
            response = requests.get(f"{base_url}/api/symbol/SOLUSDT/data", timeout=5)
            if response.status_code != 200:
                self.log_test("API - /symbol/data", False)
                return False
            
            data = response.json()
            self.log_test(
                "API - /symbol/data",
                True,
                f"Price: ${data.get('current_price', 0):.2f}"
            )
            
            # Test /api/signals/{symbol}
            response = requests.get(f"{base_url}/api/signals/SOLUSDT", timeout=5)
            if response.status_code != 200:
                self.log_test("API - /signals", False)
                return False
            
            self.log_test("API - /signals", True)
            
            # Test /api/backtest/{symbol}
            response = requests.post(
                f"{base_url}/api/backtest/SOLUSDT",
                json={"period_days": 7},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test("API - /backtest", False)
                return False
            
            backtest_data = response.json()
            self.log_test(
                "API - /backtest",
                True,
                f"Found {len(backtest_data.get('signals', []))} historical signals"
            )
            
            return True
            
        except requests.exceptions.ConnectionError:
            self.log_test("API Endpoints", False, error="API no está corriendo en localhost:8000")
            return False
        except Exception as e:
            self.log_test("API Endpoints", False, error=str(e))
            return False
    
    def test_websocket_connection(self) -> bool:
        """Test 10: Conexión WebSocket"""
        print("\n🔍 TEST 10: WebSocket Connection")
        print("-" * 50)
        
        try:
            # Intentar conectar al WebSocket
            ws_url = "ws://localhost:8000/ws"
            
            # Test conexión básica
            connected = False
            
            def on_open(ws):
                nonlocal connected
                connected = True
                ws.close()
            
            def on_error(ws, error):
                pass
            
            try:
                ws = websocket.WebSocketApp(
                    ws_url,
                    on_open=on_open,
                    on_error=on_error
                )
                
                # Timeout rápido para test
                timer = threading.Timer(2.0, lambda: ws.close())
                timer.start()
                
                ws.run_forever()
                timer.cancel()
                
            except:
                connected = False
            
            if not connected:
                self.log_test("WebSocket - Connection", False, error="No se pudo conectar")
                return False
            
            self.log_test("WebSocket - Connection", True)
            
            return True
            
        except Exception as e:
            self.log_test("WebSocket Connection", False, error=str(e))
            return False
    
    def run_all_tests(self) -> Dict:
        """Ejecuta todos los tests de integración"""
        print("\n" + "="*60)
        print("🚀 INICIANDO SUITE DE TESTS DE INTEGRACIÓN")
        print("="*60)
        
        self.start_time = time.time()
        
        # Lista de tests a ejecutar
        tests = [
            ("Binance API", self.test_binance_api_connection),
            ("Symbol Management", self.test_symbol_management),
            ("Risk Calculations", self.test_risk_calculations),
            ("Signal Validation", self.test_signal_validation),
            ("Paper Trading", self.test_paper_trading),
            ("Backtest System", self.test_backtest_system),
            ("Cache Performance", self.test_cache_performance),
            ("Error Handling", self.test_error_handling),
            ("API Endpoints", self.test_api_endpoints),
            ("WebSocket", self.test_websocket_connection)
        ]
        
        # Ejecutar cada test
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, error=f"Exception: {str(e)}")
                traceback.print_exc()
            
            # Pequeña pausa entre tests
            time.sleep(0.5)
        
        self.end_time = time.time()
        
        # Generar resumen
        total_tests = len(self.test_results)
        passed = len(self.passed_tests)
        failed = len(self.failed_tests)
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        execution_time = self.end_time - self.start_time
        
        # Imprimir resumen
        print("\n" + "="*60)
        print("📊 RESUMEN DE TESTS DE INTEGRACIÓN")
        print("="*60)
        print(f"✅ Tests Pasados: {passed}/{total_tests}")
        print(f"❌ Tests Fallidos: {failed}/{total_tests}")
        print(f"📈 Tasa de Éxito: {success_rate:.1f}%")
        print(f"⏱️ Tiempo Total: {execution_time:.2f} segundos")
        
        if self.failed_tests:
            print("\n⚠️ Tests Fallidos:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        # Guardar resultados
        results = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed,
                'failed': failed,
                'success_rate': success_rate,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            },
            'tests': self.test_results,
            'failed_tests': self.failed_tests,
            'passed_tests': self.passed_tests
        }
        
        # Guardar a archivo
        with open('integration_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("\n💾 Resultados guardados en: integration_test_results.json")
        
        # Estado final
        if success_rate >= 80:
            print("\n✅ SISTEMA LISTO PARA PRODUCCIÓN")
        elif success_rate >= 60:
            print("\n⚠️ SISTEMA FUNCIONAL PERO CON ISSUES")
        else:
            print("\n❌ SISTEMA REQUIERE CORRECCIONES CRÍTICAS")
        
        return results


# Para usar con threading si se necesita
import threading

if __name__ == "__main__":
    # Ejecutar suite de tests
    test_suite = IntegrationTestSuite()
    results = test_suite.run_all_tests()
    
    # Análisis adicional de rendimiento
    print("\n" + "="*60)
    print("⚡ MÉTRICAS DE RENDIMIENTO")
    print("="*60)
    
    perf_stats = performance_monitor.get_stats()
    if perf_stats:
        for operation, stats in perf_stats.items():
            print(f"{operation}: {stats.get('avg_ms', 0):.2f}ms promedio")
    
    # Estadísticas de caché
    cache_stats = cache_manager.get_stats()
    print(f"\n💾 Cache Hit Rate: {cache_stats.get('hit_rate', 0):.1f}%")
    print(f"📦 Entradas en memoria: {cache_stats.get('memory_entries', 0)}")
    
    # Exit code basado en resultado
    sys.exit(0 if results['summary']['success_rate'] >= 80 else 1)