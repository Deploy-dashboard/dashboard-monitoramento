from io import BytesIO
from client import Client
import streamlit as st
import pandas as pd
import requests, os
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import warnings

warnings.simplefilter("ignore")

st.set_page_config(page_title="Dashboard", layout="wide", page_icon="images\\icon.png")

def login_page():
  
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("## Repositório CPD")
        st.markdown("Entre com o nome de usuário e senha:")

        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        if st.button(":material/login: Entrar", width='stretch'):
            client = Client()
            if client.login(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

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

def atualiza_id(prog):
    if prog == "Todos":
        return "null"
    else:
        for chave, valor in programas.items():
            if valor == prog:
                return chave  

def report_tab1():
    
    select_sp = st.selectbox("Subprograma",options=lista_sp, key="sp_tab1")
    sp = num_sp(select_sp)
    url = f'http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7027-1707:2025/9/ID_FONTE_DADO="null"&CD_PROGRAMA={sp}'
    response = requests.get(url)
    response.raise_for_status()

    excel = BytesIO(response.content)
    df = pd.DataFrame(pd.read_excel(excel))
    df.insert(loc=3, column="% de registros digitalizados", value=((pd.to_numeric(df["Total de registros digitalizados"]) / pd.to_numeric(df["Total de registros previstos"]))*100).round(2))

    mapa_sub = { s.split(" - ")[0]: " - ".join(s.split(" - ")[1:]) for s in lista_sp if s != "Todos"}
    df.insert(1, "Nome subprograma", df["Cód. subprograma"].astype(str).map(mapa_sub))

    st.markdown("**Tabela:**")
    column_config = {
    col: st.column_config.NumberColumn(
        col,
        format="localized"
    )
    for col in df.columns[2:]
}
    st.dataframe(df, hide_index=True, column_config=column_config)
    
    if sp == "null":

        def get_color(v):
            if v <= 30:
                return 'red'
            elif v <= 50:
                return 'orange'
            elif v <= 70:
                return 'yellow'
            else:
                return 'green'
        
        labels1 = df["Cód. subprograma"].astype(str)+" - "+df["Nome subprograma"]  
        processados1 = df["% de registros processados"]
        colors = [get_color(v) for v in processados1]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=processados1,   
            y=labels1,        
            name="Processados",
            marker_color=colors,
            orientation='h',  
            offsetgroup=1
        ))

        fig.update_layout(
            height=800,
            title="Registros processados por subprograma:",
            xaxis_title="Registros processados (%)",   
            yaxis_title="Subprograma",
            barmode='group',
            xaxis_tickangle=0,
            bargap=0.15,
            bargroupgap=0.05,
            template="plotly_white",
            legend=dict(
                title='',
                orientation='h',
                yanchor='bottom',
                y=1.05,
                xanchor='right',
                x=1,
            )
        )

        st.plotly_chart(fig, width="stretch")

        labels2 = df["Cód. subprograma"].astype(str)  
        decodificados2 = df["% de registros processados"]
        digitalizados2 = df["% de registros digitalizados"]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=labels2,
            y=decodificados2,
            name="Decodificados",
            marker_color='#4169E1',
            offsetgroup=1
        ))

        fig.add_trace(go.Bar(
            x=labels2,
            y=digitalizados2,
            name="Digitalizados",
            marker_color="#008080",
            offsetgroup=2
        ))

        fig.update_layout(
            title="Comparativo de registros digitalizados e processados: ",
            xaxis_title="Código do Subprograma",
            yaxis_title="Registros processados (%)",
            barmode='group',  
            xaxis_tickangle=0,
            bargap=0.15,      
            bargroupgap=0.05, 
            template="plotly_white",
            legend=dict(
                title='',
                orientation='h',
                yanchor='bottom',
                y=1.05,
                xanchor='right',
                x=1,
            )
        )

        st.plotly_chart(fig, width="stretch")

