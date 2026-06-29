from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Evento, Status, Usuario
from ..schemas import ResumoDashboard
from ..security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/resumo", response_model=ResumoDashboard)
def resumo(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    eventos = db.query(Evento).filter(Evento.usuario_id == usuario.id).all()

    realizados_patrimonio = [e for e in eventos if e.status == Status.REALIZADO and e.afeta_patrimonio]
    receitas = sum(e.valor for e in realizados_patrimonio if e.valor > 0)
    gastos = sum(e.valor for e in realizados_patrimonio if e.valor < 0)
    previstos = sum(e.valor for e in eventos if e.status == Status.PREVISTO)

    gasto_por_categoria: dict[str, float] = {}
    for e in realizados_patrimonio:
        if e.valor < 0:
            gasto_por_categoria[e.categoria_id] = gasto_por_categoria.get(e.categoria_id, 0.0) + e.valor

    return ResumoDashboard(
        receitas=round(receitas, 2),
        gastos=round(gastos, 2),
        resultado=round(receitas + gastos, 2),
        obrigacoes_futuras=round(previstos, 2),
        gasto_por_categoria={k: round(v, 2) for k, v in gasto_por_categoria.items()},
    )
