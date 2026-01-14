# fii_analyzer/core/entities/fii.py

from dataclasses import dataclass


@dataclass
class FII:
    ticker: str
    price: float
    dividend_yield: float
    pvp: float
    sector: str
    liquidity: float
    vacancia: float
