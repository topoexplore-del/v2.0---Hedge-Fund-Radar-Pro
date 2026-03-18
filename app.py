"""
HEDGE FUND RADAR PRO — Market Scanner v2.0
Dashboard en tiempo real con análisis técnico + IA + fundamental.

Deploy: share.streamlit.io
Repo: GitHub → hedge-fund-radar-pro
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# Módulos internos
from data.tickers import MARKET_MAP, get_tickers, parse_custom_tickers, WATCHLIST_CORE
from data.fetcher import fetch_ohlcv_batch, fetch_fundamentals_batch, fetch_finviz_overview
from scanner.technical_model import compute_technical_score, get_last_confirmed
from scanner.ai_model import compute_ai_probability
from scanner.fundamental_model import evaluate_fundamentals, format_market_cap
from scanner.state_machine import compute_state, state_emoji, state_priority

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Hedge Fund Radar Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
    .entry-alert {
        background: linear-gradient(135deg, #1a472a 0%, #0d2818 100%);
        border: 1px solid #28a745;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 4px 0;
        color: #e0e0e0;
    }
    .accum-alert {
        background: linear-gradient(135deg, #3d2e00 0%, #1a1400 100%);
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 4px 0;
        color: #e0e0e0;
    }
    .metric-card {
        background: #1A1D23;
        border-radius: 10px;
        padding: 16px;
        border: 1px solid #2d3139;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 🎯 HEDGE FUND RADAR PRO")
    st.markdown("*Scanner de mercado en tiempo real*")
    st.divider()

    # Selección de mercados
    st.markdown("### 📡 Mercados a escanear")
    selected_markets = st.multiselect(
        "Selecciona índices/sectores",
        options=list(MARKET_MAP.keys()),
        default=["🎯 Watchlist Core (20)"],
    )

    # Tickers personalizados
    custom_input = st.text_input(
        "Tickers adicionales (separados por coma)",
        placeholder="TSLA, AAPL, MSFT...",
    )

    st.divider()

    # Filtros
    st.markdown("### 🔧 Filtros")
    min_score = st.slider("Score técnico mínimo", 0, 100, 0, step=5)
    min_ai = st.slider("AI Probability mínimo %", 0, 95, 0, step=5)
    filter_state = st.multiselect(
        "Mostrar estados",
        ["ENTRY+", "ENTRY", "ACCUM", "WAIT"],
        default=["ENTRY+", "ENTRY", "ACCUM", "WAIT"],
    )

    st.divider()

    # Refresh
    st.markdown("### ⏱️ Actualización")
    auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)
    if st.button("🔄 Actualizar ahora", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    st.caption("⚠️ Solo velas cerradas (anti-repintado)")
    st.caption("📊 Datos: Yahoo Finance + Finviz")

# ─────────────────────────────────────────────────────────────────
# CONSTRUIR LISTA DE TICKERS
# ─────────────────────────────────────────────────────────────────

ticker_list = get_tickers(selected_markets)
if custom_input:
    ticker_list = list(set(ticker_list + parse_custom_tickers(custom_input)))

if not ticker_list:
    st.warning("Selecciona al menos un mercado o ingresa tickers para comenzar.")
    st.stop()

# ─────────────────────────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────────────────────────

st.markdown("# 🎯 HEDGE FUND RADAR PRO")

progress_bar = st.progress(0, text="Cargando datos de mercado...")

# Datos OHLCV
ohlcv_data = fetch_ohlcv_batch(tuple(ticker_list))
progress_bar.progress(40, text="Calculando modelos técnicos...")

# Fundamentales
fund_data = fetch_fundamentals_batch(tuple(ticker_list))
progress_bar.progress(70, text="Evaluando señales...")

# ─────────────────────────────────────────────────────────────────
# PROCESAR CADA TICKER
# ─────────────────────────────────────────────────────────────────

results = []
chart_data = {}

for ticker in ticker_list:
    if ticker not in ohlcv_data:
        continue

    df = ohlcv_data[ticker]

    try:
        # Modelo técnico
        df = compute_technical_score(df)
        # Modelo IA
        df = compute_ai_probability(df)
        # Última vela confirmada
        last = get_last_confirmed(df)

        if last.empty or pd.isna(last.get("score")):
            continue

        # Fundamentales
        fund = fund_data.get(ticker, {})
        fund_eval = evaluate_fundamentals(fund)

        # Máquina de estados
        state_result = compute_state(
            score=last["score"],
            ai_prob=last["ai_prob"],
            extension=last["extension"],
            fundamental_score=fund_eval["fundamental_score"],
        )

        # Guardar chart data para gráficos interactivos
        chart_data[ticker] = df

        results.append({
            "Ticker": ticker,
            "Nombre": fund_eval.get("name", ticker)[:25],
            "Precio": last["Close"],
            "Score": int(last["score"]),
            "AI %": round(last["ai_prob"], 1),
            "Estado": state_result["state"],
            "Emoji": state_emoji(state_result["state"]),
            "Color": state_result["color"],
            "Confianza": state_result["confidence"],
            "Extension %": round(last["extension"], 1),
            "RSI": round(last["rsi"], 1) if not pd.isna(last.get("rsi")) else None,
            "ADX": round(last["adx"], 1) if not pd.isna(last.get("adx")) else None,
            "Rel Vol": round(last["rel_vol"], 2) if not pd.isna(last.get("rel_vol")) else None,
            "P/E": fund_eval["pe_value"],
            "PE Grade": fund_eval["pe_grade"],
            "ROE %": fund_eval["roe_value"],
            "ROE Grade": fund_eval["roe_grade"],
            "ROA %": fund_eval["roa_value"],
            "ROA Grade": fund_eval["roa_grade"],
            "EPS Gr %": fund_eval["eps_growth_value"],
            "EPS Grade": fund_eval["eps_growth_grade"],
            "Fund Score": fund_eval["fundamental_score"],
            "Sector": fund_eval.get("sector", "N/A"),
            "Mkt Cap": fund_eval.get("market_cap"),
            "Alertas": " | ".join(fund_eval.get("alerts", [])),
            "Razones": " | ".join(state_result["reasons"]),
            "_priority": state_priority(state_result["state"]),
            "_score": last["score"],
            "_ai": last["ai_prob"],
        })

    except Exception as e:
        continue

progress_bar.progress(100, text="Listo!")
time.sleep(0.3)
progress_bar.empty()

# ─────────────────────────────────────────────────────────────────
# DATAFRAME DE RESULTADOS
# ─────────────────────────────────────────────────────────────────

if not results:
    st.error("No se pudieron procesar tickers. Verifica tu conexión o selección.")
    st.stop()

df_results = pd.DataFrame(results)

# Aplicar filtros
df_filtered = df_results[
    (df_results["Score"] >= min_score) &
    (df_results["AI %"] >= min_ai) &
    (df_results["Estado"].isin(filter_state))
].sort_values("_priority", ascending=False)

# ─────────────────────────────────────────────────────────────────
# MÉTRICAS RESUMEN
# ─────────────────────────────────────────────────────────────────

col1, col2, col3, col4, col5, col6 = st.columns(6)

n_total = len(df_results)
n_entry = len(df_results[df_results["Estado"].isin(["ENTRY", "ENTRY+"])])
n_accum = len(df_results[df_results["Estado"] == "ACCUM"])
avg_score = df_results["Score"].mean()
avg_ai = df_results["AI %"].mean()
n_strong_fund = len(df_results[df_results["Fund Score"] >= 60])

col1.metric("Tickers", n_total)
col2.metric("🚀 ENTRY", n_entry)
col3.metric("📊 ACCUM", n_accum)
col4.metric("Avg Score", f"{avg_score:.0f}")
col5.metric("Avg AI", f"{avg_ai:.0f}%")
col6.metric("Fund Strong", n_strong_fund)

# ─────────────────────────────────────────────────────────────────
# PANEL DE ALERTAS EN TIEMPO REAL
# ─────────────────────────────────────────────────────────────────

entries = df_filtered[df_filtered["Estado"].isin(["ENTRY", "ENTRY+"])].sort_values("_ai", ascending=False)
accums = df_filtered[df_filtered["Estado"] == "ACCUM"].sort_values("_ai", ascending=False)

if len(entries) > 0:
    st.markdown("## 🚨 ALERTAS ACTIVAS — ENTRY SIGNALS")
    for _, row in entries.iterrows():
        emoji = "🚀" if row["Estado"] == "ENTRY+" else "🟢"
        fund_badge = f"Fund: {row['Fund Score']:.0f}/100" if row["Fund Score"] else ""
        st.markdown(f"""
        <div class="entry-alert">
            <strong>{emoji} {row['Ticker']}</strong> — {row['Nombre']} | 
            Score: <strong>{row['Score']}</strong> | AI: <strong>{row['AI %']}%</strong> | 
            RSI: {row['RSI']} | ADX: {row['ADX']} | Ext: {row['Extension %']}% | {fund_badge}<br/>
            <small>{row['PE Grade']} | {row['ROE Grade']} | {row['ROA Grade']} | {row['EPS Grade']}</small><br/>
            <small style="opacity:0.7">{row['Razones']}</small>
        </div>
        """, unsafe_allow_html=True)

if len(accums) > 0:
    st.markdown("## 📊 ACUMULACIÓN — Monitorear")
    for _, row in accums.head(10).iterrows():
        st.markdown(f"""
        <div class="accum-alert">
            📊 <strong>{row['Ticker']}</strong> — {row['Nombre']} | 
            Score: {row['Score']} | AI: {row['AI %']}% | 
            Ext: {row['Extension %']}%
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# TABLA RADAR PRINCIPAL
# ─────────────────────────────────────────────────────────────────

