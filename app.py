import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# 1. Configuração da Página
st.set_page_config(page_title="FASICLIN - Dashboard Premium", layout="wide")

# Estilização CSS para visual Moderno e Clean
st.markdown("""
    <style>
    .kpi-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #004a87;
        margin-bottom: 15px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 15px;
    }
    .main-title {
        color: #004a87;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .growth-indicator {
        font-size: 14px;
        font-weight: bold;
        margin-top: 5px;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Identificação da Planilha Atualizada e GIDs Fornecidos
SHEET_ID = "1slAr_6YDKRKBqsZK4G6JguD47FD8dz3Oa-9OD8hCYyE"
ABAS_CONFIG = {
    "SINOP": "1049389082",
    "SORRISO": "608902302",       
    "CUIABA": "1444156369",        
    "RONDONOPOLIS": "1726640375",   
    "PRIMAVERA": "470975982"      
}

@st.cache_data(ttl=10)
def load_all_data():
    lista_dfs = []
    cache_buster = int(time.time() // 10) 
    
    for nome_aba, gid in ABAS_CONFIG.items():
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}&cb={cache_buster}"
            df_temp = pd.read_csv(url)
            
            df_temp.columns = [
                str(c).replace('\n', ' ').replace('\r', ' ').strip().upper() 
                for c in df_temp.columns
            ]
            df_temp.columns = [" ".join(c.split()) for c in df_temp.columns]
            
            df_temp['UNIDADE_NOME'] = nome_aba
            lista_dfs.append(df_temp)
        except Exception as e:
            st.sidebar.warning(f"Aba {nome_aba} não pôde ser carregada.")
            
    return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()

df_raw = load_all_data()

if not df_raw.empty:
    COL_CLINICA = "CLINICA"
    COL_ANO = "ANO LETIVO"
    COL_META = "QUANTIDADE DE PROCEDIMENTO POR SEMESTRE"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO"]

    if COL_META not in df_raw.columns:
        for c in df_raw.columns:
            if "PROCEDIMENTO" in c and "SEMESTRE" in c:
                COL_META = c
                break

    colunas_numericas = [COL_META] + [m for m in MESES if m in df_raw.columns]
    for c in colunas_numericas:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)

    # Criar coluna com o Total Realizado na linha (soma dos meses)
    df_raw['TOTAL_REALIZADO_LINHA'] = df_raw[colunas_numericas[1:]].sum(axis=1)

    # --- INTERFACE ---
    st.markdown('<h1 class="main-title">🏥 FASICLIN - Gestão de Metas e Produtividade</h1>', unsafe_allow_html=True)

    # Filtros dispostos de forma compacta
    col_u, col_a, col_c = st.columns(3)
    
    with col_u:
        unidades_disponiveis = sorted(df_raw['UNIDADE_NOME'].unique().tolist())
        unidade_sel = st.selectbox("Unidade:", unidades_disponiveis)
    
    df_unidade = df_raw[df_raw['UNIDADE_NOME'] == unidade_sel].copy()

    with col_a:
        if COL_ANO in df_unidade.columns:
            anos_disponiveis = sorted(df_unidade[COL_ANO].dropna().unique().tolist(), reverse=True)
            ano_sel = st.selectbox("Ano Letivo Principal (para os KPIs):", anos_disponiveis)
        else:
            ano_sel = "Geral"

    # Base filtrada para o Ano selecionado e Clínica específica
    df_filtrado = df_unidade[df_unidade[COL_ANO] == ano_sel] if COL_ANO in df_unidade.columns else df_unidade.copy()

    with col_c:
        clinicas_disponiveis = ["TODAS"] + sorted(df_filtrado[COL_CLINICA].dropna().unique().tolist())
        clinica_sel = st.selectbox("Filtrar por Clínica:", clinicas_disponiveis)

    # Base estrita para os números do painel superior
    df_kpi_atual = df_filtrado.copy()
    if clinica_sel != "TODAS":
        df_kpi_atual = df_kpi_atual[df_kpi_atual[COL_CLINICA] == clinica_sel]

    # --- CÁLCULOS EXECUTIVOS DO ANO SELECIONADO ---
    total_meta = df_kpi_atual[COL_META].sum()
    meses_reais = [m for m in MESES if m in df_kpi_atual.columns]
    total_realizado = df_kpi_atual['TOTAL_REALIZADO_LINHA'].sum()
    falta = max(0, total_meta - total_realizado)
    perc_total = (total_realizado / total_meta * 100) if total_meta > 0 else 0

    soma_por_mes = df_kpi_atual[meses_reais].sum() if meses_reais else pd.Series()
    meses_com_dados = sum(soma_por_mes > 0)
    total_meses_periodo = len(meses_reais) if meses_reais else 1
    meses_restantes = max(1, total_meses_periodo - meses_com_dados)
    media_necessaria_mes = int(falta / meses_restantes) if falta > 0 else 0

    # --- LÓGICA DO INDICATIVO DE CRESCIMENTO ---
    texto_crescimento = '<span style="color:gray; font-size:12px;">Primeiro período registrado</span>'
    
    if COL_ANO in df_unidade.columns and len(anos_disponiveis) > 1:
        try:
            # Encontra o índice do ano selecionado e pega o próximo na lista (o anterior no tempo cronológico)
            idx_ano_atual = anos_disponiveis.index(ano_sel)
            if idx_ano_atual < len(anos_disponiveis) - 1:
                ano_anterior = anos_disponiveis[idx_ano_atual + 1]
                
                # Filtra os dados do ano anterior com base no mesmo critério de Clínica
                df_ano_ant = df_unidade[df_unidade[COL_ANO] == ano_anterior]
                if clinica_sel != "TODAS":
                    df_ano_ant = df_ano_ant[df_ano_ant[COL_CLINICA] == clinica_sel]
                
                total_realizado_anterior = df_ano_ant['TOTAL_REALIZADO_LINHA'].sum()
                
                if total_realizado_anterior > 0:
                    variacao = ((total_realizado - total_realizado_anterior) / total_realizado_anterior) * 100
                    if variacao >= 0:
                        texto_crescimento = f'<span class="growth-indicator" style="color:#299947;">▲ +{variacao:.1f}%</span> <span style="color:gray; font-size:12px;">vs {ano_anterior}</span>'
                    else:
                        texto_crescimento = f'<span class="growth-indicator" style="color:#d32f2f;">▼ {variacao:.1f}%</span> <span style="color:gray; font-size:12px;">vs {ano_anterior}</span>'
                else:
                    texto_crescimento = '<span style="color:gray; font-size:12px;">Sem dados em período anterior</span>'
        except:
            pass

    st.markdown("---")

    # --- BLOCO DE METRICAS / KPIS COM O CRESCIMENTO ENGENHARADO ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f'<div class="kpi-container"><b>🎯 META SEMESTRAL ({ano_sel})</b><h2>{total_meta:,.0f}</h2><span style="color:gray; font-size:12px;">Procedimentos planejados</span></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="kpi-container" style="border-left-color: #299947;"><b>✅ REALIZADO ({ano_sel})</b><h2>{total_realizado:,.0f}</h2>{texto_crescimento}</div>', unsafe_allow_html=True)
    with kpi3:
        cor_status = "#299947" if perc_total >= 100 else "#004a87"
        st.markdown(f'<div class="kpi-container" style="border-left-color: {cor_status};"><b>📈 EFICIÊNCIA ({ano_sel})</b><h2>{perc_total:.1f}%</h2><span style="color:gray; font-
