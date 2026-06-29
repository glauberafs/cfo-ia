"""Normalizacao: Transacao Bruta (Pluggy) -> Evento Financeiro."""
import hashlib
import uuid

from .models import EventoFinanceiro, Natureza, Status, TipoConta, NEUTRAS_PATRIMONIO
from .categorize import categorizar


def hash_transacao(t: dict, conta_id: str) -> str:
    base = f"{t.get('date')}|{t.get('description')}|{t.get('amount')}|{conta_id}"
    return hashlib.sha256(base.encode()).hexdigest()


def _normalizar_sinal(amount: float, tipo_conta: str) -> float:
    if tipo_conta == TipoConta.CARTAO:
        return -amount
    return amount


def _inferir_natureza(t: dict, tipo_conta: str, valor: float) -> str:
    ccm = t.get("creditCardMetadata") or {}
    desc = (t.get("description") or "").upper()
    fee = ccm.get("feeType")

    if fee or "ANUIDADE" in desc or "TARIFA" in desc:
        return Natureza.TARIFA

    if tipo_conta == TipoConta.CARTAO:
        if valor > 0:
            return Natureza.PAGAMENTO_FATURA
        if (ccm.get("totalInstallments") or 1) > 1:
            return Natureza.PARCELA
        return Natureza.COMPRA

    if (ccm.get("totalInstallments") or 1) > 1:
        return Natureza.PARCELA
    if "APLICACAO" in desc:
        return Natureza.APLICACAO
    if "RESGATE" in desc:
        return Natureza.RESGATE
    chaves_transf = ("PIX", "TED ", " TED", "DOC ", "TRANSFER")
    if any(k in desc for k in chaves_transf):
        return Natureza.TRANSFERENCIA
    if valor > 0:
        return Natureza.RECEITA
    return Natureza.COMPRA


def normalizar(t: dict, conta, transacao_bruta_id: str) -> EventoFinanceiro:
    tipo = conta.tipo
    valor = _normalizar_sinal(float(t.get("amount", 0)), tipo)
    natureza = _inferir_natureza(t, tipo, valor)
    status = Status.PREVISTO if (t.get("status") == "PENDING") else Status.REALIZADO

    merchant = t.get("merchant") or {}
    contraparte = merchant.get("name")
    if not contraparte:
        pdata = t.get("paymentData") or {}
        recv = pdata.get("receiver") or {}
        contraparte = recv.get("name")

    cat_id, cat_fonte, cat_conf = categorizar(
        t.get("description", ""), natureza, merchant.get("category")
    )

    ccm = t.get("creditCardMetadata") or {}

    return EventoFinanceiro(
        id=str(uuid.uuid4()),
        transacao_bruta_id=transacao_bruta_id,
        conta_id=conta.id,
        data=(t.get("date", "")[:10]),
        descricao=t.get("description", ""),
        descricao_raw=t.get("descriptionRaw") or t.get("description", ""),
        valor=round(valor, 2),
        natureza=natureza,
        status=status,
        categoria_id=cat_id,
        categoria_fonte=cat_fonte,
        categoria_confianca=cat_conf,
        afeta_patrimonio=(natureza not in NEUTRAS_PATRIMONIO),
        contraparte=contraparte,
        parcela_numero=ccm.get("installmentNumber"),
        parcela_total=ccm.get("totalInstallments"),
    )