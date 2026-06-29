from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.alertas_service import listar_alertas
from ..db import get_db
from ..models import Usuario
from ..schemas import AlertaOut
from ..security import get_current_user

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("", response_model=list[AlertaOut])
def listar(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Tendencia de fechar o mes acima do orcado (run-rate) + projecao de saldo negativo."""
    return listar_alertas(db, usuario)
