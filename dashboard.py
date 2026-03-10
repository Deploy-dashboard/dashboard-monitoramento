from io import BytesIO
from client import Client
import streamlit as st
import pandas as pd
import requests, warnings
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
from db import conecta_banco
from sqlalchemy import text

engine = conecta_banco()
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
                st.session_state.username = username
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

    hoje = pd.Timestamp(date.today())

    if "datas" not in st.session_state:
        datas = pd.read_sql("SELECT * FROM DATAS", engine)
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

        datas["porcent_digitalizados"] = (datas["digitalizados"] / datas["previstos"] * 100).round(2)

        mask = datas["inicio"].notna() & datas["fim"].notna()

        datas.loc[mask, "diferenca"] = (datas.loc[mask, "fim"] - datas.loc[mask, "inicio"]).dt.days.clip(lower=1)

        datas.loc[mask, "media_dia"] = (datas.loc[mask, "previstos"] / datas.loc[mask, "diferenca"]).round(0)

        dias_passados = (hoje - datas["inicio"]).dt.days.clip(lower=0)

        datas["esperado_hoje"] = (datas["media_dia"] * dias_passados).clip(lower=0, upper=datas["previstos"]).round(0)

        return datas


    with st.form("form_tab4"):

        datas_editadas = st.data_editor(
            datas,
            num_rows="dynamic",
            disabled=[
                "nome", "previstos", "digitalizados",
                "diferenca", "media_dia",
                "esperado_hoje", "porcent_digitalizados", "cor"
            ],
            column_config={ 
                "previstos": st.column_config.NumberColumn(format="localized"), 
                "digitalizados": st.column_config.NumberColumn(format="localized"), 
                "inicio": st.column_config.DateColumn(format="DD/MM/YYYY"), 
                "fim": st.column_config.DateColumn(format="DD/MM/YYYY"), 
                "diferenca": None, 
                "media_dia": None, 
                "esperado_hoje": st.column_config.NumberColumn(format="localized"), 
                "cor": None 
                },  
            hide_index=True
        )

        salvar = st.form_submit_button(":material/save:  Salvar alterações")

    datas_calculadas = recalcular_colunas(datas_editadas.copy(), df_base, hoje)

    st.session_state.datas = datas_calculadas

    if salvar:
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM [DATAS]"))
                datas_calculadas.to_sql("DATAS", conn, if_exists="append", index=False)
            st.success("Alterações salvas com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    datas = st.session_state.datas


    labels = datas["subprograma"].astype(str) + " - " + datas["nome"]

    datas["cor"] = datas.apply(
        lambda row: "green"
        if (row["digitalizados"] >= row["esperado_hoje"] or row["digitalizados"] >= row["esperado_hoje"] * 0.9) else "red", axis=1)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=datas["porcent_digitalizados"],
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


# arquivo_geral = 'progresso.csv'
# df_geral = pd.DataFrame(pd.read_csv(arquivo_geral))
# colunas_data = df_geral.columns[2:]
# for col in colunas_data:
#     df_geral[col] = pd.to_datetime(df_geral[col], errors='coerce')
# for sp in lista_num_sp:
#     if (sp != "null") and (int(sp) not in df_geral["subprograma"].values):
#         df_geral.loc[len(df_geral), 'subprograma'] = int(sp)

# mapa_sub = {s.split(" - ")[0]: " - ".join(s.split(" - ")[1:]) for s in lista_sp if s != "Todos"}
# mask = df_geral["nome"].isna()
# df_geral.loc[mask, "nome"] = (df_geral.loc[mask, "subprograma"].astype(str).map(mapa_sub))
# df_formativa = df_geral[df_geral['nome'].str.contains('FORMATIVA')]
# df_somativa = df_geral[~df_geral['nome'].str.contains('FORMATIVA')]
# df_geral.to_csv(arquivo_geral, index=False)
# df_formativa = df_formativa[['subprograma', 'nome', 'dv_banco',
# 'dv_producao',
# 'categorizacao_tn',
# 'rel_categroizacao',
# 'certif_sinc',
# 'nm_aluno',
# 'certif_obj',
# 'certif_ctx',
# 'certif_esc',
# 'certif_co',
# 'co_rel_pgto',
# 'medida_obj',
# 'medida_ctx',
# 'medida_esc',
# 'pareamento',
# 'rel_verificacao',]]

# df_somativa = df_somativa[['subprograma', 'nome', 'dv_banco',
# 'dv_producao',
# 'frop1',
# 'frop1_ret',
# 'frop2',
# 'frop3',
# 'recuperacao',  
# 'recuperacao_t2',
# 'recuperacao_ex',
# 'recuperacao_ex_ret',
# 'nm_aluno',
# 'categorizacao_tn',
# 'rel_categroizacao',
# 'certif_obj',
# 'certif_ctx',
# 'certif_nap',
# 'medida_obj',
# 'medida_ctx',
# 'rel_tratamento',
# 'rel_verificacao']]

# if "recuperacao_ex" not in df_somativa.columns:
#     df_somativa.insert(10, "recuperacao_ex", value=pd.NaT)
# if "recuperacao_ex_ret" not in df_somativa.columns:
#     df_somativa.insert(11, "recuperacao_ex_ret", value=pd.NaT)
# df_formativa.to_csv("progresso_formativa.csv", index=False)
# df_somativa.to_csv("progresso_somativa.csv", index=False)

def criar_grafico_progresso(df_aux, ordem_tarefas, num_linhas):
    
    df_aux["Data"] = pd.to_datetime(df_aux["Data"], errors="coerce")
    df_aux["data_conclusao"] = pd.to_datetime(df_aux["data_conclusao"], errors="coerce")

    mapa_tarefas = {tarefa: i for i, tarefa in enumerate(ordem_tarefas)}
    df_aux["x_linha"] = df_aux["tarefas"].map(mapa_tarefas)

    max_nos = df_aux["x_linha"].max() if not df_aux.empty else 0
    ordem_y = df_aux["nome"].drop_duplicates().tolist()

    mask = df_aux["Data"].notna() & df_aux["data_conclusao"].notna() & (df_aux["Data"] < df_aux["data_conclusao"])

    df_aux.loc[mask, "atraso"] = (df_aux.loc[mask, "data_conclusao"] - df_aux.loc[mask, "Data"]).dt.days.clip(lower=1)

    df_aux = df_aux.sort_values(by="nome", ascending=False)

    df_aux["Data_hover"] = df_aux["Data"].dt.strftime("%d/%m/%Y").fillna("Sem data definida")
    df_aux["Data_conclusao_hover"] = df_aux["data_conclusao"].dt.strftime("%d/%m/%Y").fillna("")

    df_aux["atraso"] = df_aux["atraso"].fillna("")
    
    if df_aux.empty or not ordem_tarefas:
        fig = px.scatter(title="Nenhum dado disponível ainda.")
        return fig

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
            "Atrasado": "red",
            "Nao se aplica": "white"
        }
    )
    
    fig.update_xaxes(
        range=[-0.5, max_nos + 0.5],
        tickmode="array",
        side='top',
        tickfont=dict(size=15),
        tickvals=list(mapa_tarefas.values()),
        ticktext=list(mapa_tarefas.keys()),
        tickangle=90,
        showgrid=False,
        zeroline=False
    )
    
    for trace in fig.data:
        status = trace.name
        df_trace = df_aux[df_aux["Status"] == status]
        
        if "data_conclusao" in df_trace.columns:
            trace.customdata = df_trace[["nome", "tarefas", "Data_hover", "usuario_concluiu", "Data_conclusao_hover", "atraso"]].values
            trace.hovertemplate = (
                "<b>Subprograma:</b> %{customdata[0]}<br>"
                "<b>Tarefa:</b> %{customdata[1]}<br>"
                "<b>Data:</b> %{customdata[2]}<br>"
                "<b>Concluído por:</b> %{customdata[3]}<br>"
                "<b>Data conclusão:</b> %{customdata[4]}<br>"
                "<b>Dias de atraso:</b> %{customdata[5]}"
                "<extra></extra>"
            )
        else:
            trace.customdata = df_trace[["nome", "tarefas", "Data_hover"]].values
            trace.hovertemplate = (
                "<b>Subprograma:</b> %{customdata[0]}<br>"
                "<b>Tarefa:</b> %{customdata[1]}<br>"
                "<b>Data:</b> %{customdata[2]}"
                "<extra></extra>"
            )
    
    altura = min(max(400, num_linhas * 80 + 200), 1500)
    
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


