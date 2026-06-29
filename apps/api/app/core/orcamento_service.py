"""Orcamento por categoria e comparativo real x orcado (mensal e anual).

mes=0 no orcamento representa o valor ANUAL daquela categoria/ano; quando o
usuario pede o comparativo de um mes especifico e nao ha orcamento mensal
cadastrado, usamos esse anual / 12 como fallback (ORIGEM ANUAL_PRORRATEADO).
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Evento, Orcamento, Status, Usuario


def upsert_orcamento(db: Session, usuario: Usuario, categoria_id: str, ano: int, mes: int, valor: float) -> Orcamento:
    orc = (
        db.query(Orcamento)
        .filter(
            Orcamento.usuario_id == usuario.id,
            Orcamento.categoria_id == categoria_id,
            Orcamento.ano == ano,
            Orcamento.mes == mes,
        )
        .first()
    )
    if orc:
        orc.valor = valor
    else:
        orc = Orcamento(usuario_id=usuario.id, categoria_id=categoria_id, ano=ano, mes=mes, valor=valor)
        db.add(orc)
    db.commit()
    db.refresh(orc)
    return orc


def listar_orcamentos(db: Session, usuario: Usuario, ano: int) -> list[Orcamento]:
    return (
        db.query(Orcamento)
        .filter(Orcamento.usuario_id == usuario.id, Orcamento.ano == ano)
        .order_by(Orcamento.categoria_id, Orcamento.mes)
        .all()
    )


def _gasto_realizado_por_categoria(db: Session, usuario_id: str, ano: int, mes: int | None) -> dict[str, float]:
    """Soma (em valor absoluto) o gasto realizado por categoria no periodo."""
    q = db.query(Evento.categoria_id, func.sum(Evento.valor)).filter(
        Evento.usuario_id == usuario_id,
        Evento.status == Status.REALIZADO,
        Evento.afeta_patrimonio.is_(True),
        Evento.valor < 0,
        func.substr(Evento.data, 1, 4) == str(ano),
    )
    if mes:
        q = q.filter(func.substr(Evento.data, 6, 2) == f"{mes:02d}")
    q = q.group_by(Evento.categoria_id)
    return {cat: abs(total) for cat, total in q.all()}


def comparativo(db: Session, usuario: Usuario, ano: int, mes: int | None) -> dict:
    realizado_por_cat = _gasto_realizado_por_categoria(db, usuario.id, ano, mes)

    orcamentos_ano = listar_orcamentos(db, usuario, ano)
    anuais = {o.categoria_id: o.valor for o in orcamentos_ano if o.mes == 0}
    mensais = {(o.categoria_id, o.mes): o.valor for o in orcamentos_ano if o.mes != 0}

    categorias_relevantes = set(realizado_por_cat) | set(anuais)
    if mes:
        categorias_relevantes |= {c for (c, m) in mensais if m == mes}
    else:
        categorias_relevantes |= {c for (c, _m) in mensais}

    linhas = []
    orcado_total = 0.0
    realizado_total = 0.0

    for cat in sorted(categorias_relevantes):
        realizado = round(realizado_por_cat.get(cat, 0.0), 2)
        realizado_total += realizado

        if mes:
            valor_mensal = mensais.get((cat, mes))
            if valor_mensal is not None:
                orcado, origem = valor_mensal, "MENSAL"
            elif cat in anuais:
                orcado, origem = round(anuais[cat] / 12, 2), "ANUAL_PRORRATEADO"
            else:
                orcado, origem = None, None
        else:
            soma_mensal = sum(v for (c, _m), v in mensais.items() if c == cat)
            if cat in anuais:
                orcado, origem = anuais[cat], "ANUAL"
            elif soma_mensal:
                orcado, origem = round(soma_mensal, 2), "MENSAL"
            else:
                orcado, origem = None, None

        if orcado is not None:
            orcado_total += orcado
            desvio = round(realizado - orcado, 2)
            desvio_pct = round((desvio / orcado) * 100, 1) if orcado else None
        else:
            desvio = None
            desvio_pct = None

        linhas.append({
            "categoria_id": cat,
            "orcado": orcado,
            "realizado": realizado,
            "desvio": desvio,
            "desvio_pct": desvio_pct,
            "origem_orcamento": origem,
        })

    return {
        "ano": ano,
        "mes": mes,
        "categorias": linhas,
        "orcado_total": round(orcado_total, 2),
        "realizado_total": round(realizado_total, 2),
    }
