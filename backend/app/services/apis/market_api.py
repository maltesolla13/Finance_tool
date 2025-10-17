import yfinance as yf
from datetime import datetime, timedelta
from decimal import Decimal


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


def fetch_high_on_or_after(ticker: str, date: datetime) -> Decimal:
    return _first_trading_day_ohlc(ticker, date)["high"]


def fetch_low_on_or_after(ticker: str, date: datetime) -> Decimal:
    return _first_trading_day_ohlc(ticker, date)["low"]
