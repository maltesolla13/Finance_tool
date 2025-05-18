from decimal import Decimal
from dataclasses import dataclass


@dataclass
class SchemaKaufitem:
    name: str
    preis: Decimal
    Kategorie: str
    konto: str
    laden: str

@dataclass
class SchemaFixkosten:
    name: str
    preis: Decimal
    Kategorie: str
    konto: str

@dataclass
class SchemaSparplan:
    name: str
    preis: Decimal
    isn: str


