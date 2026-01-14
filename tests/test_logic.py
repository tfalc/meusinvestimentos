
import unittest
from unittest.mock import MagicMock, patch
from core.entities.fii import FII
from core.use_cases.analyze_buy import AnalyzeBuy
from core.use_cases.analyze_sell import AnalyzeSell
from adapters.repositories.fii_repository import FIIRepository

class TestFIIAnalysis(unittest.TestCase):
    def setUp(self):
        self.fiis = [
            FII(ticker="FIIA11", price=100.0, dividend_yield=10.0, pvp=1.0, sector="Lajes", liquidity=100000, vacancia=5.0),
            FII(ticker="FIIB11", price=150.0, dividend_yield=4.0, pvp=1.6, sector="Shoppings", liquidity=50000, vacancia=15.0),
            FII(ticker="FIIC11", price=80.0, dividend_yield=12.0, pvp=0.9, sector="Papel", liquidity=200000, vacancia=0.0),
        ]

    def test_analyze_buy(self):
        use_case = AnalyzeBuy()
        # Budget 120, max_pvp 1.1
        result = use_case.execute(self.fiis, budget=120.0, max_pvp=1.1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].ticker, "FIIC11") # DY 12.0
        self.assertEqual(result[1].ticker, "FIIA11") # DY 10.0
        # FIIB11 ignored (price > budget, pvp > 1.1)

    def test_analyze_sell(self):
        use_case = AnalyzeSell()
        # min_dy 6.0, max_pvp 1.5, max_vacancia 10.0
        result = use_case.execute(self.fiis, min_dy=6.0, max_pvp=1.5, max_vacancia=10.0)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].ticker, "FIIB11") 
        # FIIB11: DY 4.0 (<6), PVP 1.6 (>1.5), Vacancia 15 (>10) -> Sell candidate

    @patch('adapters.repositories.fii_repository.requests.get')
    def test_repository_parsing(self, mock_get):
        html_content = """
        <html>
            <table>
                <thead>
                    <tr>
                        <th>Código</th><th>Setor</th><th>Liquidez Diária</th><th>P/VP</th><th>Dividend Yield</th><th>Vacância Física</th><th>Preço Atual</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>TEST11</td><td>Logística</td><td>R$ 1.000,00</td><td>0,95</td><td>10,5%</td><td>2,5%</td><td>R$ 100,50</td>
                    </tr>
                </tbody>
            </table>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        repo = FIIRepository()
        fiis = repo.get_all()

        self.assertEqual(len(fiis), 1)
        fii = fiis[0]
        self.assertEqual(fii.ticker, "TEST11")
        self.assertEqual(fii.sector, "Logística")
        self.assertEqual(fii.liquidity, 1000.0)
        self.assertEqual(fii.pvp, 0.95)
        self.assertEqual(fii.dividend_yield, 10.5)
        self.assertEqual(fii.vacancia, 2.5)
        self.assertEqual(fii.price, 100.50)

if __name__ == '__main__':
    unittest.main()
