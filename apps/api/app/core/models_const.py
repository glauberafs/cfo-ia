"""Constantes do dominio (naturezas, status), sem dependencia de banco/ORM."""


class Natureza:
    COMPRA = "COMPRA"
    RECEITA = "RECEITA"
    TRANSFERENCIA = "TRANSFERENCIA"                    # entre contas do proprio usuario (neutra)
    TRANSFERENCIA_TERCEIRO = "TRANSFERENCIA_TERCEIRO"  # para/de outra pessoa (afeta patrimonio)
    PARCELA = "PARCELA"
    PAGAMENTO_FATURA = "PAGAMENTO_FATURA"
    TARIFA = "TARIFA"
    APLICACAO = "APLICACAO"
    RESGATE = "RESGATE"


class Status:
    REALIZADO = "REALIZADO"
    PREVISTO = "PREVISTO"


class TipoConta:
    CONTA = "CONTA"
    CARTAO = "CARTAO"


NEUTRAS_PATRIMONIO = {
    Natureza.TRANSFERENCIA,
    Natureza.PAGAMENTO_FATURA,
    Natureza.APLICACAO,
    Natureza.RESGATE,
}

# Categorias que, quando aplicadas manualmente, marcam o evento como neutro
# (afeta_patrimonio=False): pagamento de fatura de cartao e transferencias proprias
# nao sao despesa real -- as compras do cartao ja entram individualmente.
NEUTRAS_CATEGORIA = {
    "neutro",
    "pagamento_cartao",
}