st.markdown("## 📡 RADAR TABLE — Resultados completos")

# Preparar tabla para display
display_cols = [
    "Emoji", "Ticker", "Nombre", "Precio", "Score", "AI %", "Estado",
    "Extension %", "RSI", "ADX", "Rel Vol",
    "P/E", "PE Grade", "ROE %", "ROE Grade", "ROA %", "ROA Grade",
    "EPS Gr %", "EPS Grade", "Fund Score", "Sector",
]

df_display = df_filtered[display_cols].copy()
df_display["Mkt Cap"] = df_filtered["Mkt Cap"].apply(format_market_cap)
df_display["Precio"] = df_display["Precio"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")

# Sorting options
sort_col = st.selectbox(
    "Ordenar por",
    ["Score ↓", "AI % ↓", "Fund Score ↓", "Extension % ↓", "Estado ↓"],
    index=0,
)

sort_map = {
    "Score ↓": ("Score", False),
    "AI % ↓": ("AI %", False),
    "Fund Score ↓": ("Fund Score", False),
    "Extension % ↓": ("Extension %", False),
    "Estado ↓": ("_priority" if "_priority" in df_filtered.columns else "Score", False),
}

if sort_col == "Estado ↓":
    df_display = df_filtered[display_cols].copy()
    df_display["Mkt Cap"] = df_filtered["Mkt Cap"].apply(format_market_cap)
    df_display["Precio"] = df_filtered["Precio"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
    idx = df_filtered.sort_values("_priority", ascending=False).index
    df_display = df_display.loc[idx]
else:
    col_name, asc = sort_map[sort_col]
    df_display = df_display.sort_values(col_name, ascending=asc)

st.dataframe(
    df_display.reset_index(drop=True),
    use_container_width=True,
    height=min(600, 35 * len(df_display) + 60),
)

st.caption(f"Mostrando {len(df_display)} de {len(df_results)} tickers | Filtros activos: Score ≥ {min_score}, AI ≥ {min_ai}%")

# ─────────────────────────────────────────────────────────────────
# GRÁFICOS INTERACTIVOS
# ─────────────────────────────────────────────────────────────────

st.divider()
st.markdown("## 📈 ANÁLISIS DE GRÁFICAS — Detalle por Ticker")

# Selector de ticker
available_tickers = df_filtered["Ticker"].tolist()
if available_tickers:
    selected_ticker = st.selectbox(
        "Seleccionar ticker para análisis detallado",
        available_tickers,
        index=0,
    )

    if selected_ticker in chart_data:
        df_chart = chart_data[selected_ticker].tail(120)  # Últimos 120 días

        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.45, 0.18, 0.18, 0.19],
            subplot_titles=("Precio + EMAs + Bollinger Bands", "RSI (14)", "ADX (14)", "Volumen Relativo"),
        )

        # ── PRECIO + EMAs + BB ──
        fig.add_trace(go.Candlestick(
            x=df_chart.index,
            open=df_chart["Open"], high=df_chart["High"],
            low=df_chart["Low"], close=df_chart["Close"],
            name="Precio", increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["ema50"],
            name="EMA 50", line=dict(color="#2196F3", width=1.5),
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["ema200"],
            name="EMA 200", line=dict(color="#FF9800", width=1.5),
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["bb_upper"],
            name="BB Upper", line=dict(color="#9E9E9E", width=0.8, dash="dot"),
            showlegend=False,
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["bb_lower"],
            name="BB Lower", line=dict(color="#9E9E9E", width=0.8, dash="dot"),
            fill="tonexty", fillcolor="rgba(158,158,158,0.08)",
            showlegend=False,
        ), row=1, col=1)

        # Marcar señales ENTRY en el chart
        entry_mask = (df_chart["score"] >= 75) & (df_chart["ai_prob"] > 70) & (df_chart["extension"] < 12)
        entry_points = df_chart[entry_mask]
        if len(entry_points) > 0:
            fig.add_trace(go.Scatter(
                x=entry_points.index,
                y=entry_points["Low"] * 0.995,
                mode="markers",
                marker=dict(symbol="triangle-up", size=12, color="#00c853"),
                name="ENTRY Signal",
            ), row=1, col=1)

        # ── RSI ──
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["rsi"],
            name="RSI", line=dict(color="#AB47BC", width=1.5),
        ), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

        # ── ADX ──
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["adx"],
            name="ADX", line=dict(color="#FF7043", width=1.5),
        ), row=3, col=1)
        fig.add_hline(y=25, line_dash="dash", line_color="orange", opacity=0.5, row=3, col=1)

        # ── VOLUMEN RELATIVO ──
        vol_colors = ["#26a69a" if v > 1 else "#ef5350" for v in df_chart["rel_vol"]]
        fig.add_trace(go.Bar(
            x=df_chart.index, y=df_chart["rel_vol"],
            name="Rel Volume", marker_color=vol_colors, opacity=0.7,
        ), row=4, col=1)
        fig.add_hline(y=1, line_dash="dash", line_color="white", opacity=0.3, row=4, col=1)

        fig.update_layout(
            height=800,
            template="plotly_dark",
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=60, r=20, t=60, b=20),
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)")

        st.plotly_chart(fig, use_container_width=True)

        # ── Detalle fundamental del ticker seleccionado ──
        if selected_ticker in fund_data:
            fund = fund_data[selected_ticker]
            fund_eval = evaluate_fundamentals(fund)

            st.markdown(f"### 📊 Fundamentales — {selected_ticker}")
            fc1, fc2, fc3, fc4, fc5 = st.columns(5)

            with fc1:
                pe_val = fund_eval["pe_value"]
                st.metric("P/E Ratio", f"{pe_val:.1f}" if pe_val else "N/A")
                st.caption(fund_eval["pe_grade"])

            with fc2:
                roe_val = fund_eval["roe_value"]
                st.metric("ROE", f"{roe_val:.1f}%" if roe_val else "N/A")
                st.caption(fund_eval["roe_grade"])

            with fc3:
                roa_val = fund_eval["roa_value"]
                st.metric("ROA", f"{roa_val:.1f}%" if roa_val else "N/A")
                st.caption(fund_eval["roa_grade"])

            with fc4:
                eps_val = fund_eval["eps_growth_value"]
                st.metric("EPS Growth", f"{eps_val:.1f}%" if eps_val else "N/A")
                st.caption(fund_eval["eps_growth_grade"])

            with fc5:
                st.metric("Fund Score", f"{fund_eval['fundamental_score']:.0f}/100")
                st.caption(fund_eval.get("sector", ""))

            if fund_eval.get("alerts"):
                for alert in fund_eval["alerts"]:
                    st.warning(alert)

