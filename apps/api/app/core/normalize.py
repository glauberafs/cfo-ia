"""Normalizacao: Transacao Bruta (Pluggy) -> Evento Financeiro.

Corrige o problema conhecido #3 (transferencia para terceiro tratada como
neutra): a transferencia so e neutra se a contraparte casar com um dos
apelidos/documentos proprios do usuario (contas proprias em outros bancos).
Caso contrario e TRANSFERENCIA_TERCEIRO, que afeta o patrimonio de fato.

Validado com dados reais (Santander): os campos estruturados da Pluggy
(`merchant.name`, `paymentData.receiver.name`) costumam vir vazios para
PIX/TED nesse banco -- o nome da contraparte so existe como texto livre na
descricao ("PIX ENVIADO   NOME DA PESSOA"). Por isso ha um fallback que
extrai o nome da descricao quando os campos estruturados nao trazem nada.
"""
import hashlib
import re
import uuid

from .categorize import categorizar
from .models_const import Natureza, Status, TipoConta, NEUTRAS_PATRIMONIO


def hash_transacao(t: dict, conta_id: str) -> str:
    base = f"{t.get('date')}|{t.get('description')}|{t.get('amount')}|{conta_id}"
    return hashlib.sha256(base.encode()).hexdigest()


def chave_memoria(descricao: str) -> str:
    """Normaliza a descricao para casar transacoes do mesmo estabelecimento."""
    t = (descricao or "").upper()
    for pref in ["COMPRA CARTAO DEB MC", "COMPRA CARTAO", "PIX ENVIADO",
                 "PIX RECEBIDO", "PIX AGENDADO", "PIX", "TED", "DOC"]:
        t = t.replace(pref, " ")
    t = re.sub(r"\d{2}/\d{2}", " ", t)
    t = re.sub(r"\d{2}:\d{2}", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _normalizar_sinal(amount: float, tipo_conta: str) -> float:
    if tipo_conta == TipoConta.CARTAO:
        return -amount
    return amount


PREFIXOS_TRANSFERENCIA = ("PIX RECEBIDO", "PIX ENVIADO", "PIX AGENDADO", "PIX", "TED", "DOC", "TRANSFERENCIA")


def _extrair_contraparte_da_descricao(descricao: str) -> str | None:
    """Fallback quando merchant.name/paymentData.receiver.name vem vazio: o
    nome geralmente esta na propria descricao apos o prefixo do tipo de transferencia."""
    t = (descricao or "").strip()
    t_upper = t.upper()
    for pref in PREFIXOS_TRANSFERENCIA:
        if t_upper.startswith(pref):
            t = t[len(pref):].strip()
            break
    t = re.sub(r"\s+", " ", t).strip()
    return t or None


def _contraparte_e_propria(contraparte: str | None, apelidos_proprios: list[str]) -> bool:
    """Compara por substring (nao igualdade exata): bancos costumam truncar ou
    abreviar o nome na descricao (ex: "Glauber" vs apelido cadastrado
    "Glauber Santos"). O usuario controla a lista de apelidos, entao o risco
    de falso positivo com terceiros de primeiro nome igual e aceitavel."""
    if not contraparte or not apelidos_proprios:
        return False
    c = contraparte.strip().upper()
    if not c:
        return False
    for apelido in apelidos_proprios:
        a = apelido.strip().upper()
        if a and (a in c or c in a):
            return True
    return False


def _inferir_natureza(t: dict, tipo_conta: str, valor: float, contraparte_propria: bool) -> str:
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
        return Natureza.TRANSFERENCIA if contraparte_propria else Natureza.TRANSFERENCIA_TERCEIRO

    if valor > 0:
        return Natureza.RECEITA
    return Natureza.COMPRA


def normalizar(t: dict, conta, transacao_bruta_id: str, apelidos_proprios: list[str] | None = None) -> dict:
    """Retorna um dict pronto para instanciar o modelo Evento (ORM)."""
    apelidos_proprios = apelidos_proprios or []
    tipo = conta.tipo
    valor = _normalizar_sinal(float(t.get("amount", 0)), tipo)

    descricao = t.get("description", "")
    merchant = t.get("merchant") or {}
    contraparte = merchant.get("name")
    if not contraparte:
        pdata = t.get("paymentData") or {}
        recv = pdata.get("receiver") or {}
        contraparte = recv.get("name")
    if not contraparte and descricao.upper().startswith(PREFIXOS_TRANSFERENCIA):
        contraparte = _extrair_contraparte_da_descricao(descricao)

    propria = _contraparte_e_propria(contraparte, apelidos_proprios)
    natureza = _inferir_natureza(t, tipo, valor, propria)
    status = Status.PREVISTO if (t.get("status") == "PENDING") else Status.REALIZADO

    cat_id, cat_fonte, cat_conf = categorizar(
        descricao, natureza, merchant.get("category"), valor
    )

    ccm = t.get("creditCardMetadata") or {}

    return dict(
        id=str(uuid.uuid4()),
        usuario_id=conta.usuario_id,
        transacao_bruta_id=transacao_bruta_id,
        conta_id=conta.id,
        data=(t.get("date", "")[:10]),
        descricao=descricao,
        descricao_raw=t.get("descriptionRaw") or descricao,
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
        tags=[],
    )
