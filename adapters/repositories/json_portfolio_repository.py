import json
import os
import sys
from typing import List, Tuple
from dataclasses import asdict

from core.interfaces.portfolio_repository import PortfolioRepositoryInterface
from core.entities.portfolio import PortfolioItem, Transaction

class JsonPortfolioRepository(PortfolioRepositoryInterface):
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.getcwd()

    def _get_paths(self, user_id: str) -> Tuple[str, str]:
        if user_id and user_id != 'default':
            portfolio_path = os.path.join(self.base_path, f"portfolio_{user_id}.json")
            transactions_path = os.path.join(self.base_path, f"transactions_{user_id}.json")
        else:
            portfolio_path = os.path.join(self.base_path, "portfolio.json")
            transactions_path = os.path.join(self.base_path, "transactions.json")
        return portfolio_path, transactions_path

    def _ensure_file_exists(self, file_path: str):
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)

    def load_portfolio(self, user_id: str) -> List[PortfolioItem]:
        portfolio_path, _ = self._get_paths(user_id)
        self._ensure_file_exists(portfolio_path)
        try:
            with open(portfolio_path, 'r') as f:
                data = json.load(f)
                return [PortfolioItem(**item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_portfolio(self, user_id: str, items: List[PortfolioItem]):
        portfolio_path, _ = self._get_paths(user_id)
        with open(portfolio_path, 'w') as f:
            json.dump([asdict(item) for item in items], f, indent=4)

    def get_transactions(self, user_id: str, ticker: str = None) -> List[Transaction]:
        _, transactions_path = self._get_paths(user_id)
        self._ensure_file_exists(transactions_path)
        try:
            with open(transactions_path, 'r') as f:
                data = json.load(f)
                transactions = [Transaction(**item) for item in data]
                if ticker:
                    transactions = [t for t in transactions if t.ticker == ticker]
                # Sort by date descending
                return sorted(transactions, key=lambda x: x.date, reverse=True)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def add_transaction(self, user_id: str, transaction: Transaction):
        _, transactions_path = self._get_paths(user_id)
        self._ensure_file_exists(transactions_path)
        try:
            with open(transactions_path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []
        
        data.append(asdict(transaction))
        
        with open(transactions_path, 'w') as f:
            json.dump(data, f, indent=4)
