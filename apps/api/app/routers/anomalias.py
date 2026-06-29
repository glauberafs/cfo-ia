from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.anomalias_service import detectar
from ..db import get_db
from ..models import Usuario
from ..schemas import AnomaliaOut
from ..security import get_current_user

router = APIRouter(prefix="/anomalias", tags=["anomalias"])


@router.get("", response_model=list[AnomaliaOut])
def listar(
    ano: int | None = None,
    mes: int | None = None,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compara o gasto por categoria do mes com a media dos 3 meses anteriores."""
    return detectar(db, usuario, ano, mes)
