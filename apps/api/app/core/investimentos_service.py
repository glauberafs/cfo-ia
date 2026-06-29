"""Analise de investimentos: rentabilidade dos ativos manuais (categoria
'investimento') comparando o que foi efetivamente aportado/retirado com o
valor atual. A Pluggy pessoal nao traz posicao de carteira, so movimentacao
(eventos APLICACAO/RESGATE) -- por isso a rentabilidade real vem do
patrimonio manual, e so contamos quantos eventos desse tipo existem como
sinal de que ha investimento acontecendo fora do que foi cadastrado a mao.
"""
from sqlalchemy.orm import Session

from ..models import Evento, Natureza, Usuario
from . import patrimonio_service


def resumo(db: Session, usuario: Usuario) -> dict:
    ativos_investimento = [a for a in patrimonio_service.listar_ativos(db, usuario) if a.categoria == "investimento"]

    detalhes = []
    total_atual = 0.0
    total_aportado_liquido = 0.0

    for ativo in ativos_investimento:
        movs = patrimonio_service.listar_movimentos(db, usuario, ativo.id)
        aportado_liquido = round(sum(m.valor for m in movs if m.tipo in ("APORTE", "RETIRADA")), 2)
        rentabilidade_rs = round(ativo.valor_atual - aportado_liquido, 2)
        rentabilidade_pct = round((rentabilidade_rs / aportado_liquido) * 100, 1) if aportado_liquido else None

        detalhes.append({
            "ativo_id": ativo.id,
            "nome": ativo.nome,
            "valor_atual": round(ativo.valor_atual, 2),
            "total_aportado_liquido": aportado_liquido,
            "rentabilidade_rs": rentabilidade_rs,
            "rentabilidade_pct": rentabilidade_pct,
        })
        total_atual += ativo.valor_atual
        total_aportado_liquido += aportado_liquido

    eventos_movimentacao = (
        db.query(Evento)
        .filter(Evento.usuario_id == usuario.id, Evento.natureza.in_([Natureza.APLICACAO, Natureza.RESGATE]))
        .count()
    )

    rentabilidade_rs_total = round(total_atual - total_aportado_liquido, 2)
    return {
        "total_investido_atual": round(total_atual, 2),
        "total_aportado_liquido": round(total_aportado_liquido, 2),
        "rentabilidade_rs_total": rentabilidade_rs_total,
        "rentabilidade_pct_total": (
            round((rentabilidade_rs_total / total_aportado_liquido) * 100, 1) if total_aportado_liquido else None
        ),
        "ativos": detalhes,
        "eventos_movimentacao_detectados": eventos_movimentacao,
    }
