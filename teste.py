import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import requests

st.set_page_config(layout='wide')
res_prog = requests.get(f'http://10.0.10.22:41112/gw/reports/documentos/filter/CAED7029-2307:2025/null/null')
data_prog = res_prog.json()
dados_prog = data_prog[0]["dados"]
programas = {item["key"]: item["value"] for item in dados_prog}
programas["Todos"] = "Todos"

id_prog = programas.keys()
sp = {}
for key in id_prog:
    if key != "Todos":
        res_sp = requests.get(f'http://10.0.10.22:41112/gw/reports/documentos/filterssrs/CAED7029-2307:2025/58/{key}/ID_FONTE_DADO={key}&CD_PROGRAMA=undefined&DC_SOLICITACAO=undefined')
        data_sp = res_sp.json()
        sp[key] = data_sp[0]["dados"]

subprogramas = {
    k: [item["value"] for item in v]
    for k, v in sp.items()
}

lista_aux = []
lista_sp = []
for valor in subprogramas.values():
    lista_aux.append(valor)
for sublista in lista_aux:
    for item in sublista:
        lista_sp.append(item)

lista_sp.insert(0, "Todos")
lista_sp = lista_sp[:1] + sorted(lista_sp[1:])

def num_sp(sp):
    if sp != "Todos":
        return int(sp[0:4])
    return "null"

lista_num_sp = []
for i in lista_sp:
    lista_num_sp.append(num_sp(i))

arquivo_geral = 'progresso.csv'
df_geral = pd.DataFrame(pd.read_csv(arquivo_geral))
colunas_data = df_geral.columns[2:]
for col in colunas_data:
    df_geral[col] = pd.to_datetime(df_geral[col], errors='coerce')
for sp in lista_num_sp:
    if (sp != "null") and (int(sp) not in df_geral["subprograma"].values):
        df_geral.loc[len(df_geral), 'subprograma'] = int(sp)

mapa_sub = {s.split(" - ")[0]: " - ".join(s.split(" - ")[1:]) for s in lista_sp if s != "Todos"}
mask = df_geral["nome"].isna()
df_geral.loc[mask, "nome"] = (df_geral.loc[mask, "subprograma"].astype(str).map(mapa_sub))
df_formativa = df_geral[df_geral['nome'].str.contains('FORMATIVA')]
df_somativa = df_geral[~df_geral['nome'].str.contains('FORMATIVA')]
df_geral.to_csv(arquivo_geral, index=False)
df_formativa = df_formativa[[
        'subprograma', 'nome', 'dv_banco', 'dv_producao', 
        'imagem', 'conf_hmg', 'conf_pro_t1', 'recuperacao',
       'recuperacao_t2', 'nm_aluno', 'categorizacao_tn', 'rel_categroizacao',
       'certif_obj', 'certif_ctx', 'certif_nap', 'certif_esc', 'certif_sinc',
       'certif_co', 'co_rel_pgto', 'medida_obj', 'medida_ctx', 'medida_esc',
       'pareamento', 'rel_tratamento', 'rel_verificacao'
       ]]
df_formativa.to_csv("progresso_formativa.csv", index=False)
df_somativa.to_csv("progresso_somativa.csv", index=False)


def criar_grafico_progresso(df_aux, ordem_tarefas, num_linhas):
    
    mapa_tarefas = {tarefa: i for i, tarefa in enumerate(ordem_tarefas)}
    df_aux["x_linha"] = df_aux["tarefas"].map(mapa_tarefas)
    max_nos = df_aux["x_linha"].max()
    ordem_y = df_aux["nome"].drop_duplicates().tolist()
    df_aux["Data_hover"] = df_aux["Data"].dt.strftime("%d/%m/%Y")
    df_aux["Data_hover"] = df_aux["Data_hover"].fillna("Sem data definida")
    
    df_aux = df_aux.sort_values(by='nome', ascending=False)
    
    fig = px.scatter(
        df_aux,
        x="x_linha",
        y="nome",
        category_orders={
            "nome": ordem_y
        },
        color="Status",
        size="size",
        size_max=19,
        hover_name="tarefas",
        hover_data={
            "tarefas": False,
            "Data_hover": True,
            "x_linha": False,
            "nome": True,
            "Status": True
        },
        color_discrete_map={
            "Concluído": "green",
            "Pendente": "gray",
            "Finaliza hoje": "yellow",
            "Atrasado": "red"
        }
    )
    
    fig.update_xaxes(
        range=[-0.5, max_nos + 0.5],
        tickmode="array",
        side='top',
        tickvals=list(mapa_tarefas.values()),
        ticktext=list(mapa_tarefas.keys()),
        tickangle=90,
        showgrid=False,
        zeroline=False
    )
    
    for trace in fig.data:
        status = trace.name
        df_trace = df_aux[df_aux["Status"] == status]
        trace.customdata = df_trace[["nome", "tarefas", "Data_hover"]].values
        trace.hovertemplate = (
            "<b>Subprograma:</b> %{customdata[0]}<br>"
            "<b>Tarefa:</b> %{customdata[1]}<br>"
            "<b>Data:</b> %{customdata[2]}"
            "<extra></extra>"
        )
    
    altura = min(max(400, num_linhas * 80 + 200), 1200)
    
    if num_linhas <= 5:
        legend_y = 1.3
        legend_x = -0.25
    else:
        legend_y = 1
        legend_x = -0.29
    
    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        height=altura,
        hoverlabel=dict(
            bgcolor="black",
            font_size=16,
            font_family="Arial",
            bordercolor="black",
            align="left",
            namelength=-1
        ),
        legend=dict(
            title='',
            orientation='h',
            xanchor='left',
            yanchor='top',
            y=legend_y,
            x=legend_x,
            xref='paper',
            yref='paper'
        )
    )
    
    return fig


