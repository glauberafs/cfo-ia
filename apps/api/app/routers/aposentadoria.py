from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.aposentadoria_service import projetar, upsert_perfil
from ..db import get_db
from ..models import PerfilAposentadoria, Usuario
from ..schemas import PerfilAposentadoriaCriar, PerfilAposentadoriaOut, ProjecaoAposentadoria
from ..security import get_current_user

router = APIRouter(prefix="/aposentadoria", tags=["aposentadoria"])


@router.put("/perfil", response_model=PerfilAposentadoriaOut)
def definir_perfil(
    dados: PerfilAposentadoriaCriar,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return upsert_perfil(db, usuario, dados.model_dump())


@router.get("/perfil", response_model=PerfilAposentadoriaOut)
def obter_perfil(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    perfil = db.query(PerfilAposentadoria).filter(PerfilAposentadoria.usuario_id == usuario.id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil ainda nao cadastrado. Use PUT /aposentadoria/perfil.")
    return perfil


@router.get("/projecao", response_model=ProjecaoAposentadoria)
def obter_projecao(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    perfil = db.query(PerfilAposentadoria).filter(PerfilAposentadoria.usuario_id == usuario.id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil ainda nao cadastrado. Use PUT /aposentadoria/perfil.")
    return projetar(db, usuario, perfil)
