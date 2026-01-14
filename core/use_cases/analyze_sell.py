from typing import List
from core.entities.fii import FII


class AnalyzeSell:
    def execute(self, fiis: List[FII], min_dy: float = 6.0, max_pvp: float = 1.5, max_vacancia: float = 10.0) -> List[FII]:
        """
        Identifica FIIs potenciais para venda.
        Critérios (OU):
        - Dividend Yield abaixo do mínimo (anualizado)
        - P/VP muito alto (sobrevalorizado)
        - Vacância alta
        """
        filtered_fiis = [
            fii for fii in fiis
            if (fii.dividend_yield < min_dy and fii.dividend_yield > 0) # DY muito baixo (mas existente)
            or fii.pvp > max_pvp 
            or fii.vacancia > max_vacancia
        ]
        return filtered_fiis
