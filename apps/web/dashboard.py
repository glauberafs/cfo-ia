"""CFO IA - UI temporaria (Streamlit como cliente da API).

Isto NAO e a UI final do produto (vira frontend web de verdade depois).
Serve para validar a API multiusuario enquanto o frontend nao existe.
"""
import os
from datetime import date

import pandas as pd
import requests
import streamlit as st


def _api_url() -> str:
    """No Streamlit Community Cloud, a URL da API fica em st.secrets (Settings -> Secrets);
    localmente, na variavel de ambiente API_URL (ver .env.example)."""
    try:
        return st.secrets["API_URL"]
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return os.environ.get("API_URL", "http://localhost:8000")


API_URL = _api_url()

CATEGORIAS = [
    "nao_classificado", "neutro", "pagamento_cartao",
    "mercado", "restaurante", "delivery", "padaria_cafe",
    "combustivel", "transporte_app", "transporte_publico",
    "estacionamento_pedagio", "manutencao_veiculo", "seguro_veiculo",
    "aluguel_financiamento", "condominio", "energia", "agua", "gas",
    "internet_telefone", "manutencao_casa",
    "plano_saude", "farmacia", "consultas_exames", "academia",
    "mensalidade", "cursos", "livros_materiais",
    "streaming", "assinaturas", "viagens", "bares_eventos", "hobbies",
    "vestuario", "eletronicos", "casa", "presentes",
    "tarifas_bancarias", "juros", "impostos_taxas",
    "salario", "renda_extra", "rendimentos", "reembolsos", "outras_receitas",
    "saque", "outros",
]

st.set_page_config(page_title="CFO IA", layout="wide")
st.title("CFO IA")
st.caption("Sistema inteligente de gestao financeira pessoal")


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state['token']}"}


