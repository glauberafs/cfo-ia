"""Forecast de caixa: saldo futuro de contas e fatura prevista de cartoes.

Usa so o que ja esta nos dados (eventos PREVISTO: parcelas futuras, pagamento
de fatura previsto) -- nao estima gasto recorrente por media historica ainda
(proximo passo, se fizer sentido).
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..models import Conta, Evento, Natureza, Status, TipoConta, Usuario


def projetar_saldo(db: Session, usuario: Usuario, dias: int = 30) -> list[dict]:
    hoje = date.today()
    fim = hoje + timedelta(days=dias)

    contas = db.query(Conta).filter(Conta.usuario_id == usuario.id, Conta.tipo == TipoConta.CONTA).all()
    resultado = []

    for conta in contas:
        eventos = (
            db.query(Evento)
            .filter(
                Evento.usuario_id == usuario.id,
                Evento.conta_id == conta.id,
                Evento.status == Status.PREVISTO,
                Evento.data >= hoje.isoformat(),
                Evento.data <= fim.isoformat(),
            )
            .order_by(Evento.data)
            .all()
        )

        saldo = conta.saldo
        pontos = [{"data": hoje.isoformat(), "saldo": round(saldo, 2)}]
        for ev in eventos:
            saldo += ev.valor
            pontos.append({"data": ev.data, "saldo": round(saldo, 2)})

        resultado.append({
            "conta_id": conta.id,
            "nome": conta.nome,
            "saldo_atual": round(conta.saldo, 2),
            "saldo_projetado": round(saldo, 2),
            "pontos": pontos,
        })

    return resultado


def projetar_fatura(db: Session, usuario: Usuario) -> list[dict]:
    """Fatura do mes atual de cada cartao: realizado (compras ja feitas) +
    previsto (parcelas futuras que caem neste mes). Pagamento de fatura nao entra."""
    hoje = date.today()
    competencia = hoje.strftime("%Y-%m")

    cartoes = db.query(Conta).filter(Conta.usuario_id == usuario.id, Conta.tipo == TipoConta.CARTAO).all()
    resultado = []

    for cartao in cartoes:
        eventos = (
            db.query(Evento)
            .filter(
                Evento.usuario_id == usuario.id,
                Evento.conta_id == cartao.id,
                Evento.data.like(f"{competencia}%"),
                Evento.natureza.in_([Natureza.COMPRA, Natureza.PARCELA, Natureza.TARIFA]),
            )
            .all()
        )
        realizado = sum(-ev.valor for ev in eventos if ev.status == Status.REALIZADO)
        previsto = sum(-ev.valor for ev in eventos if ev.status == Status.PREVISTO)

        resultado.append({
            "conta_id": cartao.id,
            "nome": cartao.nome,
            "competencia": competencia,
            "realizado": round(realizado, 2),
            "previsto": round(previsto, 2),
            "total": round(realizado + previsto, 2),
        })

    return resultado