def processar_tarefas(df, tabela_tarefas):
    
    colunas_tarefas = df.columns[2:]
    linhas = []
    
    for idx, row in df.iterrows():
        if pd.isna(row['subprograma']) or pd.isna(row['nome']):
            continue
        for tarefa in colunas_tarefas:
            data_termino = row[tarefa]
            linhas.append(
                dict(
                    Projeto=str(int(row['subprograma'])) + ' - ' + str(row['nome']),
                    Tarefa=tarefa,
                    ID=f"{row['nome']}|{tarefa}",
                    Data=data_termino
                )
            )
    
    try:
        df_aux = ler_sql(tabela_tarefas)
        if df_aux is None or df_aux.empty or "nome" not in df_aux.columns:
            raise ValueError("Arquivo de tarefas inválido ou vazio")
        df_aux["concluido"] = df_aux["concluido"].fillna(False).astype(bool)
        
        if "usuario_concluiu" not in df_aux.columns:
            df_aux["usuario_concluiu"] = None

        if "data_conclusao" not in df_aux.columns:
            df_aux["data_conclusao"] = None

        if "nao_aplica" not in df_aux.columns:
            df_aux["nao_aplica"] = False
        
        df_aux["nao_aplica"] = df_aux["nao_aplica"].fillna(False).astype(bool)
        df_aux = df_aux.drop_duplicates(subset=["nome", "tarefas"], keep="last")
    except (FileNotFoundError, pd.errors.EmptyDataError, ValueError):
        df_aux = pd.DataFrame(columns=["nome", "tarefas", "concluido", "usuario_concluiu", "data_conclusao"])
        df_aux["concluido"] = df_aux["concluido"].astype(bool)
        df_aux["usuario_concluiu"] = None
        df_aux["data_conclusao"] = None

    df_marcos = pd.DataFrame(linhas)

    if df_marcos.empty:
        return pd.DataFrame(columns=["nome", "tarefas", "Data", "concluido", "Status", "size"])

    df_marcos.rename(columns={"Projeto": "nome", "Tarefa": "tarefas"}, inplace=True)
    
    df_marcos = df_marcos.drop_duplicates(subset=["nome", "tarefas"])
    
    df_aux = df_marcos.merge(df_aux, on=["nome", "tarefas"], how="left")
    df_aux["concluido"] = df_aux["concluido"].fillna(False).astype(bool)

    if "usuario_concluiu" not in df_aux.columns:
        df_aux["usuario_concluiu"] = None
    
    if 'Data_y' in df_aux.columns:
        df_aux.drop(columns='Data_y', inplace=True)
    if 'Data_x' in df_aux.columns:
        df_aux.rename(columns={'Data_x': 'Data'}, inplace=True)
    if 'ID_y' in df_aux.columns:
        df_aux.drop(columns='ID_y', inplace=True)
    if 'ID_x' in df_aux.columns:
        df_aux.drop(columns='ID_x', inplace=True)

    if "data_conclusao" not in df_aux.columns:
        df_aux["data_conclusao"] = None

    df_aux = df_aux.drop_duplicates(subset=["nome", "tarefas"])

    df_aux["Status"] = "Pendente"

    df_aux.loc[df_aux["concluido"] == True, "Status"] = "Concluído"
    df_aux.loc[df_aux["nao_aplica"] == True, "Status"] = "Nao se aplica"
    df_aux['size'] = int(5)

    df_aux["data_conclusao"] = df_aux["data_conclusao"].where(df_aux["data_conclusao"].notna(), other=None)

    df_aux.loc[(df_aux["concluido"] == True) & (df_aux["usuario_concluiu"].isna()), "usuario_concluiu"] = "Sem informação"
    df_aux.loc[(df_aux["concluido"] == False) & (df_aux["usuario_concluiu"].notna()), "usuario_concluiu"] = "Sem informação"
    df_aux.loc[(df_aux["concluido"] == False) & (df_aux["usuario_concluiu"] == 'Sem informação'), "usuario_concluiu"] = None
    df_aux.loc[(df_aux["concluido"] == False) & ((df_aux["usuario_concluiu"] == 'Sem informação') | (df_aux["usuario_concluiu"].isna())), "data_conclusao"] = None
    df_aux["usuario_concluiu"] = df_aux["usuario_concluiu"].fillna("")
    df_aux["usuario_concluiu"] = df_aux["usuario_concluiu"].fillna("")
    
    hoje = pd.Timestamp(date.today())
    df_aux.loc[(df_aux["Status"] == "Pendente") & (df_aux["Data"] == hoje), "Status"] = "Finaliza hoje"
    df_aux.loc[(df_aux["Status"] == "Pendente") & (df_aux["Data"] < hoje), "Status"] = "Atrasado"

    return df_aux

