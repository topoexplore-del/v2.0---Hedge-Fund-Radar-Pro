"""
Universo global de tickers para el Hedge Fund Radar Pro.
Organizado por mercado e índice. Extensible por el usuario.
"""

# ── WATCHLIST ORIGINAL (prioridad máxima) ────────────────────────
WATCHLIST_CORE = [
    "VRT", "POWL", "ETN", "ANET", "MPWR", "PWR", "CAT", "FCX",
    "NVDA", "PLTR", "AVGO", "AMD", "LMT", "NOC", "CEG", "SMCI",
    "GE", "ROK", "URI", "DE"
]

# ── S&P 500 TOP HOLDINGS + KEY STOCKS ────────────────────────────
SP500_TOP = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "UNH",
    "JNJ", "V", "XOM", "JPM", "PG", "MA", "HD", "CVX", "MRK", "ABBV",
    "LLY", "PEP", "KO", "COST", "ADBE", "WMT", "CRM", "MCD", "CSCO",
    "ACN", "ABT", "TMO", "DHR", "NKE", "LIN", "TXN", "PM", "NEE",
    "ORCL", "QCOM", "UPS", "RTX", "HON", "LOW", "UNP", "INTC", "SPGI",
    "GS", "BA", "ISRG", "MDT", "BLK", "AXP", "SBUX", "GILD", "ADI",
    "SYK", "MMC", "LRCX", "BKNG", "VRTX", "REGN", "MDLZ", "SCHW",
    "CB", "AMT", "MO", "ZTS", "PLD", "CI", "SO", "DUK", "BDX",
    "CME", "CL", "ICE", "BSX", "EOG", "SLB", "PNC", "TGT", "WM",
    "MCO", "APD", "FDX", "NSC", "ITW", "KLAC", "SNPS", "CDNS",
    "ORLY", "ADP", "MSI", "GD", "SHW", "CTAS", "PH", "HUM",
    "MCHP", "PCAR", "KMB", "AIG", "PRU", "MET", "ALL", "TRV",
    "AFL", "AEP", "D", "XEL", "ES", "WEC", "EXC", "ED", "PEG",
    "FSLR", "ENPH", "SEDG", "RUN", "PLUG", "DKNG", "COIN", "SQ",
    "SNOW", "NET", "CRWD", "ZS", "PANW", "DDOG", "MDB", "SHOP",
    "TTD", "ROKU", "U", "RBLX", "ABNB", "DASH", "LYFT", "UBER",
    "ARM", "SMCI", "IONQ", "RGTI", "QUBT",
]

# ── NASDAQ 100 (complemento al SP500) ───────────────────────────
NASDAQ100_EXTRA = [
    "MRVL", "FTNT", "TEAM", "WDAY", "MNST", "FAST", "PAYX",
    "ODFL", "VRSK", "CPRT", "ANSS", "DLTR", "EBAY", "EA", "CTSH",
    "WBD", "LCID", "RIVN", "CHPT", "NKLA", "SOFI",
    "HOOD", "MARA", "RIOT", "CLSK", "BITF",
]

# ── SECTORES ESTRATÉGICOS ────────────────────────────────────────
SECTOR_ENERGY = [
    "OXY", "COP", "PSX", "VLO", "MPC", "DVN", "HAL", "BKR",
    "FANG", "PXD", "HES", "APA", "OVV", "CTRA", "AR",
]

SECTOR_DEFENSE = [
    "LMT", "NOC", "RTX", "GD", "BA", "HII", "LHX", "TDG",
    "HEI", "KTOS", "LDOS", "BWXT",
]

SECTOR_AI_SEMIS = [
    "NVDA", "AMD", "INTC", "AVGO", "QCOM", "TXN", "MU", "LRCX",
    "KLAC", "AMAT", "ASML", "TSM", "ON", "MRVL", "MCHP",
    "ADI", "NXPI", "MPWR", "SWKS", "QRVO",
]

SECTOR_BIOTECH = [
    "MRNA", "BNTX", "REGN", "VRTX", "BIIB", "ILMN", "SGEN",
    "ALNY", "BMRN", "EXAS", "RARE", "NBIX", "SRPT", "PCVX",
]

SECTOR_INFRASTRUCTURE = [
    "VRT", "POWL", "ETN", "PWR", "EMR", "ROK", "AME", "GNRC",
    "URI", "CAT", "DE", "PCAR", "CMI", "TT", "XYL", "WMS",
]

# ── MERCADOS INTERNACIONALES ─────────────────────────────────────
# Europa (ADRs o tickers US-listed)
EUROPE_MAJOR = [
    "ASML", "SAP", "NVO", "AZN", "SHEL", "TTE", "UL", "DEO",
    "GSK", "BP", "RIO", "BHP", "VALE", "GOLD", "NEM",
    "SAN", "BBVA", "ING", "DB", "UBS", "CS",
]

# Asia (ADRs)
ASIA_MAJOR = [
    "TSM", "BABA", "JD", "PDD", "BIDU", "NIO", "XPEV", "LI",
    "SONY", "TM", "HMC", "MUFG", "SMFG", "MFG",
    "SE", "GRAB", "CPNG",
]

# LATAM (ADRs + principales)
LATAM_MAJOR = [
    "NU", "MELI", "STNE", "PAGS", "XP", "GLOB",
    "VALE", "PBR", "ITUB", "BBD", "ABEV", "SBS",
    "AMX", "FMX", "KOF", "BSMX", "TV",
    "EC", "ECOPETROL", "CIB", "BHC",
    "SUPV", "YPF", "GGAL", "PAM", "CRESY",
]

# ── CRIPTO-RELATED ───────────────────────────────────────────────
CRYPTO_STOCKS = [
    "COIN", "MSTR", "MARA", "RIOT", "CLSK", "BITF", "HUT",
    "CIFR", "BTBT", "SOS",
]

# ── FUNCIONES DE ACCESO ──────────────────────────────────────────

MARKET_MAP = {
    "🎯 Watchlist Core (20)": WATCHLIST_CORE,
    "🇺🇸 S&P 500 Top": SP500_TOP,
    "🇺🇸 NASDAQ Extra": NASDAQ100_EXTRA,
    "⚡ Energía": SECTOR_ENERGY,
    "🛡️ Defensa": SECTOR_DEFENSE,
    "🤖 AI & Semiconductores": SECTOR_AI_SEMIS,
    "🧬 Biotech": SECTOR_BIOTECH,
    "🏗️ Infraestructura": SECTOR_INFRASTRUCTURE,
    "🇪🇺 Europa (ADRs)": EUROPE_MAJOR,
    "🇨🇳 Asia (ADRs)": ASIA_MAJOR,
    "🌎 LATAM": LATAM_MAJOR,
    "₿ Cripto-Related": CRYPTO_STOCKS,
}


def get_tickers(markets: list[str]) -> list[str]:
    """Retorna lista única de tickers para los mercados seleccionados."""
    tickers = []
    for market in markets:
        tickers.extend(MARKET_MAP.get(market, []))
    # Deduplicar preservando orden
    seen = set()
    unique = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def get_all_tickers() -> list[str]:
    """Retorna todos los tickers disponibles sin duplicados."""
    return get_tickers(list(MARKET_MAP.keys()))


def parse_custom_tickers(text: str) -> list[str]:
    """Parsea tickers ingresados manualmente (comma o space separated)."""
    import re
    tickers = re.split(r'[,\s;]+', text.strip().upper())
    return [t for t in tickers if t and len(t) <= 10]
