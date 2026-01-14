# fii_analyzer/application/cli.py

import logging
from adapters.repositories.fii_repository import FIIRepository
from adapters.outputs.fii_console_outputs import FIIConsoleOutputs
from core.use_cases.analyze_buy import AnalyzeBuy
from core.use_cases.analyze_sell import AnalyzeSell


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        print("Iniciando análise de FIIs...")
        repository = FIIRepository()
        output = FIIConsoleOutputs()

        # Dados do repositório
        print("Obtendo dados dos FIIs (isso pode demorar um pouco)...")
        fiis = repository.get_all()
        
        if not fiis:
            print("Não foi possível obter dados dos FIIs. Verifique sua conexão ou os logs.")
            return

        print(f"Foram encontrados {len(fiis)} FIIs.")

        # Análise de Compra
        try:
            budget_input = input("Qual o valor disponível para aporte? R$")
            budget = float(budget_input.replace(",", "."))
        except ValueError:
            print("Valor inválido inserido.")
            return

        buy_analysis = AnalyzeBuy()
        recommended_fiis = buy_analysis.execute(fiis, budget)
        output.display(recommended_fiis, "\nFIIs recomendados para compra:")

        # Análise de Venda
        sell_analysis = AnalyzeSell()
        fiis_to_sell = sell_analysis.execute(fiis)
        output.display(fiis_to_sell, "\nFIIs recomendados para venda (DY < 6%, P/VP > 1.5 ou Vacância > 10%):")
        
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
