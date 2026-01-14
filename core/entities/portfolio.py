from dataclasses import dataclass

@dataclass
class Transaction:
    date: str
    ticker: str
    quantity: int
    price: float
    type: str  # 'BUY' or 'SELL'

@dataclass
class PortfolioItem:
    ticker: str
    quantity: int
    average_price: float
