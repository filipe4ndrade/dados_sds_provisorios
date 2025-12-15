"""
MÃ³dulo de anÃ¡lise para ViolÃªncia DomÃ©stica
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import datetime
from .utils import criar_mapa_calor


@st.cache_data
def carregar_dados_vd(arquivo, sheet):
    df = pd.read_excel(arquivo, sheet_name=sheet)
    df = df.rename(columns={
        'MUNICÍPIO DO FATO': 'MUNICIPIO',
        'REGIAO GEOGRÁFICA': 'REGIAO_GEOGRAFICA',
        'DATA DO FATO': 'DATA',
        'IDADE SENASP': 'FAIXA_IDADE',
        'TOTAL DE VÍTIMAS': 'TOTAL'
    })
    df['DATA'] = pd.to_datetime(df['DATA'])
    df['MES'] = df['DATA'].dt.month
    return df


def render(base_info):
    with st.spinner('Carregando dados de Violência Doméstica...'):
        df = carregar_dados_vd(base_info['arquivo'], base_info['sheet'])
    
    st.markdown(f'<p style="font-size:2rem; font-weight:bold; text-align:center; color:#9467bd;">🗜️ {base_info["nome"]}</p>', unsafe_allow_html=True)
    st.markdown(f"**Período:** {base_info['periodo']} | **Total de registros:** {len(df):,}")
    
    # Filtros
    st.sidebar.header("🔍 Filtros")
    anos = sorted(df['ANO'].unique())
    col1, col2 = st.sidebar.columns(2)
    ano_inicio = col1.selectbox("Ano inicial", anos, index=0)
    ano_fim = col2.selectbox("Ano final", anos, index=len(anos)-1)
    
    naturezas = ['Todas'] + sorted(df['NATUREZA'].unique().tolist())
    natureza = st.sidebar.multiselect("Natureza", naturezas, default=['Todas'])
    
    sexos = ['Todos'] + sorted(df['SEXO'].unique().tolist())
    sexo = st.sidebar.multiselect("Sexo", sexos, default=['Todos'])
    
    # Aplicar filtros
    df_filt = df[(df['ANO'] >= ano_inicio) & (df['ANO'] <= ano_fim)]
    if 'Todas' not in natureza:
        df_filt = df_filt[df_filt['NATUREZA'].isin(natureza)]
    if 'Todos' not in sexo:
        df_filt = df_filt[df_filt['SEXO'].isin(sexo)]
    
    # Métricas
    st.header("📊 Indicadores")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total de Casos", f"{df_filt['TOTAL'].sum():,}")
    with col2:
        st.metric("Média Anual", f"{df_filt.groupby('ANO')['TOTAL'].sum().mean():.0f}")
    with col3:
        st.metric("Municípios", f"{df_filt['MUNICIPIO'].nunique()}")
    with col4:
        fem = df_filt[df_filt['SEXO'].str.contains('FEM', case=False, na=False)]
        perc = (fem['TOTAL'].sum() / df_filt['TOTAL'].sum() * 100) if df_filt['TOTAL'].sum() > 0 else 0
        st.metric("% Feminino", f"{perc:.1f}%")
    with col5:
        tipos = df_filt['NATUREZA'].nunique()
        st.metric("Tipos de Crime", f"{tipos}")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Evolução", "🗺️ Geografia", "🧥 Perfil", "📊 Detalhes"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            df_ano = df_filt.groupby('ANO')['TOTAL'].sum().reset_index()
            fig = px.line(df_ano, x='ANO', y='TOTAL', markers=True, title='Evolução Anual')
            fig.update_traces(line_color='#9467bd', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            df_mes = df_filt.groupby('MES')['TOTAL'].sum().reset_index()
            df_mes['MES_NOME'] = df_mes['MES'].apply(lambda x: calendar.month_abbr[x])
            fig = px.bar(df_mes, x='MES_NOME', y='TOTAL', title='Distribuição Mensal')
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Evolução por Natureza (Top 10)")
        top_nat = df_filt.groupby('NATUREZA')['TOTAL'].sum().sort_values(ascending=False).head(10).index
        df_nat_ano = df_filt[df_filt['NATUREZA'].isin(top_nat)].groupby(['ANO', 'NATUREZA'])['TOTAL'].sum().reset_index()
        fig = px.line(df_nat_ano, x='ANO', y='TOTAL', color='NATUREZA', markers=True)
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("🗺️ Mapa")
        col1, col2 = st.columns([3, 1])
        with col2:
            ano_map = st.selectbox("Ano", ['Todos'] + anos)
            top_n = st.slider("Top N", 5, 30, 20)
        with col1:
            ano_f = None if ano_map == 'Todos' else ano_map
            mapa = criar_mapa_calor(df_filt, 'MUNICIPIO', 'TOTAL', ano_f, None, top_n)
            from streamlit_folium import st_folium
            st_folium(mapa, width=700, height=500)
        
        col1, col2 = st.columns(2)
        with col1:
            df_mun = df_filt.groupby('MUNICIPIO')['TOTAL'].sum().sort_values(ascending=False).head(15).reset_index()
            fig = px.bar(df_mun, x='TOTAL', y='MUNICIPIO', orientation='h', title='Top 15 MunicÃ­pios')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            df_reg = df_filt.groupby('REGIAO_GEOGRAFICA')['TOTAL'].sum().reset_index()
            fig = px.pie(df_reg, values='TOTAL', names='REGIAO_GEOGRAFICA', hole=0.4, title='Por RegiÃ£o')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Perfil das Vítimas")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Por Sexo")
            df_sexo = df_filt.groupby('SEXO')['TOTAL'].sum().reset_index()
            fig = px.pie(df_sexo, values='TOTAL', names='SEXO')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Por Faixa Etária")
            df_idade = df_filt.groupby('FAIXA_IDADE')['TOTAL'].sum().sort_values(ascending=False).reset_index()
            fig = px.bar(df_idade, x='TOTAL', y='FAIXA_IDADE', orientation='h')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Natureza por Sexo (Top 10)")
        top_nat = df_filt.groupby('NATUREZA')['TOTAL'].sum().sort_values(ascending=False).head(10).index
        df_nat_sex = df_filt[df_filt['NATUREZA'].isin(top_nat)].groupby(['NATUREZA', 'SEXO'])['TOTAL'].sum().reset_index()
        fig = px.bar(df_nat_sex, x='NATUREZA', y='TOTAL', color='SEXO', barmode='group')
        fig.update_layout(height=400, xaxis={'tickangle': -45})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Ranking Municípios")
            df_rank = df_filt.groupby('MUNICIPIO')['TOTAL'].sum().sort_values(ascending=False).head(20).reset_index()
            st.dataframe(df_rank, use_container_width=True)
        
        with col2:
            st.subheader("Por Natureza do Crime")
            df_nat = df_filt.groupby('NATUREZA')['TOTAL'].sum().sort_values(ascending=False).head(15).reset_index()
            st.dataframe(df_nat, use_container_width=True)
        
        csv = df_filt.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv,
                          file_name=f'violencia_domestica_pe_{datetime.now().strftime("%Y%m%d")}.csv',
                          mime='text/csv')



