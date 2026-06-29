from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.orcamento_service import comparativo as comparativo_service
from ..core.orcamento_service import listar_orcamentos, upsert_orcamento
from ..db import get_db
from ..models import Usuario
from ..schemas import ComparativoResumo, OrcamentoCriar, OrcamentoOut
from ..security import get_current_user

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])


@router.put("", response_model=OrcamentoOut)
def definir(
    dados: OrcamentoCriar,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria ou atualiza o orcamento de uma categoria (mes=0 para orcamento anual)."""
    return upsert_orcamento(db, usuario, dados.categoria_id, dados.ano, dados.mes, dados.valor)


@router.get("", response_model=list[OrcamentoOut])
def listar(
    ano: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return listar_orcamentos(db, usuario, ano)


@router.get("/comparativo", response_model=ComparativoResumo)
def comparativo(
    ano: int,
    mes: int | None = None,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Real x orcado por categoria. Sem 'mes' compara o ano inteiro; com 'mes', so aquele mes."""
    return comparativo_service(db, usuario, ano, mes)
