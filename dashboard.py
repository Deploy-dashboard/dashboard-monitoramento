from io import BytesIO
from client import Client
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import date

st.set_page_config(page_title="Dashboard", layout="wide", page_icon="images\\icon.png")

def login_page():
  
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("## Repositório CPD")
        st.markdown("Entre com o nome de usuário e senha:")

        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar", use_container_width=True):
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
            
###################################################

        # datas = pd.DataFrame(pd.read_csv("datas.csv"))
        # labels1 = datas["subprograma"]
        # processados1 = df["% de registros processados"]
        # colors = [get_color(v) for v in processados1]

        # fig = go.Figure()

        # fig.add_trace(go.Bar(
        #     x=processados1,   
        #     y=labels1,        
        #     name="Processados",
        #     marker_color=colors,
        #     orientation='h',  
        #     offsetgroup=1
        # ))

        # fig.update_layout(
        #     height=800,
        #     title="Registros processados por subprograma:",
        #     xaxis_title="Registros processados (%)",   
        #     yaxis_title="Subprograma",
        #     barmode='group',
        #     xaxis_tickangle=0,
        #     bargap=0.15,
        #     bargroupgap=0.05,
        #     template="plotly_white",
        #     legend=dict(
        #         title='',
        #         orientation='h',
        #         yanchor='bottom',
        #         y=1.05,
        #         xanchor='right',
        #         x=1,
        #     )
        # )

        # st.plotly_chart(fig, width="stretch")

