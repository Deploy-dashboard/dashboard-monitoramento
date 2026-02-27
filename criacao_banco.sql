USE TD_DASHBOARD_CPD

CREATE TABLE PROGRESSO_SOMATIVAS (
	subprograma INT PRIMARY KEY,
	nome VARCHAR(255),
	dv_banco DATE,
	dv_producao DATE,
	frop1 DATE,
	frop1_ret DATE,
	frop2 DATE,
	frop3 DATE,
	recuperacao DATE,
	recuperacao_t2 DATE,
	recuperacao_ex DATE,
	recuperacao_ex_ret DATE,
	nm_aluno DATE,
	categorizacao_tn DATE,
	rel_categroizacao DATE,
	certif_obj DATE,
	certif_ctx DATE,
	certif_nap DATE,
	medida_obj DATE,
	medida_ctx DATE,
	rel_tratamento DATE,
	rel_verificacao DATE
);

CREATE TABLE PROGRESSO_FORMATIVA(
	subprograma INT PRIMARY KEY,
	nome VARCHAR(255),
	dv_banco DATE,
	dv_producao DATE,
	categorizacao_tn DATE,
	rel_categroizacao DATE,
	certif_sinc DATE,
	nm_aluno DATE,
	certif_obj DATE,
	certif_ctx DATE,
	certif_esc DATE,
	certif_co DATE,
	co_rel_pgto DATE,
	medida_obj DATE,
	medida_ctx DATE,
	medida_esc DATE,
	pareamento DATE,
	rel_verificacao DATE
);

CREATE TABLE PROGRESSO_FLUENCIA( 
    subprograma INT PRIMARY KEY,
    nome VARCHAR(255),
    conf_hmg DATE,
	conf_pro_t1 DATE,
    certif_sinc DATE,
    nm_aluno DATE,
    certif_co DATE,
    co_rel_pgto DATE
);

CREATE TABLE PROGRESSO_CORRECAO(
    subprograma INT PRIMARY KEY,
    nome VARCHAR(255),
    imagem DATE,
    conf_hmg DATE,
    conf_pro_t1 DATE,
    recuperacao DATE,
    recuperacao_t2 DATE,
    recuperacao_ex DATE,
    recuperacao_ex_ret DATE,
    certif_esc DATE,
    certif_co DATE,
    co_rel_pgto DATE,
    medida_esc DATE,
    pareamento DATE
);

CREATE TABLE TAREFAS_SOMATIVA(
    id INT IDENTITY(1,1) PRIMARY KEY,
    nome VARCHAR(255),
    tarefas VARCHAR(255),
    concluido BIT
);

CREATE TABLE TAREFAS_FORMATIVA(
    id INT IDENTITY(1,1) PRIMARY KEY,
    nome VARCHAR(255),
    tarefas VARCHAR(255),
    concluido BIT
);

CREATE TABLE TAREFAS_FLUENCIA(
    id INT IDENTITY(1,1) PRIMARY KEY,
    nome VARCHAR(255),
    tarefas VARCHAR(255),
    concluido BIT
);

CREATE TABLE TAREFAS_CORRECAO(
    id INT IDENTITY(1,1) PRIMARY KEY,
    nome VARCHAR(255),
    tarefas VARCHAR(255),
    concluido BIT
);

CREATE TABLE DATAS(
    subprograma INT PRIMARY KEY,
    nome VARCHAR(255),
    previstos INT,
    digitalizados INT,
    inicio DATE,
    fim DATE,
    diferenca INT,
    media_dia FLOAT,
    esperado_hoje FLOAT,
    porcent_digitalizados FLOAT,
    cor VARCHAR(255)
);

CREATE TABLE TAREFAS(
	id INT IDENTITY (1,1) PRIMARY KEY, 
	nome VARCHAR(255),
	tarefas VARCHAR(255),
	concluido BIT
);

CREATE TABLE PROGRESSO(
	subprograma INT PRIMARY KEY,
	nome VARCHAR(255),
	dv_banco DATE,
	dv_producao DATE,
	frop1 DATE,
	frop1_ret DATE,
	frop2 DATE,
	frop3 DATE,
	recuperacao DATE,
	recuperacao_t2 DATE,
	recuperacao_ex DATE,
	recuperacao_ex_ret DATE,
	nm_aluno DATE,
	categorizacao_tn DATE,
	rel_categroizacao DATE,
	certif_obj DATE,
	certif_ctx DATE,
	certif_nap DATE,
	medida_obj DATE,
	medida_ctx DATE,
	rel_tratamento DATE,
	rel_verificacao DATE
);

