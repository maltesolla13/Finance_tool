from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime


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
    preis: Decimal
    isn: str
    datum: datetime

    class Config:
        extra = 'allow'
