"""
Funções auxiliares comuns para todos os módulos de análise
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
import folium
from streamlit_folium import st_folium
from coordenadas import COORDENADAS_MUNICIPIOS


def criar_mapa_calor(df, col_municipio, col_vitimas, ano=None, mes=None, top_n=20):
    """
    Cria um mapa de calor interativo com os municípios
    
    Args:
        df: DataFrame com os dados
        col_municipio: Nome da coluna com os municípios
        col_vitimas: Nome da coluna com número de vítimas/casos
        ano: Ano específico para filtrar (None = todos)
        mes: Mês específico para filtrar (None = todos)
        top_n: Número de municípios a exibir
    
    Returns:
        Mapa folium
    """
    df_mapa = df.copy()
    
    # Aplicar filtros
    if ano is not None and 'ANO' in df_mapa.columns:
        df_mapa = df_mapa[df_mapa['ANO'] == ano]
    
    if mes is not None and 'MES' in df_mapa.columns:
        df_mapa = df_mapa[df_mapa['MES'] == mes]
    
    # Agrupar por município
    df_mapa_agg = df_mapa.groupby(col_municipio)[col_vitimas].sum().sort_values(ascending=False).head(top_n).reset_index()
    
    # Criar mapa centrado em Pernambuco
    m = folium.Map(location=[-8.0476, -35.8770], zoom_start=7, tiles='OpenStreetMap')
    
    if len(df_mapa_agg) == 0:
        return m
    
    max_vitimas = df_mapa_agg[col_vitimas].max()
    
    for _, row in df_mapa_agg.iterrows():
        municipio = row[col_municipio]
        vitimas = row[col_vitimas]
        
        # Normalizar nome do município para buscar coordenadas
        municipio_upper = municipio.upper().strip()
        
        if municipio_upper in COORDENADAS_MUNICIPIOS:
            coords = COORDENADAS_MUNICIPIOS[municipio_upper]
            
            # Calcular tamanho proporcional
            radius = (vitimas / max_vitimas) * 30000 + 5000
            
            # Definir cor baseada na intensidade
            if vitimas > max_vitimas * 0.7:
                color = '#8B0000'
            elif vitimas > max_vitimas * 0.4:
                color = '#DC143C'
            elif vitimas > max_vitimas * 0.2:
                color = '#FF6347'
            else:
                color = '#FFA07A'
            
            folium.Circle(
                location=[coords['lat'], coords['lon']],
                radius=radius,
                popup=f"<b>{municipio}</b><br>Total: {vitimas:,}",
                tooltip=f"{municipio}: {vitimas:,}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6,
                weight=2
            ).add_to(m)
    
    # Adicionar legenda
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
        <p style="margin:0"><b>Intensidade</b></p>
        <p style="margin:5px 0"><span style="color:#8B0000">●</span> Muito Alta (>70%)</p>
        <p style="margin:5px 0"><span style="color:#DC143C">●</span> Alta (40-70%)</p>
        <p style="margin:5px 0"><span style="color:#FF6347">●</span> Média (20-40%)</p>
        <p style="margin:5px 0"><span style="color:#FFA07A">●</span> Baixa (<20%)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def criar_filtros_padrao(df, prefixo_colunas=None):
    """
    Cria filtros padrão na sidebar
    
    Args:
        df: DataFrame com os dados
        prefixo_colunas: Dict com mapeamento de nomes de colunas {padrão: real}
                        Ex: {'municipio': 'MUNICIPIO DO FATO', 'regiao': 'REGIAO GEOGRAFICA'}
    
    Returns:
        Dict com os filtros aplicados
    """
    if prefixo_colunas is None:
        prefixo_colunas = {}
    
    filtros = {}
    
    # Mapeamento de colunas
    col_ano = prefixo_colunas.get('ano', 'ANO')
    col_mes = prefixo_colunas.get('mes', 'MES')
    col_regiao = prefixo_colunas.get('regiao', 'REGIAO_GEOGRAFICA')
    col_municipio = prefixo_colunas.get('municipio', 'MUNICIPIO')
    col_sexo = prefixo_colunas.get('sexo', 'SEXO')
    col_idade = prefixo_colunas.get('idade', 'IDADE')
    
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de ano
    if col_ano in df.columns:
        anos_disponiveis = sorted(df[col_ano].unique())
        col_ano1, col_ano2 = st.sidebar.columns(2)
        filtros['ano_inicio'] = col_ano1.selectbox("Ano inicial", anos_disponiveis, index=0)
        filtros['ano_fim'] = col_ano2.selectbox("Ano final", anos_disponiveis, index=len(anos_disponiveis)-1)
    
    # Filtro de mês
    if col_mes in df.columns or 'DATA' in df.columns:
        meses = ['Todos'] + [calendar.month_name[i] for i in range(1, 13)]
        filtros['meses'] = st.sidebar.multiselect("Mês", options=meses, default=['Todos'])
    
    # Filtro de região
    if col_regiao in df.columns:
        regioes = ['Todas'] + sorted(df[col_regiao].unique().tolist())
        filtros['regioes'] = st.sidebar.multiselect("Região Geográfica", options=regioes, default=['Todas'])
    
    # Filtro de município
    if col_municipio in df.columns:
        municipios = ['Todos'] + sorted(df[col_municipio].unique().tolist())
        filtros['municipios'] = st.sidebar.multiselect("Município", options=municipios, default=['Todos'])
    
    # Filtro de sexo
    if col_sexo in df.columns:
        sexos = ['Todos'] + sorted(df[col_sexo].unique().tolist())
        filtros['sexos'] = st.sidebar.multiselect("Sexo", options=sexos, default=['Todos'])
    
    # Filtro de idade
    if col_idade in df.columns:
        idade_valida = df[col_idade].dropna()
        if len(idade_valida) > 0:
            filtros['idade_min'], filtros['idade_max'] = st.sidebar.slider(
                "Faixa Etária",
                min_value=int(idade_valida.min()),
                max_value=int(idade_valida.max()),
                value=(int(idade_valida.min()), int(idade_valida.max()))
            )
    
    return filtros


def aplicar_filtros(df, filtros, prefixo_colunas=None):
    """
    Aplica os filtros ao DataFrame
    
    Args:
        df: DataFrame original
        filtros: Dict com os filtros (retorno de criar_filtros_padrao)
        prefixo_colunas: Dict com mapeamento de nomes de colunas
    
    Returns:
        DataFrame filtrado
    """
    if prefixo_colunas is None:
        prefixo_colunas = {}
    
    df_filtrado = df.copy()
    
    # Mapeamento de colunas
    col_ano = prefixo_colunas.get('ano', 'ANO')
    col_mes = prefixo_colunas.get('mes', 'MES')
    col_regiao = prefixo_colunas.get('regiao', 'REGIAO_GEOGRAFICA')
    col_municipio = prefixo_colunas.get('municipio', 'MUNICIPIO')
    col_sexo = prefixo_colunas.get('sexo', 'SEXO')
    col_idade = prefixo_colunas.get('idade', 'IDADE')
    
    # Filtro de ano
    if 'ano_inicio' in filtros and 'ano_fim' in filtros and col_ano in df_filtrado.columns:
        df_filtrado = df_filtrado[(df_filtrado[col_ano] >= filtros['ano_inicio']) & 
                                   (df_filtrado[col_ano] <= filtros['ano_fim'])]
    
    # Filtro de mês
    if 'meses' in filtros and col_mes in df_filtrado.columns:
        if 'Todos' not in filtros['meses'] and len(filtros['meses']) > 0:
            meses_nomes = ['Todos'] + [calendar.month_name[i] for i in range(1, 13)]
            meses_numeros = [meses_nomes.index(m) for m in filtros['meses'] if m != 'Todos']
            df_filtrado = df_filtrado[df_filtrado[col_mes].isin(meses_numeros)]
    
    # Filtro de região
    if 'regioes' in filtros and col_regiao in df_filtrado.columns:
        if 'Todas' not in filtros['regioes'] and len(filtros['regioes']) > 0:
            df_filtrado = df_filtrado[df_filtrado[col_regiao].isin(filtros['regioes'])]
    
    # Filtro de município
    if 'municipios' in filtros and col_municipio in df_filtrado.columns:
        if 'Todos' not in filtros['municipios'] and len(filtros['municipios']) > 0:
            df_filtrado = df_filtrado[df_filtrado[col_municipio].isin(filtros['municipios'])]
    
    # Filtro de sexo
    if 'sexos' in filtros and col_sexo in df_filtrado.columns:
        if 'Todos' not in filtros['sexos'] and len(filtros['sexos']) > 0:
            df_filtrado = df_filtrado[df_filtrado[col_sexo].isin(filtros['sexos'])]
    
    # Filtro de idade
    if 'idade_min' in filtros and 'idade_max' in filtros and col_idade in df_filtrado.columns:
        df_filtrado = df_filtrado[(df_filtrado[col_idade] >= filtros['idade_min']) & 
                                   (df_filtrado[col_idade] <= filtros['idade_max'])]
    
    return df_filtrado


def exibir_metricas_principais(df, col_vitimas='TOTAL DE VITIMAS', col_municipio='MUNICIPIO', 
                                col_idade='IDADE', col_sexo='SEXO', col_ano='ANO'):
    """
    Exibe métricas principais em cards
    """
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total = df[col_vitimas].sum() if col_vitimas in df.columns else len(df)
        st.metric("Total de Casos", f"{total:,}")
    
    with col2:
        if col_ano in df.columns:
            media_anual = df.groupby(col_ano)[col_vitimas if col_vitimas in df.columns else col_ano].sum().mean()
            st.metric("Média Anual", f"{media_anual:.0f}")
        else:
            st.metric("Registros", f"{len(df):,}")
    
    with col3:
        if col_municipio in df.columns:
            municipios_afetados = df[col_municipio].nunique()
            st.metric("Municípios", f"{municipios_afetados}")
        else:
            st.metric("Período", "Múltiplos anos")
    
    with col4:
        if col_idade in df.columns:
            idade_media = df[col_idade].mean()
            if pd.notna(idade_media):
                st.metric("Idade Média", f"{idade_media:.1f} anos")
            else:
                st.metric("Idade", "N/A")
        else:
            st.metric("Dados", "Disponíveis")
    
    with col5:
        if col_sexo in df.columns:
            try:
                sexo_masc = df[df[col_sexo].str.upper().str.contains('MASC', na=False)]
                perc = (len(sexo_masc) / len(df) * 100) if len(df) > 0 else 0
                st.metric("% Masculino", f"{perc:.1f}%")
            except:
                st.metric("Sexo", "Dados variados")
        else:
            st.metric("Info", "Completa")
