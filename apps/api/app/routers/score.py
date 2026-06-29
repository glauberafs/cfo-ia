from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.score_service import calcular
from ..db import get_db
from ..models import Usuario
from ..schemas import ScoreFinanceiro
from ..security import get_current_user

router = APIRouter(prefix="/score", tags=["score"])


@router.get("", response_model=ScoreFinanceiro)
def obter_score(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Indicador composto 0-1000: poupanca, aderencia ao orcamento, saldo futuro e patrimonio."""
    return calcular(db, usuario)