# ─────────────────────────────────────────────────────────────────
# SCORE DISTRIBUTION CHART
# ─────────────────────────────────────────────────────────────────

st.divider()
st.markdown("## 📊 Distribución de señales")

col_d1, col_d2 = st.columns(2)

with col_d1:
    fig_scatter = go.Figure()
    for state in ["ENTRY+", "ENTRY", "ACCUM", "WAIT"]:
        mask = df_results["Estado"] == state
        sub = df_results[mask]
        if len(sub) > 0:
            colors = {"ENTRY+": "#00c853", "ENTRY": "#28a745", "ACCUM": "#ffc107", "WAIT": "#6c757d"}
            fig_scatter.add_trace(go.Scatter(
                x=sub["Score"], y=sub["AI %"],
                mode="markers+text",
                text=sub["Ticker"],
                textposition="top center",
                textfont=dict(size=9),
                marker=dict(size=10, color=colors.get(state, "#666")),
                name=state,
            ))

    fig_scatter.update_layout(
        title="Score vs AI Probability",
        xaxis_title="Technical Score",
        yaxis_title="AI Probability %",
        template="plotly_dark",
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        height=400,
    )
    # Zonas de referencia
    fig_scatter.add_vrect(x0=75, x1=100, fillcolor="green", opacity=0.05, line_width=0)
    fig_scatter.add_hrect(y0=70, y1=95, fillcolor="green", opacity=0.05, line_width=0)

    st.plotly_chart(fig_scatter, use_container_width=True)

