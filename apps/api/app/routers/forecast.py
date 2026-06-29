from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.forecast_service import projetar_fatura, projetar_saldo
from ..db import get_db
from ..models import Usuario
from ..schemas import ForecastFaturaConta, ForecastSaldoConta
from ..security import get_current_user

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/saldo", response_model=list[ForecastSaldoConta])
def saldo(
    dias: int = 30,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Projeta o saldo de cada conta bancaria com base nos eventos PREVISTO conhecidos."""
    return projetar_saldo(db, usuario, dias)


@router.get("/fatura", response_model=list[ForecastFaturaConta])
def fatura(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fatura do mes atual de cada cartao: compras realizadas + parcelas previstas."""
    return projetar_fatura(db, usuario)
