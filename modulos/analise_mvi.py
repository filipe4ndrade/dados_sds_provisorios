"""
Módulo de análise para Mortes Violentas Intencionais (MVI)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
from datetime import datetime
from streamlit_folium import st_folium
from .utils import criar_mapa_calor, criar_filtros_padrao, aplicar_filtros, exibir_metricas_principais


@st.cache_data
def carregar_dados_mvi(arquivo, sheet):
    """Carrega e prepara os dados de MVI"""
    df = pd.read_excel(arquivo, sheet_name=sheet)
    
    # Garantir que DATA seja datetime
    df['DATA'] = pd.to_datetime(df['DATA'])
    df['MES'] = df['DATA'].dt.month
    df['MES_NOME'] = df['DATA'].dt.month_name()
    df['DIA'] = df['DATA'].dt.day
    
    # Limpar região geográfica
    df['REGIAO_GEOGRAFICA'] = df['REGIAO_GEOGRAFICA'].replace(0, 'NÃO INFORMADO')
    
    return df


def render(base_info):
    """Renderiza a interface de análise de MVI"""
    
    # Carregar dados
    with st.spinner('Carregando dados de MVI...'):
        df = carregar_dados_mvi(base_info['arquivo'], base_info['sheet'])
    
    # Header
    st.markdown(f'<p style="font-size:2rem; font-weight:bold; text-align:center; color:#d62728;">💀 {base_info["nome"]}</p>', unsafe_allow_html=True)
    st.markdown(f"**Período:** {base_info['periodo']} | **Total de registros:** {len(df):,}")
    
    # Criar filtros
    filtros = criar_filtros_padrao(df)
    
    # Adicionar filtro específico de natureza jurídica
    st.sidebar.markdown("---")
    naturezas = ['Todas'] + sorted(df['NATUREZA JURIDICA'].unique().tolist())
    filtros['naturezas'] = st.sidebar.multiselect("Natureza Jurídica", options=naturezas, default=['Todas'])
    
    # Aplicar filtros
    df_filtrado = aplicar_filtros(df, filtros)
    
    # Aplicar filtro de natureza
    if 'Todas' not in filtros['naturezas'] and len(filtros['naturezas']) > 0:
        df_filtrado = df_filtrado[df_filtrado['NATUREZA JURIDICA'].isin(filtros['naturezas'])]
    
    # Métricas principais
    st.header("📊 Indicadores Principais")
    exibir_metricas_principais(df_filtrado)
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Evolução Temporal",
        "🗺️ Análise Geográfica",
        "👥 Perfil das Vítimas",
        "⚖️ Natureza Jurídica",
        "📊 Análise Detalhada"
    ])
    
    with tab1:
        render_evolucao_temporal(df_filtrado)
    
    with tab2:
        render_analise_geografica(df_filtrado, filtros)
    
    with tab3:
        render_perfil_vitimas(df_filtrado)
    
    with tab4:
        render_natureza_juridica(df_filtrado)
    
    with tab5:
        render_analise_detalhada(df_filtrado, df, filtros)


def render_evolucao_temporal(df):
    """Renderiza análises de evolução temporal"""
    st.header("Evolução Temporal das MVI")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Vítimas por Ano")
        df_ano = df.groupby('ANO')['TOTAL DE VITIMAS'].sum().reset_index()
        fig = px.line(df_ano, x='ANO', y='TOTAL DE VITIMAS', markers=True,
                      title='Evolução Anual das Vítimas de MVI')
        fig.update_traces(line_color='#d62728', line_width=3)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Distribuição por Mês")
        df_mes = df.groupby('MES')['TOTAL DE VITIMAS'].sum().reset_index()
        df_mes['MES_NOME'] = df_mes['MES'].apply(lambda x: calendar.month_abbr[int(x)])
        fig = px.bar(df_mes, x='MES_NOME', y='TOTAL DE VITIMAS',
                     title='Distribuição Mensal das Vítimas')
        fig.update_traces(marker_color='#ff7f0e')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap
    st.subheader("Heatmap: Vítimas por Ano e Mês")
    df_heatmap = df.groupby(['ANO', 'MES'])['TOTAL DE VITIMAS'].sum().reset_index()
    df_pivot = df_heatmap.pivot(index='ANO', columns='MES', values='TOTAL DE VITIMAS').fillna(0)
    df_pivot.columns = [calendar.month_abbr[int(i)] for i in df_pivot.columns]
    
    fig = px.imshow(df_pivot, labels=dict(x="Mês", y="Ano", color="Vítimas"),
                    x=df_pivot.columns, y=df_pivot.index, aspect="auto",
                    color_continuous_scale='Reds')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def render_analise_geografica(df, filtros):
    """Renderiza análises geográficas"""
    st.header("Análise Geográfica")
    
    # Mapa
    st.subheader("🗺️ Mapa de Calor - MVI por Município")
    
    col_map1, col_map2 = st.columns([3, 1])
    
    with col_map2:
        st.write("**Controles do Mapa:**")
        anos = sorted(df['ANO'].unique())
        map_ano = st.selectbox("Ano", ['Todos'] + list(anos), key='map_ano_mvi')
        map_mes = st.selectbox("Mês", ['Todos'] + list(range(1, 13)), key='map_mes_mvi',
                             format_func=lambda x: 'Todos' if x == 'Todos' else calendar.month_name[x])
        top_n = st.slider("Top N municípios", 5, 50, 20, key='top_n_mvi')
    
    with col_map1:
        ano_filtro = None if map_ano == 'Todos' else map_ano
        mes_filtro = None if map_mes == 'Todos' else map_mes
        
        mapa = criar_mapa_calor(df, 'MUNICIPIO', 'TOTAL DE VITIMAS', ano_filtro, mes_filtro, top_n)
        st_folium(mapa, width=700, height=500)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 15 Municípios")
        df_mun = df.groupby('MUNICIPIO')['TOTAL DE VITIMAS'].sum().sort_values(ascending=False).head(15).reset_index()
        fig = px.bar(df_mun, x='TOTAL DE VITIMAS', y='MUNICIPIO', orientation='h')
        fig.update_traces(marker_color='#1f77b4')
        fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Por Região")
        df_reg = df.groupby('REGIAO_GEOGRAFICA')['TOTAL DE VITIMAS'].sum().reset_index()
        fig = px.pie(df_reg, values='TOTAL DE VITIMAS', names='REGIAO_GEOGRAFICA', hole=0.4)
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)


def render_perfil_vitimas(df):
    """Renderiza análises de perfil das vítimas"""
    st.header("Perfil das Vítimas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Por Sexo")
        df_sexo = df.groupby('SEXO')['TOTAL DE VITIMAS'].sum().reset_index()
        fig = px.pie(df_sexo, values='TOTAL DE VITIMAS', names='SEXO')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Evolução por Sexo")
        df_sexo_ano = df.groupby(['ANO', 'SEXO'])['TOTAL DE VITIMAS'].sum().reset_index()
        fig = px.line(df_sexo_ano, x='ANO', y='TOTAL DE VITIMAS', color='SEXO', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    
    # Idade
    st.subheader("Distribuição por Idade")
    col1, col2 = st.columns(2)
    
    with col1:
        df_idade = df[df['IDADE'].notna()]
        fig = px.histogram(df_idade, x='IDADE', nbins=50)
        fig.update_traces(marker_color='#ff7f0e')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        bins = [0, 12, 17, 24, 29, 39, 49, 59, 100]
        labels = ['0-12', '13-17', '18-24', '25-29', '30-39', '40-49', '50-59', '60+']
        df['FAIXA_ETARIA'] = pd.cut(df['IDADE'], bins=bins, labels=labels, include_lowest=True)
        df_faixa = df.groupby('FAIXA_ETARIA')['TOTAL DE VITIMAS'].sum().reset_index()
        fig = px.bar(df_faixa, x='FAIXA_ETARIA', y='TOTAL DE VITIMAS')
        st.plotly_chart(fig, use_container_width=True)


def render_natureza_juridica(df):
    """Renderiza análises por natureza jurídica"""
    st.header("Análise por Natureza Jurídica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição")
        df_nat = df.groupby('NATUREZA JURIDICA')['TOTAL DE VITIMAS'].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(df_nat, x='TOTAL DE VITIMAS', y='NATUREZA JURIDICA', orientation='h')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Proporção")
        fig = px.pie(df_nat, values='TOTAL DE VITIMAS', names='NATUREZA JURIDICA')
        st.plotly_chart(fig, use_container_width=True)
    
    # Evolução
    st.subheader("Evolução Temporal por Natureza")
    df_nat_ano = df.groupby(['ANO', 'NATUREZA JURIDICA'])['TOTAL DE VITIMAS'].sum().reset_index()
    fig = px.line(df_nat_ano, x='ANO', y='TOTAL DE VITIMAS', color='NATUREZA JURIDICA', markers=True)
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def render_analise_detalhada(df_filtrado, df_original, filtros):
    """Renderiza análises detalhadas e exportação"""
    st.header("Análise Detalhada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ranking de Municípios")
        df_rank = df_filtrado.groupby('MUNICIPIO').agg({
            'TOTAL DE VITIMAS': 'sum',
            'IDADE': 'mean'
        }).reset_index()
        df_rank.columns = ['Município', 'Total', 'Idade Média']
        df_rank = df_rank.sort_values('Total', ascending=False).head(20)
        df_rank['Idade Média'] = df_rank['Idade Média'].round(1)
        st.dataframe(df_rank, use_container_width=True)
    
    with col2:
        st.subheader("Por Região")
        df_stats = df_filtrado.groupby('REGIAO_GEOGRAFICA').agg({
            'TOTAL DE VITIMAS': 'sum',
            'IDADE': 'mean',
            'MUNICIPIO': 'nunique'
        }).reset_index()
        df_stats.columns = ['Região', 'Total', 'Idade Média', 'Municípios']
        df_stats = df_stats.sort_values('Total', ascending=False)
        df_stats['Idade Média'] = df_stats['Idade Média'].round(1)
        st.dataframe(df_stats, use_container_width=True)
    
    # Download
    st.subheader("Exportar Dados")
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", data=csv,
                      file_name=f'mvi_pe_{datetime.now().strftime("%Y%m%d")}.csv',
                      mime='text/csv')
