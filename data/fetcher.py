"""
Módulo de obtención de datos: Yahoo Finance + Finviz.
Diseñado para eficiencia en Streamlit Cloud con caching agresivo.
Anti-repintado: solo usa velas CERRADAS (confirmadas).
"""

import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# DATOS OHLCV (Yahoo Finance)
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ohlcv_batch(tickers: tuple, period: str = "6mo", interval: str = "1d") -> dict[str, pd.DataFrame]:
    """
    Descarga datos OHLCV en batch para una lista de tickers.
    Retorna dict {ticker: DataFrame} con datos limpios.
    
    ANTI-REPINTADO: Elimina la última fila si el mercado está abierto
    (vela incompleta). Solo retorna velas cerradas confirmadas.
    """
    if not tickers:
        return {}

    ticker_list = list(tickers)
    results = {}

    # Batch download para eficiencia (máximo 50 por batch)
    batch_size = 50
    for i in range(0, len(ticker_list), batch_size):
        batch = ticker_list[i:i + batch_size]
        try:
            data = yf.download(
                batch,
                period=period,
                interval=interval,
                group_by="ticker",
                progress=False,
                threads=True,
                auto_adjust=True,
            )

            if data.empty:
                continue

            for ticker in batch:
                try:
                    if len(batch) == 1:
                        df = data.copy()
                    else:
                        if ticker not in data.columns.get_level_values(0):
                            continue
                        df = data[ticker].copy()

                    df = df.dropna(subset=["Close", "Volume"])

                    if len(df) < 60:
                        continue

                    # ── ANTI-REPINTADO ──
                    # Verificar si la última vela podría estar incompleta
                    # Si el último dato es de hoy y el mercado podría estar abierto,
                    # eliminar la última fila
                    if len(df) > 0:
                        last_date = df.index[-1]
                        now = datetime.now()
                        if hasattr(last_date, 'date'):
                            if last_date.date() == now.date():
                                # Posible vela incompleta: eliminar
                                df = df.iloc[:-1]

                    if len(df) < 60:
                        continue

                    # Asegurar tipos correctos
                    for col in ["Open", "High", "Low", "Close"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)

                    results[ticker] = df

                except Exception as e:
                    logger.warning(f"Error procesando {ticker}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error en batch download: {e}")
            continue

    return results


# ─────────────────────────────────────────────────────────────────
# DATOS FUNDAMENTALES (Yahoo Finance)
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fundamentals_batch(tickers: tuple) -> dict[str, dict]:
    """
    Obtiene datos fundamentales de Yahoo Finance.
    Cache de 1 hora (fundamentales no cambian cada minuto).
    """
    results = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            results[ticker] = {
                "pe_trailing": _safe_get(info, "trailingPE"),
                "pe_forward": _safe_get(info, "forwardPE"),
                "roe": _safe_pct(info, "returnOnEquity"),
                "roa": _safe_pct(info, "returnOnAssets"),
                "eps_trailing": _safe_get(info, "trailingEps"),
                "eps_forward": _safe_get(info, "forwardEps"),
                "eps_growth": _safe_pct(info, "earningsQuarterlyGrowth"),
                "revenue_growth": _safe_pct(info, "revenueGrowth"),
                "market_cap": _safe_get(info, "marketCap"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "name": info.get("shortName", ticker),
                "price": _safe_get(info, "currentPrice") or _safe_get(info, "regularMarketPrice"),
                "debt_to_equity": _safe_get(info, "debtToEquity"),
                "current_ratio": _safe_get(info, "currentRatio"),
                "profit_margin": _safe_pct(info, "profitMargins"),
                "dividend_yield": _safe_pct(info, "dividendYield"),
                "beta": _safe_get(info, "beta"),
                "52w_high": _safe_get(info, "fiftyTwoWeekHigh"),
                "52w_low": _safe_get(info, "fiftyTwoWeekLow"),
            }
        except Exception as e:
            logger.warning(f"Error fundamentales {ticker}: {e}")
            results[ticker] = _empty_fundamentals(ticker)

    return results


# ─────────────────────────────────────────────────────────────────
# FINVIZ SCREENER (Optional Enhancement)
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_finviz_overview(tickers: tuple) -> dict[str, dict]:
    """
    Intenta obtener datos de Finviz como complemento.
    Falla silenciosamente si no está disponible.
    """
    results = {}
    try:
        from finvizfinance.quote import finvizfinance as fvz
        for ticker in tickers[:100]:  # Limitar para evitar rate limits
            try:
                stock = fvz(ticker)
                data = stock.ticker_fundament()
                results[ticker] = {
                    "finviz_pe": _parse_float(data.get("P/E", None)),
                    "finviz_roe": _parse_pct(data.get("ROE", None)),
                    "finviz_roa": _parse_pct(data.get("ROA", None)),
                    "finviz_eps_growth": _parse_pct(data.get("EPS next Y", None)),
                    "finviz_target": _parse_float(data.get("Target Price", None)),
                    "finviz_rsi": _parse_float(data.get("RSI (14)", None)),
                    "finviz_rel_volume": _parse_float(data.get("Rel Volume", None)),
                    "finviz_short_float": _parse_pct(data.get("Short Float", None)),
                    "finviz_perf_week": _parse_pct(data.get("Perf Week", None)),
                    "finviz_perf_month": _parse_pct(data.get("Perf Month", None)),
                }
            except Exception:
                continue
    except ImportError:
        logger.info("finvizfinance no disponible, omitiendo Finviz data")
    except Exception as e:
        logger.warning(f"Error Finviz: {e}")

    return results


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _safe_get(info: dict, key: str):
    """Extrae valor numérico seguro de yfinance info."""
    val = info.get(key)
    if val is None or val == "N/A":
        return None
    try:
        v = float(val)
        return v if np.isfinite(v) else None
    except (ValueError, TypeError):
        return None


def _safe_pct(info: dict, key: str):
    """Extrae porcentaje de yfinance (viene como decimal 0.xx)."""
    val = _safe_get(info, key)
    if val is not None and abs(val) < 10:  # yfinance da decimales
        return round(val * 100, 2)
    return val


def _parse_float(val):
    """Parsea float de string Finviz."""
    if val is None or val == "-" or val == "":
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_pct(val):
    """Parsea porcentaje de Finviz (viene como '12.34%')."""
    if val is None or val == "-" or val == "":
        return None
    try:
        return float(str(val).replace("%", "").replace(",", ""))
    except (ValueError, TypeError):
        return None


def _empty_fundamentals(ticker: str) -> dict:
    """Retorna dict vacío de fundamentales para fallback."""
    return {
        "pe_trailing": None, "pe_forward": None,
        "roe": None, "roa": None,
        "eps_trailing": None, "eps_forward": None,
        "eps_growth": None, "revenue_growth": None,
        "market_cap": None, "sector": "N/A", "industry": "N/A",
        "name": ticker, "price": None,
        "debt_to_equity": None, "current_ratio": None,
        "profit_margin": None, "dividend_yield": None,
        "beta": None, "52w_high": None, "52w_low": None,
    }
