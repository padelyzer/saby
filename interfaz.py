# Importar librerías
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from datetime import datetime
from motor_trading import (
    obtener_datos, 
    calcular_indicadores, 
    calcular_score, 
    calcular_semaforo_mercado, 
    obtener_top_movers_binance,
    ejecutar_simulacion,
    analizar_resultados
)

def estilo_binance():
    """Aplica estilos CSS similares a Binance"""
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
        background-color: #0B0E11;
    }
    
    .stApp {
        background-color: #0B0E11;
        color: #EAECEF;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1E2329 0%, #2B3139 100%);
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #2B3139;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    .price-up {
        color: #0ECB81;
        font-weight: bold;
    }
    
    .price-down {
        color: #F6465D;
        font-weight: bold;
    }
    
    .binance-header {
        background: linear-gradient(135deg, #F0B90B 0%, #F8D12F 100%);
        color: #000;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .market-status {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px;
        border-radius: 6px;
        margin: 10px 0;
        font-weight: bold;
        text-align: center;
    }
    
    .status-green {
        background-color: #0ECB81;
        color: #000;
    }
    
    .status-yellow {
        background-color: #F0B90B;
        color: #000;
    }
    
    .status-red {
        background-color: #F6465D;
        color: #FFF;
    }
    
    .crypto-table {
        background-color: #1E2329;
        border-radius: 8px;
        padding: 20px;
        border: 1px solid #2B3139;
    }
    
    .stDataFrame {
        background-color: #1E2329;
    }
    
    div[data-testid="metric-container"] {
        background-color: #1E2329;
        border: 1px solid #2B3139;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    .sidebar .sidebar-content {
        background-color: #1E2329;
    }
    
    h1, h2, h3 {
        color: #EAECEF;
    }
    
    .stSelectbox label {
        color: #EAECEF;
    }
    
    .stButton > button {
        background-color: #F0B90B;
        color: #000;
        border: none;
        border-radius: 4px;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #F8D12F;
        color: #000;
    }
    </style>
    """, unsafe_allow_html=True)

def mostrar_analisis_vivo():
    """Muestra la sección de análisis en vivo."""
    # --- SECCIÓN SEMÁFORO DE MERCADO ---
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🚦 Estado del Mercado (S&P 500)")
        estado_mercado = calcular_semaforo_mercado()
        
        if estado_mercado == 'VERDE':
            st.markdown("""
            <div class="market-status status-green">
                🟢 RISK-ON: Entorno favorable para compras
            </div>
            """, unsafe_allow_html=True)
        elif estado_mercado == 'AMARILLO':
            st.markdown("""
            <div class="market-status status-yellow">
                🟡 PRECAUCIÓN: Mercado en zona de indecisión
            </div>
            """, unsafe_allow_html=True)
        elif estado_mercado == 'ROJO':
            st.markdown("""
            <div class="market-status status-red">
                🔴 RISK-OFF: Entorno desfavorable para compras
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("❓ Estado del mercado desconocido")

    st.markdown("---")

    # --- SECCIÓN DE ANÁLISIS DE ACTIVOS ---
    st.markdown("### 📈 Top Movers - Análisis de Señales")
    
    # Sidebar con controles
    with st.sidebar:
        st.markdown("### ⚙️ Configuración Análisis")
        num_assets = st.slider("📊 Número de activos", min_value=5, max_value=50, value=20)
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False)
        
        if st.button("🔄 Actualizar Datos"):
            st.rerun()
    
    # Obtener datos con fallback
    with st.spinner("🔄 Obteniendo datos de mercado..."):
        activos = obtener_top_movers_binance(limit=num_assets)
        
        # Fallback en caso de que no funcione el scraping
        if not activos:
            st.warning("⚠️ No se pudieron obtener datos de Binance. Usando activos predeterminados.")
            activos = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'XRP-USD', 
                      'SOL-USD', 'DOT-USD', 'DOGE-USD', 'AVAX-USD', 'SHIB-USD',
                      'MATIC-USD', 'LTC-USD', 'LINK-USD', 'UNI-USD', 'ATOM-USD']

    # Contenedor para la tabla
    placeholder = st.empty()
    
    with placeholder.container():
        resultados = []
        
        # Crear columnas para métricas rápidas
        metric_cols = st.columns(4)
        
        progress_text = st.empty()
        barra_progreso = st.progress(0)
        
        total_assets = min(len(activos), num_assets)
        
        for i, ticker in enumerate(activos[:num_assets]):
            progress_text.text(f"🔍 Analizando {ticker}... ({i+1}/{total_assets})")
            
            df = obtener_datos(ticker)
            if df is not None and len(df) > 0:
                df = calcular_indicadores(df)
                score, etapa, direccion = calcular_score(df)
                
                # Calcular cambio 24h
                if len(df) >= 2:
                    close_actual = df['Close'].iloc[-1]
                    close_anterior = df['Close'].iloc[-2]
                    # Convertir a float si es necesario
                    if isinstance(close_actual, pd.Series):
                        close_actual = close_actual.iloc[0]
                    if isinstance(close_anterior, pd.Series):
                        close_anterior = close_anterior.iloc[0]
                    cambio_24h = ((close_actual / close_anterior) - 1) * 100
                else:
                    cambio_24h = 0
                
                # Formatear precio - asegurar que es un float
                precio_actual = df['Close'].iloc[-1]
                if isinstance(precio_actual, pd.Series):
                    precio_actual = precio_actual.iloc[0]
                precio_actual = float(precio_actual)
                
                # Obtener RSI de manera segura
                rsi_val = df['RSI'].iloc[-1]
                if isinstance(rsi_val, pd.Series):
                    rsi_val = rsi_val.iloc[0]
                rsi_str = f"{float(rsi_val):.1f}" if not pd.isna(rsi_val) else "N/A"
                
                # Obtener volumen de manera segura
                vol_val = df['Volume'].iloc[-1]
                if isinstance(vol_val, pd.Series):
                    vol_val = vol_val.iloc[0]
                vol_str = f"{float(vol_val):,.0f}" if not pd.isna(vol_val) else "N/A"
                
                resultados.append({
                    'Símbolo': ticker.replace('-USD', ''),
                    'Precio': f"${precio_actual:.4f}",
                    'Cambio 24h': f"{cambio_24h:+.2f}%",
                    'Dirección': direccion,
                    'Score': score,
                    'RSI': rsi_str,
                    'Etapa': etapa,
                    'Volumen': vol_str
                })
            
            barra_progreso.progress((i + 1) / total_assets)
        
        progress_text.empty()
        barra_progreso.empty()

        if resultados:
            df_resultados = pd.DataFrame(resultados)
            
            # Mostrar métricas destacadas
            with metric_cols[0]:
                best_score = df_resultados['Score'].max()
                st.metric("🏆 Mejor Score", f"{best_score:.1f}")
            
            with metric_cols[1]:
                avg_score = df_resultados['Score'].mean()
                st.metric("📊 Score Promedio", f"{avg_score:.1f}")
            
            with metric_cols[2]:
                oportunidades = len(df_resultados[df_resultados['Score'] >= 2])
                st.metric("🎯 Oportunidades", oportunidades)
            
            with metric_cols[3]:
                total_analizado = len(df_resultados)
                st.metric("📈 Total Analizado", total_analizado)

            # Tabla estilizada
            st.markdown("### 📋 Tabla de Análisis")
            
            def aplicar_estilos(df):
                def colorear_cambio(val):
                    if '+' in str(val):
                        return 'color: #0ECB81; font-weight: bold'
                    elif '-' in str(val):
                        return 'color: #F6465D; font-weight: bold'
                    return ''
                
                def colorear_score(val):
                    try:
                        val_num = float(val)
                        if val_num >= 3:
                            return 'background-color: #0ECB81; color: white; font-weight: bold'
                        elif val_num >= 1.5:
                            return 'background-color: #4CAF50; color: white'
                        elif val_num <= -1:
                            return 'background-color: #F6465D; color: white'
                        else:
                            return 'background-color: #2B3139; color: #EAECEF'
                    except:
                        return ''
                
                def colorear_etapa(val):
                    if 'Temprano' in str(val):
                        return 'background-color: #0ECB81; color: white'
                    elif 'Tardía' in str(val):
                        return 'background-color: #F6465D; color: white'
                    elif 'Madura' in str(val):
                        return 'background-color: #F0B90B; color: black'
                    else:
                        return 'background-color: #2B3139; color: #EAECEF'
                
                return df.style.applymap(colorear_cambio, subset=['Cambio 24h'])\
                             .applymap(colorear_score, subset=['Score'])\
                             .applymap(colorear_etapa, subset=['Etapa'])
            
            # Ordenar por score descendente
            df_resultados = df_resultados.sort_values('Score', ascending=False)
            
            st.dataframe(
                aplicar_estilos(df_resultados),
                use_container_width=True,
                height=600
            )
            
            # Gráfico de distribución de scores
            col1, col2 = st.columns(2)
            
            with col1:
                fig_hist = px.histogram(
                    df_resultados, 
                    x='Score', 
                    nbins=20,
                    title="📊 Distribución de Scores",
                    color_discrete_sequence=['#F0B90B']
                )
                fig_hist.update_layout(
                    plot_bgcolor='#1E2329',
                    paper_bgcolor='#1E2329',
                    font_color='#EAECEF'
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Top 5 mejores oportunidades
                top_5 = df_resultados.head(5)
                fig_bar = px.bar(
                    top_5,
                    x='Símbolo',
                    y='Score',
                    title="🎯 Top 5 Oportunidades",
                    color='Score',
                    color_continuous_scale=['#F6465D', '#F0B90B', '#0ECB81']
                )
                fig_bar.update_layout(
                    plot_bgcolor='#1E2329',
                    paper_bgcolor='#1E2329',
                    font_color='#EAECEF'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        else:
            st.error("❌ No se pudieron obtener datos para ningún activo.")

def mostrar_paper_trading():
    """Muestra la sección de paper trading y backtesting."""
    st.header("🔬 Valida y Optimiza tu Estrategia")
    st.markdown("Ejecuta simulaciones de trading para evaluar el rendimiento de la estrategia")
    
    # Controles de simulación
    col1, col2, col3 = st.columns(3)
    
    with col1:
        capital_inicial = st.number_input(
            "💰 Capital Inicial (USD)", 
            min_value=1000, 
            max_value=1000000, 
            value=10000, 
            step=1000
        )
    
    with col2:
        dias_simulacion = st.slider(
            "📅 Días de Simulación", 
            min_value=30, 
            max_value=365, 
            value=60
        )
    
    with col3:
        apalancamiento = st.select_slider(
            "⚡ Apalancamiento",
            options=[1, 2, 3, 5, 10],
            value=3,
            help="💡 3x recomendado para reducir drawdown máximo"
        )
    
    # Sidebar con configuración de paper trading
    with st.sidebar:
        st.markdown("### 🔬 Configuración Paper Trading")
        st.markdown(f"**Capital:** ${capital_inicial:,}")
        st.markdown(f"**Período:** {dias_simulacion} días")
        st.markdown(f"**Apalancamiento:** {apalancamiento}x")
        st.markdown("**Tamaño posición:** 10% del capital")
        if apalancamiento > 1:
            st.markdown("**Stop Loss:** 1%")
            st.markdown("**Take Profit:** 2%")
        else:
            st.markdown("**Stop Loss:** 3%")
            st.markdown("**Take Profit:** 7%")
        st.markdown("**Tipo:** LONG y SHORT")
    
    # Botón de ejecución
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Iniciar Simulación de Paper Trading", type="primary", use_container_width=True):
            
            with st.spinner("🔄 Ejecutando simulación... Esto puede tardar varios minutos."):
                try:
                    # Ejecutar simulación con apalancamiento
                    equity_curve = ejecutar_simulacion(capital_inicial, dias_simulacion, apalancamiento)
                    
                    # Analizar resultados
                    resultados = analizar_resultados()
                    
                    if resultados and resultados['total_trades'] > 0:
                        st.success("✅ Simulación completada exitosamente!")
                        
                        # Mostrar métricas principales
                        st.markdown("### 📊 Métricas de Rendimiento")
                        
                        # Usar 3 columnas con espaciado para mejor visualización
                        metric_cols = st.columns([1, 1, 1], gap="large")
                        
                        with metric_cols[0]:
                            # Profit Factor con formato mejorado
                            pf_value = resultados['profit_factor']
                            pf_emoji = "✅" if pf_value > 1.5 else "⚠️" if pf_value > 1 else "🔴"
                            
                            st.metric(
                                "📈 Profit Factor", 
                                f"{pf_value:.2f}",
                                delta=pf_emoji,
                                help="Ganancia/Pérdida. >1.5 excelente"
                            )
                            
                            # Total de trades
                            st.metric(
                                "📊 Total Trades", 
                                f"{resultados['total_trades']}",
                                delta="operaciones ejecutadas"
                            )
                        
                        with metric_cols[1]:
                            # Win Rate con formato claro
                            wr = resultados['win_rate']
                            wr_delta = f"+{wr - 50:.1f}%" if wr >= 50 else f"{wr - 50:.1f}%"
                            
                            st.metric(
                                "🎯 Win Rate", 
                                f"{wr:.1f}%",
                                delta=wr_delta,
                                help="Porcentaje de trades ganadores"
                            )
                            
                            # P&L Neto
                            pnl = resultados['ganancia_neta_usd']
                            pnl_pct = resultados['ganancia_neta_porc']
                            
                            st.metric(
                                "💰 P&L Neto", 
                                f"${pnl:,.0f}",
                                delta=f"{pnl_pct:+.1f}%"
                            )
                        
                        with metric_cols[2]:
                            # Rendimiento total con formato claro
                            capital_final = capital_inicial + resultados['ganancia_neta_usd']
                            rendimiento_total = ((capital_final / capital_inicial) - 1) * 100
                            
                            st.metric(
                                "📈 Rendimiento", 
                                f"{rendimiento_total:+.1f}%",
                                delta=f"Final: ${capital_final:,.0f}",
                                help="Rendimiento total del período"
                            )
                            
                            # Calcular drawdown máximo si hay equity curve
                            if 'equity_curve' in resultados and resultados['equity_curve']:
                                capitals = [e['Capital'] for e in resultados['equity_curve']]
                                if capitals:
                                    peak = capitals[0]
                                    max_dd = 0
                                    for capital in capitals:
                                        if capital > peak:
                                            peak = capital
                                        dd = ((capital - peak) / peak) * 100
                                        if dd < max_dd:
                                            max_dd = dd
                                    
                                    st.metric(
                                        "📉 Max Drawdown",
                                        f"{max_dd:.1f}%",
                                        delta="riesgo máximo"
                                    )
                        
                        # Evaluación de la estrategia
                        st.markdown("### 🎯 Evaluación de la Estrategia")
                        
                        if resultados['profit_factor'] >= 1.5 and resultados['win_rate'] >= 40:
                            st.success("🏆 **ESTRATEGIA SÓLIDA** - Profit Factor alto y Win Rate aceptable")
                        elif resultados['profit_factor'] >= 1.2:
                            st.warning("⚠️ **ESTRATEGIA PROMETEDORA** - Considera optimizar para mejorar el Win Rate")
                        elif resultados['profit_factor'] >= 1.0:
                            st.info("📊 **ESTRATEGIA MARGINAL** - Necesita optimización antes de usar en real")
                        else:
                            st.error("❌ **ESTRATEGIA NO RENTABLE** - Requiere ajustes significativos")
                        
                        # Gráfico de Equity Curve
                        if equity_curve:
                            st.markdown("### 📈 Curva de Capital (Equity Curve)")
                            
                            df_equity = pd.DataFrame(equity_curve)
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=df_equity['Fecha'],
                                y=df_equity['Capital'],
                                mode='lines',
                                name='Capital',
                                line=dict(color='#F0B90B', width=3),
                                fill='tonexty'
                            ))
                            
                            # Línea de capital inicial
                            fig.add_hline(
                                y=capital_inicial, 
                                line_dash="dash", 
                                line_color="#848E9C",
                                annotation_text=f"Capital Inicial: ${capital_inicial:,}"
                            )
                            
                            fig.update_layout(
                                title="Evolución del Capital Durante la Simulación",
                                xaxis_title="Fecha",
                                yaxis_title="Capital (USD)",
                                plot_bgcolor='#1E2329',
                                paper_bgcolor='#1E2329',
                                font_color='#EAECEF',
                                height=500
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Historial de trades
                        st.markdown("### 📋 Historial de Operaciones")
                        
                        if os.path.exists('paper_trades.csv'):
                            df_trades = pd.read_csv('paper_trades.csv')
                            
                            # Formatear columnas numéricas
                            if 'Precio' in df_trades.columns:
                                df_trades['Precio'] = df_trades['Precio'].apply(lambda x: f"${x:.4f}" if pd.notna(x) else "")
                            if 'Resultado_USD' in df_trades.columns:
                                df_trades['Resultado_USD'] = df_trades['Resultado_USD'].apply(
                                    lambda x: f"${x:+.2f}" if pd.notna(x) and x != '' else ""
                                )
                            if 'Resultado_Porc' in df_trades.columns:
                                df_trades['Resultado_Porc'] = df_trades['Resultado_Porc'].apply(
                                    lambda x: f"{x:+.1f}%" if pd.notna(x) and x != '' else ""
                                )
                            
                            # Aplicar estilos a la tabla
                            def colorear_resultado(val):
                                if pd.isna(val) or val == '':
                                    return ''
                                try:
                                    if '+' in str(val):
                                        return 'color: #0ECB81; font-weight: bold'
                                    elif '-' in str(val):
                                        return 'color: #F6465D; font-weight: bold'
                                except:
                                    return ''
                                return ''
                            
                            def colorear_tipo(val):
                                if val == 'Entrada':
                                    return 'background-color: #0ECB81; color: white'
                                elif val == 'Salida':
                                    return 'background-color: #F6465D; color: white'
                                return ''
                            
                            styled_df = df_trades.style.applymap(colorear_resultado, subset=['Resultado_USD', 'Resultado_Porc'])\
                                                      .applymap(colorear_tipo, subset=['Tipo'])
                            
                            st.dataframe(styled_df, use_container_width=True, height=400)
                        
                        # Recomendaciones de optimización
                        st.markdown("### 🔧 Recomendaciones de Optimización")
                        
                        if resultados['profit_factor'] < 1.2:
                            st.markdown("- 📉 **Ajustar Stop Loss:** Considera cambiar de 1.5x ATR a 2.0x ATR")
                            st.markdown("- 📈 **Ajustar Take Profit:** Prueba con 2.5x ATR en lugar de 3.0x ATR")
                        
                        if resultados['win_rate'] < 40:
                            st.markdown("- 🎯 **Filtros más estrictos:** Aumenta el score mínimo de 3 a 3.5 o 4")
                            st.markdown("- 📊 **Añadir filtro de volumen:** Solo entrar si volumen > 2x promedio")
                        
                        if resultados['total_trades'] < 10:
                            st.markdown("- 📅 **Extender período:** Aumenta los días de simulación para más datos")
                            st.markdown("- 🎚️ **Reducir score mínimo:** Prueba con score ≥ 2.5 para más oportunidades")
                    
                    else:
                        st.warning("⚠️ No se encontraron trades en la simulación. Intenta con un período más largo o ajusta los parámetros.")
                
                except Exception as e:
                    st.error(f"❌ Error durante la simulación: {str(e)}")
                    st.info("💡 Intenta con un período más corto o verifica tu conexión a internet.")

def mostrar_live_bot_monitor():
    """Muestra la pestaña de monitoreo del bot en vivo."""
    st.header("🤖 Monitor del Bot de Paper Trading")
    
    # Instrucciones
    st.info("""
    📋 **Instrucciones para usar el Bot:**
    
    1. **Ejecutar el Bot:** Abre una nueva terminal, navega a esta carpeta y ejecuta:
       ```bash
       python live_bot.py
       ```
    
    2. **Monitoreo:** Esta pestaña muestra el estado actual del bot en tiempo real
    
    3. **Detener el Bot:** En la terminal del bot, presiona `Ctrl+C`
    
    ⚠️ **Importante:** El bot debe estar ejecutándose en una terminal separada para que aparezcan datos aquí.
    """)
    
    # Botón de refresco
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refrescar Datos", type="primary", use_container_width=True):
            st.rerun()
    
    # Verificar si existen los archivos del bot
    bot_estado_existe = os.path.exists('bot_estado.json')
    live_trades_existe = os.path.exists('live_paper_trades.csv')
    
    if not bot_estado_existe:
        st.warning("⚠️ El bot no se ha ejecutado aún. Ejecuta `python live_bot.py` en una terminal.")
        return
    
    try:
        # Cargar estado del bot
        with open('bot_estado.json', 'r') as f:
            estado_bot = json.load(f)
        
        balance_actual = estado_bot.get('balance', 0)
        posiciones_abiertas = estado_bot.get('posiciones_abiertas', [])
        ultima_actualizacion = estado_bot.get('ultima_actualizacion', 'Desconocido')
        
        # Calcular métricas
        balance_inicial = 100.0
        ganancia_perdida = balance_actual - balance_inicial
        rendimiento = (ganancia_perdida / balance_inicial) * 100 if balance_inicial > 0 else 0
        
        # Mostrar métricas principales
        st.markdown("### 📊 Estado del Bot en Tiempo Real")
        
        # Última actualización
        try:
            if ultima_actualizacion != 'Desconocido':
                dt_update = datetime.fromisoformat(ultima_actualizacion.replace('Z', '+00:00'))
                tiempo_transcurrido = datetime.now() - dt_update.replace(tzinfo=None)
                minutos_transcurridos = int(tiempo_transcurrido.total_seconds() / 60)
                
                if minutos_transcurridos < 2:
                    status_color = "🟢"
                    status_text = "Activo"
                elif minutos_transcurridos < 10:
                    status_color = "🟡"
                    status_text = "Reciente"
                else:
                    status_color = "🔴"
                    status_text = "Inactivo"
                
                st.markdown(f"**Estado:** {status_color} {status_text} | **Última actualización:** {dt_update.strftime('%H:%M:%S')} ({minutos_transcurridos}m)")
        except:
            st.markdown("**Estado:** ❓ Desconocido")
        
        # Métricas en columnas
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric(
                "💰 Balance Actual",
                f"${balance_actual:.2f}",
                delta=f"${ganancia_perdida:+.2f}"
            )
        
        with metric_cols[1]:
            color = "normal" if rendimiento >= 0 else "inverse"
            st.metric(
                "📈 Rendimiento",
                f"{rendimiento:+.2f}%",
                delta=f"Desde inicio"
            )
        
        with metric_cols[2]:
            st.metric(
                "🎯 Posiciones Abiertas",
                len(posiciones_abiertas)
            )
        
        with metric_cols[3]:
            # Calcular número de trades si existe el archivo
            total_trades = 0
            if live_trades_existe:
                try:
                    df_trades = pd.read_csv('live_paper_trades.csv')
                    salidas = df_trades[df_trades['Tipo'] == 'Salida']
                    total_trades = len(salidas)
                except:
                    pass
            
            st.metric(
                "📊 Trades Completados",
                total_trades
            )
        
        # Mostrar posiciones abiertas
        if posiciones_abiertas:
            st.markdown("### 📋 Posiciones Abiertas")
            
            posiciones_df = []
            for pos in posiciones_abiertas:
                # Calcular P&L no realizado
                try:
                    ticker = pos['ticker']
                    precio_entrada = pos['precio_entrada']
                    
                    # Obtener precio actual
                    df_precio = obtener_datos(ticker, period='5d')
                    if df_precio is not None and len(df_precio) > 0:
                        precio_actual = df_precio['Close'].iloc[-1]
                        tamano_usd = pos['tamano_usd']
                        acciones = tamano_usd / precio_entrada
                        pnl_no_realizado = acciones * (precio_actual - precio_entrada)
                        pnl_porc = ((precio_actual / precio_entrada) - 1) * 100
                    else:
                        precio_actual = precio_entrada
                        pnl_no_realizado = 0
                        pnl_porc = 0
                except:
                    precio_actual = pos['precio_entrada']
                    pnl_no_realizado = 0
                    pnl_porc = 0
                
                posiciones_df.append({
                    'Ticker': pos['ticker'],
                    'Precio Entrada': f"${pos['precio_entrada']:.4f}",
                    'Precio Actual': f"${precio_actual:.4f}",
                    'Stop Loss': f"${pos['stop_loss']:.4f}",
                    'Take Profit': f"${pos['take_profit']:.4f}",
                    'Tamaño': f"${pos['tamano_usd']:.0f}",
                    'Score': f"{pos['score_entrada']:.1f}",
                    'P&L No Realizado': f"${pnl_no_realizado:+.2f}",
                    'P&L %': f"{pnl_porc:+.2f}%"
                })
            
            if posiciones_df:
                df_pos = pd.DataFrame(posiciones_df)
                
                # Aplicar estilos
                def colorear_pnl(val):
                    if '+' in str(val):
                        return 'color: #0ECB81; font-weight: bold'
                    elif '-' in str(val):
                        return 'color: #F6465D; font-weight: bold'
                    return ''
                
                styled_pos = df_pos.style.applymap(colorear_pnl, subset=['P&L No Realizado', 'P&L %'])
                st.dataframe(styled_pos, use_container_width=True)
        
        else:
            st.info("📭 No hay posiciones abiertas actualmente")
        
        # Mostrar historial de trades
        if live_trades_existe:
            st.markdown("### 📈 Historial de Operaciones")
            
            try:
                df_trades = pd.read_csv('live_paper_trades.csv')
                
                if not df_trades.empty:
                    # Mostrar estadísticas rápidas
                    salidas = df_trades[df_trades['Tipo'] == 'Salida']
                    
                    if not salidas.empty:
                        trades_ganadores = len(salidas[salidas['Resultado_USD'] > 0])
                        win_rate = (trades_ganadores / len(salidas)) * 100 if len(salidas) > 0 else 0
                        
                        ganancia_total = salidas['Resultado_USD'].sum()
                        
                        # Métricas de trading
                        trade_cols = st.columns(3)
                        
                        with trade_cols[0]:
                            st.metric("🎯 Win Rate", f"{win_rate:.1f}%")
                        
                        with trade_cols[1]:
                            st.metric("💰 P&L Realizado", f"${ganancia_total:+.2f}")
                        
                        with trade_cols[2]:
                            promedio_trade = ganancia_total / len(salidas) if len(salidas) > 0 else 0
                            st.metric("📊 Promedio por Trade", f"${promedio_trade:+.2f}")
                    
                    # Tabla de trades
                    def colorear_resultado_live(val):
                        if pd.isna(val) or val == '':
                            return ''
                        try:
                            val_num = float(val)
                            if val_num > 0:
                                return 'color: #0ECB81; font-weight: bold'
                            elif val_num < 0:
                                return 'color: #F6465D; font-weight: bold'
                        except:
                            return ''
                        return ''
                    
                    def colorear_tipo_live(val):
                        if val == 'Entrada':
                            return 'background-color: #0ECB81; color: white'
                        elif val == 'Salida':
                            return 'background-color: #F6465D; color: white'
                        return ''
                    
                    # Mostrar solo los últimos 20 trades
                    df_recent = df_trades.tail(20)
                    
                    styled_trades = df_recent.style.applymap(colorear_resultado_live, subset=['Resultado_USD', 'Resultado_Porc'])\
                                                  .applymap(colorear_tipo_live, subset=['Tipo'])
                    
                    st.dataframe(styled_trades, use_container_width=True, height=400)
                    
                    # Gráfico de evolución del balance
                    if len(df_trades) > 1:
                        st.markdown("### 📈 Evolución del Balance")
                        
                        # Filtrar solo entradas y salidas con balance
                        df_balance = df_trades[df_trades['Balance_Post'].notna()].copy()
                        df_balance['Timestamp'] = pd.to_datetime(df_balance['Timestamp'])
                        
                        if len(df_balance) > 0:
                            fig_balance = go.Figure()
                            fig_balance.add_trace(go.Scatter(
                                x=df_balance['Timestamp'],
                                y=df_balance['Balance_Post'],
                                mode='lines+markers',
                                name='Balance',
                                line=dict(color='#F0B90B', width=3),
                                marker=dict(size=6)
                            ))
                            
                            # Línea de balance inicial
                            fig_balance.add_hline(
                                y=balance_inicial, 
                                line_dash="dash", 
                                line_color="#848E9C",
                                annotation_text=f"Balance Inicial: ${balance_inicial:.0f}"
                            )
                            
                            fig_balance.update_layout(
                                title="Evolución del Balance del Bot",
                                xaxis_title="Fecha y Hora",
                                yaxis_title="Balance (USD)",
                                plot_bgcolor='#1E2329',
                                paper_bgcolor='#1E2329',
                                font_color='#EAECEF',
                                height=400
                            )
                            
                            st.plotly_chart(fig_balance, use_container_width=True)
                
                else:
                    st.info("📭 No hay trades registrados aún")
            
            except Exception as e:
                st.error(f"❌ Error leyendo historial de trades: {e}")
        
        else:
            st.info("📄 El archivo de trades no existe aún. El bot generará trades cuando encuentre oportunidades.")
    
    except Exception as e:
        st.error(f"❌ Error leyendo estado del bot: {e}")
    
    # Sidebar con información del bot
    with st.sidebar:
        st.markdown("### 🤖 Configuración del Bot")
        st.markdown("**Balance inicial:** $100.00")
        st.markdown("**Tamaño posición:** $10.00")
        st.markdown("**Filtros entrada:**")
        st.markdown("- Score ≥ 4.5")
        st.markdown("- Mercado = VERDE")
        st.markdown("- Etapa = Inicio Temprano")
        st.markdown("**Stop Loss:** 1.5x ATR")
        st.markdown("**Take Profit:** 3.0x ATR")
        st.markdown("**Frecuencia:** Cada 5 minutos")

def mostrar_dashboard():
    """Construye y muestra el dashboard principal con pestañas."""
    st.set_page_config(
        page_title="Trading Dashboard", 
        layout="wide",
        page_icon="📊",
        initial_sidebar_state="expanded"
    )
    
    # Aplicar estilos de Binance
    estilo_binance()

    # Header principal estilo Binance
    st.markdown("""
    <div class="binance-header">
        <h1>📊 TRADING ANALYSIS DASHBOARD</h1>
        <p>Sistema de análisis educativo para mercados de criptomonedas</p>
    </div>
    """, unsafe_allow_html=True)

    # Crear pestañas principales
    tab1, tab2, tab3 = st.tabs([
        "📈 Análisis en Vivo", 
        "🔬 Paper Trading & Backtesting",
        "🤖 Live Paper Trading Bot"
    ])
    
    with tab1:
        mostrar_analisis_vivo()
    
    with tab2:
        mostrar_paper_trading()
    
    with tab3:
        mostrar_live_bot_monitor()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #848E9C; font-size: 0.8em;'>
        📊 Dashboard de Trading Educativo | Datos proporcionados por Yahoo Finance
    </div>
    """, unsafe_allow_html=True)