def renderizar_editor_progresso(df, tab_key, column_configs):
    
    form_key = f"form_{tab_key}"
    
    with st.form(key=form_key):
        progresso = st.data_editor(
            df,
            num_rows="dynamic",
            column_config=column_configs,
            key=f'editor_{tab_key}'
        )
        
        nova_coluna = st.text_input("Adicionar nova coluna de tarefas")
        submitted = st.form_submit_button(":material/save: Salvar alterações")
    
    return progresso, nova_coluna, submitted


def renderizar_quadro_tarefas(df_aux, select_sub, tab_key, tabela_tarefas):

    with st.container(border=True):
        st.markdown(f"**{select_sub}**")

        tarefas_sub = df_aux[df_aux["nome"] == select_sub]

        for idx, row in tarefas_sub.iterrows():

            chave_checkbox = f"{tab_key}_{select_sub}_{idx}"
            chave_na = f"{tab_key}_{select_sub}_{idx}_na"

            if chave_checkbox not in st.session_state:
                st.session_state[chave_checkbox] = bool(row["concluido"])

            if chave_na not in st.session_state:
                valor_na = row.get("nao_aplica", False)

                if pd.isna(valor_na):
                    valor_na = False

                st.session_state[chave_na] = bool(valor_na)

            col1, col2, col3, col4 = st.columns([1,1,5,2])

            with col1:
                st.text(row["tarefas"])

            with col2:
                st.checkbox(
                    "Concluido",
                    # row["tarefas"],
                    key=chave_checkbox
                )

            with col3:
                st.checkbox(
                    "Não se aplica",
                    key=chave_na
                )

            nova_status = st.session_state[chave_checkbox]
            nao_aplica = bool(st.session_state[chave_na])
            status_anterior = bool(row["concluido"])

            if nao_aplica:
                nova_status = False

            if nova_status and not status_anterior:
                username = st.session_state.get("username", "Usuário desconhecido")
                hoje_str = date.today()

                df_aux.loc[
                    (df_aux["nome"] == select_sub) &
                    (df_aux["tarefas"] == row["tarefas"]),
                    "usuario_concluiu"
                ] = username

                df_aux.loc[
                    (df_aux["nome"] == select_sub) &
                    (df_aux["tarefas"] == row["tarefas"]),
                    "data_conclusao"
                ] = hoje_str

            elif nova_status:
                nao_aplica = False
                with col4:
                    usuario_salvo = row.get("usuario_concluiu", "")
                    if usuario_salvo:
                        st.caption(f"✓ {usuario_salvo}")

            df_aux.loc[
                (df_aux["nome"] == select_sub) &
                (df_aux["tarefas"] == row["tarefas"]),
                "concluido"
            ] = nova_status

            df_aux.loc[
                (df_aux["nome"] == select_sub) &
                (df_aux["tarefas"] == row["tarefas"]),
                "nao_aplica"
            ] = nao_aplica

    if st.button(":material/save: Salvar progresso das tarefas", key=f"salvar_tarefas_{tab_key}"):
        return True, df_aux

    return False, df_aux

