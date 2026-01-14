from abc import ABC, abstractmethod
from typing import List
from core.entities.portfolio import PortfolioItem, Transaction

class PortfolioRepositoryInterface(ABC):
    @abstractmethod
    def load_portfolio(self, user_id: str) -> List[PortfolioItem]:
        pass

    @abstractmethod
    def save_portfolio(self, user_id: str, items: List[PortfolioItem]):
        pass

    @abstractmethod
    def get_transactions(self, user_id: str, ticker: str = None) -> List[Transaction]:
        pass

    @abstractmethod
    def add_transaction(self, user_id: str, transaction: Transaction):
        pass
