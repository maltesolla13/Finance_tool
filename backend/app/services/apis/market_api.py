from bisect import bisect_right
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

import yfinance as yf

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


def _last_trading_day_ohlc(ticker: str, date: datetime, interval: str = "1d"):
    """
    Liefert OHLC des letzten Tages <= date mit Kursdaten (max. 7 Tage zurück).
    """
    current_date = date
    for _ in range(7):
        # kleines Fenster zurück + 1 nach vorn, dann <= date filtern
        start_str = (current_date - timedelta(days=7)).strftime("%Y-%m-%d")
        end_str = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
        hist = yf.Ticker(ticker).history(
            start=start_str, end=end_str, interval=interval)
        if not hist.empty:
            filt = hist[hist.index.date <= date.date()]
            if not filt.empty:
                row = filt.iloc[-1]
                return {
                    "open":  Decimal(str(row["Open"])),
                    "high":  Decimal(str(row["High"])),
                    "low":   Decimal(str(row["Low"])),
                    "close": Decimal(str(row["Close"])),
                    "date":  datetime.combine(filt.index[-1].date(),
                                              datetime.min.time())
                }
        current_date -= timedelta(days=1)
    raise ValueError(f"No OHLC <= {date:%Y-%m-%d} for {ticker}")


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


def fetch_low_on_or_before(
        ticker: str, date: datetime, in_eur: bool = True) -> Decimal:
    o = _last_trading_day_ohlc(ticker, date)
    return _to_eur(o["low"], ticker, o["date"]) if in_eur else o["low"]


def fetch_high_on_or_before(
        ticker: str, date: datetime, in_eur: bool = True) -> Decimal:
    o = _last_trading_day_ohlc(ticker, date)
    return _to_eur(o["high"], ticker, o["date"]) if in_eur else o["high"]


def fetch_daily_lows_eur(ticker, start_date, end_date):
    """Load a whole price range in EUR, carrying preceding quotes over holidays.

    Retains the application's daily-low convention. FX rates must also come
    from the requested day or an earlier trading session.
    """
    def series(symbol, column):
        history = yf.Ticker(symbol).history(
            start=(start_date - timedelta(days=30)).isoformat(),
            end=(end_date + timedelta(days=1)).isoformat(),
            interval="1d",
        )
        values = {}
        for stamp, row in history.iterrows():
            value = Decimal(str(row[column]))
            if value.is_finite() and value > 0:
                values[stamp.date()] = value
        if not values:
            raise ValueError(f"Keine Kursdaten fuer {symbol}.")
        days = sorted(values)

        def at(day):
            index = bisect_right(days, day) - 1
            if index < 0:
                raise ValueError(f"Kein Kurs fuer {symbol} am oder vor {day}.")
            return values[days[index]]

        return at

    low = series(ticker, "Low")
    currency, multiplier = resolve_currency(ticker)
    def fx(day):
        return Decimal(1)

    if currency != "EUR":
        try:
            inverse = series(f"EUR{currency}=X", "Close")
            inverse(start_date)
            def fx(day):
                return Decimal(1) / inverse(day)
        except ValueError:
            fx = series(f"{currency}EUR=X", "Close")
    result = {}
    day = start_date
    while day <= end_date:
        result[day] = (low(day) * multiplier * fx(day)).quantize(
            Decimal("0.00001"), rounding=ROUND_HALF_UP
        )
        day += timedelta(days=1)
    return result