def report_tab2():
    
    @st.cache_data(ttl=3600, show_spinner="Atualizando dados do sistema...")
    def sol(sp, inst):
        url = f'http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7028-1707:2025/9/ID_FONTE_DADO={"null"}&CD_PROGRAMA={sp}&DC_INSTRUMENTO_TIPO={inst}'
        response = requests.get(url)
        content = BytesIO(response.content)
        return pd.DataFrame(pd.read_excel(content))
    
    df = sol("null", "null") 
    instrumentos = df['Instrumento'].unique().tolist()
    instrumentos = sorted(instrumentos)
    instrumentos.insert(0, "Todos")

    select_sp = st.selectbox("Subprograma",options=lista_sp, key="sp_tab2")
    sp = num_sp(select_sp)
    
    inst = st.selectbox("Instrumento", options=instrumentos)
    if inst == "Todos":
        inst = "null"

    table = sol(sp, inst)
    
    table["Total de registros digitalizados"] = pd.to_numeric(table["Total de registros digitalizados"], errors="coerce")
    table["Total de registros previstos"] = pd.to_numeric(table["Total de registros previstos"], errors="coerce")
    table["% de registros digitalizados"] = ((table["Total de registros digitalizados"] / table["Total de registros previstos"]) * 100).round(2)
    
    mapa_sub = { s.split(" - ")[0]: " - ".join(s.split(" - ")[1:]) for s in lista_sp if s != "Todos"}
    table.insert(1, "Nome subprograma", table["Cód. subprograma"].astype(str).map(mapa_sub))

    st.markdown("**Tabela:**")
    column_config = {
    col: st.column_config.NumberColumn(
        col,
        format="localized"
    )
    for col in table.columns[4:]
    }
    st.dataframe(table, hide_index=True, column_config=column_config)


    if (inst != "null") and (sp == "null") and (len(table["Cód. subprograma"].unique()) > 1):
        labels = table["Cód. subprograma"].astype(str).drop_duplicates()
        processados = table["% de registros processados"]
        
        barras = go.Figure()

        barras.add_trace(go.Bar(
            x=labels,
            y=processados,
            name="Decodificados",
            marker_color='#4169E1',
            offsetgroup=0
        ))


        barras.update_layout(
            title="Comparativo de Registros processados: ",
            xaxis_title="Código do Subprograma",
            yaxis_title="Registros processados (%)",
            barmode='group',
            xaxis_tickangle=0,
            bargap=0.15,      
            bargroupgap=0.05, 
            template="plotly_white",
        )

        st.plotly_chart(barras)

    elif (inst == "null") and (sp != "null"):

        table = table.drop_duplicates(subset=['Instrumento'])
        labels = table["Instrumento"].astype(str)
        labels = labels.drop_duplicates()
        processados = table["% de registros processados"]
        
        barras = go.Figure()

        barras.add_trace(go.Bar(
            x=processados,
            y=labels,
            name="processados",
            marker_color='#4169E1',
            orientation='h',
            offsetgroup=1
        ))

        barras.update_layout(
            title=f"Comparativo de Instrumentos processados no subprograma {sp}: ",
            xaxis_title="Registros processados (%)",
            yaxis_title="Instrumento",
            barmode='group',
            xaxis_tickangle=0,
            bargap=0.15,      
            bargroupgap=0.05, 
            template="plotly_white",
                 legend=dict(
                title='',
                orientation='h',
                yanchor='bottom',
                y=1.05,
                xanchor='right',
                x=1,
            )
        )

        barras.update_xaxes(range=[0, 101])
        st.plotly_chart(barras, width='stretch')
        
