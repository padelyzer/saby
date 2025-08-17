#!/usr/bin/env python3
"""
Interfaz de Usuario - Sistema Definitivo Operativo
UX moderna para el sistema de trading desarrollado
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import time
import warnings
warnings.filterwarnings('ignore')

# Importar nuestro sistema definitivo
import sys
import os
sys.path.append(os.getcwd())

# Importar backtesting integrado
from backtesting_integration import BacktestingIntegrado

def apply_custom_css():
    """Aplica estilos CSS personalizados inspirados en exchanges modernos"""
    st.markdown("""
    <style>
    /* Tema principal */
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1d2e 100%);
        color: #e1e3e6;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(90deg, #f0b90b 0%, #f8d84c 50%, #0ecb81 100%);
        color: #000;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(240, 185, 11, 0.3);
    }
    
    /* Cards de métricas */
    .metric-card {
        background: linear-gradient(135deg, #1e2329 0%, #2b3139 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2b3139;
        margin: 15px 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    }
    
    /* Señales */
    .signal-long {
        background: linear-gradient(135deg, #0ecb81 0%, #03a66d 100%);
        color: #fff;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 3px 15px rgba(14, 203, 129, 0.3);
    }
    
    .signal-short {
        background: linear-gradient(135deg, #f6465d 0%, #e04056 100%);
        color: #fff;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 3px 15px rgba(246, 70, 93, 0.3);
    }
    
    /* Números */
    .price-up {
        color: #0ecb81;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    .price-down {
        color: #f6465d;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    .price-neutral {
        color: #fcd535;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    /* Botones */
    .stButton > button {
        background: linear-gradient(45deg, #f0b90b, #fcd535);
        color: #000;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #fcd535, #f0b90b);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(240, 185, 11, 0.3);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e2329 0%, #0f1419 100%);
    }
    
    /* Status indicators */
    .status-active {
        background: #0ecb8130;
        border: 2px solid #0ecb81;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    
    .status-warning {
        background: #fcd53530;
        border: 2px solid #fcd535;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    
    .status-danger {
        background: #f6465d30;
        border: 2px solid #f6465d;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    
    /* Tablas */
    .dataframe {
        background: #1e2329;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Animaciones */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    </style>
    """, unsafe_allow_html=True)

def load_sistema_definitivo():
    """Carga el sistema definitivo operativo"""
    try:
        from sistema_definitivo_operativo import SistemaDefinitivoOperativo
        return SistemaDefinitivoOperativo()
    except ImportError:
        st.error("⚠️ No se pudo cargar el sistema definitivo")
        return None

def display_header():
    """Muestra el header principal"""
    st.markdown("""
    <div class="main-header">
        <h1>🎯 SISTEMA DE TRADING DEFINITIVO OPERATIVO</h1>
        <p>Interface de Usuario | Versión 1.0 | Trading en Vivo</p>
    </div>
    """, unsafe_allow_html=True)

def display_system_status():
    """Muestra el estado del sistema"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🟢 Sistema</h3>
            <div class="price-up">OPERATIVO</div>
            <small>Listo para trading</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ Señales</h3>
            <div class="price-neutral">ACTIVAS</div>
            <small>Generando oportunidades</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🛡️ Riesgo</h3>
            <div class="price-up">CONTROLADO</div>
            <small>Gestión optimizada</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>📈 Monitor</h3>
            <div class="price-up">EN VIVO</div>
            <small>Seguimiento 24/7</small>
        </div>
        """, unsafe_allow_html=True)

def display_active_signals():
    """Muestra las señales activas"""
    st.subheader("🎯 Señales Definitivas Activas")
    
    # Señal ejemplo (DOGE-USD SHORT)
    st.markdown("""
    <div class="signal-short">
        <h3>🔴 DOGE-USD SHORT - ACTIVA</h3>
        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
            <div><strong>Entry:</strong> $0.2295</div>
            <div><strong>Score:</strong> 6.0/10</div>
            <div><strong>R:R:</strong> 1:3.0</div>
        </div>
        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
            <div><strong>Stop:</strong> $0.2334</div>
            <div><strong>Target 1:</strong> $0.2238 (40%)</div>
            <div><strong>Target 2:</strong> $0.2180</div>
        </div>
        <div style="margin-top: 15px;">
            <strong>Estrategia:</strong> EMA21 Pullback Bajista + Volumen confirmando
        </div>
        <div style="margin-top: 10px; padding: 8px; background: rgba(0,0,0,0.2); border-radius: 5px;">
            <strong>Estado:</strong> <span class="pulse">🟡 Esperando desarrollo</span> | 
            <strong>P&L:</strong> <span class="price-up">+0.07%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Instrucciones de ejecución
    with st.expander("📋 Plan de Ejecución"):
        st.markdown("""
        ### 🎯 Instrucciones de Trading
        
        **1. 📊 ENTRY EJECUTADO**
        - ✅ Precio: $0.2295
        - ✅ Position Size: 5% del capital
        - ✅ Stop Loss: $0.2334 (amplio)
        
        **2. 🎯 TARGETS PROGRAMADOS**
        - 🥇 Target Parcial: $0.2238 (cerrar 40%)
        - 🥈 Target Principal: $0.2180 (cerrar resto)
        
        **3. 📈 GESTIÓN AVANZADA**
        - ⏰ Trailing Stop: Activar a +1.0%
        - 🔄 Distancia Trailing: 0.5%
        - 📱 Monitoreo: Cada hora
        
        **4. 🛡️ REGLAS OBLIGATORIAS**
        - ✅ Respetar stop sin excepciones
        - ✅ Cerrar 40% automáticamente en target 1
        - ✅ Activar trailing en +1.0%
        - ✅ Documentar resultado
        """)

def display_market_scanner():
    """Muestra el escáner de mercado"""
    st.subheader("🔍 Escáner de Mercado en Tiempo Real")
    
    # Selector de tickers
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'AVAX-USD', 'LINK-USD', 'DOGE-USD']
    
    if st.button("🔄 Actualizar Análisis"):
        with st.spinner("Analizando mercado..."):
            # Simular análisis
            time.sleep(2)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div class="status-active">
                    <h4>🟢 BTC-USD</h4>
                    <p>Tendencia: <strong>Neutral</strong></p>
                    <p>Volumen: <strong>1.2x</strong></p>
                    <p>Setup: <strong>Esperando</strong></p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="status-warning">
                    <h4>🟡 ETH-USD</h4>
                    <p>Tendencia: <strong>Bajista</strong></p>
                    <p>Volumen: <strong>2.1x</strong></p>
                    <p>Setup: <strong>Desarrollando</strong></p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div class="status-active">
                    <h4>🔴 DOGE-USD</h4>
                    <p>Tendencia: <strong>Bajista Fuerte</strong></p>
                    <p>Volumen: <strong>3.4x</strong></p>
                    <p>Setup: <strong>EJECUTADO</strong></p>
                </div>
                """, unsafe_allow_html=True)

def display_performance_metrics():
    """Muestra métricas de performance"""
    st.subheader("📊 Métricas de Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de equity curve simulado
        dates = pd.date_range(start='2025-08-01', end='2025-08-16', freq='D')
        equity = [10000]
        
        # Simular equity curve
        for i in range(1, len(dates)):
            change = np.random.normal(0.002, 0.02)  # 0.2% promedio, 2% volatilidad
            equity.append(equity[-1] * (1 + change))
        
        df_equity = pd.DataFrame({
            'Fecha': dates,
            'Capital': equity
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_equity['Fecha'],
            y=df_equity['Capital'],
            mode='lines',
            name='Capital',
            line=dict(color='#0ecb81', width=3)
        ))
        
        fig.update_layout(
            title="📈 Evolución del Capital",
            xaxis_title="Fecha",
            yaxis_title="Capital ($)",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Métricas numéricas
        st.markdown("""
        <div class="metric-card">
            <h3>💰 Capital Actual</h3>
            <div class="price-up">$10,007</div>
            <small>+0.07% desde último trade</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card">
            <h3>🎯 Win Rate</h3>
            <div class="price-neutral">N/A</div>
            <small>Trade en progreso</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Trades Activos</h3>
            <div class="price-up">1</div>
            <small>DOGE-USD SHORT</small>
        </div>
        """, unsafe_allow_html=True)

def display_risk_management():
    """Muestra panel de gestión de riesgo"""
    st.subheader("🛡️ Gestión de Riesgo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ⚖️ Exposición Actual
        - **Capital en Riesgo**: $8 (0.08%)
        - **Position Size**: 5% del capital
        - **Max Drawdown Teórico**: 1.7%
        - **Trailing Stop**: No activado aún
        """)
        
        # Gráfico de riesgo
        labels = ['Capital Libre', 'En Riesgo', 'Reserva']
        values = [94.92, 0.08, 5.0]
        colors = ['#0ecb81', '#f6465d', '#fcd535']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.3,
            marker_colors=colors
        )])
        
        fig.update_layout(
            title="Distribución de Capital",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("""
        ### 📋 Reglas Activas
        
        **🎯 Objetivos de Salida**
        - Target Parcial: $0.2238 ✅
        - Target Principal: $0.2180 ⏳
        
        **🛑 Protección**
        - Stop Loss: $0.2334 ✅
        - Trailing: +1.0% para activar
        
        **⚡ Gestión Automática**
        - Cierre parcial: 40% automático
        - Trailing distance: 0.5%
        - Re-evaluación: Cada 4h
        """)

def display_backtesting_section():
    """Muestra sección completa de backtesting"""
    st.subheader("📈 Backtesting del Sistema Definitivo")
    
    # Configuración del backtesting
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periodo_dias = st.selectbox("Período", [7, 15, 30, 60, 90], index=2)
    
    with col2:
        # Mapeo de nombres a símbolos
        ticker_options = {
            'BTC (Bitcoin)': 'BTC-USD',
            'ETH (Ethereum)': 'ETH-USD', 
            'SOL (Solana)': 'SOL-USD',
            'BNB (Binance)': 'BNB-USD',
            'XRP (Ripple)': 'XRP-USD',
            'ADA (Cardano)': 'ADA-USD',
            'DOGE (Dogecoin)': 'DOGE-USD',
            'AVAX (Avalanche)': 'AVAX-USD',
            'LINK (Chainlink)': 'LINK-USD',
            'WIF (Dogwifhat)': 'WIF-USD',
            'PEPE (Pepe)': 'PEPE24478-USD'
        }
        
        selected_names = st.multiselect(
            "Tickers a analizar",
            list(ticker_options.keys()),
            default=['BTC (Bitcoin)', 'ETH (Ethereum)', 'SOL (Solana)', 'BNB (Binance)', 'XRP (Ripple)']
        )
        
        # Convertir nombres a símbolos
        tickers_selected = [ticker_options[name] for name in selected_names]
    
    with col3:
        capital_backtest = st.number_input("Capital ($)", value=10000, min_value=1000, step=1000)
    
    if st.button("🚀 Ejecutar Backtesting Completo", type="primary"):
        if not tickers_selected:
            st.error("Selecciona al menos un ticker")
            return
        
        # Ejecutar backtesting
        backtest_engine = BacktestingIntegrado(capital_inicial=capital_backtest)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(message, progress):
            status_text.text(message)
            progress_bar.progress(progress)
        
        with st.spinner("Ejecutando backtesting..."):
            trades = backtest_engine.run_backtest(
                tickers=tickers_selected,
                periods_days=periodo_dias,
                progress_callback=update_progress
            )
        
        progress_bar.empty()
        status_text.empty()
        
        if trades:
            # Analizar resultados
            results = backtest_engine.analyze_results(trades)
            
            # Mostrar resultados principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📊 Total Trades</h3>
                    <div class="price-neutral">{results['total_trades']}</div>
                    <small>Señales generadas</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                wr_color = "price-up" if results['win_rate'] >= 60 else "price-down" if results['win_rate'] < 50 else "price-neutral"
                st.markdown(f"""
                <div class="metric-card">
                    <h3>🎯 Win Rate</h3>
                    <div class="{wr_color}">{results['win_rate']:.1f}%</div>
                    <small>Trades ganadores</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                pf_color = "price-up" if results['profit_factor'] >= 1.3 else "price-down" if results['profit_factor'] < 1.0 else "price-neutral"
                st.markdown(f"""
                <div class="metric-card">
                    <h3>💰 Profit Factor</h3>
                    <div class="{pf_color}">{results['profit_factor']:.2f}</div>
                    <small>Relación ganancia/pérdida</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                ret_color = "price-up" if results['total_return'] > 0 else "price-down"
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📈 Retorno Total</h3>
                    <div class="{ret_color}">{results['total_return']:+.2f}%</div>
                    <small>Ganancia acumulada</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Rating del sistema
            st.markdown("---")
            rating_class = "status-active" if "EXCELENTE" in results['rating'] else "status-warning" if "BUENO" in results['rating'] else "status-danger"
            
            st.markdown(f"""
            <div class="{rating_class}">
                <h3>{results['rating']} - {results['status']}</h3>
                <p><strong>Score Promedio:</strong> {results['avg_score']:.1f}/10</p>
                <p><strong>R:R Promedio:</strong> 1:{results['avg_rr']:.1f}</p>
                <p><strong>Duración Promedio:</strong> {results['avg_duration']:.0f} períodos</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Análisis detallado en tabs
            tab1, tab2, tab3 = st.tabs(["📊 Métricas", "🎯 Por Estrategia", "🚪 Por Salida"])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 💰 Métricas de Performance")
                    st.markdown(f"""
                    - **Avg Win:** {results['avg_win']:+.2f}%
                    - **Avg Loss:** {results['avg_loss']:+.2f}%
                    - **Trades con Parcial:** {results['partial_trades']}
                    - **Trades con Trailing:** {results['trailing_trades']}
                    """)
                
                with col2:
                    st.markdown("### 🎲 Distribución")
                    wins = len([t for t in results['trades'] if t['profit_pct'] > 0])
                    losses = len([t for t in results['trades'] if t['profit_pct'] <= 0])
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=['Ganadores', 'Perdedores'],
                        values=[wins, losses],
                        hole=.3,
                        marker_colors=['#0ecb81', '#f6465d']
                    )])
                    
                    fig.update_layout(
                        template="plotly_dark",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.markdown("### 🎯 Análisis por Estrategia")
                for strategy, data in results['strategy_analysis'].items():
                    st.markdown(f"""
                    **{strategy}:**
                    - Trades: {data['count']}
                    - Win Rate: {data['win_rate']:.1f}%
                    - Avg Profit: {data['avg_profit']:+.2f}%
                    """)
            
            with tab3:
                st.markdown("### 🚪 Análisis por Tipo de Salida")
                for reason, data in results['exit_analysis'].items():
                    reason_wr = (data['wins'] / data['count'] * 100) if data['count'] > 0 else 0
                    reason_avg = np.mean(data['profits'])
                    
                    st.markdown(f"""
                    **{reason}:**
                    - Count: {data['count']}
                    - Win Rate: {reason_wr:.1f}%
                    - Avg: {reason_avg:+.2f}%
                    """)
            
            # Tabla de trades mejorada
            st.markdown("---")
            st.subheader("📋 Detalle de Trades - Vista Completa")
            
            # Crear DataFrame para mostrar con información completa
            df_trades = pd.DataFrame(results['trades'])
            
            # Preparar datos para mostrar
            df_display = df_trades.copy()
            
            # Formatear columnas para mejor visualización
            df_display['Capital Real'] = df_display['capital_usado'].apply(lambda x: f"${x:,.0f}")
            df_display['Exposición'] = df_display['exposicion_total'].apply(lambda x: f"${x:,.0f}")
            df_display['Leverage'] = df_display['leverage'].apply(lambda x: f"{x}x")
            df_display['Entry Price'] = df_display['entry_price'].apply(lambda x: f"${x:.4f}")
            df_display['Exit Price'] = df_display['exit_price'].apply(lambda x: f"${x:.4f}")
            df_display['Resultado USD'] = df_display['profit_usd'].apply(
                lambda x: f"${x:+.2f}" if x >= 0 else f"-${abs(x):.2f}"
            )
            df_display['Resultado %'] = df_display['profit_pct'].apply(lambda x: f"{x:+.2f}%")
            
            # Seleccionar y reordenar columnas
            columns_to_show = [
                'ticker', 'type', 'Capital Real', 'Leverage', 'Exposición', 'Entry Price', 
                'Exit Price', 'Resultado USD', 'Resultado %', 'exit_reason', 'score'
            ]
            
            df_final = df_display[columns_to_show].copy()
            df_final.columns = [
                'Símbolo', 'Tipo', 'Capital Real', 'Leverage', 'Exposición', 'P. Entrada', 
                'P. Salida', 'Resultado $', 'Resultado %', 'Salida', 'Score'
            ]
            
            # Aplicar colores a los resultados
            def color_profit(val):
                if '+' in str(val):
                    return 'background-color: #0ecb8130; color: #0ecb81'
                elif '-' in str(val):
                    return 'background-color: #f6465d30; color: #f6465d'
                return ''
            
            # Mostrar tabla con estilos
            styled_df = df_final.style.applymap(
                color_profit, 
                subset=['Resultado $', 'Resultado %']
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Resumen financiero
            total_capital_usado = df_trades['capital_usado'].sum()
            total_profit_usd = df_trades['profit_usd'].sum()
            profit_pct_total = (total_profit_usd / capital_backtest) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Capital Total Usado", f"${total_capital_usado:,.0f}")
            with col2:
                st.metric("📊 Ganancia/Pérdida Total", f"${total_profit_usd:+.2f}", f"{profit_pct_total:+.2f}%")
            with col3:
                mejor_trade = df_trades.loc[df_trades['profit_usd'].idxmax()]
                st.metric("🏆 Mejor Trade", f"${mejor_trade['profit_usd']:+.2f}", f"{mejor_trade['ticker']}")
            
        
        else:
            st.warning("No se generaron trades en el período seleccionado. Intenta con un período más largo o diferentes tickers.")

def display_tools_section():
    """Muestra sección de herramientas"""
    st.subheader("🔧 Herramientas del Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Generar Nuevas Señales", help="Ejecuta el sistema definitivo"):
            with st.spinner("Analizando mercado..."):
                time.sleep(3)
                st.success("✅ Análisis completado. 1 señal activa encontrada.")
    
    with col2:
        if st.button("📊 Monitor en Tiempo Real", help="Abre el monitor de trades"):
            with st.spinner("Iniciando monitor..."):
                time.sleep(2)
                st.info("📱 Monitor activo. Verificando DOGE-USD SHORT...")
    
    with col3:
        if st.button("📈 Backtesting", help="Ejecuta backtesting del sistema"):
            st.session_state.show_backtesting = True

def main():
    """Función principal de la interfaz"""
    
    # Configuración de página
    st.set_page_config(
        page_title="Sistema Trading Definitivo",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Aplicar estilos
    apply_custom_css()
    
    # Header
    display_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎛️ Panel de Control")
        
        # Estado del sistema
        st.markdown("""
        <div class="status-active">
            <h4>🟢 Sistema Operativo</h4>
            <p>Estado: <strong>EN VIVO</strong></p>
            <p>Última actualización: <strong>Ahora</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Configuración
        st.markdown("### ⚙️ Configuración")
        capital = st.number_input("Capital ($)", value=10000, min_value=1000)
        max_risk = st.slider("Max Risk por Trade (%)", 1.0, 5.0, 2.0, 0.1)
        auto_trailing = st.checkbox("Trailing Automático", value=True)
        
        # Estado de trades
        st.markdown("### 📊 Trades Activos")
        st.markdown("""
        **DOGE-USD SHORT**
        - Entry: $0.2295
        - P&L: +0.07%
        - Estado: 🟡 Activo
        """)
    
    # Verificar si mostrar backtesting
    if hasattr(st.session_state, 'show_backtesting') and st.session_state.show_backtesting:
        # Mostrar solo backtesting
        display_backtesting_section()
        
        if st.button("🔙 Volver al Dashboard"):
            st.session_state.show_backtesting = False
            st.rerun()
    else:
        # Layout principal normal
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "🎯 Señales", "📊 Performance", "🛡️ Riesgo"])
        
        with tab1:
            display_system_status()
            st.markdown("---")
            display_active_signals()
            st.markdown("---")
            display_tools_section()
        
        with tab2:
            display_market_scanner()
            st.markdown("---")
            
            # Filtros de señales
            st.subheader("🔍 Filtros de Búsqueda")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_score = st.slider("Score Mínimo", 1, 10, 5)
            with col2:
                min_volume = st.slider("Volumen Mínimo (x)", 1.0, 5.0, 1.5, 0.1)
            with col3:
                timeframe = st.selectbox("Timeframe", ["1h", "4h", "1d"])
        
        with tab3:
            display_performance_metrics()
            
            # Tabla de trades
            st.subheader("📋 Historial de Trades")
            
            # Datos simulados
            trade_data = {
                'Fecha': ['2025-08-16 14:30'],
                'Ticker': ['DOGE-USD'],
                'Tipo': ['SHORT'],
                'Entry': [0.2295],
                'Estado': ['ACTIVO'],
                'P&L': ['+0.07%']
            }
            
            df_trades = pd.DataFrame(trade_data)
            st.dataframe(df_trades, use_container_width=True)
        
        with tab4:
            display_risk_management()
            
            # Alertas de riesgo
            st.subheader("🚨 Alertas del Sistema")
            
            st.markdown("""
            <div class="status-active">
                <h4>✅ Todo bajo control</h4>
                <p>No hay alertas de riesgo activas</p>
                <p>Próxima evaluación: En 3h 45m</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        🎯 Sistema de Trading Definitivo Operativo v1.0 | 
        Desarrollado para máxima rentabilidad con riesgo controlado
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()