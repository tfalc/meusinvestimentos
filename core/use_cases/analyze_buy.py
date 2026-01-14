from typing import List
from core.entities.fii import FII


class AnalyzeBuy:
    def execute(self, fiis: List[FII], budget: float, max_pvp: float = 1.10, min_liquidity: float = 0) -> List[FII]:
        """
        Filtra FIIs para compra.
        :param fiis: Lista de FIIs
        :param budget: Orçamento disponível
        :param max_pvp: Máximo P/VP aceitável (default 1.10)
        :param min_liquidity: Liquidez mínima diária (default 0)
        :return: Lista de FIIs recomendados ordenados por DY
        """
        filtered_fiis = [
            fii for fii in fiis
            if fii.price > 0 and fii.price <= budget and fii.pvp <= max_pvp and fii.liquidity >= min_liquidity
        ]
        # Ordena pelos melhores dividend yields
        filtered_fiis.sort(key=lambda x: x.dividend_yield, reverse=True)
        return filtered_fiis
