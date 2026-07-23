import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
import io

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="FASICLIN - Intelligence Dashboard", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ESTILIZAÇÃO CSS CUSTOMIZADA (LAYOUT EXECUTIVO CLEAN)
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
    }
    .main-header {
        background: linear-gradient(135deg, #003366 0%, #004a87 100%);
        padding: 20px 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-weight: 700;
        margin: 0;
        font-size: 26px;
    }
    .main-header p {
        color: #d0e1f9;
        margin: 5px 0 0 0;
        font-size: 14px;
    }
    .kpi-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-title {
        color: #64748b;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        color: #0f172a;
        font-size: 28px;
        font-weight: 800;
        margin: 8px 0;
    }
    .kpi-sub {
        font-size: 12px;
        color: #64748b;
    }
    .course-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 18px;
        border-left: 4px solid #004a87;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. LEITURA E CARREGAMENTO DOS DADOS
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
            df_temp = pd.read_csv(url, dtype=str)
            
            df_temp.columns = [
                str(c).replace('\n', ' ').replace('\r', ' ').strip().upper() 
                for c in df_temp.columns
            ]
            df_temp.columns = [" ".join(c.split()) for c in df_temp.columns]
            
            df_temp['UNIDADE_NOME'] = nome_aba
            lista_dfs.append(df_temp)
        except Exception:
            pass
            
    return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else pd.DataFrame()

df_raw = load_all_data()

if not df_raw.empty:
    COL_CLINICA = "CLINICA"
    COL_ANO = "ANO LETIVO"
    COL_META = "QUANTIDADE DE PROCEDIMENTO POR SEMESTRE"
    COL_ALUNOS = "QUANTIDADE DE ALUNOS"
    MESES = ["FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

    if COL_META not in df_raw.columns:
        for c in df_raw.columns:
            if "PROCEDIMENTO" in c and "SEMESTRE" in c:
                COL_META = c
                break

    colunas_numericas = [COL_META] + [m for m in MESES if m in df_raw.columns]
    if COL_ALUNOS in df_raw.columns:
        colunas_numericas.append(COL_ALUNOS)

    for c in colunas_numericas:
        if c in df_raw.columns:
            df_raw[c] = df_raw[c].astype(str).str.strip()
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce').fillna(0)

    df_raw = df_raw.dropna(subset=[COL_CLINICA])
    df_raw = df_raw[df_raw[COL_CLINICA].astype(str).str.strip() != ""]

    meses_existentes = [m for m in MESES if m in df_raw.columns]
    df_raw['TOTAL_REALIZADO_LINHA'] = df_raw[meses_existentes].sum(axis=1) if meses_existentes else 0

    # --- CABEÇALHO DO PAINEL ---
    st.markdown("""
        <div class="main-header">
            <h1>🏥 FASICLIN - Dashboard de Gestão & Performance</h1>
            <p>Acompanhamento estratégico de metas de procedimentos e produtividade acadêmica</p>
        </div>
    """, unsafe_allow_html=True)

    # --- FILTROS HORIZONTAIS NO TOPO ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        ordem_unidades = ["SINOP", "SORRISO", "CUIABA", "RONDONOPOLIS", "PRIMAVERA"]
        unidades_disponiveis = [u for u in ordem_unidades if u in df_raw['UNIDADE_NOME'].unique().tolist()]
        for u in df_raw['UNIDADE_NOME'].unique():
            if u not in unidades_disponiveis:
                unidades_disponiveis.append(u)
        unidade_sel = st.selectbox("📍 Unidade / Campus:", unidades_disponiveis)
    
    df_unidade = df_raw[df_raw['UNIDADE_NOME'] == unidade_sel].copy()

    with col_f2:
        if COL_ANO in df_unidade.columns:
            anos_disponiveis = ["TODOS"] + sorted(df_unidade[COL_ANO].dropna().unique().tolist(), reverse=True)
            ano_sel = st.selectbox("📅 Ano Letivo Principal:", anos_disponiveis)
        else:
            ano_sel = "Geral"

    if ano_sel == "TODOS" or ano_sel == "Geral":
        df_filtrado = df_unidade.copy()
    else:
        df_filtrado = df_unidade[df_unidade[COL_ANO] == ano_sel]

    with col_f3:
        clinicas_disponiveis = ["TODAS"] + sorted(df_filtrado[COL_CLINICA].dropna().unique().tolist())
        clinica_sel = st.selectbox("🩺 Curso / Clínica:", clinicas_disponiveis)

    st.markdown("<br>", unsafe_allow_html=True)

    df_kpi_atual = df_filtrado.copy()
    if clinica_sel != "TODAS":
        df_kpi_atual = df_kpi_atual[df_kpi_atual[COL_CLINICA] == clinica_sel]

    # --- CÁLCULOS EXECUTIVOS ---
    total_meta = df_kpi_atual[COL_META].sum()
    total_realizado = df_kpi_atual['TOTAL_REALIZADO_LINHA'].sum()
    falta = max(0, total_meta - total_realizado)
    perc_total = (total_realizado / total_meta * 100) if total_meta > 0 else 0
    total_alunos = df_kpi_atual[COL_ALUNOS].sum() if COL_ALUNOS in df_kpi_atual.columns else 0

    # --- CARDS DE KPI SUPERIORES ---
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">🎯 Meta Semestral</div>
                <div class="kpi-value">{total_meta:,.0f}</div>
                <div class="kpi-sub">Procedimentos Projetados</div>
            </div>
        """, unsafe_allow_html=True)
        
    with k2:
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 4px solid #10b981;">
                <div class="kpi-title">✅ Realizado no Período</div>
                <div class="kpi-value" style="color:#10b981;">{total_realizado:,.0f}</div>
                <div class="kpi-sub">Procedimentos Concluídos</div>
            </div>
        """, unsafe_allow_html=True)

    with k3:
        cor_efic = "#10b981" if perc_total >= 100 else "#3b82f6" if perc_total >= 70 else "#ef4444"
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 4px solid {cor_efic};">
                <div class="kpi-title">📈 Atingimento de Meta</div>
                <div class="kpi-value" style="color:{cor_efic};">{perc_total:.1f}%</div>
                <div class="kpi-sub">Eficiência Operacional</div>
            </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 4px solid #f59e0b;">
                <div class="kpi-title">👥 Corpo Discente</div>
                <div class="kpi-value" style="color:#f59e0b;">{total_alunos:,.0f}</div>
                <div class="kpi-sub">Alunos em Prática</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ABAS DE NAVEGAÇÃO ---
    aba_geral, aba_detalhada, aba_dados = st.tabs(["📊 Visão Geral Executiva", "📋 Desempenho por Curso", "💾 Tabela de Dados"])

    with aba_geral:
        c_left, c_right = st.columns(2)

        with c_left:
            st.subheader("📊 Meta vs. Realizado por Clínica")
            
            agg_dict = {COL_META: 'sum', 'TOTAL_REALIZADO_LINHA': 'sum'}
            if COL_ALUNOS in df_kpi_atual.columns:
                agg_dict[COL_ALUNOS] = 'sum'

            resumo = df_kpi_atual.groupby(COL_CLINICA, as_index=False).agg(agg_dict).rename(columns={'TOTAL_REALIZADO_LINHA': 'REALIZADO'})

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name='Realizado', 
                x=resumo[COL_CLINICA], 
                y=resumo['REALIZADO'], 
                marker_color='#10b981',
                text=resumo['REALIZADO'], 
                textposition='auto'
            ))
            fig_bar.add_trace(go.Bar(
                name='Meta Semestral', 
                x=resumo[COL_CLINICA], 
                y=resumo[COL_META], 
                marker_color='#004a87',
                text=resumo[COL_META], 
                textposition='auto'
            ))

            fig_bar.update_layout(
                barmode='group',
                height=350,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(t=20, b=20, l=10, r=10),
                legend=dict(orientation="h", y=1.1, x=0)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_right:
            st.subheader("📅 Curva de Evolução Mensal")
            
            df_meses = df_kpi_atual.melt(
                id_vars=[COL_CLINICA], 
                value_vars=meses_existentes,
                var_name='MÊS', 
                value_name='ATENDIMENTOS'
            )
            df_evolucao = df_meses.groupby('MÊS', as_index=False)['ATENDIMENTOS'].sum()
            df_evolucao['MÊS'] = pd.Categorical(df_evolucao['MÊS'], categories=MESES, ordered=True)
            df_evolucao = df_evolucao.sort_values('MÊS')

            fig_line = px.line(
                df_evolucao, 
                x='MÊS', 
                y='ATENDIMENTOS',
                markers=True,
                text='ATENDIMENTOS'
            )
            fig_line.update_traces(
                line_color='#004a87', 
                line_width=3, 
                marker_size=8,
                textposition="top center"
            )
            fig_line.update_layout(
                height=350,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(t=20, b=20, l=10, r=10),
                xaxis_title="",
                yaxis_title="Qtd. Procedimentos"
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("---")

        # --- ALTERAÇÃO 1: GRÁFICO COMPARATIVO EM LINHA ---
        st.subheader("📈 Comparativo da Evolução Mensal entre Anos Letivos")
        
        df_unidade_comp = df_unidade.copy()
        if clinica_sel != "TODAS":
            df_unidade_comp = df_unidade_comp[df_unidade_comp[COL_CLINICA] == clinica_sel]

        # Reformata para mesclar meses e anos
        df_comp_meses = df_unidade_comp.melt(
            id_vars=[COL_ANO, COL_CLINICA],
            value_vars=meses_existentes,
            var_name='MÊS',
            value_name='ATENDIMENTOS'
        )
        
        df_comp_evol = df_comp_meses.groupby([COL_ANO, 'MÊS'], as_index=False)['ATENDIMENTOS'].sum()
        df_comp_evol['MÊS'] = pd.Categorical(df_comp_evol['MÊS'], categories=MESES, ordered=True)
        df_comp_evol = df_comp_evol.sort_values('MÊS')

        fig_comp_line = px.line(
            df_comp_evol,
            x='MÊS',
            y='ATENDIMENTOS',
            color=COL_ANO,
            markers=True,
            text='ATENDIMENTOS',
            color_discrete_sequence=['#004a87', '#10b981', '#f59e0b', '#8b5cf6']
        )
        
        fig_comp_line.update_traces(
            line_width=3, 
            marker_size=8,
            textposition="top center"
        )
        
        fig_comp_line.update_layout(
            height=380,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(t=20, b=20, l=10, r=10),
            legend=dict(orientation="h", y=1.1, x=0, title="Ano Letivo:"),
            xaxis_title="",
            yaxis_title="Procedimentos Realizados"
        )
        st.plotly_chart(fig_comp_line, use_container_width=True)

    with aba_detalhada:
        st.subheader("📋 Detalhamento e Média por Aluno")
        
        for i in range(0, len(resumo), 3):
            cols = st.columns(3)
            sub_df = resumo.iloc[i:i+3]
            for idx, (_, row) in enumerate(sub_df.iterrows()):
                p_ind = (row['REALIZADO'] / row[COL_META] * 100) if row[COL_META] > 0 else 0
                qtd_alunos = int(row[COL_ALUNOS]) if COL_ALUNOS in row else 0
                media_atend_aluno = (row['REALIZADO'] / qtd_alunos) if qtd_alunos > 0 else 0
                
                with cols[idx]:
                    st.markdown(f"""
                    <div class="course-card">
                        <h4 style="margin:0 0 10px 0; color:#004a87;">{row[COL_CLINICA]}</h4>
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span>Realizado: <b>{int(row['REALIZADO']):,}</b></span>
                            <span>Meta: <b>{int(row[COL_META]):,}</b></span>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:13px; color:#64748b; margin-bottom:10px;">
                            <span>👥 Alunos: <b>{qtd_alunos}</b></span>
                            <span>⚡ Média/Aluno: <b>{media_atend_aluno:.1f}</b></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(min(p_ind/100, 1.0))
                    st.caption(f"Aproveitamento: **{p_ind:.1f}%**")

    # --- ALTERAÇÃO 2: DOWNLOAD DA TABELA EM EXCEL (.XLSX) ---
    with aba_dados:
        st.subheader("💾 Dados Consolidados")
        
        colunas_exibir = [COL_CLINICA, COL_ANO, COL_ALUNOS, COL_META, 'TOTAL_REALIZADO_LINHA'] + meses_existentes
        cols_presentes = [c for c in colunas_exibir if c in df_kpi_atual.columns]
        
        df_exibicao = df_kpi_atual[cols_presentes].copy()
        st.dataframe(df_exibicao, use_container_width=True)
        
        # Gerador do arquivo Excel em memória
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            df_exibicao.to_excel(writer, index=False, sheet_name='Consolidado_FASICLIN')
        buffer_excel.seek(0)

        st.download_button(
            label="📊 Baixar Tabela Completa em Excel (.xlsx)",
            data=buffer_excel,
            file_name=f"FASICLIN_{unidade_sel}_{ano_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.warning("Nenhum dado pôde ser carregado. Verifique o compartilhamento da planilha no Google Sheets.")
