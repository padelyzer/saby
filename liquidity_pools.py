#!/usr/bin/env python3
"""
Sistema de Detección de Pools de Liquidez
Identifica zonas donde se acumulan stops y liquidaciones
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

class LiquidityPoolDetector:
    """Detecta pools de liquidez basados en niveles de apalancamiento común"""
    
    def __init__(self):
        # Niveles de apalancamiento comunes en crypto
        self.common_leverages = [3, 5, 10, 20, 25, 50, 100]
        
        # Configuración
        self.min_pool_strength = 3  # Mínimo de niveles confluyentes
        self.liquidation_buffer = 0.002  # 0.2% buffer para liquidación
        
    def calculate_liquidation_levels(self, entry_price: float, leverage: int, direction: str = 'LONG') -> float:
        """
        Calcula el nivel de liquidación para una posición
        
        Fórmula para LONG: Liq = Entry * (1 - 1/leverage + fees)
        Fórmula para SHORT: Liq = Entry * (1 + 1/leverage - fees)
        """
        # Incluir fees de mantenimiento (aproximado 0.5%)
        maintenance_margin = 0.005
        
        if direction == 'LONG':
            # Liquidación cuando el precio cae
            liquidation_price = entry_price * (1 - (1/leverage) + maintenance_margin)
        else:  # SHORT
            # Liquidación cuando el precio sube
            liquidation_price = entry_price * (1 + (1/leverage) - maintenance_margin)
        
        return liquidation_price
    
    def find_volume_nodes(self, df: pd.DataFrame, window: int = 20) -> List[Dict]:
        """
        Encuentra nodos de alto volumen (puntos de entrada populares)
        """
        # Calcular perfil de volumen
        volume_profile = []
        
        # Dividir el rango de precio en bins
        price_range = df['High'].max() - df['Low'].min()
        n_bins = 50
        bin_size = price_range / n_bins
        
        for i in range(n_bins):
            price_level = df['Low'].min() + (i * bin_size)
            price_high = price_level + bin_size
            
            # Volumen en este rango de precio
            mask = (df['Low'] <= price_high) & (df['High'] >= price_level)
            volume_at_level = df.loc[mask, 'Volume'].sum()
            
            if volume_at_level > 0:
                volume_profile.append({
                    'price': price_level + (bin_size / 2),
                    'volume': volume_at_level,
                    'normalized': 0  # Se normalizará después
                })
        
        # Normalizar volumen
        if volume_profile:
            max_volume = max(vp['volume'] for vp in volume_profile)
            for vp in volume_profile:
                vp['normalized'] = vp['volume'] / max_volume
        
        # Filtrar solo nodos significativos (>50% del máximo)
        significant_nodes = [vp for vp in volume_profile if vp['normalized'] > 0.5]
        
        # Ordenar por volumen
        significant_nodes.sort(key=lambda x: x['volume'], reverse=True)
        
        return significant_nodes[:10]  # Top 10 nodos
    
    def detect_liquidity_pools(self, df: pd.DataFrame, current_price: float) -> Dict:
        """
        Detecta pools de liquidez basados en:
        1. Niveles de liquidación comunes
        2. Nodos de alto volumen (entradas populares)
        3. Máximos y mínimos históricos
        """
        
        # 1. Encontrar puntos de entrada populares (nodos de volumen)
        volume_nodes = self.find_volume_nodes(df)
        
        # 2. Calcular pools de liquidación para cada nodo y leverage
        liquidity_pools = {
            'above_price': [],  # Liquidaciones de shorts (precio sube)
            'below_price': []   # Liquidaciones de longs (precio baja)
        }
        
        # Para cada punto de entrada popular
        for node in volume_nodes:
            entry_price = node['price']
            entry_volume = node['normalized']
            
            # Calcular liquidaciones para diferentes leverages
            for leverage in self.common_leverages:
                # Liquidación de LONGS (debajo del precio)
                long_liq = self.calculate_liquidation_levels(entry_price, leverage, 'LONG')
                
                # Solo considerar si está relativamente cerca del precio actual (dentro del 20%)
                if abs(long_liq - current_price) / current_price < 0.20:
                    liquidity_pools['below_price'].append({
                        'price': long_liq,
                        'leverage': leverage,
                        'entry_price': entry_price,
                        'strength': entry_volume * (100 / leverage),  # Mayor leverage = más débil
                        'type': 'LONG_LIQUIDATION',
                        'distance_pct': ((long_liq - current_price) / current_price) * 100
                    })
                
                # Liquidación de SHORTS (arriba del precio)
                short_liq = self.calculate_liquidation_levels(entry_price, leverage, 'SHORT')
                
                if abs(short_liq - current_price) / current_price < 0.20:
                    liquidity_pools['above_price'].append({
                        'price': short_liq,
                        'leverage': leverage,
                        'entry_price': entry_price,
                        'strength': entry_volume * (100 / leverage),
                        'type': 'SHORT_LIQUIDATION',
                        'distance_pct': ((short_liq - current_price) / current_price) * 100
                    })
        
        # 3. Agregar máximos y mínimos históricos (atraen stops)
        recent_high = df['High'].tail(100).max()
        recent_low = df['Low'].tail(100).min()
        
        # Stops típicos arriba de máximos (para shorts)
        for offset in [0.01, 0.02, 0.03]:  # 1%, 2%, 3% arriba
            stop_level = recent_high * (1 + offset)
            liquidity_pools['above_price'].append({
                'price': stop_level,
                'leverage': 0,  # No es liquidación, es stop
                'entry_price': recent_high,
                'strength': 5 * (1 - offset * 10),  # Más cerca = más fuerte
                'type': 'SHORT_STOPS',
                'distance_pct': ((stop_level - current_price) / current_price) * 100
            })
        
        # Stops típicos debajo de mínimos (para longs)
        for offset in [0.01, 0.02, 0.03]:
            stop_level = recent_low * (1 - offset)
            liquidity_pools['below_price'].append({
                'price': stop_level,
                'leverage': 0,
                'entry_price': recent_low,
                'strength': 5 * (1 - offset * 10),
                'type': 'LONG_STOPS',
                'distance_pct': ((stop_level - current_price) / current_price) * 100
            })
        
        # 4. Agrupar pools cercanos (cluster)
        clustered_pools = self.cluster_liquidity_levels(liquidity_pools, tolerance=0.005)
        
        # 5. Calcular heatmap de liquidez
        heatmap = self.calculate_liquidity_heatmap(clustered_pools, current_price)
        
        return {
            'current_price': current_price,
            'pools': clustered_pools,
            'heatmap': heatmap,
            'volume_nodes': volume_nodes[:5],  # Top 5 nodos
            'analysis_time': datetime.now().isoformat()
        }
    
    def cluster_liquidity_levels(self, pools: Dict, tolerance: float = 0.005) -> Dict:
        """
        Agrupa niveles de liquidez cercanos para identificar zonas fuertes
        """
        clustered = {
            'above_price': [],
            'below_price': []
        }
        
        for direction in ['above_price', 'below_price']:
            if not pools[direction]:
                continue
            
            # Ordenar por precio
            sorted_pools = sorted(pools[direction], key=lambda x: x['price'])
            
            current_cluster = [sorted_pools[0]]
            
            for pool in sorted_pools[1:]:
                # Si está cerca del cluster actual, agregarlo
                cluster_avg = sum(p['price'] for p in current_cluster) / len(current_cluster)
                
                if abs(pool['price'] - cluster_avg) / cluster_avg < tolerance:
                    current_cluster.append(pool)
                else:
                    # Crear nuevo cluster
                    if len(current_cluster) >= 2:  # Solo si tiene múltiples niveles
                        clustered[direction].append(self.merge_cluster(current_cluster))
                    current_cluster = [pool]
            
            # Agregar último cluster
            if len(current_cluster) >= 2:
                clustered[direction].append(self.merge_cluster(current_cluster))
        
        return clustered
    
    def merge_cluster(self, cluster: List[Dict]) -> Dict:
        """
        Combina múltiples niveles en un pool de liquidez fuerte
        """
        avg_price = sum(p['price'] for p in cluster) / len(cluster)
        total_strength = sum(p['strength'] for p in cluster)
        leverages = list(set(p['leverage'] for p in cluster if p['leverage'] > 0))
        
        return {
            'price': avg_price,
            'strength': total_strength,
            'num_levels': len(cluster),
            'leverages': leverages,
            'type': 'LIQUIDITY_CLUSTER',
            'distance_pct': cluster[0]['distance_pct'],  # Usar el primero
            'components': cluster
        }
    
    def calculate_liquidity_heatmap(self, pools: Dict, current_price: float) -> List[Dict]:
        """
        Crea un mapa de calor de liquidez
        """
        heatmap = []
        
        # Combinar todos los pools
        all_pools = pools['above_price'] + pools['below_price']
        
        for pool in all_pools:
            distance = abs(pool['price'] - current_price) / current_price
            
            # Calcular importancia (más cerca y más fuerte = más importante)
            importance = pool['strength'] / (1 + distance * 10)
            
            heatmap.append({
                'price': pool['price'],
                'strength': pool['strength'],
                'importance': importance,
                'distance_pct': pool['distance_pct'],
                'type': pool['type'],
                'direction': 'ABOVE' if pool['price'] > current_price else 'BELOW'
            })
        
        # Ordenar por importancia
        heatmap.sort(key=lambda x: x['importance'], reverse=True)
        
        return heatmap[:20]  # Top 20 niveles
    
    def suggest_entry_exit(self, liquidity_data: Dict, signal_type: str) -> Dict:
        """
        Sugiere niveles de entrada y salida basados en pools de liquidez
        """
        current_price = liquidity_data['current_price']
        suggestions = {
            'entries': [],
            'stop_losses': [],
            'take_profits': [],
            'warnings': []
        }
        
        if signal_type == 'LONG':
            # Para LONG: Evitar stops donde hay pools de liquidación de longs
            below_pools = liquidity_data['pools']['below_price']
            above_pools = liquidity_data['pools']['above_price']
            
            # Stop Loss: Debajo del pool de liquidez más cercano
            if below_pools:
                nearest_pool = min(below_pools, key=lambda x: abs(x['price'] - current_price))
                suggested_sl = nearest_pool['price'] * 0.995  # 0.5% debajo del pool
                
                suggestions['stop_losses'].append({
                    'price': suggested_sl,
                    'reason': f"Debajo del pool de liquidez en ${nearest_pool['price']:.2f}",
                    'strength': 'HIGH'
                })
                
                if nearest_pool['strength'] > 10:
                    suggestions['warnings'].append(
                        f"⚠️ Pool de liquidez fuerte en ${nearest_pool['price']:.2f} - Posible barrido"
                    )
            
            # Take Profit: Justo antes de pools de liquidación de shorts
            if above_pools:
                for pool in above_pools[:3]:  # Top 3 pools arriba
                    suggested_tp = pool['price'] * 0.995  # Justo antes del pool
                    
                    suggestions['take_profits'].append({
                        'price': suggested_tp,
                        'reason': f"Antes del pool de shorts en ${pool['price']:.2f}",
                        'strength': 'MEDIUM' if pool['strength'] > 5 else 'LOW'
                    })
        
        else:  # SHORT
            # Para SHORT: Inverso
            below_pools = liquidity_data['pools']['below_price']
            above_pools = liquidity_data['pools']['above_price']
            
            # Stop Loss: Arriba del pool de liquidez más cercano
            if above_pools:
                nearest_pool = min(above_pools, key=lambda x: abs(x['price'] - current_price))
                suggested_sl = nearest_pool['price'] * 1.005  # 0.5% arriba del pool
                
                suggestions['stop_losses'].append({
                    'price': suggested_sl,
                    'reason': f"Arriba del pool de liquidez en ${nearest_pool['price']:.2f}",
                    'strength': 'HIGH'
                })
            
            # Take Profit: Justo antes de pools de liquidación de longs
            if below_pools:
                for pool in below_pools[:3]:
                    suggested_tp = pool['price'] * 1.005  # Justo después del pool
                    
                    suggestions['take_profits'].append({
                        'price': suggested_tp,
                        'reason': f"Después del pool de longs en ${pool['price']:.2f}",
                        'strength': 'MEDIUM' if pool['strength'] > 5 else 'LOW'
                    })
        
        # Entrada sugerida: Después de barrido de liquidez
        volume_nodes = liquidity_data.get('volume_nodes', [])
        if volume_nodes:
            nearest_node = min(volume_nodes, key=lambda x: abs(x['price'] - current_price))
            
            suggestions['entries'].append({
                'price': nearest_node['price'],
                'reason': "Nodo de alto volumen - Zona de interés institucional",
                'strength': 'HIGH' if nearest_node['normalized'] > 0.8 else 'MEDIUM'
            })
        
        return suggestions
    
    def analyze_liquidity_risk(self, df: pd.DataFrame, entry: float, stop_loss: float, 
                               take_profit: float, direction: str) -> Dict:
        """
        Analiza el riesgo de una operación basado en pools de liquidez
        """
        current_price = df['Close'].iloc[-1]
        liquidity_data = self.detect_liquidity_pools(df, current_price)
        
        risk_analysis = {
            'risk_score': 0,  # 0-10, menor es mejor
            'warnings': [],
            'opportunities': [],
            'adjustments': []
        }
        
        # Analizar Stop Loss
        sl_distance = abs(stop_loss - entry) / entry
        
        for pool in liquidity_data['pools']['below_price' if direction == 'LONG' else 'above_price']:
            pool_distance = abs(pool['price'] - stop_loss) / stop_loss
            
            if pool_distance < 0.01:  # Stop muy cerca de pool (1%)
                risk_analysis['risk_score'] += 3
                risk_analysis['warnings'].append(
                    f"⚠️ Stop Loss muy cerca de pool de liquidez en ${pool['price']:.2f}"
                )
                
                # Sugerir ajuste
                if direction == 'LONG':
                    new_sl = pool['price'] * 0.99
                    risk_analysis['adjustments'].append(
                        f"Mover SL a ${new_sl:.2f} (debajo del pool)"
                    )
                else:
                    new_sl = pool['price'] * 1.01
                    risk_analysis['adjustments'].append(
                        f"Mover SL a ${new_sl:.2f} (arriba del pool)"
                    )
        
        # Analizar Take Profit
        for pool in liquidity_data['pools']['above_price' if direction == 'LONG' else 'below_price']:
            pool_distance = abs(pool['price'] - take_profit) / take_profit
            
            if pool_distance < 0.02:  # TP cerca de pool
                if pool['strength'] > 10:
                    risk_analysis['opportunities'].append(
                        f"✅ TP bien ubicado antes de pool fuerte en ${pool['price']:.2f}"
                    )
                else:
                    risk_analysis['warnings'].append(
                        f"⚠️ Pool débil en ${pool['price']:.2f} - Posible continuación"
                    )
        
        # Calcular score final
        risk_analysis['risk_score'] = min(10, risk_analysis['risk_score'])
        
        # Clasificación del riesgo
        if risk_analysis['risk_score'] <= 3:
            risk_analysis['classification'] = 'BAJO RIESGO'
        elif risk_analysis['risk_score'] <= 6:
            risk_analysis['classification'] = 'RIESGO MEDIO'
        else:
            risk_analysis['classification'] = 'ALTO RIESGO'
        
        return risk_analysis

def format_liquidity_report(ticker: str, liquidity_data: Dict) -> str:
    """Formatea un reporte de liquidez para mostrar"""
    
    report = f"""