# @st.cache_data(ttl=600)
def ler_sql(tabela):
    try:
        return pd.read_sql(f"SELECT * FROM {tabela}", engine)
    except:
        st.text("Erro, recarregue a página!") 

def salvar_tarefas(df_tarefas, tabela_tarefas, nome):
    colunas = ["nome", "tarefas", "concluido", "nao_aplica"]
    if "usuario_concluiu" in df_tarefas.columns:
        colunas.append("usuario_concluiu")

    if "data_conclusao" in df_tarefas.columns:
        colunas.append("data_conclusao")
    
    df_save = df_tarefas[colunas].drop_duplicates()
    df_save = df_save[df_save["nome"] == nome]

    with engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM [{tabela_tarefas}] WHERE nome = :nome"),
            {"nome": nome}
        )
        if not df_save.empty:
            df_save.to_sql(tabela_tarefas, conn, if_exists="append", index=False)

def remover_tarefas(prog, nome):
    tarefas = ler_sql(nome)
    temp = prog["subprograma"].astype(str) + " + " + prog["nome"]
    tarefas = tarefas[tarefas["nome"].isin(temp)]
    tarefas.to_sql("nome", engine, if_exists="replace", index=False)

def atualizar_banco(tabela_somativa, tabela_formativa, tabela_fluencia, tabela_correcao):
    df_somativa = ler_sql(tabela_somativa)
    df_formativa = ler_sql(tabela_formativa)
    df_fluencia = ler_sql(tabela_fluencia)
    df_correcao = ler_sql(tabela_correcao)

    for col in df_somativa.columns[2:]:
        df_somativa[col] = pd.to_datetime(df_somativa[col], errors='coerce')
    for col in df_formativa.columns[2:]:
        df_formativa[col] = pd.to_datetime(df_formativa[col], errors='coerce')

    def filtrar_novos(df, tabela):
        ids = pd.read_sql(f"SELECT subprograma FROM [{tabela}]", engine)["subprograma"].tolist()
        return df[~df["subprograma"].isin(ids)]

    df_formativa_novos = filtrar_novos(df_formativa, tabela_formativa)
    df_somativa_novos  = filtrar_novos(df_somativa,  tabela_somativa)
    df_fluencia_novos  = filtrar_novos(df_fluencia,  tabela_fluencia)
    df_correcao_novos  = filtrar_novos(df_correcao,  tabela_correcao)

    if not df_formativa_novos.empty:
        df_formativa_novos.to_sql(tabela_formativa, engine, if_exists="append", index=False)
    if not df_somativa_novos.empty:
        df_somativa_novos.to_sql(tabela_somativa, engine, if_exists="append", index=False)
    if not df_fluencia_novos.empty:
        df_fluencia_novos.to_sql(tabela_fluencia, engine, if_exists="append", index=False)
    if not df_correcao_novos.empty:
        df_correcao_novos.to_sql(tabela_correcao, engine, if_exists="append", index=False)

    colunas_progresso = pd.read_sql("SELECT TOP 0 * FROM [PROGRESSO]", engine).columns.tolist()
    
    df_geral = pd.concat([df_somativa, df_formativa], ignore_index=True)
    df_geral = df_geral.sort_values(by='subprograma')

    colunas_validas = [c for c in df_geral.columns if c in colunas_progresso]
    df_geral_insert = df_geral[colunas_validas]

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM [PROGRESSO]"))
        df_geral_insert.to_sql("PROGRESSO", conn, if_exists="append", index=False)