with col_d2:
    # Fundamental score distribution
    fund_scores = df_results[df_results["Fund Score"] > 0]["Fund Score"]
    if len(fund_scores) > 0:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=fund_scores,
            nbinsx=20,
            marker_color="#2196F3",
            opacity=0.7,
        ))
        fig_hist.update_layout(
            title="Distribución Fundamental Score",
            xaxis_title="Fundamental Score",
            yaxis_title="Cantidad",
            template="plotly_dark",
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            height=400,
        )
        fig_hist.add_vline(x=60, line_dash="dash", line_color="green", opacity=0.5,
                           annotation_text="Strong ≥60")
        fig_hist.add_vline(x=30, line_dash="dash", line_color="red", opacity=0.5,
                           annotation_text="Weak <30")
        st.plotly_chart(fig_hist, use_container_width=True)

# ─────────────────────────────────────────────────────────────────
# REFERENCIA DE PARÁMETROS FUNDAMENTALES
# ─────────────────────────────────────────────────────────────────

with st.expander("📚 Guía de referencia: Parámetros fundamentales"):
    st.markdown("""
    ### P/E Ratio (Price-to-Earnings)
    Mide cuánto paga el mercado por cada dólar de ganancia.
    | Rango | Evaluación | Acción |
    |-------|------------|--------|
    | < 15 | 🟢 Barato | Potencial oportunidad de valor |
    | 15-25 | 🟡 Justo | Precio razonable |
    | 25-40 | 🟠 Caro | Precaución, ya descontado crecimiento |
    | > 40 | 🔴 Sobrevalorado | Alto riesgo de corrección |
    
    **Importante**: Comparar SIEMPRE con el P/E promedio del sector. Un P/E de 30 en tech es distinto que en utilities.
    
    ### ROE (Return on Equity)
    Mide la eficiencia del capital propio para generar ganancias.
    | Rango | Evaluación |
    |-------|------------|
    | > 20% | 🟢 Excelente |
    | 15-20% | 🟡 Bueno |
    | 10-15% | 🟠 Medio |
    | < 10% | 🔴 Débil |
    
    **Alerta**: ROE alto + Deuda alta = ROE inflado artificialmente. Verificar D/E ratio.
    
    ### ROA (Return on Assets)
    Mide la eficiencia de TODOS los activos (propios + deuda).
    | Rango | Evaluación |
    |-------|------------|
    | > 10% | 🟢 Excelente |
    | 5-10% | 🟡 Bueno |
    | 3-5% | 🟠 Medio |
    | < 3% | 🔴 Débil |
    
    **Nota**: Bancos operan naturalmente con ROA bajo (~1-2%). Comparar dentro del sector.
    
    ### EPS Growth (Earnings Per Share Growth)
    Crecimiento de las ganancias por acción año contra año.
    | Rango | Evaluación |
    |-------|------------|
    | > 25% | 🟢 Fuerte |
    | 10-25% | 🟡 Sólido |
    | 0-10% | 🟠 Moderado |
    | < 0% | 🔴 Declive |
    
    **Clave**: Buscar CONSISTENCIA en los últimos 4 trimestres, no solo el último dato.
    
    ### Qué considerar al invertir según estos parámetros:
    1. **Nunca usar un solo indicador** — combinar P/E + ROE + ROA + EPS Growth
    2. **Contexto sectorial** — comparar con peers del mismo sector
    3. **Tendencia** — ¿están mejorando o empeorando trimestre a trimestre?
    4. **Calidad de ganancias** — EPS sostenido por operaciones reales, no por ingeniería contable
    5. **Deuda** — D/E ratio alto invalida métricas positivas de ROE
    6. **Ciclo económico** — sectores cíclicos pueden tener métricas distorsionadas
    """)

# ─────────────────────────────────────────────────────────────────
# DISCLAIMER
# ─────────────────────────────────────────────────────────────────

st.divider()
st.caption("""
⚠️ **DISCLAIMER**: Esta herramienta es solo para fines informativos y educativos. 
No constituye asesoría financiera ni recomendación de inversión. 
Todo trading implica riesgo de pérdida de capital. Haga su propia investigación 
antes de tomar decisiones de inversión.
""")

# ─────────────────────────────────────────────────────────────────
# AUTO-REFRESH
# ─────────────────────────────────────────────────────────────────

if auto_refresh:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
