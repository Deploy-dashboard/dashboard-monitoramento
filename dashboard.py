from io import BytesIO
from client import Client
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False


def login_page():
    st.markdown(
    """
    <div style="
        margin: 0 auto;
        margin-top: 70px;
        width: 380px;
        padding: 30px;
        border-radius: 12px;   
        text-align: center;
    ">
    """,
    unsafe_allow_html=True
    )
    st.markdown("### Repositório CPD")
    client = Client()
    st.set_page_config(page_title="Login", layout="centered", page_icon="images\\icon.png")
    st.markdown("Entre com o nome de usuário e senha:")

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if client.login(username, password):
            st.session_state['logged_in'] = True
            st.rerun()  
            
        st.error("Usuário ou senha incorretos.")

programas = {"null" : ["null"],
            234 : [2026, 2087, "null"],
            220 : [2050, "null"],
            130 : [2070, "null"],
            149 : [2075, "null"],
            194 : [2077, "null"],
            208 : [2082, "null"],
            197 : [2085, "null"],
            234 : [2026, 2087, "null"],
            129 : [2132, "null"]
            }

subprogramas = ["Todos", 
                "2026 - MG BELO HORIZONTE - 3ª AV. SOMATIVA 2025 (SIMULADO)", 
                "2050 - BR CAEd - PPGP 2025", 
                "2070 - GO GOIÁS - AV. SOMATIVA EF EM 2025 (SAEGO)", 
                "2075 - CE CEARÁ - AV. SOMATIVA EM 2025 (SPAECE EM)", 
                "2082 - TO TOCANTINS - 1ª AV. SOMATIVA 2025 (SIMULADO)", 
                "2085 - MT MATO GROSSO - AV. SOMATIVA 2025 EF EM (AVALIA MT)", 
                "2087 - MG BELO HORIZONTE - 5ª AV. FORMATIVA 2025 (NOVEMBRO)", 
                "2091 - PE RECIFE - 3ª AV. FORMATIVA 2025",
                "2101 - SC FLORIANÓPOLIS - 2ª AV. SOMATIVA 2025", 
                "2132 - PI PIAUÍ - AV. SOMATIVA 2025 EF EM (SAEPI)",
                "2104 - BR CAEd - PRÉ-TESTE 2025 - LOTE 04 (BANCO)"
                ]

def num_sp(sp):
    if sp != "Todos":
        num = sp[0:4]
        num = int(num)
        return num
    return "null"

def atualiza_id(id):

    if id == "null":
        return "null"
    if id == 234:
        return 250
    elif id == 220:
        return 232
    elif id == 130:
        return 124
    elif id == 149:
        return 143
    elif id == 208:
        return 212
    elif id == 197:
        return 201
    elif id == 234:
        return 250
    return 123


