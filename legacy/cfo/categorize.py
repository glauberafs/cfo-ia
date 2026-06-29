"""Categorizacao propria (regra + futuro LLM).

No tier pessoal da Pluggy o campo `category` costuma vir vazio (e recurso Pro),
entao classificamos por conta propria. v1 = regras por palavra-chave na descricao.
Casos sem confianca caem em 'nao_classificado' para revisao -> dps entra o LLM.
"""

# (palavras-chave) -> (categoria_id, grupo)
REGRAS = [
    (("posto", "ipiranga", "shell", "combust", "gasolina", "petrobras"), "combustivel", "Transporte"),
    (("uber", "99 ", "99app", "cabify"), "transporte_app", "Transporte"),
    (("supermerc", "mercado", "atacad", "carrefour", "pao de acucar", "assai"), "mercado", "Alimentacao"),
    (("ifood", "rappi", "delivery"), "delivery", "Alimentacao"),
    (("restaurante", "lanchonete", "bar ", "padaria", "cafe"), "restaurante", "Alimentacao"),
    (("netflix", "spotify", "disney", "hbo", "prime video", "youtube premium"), "streaming", "Lazer"),
    (("farmacia", "drogaria", "droga raia", "pacheco"), "farmacia", "Saude"),
    (("academia", "smartfit", "gympass"), "academia", "Saude"),
    (("enel", "light", "cemig", "energia"), "energia", "Moradia"),
    (("sabesp", "agua", "cedae"), "agua", "Moradia"),
    (("vivo", "claro", "tim", "internet", "net "), "internet_telefone", "Moradia"),
    (("salario", "pagamento salario", "folha"), "salario", "Receitas"),
]


def categorizar(descricao: str, natureza: str, merchant_category: str | None = None):
    """Retorna (categoria_id, fonte, confianca)."""
    # naturezas neutras nao precisam de categoria de consumo
    from .models import NEUTRAS_PATRIMONIO
    if natureza in NEUTRAS_PATRIMONIO:
        return ("neutro", "REGRA", 1.0)

    texto = (descricao or "").lower()
    for chaves, cat, _grupo in REGRAS:
        if any(k in texto for k in chaves):
            return (cat, "REGRA", 0.9)

    # dica da Pluggy (so plano Pro) como fallback fraco
    if merchant_category:
        return (merchant_category.lower().replace(" ", "_"), "PLUGGY", 0.6)

    return ("nao_classificado", "REGRA", 0.0)
