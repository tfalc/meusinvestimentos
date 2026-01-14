from typing import List, Dict, Any, Optional
from core.entities.fii import FII
from core.entities.portfolio import PortfolioItem

class SmartAnalysisService:
    def analyze_fii(self, fii: FII, portfolio_items: Optional[List[PortfolioItem]] = None) -> Dict[str, Any]:
        """
        Calcula um 'Smart Score' (0-100) e gera uma análise em texto usando heurísticas avançadas.
        Simula uma análise de IA baseada em regras de mercado, considerando a carteira atual.
        """
        score = 0
        reasons = []
        tags = []
        
        # Obter contexto da carteira
        in_portfolio = False
        portfolio_sectors = set()
        
        if portfolio_items:
            in_portfolio = any(item.ticker == fii.ticker for item in portfolio_items)
            # Para identificar setores da carteira, precisaríamos cruzar dados.
            # Como aqui recebemos apenas fii atual e a lista de itens (que só tem ticker),
            # vamos assumir que a diversificação será calculada no método recommend ou 
            # passada como parâmetro extra se quiséssemos precisão absoluta de setores.
            # Por simplicidade, vamos focar no "in_portfolio" aqui.

        # 1. Análise de P/VP (Peso 30)
        if 0.8 <= fii.pvp <= 1.05:
            score += 30
            reasons.append("Preço justo ou descontado (Bom P/VP).")
        elif 0.7 <= fii.pvp < 0.8:
            score += 20
            reasons.append("Muito descontado, mas atenção ao risco.")
        elif 1.05 < fii.pvp <= 1.2:
            score += 15
            reasons.append("Leve ágio, aceitável para fundos de tijolo premium.")
        else:
            score += 0
            reasons.append("Preço descolado do valor patrimonial (Risco).")

        # 2. Análise de Dividend Yield (Peso 30)
        if 9.0 <= fii.dividend_yield <= 16.0:
            score += 30
            reasons.append("Yield excelente e sustentável.")
        elif 6.0 <= fii.dividend_yield < 9.0:
            score += 20
            reasons.append("Yield conservador.")
        elif fii.dividend_yield > 16.0:
            score += 15
            reasons.append("Yield suspeitamente alto (Risco de não recorrência).")
        else:
            score += 5
            reasons.append("Yield baixo para a renda variável.")

        # 3. Liquidez (Peso 20)
        if fii.liquidity > 1_000_000:
            score += 20
            reasons.append("Altíssima liquidez.")
        elif fii.liquidity > 200_000:
            score += 15
            reasons.append("Liquidez adequada para investidor varejo.")
        else:
            score += 5
            reasons.append("Baixa liquidez (dificuldade de saída).")

        # 4. Vacância (Peso 20)
        if fii.vacancia <= 5.0:
            score += 20
            reasons.append("Vacância controlada (Ocupação alta).")
        elif 5.0 < fii.vacancia <= 15.0:
            score += 10
            reasons.append("Vacância moderada, exige monitoramento.")
        else:
            score += 0
            reasons.append("Vacância alta (Imóveis vagos pressionam custos).")

        # 5. Bônus de Carteira e Estratégia (IA Contextual)
        if in_portfolio:
            # Se já tenho e é bom (score base alto), incentivar aumento de posição
            if score >= 60:
                score += 10 # Boost para reforçar posição vencedora
                score = min(score, 100) # Cap em 100
                reasons.append("Já está na sua carteira (Oportunidade de aumentar posição).")
                tags.append("Aumentar Posição")
        
        # Gerar Texto da "IA"
        sentiment = "Neutro"
        if score >= 80:
            sentiment = "Altamente Recomendado (Compra Forte)"
        elif score >= 60:
            sentiment = "Recomendado (Compra)"
        elif score >= 40:
            sentiment = "Observação (Neutro)"
        else:
            sentiment = "Não Recomendado (Venda/Evitar)"

        analysis_text = f"🤖 **Análise Inteligente:** O fundo apresenta um score de **{score}/100** ({sentiment}). "
        analysis_text += " ".join(reasons)

        return {
            "score": score,
            "sentiment": sentiment,
            "analysis_text": analysis_text,
            "details": reasons,
            "tags": tags,
            "in_portfolio": in_portfolio
        }

    def recommend_allocation(self, all_fiis: List[FII], current_portfolio: List[PortfolioItem], monthly_contribution: float, target_income: float) -> Dict[str, Any]:
        """
        Gera uma recomendação de alocação de ativos baseada em score e diversificação.
        Retorna uma carteira sugerida e projeções.
        """
        # 1. Avaliar todos os FIIs disponíveis
        scored_fiis = []
        for fii in all_fiis:
            analysis = self.analyze_fii(fii, current_portfolio)
            scored_fiis.append({
                'fii': fii,
                'score': analysis['score'],
                'analysis': analysis
            })
        
        # 2. Filtrar apenas os "Bons" (Score >= 60) e Ordenar
        # Prioriza Score alto, depois Yield, depois Liquidez
        best_fiis = sorted(
            [item for item in scored_fiis if item['score'] >= 60],
            key=lambda x: (x['score'], x['fii'].dividend_yield),
            reverse=True
        )

        # 3. Seleção Inteligente (Top Picks diversificados)
        # Tenta pegar top 10, garantindo max 2 por setor se possível
        selected_allocation = []
        sectors_count = {}
        
        # Primeiro, garante que os bons que o usuário JÁ TEM estejam na lista (reforço de posição)
        current_tickers = {item.ticker for item in current_portfolio}
        for item in best_fiis:
            fii = item['fii']
            if fii.ticker in current_tickers:
                selected_allocation.append(item)
                sectors_count[fii.sector] = sectors_count.get(fii.sector, 0) + 1
        
        # Depois preenche com novas oportunidades até completar ex: 10 ativos
        target_size = max(10, len(selected_allocation) + 5)
        
        for item in best_fiis:
            if len(selected_allocation) >= target_size:
                break
            
            fii = item['fii']
            # Se já pegamos, pula
            if any(s['fii'].ticker == fii.ticker for s in selected_allocation):
                continue
                
            # Controle de diversificação (max 3 por setor na sugestão)
            if sectors_count.get(fii.sector, 0) < 3:
                selected_allocation.append(item)
                sectors_count[fii.sector] = sectors_count.get(fii.sector, 0) + 1
        
        # 4. Cálculo de Pesos (Alocação)
        # Distribuição baseada no Score: Score maior = maior peso
        total_score = sum(item['score'] for item in selected_allocation)
        if total_score == 0: return {} # Fallback

        allocation_plan = []
        avg_yield_monthly = 0
        
        for item in selected_allocation:
            weight = item['score'] / total_score
            fii = item['fii']
            
            # Yield mensal aproximado (DY anual / 12)
            dy_monthly_decimal = (fii.dividend_yield / 100) / 12
            avg_yield_monthly += dy_monthly_decimal * weight
            
            allocation_plan.append({
                'ticker': fii.ticker,
                'sector': fii.sector,
                'price': fii.price,
                'weight': weight,
                'score': item['score'],
                'dy_anual': fii.dividend_yield,
                'reason': item['analysis']['analysis_text']
            })

        # 5. Projeção Temporal (Juros Compostos)
        # Meta: target_income
        # Variáveis: Patrimonio Inicial (aprox 0 para novos, ou atual), Aporte Mensal, Yield Médio
        
        # Calcular patrimonio atual do usuario
        current_equity = 0
        for p_item in current_portfolio:
            # Tenta achar preço atual na lista de all_fiis, senão usa medio
            fii_data = next((f for f in all_fiis if f.ticker == p_item.ticker), None)
            price = fii_data.price if fii_data else p_item.average_price
            current_equity += p_item.quantity * price

        months_to_goal = 0
        projected_equity = current_equity
        current_monthly_income = projected_equity * avg_yield_monthly
        
        projection_data = []
        
        # Simulação mês a mês (limite 30 anos = 360 meses para evitar loop infinito)
        while current_monthly_income < target_income and months_to_goal < 360:
            months_to_goal += 1
            # Renda é reinvestida + Aporte novo
            investment = current_monthly_income + monthly_contribution
            projected_equity += investment
            
            # Atualiza renda baseada no novo patrimonio
            current_monthly_income = projected_equity * avg_yield_monthly
            
            if months_to_goal % 6 == 0: # Grava a cada 6 meses para grafico
                projection_data.append({
                    'mes': months_to_goal,
                    'renda': current_monthly_income,
                    'patrimonio': projected_equity
                })

        return {
            'allocation_plan': allocation_plan,
            'avg_yield_monthly': avg_yield_monthly * 100, # %
            'months_to_goal': months_to_goal,
            'projected_equity_needed': projected_equity,
            'projection_data': projection_data,
            'current_equity': current_equity
        }

    def analyze_future_viability(self, fii: FII) -> Dict[str, Any]:
        """
        Gera uma análise preditiva sobre a viabilidade futura do FII e sua gestão,
        focando em riscos de liquidação e sustentabilidade do negócio.
        """
        risk_score = 0 # 0 (Seguro) a 100 (Risco Crítico)
        viability_text = []
        management_outlook = ""
        sector_outlook = ""
        
        # 1. Análise de "Quebra" ou Liquidação (P/VP e Liquidez)
        if fii.pvp < 0.60:
            risk_score += 40
            viability_text.append("🚨 **Risco de Liquidação:** O mercado precifica o ativo muito abaixo do valor patrimonial (P/VP < 0.6). Isso geralmente indica desconfiança grave na gestão ou na qualidade dos imóveis. Pode haver risco de liquidação ou amortização total.")
        elif fii.pvp < 0.80:
            risk_score += 20
            viability_text.append("⚠️ **Sinal de Alerta:** Desconto agressivo pode indicar problemas estruturais no fundo ou na tese de investimento da gestora.")
        
        if fii.liquidity < 10000:
            risk_score += 30
            viability_text.append("📉 **Ativo Zumbi:** Liquidez diária extremamente baixa. Risco de ficar 'preso' no ativo caso a gestora decida encerrar atividades ou o mercado perca interesse.")
            
        # 2. Análise de Gestão (Proxy via Vacância e Consistência)
        # Assumindo que vacância alta persistente é falha de gestão comercial
        if fii.vacancia > 25.0:
            risk_score += 25
            management_outlook = "A gestão enfrenta dificuldades severas para ocupar os imóveis. Isso pode indicar ativos obsoletos (má localização/qualidade) ou ineficiência comercial da administradora."
        elif fii.vacancia > 15.0:
            risk_score += 10
            management_outlook = "Desafio para a gestão: A vacância está acima da média de mercado, pressionando custos de condomínio/IPTU e reduzindo dividendos."
        elif fii.vacancia < 3.0:
            management_outlook = "Gestão Premium: A ocupação próxima de 100% demonstra excelente capacidade comercial e qualidade dos ativos geridos."
        else:
            management_outlook = "Gestão Estável: A vacância está dentro dos padrões aceitáveis de mercado, indicando uma administração competente."

        # 3. Perspectivas Setoriais (Cenários de Curto/Médio Prazo)
        # Baseado em conhecimento de mercado embutido
        sector = fii.sector.lower() if fii.sector else ""
        
        if "log" in sector or "ind" in sector:
            sector_outlook = "🏭 **Logística/Industrial:** Setor resiliente impulsionado pelo e-commerce. A tendência de médio prazo permanece positiva, mas a localização (Last Mile) será o diferencial entre fundos que crescem e os que estagnam."
        elif "shop" in sector:
            sector_outlook = "🛍️ **Shoppings:** Setor em recuperação pós-pandemia, mas sensível a juros altos (que reduzem consumo). A gestão precisa inovar em 'mix' de lojas e experiências para manter relevância contra o varejo digital."
        elif "laje" in sector or "escrit" in sector or "corp" in sector:
            sector_outlook = "🏢 **Lajes Corporativas:** O setor vive um momento de transformação com o modelo híbrido. Fundos com ativos 'Triple A' em regiões prime (ex: Faria Lima) tendem a se valorizar, enquanto prédios antigos em regiões secundárias correm risco de obsolescência."
        elif "papel" in sector or "receb" in sector:
            sector_outlook = "📄 **Papel (Recebíveis):** Menor risco de vacância física, mas alto risco de crédito (calote dos CRIs). O foco da análise deve ser a qualidade da carteira de crédito da gestora, não o imóvel em si."
        elif "híbrido" in sector or "misto" in sector:
             sector_outlook = "🔄 **Híbrido:** A flexibilidade de mandato permite à gestão pivotar estratégias, o que é positivo em cenários voláteis. Depende inteiramente da habilidade de alocação de capital do gestor (Stock Picking)."
        else:
            sector_outlook = f"🔮 **Setor {fii.sector}:** Requer análise específica dos ativos subjacentes. Acompanhe relatórios gerenciais para entender a estratégia de reciclagem de portfólio."

        # Conclusão baseada no Score de Risco
        if risk_score >= 60:
            conclusion = "🔴 **CONCLUSÃO: ALTO RISCO.** A viabilidade de longo prazo deste FII é questionável baseada nos indicadores atuais. Há sinais que podem preceder uma liquidação ou perda permanente de capital."
        elif risk_score >= 30:
            conclusion = "🟡 **CONCLUSÃO: ATENÇÃO.** Existem pontos de fragilidade que exigem monitoramento próximo. A gestão precisará provar valor nos próximos 12-24 meses."
        else:
            conclusion = "🟢 **CONCLUSÃO: ROBUSTO.** Os indicadores sugerem uma operação saudável com boa perspectiva de continuidade no médio/longo prazo."

        return {
            "risk_score": risk_score,
            "viability_text": viability_text,
            "management_outlook": management_outlook,
            "sector_outlook": sector_outlook,
            "conclusion": conclusion
        }

    def recommend(self, fiis: List[FII], budget: float, min_liquidity: float = 0, portfolio_items: List[PortfolioItem] = []) -> List[Dict[str, Any]]:
        recommendations = []
        
        # Mapear setores já existentes na carteira para sugerir diversificação
        portfolio_tickers = {item.ticker for item in portfolio_items}
        portfolio_sectors = set()
        
        # Criar mapa rápido de FIIs do mercado para descobrir setores da carteira
        market_map = {f.ticker: f for f in fiis}
        
        for ticker in portfolio_tickers:
            if ticker in market_map:
                portfolio_sectors.add(market_map[ticker].sector)
        
        for fii in fiis:
            # Filtros Hard
            if fii.price <= budget and fii.liquidity >= min_liquidity:
                # Passamos items da carteira para análise individual
                analysis = self.analyze_fii(fii, portfolio_items)
                
                # Lógica de Diversificação (Se o setor não está na carteira, dá um boost pequeno)
                if fii.sector and fii.sector not in portfolio_sectors and analysis["score"] >= 60:
                     analysis["score"] += 5
                     analysis["score"] = min(analysis["score"], 100)
                     analysis["tags"].append("Diversificação (Novo Setor)")
                     analysis["analysis_text"] += " **Bônus de Diversificação:** Setor ainda não presente na sua carteira."

                if analysis["score"] >= 60:
                    recommendations.append({
                        "fii": fii,
                        **analysis
                    })
        
        # Ordenar:
        # 1. Score total (decrescente)
        # 2. Se já está na carteira (prioridade para reforçar posições boas) - False < True, então reverse=True coloca True primeiro? Não, True=1.
        #    Queremos priorizar carteira? O usuário disse "priorizar o que já existe".
        #    Então vamos usar in_portfolio como critério de desempate ou peso.
        
        recommendations.sort(key=lambda x: (
            x["score"], 
            x["in_portfolio"], # Prioriza quem já está na carteira se scores forem iguais/similares
            x["fii"].dividend_yield
        ), reverse=True)
        
        return recommendations
