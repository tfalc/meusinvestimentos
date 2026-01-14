import sys
import os

# Adiciona o diretório raiz ao sys.path para permitir importações absolutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import altair as alt
from dataclasses import asdict
from adapters.repositories.fii_repository import FIIRepository
from adapters.repositories.fundamentus_repository import FundamentusRepository
from adapters.repositories.json_portfolio_repository import JsonPortfolioRepository
from core.services.portfolio_service import PortfolioService
from core.services.ai_analysis_service import SmartAnalysisService
from core.services.dividend_service import DividendService
from core.use_cases.analyze_buy import AnalyzeBuy
from core.use_cases.analyze_sell import AnalyzeSell
from core.entities.fii import FII

# Configuração da Página
st.set_page_config(
    page_title="Calculadora de FIIs",
    page_icon="🏢",
    layout="wide"
)

# Carregar Estilo CSS Externo
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

css_path = os.path.join(os.path.dirname(__file__), 'style.css')
load_css(css_path)

from core.services.auth_service import AuthService

# Inicialização de Estado da Sessão para Autenticação
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Serviço de Autenticação
auth_service = AuthService()

def login_page():
    st.title("🔐 Login Calculadora FII")
    
    tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
    
    with tab1:
        st.subheader("Acesse sua carteira")
        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar", type="primary"):
            if auth_service.login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
                
    with tab2:
        st.subheader("Novo Usuário")
        new_user = st.text_input("Escolha um Usuário", key="reg_user")
        new_pass = st.text_input("Escolha uma Senha", type="password", key="reg_pass")
        if st.button("Criar Conta"):
            if new_user and new_pass:
                if auth_service.register(new_user, new_pass):
                    st.success("Conta criada com sucesso! Vá para a aba 'Entrar'.")
                else:
                    st.error("Usuário já existe. Tente outro nome.")
            else:
                st.warning("Preencha todos os campos.")

if not st.session_state.authenticated:
    login_page()
    st.stop()

# Serviços (Instanciados com contexto do usuário)
portfolio_repository = JsonPortfolioRepository()
portfolio_service = PortfolioService(repository=portfolio_repository, user_id=st.session_state.username)
ai_service = SmartAnalysisService()
dividend_service = DividendService()

# Inicialização de Estado da Sessão
if 'show_add_modal' not in st.session_state:
    st.session_state.show_add_modal = False
if 'show_aporte_modal' not in st.session_state:
    st.session_state.show_aporte_modal = False
if 'editing_ticker' not in st.session_state:
    st.session_state.editing_ticker = None
if 'is_deleting' not in st.session_state:
    st.session_state.is_deleting = False
if 'fiis_to_delete' not in st.session_state:
    st.session_state.fiis_to_delete = []

# Função para carregar dados com cache
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_data(source="Fundamentus"):
    if source == "Fundamentus":
        repository = FundamentusRepository()
    else:
        repository = FIIRepository()
    return repository.get_all()

