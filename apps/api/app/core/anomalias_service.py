"""Deteccao de anomalias: compara o gasto do mes por categoria com a media
dos 3 meses anteriores. So aponta anomalia se a categoria tiver historico
(senao nao ha base de comparacao) e um piso minimo (evita ruido em categorias
pequenas onde uma variacao de R$10 parece "100% acima da media")."""
from datetime import date

from sqlalchemy.orm import Session

from ..models import Usuario
from .dre_service import _mes_anterior, _periodo_mes, _resumo


def detectar(
    db: Session, usuario: Usuario, ano: int | None = None, mes: int | None = None,
    limiar_pct: float = 40.0, minimo_historico: float = 50.0, meses_historico: int = 3,
) -> list[dict]:
    hoje = date.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    ini, fim = _periodo_mes(ano, mes)
    atual = _resumo(db, usuario.id, ini, fim)["por_categoria"]

    historico: dict[str, list[float]] = {}
    a, m = ano, mes
    for _ in range(meses_historico):
        a, m = _mes_anterior(a, m)
        ini_h, fim_h = _periodo_mes(a, m)
        for cat, valor in _resumo(db, usuario.id, ini_h, fim_h)["por_categoria"].items():
            historico.setdefault(cat, []).append(abs(valor))

    anomalias = []
    for cat, valor_atual in atual.items():
        valores_historicos = historico.get(cat)
        if not valores_historicos:
            continue
        media = sum(valores_historicos) / len(valores_historicos)
        if media < minimo_historico:
            continue
        valor_atual_abs = abs(valor_atual)
        variacao_pct = ((valor_atual_abs - media) / media) * 100
        if variacao_pct >= limiar_pct:
            anomalias.append({
                "categoria_id": cat,
                "valor_atual": round(valor_atual_abs, 2),
                "media_historica": round(media, 2),
                "variacao_pct": round(variacao_pct, 1),
                "mensagem": (
                    f"Gasto em '{cat}' este mes (R$ {valor_atual_abs:,.2f}) esta "
                    f"{variacao_pct:.0f}% acima da media dos ultimos {len(valores_historicos)} "
                    f"meses (R$ {media:,.2f})."
                ),
            })

    return sorted(anomalias, key=lambda a: -a["variacao_pct"])