╔════════════════════════════════════════════════════════════════╗
║                 💧 ANÁLISIS DE POOLS DE LIQUIDEZ                ║
║                         {ticker}                                 ║
╚════════════════════════════════════════════════════════════════╝

📊 **PRECIO ACTUAL:** ${liquidity_data['current_price']:.2f}

🔥 **POOLS DE LIQUIDACIÓN MÁS IMPORTANTES:**
{'='*60}
"""
    
    # Top 5 pools por importancia
    top_pools = liquidity_data['heatmap'][:5]
    
    for i, pool in enumerate(top_pools, 1):
        direction = "↑" if pool['direction'] == 'ABOVE' else "↓"
        emoji = "🔴" if 'SHORT' in pool['type'] else "🟢" if 'LONG' in pool['type'] else "⚪"
        
        report += f"""
{i}. {emoji} ${pool['price']:.2f} ({pool['distance_pct']:+.2f}%) {direction}
   Fuerza: {'█' * int(pool['strength'])} {pool['strength']:.1f}
   Tipo: {pool['type']}
"""
    
    # Nodos de volumen
    report += f"""
📈 **ZONAS DE ALTO VOLUMEN (Entradas Populares):**
{'='*60}
"""
    
    for node in liquidity_data['volume_nodes'][:3]:
        report += f"• ${node['price']:.2f} - Volumen: {'█' * int(node['normalized'] * 10)}\n"
    
    # Recomendaciones
    report += f"""
