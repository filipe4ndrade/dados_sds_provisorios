"""
MÃ³dulo de anÃ¡lise para Estupro e Crimes Sexuais
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import datetime
from streamlit_folium import st_folium
from .utils import criar_mapa_calor, criar_filtros_padrao, aplicar_filtros, exibir_metricas_principais


@st.cache_data
def carregar_dados_estupro(arquivo, sheet):
    """Carrega e prepara os dados de Estupro"""
    df = pd.read_excel(arquivo, sheet_name=sheet)
    
    # Renomear colunas para padrão
    df = df.rename(columns={
        'MUNICÍPIO DO FATO': 'MUNICIPIO',
        'REGIAO GEOGRÁFICA': 'REGIAO_GEOGRAFICA',
        'DATA DO FATO': 'DATA',
        'IDADE SENASP': 'FAIXA_IDADE',
        'TOTAL DE VÍTIMAS': 'TOTAL'
    })
    
    # Preparar dados
    df['DATA'] = pd.to_datetime(df['DATA'])
    df['MES'] = df['DATA'].dt.month
    df['MES_NOME'] = df['DATA'].dt.month_name()
    
    return df


def render(base_info):
    """Renderiza a interface de anÃ¡lise de Estupro"""
    
    # Carregar dados
    with st.spinner('Carregando dados de Estupro...'):
        df = carregar_dados_estupro(base_info['arquivo'], base_info['sheet'])
    
    # Header
    st.markdown(f'<p style="font-size:2rem; font-weight:bold; text-align:center; color:#ff7f0e;">⚠️ {base_info["nome"]}</p>', unsafe_allow_html=True)
    st.markdown(f"**Período:** {base_info['periodo']} | **Total de registros:** {len(df):,}")
    
    # Criar filtros com mapeamento de colunas
    mapeamento = {
        'municipio': 'MUNICIPIO',
        'regiao': 'REGIAO_GEOGRAFICA',
        'sexo': 'SEXO',
        'ano': 'ANO'
    }
    filtros = criar_filtros_padrao(df, mapeamento)
    
    # Filtros adicionais especÃ­ficos
    st.sidebar.markdown("---")
    naturezas = ['Todas'] + sorted(df['NATUREZA'].unique().tolist())
    filtros['naturezas'] = st.sidebar.multiselect("Natureza do Crime", options=naturezas, default=['Todas'])
    
    faixas_idade = ['Todas'] + sorted(df['FAIXA_IDADE'].unique().tolist())
    filtros['faixas_idade'] = st.sidebar.multiselect("Faixa EtÃ¡ria", options=faixas_idade, default=['Todas'])
    
    # Aplicar filtros
    df_filtrado = aplicar_filtros(df, filtros, mapeamento)
    
    # Aplicar filtros especÃ­ficos
    if 'Todas' not in filtros['naturezas'] and len(filtros['naturezas']) > 0:
        df_filtrado = df_filtrado[df_filtrado['NATUREZA'].isin(filtros['naturezas'])]
    
    if 'Todas' not in filtros['faixas_idade'] and len(filtros['faixas_idade']) > 0:
        df_filtrado = df_filtrado[df_filtrado['FAIXA_IDADE'].isin(filtros['faixas_idade'])]
    
    # MÃ©tricas
    st.header("Indicadores Principais")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total de Casos", f"{df_filtrado['TOTAL'].sum():,}")
    
    with col2:
        media = df_filtrado.groupby('ANO')['TOTAL'].sum().mean()
        st.metric("Média Anual", f"{media:.0f}")
    
    with col3:
        munic = df_filtrado['MUNICIPIO'].nunique()
        st.metric("Municípios", f"{munic}")
    
    with col4:
        if 'SEXO' in df_filtrado.columns:
            fem = df_filtrado[df_filtrado['SEXO'].str.contains('FEM', case=False, na=False)]
            perc = (fem['TOTAL'].sum() / df_filtrado['TOTAL'].sum() * 100) if df_filtrado['TOTAL'].sum() > 0 else 0
            st.metric("% Feminino", f"{perc:.1f}%")
        else:
            st.metric("Casos", f"{len(df_filtrado):,}")
    
    with col5:
        menor = df_filtrado[df_filtrado['FAIXA_IDADE'].str.contains('00-11|12-17', case=False, na=False)]
        perc_menor = (menor['TOTAL'].sum() / df_filtrado['TOTAL'].sum() * 100) if df_filtrado['TOTAL'].sum() > 0 else 0
        st.metric("% Menores", f"{perc_menor:.1f}%")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Evolução Temporal",
        "🗺️ Análise Geográfica",
        "🧥 Perfil das Vítimas",
        "📊 Análise Detalhada"
    ])
    
    with tab1:
        render_evolucao(df_filtrado)
    
    with tab2:
        render_geografica(df_filtrado)
    
    with tab3:
        render_perfil(df_filtrado)
    
    with tab4:
        render_detalhada(df_filtrado)


def render_evolucao(df):
    """Renderiza evolução temporal"""
    st.header("Evolução Temporal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        df_ano = df.groupby('ANO')['TOTAL'].sum().reset_index()
        fig = px.line(df_ano, x='ANO', y='TOTAL', markers=True,
                     title='Evolução Anual de Casos')
        fig.update_traces(line_color='#ff7f0e', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        df_mes = df.groupby('MES')['TOTAL'].sum().reset_index()
        df_mes['MES_NOME'] = df_mes['MES'].apply(lambda x: calendar.month_abbr[int(x)])
        fig = px.bar(df_mes, x='MES_NOME', y='TOTAL', title='Distribuição Mensal')
        st.plotly_chart(fig, use_container_width=True)
    
    # Por natureza ao longo do tempo
    st.subheader("Evolução por Natureza do Crime")
    df_nat = df.groupby(['ANO', 'NATUREZA'])['TOTAL'].sum().reset_index()
    fig = px.line(df_nat, x='ANO', y='TOTAL', color='NATUREZA', markers=True)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def render_geografica(df):
    """Renderiza análise geográfica"""
    st.header("Análise Geográfica")
    
    st.subheader("🗺️ Mapa de Calor")
    col1, col2 = st.columns([3, 1])
    
    with col2:
        anos = sorted(df['ANO'].unique())
        ano = st.selectbox("Ano", ['Todos'] + list(anos))
        top_n = st.slider("Top N municÃ­pios", 5, 30, 15)
    
    with col1:
        ano_filtro = None if ano == 'Todos' else ano
        mapa = criar_mapa_calor(df, 'MUNICIPIO', 'TOTAL', ano_filtro, None, top_n)
        st_folium(mapa, width=700, height=500)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 15 MunicÃ­pios")
        df_mun = df.groupby('MUNICIPIO')['TOTAL'].sum().sort_values(ascending=False).head(15).reset_index()
        fig = px.bar(df_mun, x='TOTAL', y='MUNICIPIO', orientation='h')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Por Região")
        df_reg = df.groupby('REGIAO_GEOGRAFICA')['TOTAL'].sum().reset_index()
        fig = px.pie(df_reg, values='TOTAL', names='REGIAO_GEOGRAFICA', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)


def render_perfil(df):
    """Renderiza perfil das vítimas"""
    st.header("Perfil das Vítimas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Por Sexo")
        df_sexo = df.groupby('SEXO')['TOTAL'].sum().reset_index()
        fig = px.pie(df_sexo, values='TOTAL', names='SEXO')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Por Faixa Etária")
        df_idade = df.groupby('FAIXA_IDADE')['TOTAL'].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(df_idade, x='TOTAL', y='FAIXA_IDADE', orientation='h')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Natureza por faixa etária
    st.subheader("Natureza do Crime por Faixa Etária")
    df_nat_idade = df.groupby(['FAIXA_IDADE', 'NATUREZA'])['TOTAL'].sum().reset_index()
    fig = px.bar(df_nat_idade, x='FAIXA_IDADE', y='TOTAL', color='NATUREZA', barmode='stack')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_detalhada(df):
    """Renderiza análise detalhada"""
    st.header("Análise Detalhada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ranking de Municípios")
        df_rank = df.groupby('MUNICIPIO')['TOTAL'].sum().sort_values(ascending=False).head(20).reset_index()
        df_rank.columns = ['Município', 'Total de Casos']
        st.dataframe(df_rank, use_container_width=True)
    
    with col2:
        st.subheader("Por Natureza do Crime")
        df_nat = df.groupby('NATUREZA')['TOTAL'].sum().sort_values(ascending=False).reset_index()
        df_nat.columns = ['Natureza', 'Total']
        st.dataframe(df_nat, use_container_width=True)
    
    # Download
    st.subheader("Exportar Dados")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", data=csv,
                      file_name=f'estupro_pe_{datetime.now().strftime("%Y%m%d")}.csv',
                      mime='text/csv')



