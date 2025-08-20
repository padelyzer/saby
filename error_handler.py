#!/usr/bin/env python3
"""
Sistema centralizado de gestión de errores y logging
"""

import logging
import traceback
from datetime import datetime, timedelta
import json
from typing import Any, Dict, Optional
import sys
import os

# Configuración de logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configurar formato de logs
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class ErrorHandler:
    """Manejador centralizado de errores"""
    
    def __init__(self, service_name: str = "trading_system"):
        self.service_name = service_name
        self.error_count = 0
        self.error_history = []
        self.setup_logging()
        
    def setup_logging(self):
        """Configura el sistema de logging"""
        # Logger principal
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo
        log_file = f"{LOG_DIR}/{self.service_name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # Handler para errores críticos
        error_file = f"{LOG_DIR}/{self.service_name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Agregar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None, critical: bool = False) -> Dict:
        """
        Maneja un error de manera centralizada
        
        Args:
            error: La excepción capturada
            context: Contexto adicional del error
            critical: Si el error es crítico y debe detener el sistema
        
        Returns:
            Diccionario con información del error
        """
        self.error_count += 1
        
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'critical': critical,
            'error_count': self.error_count
        }
        
        # Agregar al historial
        self.error_history.append(error_info)
        if len(self.error_history) > 100:  # Mantener solo los últimos 100 errores
            self.error_history.pop(0)
        
        # Logging según severidad
        if critical:
            self.logger.critical(f"CRITICAL ERROR: {error_info['error_message']}")
            self.logger.critical(f"Context: {json.dumps(context, default=str)}")
            self.logger.critical(f"Traceback: {error_info['traceback']}")
            
            # Si es crítico, también guardar en archivo especial
            self.save_critical_error(error_info)
        else:
            self.logger.error(f"ERROR: {error_info['error_message']}")
            if context:
                self.logger.error(f"Context: {json.dumps(context, default=str)}")
        
        return error_info
    
    def save_critical_error(self, error_info: Dict):
        """Guarda errores críticos en archivo separado"""
        critical_file = f"{LOG_DIR}/critical_errors.json"
        
        try:
            # Leer errores existentes
            if os.path.exists(critical_file):
                with open(critical_file, 'r') as f:
                    critical_errors = json.load(f)
            else:
                critical_errors = []
            
            # Agregar nuevo error
            critical_errors.append(error_info)
            
            # Guardar
            with open(critical_file, 'w') as f:
                json.dump(critical_errors, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error guardando error crítico: {e}")
    
    def log_trading_action(self, action: str, symbol: str, details: Dict):
        """Registra acciones de trading"""
        self.logger.info(f"TRADING ACTION: {action} for {symbol}")
        self.logger.info(f"Details: {json.dumps(details, default=str)}")
        
        # Guardar en archivo de auditoría
        audit_file = f"{LOG_DIR}/trading_audit_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            if os.path.exists(audit_file):
                with open(audit_file, 'r') as f:
                    audit_log = json.load(f)
            else:
                audit_log = []
            
            audit_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'symbol': symbol,
                'details': details
            })
            
            with open(audit_file, 'w') as f:
                json.dump(audit_log, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error en auditoría: {e}")
    
    def get_error_stats(self) -> Dict:
        """Obtiene estadísticas de errores"""
        if not self.error_history:
            return {
                'total_errors': 0,
                'critical_errors': 0,
                'error_types': {},
                'last_error': None
            }
        
        error_types = {}
        critical_count = 0
        
        for error in self.error_history:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
            if error['critical']:
                critical_count += 1
        
        return {
            'total_errors': self.error_count,
            'critical_errors': critical_count,
            'error_types': error_types,
            'last_error': self.error_history[-1] if self.error_history else None,
            'errors_last_hour': len([e for e in self.error_history 
                                    if datetime.fromisoformat(e['timestamp']) > 
                                    datetime.now() - timedelta(hours=1)])
        }
    
    def check_system_health(self) -> Dict:
        """Verifica la salud del sistema basándose en errores"""
        stats = self.get_error_stats()
        
        health_status = "HEALTHY"
        issues = []
        
        # Verificar errores críticos
        if stats['critical_errors'] > 0:
            health_status = "CRITICAL"
            issues.append(f"{stats['critical_errors']} errores críticos detectados")
        
        # Verificar tasa de errores
        elif stats.get('errors_last_hour', 0) > 10:
            health_status = "WARNING"
            issues.append(f"{stats.get('errors_last_hour', 0)} errores en la última hora")
        
        # Verificar tipos de errores recurrentes
        for error_type, count in stats['error_types'].items():
            if count > 5:
                if health_status == "HEALTHY":
                    health_status = "WARNING"
                issues.append(f"Error recurrente: {error_type} ({count} veces)")
        
        return {
            'status': health_status,
            'issues': issues,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }


# Singleton global
error_handler = ErrorHandler()

def safe_execute(func, *args, **kwargs):
    """
    Ejecuta una función de manera segura con manejo de errores
    
    Usage:
        result = safe_execute(risky_function, arg1, arg2, context={'symbol': 'BTCUSDT'})
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        context = kwargs.pop('context', {})
        context['function'] = func.__name__
        context['args'] = str(args)[:100]  # Limitar tamaño
        
        error_info = error_handler.handle_error(e, context)
        
        # Retornar None o valor por defecto
        return kwargs.get('default', None)


class TradingErrorContext:
    """Context manager para manejo de errores en trading"""
    
    def __init__(self, operation: str, symbol: str = None, critical: bool = False):
        self.operation = operation
        self.symbol = symbol
        self.critical = critical
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            context = {
                'operation': self.operation,
                'symbol': self.symbol
            }
            
            error_handler.handle_error(
                exc_val,
                context=context,
                critical=self.critical
            )
            
            # Suprimir excepción si no es crítica
            return not self.critical


if __name__ == "__main__":
    # Test del sistema de errores
    print("🔍 Probando sistema de gestión de errores...")
    
    # Test error normal
    try:
        1 / 0
    except Exception as e:
        error_handler.handle_error(e, context={'test': 'division_by_zero'})
    
    # Test error crítico
    try:
        raise ValueError("Error crítico de prueba")
    except Exception as e:
        error_handler.handle_error(e, context={'test': 'critical'}, critical=True)
    
    # Test con context manager
    with TradingErrorContext("test_operation", "BTCUSDT"):
        print("Operación segura")
        # raise Exception("Error de prueba")  # Descomentar para probar
    
    # Test acción de trading
    error_handler.log_trading_action(
        "SIGNAL_GENERATED",
        "BTCUSDT",
        {'action': 'BUY', 'price': 50000, 'confidence': 0.75}
    )
    
    # Mostrar estadísticas
    print("\n📊 Estadísticas de errores:")
    stats = error_handler.get_error_stats()
    print(json.dumps(stats, indent=2, default=str))
    
    # Verificar salud del sistema
    print("\n🏥 Salud del sistema:")
    health = error_handler.check_system_health()
    print(json.dumps(health, indent=2, default=str))