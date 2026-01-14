import pandas as pd
import requests
import logging
from io import StringIO
from core.entities.fii import FII

class FundamentusRepository:
    def get_all(self) -> list[FII]:
        url = "https://www.fundamentus.com.br/fii_resultado.php"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            # O Fundamentus retorna uma tabela HTML simples, ideal para pd.read_html
            # Precisamos passar o header simulando um browser para não sermos bloqueados
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Corrige FutureWarning usando StringIO
            html_content = StringIO(response.text)
            
            # Lê todas as tabelas da página
            dfs = pd.read_html(html_content, decimal=",", thousands=".")
            
            if not dfs:
                logging.error("Nenhuma tabela encontrada no Fundamentus.")
                return []
                
            df = dfs[0]
            
            # Mapeamento e limpeza
            fiis = []
            
            # Colunas esperadas no Fundamentus:
            # Papel, Segmento, Cotação, FFO Yield, Dividend Yield, P/VP, Valor de Mercado, Liquidez, Qtd de imóveis, Preço do m2, Aluguel do m2, Cap Rate, Vacância Média
            
            for _, row in df.iterrows():
                try:
                    ticker = str(row.get('Papel', '')).strip()
                    sector = str(row.get('Segmento', '')).strip()
                    
                    price = self._clean_float(row.get('Cotação', 0))
                    dy = self._clean_float(row.get('Dividend Yield', 0)) # Já vem em %? O pandas costuma converter se tiver decimal=","
                    pvp = self._clean_float(row.get('P/VP', 0))
                    liquidity = self._clean_float(row.get('Liquidez', 0))
                    vacancia = self._clean_float(row.get('Vacância Média', 0))
                    
                    # No Fundamentus, DY e Vacância vêm como string "12,00%" se não for tratado,
                    # mas o read_html com decimal="," ajuda. Se vier string com %, precisamos limpar.
                    if isinstance(row.get('Dividend Yield'), str) and '%' in row.get('Dividend Yield'):
                         dy = self._parse_pct(row.get('Dividend Yield'))
                    
                    if isinstance(row.get('Vacância Média'), str) and '%' in row.get('Vacância Média'):
                         vacancia = self._parse_pct(row.get('Vacância Média'))

                    fiis.append(
                        FII(
                            ticker=ticker,
                            price=price,
                            dividend_yield=dy,
                            pvp=pvp,
                            sector=sector,
                            liquidity=liquidity,
                            vacancia=vacancia
                        )
                    )
                except Exception as e:
                    logging.warning(f"Erro ao processar linha do Fundamentus para {row.get('Papel')}: {e}")
                    continue
                    
            return fiis

        except Exception as e:
            logging.error(f"Erro ao acessar Fundamentus: {e}")
            return []

    def _clean_float(self, value) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
            value = value.replace('R$', '').replace('%', '')
            try:
                return float(value)
            except:
                return 0.0
        return 0.0

    def _parse_pct(self, value: str) -> float:
        if not value: return 0.0
        return self._clean_float(value)
