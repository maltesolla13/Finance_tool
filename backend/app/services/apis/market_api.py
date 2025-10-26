import yfinance as yf
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP


def _first_trading_day_ohlc(ticker: str, date: datetime, interval: str = "1d"):
    """
        Liefert OHLC des ersten Tages >= date mit Kursdaten (max. 7 Versuche).
    """
    current_date = date
    for _ in range(7):
        start_str = current_date.strftime("%Y-%m-%d")
        end_str = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
        hist = yf.Ticker(ticker).history(start=start_str, end=end_str,
                                         interval=interval)
        if not hist.empty:
            row = hist.iloc[0]
            return {
                "open": Decimal(str(row["Open"])),
                "high": Decimal(str(row["High"])),
                "low": Decimal(str(row["Low"])),
                "close": Decimal(str(row["Close"])),
                "date": current_date,
            }
        current_date += timedelta(days=1)
    raise ValueError(f"No OHLC for {ticker} around {date:%Y-%m-%d}")


# ---- Währung ermitteln (inkl. London-GBp) -----------------------------------

EX_SUFFIX_TO_CCY = {
    ".DE": "EUR", ".F": "EUR", ".PA": "EUR", ".MI": "EUR", ".AS": "EUR",
    ".SW": "CHF", ".VX": "CHF",
    ".L": "GBp",   # London liefert Pence
    ".TO": "CAD", ".V": "CAD",
    ".T": "JPY", ".KS": "KRW", ".HK": "HKD",
}


def _infer_ccy_from_ticker(t: str) -> str | None:
    # Krypto-Paare wie ETH-USD
    if "-" in t and t.rsplit("-", 1)[-1] in {
        "USD", "EUR", "GBP", "CHF", "JPY", "CAD"
    }:
        return t.rsplit("-", 1)[-1]
    for suf, ccy in EX_SUFFIX_TO_CCY.items():
        if t.endswith(suf):
            return ccy
    return None


def resolve_currency(ticker: str) -> tuple[str, Decimal]:
    """
    Liefert (ccy, multiplier). multiplier=0.01 z.B. für GBp→GBP, sonst 1.
    """
    try:
        fi = yf.Ticker(ticker).fast_info
        cur = getattr(fi, "currency", None)
        if cur is None and isinstance(fi, dict):
            # falls fast_info dict-artig ist
            cur = fi.get("currency")
        if cur:
            return (
                "GBP",
                Decimal("0.01")) if cur == "GBp" else (cur, Decimal("1"))
    except Exception:
        pass
    cur = _infer_ccy_from_ticker(ticker) or "USD"
    return ("GBP", Decimal("0.01")) if cur == "GBp" else (cur, Decimal("1"))

# ---- FX: EUR pro 1 CCY am selben Handelstag ---------------------------------


def _fx_rate_EUR_per(ccy: str, date: datetime) -> Decimal:
    if ccy == "EUR":
        return Decimal("1")
    # Versuch 1: EURCCY=X (CCY je 1 EUR) -> EUR/CCY = 1 / (CCY/EUR)
    try:
        r = _first_trading_day_ohlc(f"EUR{ccy}=X", date)["close"]
        return (Decimal("1") / Decimal(str(r)))
    except Exception:
        # Versuch 2: CCYEUR=X (EUR je 1 CCY) -> EUR/CCY = (EUR/CCY)
        r = _first_trading_day_ohlc(f"{ccy}EUR=X", date)["close"]
        return Decimal(str(r))


def _to_eur(raw_price: Decimal, ticker: str, date: datetime) -> Decimal:
    ccy, mult = resolve_currency(ticker)  # z.B. ("USD", 1) oder ("GBP", 0.01)
    price_in_ccy = (raw_price * mult)     # GBp -> GBP, sonst identisch
    eur_per_ccy = _fx_rate_EUR_per(ccy, date)
    return (price_in_ccy * eur_per_ccy).quantize(Decimal("0.00001"),
                                                 rounding=ROUND_HALF_UP)

# ---- Öffentliche API: jetzt standardmäßig EUR zurückgeben -------------------


def fetch_high_on_or_after(
        ticker: str, date: datetime, in_eur: bool = True) -> Decimal:
    o = _first_trading_day_ohlc(ticker, date)
    return _to_eur(o["high"], ticker, o["date"]) if in_eur else o["high"]


def fetch_low_on_or_after(
        ticker: str, date: datetime, in_eur: bool = True) -> Decimal:
    o = _first_trading_day_ohlc(ticker, date)
    return _to_eur(o["low"], ticker, o["date"]) if in_eur else o["low"]
