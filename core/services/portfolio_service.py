from datetime import datetime
from typing import List
from core.entities.portfolio import PortfolioItem, Transaction
from core.interfaces.portfolio_repository import PortfolioRepositoryInterface

class PortfolioService:
    def __init__(self, repository: PortfolioRepositoryInterface, user_id: str = None):
        self.repository = repository
        self.user_id = user_id

    def load_portfolio(self) -> List[PortfolioItem]:
        return self.repository.load_portfolio(self.user_id)

    def save_portfolio(self, items: List[PortfolioItem]):
        self.repository.save_portfolio(self.user_id, items)

    def get_transactions(self, ticker: str = None) -> List[Transaction]:
        return self.repository.get_transactions(self.user_id, ticker)

    def _record_transaction(self, ticker: str, quantity: int, price: float, transaction_type: str):
        new_transaction = Transaction(
            date=datetime.now().isoformat(),
            ticker=ticker,
            quantity=quantity,
            price=price,
            type=transaction_type
        )
        self.repository.add_transaction(self.user_id, new_transaction)

    def add_asset(self, ticker: str, quantity: int, average_price: float):
        ticker = ticker.upper().strip()
        items = self.load_portfolio()
        
        # Verifica se já existe para atualizar
        existing_item = next((item for item in items if item.ticker == ticker), None)
        
        if existing_item:
            # Atualiza preço médio ponderado e quantidade
            total_value = (existing_item.quantity * existing_item.average_price) + (quantity * average_price)
            new_quantity = existing_item.quantity + quantity
            existing_item.average_price = total_value / new_quantity if new_quantity > 0 else 0
            existing_item.quantity = new_quantity
        else:
            items.append(PortfolioItem(ticker, quantity, average_price))
            
        self.save_portfolio(items)
        self._record_transaction(ticker, quantity, average_price, 'BUY')

    def sell_asset(self, ticker: str, quantity: int, price: float):
        ticker = ticker.upper().strip()
        items = self.load_portfolio()
        
        existing_item = next((item for item in items if item.ticker == ticker), None)
        
        if existing_item:
            if existing_item.quantity < quantity:
                raise ValueError("Quantidade insuficiente para venda.")
            
            existing_item.quantity -= quantity
            
            # Se quantidade zerar, remove o item?
            # Por enquanto, se zerar, vamos remover da lista de portfolio visível,
            # mas manter o histórico.
            if existing_item.quantity <= 0:
                items = [item for item in items if item.ticker != ticker]
            
            self.save_portfolio(items)
            self._record_transaction(ticker, quantity, price, 'SELL')
        else:
            raise ValueError("Ativo não encontrado na carteira.")

    def remove_asset(self, ticker: str):
        ticker = ticker.upper().strip()
        items = self.load_portfolio()
        
        # Optional: Record SELL transaction if we knew the sell price, 
        # but remove_asset currently just deletes. 
        # For now, we just update the portfolio state.
        
        items = [item for item in items if item.ticker != ticker]
        self.save_portfolio(items)
        
    def clear_portfolio(self):
        self.save_portfolio([])
