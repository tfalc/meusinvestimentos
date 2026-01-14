from bs4 import BeautifulSoup
import requests
from core.entities.fii import FII
import logging

class FIIRepository:
    def get_all(self) -> list[FII]:
        url = "https://www.fundsexplorer.com.br/ranking"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Erro ao acessar {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", class_="default-fiis-table__container__table")
        if table is None:
            # Tenta encontrar qualquer tabela se a classe específica falhar
            table = soup.find("table")
            if table is None:
                logging.error("Tabela de FIIs não encontrada na página.")
                return []

        headers_row = table.find("thead").find_all("th")
        col_map = self._map_columns(headers_row)

        if 'ticker' not in col_map:
             logging.error("Coluna de Ticker não encontrada.")
             return []

        rows = table.find("tbody").find_all("tr")
        fiis = []

        for row in rows:
            columns = row.find_all("td")
            try:
                ticker = self._get_text(columns, col_map.get('ticker'))
                sector = self._get_text(columns, col_map.get('sector'))
                price = self._parse_float(self._get_text(columns, col_map.get('price')))
                liquidity = self._parse_float(self._get_text(columns, col_map.get('liquidity')))
                pvp = self._parse_float(self._get_text(columns, col_map.get('pvp')))
                dividend_yield = self._parse_float(self._get_text(columns, col_map.get('dy')))
                vacancia = self._parse_float(self._get_text(columns, col_map.get('vacancia')))

                fiis.append(
                    FII(
                        ticker=ticker,
                        price=price,
                        dividend_yield=dividend_yield,
                        pvp=pvp,
                        sector=sector,
                        liquidity=liquidity,
                        vacancia=vacancia,
                    )
                )
            except Exception as e:
                # Log leve para debug, mas continua processamento
                continue

        return fiis

    def _map_columns(self, headers) -> dict:
        mapping = {}
        for i, header in enumerate(headers):
            text = header.get_text().strip().lower()
            if "código" in text or "fundo" in text:
                mapping['ticker'] = i
            elif "setor" in text:
                mapping['sector'] = i
            elif "preço atual" in text:
                mapping['price'] = i
            elif "liquidez" in text:
                mapping['liquidity'] = i
            elif "dividend yield" in text:
                mapping['dy'] = i
            elif "p/vp" in text:
                mapping['pvp'] = i
            elif "vacância física" in text:
                mapping['vacancia'] = i
        return mapping

    def _get_text(self, columns, index):
        if index is None or index >= len(columns):
            return ""
        return columns[index].text.strip()

    def _parse_float(self, text: str) -> float:
        if not text or text == "N/A":
            return 0.0
        try:
            # Remove caracteres não numéricos exceto . e ,
            clean_text = text.replace("R$", "").replace("%", "").strip()
            # Remove pontos de milhar e troca vírgula decimal por ponto
            clean_text = clean_text.replace(".", "").replace(",", ".")
            return float(clean_text)
        except ValueError:
            return 0.0
