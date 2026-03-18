# 🎯 HEDGE FUND RADAR PRO — Market Scanner v2.0

Scanner de mercado en tiempo real con análisis técnico + modelo IA + análisis fundamental.
Evolución del indicador PineScript original, sin limitaciones de tickers.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![License](https://img.shields.io/badge/License-Private-gray)

## 🚀 Demo en vivo

**[▶ Abrir en Streamlit Cloud](https://share.streamlit.io/)** *(Configurar después del deploy)*

## 📡 Características

### Modelo Técnico (Score 0-100)
- **EMA 50/200** — Detección de tendencia
- **RSI (14)** — Momentum en zona óptima (50-70)
- **ADX (14)** — Fuerza de tendencia emergente (18-35)
- **Bollinger Bands** — Compresión de volatilidad
- **OBV + Volumen relativo** — Acumulación institucional
- **Breakout Setup** — Cercanía al máximo de 20 períodos

### Modelo IA (Probabilidad 5-95%)
- Sigmoid con inputs normalizados: Momentum Z-score, Trend Strength, Relative Volume, ADX
- Ajuste dinámico por régimen de volatilidad
- Bounds garantizados [5%, 95%]

### Análisis Fundamental
- **P/E Ratio** — Valoración relativa con semáforo
- **ROE** — Eficiencia del capital propio
- **ROA** — Eficiencia de activos totales
- **EPS Growth** — Crecimiento de ganancias
- Score fundamental consolidado (0-100) con alertas automáticas

### Máquina de Estados
| Estado | Condición | Acción |
|--------|-----------|--------|
| ⏳ WAIT | Default | Observar |
| 📊 ACCUM | Score ≥ 60, AI > 60% | Preparar posición |
| 🟢 ENTRY | Score ≥ 75, AI > 70%, Extension < 12% | Ejecutar |
| 🚀 ENTRY+ | ENTRY + Fundamentales ≥ 60 | Señal reforzada |

### Anti-Repintado Garantizado
- Solo usa velas **cerradas confirmadas**
- Elimina automáticamente la vela actual (incompleta) durante horario de mercado
- Verificado con test de look-ahead bias

## 🏗️ Arquitectura

```
hedge-fund-radar-pro/
├── app.py                      # Streamlit dashboard principal
├── scanner/
│   ├── technical_model.py      # Score técnico (traducción fiel de PineScript)
│   ├── ai_model.py             # Modelo IA sigmoid
│   ├── fundamental_model.py    # P/E, ROE, ROA, EPS con semáforos
│   └── state_machine.py        # WAIT → ACCUM → ENTRY → ENTRY+
├── data/
│   ├── tickers.py              # Universo global (300+ tickers)
│   └── fetcher.py              # Yahoo Finance + Finviz + cache
├── requirements.txt
├── .streamlit/config.toml
└── README.md
```

## 🌍 Universo de Tickers (300+)

| Mercado | Tickers | Cobertura |
|---------|---------|-----------|
| 🎯 Watchlist Core | 20 | Las 20 originales del PineScript |
| 🇺🇸 S&P 500 Top | ~130 | Principales por capitalización |
| 🇺🇸 NASDAQ Extra | ~25 | Complemento tech/growth |
| ⚡ Energía | 15 | Oil, Gas, Renewables |
| 🛡️ Defensa | 12 | Aerospace & Defense |
| 🤖 AI & Semis | 20 | Semiconductores + AI |
| 🧬 Biotech | 14 | Biotecnología |
| 🏗️ Infraestructura | 16 | Industrial + Construction |
| 🇪🇺 Europa (ADRs) | 21 | Principales ADRs europeos |
| 🇨🇳 Asia (ADRs) | 17 | China, Japón, SE Asia |
| 🌎 LATAM | 25 | Colombia, Brasil, México, Argentina |
| ₿ Cripto-Related | 10 | Crypto mining + exchanges |

## 📊 Guía de Parámetros Fundamentales

### P/E Ratio
| Rango | Evaluación | Consideraciones |
|-------|------------|-----------------|
| < 15 | 🟢 Barato | Comparar con sector |
| 15-25 | 🟡 Justo | Zona de equilibrio |
| 25-40 | 🟠 Caro | Ya descuenta crecimiento |
| > 40 | 🔴 Sobrevalorado | Riesgo de corrección |
| < 0 | 🔴 Pérdidas | Empresa sin beneficios |

### ROE (Return on Equity)
| Rango | Evaluación | Alerta |
|-------|------------|--------|
| > 20% | 🟢 Excelente | Verificar que no sea por deuda alta |
| 15-20% | 🟡 Bueno | — |
| 10-15% | 🟠 Medio | — |
| < 10% | 🔴 Débil | Capital ineficiente |

### ROA (Return on Assets)
| Rango | Evaluación | Nota |
|-------|------------|------|
| > 10% | 🟢 Excelente | — |
| 5-10% | 🟡 Bueno | — |
| 3-5% | 🟠 Medio | — |
| < 3% | 🔴 Débil | Bancos ~1-2% es normal |

### EPS Growth
| Rango | Evaluación | Buscar |
|-------|------------|--------|
| > 25% YoY | 🟢 Fuerte | Consistencia 4 trimestres |
| 10-25% | 🟡 Sólido | — |
| 0-10% | 🟠 Moderado | — |
| < 0% | 🔴 Declive | Señal de alerta |

## 🛠️ Instalación Local

```bash
git clone https://github.com/TU-USUARIO/hedge-fund-radar-pro.git
cd hedge-fund-radar-pro
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Deploy en Streamlit Cloud

1. Push este repo a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io/)
3. Conecta tu repo de GitHub
4. Selecciona `app.py` como archivo principal
5. Deploy

## ⚠️ Disclaimer

Esta herramienta es solo para fines informativos y educativos.
No constituye asesoría financiera ni recomendación de inversión.
Todo trading implica riesgo de pérdida de capital.
