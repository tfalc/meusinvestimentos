# fii_analyzer/adapters/outputs/fii_console_outputs.py

from core.entities.fii import FII


class FIIConsoleOutputs:
    def display(self, fiis: list[FII], message: str):
        print(message)
        if not fiis:
            print("Nenhum FII foi encontrado com os critérios especificados.")
        else:
            print(f"{'Ticker':<8} | {'Preço':<10} | {'DY (%)':<8} | {'P/VP':<6} | {'Vacância (%)':<12} | {'Setor'}")
            print("-" * 80)
            for fii in fiis:
                print(
                    f"{fii.ticker:<8} | R${fii.price:<8.2f} | {fii.dividend_yield:<8.2f} | {fii.pvp:<6.2f} | {fii.vacancia:<12.2f} | {fii.sector}"
                )