def report_tab3():
    
    global programas, subprogramas
    subprog = st.selectbox("Subprograma",options=lista_sp, key="subprog_tab3")
    ns = num_sp(subprog)

    @st.cache_data(ttl=3600, show_spinner="Atualizando dados do sistema...")
    def sol(prog, subprog, solicit):
        s = f"http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7029-2307:2025/9/ID_FONTE_DADO={prog}&CD_PROGRAMA={subprog}&DC_SOLICITACAO={solicit}"
        response = requests.get(s)
        content = BytesIO(response.content)
        return pd.DataFrame(pd.read_excel(content))
    
    df  = sol("null", ns, "null")
    resume = df.loc[df["Verificação"] == ("Subtotal")]

    mapa_sub = { s.split(" - ")[0]: " - ".join(s.split(" - ")[1:]) for s in lista_sp if s != "Todos"}
    resume.insert(1, "Nome subprograma", resume["Cód. subprograma"].astype(str).map(mapa_sub))

    st.markdown("**Verificações finalizadas por programa:**")
    column_config = {
    col: st.column_config.NumberColumn(
        col,
        format="localized"
    )
    for col in resume.columns[3:]
    }
    st.dataframe(resume, hide_index=True, column_config=column_config)
    
    labels = resume["Cód. subprograma"].astype(str) 
    verificacoes = resume[f"% de verificações finalizadas"].astype(float)
    alteracao = resume[f"% de alteração das verificações finalizadas"].astype(float)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels,
        y=verificacoes,
        name="Verificações finalizadas",
        marker_color='#4169E1',
        offsetgroup=0,
    ))

    fig.add_trace(go.Bar(
        x=labels,
        y=alteracao,
        name="Alterações finalizadas",
        marker_color='#008080',
        offsetgroup=1,
    ))

    fig.update_layout(
        height=500,
        title="Gráfico comparativo de Verificações finalizadas e total de alteração por Verificação:",
        yaxis = dict(range = [0, 100]),
        xaxis_title="Subprograma",
        yaxis_title="Porcentagem (%)",
        barmode='group',  
        xaxis_tickangle=0,
        bargap=0.15,      
        bargroupgap=0.05, 
        template="plotly_white",
        legend=dict(
            title='',
            orientation='h',
            yanchor='bottom',
            y=1.05,
            xanchor='right',
            x=1
        )
    )


    st.plotly_chart(fig, width="stretch")

    st.subheader("Selecione programa, subprograma e solicitação:")
    df1 = sol("nul", "null", "null")
    verif = df1["Verificação"].unique().tolist()
    if "Subtotal" in verif:
        verif.remove("Subtotal")
    verif.insert(0, "Todos")
    del verif[-1]

    entrada_prog = st.selectbox("Programa", options=list(sorted(programas.values())), key="prog_tab3")
    prog = atualiza_id(entrada_prog)
    if prog != "null":
        opcoes_subprogramas = subprogramas[prog]
        sp = st.selectbox("Subprograma",options=opcoes_subprogramas, key="sp_tab3")
    else:
        sp = str("Todos")
    subprog = num_sp(sp)

    if "solicitacao" not in st.session_state:
        st.session_state.solicitacao = "Todos"

    def limpar():
        st.session_state.solicitacao = "Todos"

    solicitacao = str(st.selectbox("Solicitacao", options=verif, key="solicitacao"))

    st.button(":material/delete: Limpar filtro", on_click=limpar)

    if solicitacao == "Todos":
        solicitacao = "null"


    solicitacao = solicitacao.replace(" ", "%20")
    
    table = sol(prog, subprog, solicitacao)
    table = table[table["Verificação"] != "Subtotal"]
    table = table[table["Cód. subprograma"] != "Total"]
    mapa_sub = { s.split(" - ")[0]: " - ".join(s.split(" - ")[1:]) for s in lista_sp if s != "Todos"}
    table.insert(1, "Nome subprograma", table["Cód. subprograma"].astype(str).map(mapa_sub))

    column_config = {
    col: st.column_config.NumberColumn(
        col,
        format="localized"
    )
    for col in table.columns[3:]
    }
    st.dataframe(table, hide_index=True, column_config=column_config)

   
