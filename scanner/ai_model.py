"""
Modelo IA del Hedge Fund Radar Pro.
Traducción FIEL del código PineScript original.

Calcula una probabilidad de breakout exitoso (5-95%) usando:
- Momentum Z-score (RSI normalizado)
- Trend Strength (divergencia EMA50/EMA200)
- Relative Volume
- ADX normalizado
- Ajuste por régimen de volatilidad

Output: aiProb ∈ [5, 95] via función sigmoid.
"""

import pandas as pd
import numpy as np


def compute_ai_probability(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la probabilidad IA para cada barra.
    
    Requiere que compute_technical_score() ya haya sido ejecutado
    (necesita columnas: rsi, ema50, ema200, rel_vol, adx, bb_width).
    
    Args:
        df: DataFrame con indicadores técnicos precalculados
        
    Returns:
        DataFrame con columna 'ai_prob' añadida
    """
    df = df.copy()

    # ── Inputs normalizados ──
    # Momentum Z-score: cuántas desviaciones estándar del RSI respecto a 50
    df["momentum_z"] = (df["rsi"] - 50) / 10

    # Trend Strength: divergencia relativa entre EMAs
    df["trend_strength"] = (df["ema50"] - df["ema200"]) / df["ema200"].replace(0, np.nan)

    # Régimen de volatilidad: BB Width actual vs su media
    bb_width_sma50 = df["bb_width"].rolling(50).mean()
    df["vol_regime"] = df["bb_width"] / bb_width_sma50.replace(0, np.nan)

    # ── Señal cruda (raw) ──
    df["ai_raw"] = (
        df["momentum_z"] * 0.8 +
        df["trend_strength"] * 5 +
        (df["rel_vol"] - 1) * 1.2 +
        (df["adx"] / 25)
    )

    # ── Sigmoid → Probabilidad base ──
    df["ai_prob"] = 100 / (1 + np.exp(-df["ai_raw"]))

    # ── Ajuste por régimen de volatilidad ──
    df["ai_prob"] = df["ai_prob"] * (1 + (df["vol_regime"] - 1) * 0.5)

    # ── Clamp [5, 95] ──
    df["ai_prob"] = df["ai_prob"].clip(lower=5, upper=95)

    return df
