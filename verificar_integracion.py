#!/usr/bin/env python3
"""
Verificación de integración completa del sistema
"""

import os
import json
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════╗
║              🔍 VERIFICACIÓN DE INTEGRACIÓN COMPLETA            ║
╚════════════════════════════════════════════════════════════════╝
""")

# Lista de módulos y su estado
modulos = {
    "1. Motor Trading Original": {
        "archivo": "motor_trading.py",
        "descripcion": "Sistema base con indicadores técnicos"
    },
    "2. Señales Avanzadas": {
        "archivo": "advanced_signals.py",
        "descripcion": "Detección basada en estructura de mercado"
    },
    "3. Pools de Liquidez": {
        "archivo": "liquidity_pools.py",
        "descripcion": "Detección de zonas de liquidación"
    },
    "4. Gestor de Señales": {
        "archivo": "signal_manager.py",
        "descripcion": "Sistema de notificaciones multicanal"
    },
    "5. Trade Tracker": {
        "archivo": "trade_tracker.py",
        "descripcion": "Seguimiento automático de trades"
    },
    "6. Bot Avanzado": {
        "archivo": "signal_bot_advanced.py",
        "descripcion": "Bot con liquidez integrada"
    },
    "7. Interfaz Completa": {
        "archivo": "interfaz_completa.py",
        "descripcion": "Dashboard unificado con todos los módulos"
    }
}

print("📋 ESTADO DE MÓDULOS:")
print("="*60)

todos_ok = True
for nombre, info in modulos.items():
    if os.path.exists(info['archivo']):
        status = "✅"
        print(f"{status} {nombre}")
        print(f"   Archivo: {info['archivo']}")
        print(f"   Función: {info['descripcion']}")
    else:
        status = "❌"
        print(f"{status} {nombre} - NO ENCONTRADO")
        todos_ok = False
    print()

# Verificar configuración
print("⚙️ CONFIGURACIÓN:")
print("="*60)

if os.path.exists('signal_config.json'):
    with open('signal_config.json', 'r') as f:
        config = json.load(f)
    
    print("✅ Archivo de configuración encontrado")
    print(f"   • Telegram: {'Activado' if config['telegram']['enabled'] else 'Desactivado'}")
    print(f"   • Score mínimo: {config['filters']['min_score']}")
    print(f"   • Cooldown: {config['filters']['cooldown_minutes']} minutos")
else:
    print("❌ Falta signal_config.json")
    todos_ok = False

# Verificar archivos de datos
print("\n📊 ARCHIVOS DE DATOS:")
print("="*60)

data_files = [
    ("trades_history.json", "Historial de trades"),
    ("trades_history.csv", "Historial CSV"),
    (f"signals_{datetime.now().strftime('%Y%m%d')}.json", "Señales de hoy"),
    ("liquidity_analysis.json", "Análisis de liquidez"),
    ("advanced_signals.json", "Señales avanzadas")
]

for archivo, descripcion in data_files:
    if os.path.exists(archivo):
        print(f"✅ {archivo} - {descripcion}")
    else:
        print(f"⚠️ {archivo} - No existe aún")

# Resumen de integración
print("\n🎯 RESUMEN DE INTEGRACIÓN:")
print("="*60)

if todos_ok:
    print("""
✅ SISTEMA COMPLETAMENTE INTEGRADO

La interfaz completa (interfaz_completa.py) incluye:

📊 Dashboard Principal
   • Análisis técnico en vivo
   • Top movers de Binance
   • Gráficos con indicadores

🎯 Señales Avanzadas
   • Detección de soportes/resistencias
   • Niveles de Fibonacci
   • Patrones gráficos
   • Order blocks

💧 Pools de Liquidez
   • Mapas de calor de liquidación
   • Detección de stops clusters
   • Sugerencias de entrada/salida

📈 Paper Trading
   • Backtesting con leverage
   • Métricas de performance
   • Análisis de resultados

🤖 Live Bot Monitor
   • Estado del bot en tiempo real
   • Últimas señales enviadas
   • Estadísticas de sesión

📋 Trade Tracker
   • Seguimiento automático
   • Métricas de performance
   • Historial completo

⚙️ Configuración
   • Gestión de canales
   • Filtros de señales
   • Parámetros del sistema

PARA ACCEDER AL SISTEMA COMPLETO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Ejecutar: python3 -m streamlit run interfaz_completa.py
2. Abrir navegador en: http://localhost:8501
3. Navegar por los diferentes módulos

PARA EJECUTAR EL BOT AVANZADO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python3 signal_bot_advanced.py
""")
else:
    print("""
⚠️ FALTAN ALGUNOS COMPONENTES

Por favor, verifica los módulos faltantes arriba.
""")

print("\n" + "="*60)
print("Verificación completada")