def render_portfolio_view(fiis):
    st.header("Minha Carteira")
    
    # Barra de Ações
    col_actions1, col_actions2 = st.columns([0.2, 0.8])
    with col_actions1:
        if st.button("➕ Adicionar FII", type="primary", use_container_width=True):
            st.session_state.show_add_modal = True
            st.rerun()
            
    with col_actions2:
        if not st.session_state.is_deleting:
            if st.button("🗑️ Gerenciar Carteira", use_container_width=False):
                st.session_state.is_deleting = True
                st.rerun()
        else:
            col_del1, col_del2 = st.columns([0.2, 0.8])
            with col_del1:
                if st.button("✅ Concluir Edição", type="primary"):
                    st.session_state.is_deleting = False
                    st.rerun()
            with col_del2:
                if st.session_state.fiis_to_delete:
                    if st.button(f"Excluir {len(st.session_state.fiis_to_delete)} Selecionados", type="secondary"):
                        for ticker in st.session_state.fiis_to_delete:
                            portfolio_service.remove_asset(ticker)
                        st.session_state.fiis_to_delete = []
                        st.session_state.is_deleting = False
                        st.success("Ativos removidos com sucesso!")
                        st.rerun()

    # Modal de Adicionar Novo Ativo
    if st.session_state.show_add_modal:
        with st.container():
            st.markdown("### 📝 Adicionar Novo Ativo")
            with st.form("add_fii_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    ticker_input = st.text_input("Ticker (ex: HGLG11)").upper()
                with c2:
                    qtd_input = st.number_input("Quantidade", min_value=1, step=1, value=10)
                with c3:
                    pm_input = st.number_input("Preço Médio (R$)", min_value=0.0, step=0.1, value=100.0)
                
                col_btn1, col_btn2 = st.columns([0.2, 0.8])
                with col_btn1:
                    submitted = st.form_submit_button("Salvar")
                with col_btn2:
                    if st.form_submit_button("Cancelar"):
                        st.session_state.show_add_modal = False
                        st.rerun()

                if submitted:
                    if ticker_input:
                        portfolio_service.add_asset(ticker_input, qtd_input, pm_input)
                        st.success(f"{ticker_input} adicionado com sucesso!")
                        st.session_state.show_add_modal = False
                        st.rerun()
                    else:
                        st.warning("O campo Ticker é obrigatório.")
            st.markdown("---")

    # Carregar Carteira e Dados de Mercado
    portfolio_items = portfolio_service.load_portfolio()
    market_map = {f.ticker: f for f in fiis}

    # Modal de Aporte (Se acionado)
    if st.session_state.show_aporte_modal and st.session_state.editing_ticker:
        ticker = st.session_state.editing_ticker
        market_data = market_map.get(ticker)
        current_price = market_data.price if market_data else 0.0
        
        with st.container():
            st.markdown(f"### 💰 Registrar Operação em {ticker}")
            with st.form("aporte_form"):
                st.info(f"Preço Atual de Mercado: R$ {current_price:.2f}")
                
                # Tipo de Operação
                tipo_operacao = st.radio("Tipo de Operação", ["Compra", "Venda"], horizontal=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    qtd_aporte = st.number_input("Quantidade", min_value=1, step=1, value=1)
                with c2:
                    label_preco = "Preço Pago (R$)" if tipo_operacao == "Compra" else "Preço de Venda (R$)"
                    preco_aporte = st.number_input(label_preco, min_value=0.0, step=0.01, value=current_price)
                
                col_btn1, col_btn2 = st.columns([0.2, 0.8])
                with col_btn1:
                    confirm_aporte = st.form_submit_button("Confirmar")
                with col_btn2:
                    if st.form_submit_button("Cancelar"):
                        st.session_state.show_aporte_modal = False
                        st.session_state.editing_ticker = None
                        st.rerun()
                
                if confirm_aporte:
                    try:
                        if tipo_operacao == "Compra":
                            # Adiciona asset (a lógica do service já calcula o preço médio ponderado)
                            portfolio_service.add_asset(ticker, qtd_aporte, preco_aporte)
                            st.success(f"Aporte em {ticker} registrado com sucesso!")
                        else:
                            # Venda parcial
                            portfolio_service.sell_asset(ticker, qtd_aporte, preco_aporte)
                            st.success(f"Venda de {ticker} registrada com sucesso!")
                            
                        st.session_state.show_aporte_modal = False
                        st.session_state.editing_ticker = None
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            st.markdown("---")

    if not portfolio_items:
        st.info("Sua carteira está vazia. Clique em 'Adicionar FII' para começar.")
        return

    # Métricas Globais (Segmented Button Style)
    total_investido = sum(item.quantity * item.average_price for item in portfolio_items)
    total_atual = sum(item.quantity * (market_map[item.ticker].price if item.ticker in market_map else 0) for item in portfolio_items)
    rentabilidade_total = ((total_atual - total_investido) / total_investido * 100) if total_investido > 0 else 0
    lucro_total = total_atual - total_investido
    
    delta_color = "#4CAF50" if lucro_total >= 0 else "#EF5350"
    delta_symbol = "▲" if lucro_total >= 0 else "▼"
    rent_color = delta_color

    st.markdown(f"""
    <div class="metrics-container">
        <div class="metric-item">
            <span class="metric-label">Patrimônio Total</span>
            <span class="metric-value">R$ {total_atual:,.2f}</span>
            <span class="metric-delta" style="color: {delta_color}">{delta_symbol} R$ {abs(lucro_total):,.2f}</span>
        </div>
        <div class="metric-divider"></div>
        <div class="metric-item">
            <span class="metric-label">Total Investido</span>
            <span class="metric-value">R$ {total_investido:,.2f}</span>
        </div>
        <div class="metric-divider"></div>
        <div class="metric-item">
            <span class="metric-label">Rentabilidade Geral</span>
            <span class="metric-value" style="color: {rent_color}">{rentabilidade_total:.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📜 Seus Ativos")

    # Grid Layout (Cards)
    cols_per_row = 3
    chunks = [portfolio_items[i:i + cols_per_row] for i in range(0, len(portfolio_items), cols_per_row)]

    for chunk in chunks:
        cols = st.columns(cols_per_row)
        for idx, item in enumerate(chunk):
            with cols[idx]:
                market_data = market_map.get(item.ticker)
                current_price = market_data.price if market_data else 0.0
                dy = market_data.dividend_yield if market_data else 0.0
                pvp = market_data.pvp if market_data else 0.0
                vacancia = market_data.vacancia if market_data else 0.0
                
                valor_atual = item.quantity * current_price
                rent_pct = ((current_price - item.average_price) / item.average_price * 100) if item.average_price > 0 else 0
                
                # Container estilizado simulando Card
                with st.container(border=True):
                    # 1. Header Visual (Background + Título + Botão)
                    # Background Absolute
                    st.markdown(f'<div class="card-header-bg"></div>', unsafe_allow_html=True)
                    
                    # Layout em Colunas sobre o Background
                    # c_h1: Título (Esquerda)
                    # c_h2: Botão (Direita)
                    c_h1, c_h2 = st.columns([0.65, 0.35])
                    
                    with c_h1:
                        # Espaçador de padding left manual para não colar na borda
                        st.markdown(f'<div style="padding-left: 10px;"><div class="card-header-text">{item.ticker}</div></div>', unsafe_allow_html=True)
                    
                    with c_h2:
                        # Âncora CSS removida pois vamos usar seletor de classe parcial na key
                        if st.button("🔄 Operar", key=f"add_{item.ticker}", help="Registrar Aporte ou Venda"):
                             st.session_state.editing_ticker = item.ticker
                             st.session_state.show_aporte_modal = True
                             st.rerun()

                    # 3. Botão de Deletar (X vermelho) se ativo
                    if st.session_state.is_deleting:
                        st.markdown('<div class="delete-btn-container">', unsafe_allow_html=True)
                        if st.button("✕", key=f"del_{item.ticker}", help="Excluir Ativo"):
                             portfolio_service.remove_asset(item.ticker)
                             st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                    # 4. Spacer e Conteúdo
                    # Empurra o conteúdo para baixo para não sobrepor o header de 80px
                    st.markdown('<div class="card-content-spacer" style="height: 80px;"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="card-content">', unsafe_allow_html=True)
                    
                    m_c1, m_c2, m_c3 = st.columns(3)
                    m_c1.metric("Preço", f"R$ {current_price:.2f}")
                    m_c2.metric("Quantidade", f"{item.quantity}")
                    m_c3.metric("Posição", f"R$ {valor_atual:,.2f}", delta=f"{rent_pct:.2f}%")
                    
                    # Análise Inteligente
                    ai_analysis = ai_service.analyze_fii(market_data) if market_data else None
                    if ai_analysis:
                        score = ai_analysis['score']
                        rec_label = "MANTER" if score >= 50 else "VENDER"
                        color = "#03DAC6" if score >= 50 else "#CF6679"
                        
                        # Usando variáveis CSS para cores adaptativas
                        st.markdown(f"""
                        <div style="background-color: var(--metric-bg); padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid var(--metric-border);">
                            <div style="font-size: 0.75rem; color: var(--text-color-secondary); text-transform: uppercase;">Smart Score</div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                                <span style="font-size: 1.3rem; font-weight: bold; color: var(--text-color-primary);">{score}/100</span>
                                <span style="color: {color}; font-weight: bold; border: 1px solid {color}; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">{rec_label}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Dados indisponíveis para análise.")
                    
                    st.markdown('</div>', unsafe_allow_html=True) # End card-content

                    # Expander para detalhes
                    with st.expander("Ver Detalhes"):
                        tab_pos, tab_fund, tab_ai, tab_hist = st.tabs(["Minha Posição", "Indicadores", "🤖 Análise IA", "📜 Histórico"])
                        with tab_pos:
                            st.write(f"**Quantidade:** {item.quantity}")
                            st.write(f"**PM:** R$ {item.average_price:.2f}")
                            st.write(f"**Lucro/Prej:** R$ {valor_atual - (item.quantity * item.average_price):.2f}")
                        with tab_fund:
                            if market_data:
                                st.write(f"**DY:** {dy:.2f}%")
                                st.write(f"**P/VP:** {pvp:.2f}")
                                st.write(f"**Vacância:** {vacancia:.2f}%")
                                st.write(f"**Liquidez:** R$ {market_data.liquidity:,.0f}")
                        with tab_ai:
                            if ai_analysis:
                                st.markdown(f"**Sentimento:** {ai_analysis['sentiment']}")
                                st.info(ai_analysis['analysis_text'])
                        with tab_hist:
                            transactions = portfolio_service.get_transactions(item.ticker)
                            if transactions:
                                df_hist = pd.DataFrame([asdict(t) for t in transactions])
                                
                                # Traduzir Tipos
                                df_hist['type'] = df_hist['type'].map({'BUY': 'Compra', 'SELL': 'Venda'})
                                
                                # Formatação
                                df_hist['date'] = pd.to_datetime(df_hist['date']).dt.strftime('%d/%m/%Y %H:%M')
                                df_hist.rename(columns={
                                    'date': 'Data',
                                    'quantity': 'Qtd',
                                    'price': 'Preço (R$)',
                                    'type': 'Tipo'
                                }, inplace=True)
                                
                                st.dataframe(
                                    df_hist[['Data', 'Tipo', 'Qtd', 'Preço (R$)']], 
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                # Gráfico de Evolução do Preço
                                if len(transactions) > 1:
                                    chart_data = pd.DataFrame([asdict(t) for t in transactions])
                                    chart_data['date'] = pd.to_datetime(chart_data['date'])
                                    # Traduzir para tooltip e cor
                                    chart_data['Operação'] = chart_data['type'].map({'BUY': 'Compra', 'SELL': 'Venda'})
                                    
                                    # Inject Theme Colors
                                    current_theme_colors = THEMES[theme]
                                    chart_color = current_theme_colors['text_color_primary']
                                    # Use different colors for Buy/Sell if possible, or just points
                                    
                                    base_chart = alt.Chart(chart_data).encode(
                                        x=alt.X('date', title='Data', axis=alt.Axis(format='%d/%m/%Y', labelColor=chart_color, titleColor=chart_color)),
                                        y=alt.Y('price', title='Preço (R$)', scale=alt.Scale(zero=False), axis=alt.Axis(labelColor=chart_color, titleColor=chart_color)),
                                        tooltip=[
                                            alt.Tooltip('date', title='Data', format='%d/%m/%Y'),
                                            alt.Tooltip('Operação', title='Operação'),
                                            alt.Tooltip('price', title='Preço', format='R$ .2f'),
                                            alt.Tooltip('quantity', title='Qtd')
                                        ]
                                    )
                                    
                                    # Line connection
                                    line = base_chart.mark_line(color=current_theme_colors['accent_color'])
                                    
                                    # Points colored by type
                                    points = base_chart.mark_circle(size=100).encode(
                                        color=alt.Color('Operação', scale=alt.Scale(domain=['Compra', 'Venda'], range=['#4CAF50', '#EF5350']), legend=alt.Legend(title="Operação", titleColor=chart_color, labelColor=chart_color))
                                    )
                                    
                                    final_chart = (line + points).properties(
                                        height=200,
                                        title=alt.TitleParams(text='Histórico de Execução', color=chart_color)
                                    ).configure_view(
                                        strokeWidth=0
                                    )
                                    st.altair_chart(final_chart, use_container_width=True)
                            else:
                                st.info("Nenhum histórico de transações registrado para este ativo.")

# Theme Definitions
THEMES = {
    "Escuro (Padrão)": {
        "bg_color_primary": "#0E1117",
        "bg_color_secondary": "#262730",
        "text_color_primary": "#FAFAFA",
        "text_color_secondary": "#B0B0B0",
        "sidebar_bg": "#121212",
        "card_bg": "#1E1E1E",
        "card_border": "#333333",
        "card_shadow": "rgba(0, 0, 0, 0.3)",
        "accent_color": "#BB86FC",
        "accent_color_hover": "rgba(187, 134, 252, 0.1)",
        "metric_bg": "#2D2D2D",
        "metric_border": "#404040",
        "metric_divider": "#555555",
        "header_text_color": "#FFFFFF",
        "card_header_text": "#121212"
    },
    "Claro": {
        "bg_color_primary": "#FFFFFF",
        "bg_color_secondary": "#F0F2F6",
        "text_color_primary": "#31333F",
        "text_color_secondary": "#555555",
        "sidebar_bg": "#F8F9FB",
        "card_bg": "#FFFFFF",
        "card_border": "#E0E0E0",
        "card_shadow": "rgba(0, 0, 0, 0.1)",
        "accent_color": "#6200EE",
        "accent_color_hover": "rgba(98, 0, 238, 0.1)",
        "metric_bg": "#F0F2F6",
        "metric_border": "#D1D5DB",
        "metric_divider": "#D1D5DB",
        "header_text_color": "#31333F",
        "card_header_text": "#FFFFFF"
    },
    "Dracula": {
        "bg_color_primary": "#282a36",
        "bg_color_secondary": "#44475a",
        "text_color_primary": "#f8f8f2",
        "text_color_secondary": "#6272a4",
        "sidebar_bg": "#21222c",
        "card_bg": "#44475a",
        "card_border": "#6272a4",
        "card_shadow": "rgba(0, 0, 0, 0.3)",
        "accent_color": "#bd93f9",
        "accent_color_hover": "rgba(189, 147, 249, 0.1)",
        "metric_bg": "#282a36",
        "metric_border": "#6272a4",
        "metric_divider": "#6272a4",
        "header_text_color": "#ff79c6",
        "card_header_text": "#282a36"
    },
    "Midnight Blue": {
        "bg_color_primary": "#0f172a",
        "bg_color_secondary": "#1e293b",
        "text_color_primary": "#e2e8f0",
        "text_color_secondary": "#94a3b8",
        "sidebar_bg": "#020617",
        "card_bg": "#1e293b",
        "card_border": "#334155",
        "card_shadow": "rgba(0, 0, 0, 0.4)",
        "accent_color": "#38bdf8",
        "accent_color_hover": "rgba(56, 189, 248, 0.1)",
        "metric_bg": "#0f172a",
        "metric_border": "#334155",
        "metric_divider": "#475569",
        "header_text_color": "#38bdf8",
        "card_header_text": "#0f172a"
    }
}

def apply_theme(theme_name):
    theme = THEMES.get(theme_name, THEMES["Escuro (Padrão)"])
    css = f"""
<style>
    :root {{
        --bg-color-primary: {theme['bg_color_primary']};
        --bg-color-secondary: {theme['bg_color_secondary']};
        --text-color-primary: {theme['text_color_primary']};
        --text-color-secondary: {theme['text_color_secondary']};
        
        --sidebar-bg: {theme['sidebar_bg']};
        --card-bg: {theme['card_bg']};
        --card-border: {theme['card_border']};
        --card-shadow: {theme['card_shadow']};
        
        --accent-color: {theme['accent_color']};
        --accent-color-hover: {theme['accent_color_hover']};
        
        --metric-bg: {theme['metric_bg']};
        --metric-border: {theme['metric_border']};
        --metric-divider: {theme['metric_divider']};
        
        --header-text-color: {theme['header_text_color']};
        --card-header-text: {theme['card_header_text']};
    }}
    
    /* Force styles on Streamlit elements */
    .stApp {{
        background-color: var(--bg-color-primary);
        color: var(--text-color-primary);
    }}
    
    section[data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg);
    }}
    
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: var(--text-color-primary) !important;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: var(--header-text-color) !important;
    }}
    
    p, .stMarkdown, .stText {{
        color: var(--text-color-primary) !important;
    }}
    
    /* Ajuste específico para garantir que headers de metrics fiquem legíveis */
    div[data-testid="stMetricLabel"] label {{
        color: var(--text-color-secondary) !important;
    }}
    
    div[data-testid="stMetricValue"] {{
        color: var(--text-color-primary) !important;
    }}
</style>
"""
    if theme_name == "Claro":
        css += """
<style>
    /* Invert Dataframe colors for Light theme if base is Dark */
    div[data-testid="stDataFrame"] {
        filter: invert(1) hue-rotate(180deg);
    }
    /* Prevent inversion of specific content if needed, but usually fine for text */
    
    /* Adjust scrollbars for inverted view if visible */
</style>
"""

    st.markdown(css, unsafe_allow_html=True)

def main():
    # Theme Selection
    theme_options = list(THEMES.keys())
    theme = st.sidebar.selectbox("Tema", theme_options, index=0)
    apply_theme(theme)
    
    # Sidebar Navigation
    if 'page' not in st.session_state:
        st.session_state.page = "Minha Carteira"

    st.sidebar.header("Navegação")
    
    # Menu com Botões Estilizados
    menu_options = [
        {"label": "Minha Carteira", "icon": "💼"},
        {"label": "Visão Geral", "icon": "📊"},
        {"label": "Oportunidades", "icon": "🚀"},
        {"label": "Alertas", "icon": "⚠️"},
        {"label": "Proventos", "icon": "💰"}
    ]

    for option in menu_options:
        label = option["label"]
        icon = option["icon"]
        button_label = f"{icon}  {label}"
        
        # Define o tipo de botão baseado na página ativa
        btn_type = "primary" if st.session_state.page == label else "secondary"
        
        if st.sidebar.button(button_label, key=f"nav_{label}", use_container_width=True, type=btn_type):
            st.session_state.page = label
            st.rerun()
    
    page = st.session_state.page
    
    st.sidebar.markdown("---")
    
    # User Profile & Logout
    st.sidebar.caption(f"Logado como: **{st.session_state.username}**")
    if st.sidebar.button("🚪 Sair", key="logout_btn"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("Configurações")
    data_source = st.sidebar.selectbox("Fonte de Dados", ["Fundamentus", "FundsExplorer"])

    # Carregamento de Dados
    with st.spinner(f"Carregando dados dos FIIs via {data_source}..."):
        try:
            fiis = load_data(data_source)
            if not fiis:
                st.error("Falha ao carregar dados. Verifique a conexão.")
                return
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return

    # Roteamento de Páginas
    if page == "Minha Carteira":
        render_portfolio_view(fiis)
    
    elif page == "Visão Geral":
        st.header("📊 Visão Geral do Mercado")
        df = pd.DataFrame([vars(f) for f in fiis])
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de FIIs", len(fiis))
        col2.metric("Média de DY", f"{df['dividend_yield'].mean():.2f}%")
        col3.metric("Média de P/VP", f"{df['pvp'].mean():.2f}")
        st.dataframe(df, use_container_width=True)

    elif page == "Oportunidades":
        st.header("💰 Oportunidades de Compra com IA")
        st.markdown("A inteligência artificial analisa múltiplos fatores (DY, P/VP, Vacância, Liquidez) para recomendar os melhores ativos.")
        
        col1, col2 = st.columns(2)
        with col1:
            budget = st.number_input("Orçamento (R$)", value=100.0, step=50.0)
            min_liq = st.number_input(
                "Liquidez Mínima (R$)", 
                value=50000.0, 
                step=10000.0,
                help="Liquidez é a facilidade de vender o ativo. Valores acima de R$ 200 mil/dia são recomendados para garantir que você consiga vender suas cotas rapidamente se precisar."
            )
        with col2:
            st.info("A análise IA considera P/VP ideal entre 0.8 e 1.2, DY sustentável e Baixa Vacância.")
        
        if st.button("🤖 Executar Smart Analysis"):
            # ai_service já instanciado globalmente
            portfolio_items = portfolio_service.load_portfolio() # Carrega a carteira atual
            recommendations = ai_service.recommend(fiis, budget, min_liq, portfolio_items)
            
            if recommendations:
                st.success(f"A IA encontrou {len(recommendations)} oportunidades promissoras.")
                
                for rec in recommendations:
                    fii = rec["fii"]
                    
                    # Tags visuais
                    title_badges = ""
                    if "in_portfolio" in rec and rec["in_portfolio"]:
                        title_badges += " 💼 [Na Carteira]"
                    if "tags" in rec:
                        for tag in rec["tags"]:
                            title_badges += f" ✨ [{tag}]"

                    with st.expander(f"🏆 {fii.ticker} {title_badges} - Score: {rec['score']}/100 ({rec['sentiment']})"):
                        st.markdown(rec["analysis_text"])
                        
                        # Métricas principais
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Preço", f"R$ {fii.price:.2f}")
                        m2.metric("DY", f"{fii.dividend_yield:.2f}%")
                        m3.metric("P/VP", f"{fii.pvp:.2f}")
                        m4.metric("Vacância", f"{fii.vacancia:.2f}%")
                        
                        st.caption(f"Setor: {fii.sector} | Liquidez: R$ {fii.liquidity:,.0f}")

            else:
                st.warning("Nenhum FII atendeu aos critérios mínimos de segurança da IA com esse orçamento.")

    elif page == "Alertas":
        st.header("⚠️ Monitoramento de Riscos (IA + Carteira)")
        
        portfolio_items = portfolio_service.load_portfolio()
        if not portfolio_items:
            st.warning("Você ainda não possui FIIs na carteira para monitorar.")
        else:
            my_tickers = [item.ticker for item in portfolio_items]
            my_fiis = [f for f in fiis if f.ticker in my_tickers]
            
            st.info(f"Monitorando {len(my_fiis)} ativos da sua carteira.")

            # Configurações Manuais (Expander para não poluir)
            with st.expander("⚙️ Configurar Critérios Manuais de Alerta", expanded=False):
                c1, c2, c3 = st.columns(3)
                min_dy = c1.number_input("Min DY (%)", value=6.0)
                max_pvp = c2.number_input("Max P/VP", value=1.5)
                max_vac = c3.number_input("Max Vacância (%)", value=10.0)
            
            if st.button("🔍 Executar Análise de Risco Completa"):
                # 1. Análise Manual
                analyzer = AnalyzeSell()
                manual_risks = analyzer.execute(my_fiis, min_dy, max_pvp, max_vac)
                
                # 2. Análise IA
                # ai_service já instanciado globalmente
                ai_risks = []
                for fii in my_fiis:
                    analysis = ai_service.analyze_fii(fii, portfolio_items)
                    if analysis['score'] < 50: # Critério de Risco da IA
                        ai_risks.append({
                            "fii": fii,
                            "analysis": analysis
                        })
                
                # Exibição dos Resultados
                st.divider()
                
                # Colunas para separar os tipos de alerta
                col_ai, col_manual = st.columns(2)
                
                with col_ai:
                    st.subheader("🤖 Alertas da IA")
                    if ai_risks:
                        st.error(f"{len(ai_risks)} ativos com baixa pontuação (Score < 50).")
                        for item in ai_risks:
                            fii = item['fii']
                            analysis = item['analysis']
                            with st.expander(f"⚠️ {fii.ticker} - Score: {analysis['score']}/100"):
                                st.markdown(f"**Sentimento:** {analysis['sentiment']}")
                                st.write(analysis['analysis_text'])
                                st.metric("Preço Atual", f"R$ {fii.price:.2f}")
                    else:
                        st.success("A IA não detectou riscos graves na sua carteira.")

                with col_manual:
                    st.subheader("🛠️ Alertas Manuais")
                    if manual_risks:
                        st.warning(f"{len(manual_risks)} ativos violaram seus critérios manuais.")
                        for risk_fii in manual_risks:
                            with st.expander(f"🚨 {risk_fii.ticker} - Critérios Violados"):
                                st.write(f"**DY Atual:** {risk_fii.dividend_yield:.2f}% (Min: {min_dy}%)")
                                st.write(f"**P/VP:** {risk_fii.pvp:.2f} (Max: {max_pvp})")
                                st.write(f"**Vacância:** {risk_fii.vacancia:.2f}% (Max: {max_vac}%)")
                    else:
                        st.success("Nenhum ativo violou os critérios manuais.")

    elif page == "Proventos":
        st.header("💰 Proventos")
        
        # Get theme colors for charts
        current_theme_colors = THEMES[theme]
        chart_text_color = current_theme_colors['text_color_primary']
        chart_grid_color = current_theme_colors['metric_border']
        bar_color = current_theme_colors['accent_color']
        
        portfolio_items = portfolio_service.load_portfolio()
        if not portfolio_items:
            st.info("Você precisa adicionar ativos à sua carteira para visualizar os proventos.")
        else:
            # --- Seção de Simulação ---
            with st.expander("🔮 Simulador de Renda Passiva", expanded=False):
                st.markdown("##### Planeje sua Independência Financeira")
                
                col_meta, col_aporte = st.columns(2)
                with col_meta:
                    meta_renda = st.number_input("Meta de Renda Mensal (R$)", value=1000.0, step=100.0, min_value=0.0)
                with col_aporte:
                    aporte_mensal = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=50.0, step=100.0, help="Quanto você pretende investir por mês além do reinvestimento dos dividendos.")
                
                # Seletor de Modo de Simulação
                modo_simulacao = st.radio(
                    "Modo de Simulação", 
                    ["Individual (Por Fundo)", "Carteira Diversificada (Proporcional)", "Otimização Inteligente (IA)"],
                    horizontal=True,
                    help="Individual: Meta por fundo.\nDiversificada: Mantém proporção atual.\nOtimização: IA sugere a melhor carteira."
                )
                
                if meta_renda > 0:
                    # Obter dados de mercado atualizados para simulação
                    market_map = {f.ticker: f for f in fiis}
                    tickers = [item.ticker for item in portfolio_items]
                    
                    with st.spinner("Calculando projeções..."):
                        last_divs = dividend_service.get_last_dividends(tickers)

                    if modo_simulacao == "Individual (Por Fundo)":
                        st.caption("Descubra quanto você precisa investir em cada fundo (isoladamente) para atingir sua meta.")
                        sim_data = []
                        for item in portfolio_items:
                            ticker = item.ticker
                            market_data = market_map.get(ticker)
                            last_div = last_divs.get(ticker, 0.0)
                            price = market_data.price if market_data else 0.0
                            
                            if last_div > 0 and price > 0:
                                cotas_necessarias = meta_renda / last_div
                                investimento_total = cotas_necessarias * price
                                
                                # Quanto já tenho
                                qtd_atual = item.quantity
                                renda_atual = qtd_atual * last_div
                                
                                # Quanto falta
                                cotas_faltantes = max(0, cotas_necessarias - qtd_atual)
                                investimento_faltante = cotas_faltantes * price
                                progresso = (renda_atual / meta_renda) * 100
                                
                                sim_data.append({
                                    "Ativo": ticker,
                                    "Preço Base": price,
                                    "Últ. Dividendo": last_div,
                                    "DY (mês)": (last_div / price) * 100,
                                    "Cotas Meta": int(cotas_necessarias),
                                    "Total Necessário": investimento_total,
                                    "Falta Investir": investimento_faltante,
                                    "% Atingido": progresso
                                })
                        
                        if sim_data:
                            df_sim = pd.DataFrame(sim_data)
                            st.dataframe(
                                df_sim.style.format({
                                    "Preço Base": "R$ {:.2f}",
                                    "Últ. Dividendo": "R$ {:.4f}",
                                    "DY (mês)": "{:.2f}%",
                                    "Cotas Meta": "{:,.0f}",
                                    "Total Necessário": "R$ {:,.2f}",
                                    "Falta Investir": "R$ {:,.2f}",
                                    "% Atingido": "{:.1f}%"
                                }),
                                use_container_width=True
                            )
                            st.info("💡 O cálculo considera que você atingirá a meta investindo APENAS naquele fundo.")
                        else:
                            st.warning("Dados insuficientes para simulação individual.")

                    elif modo_simulacao == "Carteira Diversificada (Proporcional)":
                        st.caption("Descubra quanto investir na carteira como um todo, mantendo o balanceamento atual, para atingir a meta.")
                        
                        # 1. Calcular Yield Médio da Carteira e Valor Total Atual
                        valor_total_carteira = 0.0
                        renda_mensal_atual = 0.0
                        valid_items = []
                        
                        for item in portfolio_items:
                            ticker = item.ticker
                            market_data = market_map.get(ticker)
                            last_div = last_divs.get(ticker, 0.0)
                            price = market_data.price if market_data else 0.0
                            
                            if price > 0:
                                valor_item = item.quantity * price
                                renda_item = item.quantity * last_div
                                
                                valor_total_carteira += valor_item
                                renda_mensal_atual += renda_item
                                
                                valid_items.append({
                                    "ticker": ticker,
                                    "price": price,
                                    "last_div": last_div,
                                    "quantity": item.quantity,
                                    "valor_atual": valor_item
                                })

                        if valor_total_carteira > 0 and renda_mensal_atual > 0:
                            yield_medio_mensal = (renda_mensal_atual / valor_total_carteira)
                            
                            # Projeção Global
                            investimento_necessario_total = meta_renda / yield_medio_mensal
                            falta_investir_total = max(0, investimento_necessario_total - valor_total_carteira)
                            
                            # Métricas Globais da Simulação
                            col_m1, col_m2, col_m3 = st.columns(3)
                            col_m1.metric("Yield Médio Mensal", f"{yield_medio_mensal*100:.2f}%")
                            col_m2.metric("Investimento Total Meta", f"R$ {investimento_necessario_total:,.2f}")
                            col_m3.metric("Falta Investir", f"R$ {falta_investir_total:,.2f}", 
                                          delta=f"-{(falta_investir_total/investimento_necessario_total)*100:.1f}%" if investimento_necessario_total > 0 else "0%")

                            if falta_investir_total > 0:
                                st.markdown("### 🎯 Plano de Aporte Diversificado")
                                st.write("Para atingir a meta mantendo suas proporções atuais, você deve adquirir:")
                                
                                plano_aporte = []
                                for item in valid_items:
                                    peso = item["valor_atual"] / valor_total_carteira
                                    aporte_necessario = falta_investir_total * peso
                                    cotas_adicionais = aporte_necessario / item["price"]
                                    
                                    plano_aporte.append({
                                        "Ativo": item["ticker"],
                                        "Peso na Carteira": peso * 100,
                                        "Aporte Sugerido": aporte_necessario,
                                        "+ Cotas": int(cotas_adicionais),
                                        "Meta de Cotas": item["quantity"] + int(cotas_adicionais)
                                    })
                                
                                df_plano = pd.DataFrame(plano_aporte)
                                st.dataframe(
                                    df_plano.style.format({
                                        "Peso na Carteira": "{:.1f}%",
                                        "Aporte Sugerido": "R$ {:,.2f}",
                                        "+ Cotas": "{:,.0f}",
                                        "Meta de Cotas": "{:,.0f}"
                                    }),
                                    use_container_width=True
                                )
                                
                                # Projeção de Tempo (Carteira Atual)
                                if aporte_mensal > 0:
                                    st.markdown("---")
                                    st.markdown(f"### ⏳ Tempo Estimado (Carteira Atual)")
                                    patrimonio = valor_total_carteira
                                    meses = 0
                                    renda_proj = renda_mensal_atual
                                    
                                    # Simulação simples
                                    while renda_proj < meta_renda and meses < 360:
                                        patrimonio += aporte_mensal + renda_proj
                                        renda_proj = patrimonio * yield_medio_mensal
                                        meses += 1
                                    
                                    anos = meses // 12
                                    meses_rest = meses % 12
                                    st.info(f"Mantendo sua carteira atual e aportando **R$ {aporte_mensal:,.2f}** mensalmente, você atingirá a meta em **{anos} anos e {meses_rest} meses**.")

                            else:
                                st.success("🎉 Parabéns! Com o yield atual da sua carteira, sua renda mensal estimada já supera a meta!")

                        else:
                            st.warning("Não foi possível calcular o Yield da carteira. Verifique se você possui ativos com preço e dividendos > 0.")

                    elif modo_simulacao == "Otimização Inteligente (IA)":
                        st.caption("A IA analisa todo o mercado e sugere uma carteira otimizada (Top Picks) para acelerar sua meta.")
                        
                        with st.spinner("🤖 A IA está analisando milhares de dados para montar a melhor estratégia..."):
                            # fiis já está disponível no escopo (load_data)
                            recommendation = ai_service.recommend_allocation(fiis, portfolio_items, aporte_mensal, meta_renda)
                        
                        if recommendation and recommendation.get('allocation_plan'):
                            # Métricas Principais
                            c1, c2, c3 = st.columns(3)
                            anos = recommendation['months_to_goal'] // 12
                            meses = recommendation['months_to_goal'] % 12
                            c1.metric("Tempo Estimado", f"{anos} anos e {meses} meses")
                            c2.metric("Patrimônio Projetado", f"R$ {recommendation['projected_equity_needed']:,.2f}")
                            c3.metric("Yield Médio Projetado", f"{recommendation['avg_yield_monthly']:.2f}% a.m.")
                            
                            st.markdown("### 🚀 Carteira Sugerida (Smart Allocation)")
                            st.write("Esta carteira prioriza ativos com alto Score (P/VP descontado, bom DY, Liquidez) e diversificação.")
                            
                            df_alloc = pd.DataFrame(recommendation['allocation_plan'])
                            st.dataframe(
                                df_alloc[['ticker', 'sector', 'price', 'dy_anual', 'score', 'weight', 'reason']].rename(columns={
                                    'ticker': 'Ativo', 'sector': 'Setor', 'price': 'Preço', 
                                    'dy_anual': 'DY Anual', 'score': 'Smart Score', 'weight': 'Peso Sugerido', 'reason': 'Análise'
                                }).style.format({
                                    'Preço': 'R$ {:.2f}',
                                    'DY Anual': '{:.2f}%',
                                    'Smart Score': '{:.0f}',
                                    'Peso Sugerido': '{:.1%}'
                                }),
                                use_container_width=True
                            )
                            
                            # Gráfico de Projeção
                            if recommendation['projection_data']:
                                st.markdown("### 📈 Evolução Patrimonial Projetada")
                                df_proj = pd.DataFrame(recommendation['projection_data'])
                                
                                chart_proj = alt.Chart(df_proj).mark_area(
                                    line={'color':'#4CAF50'},
                                    color=alt.Gradient(
                                        gradient='linear',
                                        stops=[alt.GradientStop(color='#4CAF50', offset=0),
                                               alt.GradientStop(color='rgba(76, 175, 80, 0.1)', offset=1)],
                                        x1=1, x2=1, y1=1, y2=0
                                    )
                                ).encode(
                                    x=alt.X('mes', title='Meses'),
                                    y=alt.Y('renda', title='Renda Mensal (R$)'),
                                    tooltip=['mes', 'renda', 'patrimonio']
                                ).properties(height=300)
                                
                                st.altair_chart(chart_proj, use_container_width=True)
                                st.caption("O gráfico mostra o crescimento da sua Renda Passiva Mensal considerando reinvestimentos e novos aportes.")
                        else:
                            st.warning("Não foi possível gerar uma recomendação. Verifique a conexão com os dados de mercado.")

            st.markdown("---")

            # --- Seção de Análise de Viabilidade (IA) ---
            st.subheader("🤖 Análise Preditiva de Viabilidade")
            st.caption("A IA analisa indicadores de risco (P/VP, Liquidez, Vacância) e contexto de mercado para prever a viabilidade de longo prazo do FII.")

            col_sel_fii, col_btn_analise = st.columns([0.7, 0.3])
            
            with col_sel_fii:
                fii_options = sorted([item.ticker for item in portfolio_items])
                selected_ticker_viability = st.selectbox("Selecione um FII da sua carteira para analisar:", options=fii_options, key="sel_viability")
            
            with col_btn_analise:
                st.write("") # Spacer
                st.write("") # Spacer
                btn_analise = st.button("🔮 Analisar Futuro", key="btn_analise_viability", type="primary")

            if btn_analise and selected_ticker_viability:
                # Recuperar dados de mercado do FII selecionado
                selected_fii_data = next((f for f in fiis if f.ticker == selected_ticker_viability), None)
                
                if selected_fii_data:
                    with st.spinner(f"A IA está analisando os fundamentos e cenário do {selected_ticker_viability}..."):
                        viability_result = ai_service.analyze_future_viability(selected_fii_data)
                    
                    # Exibição dos Resultados
                    risk_score = viability_result['risk_score']
                    conclusion = viability_result['conclusion']
                    
                    # Container de Resultado
                    with st.container(border=True):
                        st.markdown(f"### Resultado: {selected_ticker_viability}")
                        
                        # Link para notícias (Google News)
                        news_url = f"https://www.google.com/search?q={selected_ticker_viability}+fundos+imobiliarios+noticias&tbm=nws"
                        st.markdown(f"🔎 [Pesquisar Notícias Recentes sobre {selected_ticker_viability}]({news_url})", unsafe_allow_html=True)

                        # Score Meter
                        col_score, col_conc = st.columns([0.3, 0.7])
                        
                        with col_score:
                            st.metric("Score de Risco", f"{risk_score}/100", help="0=Seguro, 100=Crítico")
                            if risk_score < 30:
                                st.success("Risco Baixo")
                            elif risk_score < 60:
                                st.warning("Risco Médio")
                            else:
                                st.error("Risco Alto")
                                
                        with col_conc:
                            st.markdown(conclusion)
                        
                        st.divider()
                        
                        # Detalhes
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("#### 🏢 Perspectiva da Gestão")
                            st.info(viability_result['management_outlook'])
                            
                        with c2:
                            st.markdown("#### 🏗️ Cenário Setorial")
                            st.info(viability_result['sector_outlook'])
                        
                        if viability_result['viability_text']:
                            st.markdown("#### ⚠️ Pontos de Atenção Identificados")
                            for alert in viability_result['viability_text']:
                                st.error(alert)
                else:
                    st.error("Dados de mercado não encontrados para este ativo. Verifique se ele consta na fonte de dados.")

            st.markdown("---")

            with st.spinner("Buscando histórico de dividendos..."):
                df_divs = dividend_service.get_dividend_history(portfolio_items)
            
            if df_divs.empty:
                st.warning("Não foi possível carregar o histórico de dividendos. Verifique sua conexão ou tente novamente mais tarde.")
            else:
                # Layout Top: Summary + Chart
                col_summary, col_chart = st.columns([0.25, 0.75])
                
                with col_summary:
                    with st.container(border=True):
                        st.markdown("### Resumo")
                        
                        # Metrics
                        last_12m = pd.Timestamp.now() - pd.DateOffset(months=12)
                        df_12m = df_divs[df_divs['Date'] >= last_12m]
                        
                        total_12m = df_12m['TotalReceived'].sum()
                        media_12m = total_12m / 12
                        total_all = df_divs['TotalReceived'].sum()
                        
                        st.metric("Média Mensal (12m)", f"R$ {media_12m:,.2f}")
                        st.metric("Total 12 Meses", f"R$ {total_12m:,.2f}")
                        st.metric("Total Carteira", f"R$ {total_all:,.2f}")
                        
                        st.markdown("---")
                        st.markdown("#### Distribuição")
                        
                        # Donut Chart (Altair)
                        dist_data = dividend_service.get_asset_distribution(df_divs)
                        if not dist_data.empty:
                            base = alt.Chart(dist_data).encode(
                                theta=alt.Theta(field="TotalReceived", type="quantitative"),
                                color=alt.Color(field="Ticker", type="nominal", legend=None),
                                tooltip=["Ticker", alt.Tooltip("TotalReceived", format=",.2f")]
                            )
                            
                            donut = base.mark_arc(innerRadius=40).properties(height=150)
                            
                            # Configurar fundo transparente para Altair
                            st.altair_chart(donut.configure_view(strokeWidth=0).configure(background='transparent'), use_container_width=True)
                
                with col_chart:
                    with st.container(border=True):
                        st.markdown("### Evolução de Proventos")
                        # Bar Chart
                        monthly_data = dividend_service.get_monthly_summary(df_divs)
                        
                        bar_chart = alt.Chart(monthly_data).mark_bar().encode(
                            x=alt.X('MonthYear', sort=None, title='Mês', axis=alt.Axis(labelColor=chart_text_color, titleColor=chart_text_color)),
                            y=alt.Y('TotalReceived', title='R$ Recebidos', axis=alt.Axis(labelColor=chart_text_color, titleColor=chart_text_color)),
                            color=alt.value(bar_color),
                            tooltip=['MonthYear', alt.Tooltip('TotalReceived', format=",.2f")]
                        ).properties(height=400)
                        
                        # Configurar fundo transparente e eixos adaptativos
                        st.altair_chart(bar_chart.configure_view(strokeWidth=0).configure(background='transparent').configure_axis(
                            gridColor=chart_grid_color,
                            domainColor=chart_grid_color
                        ), use_container_width=True)
                
                # Middle: Monthly History Table
                st.markdown("### Histórico Mensal")
                pivot_df = df_divs.pivot_table(index='Year', columns='Month', values='TotalReceived', aggfunc='sum', fill_value=0)
                # Rename columns 1..12 to Jan..Dez
                month_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                pivot_df.columns = [month_map.get(c, c) for c in pivot_df.columns]
                
                st.dataframe(pivot_df.style.format("R$ {:.2f}"), use_container_width=True)
                
                # Bottom: Detailed List
                st.markdown("### Meus Proventos")
                st.dataframe(
                    df_divs[['Date', 'Ticker', 'Type', 'Quantity', 'DividendPerShare', 'TotalReceived']].rename(columns={
                        'Date': 'Data Pagamento',
                        'DividendPerShare': 'Valor Unit.',
                        'TotalReceived': 'Valor Total'
                    }).style.format({
                        'Valor Unit.': 'R$ {:.2f}',
                        'Valor Total': 'R$ {:.2f}',
                        'Data Pagamento': lambda t: t.strftime('%d/%m/%Y')
                    }),
                    use_container_width=True
                )

if __name__ == "__main__":
    main()
