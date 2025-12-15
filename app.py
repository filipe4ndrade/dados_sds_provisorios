import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar
import folium
from streamlit_folium import st_folium
from coordenadas import COORDENADAS_MUNICIPIOS

# Configuração da página
st.set_page_config(
    page_title="Painel de Segurança Pública - PE",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .database-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s;
        margin: 1rem 0;
    }
    .database-card:hover {
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Inicializar estado da sessão
if 'base_selecionada' not in st.session_state:
    st.session_state.base_selecionada = None

# Header principal
st.markdown('<p class="main-header">🚨 Sistema de Análise de Segurança Pública</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Estado de Pernambuco - Análise de Múltiplas Bases de Dados</p>', unsafe_allow_html=True)

# Dicionário de bases disponíveis
BASES_DISPONIVEIS = {
    'MVI': {
        'nome': 'Mortes Violentas Intencionais (MVI)',
        'arquivo': 'dados/MICRODADOS_DE_MVI_JAN_2004_A_NOV_2025.xlsx',
        'sheet': 'Plan1',
        'periodo': 'Janeiro/2004 a Novembro/2025',
        'icone': '💀',
        'cor': '#d62728',
        'total_registros': 85240
    },
    'Estupro': {
        'nome': 'Estupro e Crime Sexuais',
        'arquivo': 'dados/MICRODADOS_ESTUPRO_JAN_2015_A_NOV_2025.xlsx',
        'sheet': 'Plan1',
        'periodo': 'Janeiro/2015 a Novembro/2025',
        'icone': '⚠️',
        'cor': '#ff7f0e',
        'total_registros': 28259
    },
    'CVP': {
        'nome': 'Crimes Violentos contra o Patrimônio (CVP)',
        'arquivo': 'dados/Microdados_de_CVP_-_Disponível_janeiro_de_2014_a_novembro_de_2025.xlsx',
        'sheet': 'microdados cvp',
        'periodo': 'Janeiro/2014 a Novembro/2025',
        'icone': '🏦',
        'cor': '#2ca02c',
        'total_registros': 169822
    },
    'Violencia_Domestica': {
        'nome': 'Violência Doméstica',
        'arquivo': 'dados/MICRODADOS_DE_VIOLÊNCIA_DOMÉSTICA_JAN_2015_A_NOV_2025.xlsx',
        'sheet': 'Plan1',
        'periodo': 'Janeiro/2015 a Novembro/2025',
        'icone': '🏠',
        'cor': '#9467bd',
        'total_registros': 408460
    }
}

# Botão para voltar à seleção de base
if st.session_state.base_selecionada is not None:
    if st.sidebar.button("🏠 Voltar para Seleção de Base", use_container_width=True):
        st.session_state.base_selecionada = None
        st.rerun()

# Tela de seleção de base
if st.session_state.base_selecionada is None:
    st.markdown("---")
    st.subheader("📊 Selecione uma Base de Dados para Análise")
    
    # Criar cards para cada base
    cols = st.columns(2)
    
    for idx, (key, info) in enumerate(BASES_DISPONIVEIS.items()):
        with cols[idx % 2]:
            if st.button(
                f"{info['icone']} {info['nome']}\n\n📅 {info['periodo']}\n\n📊 {info['total_registros']:,} registros",
                key=f"btn_{key}",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.base_selecionada = key
                st.rerun()
    
    # Informações adicionais
    st.markdown("---")
    st.info("""
    **ℹ️ Sobre as Bases de Dados:**
    
    - **MVI**: Mortes Violentas Intencionais incluem homicídios, latrocínios, feminicídios, lesões corporais seguidas de morte e mortes por intervenção legal.
    - **Estupro**: Registros de crimes sexuais incluindo estupro, estupro de vulnerável e outros crimes contra a dignidade sexual.
    - **CVP**: Crimes Violentos contra o Patrimônio incluem roubos diversos (rua, comércio, residência, veículos, etc).
    - **Violência Doméstica**: Crimes ocorridos no contexto doméstico e familiar, incluindo lesão corporal, ameaça, injúria, etc.
    """)

else:
    # Base selecionada - carregar e exibir
    base_info = BASES_DISPONIVEIS[st.session_state.base_selecionada]
    
    st.sidebar.markdown(f"### {base_info['icone']} Base Selecionada")
    st.sidebar.info(f"**{base_info['nome']}**\n\n{base_info['periodo']}")
    
    # Importar o módulo correto baseado na base selecionada
    if st.session_state.base_selecionada == 'MVI':
        from modulos import analise_mvi
        analise_mvi.render(base_info)
    
    elif st.session_state.base_selecionada == 'Estupro':
        from modulos import analise_estupro
        analise_estupro.render(base_info)
    
    elif st.session_state.base_selecionada == 'CVP':
        from modulos import analise_cvp
        analise_cvp.render(base_info)
    
    elif st.session_state.base_selecionada == 'Violencia_Domestica':
        from modulos import analise_violencia_domestica
        analise_violencia_domestica.render(base_info)

# Footer
if st.session_state.base_selecionada is None:
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>Sistema de Análise de Segurança Pública - Pernambuco</p>
            <p>Dados: Secretaria de Defesa Social de Pernambuco</p>
        </div>
        """, unsafe_allow_html=True)