💡 **ESTRATEGIA RECOMENDADA:**
{'='*60}

**Para LONG:**
• Evitar SL cerca de: ${min([p['price'] for p in liquidity_data['pools']['below_price']], default=0):.2f}
• TP ideal antes de: ${min([p['price'] for p in liquidity_data['pools']['above_price']], default=0):.2f}

**Para SHORT:**
• Evitar SL cerca de: ${max([p['price'] for p in liquidity_data['pools']['above_price']], default=0):.2f}
• TP ideal después de: ${max([p['price'] for p in liquidity_data['pools']['below_price']], default=0):.2f}

⚠️ **ADVERTENCIAS:**
• Los pools de liquidez atraen el precio como imanes
• El precio suele "barrer" estos niveles antes de revertir
• Usar stops con buffer de 0.5-1% desde los pools
"""
    
    return report

def demo_liquidity_analysis():
    """Demo del análisis de liquidez"""
    
    print("🔍 Analizando pools de liquidez para BTC-USD...")
    
    # Obtener datos
    ticker = 'BTC-USD'
    btc = yf.Ticker(ticker)
    df = btc.history(period='1mo', interval='1h')
    
    # Detectar pools
    detector = LiquidityPoolDetector()
    liquidity_data = detector.detect_liquidity_pools(df, df['Close'].iloc[-1])
    
    # Mostrar reporte
    print(format_liquidity_report(ticker, liquidity_data))
    
    # Ejemplo de análisis de trade
    print("\n" + "="*60)
    print("📋 ANÁLISIS DE TRADE EJEMPLO:")
    print("="*60)
    
    current_price = df['Close'].iloc[-1]
    entry = current_price
    stop_loss = current_price * 0.98  # -2%
    take_profit = current_price * 1.05  # +5%
    
    risk = detector.analyze_liquidity_risk(df, entry, stop_loss, take_profit, 'LONG')
    
    print(f"""
Trade Propuesto:
• Entrada: ${entry:.2f}
• Stop Loss: ${stop_loss:.2f}
• Take Profit: ${take_profit:.2f}
• Dirección: LONG

Análisis de Riesgo:
• Score: {risk['risk_score']}/10
• Clasificación: {risk['classification']}
""")
    
    if risk['warnings']:
        print("⚠️ Advertencias:")
        for warning in risk['warnings']:
            print(f"  {warning}")
    
    if risk['opportunities']:
        print("✅ Oportunidades:")
        for opp in risk['opportunities']:
            print(f"  {opp}")
    
    if risk['adjustments']:
        print("🔧 Ajustes Sugeridos:")
        for adj in risk['adjustments']:
            print(f"  {adj}")
    
    # Guardar datos
    with open('liquidity_analysis.json', 'w') as f:
        json.dump(liquidity_data, f, indent=2, default=str)
    
    print("\n💾 Análisis guardado en liquidity_analysis.json")

if __name__ == "__main__":
    demo_liquidity_analysis()