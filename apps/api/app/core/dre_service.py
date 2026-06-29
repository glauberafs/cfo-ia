"""DRE (Demonstracao de Resultado) por periodo, com comparativos MoM/YoY e
acumulado do ano (YTD) x mesmo periodo do ano anterior.
"""
import calendar
from datetime import date

from sqlalchemy.orm import Session

from ..models import Evento, Status, Usuario


def _periodo_mes(ano: int, mes: int) -> tuple[date, date]:
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, 1), date(ano, mes, ultimo_dia)


def _mes_anterior(ano: int, mes: int) -> tuple[int, int]:
    return (ano - 1, 12) if mes == 1 else (ano, mes - 1)


def _resumo(db: Session, usuario_id: str, data_ini: date, data_fim: date) -> dict:
    eventos = (
        db.query(Evento)
        .filter(
            Evento.usuario_id == usuario_id,
            Evento.status == Status.REALIZADO,
            Evento.afeta_patrimonio.is_(True),
            Evento.data >= data_ini.isoformat(),
            Evento.data <= data_fim.isoformat(),
        )
        .all()
    )
    receitas = round(sum(e.valor for e in eventos if e.valor > 0), 2)
    despesas = round(sum(e.valor for e in eventos if e.valor < 0), 2)
    por_categoria: dict[str, float] = {}
    for e in eventos:
        if e.valor < 0:
            por_categoria[e.categoria_id] = round(por_categoria.get(e.categoria_id, 0.0) + e.valor, 2)
    return {
        "receitas": receitas,
        "despesas": despesas,
        "resultado": round(receitas + despesas, 2),
        "por_categoria": por_categoria,
    }


def dre(db: Session, usuario: Usuario, ano: int, mes: int | None) -> dict:
    if mes:
        ini, fim = _periodo_mes(ano, mes)
        atual = _resumo(db, usuario.id, ini, fim)

        ano_ant, mes_ant = _mes_anterior(ano, mes)
        ini_ant, fim_ant = _periodo_mes(ano_ant, mes_ant)
        periodo_anterior = _resumo(db, usuario.id, ini_ant, fim_ant)

        ini_yoy, fim_yoy = _periodo_mes(ano - 1, mes)
        mesmo_periodo_ano_anterior = _resumo(db, usuario.id, ini_yoy, fim_yoy)

        acumulado_ano_atual = _resumo(db, usuario.id, date(ano, 1, 1), fim)
        acumulado_ano_anterior = _resumo(db, usuario.id, date(ano - 1, 1, 1), fim_yoy)
    else:
        ini, fim = date(ano, 1, 1), date(ano, 12, 31)
        atual = _resumo(db, usuario.id, ini, fim)
        periodo_anterior = None
        mesmo_periodo_ano_anterior = _resumo(db, usuario.id, date(ano - 1, 1, 1), date(ano - 1, 12, 31))
        acumulado_ano_atual = atual
        acumulado_ano_anterior = mesmo_periodo_ano_anterior

    return {
        "ano": ano,
        "mes": mes,
        "atual": atual,
        "periodo_anterior": periodo_anterior,
        "mesmo_periodo_ano_anterior": mesmo_periodo_ano_anterior,
        "acumulado_ano_atual": acumulado_ano_atual,
        "acumulado_ano_anterior": acumulado_ano_anterior,
    }
