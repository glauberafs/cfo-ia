"""Categorizacao propria (regra + futuro LLM).

Taxonomia 100% em portugues (spec v1.0). A dica de categoria da Pluggy (em
ingles, so plano Pro) NUNCA e usada diretamente como categoria final -- serve
apenas de sinal auxiliar via MAPA_PLUGGY abaixo. O que nao casa com nenhuma
regra cai em 'nao_classificado' para revisao manual / LLM.
"""
from .models_const import NEUTRAS_PATRIMONIO

# (palavras-chave) -> categoria_id
REGRAS = [
    (("posto", "ipiranga", "shell", "combust", "gasolina", "petrobras"), "combustivel"),
    (("uber", "99 ", "99app", "cabify"), "transporte_app"),
    (("metro", "onibus", "bilhete unico", "vlt", "trem"), "transporte_publico"),
    (("estacionamento", "pedagio", "sem parar", "conectcar"), "estacionamento_pedagio"),
    (("supermerc", "mercado", "atacad", "carrefour", "pao de acucar", "assai", "extra "), "mercado"),
    (("ifood", "rappi", "delivery"), "delivery"),
    (("padaria", "cafe ", "confeitaria"), "padaria_cafe"),
    (("restaurante", "lanchonete", "bar ", "churrascaria", "pizzaria"), "restaurante"),
    (("netflix", "spotify", "disney", "hbo", "prime video", "youtube premium", "deezer"), "streaming"),
    (("farmacia", "drogaria", "droga raia", "pacheco"), "farmacia"),
    (("academia", "smartfit", "gympass"), "academia"),
    (("plano de saude", "unimed", "amil", "bradesco saude", "sulamerica saude"), "plano_saude"),
    (("consulta", "exame", "laboratorio", "clinica"), "consultas_exames"),
    (("enel", "light ", "cemig", "energia eletrica", "cpfl"), "energia"),
    (("sabesp", "agua e esgoto", "cedae", "copasa"), "agua"),
    (("comgas", "gas natural", "ultragaz"), "gas"),
    (("vivo", "claro", "tim ", "internet", "net serv", "oi telecom"), "internet_telefone"),
    (("aluguel", "financiamento imovel", "imobiliaria"), "aluguel_financiamento"),
    (("condominio",), "condominio"),
    (("seguro auto", "seguro veicular", "porto seguro auto"), "seguro_veiculo"),
    (("oficina", "mecanic", "auto center", "revisao veiculo"), "manutencao_veiculo"),
    (("escola", "faculdade", "mensalidade escolar", "colegio"), "mensalidade"),
    (("curso", "udemy", "alura", "coursera"), "cursos"),
    (("livraria", "papelaria", "material escolar"), "livros_materiais"),
    (("cinema", "show", "balada", "evento "), "bares_eventos"),
    (("viagem", "hotel", "booking", "airbnb", "passagem aerea", "latam", "gol linhas", "azul linhas"), "viagens"),
    (("loja de roupa", "vestuario", "renner", "c&a", "riachuelo"), "vestuario"),
    (("magazine", "eletronico", "casas bahia", "americanas", "kabum"), "eletronicos"),
    (("presente", "loja de presentes"), "presentes"),
    (("imposto", "darf", "ipva", "iptu", "taxa "), "impostos_taxas"),
    (("tarifa", "anuidade", "manutencao de conta"), "tarifas_bancarias"),
    (("juros", "iof", "multa atraso"), "juros"),
    (("salario", "pagamento salario", "folha de pagamento"), "salario"),
    (("reembolso",), "reembolsos"),
    (("rendimento", "dividendo", "juros sobre capital"), "rendimentos"),
    (("saque",), "saque"),
]

# Sinal auxiliar fraco: categoria da Pluggy (ingles, plano Pro) -> taxonomia propria (PT).
# So usado se nenhuma regra por palavra-chave casar.
MAPA_PLUGGY = {
    "video streaming": "streaming",
    "music streaming": "streaming",
    "groceries": "mercado",
    "restaurants and bars": "restaurante",
    "food and drinks": "restaurante",
    "fuel": "combustivel",
    "transport": "transporte_app",
    "pharmacy": "farmacia",
    "health": "consultas_exames",
    "housing": "aluguel_financiamento",
    "education": "mensalidade",
    "school": "mensalidade",
    "investments": "rendimentos",
    "income": "outras_receitas",
    "salary": "salario",
}

# Categorias de RECEITA -- nunca podem vir do fallback fraco da Pluggy quando
# o evento e uma SAIDA (valor<0). Bug real visto com dados do Santander: um
# debito automatico de fatura de outro cartao (saida) virava "rendimentos"
# porque a dica da Pluggy mapeava para uma categoria de receita.
CATEGORIAS_RECEITA = {"salario", "outras_receitas", "rendimentos", "renda_extra", "reembolsos"}


def categorizar(descricao: str, natureza: str, merchant_category: str | None = None, valor: float | None = None):
    """Retorna (categoria_id, fonte, confianca)."""
    if natureza in NEUTRAS_PATRIMONIO:
        return ("neutro", "REGRA", 1.0)

    texto = (descricao or "").lower()
    for chaves, cat in REGRAS:
        if any(k in texto for k in chaves):
            return (cat, "REGRA", 0.9)

    if merchant_category:
        cat_pt = MAPA_PLUGGY.get(merchant_category.strip().lower())
        if cat_pt and not (cat_pt in CATEGORIAS_RECEITA and valor is not None and valor < 0):
            return (cat_pt, "PLUGGY", 0.6)

    return ("nao_classificado", "REGRA", 0.0)
