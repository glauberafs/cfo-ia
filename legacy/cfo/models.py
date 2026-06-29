"""Modelos do Core Financeiro. Espelham a spec do Evento Financeiro v1.0."""
from dataclasses import dataclass, field, asdict
from typing import Optional


# Naturezas possiveis de um evento
class Natureza:
    COMPRA = "COMPRA"
    RECEITA = "RECEITA"
    TRANSFERENCIA = "TRANSFERENCIA"
    PARCELA = "PARCELA"
    PAGAMENTO_FATURA = "PAGAMENTO_FATURA"
    TARIFA = "TARIFA"
    APLICACAO = "APLICACAO"
    RESGATE = "RESGATE"


class Status:
    REALIZADO = "REALIZADO"
    PREVISTO = "PREVISTO"


class TipoConta:
    CONTA = "CONTA"      # checking/savings (BANK)
    CARTAO = "CARTAO"    # credit card (CREDIT)


# Naturezas que NAO afetam o patrimonio liquido
NEUTRAS_PATRIMONIO = {
    Natureza.TRANSFERENCIA,
    Natureza.PAGAMENTO_FATURA,
    Natureza.APLICACAO,
    Natureza.RESGATE,
}


@dataclass
class Conta:
    id: str
    pluggy_account_id: str
    nome: str
    tipo: str          # TipoConta
    instituicao: str
    saldo: float
    moeda: str = "BRL"


@dataclass
class EventoFinanceiro:
    id: str
    transacao_bruta_id: str
    conta_id: str
    data: str          # ISO date
    descricao: str
    descricao_raw: str
    valor: float       # convencao unica: saida negativa, entrada positiva
    natureza: str
    status: str
    categoria_id: str
    categoria_fonte: str          # PLUGGY | REGRA | LLM | USUARIO
    categoria_confianca: Optional[float]
    afeta_patrimonio: bool
    contraparte: Optional[str] = None
    parcela_numero: Optional[int] = None
    parcela_total: Optional[int] = None
    tags: list = field(default_factory=list)

    def to_row(self) -> dict:
        d = asdict(self)
        d["tags"] = ",".join(self.tags)
        return d