def tela_login():
    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])

    with aba_login:
        email = st.text_input("Email", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")
        if st.button("Entrar"):
            r = requests.post(f"{API_URL}/auth/login", json={"email": email, "senha": senha})
            if r.status_code == 200:
                st.session_state["token"] = r.json()["access_token"]
                st.rerun()
            else:
                st.error(r.json().get("detail", "Falha no login"))

    with aba_cadastro:
        nome = st.text_input("Nome", key="cad_nome")
        email2 = st.text_input("Email", key="cad_email")
        senha2 = st.text_input("Senha", type="password", key="cad_senha")
        apelidos = st.text_input(
            "Nomes/apelidos que sao SEUS (separados por virgula) -- usado para "
            "identificar transferencia entre suas proprias contas em outros bancos",
            key="cad_apelidos",
        )
        if st.button("Criar conta"):
            lista_apelidos = [a.strip() for a in apelidos.split(",") if a.strip()]
            r = requests.post(f"{API_URL}/auth/register", json={
                "nome": nome, "email": email2, "senha": senha2, "apelidos_proprios": lista_apelidos,
            })
            if r.status_code == 201:
                st.success("Conta criada. Faca login na aba ao lado.")
            else:
                st.error(r.json().get("detail", "Falha no cadastro"))


if "token" not in st.session_state:
    tela_login()
    st.stop()

with st.sidebar:
    if st.button("Sair"):
        del st.session_state["token"]
        st.rerun()
    st.divider()

    with st.expander("Conectar banco (Pluggy)"):
        conex = requests.get(f"{API_URL}/contas/conexoes", headers=auth_headers())
        conex_lista = conex.json() if conex.status_code == 200 else []
        if conex_lista:
            st.caption("Conexoes ja registradas:")
            for c in conex_lista:
                st.write(f"- {c.get('instituicao') or 'banco'} (`{c['item_id'][:8]}...`)")
        else:
            st.caption("Nenhum banco conectado ainda.")
        novo_item = st.text_input("item_id da conexao (gerado no MeuPluggy)", key="novo_item_id")
        nova_inst = st.text_input("Instituicao (ex: Santander)", key="nova_instituicao")
        if st.button("Conectar banco"):
            if not novo_item.strip():
                st.error("Informe o item_id.")
            else:
                rc = requests.post(
                    f"{API_URL}/contas/conexoes",
                    headers=auth_headers(),
                    json={"item_id": novo_item.strip(), "instituicao": nova_inst.strip()},
                )
                if rc.status_code == 201:
                    st.success("Banco conectado. Agora clique 'Sincronizar (Pluggy real)'.")
                    st.rerun()
                else:
                    st.error(rc.json().get("detail", rc.text))

    if st.button("Rodar sync demo (sem credenciais)"):
        r = requests.post(f"{API_URL}/sync/demo", headers=auth_headers())
        if r.status_code == 200:
            st.success(f"{r.json()['novos_eventos']} novo(s) evento(s).")
        else:
            st.error(r.text)
    if st.button("Sincronizar (Pluggy real)"):
        r = requests.post(f"{API_URL}/sync", headers=auth_headers())
        if r.status_code == 200:
            st.success(f"{r.json()['novos_eventos']} novo(s) evento(s).")
        else:
            st.error(r.json().get("detail", r.text))
    if st.button("Reaplicar memoria a tudo"):
        r = requests.post(f"{API_URL}/sync/reaplicar-memoria", headers=auth_headers())
        if r.status_code == 200:
            st.success(f"{r.json()['eventos_atualizados']} evento(s) atualizado(s).")

r = requests.get(f"{API_URL}/eventos", headers=auth_headers())
if r.status_code == 401:
    del st.session_state["token"]
    st.rerun()
eventos = r.json()
df = pd.DataFrame(eventos)

if df.empty:
    st.warning("Nenhum evento ainda. Use 'Rodar sync demo' na barra lateral.")
    st.stop()

contas_lista = requests.get(f"{API_URL}/contas", headers=auth_headers()).json()
NOME_CONTA = {
    c["id"]: f"{c['nome']} ({'Cartao' if c['tipo'] == 'CARTAO' else 'Conta'})" for c in contas_lista
}
df["conta_nome"] = df["conta_id"].map(NOME_CONTA).fillna("(conta removida)")

NOME_MES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def _rotulo_periodo(ano: int, mes: int | None) -> str:
    return f"{NOME_MES[mes]}/{ano}" if mes else f"Ano {ano} (completo)"


# -- Filtro global de periodo (afeta DRE, gasto por categoria, orcamento e alertas de tendencia) --
st.subheader("Filtro de periodo")
st.caption("Define o periodo analisado no DRE, no gasto por categoria e no comparativo de orcamento abaixo.")
anos_disponiveis = sorted({int(d[:4]) for d in df["data"]}, reverse=True)
hoje = pd.Timestamp.today()
ano_default = hoje.year if hoje.year in anos_disponiveis else anos_disponiveis[0]

fc1, fc2 = st.columns([1, 1])
ano_sel = fc1.selectbox("Ano", options=anos_disponiveis, index=anos_disponiveis.index(ano_default), key="filtro_ano")
mes_sel = fc2.selectbox(
    "Mes", options=[None] + list(range(1, 13)),
    format_func=lambda m: "Ano inteiro" if m is None else NOME_MES[m],
    index=(hoje.month if ano_sel == hoje.year else 0),
    key="filtro_mes",
)
periodo_params = {"ano": int(ano_sel)}
if mes_sel:
    periodo_params["mes"] = int(mes_sel)
rotulo_periodo_atual = _rotulo_periodo(int(ano_sel), int(mes_sel) if mes_sel else None)
st.info(f"Periodo selecionado: **{rotulo_periodo_atual}**")

# -- Score financeiro --
score = requests.get(f"{API_URL}/score", headers=auth_headers()).json()
sc1, sc2 = st.columns([1, 3])
sc1.metric("Score financeiro", f"{score['score']} / {score['score_max']}", delta=score["classificacao"])
with sc2:
    st.caption("Composicao do score (poupanca 400, orcamento 300, saldo futuro 200, patrimonio 100)")
    comp_score = pd.DataFrame([
        {"componente": nome, "pontos": dados["pontos"], "pontos_max": dados["pontos_max"]}
        for nome, dados in score["componentes"].items()
    ]).set_index("componente")
    st.bar_chart(comp_score["pontos"])

# -- Alertas (tendencia de orcamento e saldo projetado negativo) + anomalias --
alertas = requests.get(f"{API_URL}/alertas", headers=auth_headers()).json()
anomalias = requests.get(f"{API_URL}/anomalias", headers=auth_headers()).json()
if alertas or anomalias:
    st.subheader("Alertas")
    for a in alertas:
        st.warning(a["mensagem"])
    for an in anomalias:
        st.error(an["mensagem"])

# -- DRE do periodo selecionado, com comparativos --
dre = requests.get(f"{API_URL}/dre", params=periodo_params, headers=auth_headers()).json()
resumo = requests.get(f"{API_URL}/dashboard/resumo", headers=auth_headers()).json()


def _delta(atual, anterior):
    if anterior in (None, 0):
        return None
    return f"{atual - anterior:,.2f} vs comparativo"


if mes_sel:
    mes_ant, ano_ant = (12, int(ano_sel) - 1) if int(mes_sel) == 1 else (int(mes_sel) - 1, int(ano_sel))
    rotulo_periodo_anterior = _rotulo_periodo(ano_ant, mes_ant)
    rotulo_mesmo_periodo_ano_anterior = _rotulo_periodo(int(ano_sel) - 1, int(mes_sel))
else:
    rotulo_periodo_anterior = None
    rotulo_mesmo_periodo_ano_anterior = _rotulo_periodo(int(ano_sel) - 1, None)

st.subheader(f"DRE -- {rotulo_periodo_atual}")
d1, d2, d3, d4 = st.columns(4)
d1.metric("Receitas", f"R$ {dre['atual']['receitas']:,.2f}")
d2.metric("Despesas", f"R$ {dre['atual']['despesas']:,.2f}")
d3.metric("Resultado", f"R$ {dre['atual']['resultado']:,.2f}")
d4.metric("Obrigacoes futuras (todas)", f"R$ {resumo['obrigacoes_futuras']:,.2f}")

comp_cols = st.columns(2 if dre["periodo_anterior"] is None else 3)
idx = 0
if dre["periodo_anterior"] is not None:
    with comp_cols[idx]:
        st.caption(f"Vs. {rotulo_periodo_anterior}")
        st.metric("Resultado", f"R$ {dre['periodo_anterior']['resultado']:,.2f}",
                   delta=_delta(dre["atual"]["resultado"], dre["periodo_anterior"]["resultado"]))
    idx += 1
with comp_cols[idx]:
    st.caption(f"Vs. {rotulo_mesmo_periodo_ano_anterior}")
    st.metric("Resultado", f"R$ {dre['mesmo_periodo_ano_anterior']['resultado']:,.2f}",
               delta=_delta(dre["atual"]["resultado"], dre["mesmo_periodo_ano_anterior"]["resultado"]))
idx += 1
with comp_cols[idx]:
    st.caption(f"Acumulado de {ano_sel} (YTD) vs mesmo periodo de {ano_sel - 1}")
    st.metric(f"YTD {ano_sel}: R$ {dre['acumulado_ano_atual']['resultado']:,.2f}",
              f"YTD {ano_sel - 1}: R$ {dre['acumulado_ano_anterior']['resultado']:,.2f}",
              delta=_delta(dre["acumulado_ano_atual"]["resultado"], dre["acumulado_ano_anterior"]["resultado"]))

st.subheader(f"Gasto por categoria -- {rotulo_periodo_atual}")
gpc = pd.Series(dre["atual"]["por_categoria"]).abs().sort_values(ascending=False)
if not gpc.empty:
    st.bar_chart(gpc)
else:
    st.info("Sem gasto no periodo selecionado.")

st.subheader("Forecast de caixa")
horizonte = st.radio(
    "Horizonte da projecao de saldo", options=[30, 90, 180, 365],
    format_func=lambda d: f"{d} dias" if d < 365 else "1 ano", horizontal=True, key="forecast_horizonte",
)
fcs1, fcs2 = st.columns(2)

with fcs1:
    st.caption(f"Saldo projetado (contas, proximos {horizonte} dias)")
    saldos = requests.get(f"{API_URL}/forecast/saldo", params={"dias": horizonte}, headers=auth_headers()).json()
    if not saldos:
        st.info("Nenhuma conta bancaria (tipo CONTA) ainda.")
    for conta in saldos:
        st.metric(
            conta["nome"],
            f"R$ {conta['saldo_projetado']:,.2f}",
            delta=f"{conta['saldo_projetado'] - conta['saldo_atual']:,.2f} ate o fim do periodo",
        )
        pontos = pd.DataFrame(conta["pontos"]).set_index("data")
        st.line_chart(pontos)

with fcs2:
    st.caption("Fatura prevista do(s) cartao(oes) -- mes atual")
    faturas = requests.get(f"{API_URL}/forecast/fatura", headers=auth_headers()).json()
    if not faturas:
        st.info("Nenhum cartao (tipo CARTAO) ainda.")
    for cartao in faturas:
        st.metric(f"{cartao['nome']} ({cartao['competencia']})", f"R$ {cartao['total']:,.2f}")
        st.caption(f"Realizado: R$ {cartao['realizado']:,.2f}  |  Previsto (parcelas): R$ {cartao['previsto']:,.2f}")

st.subheader(f"Orcamento: real x orcado -- {rotulo_periodo_atual}")
comp = requests.get(f"{API_URL}/orcamentos/comparativo", params=periodo_params, headers=auth_headers()).json()
df_comp = pd.DataFrame(comp["categorias"])
if not df_comp.empty:
    st.dataframe(
        df_comp.rename(columns={
            "categoria_id": "Categoria", "orcado": "Orcado", "realizado": "Realizado",
            "desvio": "Desvio (R$)", "desvio_pct": "Desvio (%)", "origem_orcamento": "Origem",
        }),
        hide_index=True, use_container_width=True,
    )
    cc1, cc2 = st.columns(2)
    cc1.metric("Orcado (categorias c/ orcamento)", f"R$ {comp['orcado_total']:,.2f}")
    cc2.metric("Realizado (todas categorias)", f"R$ {comp['realizado_total']:,.2f}")
else:
    st.info("Nenhum dado no periodo. Defina um orcamento abaixo ou rode um sync.")

with st.expander("Definir orcamento por categoria"):
    bc1, bc2, bc3, bc4 = st.columns([2, 1, 1, 1])
    cat_orc = bc1.selectbox("Categoria", options=[c for c in CATEGORIAS if c != "neutro"], key="def_categoria")
    ano_def = bc2.number_input("Ano", min_value=2000, max_value=2100, value=int(ano_sel), step=1, key="def_ano")
    mes_def = bc3.selectbox(
        "Mes", options=[0] + list(range(1, 13)),
        format_func=lambda m: "Anual" if m == 0 else f"{m:02d}",
        index=(mes_sel or 0), key="def_mes",
    )
    valor_def = bc4.number_input("Valor (R$)", min_value=0.0, step=50.0, key="def_valor")
    if st.button("Salvar orcamento"):
        r = requests.put(
            f"{API_URL}/orcamentos",
            json={"categoria_id": cat_orc, "ano": int(ano_def), "mes": int(mes_def), "valor": float(valor_def)},
            headers=auth_headers(),
        )
        if r.status_code == 200:
            st.success("Orcamento salvo.")
            st.rerun()
        else:
            st.error(r.text)

st.subheader("Patrimonio manual (investimentos, imoveis etc)")
st.caption(
    "A Pluggy pessoal so traz movimentacao de conta/cartao, nao posicao de carteira. "
    "Cadastre aqui o que ela nao ve, e atualize o valor sempre que quiser."
)

resumo_patrimonio = requests.get(f"{API_URL}/patrimonio/resumo", headers=auth_headers()).json()
rp1, rp2, rp3 = st.columns(3)
rp1.metric("Saldo das contas", f"R$ {resumo_patrimonio['contas']:,.2f}")
rp2.metric("Ativos cadastrados a mao", f"R$ {resumo_patrimonio['ativos_manuais']:,.2f}")
rp3.metric("Patrimonio total", f"R$ {resumo_patrimonio['total']:,.2f}")

with st.expander("Cadastrar novo ativo"):
    nc1, nc2, nc3 = st.columns(3)
    novo_nome = nc1.text_input("Nome (ex: Tesouro Direto, Apartamento)", key="novo_ativo_nome")
    novo_categoria = nc2.selectbox("Categoria", options=["investimento", "imovel", "outro"], key="novo_ativo_categoria")
    novo_valor = nc3.number_input("Valor atual (R$)", min_value=0.0, step=100.0, key="novo_ativo_valor")
    if st.button("Cadastrar ativo"):
        if not novo_nome.strip():
            st.error("Informe um nome para o ativo.")
        else:
            r = requests.post(
                f"{API_URL}/patrimonio/ativos",
                json={"nome": novo_nome, "categoria": novo_categoria, "valor_inicial": float(novo_valor)},
                headers=auth_headers(),
            )
            if r.status_code == 201:
                st.success("Ativo cadastrado.")
                st.rerun()
            else:
                st.error(r.text)

ativos = requests.get(f"{API_URL}/patrimonio/ativos", headers=auth_headers()).json()
if not ativos:
    st.info("Nenhum ativo manual cadastrado ainda.")
else:
    for ativo in ativos:
        with st.expander(f"{ativo['nome']} ({ativo['categoria']}) -- R$ {ativo['valor_atual']:,.2f}"):
            mc1, mc2, mc3, mc4 = st.columns([1, 1, 2, 1])
            tipo_mov = mc1.selectbox(
                "Tipo", options=["APORTE", "RETIRADA", "AJUSTE_VALOR"],
                format_func=lambda t: {"APORTE": "Aporte", "RETIRADA": "Retirada", "AJUSTE_VALOR": "Ajustar valor para"}[t],
                key=f"tipo_{ativo['id']}",
            )
            valor_mov = mc2.number_input("Valor (R$)", min_value=0.0, step=100.0, key=f"valor_{ativo['id']}")
            obs_mov = mc3.text_input("Observacao (opcional)", key=f"obs_{ativo['id']}")
            if mc4.button("Registrar", key=f"btn_{ativo['id']}"):
                r = requests.post(
                    f"{API_URL}/patrimonio/ativos/{ativo['id']}/movimentos",
                    json={"tipo": tipo_mov, "valor": float(valor_mov), "observacao": obs_mov},
                    headers=auth_headers(),
                )
                if r.status_code == 200:
                    st.success("Movimento registrado.")
                    st.rerun()
                else:
                    st.error(r.text)

            movs = requests.get(f"{API_URL}/patrimonio/ativos/{ativo['id']}/movimentos", headers=auth_headers()).json()
            if movs:
                st.dataframe(
                    pd.DataFrame(movs)[["data", "tipo", "valor", "observacao"]].rename(columns={
                        "data": "Data", "tipo": "Tipo", "valor": "Valor (R$)", "observacao": "Observacao",
                    }),
                    hide_index=True, use_container_width=True,
                )
            if st.button("Remover ativo", key=f"del_{ativo['id']}"):
                requests.delete(f"{API_URL}/patrimonio/ativos/{ativo['id']}", headers=auth_headers())
                st.rerun()

st.subheader("Analise de investimentos")
inv = requests.get(f"{API_URL}/investimentos/resumo", headers=auth_headers()).json()
if not inv["ativos"]:
    st.info(
        "Nenhum ativo de categoria 'investimento' cadastrado em Patrimonio manual. "
        "Cadastre um acima para ver a rentabilidade aqui."
    )
else:
    iv1, iv2, iv3 = st.columns(3)
    iv1.metric("Total investido (atual)", f"R$ {inv['total_investido_atual']:,.2f}")
    iv2.metric("Total aportado (liquido)", f"R$ {inv['total_aportado_liquido']:,.2f}")
    iv3.metric(
        "Rentabilidade",
        f"R$ {inv['rentabilidade_rs_total']:,.2f}",
        delta=f"{inv['rentabilidade_pct_total']}%" if inv["rentabilidade_pct_total"] is not None else None,
    )
    st.dataframe(
        pd.DataFrame(inv["ativos"]).rename(columns={
            "nome": "Ativo", "valor_atual": "Valor atual", "total_aportado_liquido": "Aportado (liquido)",
            "rentabilidade_rs": "Rentabilidade (R$)", "rentabilidade_pct": "Rentabilidade (%)",
        })[["Ativo", "Valor atual", "Aportado (liquido)", "Rentabilidade (R$)", "Rentabilidade (%)"]],
        hide_index=True, use_container_width=True,
    )
if inv["eventos_movimentacao_detectados"]:
    st.caption(
        f"Detectei {inv['eventos_movimentacao_detectados']} evento(s) de aplicacao/resgate nas contas "
        "sincronizadas -- sao so movimentacao (a Pluggy pessoal nao traz posicao de carteira), "
        "cadastre o ativo correspondente em Patrimonio manual para acompanhar a rentabilidade real."
    )

st.subheader("Patrimonio e aposentadoria")
perfil_resp = requests.get(f"{API_URL}/aposentadoria/perfil", headers=auth_headers())
perfil_atual = perfil_resp.json() if perfil_resp.status_code == 200 else None

with st.expander("Definir perfil de aposentadoria", expanded=(perfil_atual is None)):
    pc1, pc2, pc3 = st.columns(3)
    idade_atual = pc1.number_input(
        "Idade atual", min_value=0, max_value=100,
        value=(perfil_atual or {}).get("idade_atual", 30), key="apo_idade_atual",
    )
    idade_aposentadoria = pc2.number_input(
        "Idade desejada de aposentadoria", min_value=0, max_value=100,
        value=(perfil_atual or {}).get("idade_aposentadoria", 60), key="apo_idade_aposentadoria",
    )
    renda_desejada = pc3.number_input(
        "Renda passiva desejada (R$/mes)", min_value=0.0, step=500.0,
        value=(perfil_atual or {}).get("renda_desejada_mensal", 5000.0), key="apo_renda",
    )
    pc4, pc5 = st.columns(2)
    taxa_retorno = pc4.number_input(
        "Taxa de retorno REAL esperada (% a.a., acima da inflacao)", min_value=0.0, max_value=20.0, step=0.5,
        value=(perfil_atual or {}).get("taxa_retorno_anual_pct", 4.0), key="apo_taxa",
    )
    aporte_mensal = pc5.number_input(
        "Aporte mensal atual (R$)", min_value=0.0, step=100.0,
        value=(perfil_atual or {}).get("aporte_mensal", 0.0), key="apo_aporte",
    )
    if st.button("Salvar perfil de aposentadoria"):
        r = requests.put(
            f"{API_URL}/aposentadoria/perfil",
            json={
                "idade_atual": int(idade_atual), "idade_aposentadoria": int(idade_aposentadoria),
                "renda_desejada_mensal": float(renda_desejada), "taxa_retorno_anual_pct": float(taxa_retorno),
                "aporte_mensal": float(aporte_mensal),
            },
            headers=auth_headers(),
        )
        if r.status_code == 200:
            st.success("Perfil salvo.")
            st.rerun()
        else:
            st.error(r.text)

if perfil_atual:
    proj = requests.get(f"{API_URL}/aposentadoria/projecao", headers=auth_headers()).json()
    pj1, pj2, pj3 = st.columns(3)
    pj1.metric("Patrimonio atual", f"R$ {proj['patrimonio_atual']:,.2f}")
    pj2.metric(
        f"Patrimonio projetado aos {proj['idade_aposentadoria']}",
        f"R$ {proj['patrimonio_projetado_aposentadoria']:,.2f}",
    )
    pj3.metric(
        "Renda passiva estimada",
        f"R$ {proj['renda_passiva_estimada_mensal']:,.2f}/mes",
        delta=f"{proj['deficit_superavit_mensal']:,.2f} vs meta",
    )
    if proj["deficit_superavit_mensal"] < 0:
        st.warning(
            f"No ritmo atual, a renda passiva projetada fica R$ {abs(proj['deficit_superavit_mensal']):,.2f} "
            f"abaixo da meta. Para fechar a conta, o aporte mensal precisaria ser de "
            f"R$ {proj['aporte_mensal_necessario_para_meta']:,.2f} (hoje: R$ {aporte_mensal:,.2f})."
        )
    else:
        st.success("No ritmo atual, a meta de renda passiva e atingida ou superada.")
    traj = pd.DataFrame(proj["trajetoria"]).set_index("idade")
    st.line_chart(traj)
else:
    st.info("Defina o perfil de aposentadoria acima para ver a projecao.")

st.subheader("Classificar pendentes")
pend = df[df["categoria_id"] == "nao_classificado"][
    ["id", "data", "conta_nome", "descricao", "valor", "categoria_id"]
].copy()

if pend.empty:
    st.success("Nada pendente. Tudo classificado!")
else:
    st.caption(
        f"{len(pend)} transacao(oes) sem categoria, de debito (conta) e credito (cartao) misturadas "
        "(coluna 'Conta' mostra de onde vem cada uma). Escolha a categoria e clique em salvar. "
        "O sistema aprende e reaplica sozinho (na API, automaticamente nos proximos syncs)."
    )

    st.markdown("**Classificar com IA** -- a IA le o nome do fornecedor e sugere a categoria de cada pendente.")
    if st.button("Classificar pendentes com IA (Claude)"):
        with st.spinner("A IA esta classificando os fornecedores... pode levar ate ~1 min."):
            resp = requests.post(
                f"{API_URL}/eventos/classificar-ia", headers=auth_headers(), timeout=300,
            )
        if resp.status_code == 200:
            d = resp.json()
            st.success(
                f"IA classificou {d['classificados']} transacao(oes) "
                f"({d['fornecedores_reconhecidos']} fornecedor(es) reconhecido(s)). "
                f"Restam {d['pendentes_restantes']} pendente(s). "
                "Confira abaixo e corrija o que estiver errado (suas correcoes viram memoria)."
            )
            st.rerun()
        else:
            try:
                st.error(resp.json().get("detail", resp.text))
            except Exception:
                st.error(resp.text)
    col_f1, col_f2 = st.columns(2)
    filtro_conta = col_f1.multiselect(
        "Filtrar por conta (opcional)", options=sorted(pend["conta_nome"].unique()), key="filtro_conta_pendentes",
    )
    data_de = col_f2.date_input(
        "Classificar a partir de (data)", value=date(2026, 6, 1), key="filtro_data_pendentes",
        help="Mostra so as pendencias com data >= a escolhida. Util para focar do mes atual para frente.",
    )
    if filtro_conta:
        pend = pend[pend["conta_nome"].isin(filtro_conta)]
    _datas = pd.to_datetime(pend["data"], errors="coerce").dt.date
    pend = pend[_datas >= data_de]
    st.caption(f"{len(pend)} pendencia(s) a partir de {data_de.strftime('%d/%m/%Y')}.")
    st.caption(
        "Edite quantas linhas quiser -- nada e enviado enquanto voce nao clicar em "
        "'Salvar classificacoes'. As edicoes ficam so na tela ate la (mais rapido)."
    )
    with st.form("form_classificar", clear_on_submit=False):
        editado = st.data_editor(
            pend,
            column_config={
                "id": None,
                "data": st.column_config.TextColumn("Data", disabled=True),
                "conta_nome": st.column_config.TextColumn("Conta", disabled=True),
                "descricao": st.column_config.TextColumn("Descricao", disabled=True, width="large"),
                "valor": st.column_config.NumberColumn("Valor", disabled=True, format="R$ %.2f"),
                "categoria_id": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS),
            },
            hide_index=True, use_container_width=True, key="editor",
        )
        salvar = st.form_submit_button("Salvar classificacoes", type="primary")
    if salvar:
        original = pend.set_index("id")["categoria_id"].to_dict()
        mudou = 0
        falhas = 0
        for _, row in editado.iterrows():
            nova = row["categoria_id"]
            # so envia o que o usuario realmente mudou nesta sessao de edicao
            if nova != "nao_classificado" and original.get(row["id"]) != nova:
                resp = requests.patch(
                    f"{API_URL}/eventos/{row['id']}/categoria",
                    json={"categoria_id": nova},
                    headers=auth_headers(),
                )
                if resp.status_code in (200, 204):
                    mudou += 1
                else:
                    falhas += 1
        if falhas:
            st.warning(f"{mudou} classificada(s); {falhas} falha(s).")
        else:
            st.success(f"{mudou} classificada(s) de uma vez.")
        st.rerun()

with st.expander("Ver todas as transacoes"):
    st.dataframe(
        df[["data", "conta_nome", "natureza", "status", "categoria_id", "categoria_fonte", "valor", "descricao"]],
        hide_index=True, use_container_width=True,
    )