def processar_tarefas(df, arquivo_tarefas):
    
    colunas_tarefas = df.columns[2:]
    linhas = []
    
    for idx, row in df.iterrows():
        for tarefa in colunas_tarefas:
            data_termino = row[tarefa]
            linhas.append(
                dict(
                    Projeto=str(row['subprograma']) + ' - ' + row['nome'],
                    Tarefa=tarefa,
                    ID=f"{row['nome']}|{tarefa}",
                    Data=data_termino
                )
            )
    
    try:
        df_aux = pd.read_csv(arquivo_tarefas)
        df_aux["concluido"] = df_aux["concluido"].fillna(False).astype(bool)
    except FileNotFoundError:
        df_aux = pd.DataFrame(columns=["nome", "tarefas", "concluido"])
        df_aux["concluido"] = df_aux["concluido"].astype(bool)
    
    df_marcos = pd.DataFrame(linhas)
    df_marcos.rename(
        columns={
            "Projeto": "nome",
            "Tarefa": "tarefas",
        },
        inplace=True
    )
    
    df_aux = df_marcos.merge(
        df_aux,
        on=["nome", "tarefas"],
        how="left"
    )
    df_aux["concluido"] = df_aux["concluido"].fillna(False).astype(bool)
    
    if 'Data_y' in df_aux.columns:
        df_aux.drop(columns='Data_y', inplace=True)
    if 'Data_x' in df_aux.columns:
        df_aux.rename(columns={'Data_x': 'Data'}, inplace=True)
    if 'ID_y' in df_aux.columns:
        df_aux.drop(columns='ID_y', inplace=True)
    if 'ID_x' in df_aux.columns:
        df_aux.drop(columns='ID_x', inplace=True)
    
    df_aux["Status"] = df_aux["concluido"].map({True: 'Concluído', False: 'Pendente'})
    df_aux['size'] = int(5)
    
    hoje = pd.Timestamp(date.today())
    df_aux.loc[(df_aux["Status"] == "Pendente") & (df_aux["Data"] == hoje), "Status"] = "Finaliza hoje"
    df_aux.loc[(df_aux["Status"] == "Pendente") & (df_aux["Data"] < hoje), "Status"] = "Atrasado"
    
    return df_aux


def renderizar_editor_progresso(df, tab_key, column_configs):
    
    with st.form(key=tab_key):
        progresso = st.data_editor(
            df,
            num_rows="dynamic",
            column_config=column_configs,
            key=f'editor_{tab_key}'
        )
        
        nova_coluna = st.text_input("Adicionar nova coluna de tarefas")
        submitted = st.form_submit_button(":material/save: Salvar alterações")
    
    return progresso, nova_coluna, submitted


def renderizar_quadro_tarefas(df_aux, subs, tab_key):
    
    st.subheader("Quadro de Tarefas")
    select_sub = st.selectbox("Escolha um subprograma", options=subs, key=f'select_sub_{tab_key}')
    
    with st.form(key=f"quadro_tarefas_{tab_key}"):
        col = st.columns(1)[0]
        
        with col:
            with st.container(border=True):
                st.markdown(f"**{select_sub}**")
                
                tarefas_sub = df_aux[df_aux["nome"] == select_sub]
                
                for idx, row in tarefas_sub.iterrows():
                    marcado = st.checkbox(
                        row["tarefas"],
                        value=row["concluido"],
                        key=f"{tab_key}_{select_sub}_{idx}"
                    )
                    
                    df_aux.loc[
                        (df_aux["nome"] == select_sub) &
                        (df_aux["tarefas"] == row["tarefas"]),
                        "concluido"
                    ] = marcado
        
        enviado = st.form_submit_button(":material/save: Salvar progresso das tarefas")
    
    return enviado, df_aux


