"""Alertas: tendencia de fechar o mes acima do orcamento (run-rate simples) e
projecao de saldo negativo nos proximos dias.
"""
import calendar
from datetime import date

from sqlalchemy.orm import Session

from ..models import Usuario
from .forecast_service import projetar_saldo
from .orcamento_service import comparativo


def alertas_orcamento(db: Session, usuario: Usuario) -> list[dict]:
    """So faz sentido para o mes em curso: projeta o gasto de fim de mes pela
    razao (gasto_ate_hoje / dias_passados) e compara com o orcado."""
    hoje = date.today()
    ano, mes = hoje.year, hoje.month
    dias_no_mes = calendar.monthrange(ano, mes)[1]
    dia_atual = hoje.day

    comp = comparativo(db, usuario, ano, mes)
    alertas = []
    for linha in comp["categorias"]:
        if not linha["orcado"] or dia_atual == 0:
            continue
        projetado = round(linha["realizado"] / dia_atual * dias_no_mes, 2)
        if projetado > linha["orcado"]:
            excedente = round(projetado - linha["orcado"], 2)
            alertas.append({
                "tipo": "ORCAMENTO_TENDENCIA",
                "categoria_id": linha["categoria_id"],
                "mensagem": (
                    f"No ritmo atual, '{linha['categoria_id']}' deve fechar o mes em "
                    f"R$ {projetado:,.2f}, R$ {excedente:,.2f} acima do orcado (R$ {linha['orcado']:,.2f})."
                ),
                "valor_orcado": linha["orcado"],
                "valor_realizado": linha["realizado"],
                "valor_projetado": projetado,
            })
    return alertas


def alertas_saldo(db: Session, usuario: Usuario, dias: int = 30) -> list[dict]:
    projecoes = projetar_saldo(db, usuario, dias)
    alertas = []
    for conta in projecoes:
        negativos = [p for p in conta["pontos"] if p["saldo"] < 0]
        if negativos:
            primeiro = negativos[0]
            alertas.append({
                "tipo": "SALDO_NEGATIVO",
                "conta_id": conta["conta_id"],
                "mensagem": (
                    f"Saldo projetado de '{conta['nome']}' fica negativo "
                    f"(R$ {primeiro['saldo']:,.2f}) em {primeiro['data']}."
                ),
                "data": primeiro["data"],
                "saldo_projetado": primeiro["saldo"],
            })
    return alertas


def listar_alertas(db: Session, usuario: Usuario) -> list[dict]:
    return alertas_orcamento(db, usuario) + alertas_saldo(db, usuario)
