"""
Modelo Técnico del Hedge Fund Radar Pro.
Traducción FIEL del código PineScript original.

ANTI-REPINTADO GARANTIZADO:
- Todos los cálculos se realizan sobre la serie completa de datos
- El resultado final se toma de la PENÚLTIMA fila (última vela cerrada)
- Nunca se usa la vela actual (potencialmente incompleta)
- Los indicadores usan ventanas fijas sin look-ahead bias

Componentes del Score (0-100):
  - Trend:          30 pts  (EMA50 > EMA200 y Close > EMA200)
  - Momentum:       15 pts  (RSI entre 50-70)
  - Trend Emerging: 15 pts  (ADX entre 18-35)
  - Compression:    15 pts  (BB Width < lowest(BBW,50)*1.2)
  - Accumulation:   15 pts  (OBV > OBV_SMA10 y RelVol > 1)
  - Breakout Setup: 10 pts  (Close > Highest(20)*0.97)
"""

import pandas as pd
import numpy as np


def compute_technical_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el score técnico para cada barra del DataFrame.
    
    Args:
        df: DataFrame con columnas Open, High, Low, Close, Volume
        
    Returns:
        DataFrame con columnas adicionales de indicadores y score
    """
    df = df.copy()
    c = df["Close"]
    h = df["High"]
    v = df["Volume"]

    # ── EMAs ──
    df["ema50"] = c.ewm(span=50, adjust=False).mean()
    df["ema200"] = c.ewm(span=200, adjust=False).mean()

    # ── RSI (14) ──
    df["rsi"] = _rsi(c, 14)

    # ── ADX / DMI (14) ──
    df["adx"], df["di_plus"], df["di_minus"] = _adx_dmi(df, 14)

    # ── Bollinger Bands (20, 2σ) ──
    bb_basis = c.rolling(20).mean()
    bb_dev = c.rolling(20).std() * 2
    df["bb_upper"] = bb_basis + bb_dev
    df["bb_lower"] = bb_basis - bb_dev
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / bb_basis

    # ── Volume ──
    vol_ma = v.rolling(20).mean()
    df["rel_vol"] = v / vol_ma.replace(0, np.nan)

    # ── OBV ──
    price_change = c.diff()
    sign = np.where(price_change > 0, 1, np.where(price_change < 0, -1, 0))
    df["obv"] = (sign * v).cumsum()
    df["obv_sma10"] = df["obv"].rolling(10).mean()

    # ── Highest(20) ──
    df["highest20"] = h.rolling(20).max()

    # ── Lowest BB Width (50) ──
    df["bb_width_lowest50"] = df["bb_width"].rolling(50).min()

    # ── SCORING ──
    # Componente 1: Trend (30 pts)
    df["sig_trend"] = (
        (df["ema50"] > df["ema200"]) & (c > df["ema200"])
    ).astype(int) * 30

    # Componente 2: Momentum (15 pts)
    df["sig_momentum"] = (
        (df["rsi"] > 50) & (df["rsi"] < 70)
    ).astype(int) * 15

    # Componente 3: Trend Emerging (15 pts)
    df["sig_trend_emerging"] = (
        (df["adx"] > 18) & (df["adx"] < 35)
    ).astype(int) * 15

    # Componente 4: Compression (15 pts)
    df["sig_compression"] = (
        df["bb_width"] < df["bb_width_lowest50"] * 1.2
    ).astype(int) * 15

    # Componente 5: Accumulation (15 pts)
    df["sig_accumulation"] = (
        (df["obv"] > df["obv_sma10"]) & (df["rel_vol"] > 1)
    ).astype(int) * 15

    # Componente 6: Breakout Setup (10 pts)
    df["sig_breakout"] = (
        c > df["highest20"] * 0.97
    ).astype(int) * 10

    # Score total
    df["score"] = (
        df["sig_trend"] +
        df["sig_momentum"] +
        df["sig_trend_emerging"] +
        df["sig_compression"] +
        df["sig_accumulation"] +
        df["sig_breakout"]
    )

    # Extension (distancia % del precio respecto a EMA50)
    df["extension"] = (c - df["ema50"]) / df["ema50"] * 100

    return df


def get_last_confirmed(df: pd.DataFrame) -> pd.Series:
    """
    Retorna la ÚLTIMA fila del DataFrame (que ya es una vela cerrada
    confirmada, porque el fetcher eliminó la vela incompleta).
    """
    if len(df) == 0:
        return pd.Series(dtype=float)
    return df.iloc[-1]


# ─────────────────────────────────────────────────────────────────
# INDICADORES INTERNOS
# ─────────────────────────────────────────────────────────────────

def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI calculado con método Wilder (EMA)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _adx_dmi(df: pd.DataFrame, period: int = 14):
    """
    ADX y DMI calculados con el método estándar Wilder.
    Retorna (adx, di_plus, di_minus).
    """
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    # Wilder smoothing
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    plus_di_smooth = plus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    minus_di_smooth = minus_dm.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    plus_di = 100 * plus_di_smooth / atr.replace(0, np.nan)
    minus_di = 100 * minus_di_smooth / atr.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    return adx, plus_di, minus_di