def report_tab4():

    arquivo = "datas.csv"
    hoje = pd.Timestamp(date.today())

    if "datas" not in st.session_state:
        datas = pd.read_csv(arquivo)
        datas["inicio"] = pd.to_datetime(datas["inicio"], errors="coerce")
        datas["fim"] = pd.to_datetime(datas["fim"], errors="coerce")
        st.session_state.datas = datas

    datas = st.session_state.datas.copy()

    @st.cache_data(ttl=3600, show_spinner="Atualizando dados do sistema...")
    def sol(sp):
        url = (f'http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7027-1707:2025/9/ID_FONTE_DADO="null"&CD_PROGRAMA={sp}')
        response = requests.get(url)
        return pd.read_excel(BytesIO(response.content))

    df_base = sol("null")

    def recalcular_colunas(datas, df_base, hoje):

        datas = datas.dropna(subset=["subprograma"])

        datas = datas.merge(
            df_base[
                [
                    "Cód. subprograma",
                    "Total de registros previstos",
                    "Total de registros digitalizados"
                ]
            ],
            left_on="subprograma",
            right_on="Cód. subprograma",
            how="left"
        )

        datas["previstos"] = datas["Total de registros previstos"]
        datas["digitalizados"] = datas["Total de registros digitalizados"]

        datas.drop(columns=["Cód. subprograma", "Total de registros previstos", "Total de registros digitalizados"], inplace=True)

        datas["% digitalizados"] = (datas["digitalizados"] / datas["previstos"] * 100).round(2)

        mask = datas["inicio"].notna() & datas["fim"].notna()

        datas.loc[mask, "diferenca"] = (datas.loc[mask, "fim"] - datas.loc[mask, "inicio"]).dt.days.clip(lower=1)

        datas.loc[mask, "media dia"] = (datas.loc[mask, "previstos"] / datas.loc[mask, "diferenca"]).round(0)

        dias_passados = (hoje - datas["inicio"]).dt.days.clip(lower=0)

        datas["esperado hoje"] = (datas["media dia"] * dias_passados).clip(lower=0, upper=datas["previstos"]).round(0)

        return datas


    with st.form("form_tab4"):

        datas_editadas = st.data_editor(
            datas,
            num_rows="dynamic",
            disabled=[
                "nome", "previstos", "digitalizados",
                "diferenca", "media dia",
                "esperado hoje", "% digitalizados", "cor"
            ],
            column_config={ 
                "previstos": st.column_config.NumberColumn(format="localized"), 
                "digitalizados": st.column_config.NumberColumn(format="localized"), 
                "inicio": st.column_config.DateColumn(format="DD/MM/YYYY"), 
                "fim": st.column_config.DateColumn(format="DD/MM/YYYY"), 
                "diferenca": None, 
                "media dia": None, 
                "esperado hoje": st.column_config.NumberColumn(format="localized"), 
                "cor": None 
                },  
            hide_index=True
        )

        salvar = st.form_submit_button(":material/save:  Salvar alterações")

    datas_calculadas = recalcular_colunas(datas_editadas.copy(), df_base, hoje)

    st.session_state.datas = datas_calculadas

    if salvar:
        datas_calculadas.to_csv(arquivo, index=False)
        st.success("Alterações salvas com sucesso!")

    datas = st.session_state.datas


    labels = datas["subprograma"].astype(str) + " - " + datas["nome"]

    datas["cor"] = datas.apply(
        lambda row: "green"
        if (row["digitalizados"] >= row["esperado hoje"] or row["digitalizados"] >= row["esperado hoje"] * 0.9) else "red", axis=1)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=datas["% digitalizados"],
        y=labels,
        orientation="h",
        marker_color=datas["cor"],
        name="Digitalizados"
    ))

    fig.update_layout(
        height=800,
        title="Verificação de registros digitalizados por subprograma",
        xaxis_title="Registros digitalizados (%)",
        yaxis_title="Subprograma",
        template="plotly_white"
    )

    st.plotly_chart(fig, width='stretch')


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
        legend_x = -0.28
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



def dashboard():
    
    st.title("Dashboards")
    css = '''
    <style>
        button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
            font-size: 15px; 
            font-weight: bolder;
        }
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Processamento / Instrumento", "Verificação", "Datas digitalização", "Progresso Somativas", "Progresso Formativas"])

    with tab1:
        st.header("Relatórios de processamento:")
        report_tab1()

        st.subheader("Relatório Processamento por instrumento:")
        report_tab2()


    with tab2:
        st.header("Relatório Verificação - Subprograma / Solicitação ")
        report_tab3()

    
    with tab3:
        st.header("Datas das digitalizações")
        st.text("Adicione diretamente na tabela as datas de início e de término dos subprogramas")
        report_tab4()

    
    with tab4:
        st.subheader("Datas das tarefas correspondentes a cada subprograma")
        st.text('Adicione as datas de término de cada tarefa, também é possível adicionar novas linhas diretamente na tabela e colunas pelo formulário abaixo')
        report_tab5()


    with tab5:
        st.subheader("Datas das tarefas correspondentes a cada subprograma")
        st.text('Adicione as datas de término de cada tarefa, também é possível adicionar novas linhas diretamente na tabela e colunas pelo formulário abaixo')
        report_tab6()


def main():
  
  if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

  if not st.session_state.authenticated:
    login_page()
    st.stop()
      
  else:
    dashboard()


if __name__ == "__main__":
  main()