def report_progresso(tabela, tab_key, session_key, tabela_tarefas):
    
    st.session_state['active_tab'] = tab_key
    
    if session_key not in st.session_state:
        df = ler_sql(tabela)
        colunas_data = df.columns[2:]
        for col in colunas_data:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        st.session_state[session_key] = df
    else:
        if st.session_state[session_key].empty or st.session_state[session_key].dropna(subset=['nome']).empty:
            df = ler_sql(tabela)
            colunas_data = df.columns[2:]
            for col in colunas_data:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            st.session_state[session_key] = df
    
    df = st.session_state[session_key].copy()

    # ── GRÁFICO ANTES DO EDITOR ──────────────────────────────────────────────
    df_grafico = df.dropna(subset=['subprograma', 'nome'])

    if not df_grafico.empty:
        df_grafico["subprograma"] = df_grafico["subprograma"].astype(int)
        subs = (df_grafico["subprograma"].astype(str) + " - " + df_grafico["nome"]).unique()

        df_aux = processar_tarefas(st.session_state[session_key], tabela_tarefas)

        chave_tarefas = f"df_aux_{tab_key}"
        if chave_tarefas not in st.session_state:
            st.session_state[chave_tarefas] = df_aux.copy()
        else:
            concluido_salvo = st.session_state[chave_tarefas][["nome", "tarefas", "concluido"]].copy()
            df_aux = df_aux.drop(columns=["concluido"]).merge(concluido_salvo, on=["nome", "tarefas"], how="left")
            df_aux = df_aux.drop_duplicates(subset=["nome", "tarefas"])  # <-- adicionar esta linha
            df_aux["concluido"] = df_aux["concluido"].fillna(False).astype(bool)
            st.session_state[chave_tarefas] = df_aux.copy()

        df_aux_plot = st.session_state[chave_tarefas].copy()
        df_aux_plot["Status"] = df_aux_plot["concluido"].map({True: 'Concluído', False: 'Pendente'})
        df_aux_plot['size'] = int(5)

        hoje = pd.Timestamp(date.today())
        df_aux_plot.loc[(df_aux_plot["Status"] == "Pendente") & (df_aux_plot["Data"] == hoje), "Status"] = "Finaliza hoje"
        df_aux_plot.loc[(df_aux_plot["Status"] == "Pendente") & (df_aux_plot["Data"] < hoje), "Status"] = "Atrasado"
        df_aux_plot.loc[df_aux_plot["nao_aplica"] == True, "Status"] = "Nao se aplica"

        ordem_tarefas = df_aux_plot["tarefas"].dropna().unique().tolist()
        num_linhas = len(df_aux_plot["nome"].unique())
        fig = criar_grafico_progresso(df_aux_plot, ordem_tarefas, num_linhas)
        st.plotly_chart(fig, width='stretch', key=f'chart_{tab_key}')
    else:
        st.info("Nenhum dado cadastrado ainda. Adicione subprogramas na tabela abaixo e salve para visualizar o progresso.")

    st.subheader("Datas das tarefas correspondentes a cada subprograma")
    st.text('Adicione as datas de término de cada tarefa, também é possível adicionar novas linhas diretamente na tabela e colunas pelo formulário abaixo')

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
        
        df_final = df_final.loc[:, ~df_final.columns.str.match(r'^Unnamed|^$')]

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
        
        df_final = df_final.dropna(subset=['subprograma'])
        df_final["subprograma"] = df_final["subprograma"].astype(int)
        df_final = df_final.sort_values(by='subprograma')

        with engine.begin() as conn:
            conn.execute(text(f"DELETE FROM [{tabela}]"))
            df_final.to_sql(tabela, conn, if_exists="append", index=False)
        
        st.session_state.pop(session_key, None)
        st.session_state.pop(f"df_aux_{tab_key}", None)
        
        atualizar_banco('PROGRESSO_SOMATIVA', 'PROGRESSO_FORMATIVA', "PROGRESSO_FLUENCIA", "PROGRESSO_CORRECAO")
        st.rerun()


    if st.session_state[session_key].dropna(subset=['nome']).empty:
        return

    if not df_grafico.empty:
            st.subheader("Quadro de tarefas - marque as tarefas concluídas")
            select_sub = st.selectbox("Escolha um subprograma", options=subs, key=f'select_sub_{tab_key}')
            
            if st.button(":material/check_circle: Marcar todas como concluídas", key=f"marcar_todos_{tab_key}"):
                hoje_str = date.today()
                username = st.session_state.get("username", "Usuário desconhecido")
                mask_nao_concluidas = (                           
                    (st.session_state[chave_tarefas]["nome"] == select_sub) &
                    (st.session_state[chave_tarefas]["concluido"] == False)
                )
                st.session_state[chave_tarefas].loc[
                    st.session_state[chave_tarefas]["nome"] == select_sub, "concluido"
                ] = True
                st.session_state[chave_tarefas].loc[mask_nao_concluidas, "usuario_concluiu"] = username   
                st.session_state[chave_tarefas].loc[mask_nao_concluidas, "data_conclusao"] = hoje_str     
                salvar_tarefas(st.session_state[chave_tarefas], tabela_tarefas, select_sub)
                tarefas_sub = st.session_state[chave_tarefas][st.session_state[chave_tarefas]["nome"] == select_sub]
                for idx in tarefas_sub.index:
                    st.session_state[f"{tab_key}_{select_sub}_{idx}"] = True
                st.rerun()

            enviado, df_aux_modificado = renderizar_quadro_tarefas(
                st.session_state[chave_tarefas].copy(), select_sub, tab_key, tabela_tarefas
            )

            if enviado:  
                salvar_tarefas(df_aux_modificado, tabela_tarefas, select_sub)
                st.session_state[chave_tarefas] = df_aux_modificado.copy()
                st.success("Progresso das tarefas salvo!")
                st.rerun()

