"""
Módulo de análise para Crimes Violentos contra o Patrimônio (CVP)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import datetime
from .utils import criar_mapa_calor, exibir_metricas_principais


@st.cache_data
def carregar_dados_cvp(arquivo, sheet):
    df = pd.read_excel(arquivo, sheet_name=sheet)
    df = df.rename(columns={
        'MUNICÍPIO': 'MUNICIPIO',
        'REGIÃO GEOGRÁFICA': 'REGIAO_GEOGRAFICA'
    })
    df['DATA'] = pd.to_datetime(df['DATA'])
    df['MES'] = df['DATA'].dt.month
    return df


def render(base_info):
    with st.spinner('Carregando dados de CVP...'):
        df = carregar_dados_cvp(base_info['arquivo'], base_info['sheet'])
    
    st.markdown(f'<p style="font-size:2rem; font-weight:bold; text-align:center; color:#2ca02c;">🏦 {base_info["nome"]}</p>', unsafe_allow_html=True)
    st.markdown(f"**Período:** {base_info['periodo']} | **Total de registros:** {len(df):,}")
    
    # Filtros
    st.sidebar.header("🔍 Filtros")
    anos = sorted(df['ANO'].unique())
    col1, col2 = st.sidebar.columns(2)
    ano_inicio = col1.selectbox("Ano inicial", anos, index=0)
    ano_fim = col2.selectbox("Ano final", anos, index=len(anos)-1)
    
    regioes = ['Todas'] + sorted(df['REGIAO_GEOGRAFICA'].unique().tolist())
    regiao = st.sidebar.multiselect("Região", regioes, default=['Todas'])
    
    municipios = ['Todos'] + sorted(df['MUNICIPIO'].unique().tolist())
    municipio = st.sidebar.multiselect("Município", municipios, default=['Todos'])
    
    # Aplicar filtros
    df_filt = df[(df['ANO'] >= ano_inicio) & (df['ANO'] <= ano_fim)]
    if 'Todas' not in regiao:
        df_filt = df_filt[df_filt['REGIAO_GEOGRAFICA'].isin(regiao)]
    if 'Todos' not in municipio:
        df_filt = df_filt[df_filt['MUNICIPIO'].isin(municipio)]
    
    # Métricas
    st.header("📊 Indicadores")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Casos", f"{df_filt['TOTAL'].sum():,}")
    with col2:
        st.metric("Média Anual", f"{df_filt.groupby('ANO')['TOTAL'].sum().mean():.0f}")
    with col3:
        st.metric("Municípios", f"{df_filt['MUNICIPIO'].nunique()}")
    with col4:
        st.metric("Média Diária", f"{df_filt['TOTAL'].sum() / len(df_filt['ANO'].unique()) / 365:.1f}")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Evolução", "🗺️ Geografia", "📊 Detalhes"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            df_ano = df_filt.groupby('ANO')['TOTAL'].sum().reset_index()
            fig = px.line(df_ano, x='ANO', y='TOTAL', markers=True, title='Evolução Anual')
            fig.update_traces(line_color='#2ca02c', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            df_mes = df_filt.groupby('MES')['TOTAL'].sum().reset_index()
            df_mes['MES_NOME'] = df_mes['MES'].apply(lambda x: calendar.month_abbr[x])
            fig = px.bar(df_mes, x='MES_NOME', y='TOTAL', title='Distribuição Mensal')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("🗺️ Mapa")
        col1, col2 = st.columns([3, 1])
        with col2:
            ano_map = st.selectbox("Ano", ['Todos'] + anos)
            top_n = st.slider("Top N", 5, 30, 15)
        with col1:
            ano_f = None if ano_map == 'Todos' else ano_map
            mapa = criar_mapa_calor(df_filt, 'MUNICIPIO', 'TOTAL', ano_f, None, top_n)
            from streamlit_folium import st_folium
            st_folium(mapa, width=700, height=500)
        
        col1, col2 = st.columns(2)
        with col1:
            df_mun = df_filt.groupby('MUNICIPIO')['TOTAL'].sum().sort_values(ascending=False).head(15).reset_index()
            fig = px.bar(df_mun, x='TOTAL', y='MUNICIPIO', orientation='h', title='Top 15 Municípios')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            df_reg = df_filt.groupby('REGIAO_GEOGRAFICA')['TOTAL'].sum().reset_index()
            fig = px.pie(df_reg, values='TOTAL', names='REGIAO_GEOGRAFICA', hole=0.4, title='Por Região')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Ranking Municípios")
            df_rank = df_filt.groupby('MUNICIPIO')['TOTAL'].sum().sort_values(ascending=False).head(20).reset_index()
            st.dataframe(df_rank, use_container_width=True)
        
        with col2:
            st.subheader("Por Região")
            df_stats = df_filt.groupby('REGIAO_GEOGRAFICA').agg({
                'TOTAL': 'sum',
                'MUNICIPIO': 'nunique'
            }).reset_index()
            df_stats.columns = ['Região', 'Total', 'Municípios']
            st.dataframe(df_stats, use_container_width=True)
        
        csv = df_filt.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv,
                          file_name=f'cvp_pe_{datetime.now().strftime("%Y%m%d")}.csv',
                          mime='text/csv')
