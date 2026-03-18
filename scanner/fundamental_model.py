"""
Modelo Fundamental del Hedge Fund Radar Pro.

Analiza métricas fundamentales clave y asigna calificaciones
tipo semáforo para evaluación rápida.

Parámetros de referencia:
  P/E Ratio:    <15 barato | 15-25 justo | 25-40 caro | >40 sobrevalorado
  ROE:          >20% excelente | 15-20% bueno | 10-15% medio | <10% débil
  ROA:          >10% excelente | 5-10% bueno | 3-5% medio | <3% débil
  EPS Growth:   >25% fuerte | 10-25% sólido | 0-10% moderado | <0% declive

Consideraciones adicionales:
  - P/E debe compararse con el sector (tech ≠ utilities)
  - ROE alto con deuda excesiva es señal de alerta
  - EPS buscar consistencia, no solo el último dato
  - ROA varía por industria (bancos ~1-2% es normal)
"""

import numpy as np


# ─────────────────────────────────────────────────────────────────
# UMBRALES DE REFERENCIA
# ─────────────────────────────────────────────────────────────────

PE_THRESHOLDS = {
    "🟢 Barato":       (None, 15),
    "🟡 Justo":        (15, 25),
    "🟠 Caro":         (25, 40),
    "🔴 Sobrevalorado": (40, None),
}

ROE_THRESHOLDS = {
    "🟢 Excelente": (20, None),
    "🟡 Bueno":     (15, 20),
    "🟠 Medio":     (10, 15),
    "🔴 Débil":     (None, 10),
}

ROA_THRESHOLDS = {
    "🟢 Excelente": (10, None),
    "🟡 Bueno":     (5, 10),
    "🟠 Medio":     (3, 5),
    "🔴 Débil":     (None, 3),
}

EPS_GROWTH_THRESHOLDS = {
    "🟢 Fuerte":   (25, None),
    "🟡 Sólido":   (10, 25),
    "🟠 Moderado": (0, 10),
    "🔴 Declive":  (None, 0),
}


# ─────────────────────────────────────────────────────────────────
# EVALUACIÓN
# ─────────────────────────────────────────────────────────────────

def grade_metric(value, thresholds: dict) -> tuple[str, int]:
    """
    Evalúa un valor contra umbrales y retorna (etiqueta, puntos 0-3).
    3 = mejor, 0 = peor.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ("⚪ N/A", 0)

    points = len(thresholds) - 1
    for label, (low, high) in thresholds.items():
        if low is None and high is not None:
            if value < high:
                return (label, points)
        elif high is None and low is not None:
            if value >= low:
                return (label, points)
        elif low is not None and high is not None:
            if low <= value < high:
                return (label, points)
        points -= 1

    return ("⚪ N/A", 0)


def evaluate_fundamentals(fund_data: dict) -> dict:
    """
    Evalúa todas las métricas fundamentales de un ticker.
    
    Args:
        fund_data: dict con claves pe_trailing, roe, roa, eps_growth, etc.
        
    Returns:
        dict con grades, scores, y el fundamental_score consolidado (0-100).
    """
    pe = fund_data.get("pe_trailing")
    roe = fund_data.get("roe")
    roa = fund_data.get("roa")
    eps_g = fund_data.get("eps_growth")

    # Grading individual
    pe_grade, pe_pts = grade_pe(pe)
    roe_grade, roe_pts = grade_metric(roe, ROE_THRESHOLDS)
    roa_grade, roa_pts = grade_metric(roa, ROA_THRESHOLDS)
    eps_grade, eps_pts = grade_metric(eps_g, EPS_GROWTH_THRESHOLDS)

    # Score fundamental consolidado (0-100)
    # Ponderación: P/E 30%, ROE 30%, ROA 20%, EPS Growth 20%
    max_pts = 3 * 4  # 3 puntos máx por cada una de 4 métricas
    raw_pts = pe_pts + roe_pts + roa_pts + eps_pts
    available_metrics = sum(1 for v in [pe, roe, roa, eps_g] if v is not None)

    if available_metrics > 0:
        # Normalizar al número de métricas disponibles
        normalized = raw_pts / (available_metrics * 3) * 100
        fund_score = round(normalized, 1)
    else:
        fund_score = 0

    # Señales de alerta
    alerts = _check_alerts(fund_data)

    return {
        "pe_value": pe,
        "pe_grade": pe_grade,
        "pe_pts": pe_pts,
        "roe_value": roe,
        "roe_grade": roe_grade,
        "roe_pts": roe_pts,
        "roa_value": roa,
        "roa_grade": roa_grade,
        "roa_pts": roa_pts,
        "eps_growth_value": eps_g,
        "eps_growth_grade": eps_grade,
        "eps_growth_pts": eps_pts,
        "fundamental_score": fund_score,
        "alerts": alerts,
        "sector": fund_data.get("sector", "N/A"),
        "market_cap": fund_data.get("market_cap"),
        "name": fund_data.get("name", ""),
    }


def grade_pe(pe_value) -> tuple[str, int]:
    """
    P/E tiene lógica especial: negativo indica pérdidas.
    """
    if pe_value is None or (isinstance(pe_value, float) and np.isnan(pe_value)):
        return ("⚪ N/A", 0)
    if pe_value < 0:
        return ("🔴 Pérdidas", 0)
    return grade_metric(pe_value, PE_THRESHOLDS)


def _check_alerts(fund_data: dict) -> list[str]:
    """Genera alertas basadas en combinaciones de métricas."""
    alerts = []

    pe = fund_data.get("pe_trailing")
    roe = fund_data.get("roe")
    debt = fund_data.get("debt_to_equity")
    margin = fund_data.get("profit_margin")

    # ROE alto pero deuda alta → inflado artificialmente
    if roe is not None and debt is not None:
        if roe > 20 and debt > 200:
            alerts.append("⚠️ ROE alto con deuda excesiva (D/E > 200%)")

    # P/E negativo
    if pe is not None and pe < 0:
        alerts.append("⚠️ P/E negativo: la empresa reporta pérdidas")

    # Márgenes negativos
    if margin is not None and margin < 0:
        alerts.append("⚠️ Margen de ganancia negativo")

    # EPS en declive
    eps_g = fund_data.get("eps_growth")
    if eps_g is not None and eps_g < -20:
        alerts.append("⚠️ EPS en fuerte declive (>{:.0f}%)".format(abs(eps_g)))

    return alerts


# ─────────────────────────────────────────────────────────────────
# FORMATO DE MERCADO
# ─────────────────────────────────────────────────────────────────

def format_market_cap(mc):
    """Formatea market cap a texto legible."""
    if mc is None:
        return "N/A"
    if mc >= 1e12:
        return f"${mc/1e12:.1f}T"
    if mc >= 1e9:
        return f"${mc/1e9:.1f}B"
    if mc >= 1e6:
        return f"${mc/1e6:.0f}M"
    return f"${mc:,.0f}"
