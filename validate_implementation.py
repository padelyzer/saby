#!/usr/bin/env python3
"""
Validation Script for Phase 1 & 2 Implementation
Valida que todos los componentes estén funcionando correctamente
"""

import sys
import importlib
import traceback
from datetime import datetime
import pandas as pd
import numpy as np

class ImplementationValidator:
    def __init__(self):
        self.validation_results = {
            'phase_1': {},
            'phase_2': {},
            'integration': {},
            'summary': {}
        }
        
    def validate_all(self):
        """Ejecuta todas las validaciones"""
        
        print("🔍 VALIDACIÓN DE IMPLEMENTACIÓN - FASE 1 Y 2")
        print("="*70)
        print(f"📅 Timestamp: {datetime.now()}")
        print("="*70)
        
        # Validar Fase 1
        print("\n📋 FASE 1 - COMPONENTES CRÍTICOS:")
        print("-"*50)
        self.validate_phase_1()
        
        # Validar Fase 2
        print("\n📋 FASE 2 - COMPONENTES IMPORTANTES:")
        print("-"*50)
        self.validate_phase_2()
        
        # Validar Integración
        print("\n🔗 VALIDACIÓN DE INTEGRACIÓN:")
        print("-"*50)
        self.validate_integration()
        
        # Generar resumen
        self.generate_summary()
        
        return self.validation_results
    
    def validate_phase_1(self):
        """Valida componentes de Fase 1"""
        
        # 1. On-Chain Analysis
        self.validate_component(
            'onchain_analysis',
            'OnChainAnalyzer',
            test_method='get_onchain_score',
            test_args=('BTC', 24)
        )
        
        # 2. Macro Correlations
        self.validate_component(
            'macro_correlations',
            'MacroCorrelationAnalyzer',
            test_method='get_macro_analysis',
            test_args=('BTC-USD', 30)
        )
        
        # 3. Entry Signals Optimizer
        self.validate_component(
            'entry_signals_optimizer',
            'EntrySignalsOptimizer',
            test_method='optimize_entry_signal',
            test_args=(self.get_dummy_df(), self.get_dummy_current(), 
                      self.get_dummy_prev(), 'LONG', 7.0)
        )
        
        # 4. Paper Trading System
        self.validate_component(
            'paper_trading_system',
            'PaperTradingSystem',
            test_method='analyze_signal',
            test_args=('BTC-USD', '1h'),
            init_args=(10000,)
        )
    
    def validate_phase_2(self):
        """Valida componentes de Fase 2"""
        
        # 5. Bollinger Bands Squeeze
        self.validate_component(
            'bollinger_squeeze_strategy',
            'BollingerSqueezeStrategy',
            test_method='analyze_bollinger_signal',
            test_args=(self.get_dummy_df(), self.get_dummy_current(), 'LONG')
        )
        
        # 6. Dynamic Trailing Stops
        self.validate_component(
            'trailing_stops_dynamic',
            'DynamicTrailingStops',
            test_method='initialize_trailing_stop',
            test_args=('BTC-USD', self.get_dummy_position())
        )
        
        # 7. Volume Position Sizing
        self.validate_component(
            'volume_position_sizing',
            'VolumeBasedPositionSizing',
            test_method='calculate_optimal_position_size',
            test_args=('BTC-USD', self.get_dummy_signal(), 10000),
            init_args=(10000,)
        )
        
        # 8. Fear & Greed Index
        self.validate_component(
            'fear_greed_index',
            'FearGreedIndexAnalyzer',
            test_method='get_fear_greed_analysis',
            test_args=('BTC',)
        )
    
    def validate_component(self, module_name, class_name, test_method=None, 
                          test_args=None, init_args=None):
        """Valida un componente individual"""
        
        component_key = module_name
        
        try:
            # Importar módulo
            module = importlib.import_module(module_name)
            print(f"\n✅ Módulo '{module_name}' importado correctamente")
            
            # Verificar clase
            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                print(f"✅ Clase '{class_name}' encontrada")
                
                # Instanciar clase
                if init_args:
                    instance = cls(*init_args)
                else:
                    instance = cls()
                print(f"✅ Instancia creada exitosamente")
                
                # Probar método si se especifica
                if test_method and hasattr(instance, test_method):
                    method = getattr(instance, test_method)
                    if test_args:
                        result = method(*test_args)
                    else:
                        result = method()
                    
                    # Validar resultado
                    if result is not None:
                        print(f"✅ Método '{test_method}' ejecutado con éxito")
                        self.validation_results.setdefault('phase_1' if 'phase_1' in str(module_name) else 'phase_2', {})[component_key] = {
                            'status': 'PASS',
                            'module': module_name,
                            'class': class_name,
                            'test_method': test_method,
                            'result_type': type(result).__name__
                        }
                    else:
                        print(f"⚠️ Método '{test_method}' retornó None")
                        self.validation_results.setdefault('phase_1' if 'phase_1' in str(module_name) else 'phase_2', {})[component_key] = {
                            'status': 'WARNING',
                            'message': 'Method returned None'
                        }
                else:
                    self.validation_results.setdefault('phase_1' if 'phase_1' in str(module_name) else 'phase_2', {})[component_key] = {
                        'status': 'PASS',
                        'module': module_name,
                        'class': class_name
                    }
            else:
                print(f"❌ Clase '{class_name}' no encontrada en módulo")
                self.validation_results.setdefault('phase_1' if 'phase_1' in str(module_name) else 'phase_2', {})[component_key] = {
                    'status': 'FAIL',
                    'error': f'Class {class_name} not found'
                }
                
        except ImportError as e:
            print(f"❌ Error importando módulo '{module_name}': {e}")
            self.validation_results.setdefault('phase_1' if 'phase_1' in str(module_name) else 'phase_2', {})[component_key] = {
                'status': 'FAIL',
                'error': str(e)
            }
        except Exception as e:
            print(f"❌ Error validando '{module_name}': {e}")
            self.validation_results.setdefault('phase_1' if 'phase_1' in str(module_name) else 'phase_2', {})[component_key] = {
                'status': 'FAIL',
                'error': str(e)
            }
    
    def validate_integration(self):
        """Valida la integración entre componentes"""
        
        print("\n🔗 Probando integración entre sistemas...")
        
        try:
            # Test 1: Paper Trading + Entry Optimizer + On-Chain
            from paper_trading_system import PaperTradingSystem
            from entry_signals_optimizer import EntrySignalsOptimizer
            from onchain_analysis import OnChainAnalyzer
            
            paper = PaperTradingSystem(10000)
            optimizer = EntrySignalsOptimizer()
            onchain = OnChainAnalyzer()
            
            # Verificar que pueden trabajar juntos
            signal, msg = paper.analyze_signal('BTC-USD')
            if signal:
                print("✅ Paper Trading + Optimizers integration: PASS")
                self.validation_results['integration']['paper_optimizer'] = 'PASS'
            else:
                print(f"⚠️ Paper Trading integration: {msg}")
                self.validation_results['integration']['paper_optimizer'] = 'WARNING'
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            self.validation_results['integration']['paper_optimizer'] = 'FAIL'
        
        try:
            # Test 2: Trailing Stops + Position Sizing
            from trailing_stops_dynamic import DynamicTrailingStops
            from volume_position_sizing import VolumeBasedPositionSizing
            
            trailing = DynamicTrailingStops()
            sizing = VolumeBasedPositionSizing()
            
            position = self.get_dummy_position()
            stop_config = trailing.initialize_trailing_stop('BTC-USD', position)
            
            signal = self.get_dummy_signal()
            size_config = sizing.calculate_optimal_position_size('BTC-USD', signal, 10000)
            
            if stop_config and size_config:
                print("✅ Trailing Stops + Position Sizing integration: PASS")
                self.validation_results['integration']['stops_sizing'] = 'PASS'
            
        except Exception as e:
            print(f"❌ Stops/Sizing integration failed: {e}")
            self.validation_results['integration']['stops_sizing'] = 'FAIL'
        
        try:
            # Test 3: Fear & Greed + Macro Analysis
            from fear_greed_index import FearGreedIndexAnalyzer
            from macro_correlations import MacroCorrelationAnalyzer
            
            fg = FearGreedIndexAnalyzer()
            macro = MacroCorrelationAnalyzer()
            
            fg_analysis = fg.get_fear_greed_analysis('BTC')
            macro_analysis = macro.get_macro_analysis('BTC-USD')
            
            if fg_analysis and macro_analysis:
                print("✅ Fear&Greed + Macro integration: PASS")
                self.validation_results['integration']['fg_macro'] = 'PASS'
                
        except Exception as e:
            print(f"❌ FG/Macro integration failed: {e}")
            self.validation_results['integration']['fg_macro'] = 'FAIL'
    
    def get_dummy_df(self):
        """Genera DataFrame dummy para pruebas"""
        dates = pd.date_range(end=datetime.now(), periods=100, freq='H')
        return pd.DataFrame({
            'Open': np.random.uniform(40000, 50000, 100),
            'High': np.random.uniform(40500, 50500, 100),
            'Low': np.random.uniform(39500, 49500, 100),
            'Close': np.random.uniform(40000, 50000, 100),
            'Volume': np.random.uniform(1000, 5000, 100),
            'RSI': np.random.uniform(30, 70, 100),
            'MACD': np.random.uniform(-100, 100, 100),
            'MACD_Signal': np.random.uniform(-100, 100, 100),
            'ATR': np.random.uniform(500, 1500, 100)
        }, index=dates)
    
    def get_dummy_current(self):
        """Genera datos actuales dummy"""
        return pd.Series({
            'Open': 45000,
            'High': 45500,
            'Low': 44500,
            'Close': 45200,
            'Volume': 3000,
            'RSI': 55,
            'MACD': 50,
            'MACD_Signal': 45,
            'ATR': 1000
        })
    
    def get_dummy_prev(self):
        """Genera datos previos dummy"""
        return pd.Series({
            'Open': 44800,
            'High': 45200,
            'Low': 44600,
            'Close': 45000,
            'Volume': 2800,
            'RSI': 53,
            'MACD': 48,
            'MACD_Signal': 46,
            'ATR': 950
        })
    
    def get_dummy_position(self):
        """Genera posición dummy"""
        return {
            'id': 'test_001',
            'symbol': 'BTC-USD',
            'type': 'LONG',
            'entry_price': 45000,
            'entry_time': datetime.now(),
            'signal_score': 7.5
        }
    
    def get_dummy_signal(self):
        """Genera señal dummy"""
        return {
            'symbol': 'BTC-USD',
            'type': 'LONG',
            'final_score': 7.8,
            'entry_price': 45000,
            'timestamp': datetime.now()
        }
    
    def generate_summary(self):
        """Genera resumen de validación"""
        
        print("\n" + "="*70)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("="*70)
        
        # Contar resultados
        phase1_pass = sum(1 for v in self.validation_results.get('phase_1', {}).values() 
                         if isinstance(v, dict) and v.get('status') == 'PASS')
        phase1_total = len(self.validation_results.get('phase_1', {}))
        
        phase2_pass = sum(1 for v in self.validation_results.get('phase_2', {}).values() 
                         if isinstance(v, dict) and v.get('status') == 'PASS')
        phase2_total = len(self.validation_results.get('phase_2', {}))
        
        integration_pass = sum(1 for v in self.validation_results.get('integration', {}).values() 
                              if v == 'PASS')
        integration_total = len(self.validation_results.get('integration', {}))
        
        total_pass = phase1_pass + phase2_pass + integration_pass
        total_tests = phase1_total + phase2_total + integration_total
        
        # Imprimir resumen
        print(f"\n📈 FASE 1 - CRÍTICA:")
        print(f"   ✅ Pasadas: {phase1_pass}/{phase1_total}")
        print(f"   📊 Tasa de éxito: {(phase1_pass/phase1_total*100) if phase1_total > 0 else 0:.1f}%")
        
        print(f"\n📈 FASE 2 - IMPORTANTE:")
        print(f"   ✅ Pasadas: {phase2_pass}/{phase2_total}")
        print(f"   📊 Tasa de éxito: {(phase2_pass/phase2_total*100) if phase2_total > 0 else 0:.1f}%")
        
        print(f"\n🔗 INTEGRACIÓN:")
        print(f"   ✅ Pasadas: {integration_pass}/{integration_total}")
        print(f"   📊 Tasa de éxito: {(integration_pass/integration_total*100) if integration_total > 0 else 0:.1f}%")
        
        print(f"\n📊 TOTAL GENERAL:")
        print(f"   ✅ Pruebas pasadas: {total_pass}/{total_tests}")
        print(f"   📊 Tasa de éxito global: {(total_pass/total_tests*100) if total_tests > 0 else 0:.1f}%")
        
        # Estado final
        if total_pass == total_tests:
            print(f"\n✅ VALIDACIÓN EXITOSA - SISTEMA LISTO PARA PRODUCCIÓN")
            self.validation_results['summary']['status'] = 'SUCCESS'
        elif total_pass >= total_tests * 0.8:
            print(f"\n⚠️ VALIDACIÓN PARCIAL - REVISAR COMPONENTES FALLIDOS")
            self.validation_results['summary']['status'] = 'PARTIAL'
        else:
            print(f"\n❌ VALIDACIÓN FALLIDA - REQUIERE CORRECCIONES")
            self.validation_results['summary']['status'] = 'FAILED'
        
        self.validation_results['summary']['stats'] = {
            'phase1_success_rate': (phase1_pass/phase1_total*100) if phase1_total > 0 else 0,
            'phase2_success_rate': (phase2_pass/phase2_total*100) if phase2_total > 0 else 0,
            'integration_success_rate': (integration_pass/integration_total*100) if integration_total > 0 else 0,
            'total_success_rate': (total_pass/total_tests*100) if total_tests > 0 else 0,
            'total_tests': total_tests,
            'total_passed': total_pass
        }
        
        # Listar componentes fallidos
        failed_components = []
        for phase in ['phase_1', 'phase_2']:
            for component, result in self.validation_results.get(phase, {}).items():
                if isinstance(result, dict) and result.get('status') == 'FAIL':
                    failed_components.append(f"{phase}/{component}: {result.get('error', 'Unknown error')}")
        
        if failed_components:
            print(f"\n❌ COMPONENTES FALLIDOS:")
            for component in failed_components:
                print(f"   • {component}")
        
        return self.validation_results['summary']

def main():
    """Función principal de validación"""
    
    validator = ImplementationValidator()
    results = validator.validate_all()
    
    print("\n" + "="*70)
    print("✅ VALIDACIÓN COMPLETADA")
    print("="*70)
    
    return results

if __name__ == "__main__":
    main()