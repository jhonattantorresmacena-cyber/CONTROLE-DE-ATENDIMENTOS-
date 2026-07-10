# --- SEÇÃO DE CORRELAÇÃO DEFINITIVA (LINHAS DUPLAS INTELIGENTES) ---
    if COL_ALUNOS in df_filtrado.columns:
        st.markdown('<h3 style="color:#004a87;">🔄 Correlação Temporal: Procedimentos vs Quantidade de Alunos</h3>', unsafe_allow_html=True)
        
        df_corr_base = df_filtrado.copy()
        if clinica_sel != "TODAS":
            df_corr_base = df_corr_base[df_corr_base[COL_CLINICA] == clinica_sel]
            
        df_corr = df_corr_base.groupby(COL_CLINICA).agg({
            COL_ALUNOS: 'sum',
            'TOTAL_REALIZADO_LINHA': 'sum'
        }).reset_index()
        
        df_corr = df_corr.sort_values(by='TOTAL_REALIZADO_LINHA', ascending=False)
        
        fig_corr = go.Figure()
        
        # 1. LINHA: Quantidade de Procedimentos Realizados (Eixo Y Esquerdo - Azul)
        fig_corr.add_trace(go.Scatter(
            name="Procedimentos Realizados",
            x=df_corr[COL_CLINICA],
            y=df_corr['TOTAL_REALIZADO_LINHA'],
            mode='lines+markers+text',
            marker=dict(size=10, color='#004a87', symbol='square'),
            line=dict(width=4, color='#004a87'),
            # Transforma o texto aplicando a tag <b> para ficar em negrito com segurança
            text=df_corr['TOTAL_REALIZADO_LINHA'].apply(lambda x: f"<b>{x:,.0f}</b>"),
            textposition='top center', 
            textfont=dict(color='#004a87'), # Removido o 'font_weight' incorreto
            hovertemplate="<b>%{x}</b><br>Procedimentos: %{y:,.0f}<extra></extra>"
        ))
        
        # 2. LINHA: Quantidade de Alunos (Eixo Y Direito - Laranja)
        fig_corr.add_trace(go.Scatter(
            name="Quantidade de Alunos",
            x=df_corr[COL_CLINICA],
            y=df_corr[COL_ALUNOS],
            mode='lines+markers+text',
            marker=dict(size=10, color='#ff9800', symbol='circle'),
            line=dict(width=4, color='#ff9800'),
            yaxis='y2',
            # Transforma o texto aplicando a tag <b> para ficar em negrito com segurança
            text=df_corr[COL_ALUNOS].apply(lambda x: f"<b>{x:,.0f}</b>"),
            textposition='bottom center', 
            textfont=dict(color='#ff9800'), # Removido o 'font_weight' incorreto
            hovertemplate="<b>%{x}</b><br>Alunos: %{y:,.0f}<extra></extra>"
        ))

        # Margem extra de 25% (1.25) para que o texto mais alto nunca raspe no topo do gráfico
        max_y1 = df_corr['TOTAL_REALIZADO_LINHA'].max() * 1.25 if not df_corr.empty else 100
        max_y2 = df_corr[COL_ALUNOS].max() * 1.25 if not df_corr.empty else 100

        fig_corr.update_layout(
            height=430,
            margin=dict(t=60, b=40, l=10, r=10),
            legend=dict(orientation="h", y=1.18, x=0),
            hovermode="x unified",
            plot_bgcolor='white',
            yaxis=dict(
                title=dict(text="Procedimentos Realizados", font=dict(color="#004a87", size=13)), 
                tickfont=dict(color="#004a87"),
                gridcolor="#f1f3f5",
                range=[0, max_y1]
            ),
            yaxis2=dict(
                title=dict(text="Quantidade de Alunos", font=dict(color="#ff9800", size=13)), 
                tickfont=dict(color="#ff9800"), 
                overlaying='y', 
                side='right',
                showgrid=False,
                range=[0, max_y2]
            )
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        st.markdown("---")
