from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core import patrimonio_service
from ..db import get_db
from ..models import AtivoPatrimonio, Usuario
from ..schemas import AtivoCriar, AtivoOut, MovimentoCriar, MovimentoOut, ResumoPatrimonio
from ..security import get_current_user

router = APIRouter(prefix="/patrimonio", tags=["patrimonio"])


@router.get("/resumo", response_model=ResumoPatrimonio)
def resumo(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return patrimonio_service.resumo(db, usuario)


@router.post("/ativos", response_model=AtivoOut, status_code=201)
def criar_ativo(
    dados: AtivoCriar,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cadastra um ativo de patrimonio manual (investimento, imovel etc), com valor inicial opcional."""
    return patrimonio_service.criar_ativo(db, usuario, dados.nome, dados.categoria, dados.valor_inicial)


@router.get("/ativos", response_model=list[AtivoOut])
def listar_ativos(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return patrimonio_service.listar_ativos(db, usuario)


@router.delete("/ativos/{ativo_id}", status_code=204)
def remover_ativo(ativo_id: str, usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if not patrimonio_service.remover_ativo(db, usuario, ativo_id):
        raise HTTPException(status_code=404, detail="Ativo nao encontrado")


def _buscar_ativo(db: Session, usuario: Usuario, ativo_id: str) -> AtivoPatrimonio:
    ativo = (
        db.query(AtivoPatrimonio)
        .filter(AtivoPatrimonio.id == ativo_id, AtivoPatrimonio.usuario_id == usuario.id)
        .first()
    )
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo nao encontrado")
    return ativo


@router.post("/ativos/{ativo_id}/movimentos", response_model=AtivoOut)
def registrar_movimento(
    ativo_id: str,
    dados: MovimentoCriar,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra aporte, retirada ou ajuste direto de valor (ex: rentabilidade do mes)."""
    ativo = _buscar_ativo(db, usuario, ativo_id)
    if dados.tipo not in ("APORTE", "RETIRADA", "AJUSTE_VALOR"):
        raise HTTPException(status_code=422, detail="tipo deve ser APORTE, RETIRADA ou AJUSTE_VALOR")
    return patrimonio_service.registrar_movimento(db, usuario, ativo, dados.tipo, dados.valor, dados.data, dados.observacao)


@router.get("/ativos/{ativo_id}/movimentos", response_model=list[MovimentoOut])
def listar_movimentos(ativo_id: str, usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    _buscar_ativo(db, usuario, ativo_id)
    return patrimonio_service.listar_movimentos(db, usuario, ativo_id)
