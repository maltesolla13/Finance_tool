from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SchemaKaufitem:
    name: str
    preis: Decimal
    kategorie: str
    konto: str
    laden: str
    datum: datetime

    class Config:
        extra = 'allow'


@dataclass
class SchemaFixkosten:
    name: str
    preis: Decimal
    kategorie: str
    konto: str
    datum: datetime

    class Config:
        extra = 'allow'


@dataclass
class SchemaEinkommen:
    name: str
    preis: Decimal
    kategorie: str
    konto: str
    datum: datetime

    class Config:
        extra = 'allow'


@dataclass
class SchemaSparplan:
    name: str
    isin: str
    ticker: str  # (stock, etf, crypto)
    instrument: str
    datum: datetime
    preis: Optional[Decimal] = None
    anteile: Optional[Decimal] = None

    class Config:
        extra = 'allow'
