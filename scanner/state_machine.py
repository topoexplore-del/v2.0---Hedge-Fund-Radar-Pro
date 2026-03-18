"""
Máquina de Estados del Hedge Fund Radar Pro.

Estados:
  WAIT   → No hay señal clara. Observar.
  ACCUM  → Acumulación detectada. Preparar posición.
  ENTRY  → Señal de entrada. Ejecutar si se confirma.

Transiciones (mejoradas con fundamentales):
  WAIT → ACCUM:  score >= 60 AND ai_prob > 60
  ACCUM → ENTRY: score >= 75 AND ai_prob > 70 AND extension < 12
                  (BONUS: fundamental_score >= 50 refuerza la señal)
  ENTRY → WAIT:  Si condiciones se degradan

La integración fundamental actúa como FILTRO DE CALIDAD:
  - No bloquea señales técnicas, pero añade confianza
  - Fundamental score >= 60 → señal reforzada "ENTRY+"
  - Fundamental score < 30 → advertencia de riesgo
"""


def compute_state(
    score: float,
    ai_prob: float,
    extension: float,
    fundamental_score: float = None,
) -> dict:
    """
    Determina el estado actual y metadata de la señal.
    
    Args:
        score: Technical score (0-100)
        ai_prob: AI probability (5-95)
        extension: Distancia % del precio vs EMA50
        fundamental_score: Score fundamental (0-100) o None
        
    Returns:
        dict con state, confidence, reason, y color
    """
    state = "WAIT"
    confidence = "low"
    reasons = []
    color = "#6c757d"  # gray

    # ── Transición WAIT → ACCUM ──
    if score >= 60 and ai_prob > 60:
        state = "ACCUM"
        confidence = "medium"
        color = "#ffc107"  # amber
        reasons.append(f"Score {score}/100 ≥ 60")
        reasons.append(f"AI {ai_prob:.1f}% > 60%")

    # ── Transición ACCUM → ENTRY ──
    if score >= 75 and ai_prob > 70 and extension < 12:
        state = "ENTRY"
        confidence = "high"
        color = "#28a745"  # green
        reasons.append(f"Score {score}/100 ≥ 75")
        reasons.append(f"AI {ai_prob:.1f}% > 70%")
        reasons.append(f"Extension {extension:.1f}% < 12%")

        # ── Refuerzo fundamental ──
        if fundamental_score is not None:
            if fundamental_score >= 60:
                state = "ENTRY+"
                confidence = "very_high"
                color = "#00c853"  # bright green
                reasons.append(f"Fundamentales sólidos ({fundamental_score:.0f}/100)")
            elif fundamental_score < 30:
                confidence = "medium"
                reasons.append(f"⚠️ Fundamentales débiles ({fundamental_score:.0f}/100)")

    # ── Metadata WAIT ──
    if state == "WAIT":
        if score >= 45 and ai_prob > 50:
            reasons.append("Señales emergentes, monitorear")
            confidence = "watching"
            color = "#6c757d"
        else:
            reasons.append("Sin señal de breakout")

    return {
        "state": state,
        "confidence": confidence,
        "reasons": reasons,
        "color": color,
        "score": score,
        "ai_prob": ai_prob,
        "extension": extension,
        "fundamental_score": fundamental_score,
    }


def state_emoji(state: str) -> str:
    """Retorna emoji para el estado."""
    return {
        "WAIT": "⏳",
        "ACCUM": "📊",
        "ENTRY": "🟢",
        "ENTRY+": "🚀",
    }.get(state, "❓")


def state_priority(state: str) -> int:
    """Retorna prioridad para sorting (mayor = más importante)."""
    return {
        "ENTRY+": 4,
        "ENTRY": 3,
        "ACCUM": 2,
        "WAIT": 1,
    }.get(state, 0)
