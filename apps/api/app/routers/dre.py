from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.dre_service import dre as dre_service
from ..db import get_db
from ..models import Usuario
from ..schemas import DREResponse
from ..security import get_current_user

router = APIRouter(prefix="/dre", tags=["dre"])


@router.get("", response_model=DREResponse)
def obter_dre(
    ano: int,
    mes: int | None = None,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """DRE do periodo com comparativo vs mes anterior, mesmo mes do ano anterior,
    e acumulado do ano (YTD) vs mesmo YTD do ano anterior. Sem 'mes', compara o ano inteiro."""
    return dre_service(db, usuario, ano, mes)