###################################################
        
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
    
    url_padrao = 'http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7028-1707:2025/9/ID_FONTE_DADO=null&CD_PROGRAMA=null&DC_INSTRUMENTO_TIPO=null'
    response = requests.get(url_padrao)
    response.raise_for_status()

    excel = BytesIO(response.content)
    df = pd.DataFrame(pd.read_excel(excel))
    
    instrumentos = df['Instrumento'].unique().tolist()
    instrumentos = sorted(instrumentos)
    instrumentos.insert(0, "Todos")

    select_sp = st.selectbox("Subprograma",options=lista_sp, key="sp_tab2")
    sp = num_sp(select_sp)
    
    inst = st.selectbox("Instrumento", options=instrumentos)
    if inst == "Todos":
        inst = "null"
    url_instrumento = f'http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7028-1707:2025/9/ID_FONTE_DADO={"null"}&CD_PROGRAMA={sp}&DC_INSTRUMENTO_TIPO={inst}'
    
    response1 = requests.get(url_instrumento)
    ex = BytesIO(response1.content)
    table = pd.DataFrame(pd.read_excel(ex))
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

    def sol(prog, subprog, solicit):
        s = f"http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7029-2307:2025/9/ID_FONTE_DADO={prog}&CD_PROGRAMA={subprog}&DC_SOLICITACAO={solicit}"
        response = requests.get(s)
        content = BytesIO(response.content)
        df = pd.DataFrame(pd.read_excel(content))
        return df
    
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

    st.button("Limpar filtro", on_click=limpar)

    if solicitacao == "Todos":
        solicitacao = "null"


    solicitacao = solicitacao.replace(" ", "%20")
    
    url = f"http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7029-2307:2025/9/ID_FONTE_DADO={prog}&CD_PROGRAMA={subprog}&DC_SOLICITACAO={solicitacao}"

    resp = requests.get(url)
    excel = BytesIO(resp.content)
    table = pd.DataFrame(pd.read_excel(excel))
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
   
    col1, col2, col3 = st.columns([1.5, 1, 1])

    with col1:
        
        with st.form(key="tab4"):
            st.markdown("**Adicione as datas referentes ao início e término dos subprogramas:**")
            lista_sp.pop(0)
            select_sp = st.selectbox("Subprograma", options=lista_sp, key="sp_tab4")
            sp = num_sp(select_sp)
            inicio = st.date_input("Data de início", format="DD/MM/YYYY")
            fim = st.date_input("Data de término", format="DD/MM/YYYY")
            submitted = st.form_submit_button("Adicionar / Atualizar datas")

        arquivo = "datas.csv"
        datas = pd.read_csv(arquivo)

        datas["inicio"] = pd.to_datetime(datas["inicio"], errors="coerce")
        datas["fim"] = pd.to_datetime(datas["fim"], errors="coerce")

        url = f'http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7027-1707:2025/9/ID_FONTE_DADO="null"&CD_PROGRAMA={sp}'
        response = requests.get(url)
        response.raise_for_status()

        df = pd.read_excel(BytesIO(response.content))
        total_previsto = df.loc[df["Cód. subprograma"] == sp, "Total de registros previstos"].sum()

        mapa_sub = { s.split(" - ")[0]: " - ".join(s.split(" - ")[1:]) for s in lista_sp if s != "Todos"}

        if "nome" not in datas.columns:
            datas.insert(1, "nome", datas["subprograma"].astype(str).map(mapa_sub))

        previstos = df.loc[df["Cód. subprograma"] == sp, "Total de registros previstos"].iloc[0]
        datas.loc[datas["subprograma"] == sp,"previstos"] = previstos

        digitalizados = df.loc[df["Cód. subprograma"] == sp, "Total de registros digitalizados"].iloc[0]
        datas.loc[datas["subprograma"] == sp,"digitalizados"] = digitalizados

        df.insert(loc=3, column="% de registros digitalizados", value=((pd.to_numeric(df["Total de registros digitalizados"]) / pd.to_numeric(df["Total de registros previstos"]))*100).round(2))
        digitalizados_p = df.loc[df["Cód. subprograma"] == sp, "% de registros digitalizados"].iloc[0]
        datas.loc[datas["subprograma"] == sp,"% digitalizados"] = digitalizados_p

        if submitted:

            if sp not in datas["subprograma"].values:
                nova_linha = {
                    "subprograma": sp,
                    "nome": mapa_sub.get(str(sp)),
                    "inicio": pd.NaT,
                    "fim": pd.NaT,
                    "diferenca": None,
                    "media dia": None,
                    "esperado hoje": None,
                    "previstos": None,
                    "digitalizados": None,
                    "% digitalizados": None
                }
                datas = pd.concat([datas, pd.DataFrame([nova_linha])], ignore_index=True)

            mask = datas["subprograma"] == sp  

            hoje = pd.Timestamp(date.today())
            inicio = pd.to_datetime(inicio)
            fim = pd.to_datetime(fim)

            datas.loc[mask, "inicio"] = inicio
            datas.loc[mask, "fim"] = fim

            diferenca = (datas.loc[mask, "fim"] - datas.loc[mask, "inicio"]).dt.days.clip(lower=1)
            datas.loc[mask, "diferenca"] = diferenca

            media_dia = (total_previsto / diferenca).round(0)
            datas.loc[mask, "media dia"] = media_dia

            dias_passados = (hoje - datas.loc[mask, "inicio"]).dt.days.clip(lower=0)

            esperado_hoje = media_dia * dias_passados
            datas.loc[mask, "esperado hoje"] = esperado_hoje.clip(lower=0, upper=datas.loc[mask, "previstos"])
            datas["esperado hoje"] = datas["esperado hoje"].round(0)
                      
            datas = datas[datas["subprograma"].isin(lista_num_sp)]
            datas.to_csv(arquivo, index=False)

            st.success("Datas adicionadas!")
    
    datas = datas.sort_values(by="subprograma")
    st.dataframe(datas, hide_index=True, column_config={
        "previstos": st.column_config.NumberColumn(format="localized"),
        "inicio": st.column_config.DateColumn(format="DD/MM/YYYY"),
        "fim": st.column_config.DateColumn(format="DD/MM/YYYY"),
        "diferenca": None,
        "media dia": None,
        "digitalizados": st.column_config.NumberColumn(format="localized"),
        "esperado hoje": st.column_config.NumberColumn(format="localized"),
        "% digitalizados":None
    })

    labels = datas["subprograma"].astype(str)+" - "+datas["nome"]  
    digitalizados = datas["% digitalizados"]
    datas['cor'] = datas.apply(lambda row: 'green' if ((row['digitalizados'] > row['esperado hoje']) or (row['digitalizados'] == row['esperado hoje']) or (row['digitalizados'] > (row['esperado hoje'] * 0.9))) else 'red', axis=1)
    colors = datas["cor"]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=digitalizados,   
        y=labels,        
        name="Digitalizados",
        marker_color=colors,
        orientation='h',  
        offsetgroup=1
    ))

    fig.update_layout(
        height=800,
        title="Verificação de registros digitalizados por subprograma:",
        xaxis_title="Registros digitalizados (%)",   
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


def dashboard():
    
    st.title("Dashboards")
    
    tab1, tab2, tab3 = st.tabs(["Processamento / Instrumento", "Verificação", "Datas digitalização"])

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
        report_tab4()

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
