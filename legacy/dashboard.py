"""CFO IA - dashboard (Streamlit)."""
import re
import sqlite3

import pandas as pd
import streamlit as st

DB = "cfo.db"

CATEGORIAS = [
    "nao_classificado", "neutro",
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


def conectar():
    return sqlite3.connect(DB)


def garantir_memoria():
    with conectar() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS memoria_categoria ("
            "chave TEXT PRIMARY KEY, categoria_id TEXT)"
        )


def chave_memoria(descricao):
    t = (descricao or "").upper()
    for pref in ["COMPRA CARTAO DEB MC", "COMPRA CARTAO", "PIX ENVIADO",
                 "PIX RECEBIDO", "PIX AGENDADO", "PIX", "TED", "DOC"]:
        t = t.replace(pref, " ")
    t = re.sub(r"\d{2}/\d{2}", " ", t)
    t = re.sub(r"\d{2}:\d{2}", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def carregar_memoria():
    with conectar() as c:
        rows = c.execute("SELECT chave, categoria_id FROM memoria_categoria").fetchall()
    return {k: v for k, v in rows}


def salvar_memoria(chave, categoria_id):
    if not chave:
        return
    with conectar() as c:
        c.execute(
            "INSERT OR REPLACE INTO memoria_categoria (chave, categoria_id) VALUES (?,?)",
            (chave, categoria_id),
        )


def aplicar_memoria_em_tudo():
    mem = carregar_memoria()
    if not mem:
        return 0
    n = 0
    with conectar() as c:
        eventos = c.execute("SELECT id, descricao FROM eventos").fetchall()
        for eid, desc in eventos:
            cat = mem.get(chave_memoria(desc))
            if cat:
                c.execute(
                    "UPDATE eventos SET categoria_id=?, categoria_fonte='USUARIO', "
                    "categoria_confianca=1.0 WHERE id=?",
                    (cat, eid),
                )
                n += 1
    return n


def classificar_evento(evento_id, descricao, categoria_id):
    salvar_memoria(chave_memoria(descricao), categoria_id)
    with conectar() as c:
        c.execute(
            "UPDATE eventos SET categoria_id=?, categoria_fonte='USUARIO', "
            "categoria_confianca=1.0 WHERE id=?",
            (categoria_id, evento_id),
        )


def carregar_eventos():
    with conectar() as c:
        return pd.read_sql_query("SELECT * FROM eventos ORDER BY data", c)


st.set_page_config(page_title="CFO IA", layout="wide")
garantir_memoria()

st.title("CFO IA")
st.caption("Sistema inteligente de gestao financeira pessoal")

df = carregar_eventos()
if df.empty:
    st.warning("Nenhum evento encontrado. Rode 'python main.py' primeiro.")
    st.stop()

realizados = df[df["status"] == "REALIZADO"]
patrimonio = realizados[realizados["afeta_patrimonio"] == 1]
receitas = patrimonio[patrimonio["valor"] > 0]["valor"].sum()
gastos = patrimonio[patrimonio["valor"] < 0]["valor"].sum()
previstos = df[df["status"] == "PREVISTO"]["valor"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Receitas", f"R$ {receitas:,.2f}")
c2.metric("Gastos", f"R$ {gastos:,.2f}")
c3.metric("Resultado", f"R$ {receitas + gastos:,.2f}")
c4.metric("Obrigacoes futuras", f"R$ {previstos:,.2f}")

st.subheader("Gasto por categoria")
gpc = (
    patrimonio[patrimonio["valor"] < 0]
    .groupby("categoria_id")["valor"].sum().abs().sort_values(ascending=False)
)
if not gpc.empty:
    st.bar_chart(gpc)

st.subheader("Classificar pendentes")
pend = df[df["categoria_id"] == "nao_classificado"][
    ["id", "data", "descricao", "valor", "categoria_id"]
].copy()

if pend.empty:
    st.success("Nada pendente. Tudo classificado!")
else:
    st.caption(
        f"{len(pend)} transacao(oes) sem categoria. Escolha a categoria na coluna "
        "da direita e clique em salvar. O sistema aprende e reaplica sozinho."
    )
    editado = st.data_editor(
        pend,
        column_config={
            "id": None,
            "data": st.column_config.TextColumn("Data", disabled=True),
            "descricao": st.column_config.TextColumn("Descricao", disabled=True, width="large"),
            "valor": st.column_config.NumberColumn("Valor", disabled=True, format="R$ %.2f"),
            "categoria_id": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS),
        },
        hide_index=True, use_container_width=True, key="editor",
    )
    if st.button("Salvar classificacoes", type="primary"):
        mudou = 0
        for _, row in editado.iterrows():
            if row["categoria_id"] != "nao_classificado":
                classificar_evento(row["id"], row["descricao"], row["categoria_id"])
                mudou += 1
        total = aplicar_memoria_em_tudo()
        st.success(f"{mudou} classificada(s). Memoria reaplicada a {total} evento(s).")
        st.rerun()

with st.expander("Ver todas as transacoes"):
    st.dataframe(
        df[["data", "natureza", "status", "categoria_id", "categoria_fonte",
            "valor", "descricao"]],
        hide_index=True, use_container_width=True,
    )

if st.button("Reaplicar memoria a tudo"):
    total = aplicar_memoria_em_tudo()
    st.success(f"Memoria reaplicada a {total} evento(s).")
    st.rerun()