def atualizar_csv_geral(arquivo_somativa, arquivo_formativa):
    df_somativa = pd.read_csv(arquivo_somativa)
    df_formativa = pd.read_csv(arquivo_formativa)
    
    for col in df_somativa.columns[2:]:
        df_somativa[col] = pd.to_datetime(df_somativa[col], errors='coerce')
    for col in df_formativa.columns[2:]:
        df_formativa[col] = pd.to_datetime(df_formativa[col], errors='coerce')
    
    df_geral = pd.concat([df_somativa, df_formativa], ignore_index=True)
    df_geral = df_geral.sort_values(by='subprograma')
    
    df_geral.to_csv('progresso.csv', index=False)


def report_progresso(arquivo, tab_key, session_key, arquivo_tarefas):
    
    st.session_state['active_tab'] = tab_key
    
    if session_key not in st.session_state:
        df = pd.read_csv(arquivo)
        colunas_data = df.columns[2:]
        for col in colunas_data:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        st.session_state[session_key] = df
    
    df = st.session_state[session_key].copy()
    
    column_configs = {}
    for col in df.columns[2:]:
        column_configs[col] = st.column_config.DateColumn(col, format="DD/MM/YYYY")
    
    progresso, nova_coluna, submitted = renderizar_editor_progresso(df, tab_key, column_configs)
    
    if submitted:
        df_final = progresso.copy()
        
        if f"editor_{tab_key}" in st.session_state:
            estado_editor = st.session_state[f"editor_{tab_key}"]
            
            if "columns" in estado_editor:
                ordem_colunas = estado_editor["columns"]
                df_final = df_final[ordem_colunas]
        
        if nova_coluna:
            nova_coluna = nova_coluna.strip()
            
            if nova_coluna not in df_final.columns:
                df_final[nova_coluna] = pd.NaT
                df_final[nova_coluna] = df_final[nova_coluna].astype("datetime64[ns]")
                st.success("Dados atualizados com sucesso!")
            else:
                st.warning("Coluna já existe!")
        
        colunas_tarefa = df_final.columns[2:]
        mask_validas = df_final[colunas_tarefa].notna().any(axis=1) | df_final['nome'].notna()
        df_final = df_final[mask_validas]
        
        st.session_state[session_key] = df_final
        df_final["subprograma"] = df_final["subprograma"].astype(int)
        df_final = df_final.sort_values(by='subprograma')
        
        df_final.to_csv(arquivo, index=False)
        
        if 'somativa' in arquivo:
            atualizar_csv_geral('progresso_somativa.csv', 'progresso_formativa.csv')
        else:
            atualizar_csv_geral('progresso_somativa.csv', 'progresso_formativa.csv')
        
        st.rerun()
    
    df_aux = processar_tarefas(st.session_state[session_key], arquivo_tarefas)
    
    df = st.session_state[session_key].copy()
    df["subprograma"] = df["subprograma"].astype(int)
    subs = (df["subprograma"].astype(str) + " - " + df["nome"]).unique()
    
    enviado, df_aux_modificado = renderizar_quadro_tarefas(df_aux, subs, tab_key)
    
    if enviado:
        df_aux_modificado[["nome", "tarefas", "concluido"]].drop_duplicates().to_csv(arquivo_tarefas, index=False)
        st.success("Progresso das tarefas salvo!")
        st.rerun()  
    
    df_aux_modificado["Status"] = df_aux_modificado["concluido"].map({True: 'Concluído', False: 'Pendente'})
    df_aux_modificado['size'] = int(5)
    
    hoje = pd.Timestamp(date.today())
    df_aux_modificado.loc[(df_aux_modificado["Status"] == "Pendente") & (df_aux_modificado["Data"] == hoje), "Status"] = "Finaliza hoje"
    df_aux_modificado.loc[(df_aux_modificado["Status"] == "Pendente") & (df_aux_modificado["Data"] < hoje), "Status"] = "Atrasado"
    
    ordem_tarefas = df_aux_modificado["tarefas"].dropna().unique().tolist()
    num_linhas = len(df_aux_modificado["nome"].unique())
    fig = criar_grafico_progresso(df_aux_modificado, ordem_tarefas, num_linhas)
    
    st.subheader("Gráfico de progresso")
    st.text("Acompanhe o progresso das tarefas referentes a cada subprograma")
    st.plotly_chart(fig, use_container_width=True, key=f'chart_{tab_key}')


def report_tab5():
    report_progresso(
        arquivo='progresso_somativa.csv',
        tab_key='tab5',
        session_key='df_tab5',
        arquivo_tarefas='tarefas_somativa.csv'
    )


def report_tab6():
    report_progresso(
        arquivo='progresso_formativa.csv',
        tab_key='tab6',
        session_key='df_tab6',
        arquivo_tarefas='tarefas_formativa.csv'
    )


tab1, tab2 = st.tabs(['Progresso Somativas', 'Progresso Formativas'])

with tab1:
    report_tab5()

with tab2:
    report_tab6()