def report_tab1():
    
    select_sp = st.selectbox("Suprograma",options=subprogramas, key="sp_tab1")
    sp = num_sp(select_sp)
    url = f'http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7027-1707:2025/9/ID_FONTE_DADO="null"&CD_PROGRAMA={sp}'
    response = requests.get(url)
    response.raise_for_status()

    excel = BytesIO(response.content)
    df = pd.DataFrame(pd.read_excel(excel))
    st.markdown("**Tabela:**")
    st.dataframe(df, hide_index=True)
    
    if sp == "null":
        labels = df["Cód. subprograma"].astype(str)  
        decodificados = df["% de registros processados"]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=labels,
            y=decodificados,
            name="Decodificados",
            marker_color='#4169E1',
            offsetgroup=0
        ))


        fig.update_layout(
            title="Comparativo de registros processados: ",
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
    instrumentos.append("Todos")

    select_sp = st.selectbox("Suprograma",options=subprogramas, key="sp_tab2")
    sp = num_sp(select_sp)
    
    inst = st.selectbox("Instrumento", options=instrumentos)
    if inst == "Todos":
        inst = "null"
    url_instrumento = f'http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7028-1707:2025/9/ID_FONTE_DADO={"null"}&CD_PROGRAMA={sp}&DC_INSTRUMENTO_TIPO={inst}'
    
    response1 = requests.get(url_instrumento)
    ex = BytesIO(response1.content)
    table = pd.DataFrame(pd.read_excel(ex))
    table = table.drop_duplicates(subset=['Cód. subprograma', 'Instrumento'])
    table["Total de registros digitalizados"] = pd.to_numeric(table["Total de registros digitalizados"], errors="coerce")
    table["Total de registros previstos"] = pd.to_numeric(table["Total de registros previstos"], errors="coerce")
    table["% de registros digitalizados"] = ((table["Total de registros digitalizados"] / table["Total de registros previstos"]) * 100).round(2)

    st.markdown("**Tabela:**")
    st.dataframe(table, hide_index=True)

    if (inst != "null") and (sp == "null"):
        labels = table["Cód. subprograma"].astype(str)
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
        labels = table["Instrumento"].astype(str)
        processados = table["% de registros processados"]
        digitalizados = table["% de registros digitalizados"]
        
        barras = go.Figure()

        barras.add_trace(go.Bar(
            x=labels,
            y=processados,
            name="processados",
            marker_color='#4169E1',
            offsetgroup=0
        ))

        barras.add_trace(go.Bar(
            x=labels,
            y=digitalizados,
            name="Certificados",
            marker_color='lightblue',
            offsetgroup=1
        ))

        barras.update_layout(
            title=f"Comparativo de Instrumentos no programa {sp}: ",
            xaxis_title="Instrumento",
            yaxis_title="Registros processados (%)",
            barmode='group',
            xaxis_tickangle=-15,
            bargap=0.15,      
            bargroupgap=0.05, 
            template="plotly_white",
        )

        st.plotly_chart(barras)
        
    

    pizza = go.Figure(data=[go.Pie(labels=df["Instrumento"], values=df["Total de registros previstos"])])


    pizza.update_traces(textposition='inside', textinfo='percent+label')
    pizza.update_layout(title="Distribuição de instrumentos:", showlegend=True)

    st.plotly_chart(pizza, width="stretch") 


def report_tab3():
    
    sol = f"http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7029-2307:2025/9/ID_FONTE_DADO=null&CD_PROGRAMA=null&DC_SOLICITACAO=null"
    response = requests.get(sol)
    content = BytesIO(response.content)
    df = pd.DataFrame(pd.read_excel(content))
    resume = df.loc[df["Verificação"] == ("Subtotal")]
    st.markdown("**Verificações finalizadas por programa:**")
    st.dataframe(resume, hide_index=True)

    labels = resume["Cód. subprograma"].astype(str)  
    verificacoes = resume[f"% de verificações finalizadas"].astype(float)
    alteracao = resume[f"% de alteração das verificações finalizadas"].astype(float)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels,
        y=verificacoes,
        name="Total de verificações",
        marker_color='#4169E1',
        offsetgroup=0,
    ))

    fig.add_trace(go.Bar(
        x=labels,
        y=alteracao,
        name="Finalizadas",
        marker_color='lightblue',
        offsetgroup=1,
    ))

    fig.update_layout(
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
    verif = df["Verificação"].unique().tolist()
    entrada_prog = st.selectbox("Programa", options=list(programas.keys()), key="prog_tab3")
    prog = atualiza_id(entrada_prog)

    subprogramas = programas[entrada_prog]
    sp = st.selectbox("Suprograma",options=subprogramas, key="sp_tab3")

    solicitacao = str(st.selectbox("Solicitacao", options=verif))
    if solicitacao == "nan":
        solicitacao = "null"
    solicitacao = solicitacao.replace(" ", "%20")

    url = f"http://10.0.10.22:41112/gw/reports/generate_report_xls/CAED7029-2307:2025/9/ID_FONTE_DADO={prog}&CD_PROGRAMA={sp}&DC_SOLICITACAO={solicitacao}"

    resp = requests.get(url)
    excel = BytesIO(resp.content)
    table = pd.DataFrame(pd.read_excel(excel))
    st.markdown("**Tabela:**")
    st.dataframe(table, hide_index=True)

    

def dashboard():
    
    st.title("Dashboards")
    st.set_page_config(page_title="Dashboard", layout="wide", page_icon="images\icon.png")
    
    tab1, tab2 = st.tabs(["processamento / instrumento", "verificação"])

    with tab1:
        st.header("Relatórios de processamento:")
        report_tab1()

        st.header("Relatório Processamento por instrumento:")
        report_tab2()


    with tab2:
        st.header("Relatório Verificação - Subprograma / Solicitação ")
        report_tab3()




# if __name__ == "__main__":

#     if st.session_state['logged_in']:
#         dashboard()
#     else:
#         login_page()

dashboard()