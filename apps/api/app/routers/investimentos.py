from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.investimentos_service import resumo as resumo_service
from ..db import get_db
from ..models import Usuario
from ..schemas import ResumoInvestimentos
from ..security import get_current_user

router = APIRouter(prefix="/investimentos", tags=["investimentos"])


@router.get("/resumo", response_model=ResumoInvestimentos)
def resumo(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rentabilidade dos ativos manuais de categoria 'investimento' (aportado x valor atual)."""
    return resumo_service(db, usuario)