def report_tab5():
    report_progresso(
        tabela='PROGRESSO_SOMATIVA',
        tab_key='tab5',
        session_key='df_tab5',
        tabela_tarefas='TAREFAS_SOMATIVA'
    )


def report_tab6():
    report_progresso(
        tabela='PROGRESSO_FORMATIVA',
        tab_key='tab6',
        session_key='df_tab6',
        tabela_tarefas='TAREFAS_FORMATIVA'
    )

def report_tab7():
    report_progresso(
        tabela='PROGRESSO_FLUENCIA',
        tab_key='tab7',
        session_key='df_tab7',
        tabela_tarefas='TAREFAS_FLUENCIA'
    )

def report_tab8():
    report_progresso(
        tabela='PROGRESSO_CORRECAO',
        tab_key='tab8',
        session_key='df_tab8',
        tabela_tarefas='TAREFAS_CORRECAO'
    )

def report_tab9():
        report_progresso(
        tabela='PROGRESSO_RECURSO',
        tab_key='tab9',
        session_key='df_tab9',
        tabela_tarefas='TAREFAS_RECURSO'
    )

def dashboard():
    
    st.title("Dashboards")
    css = '''
    <style>
        button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
            font-size: 15px; 
        }
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Processamento / Instrumento", "Verificação", "Datas digitalização", "Progresso Somativas", "Progresso Formativas", "Progresso Fluência", "Progresso Correção", "Progresso Recurso"])

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
        st.header("Gráfico de progresso")
        st.text("Acompanhe o progresso das tarefas referentes a cada subprograma")
        report_tab5()


    with tab5:
        st.header("Gráfico de progresso")
        st.text("Acompanhe o progresso das tarefas referentes a cada subprograma")
        report_tab6()

    
    with tab6:
        st.header("Gráfico de progresso")
        st.text("Acompanhe o progresso das tarefas referentes a cada subprograma")
        report_tab7()


    with tab7:
        st.header("Gráfico de progresso")
        st.text("Acompanhe o progresso das tarefas referentes a cada subprograma")
        report_tab8()


    with tab8:      
        st.header("Gráfico de progresso")
        st.text("Acompanhe o progresso das tarefas referentes a cada subprograma")
        report_tab9()  

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
