from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.sync_service import classificar_evento as classificar_evento_service
from ..db import get_db
from ..models import Evento, Usuario
from ..schemas import ClassificarEvento, EventoOut
from ..security import get_current_user

router = APIRouter(prefix="/eventos", tags=["eventos"])


@router.get("", response_model=list[EventoOut])
def listar(
    categoria: str | None = None,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Evento).filter(Evento.usuario_id == usuario.id)
    if categoria:
        q = q.filter(Evento.categoria_id == categoria)
    return q.order_by(Evento.data).all()


@router.patch("/{evento_id}/categoria")
def classificar(
    evento_id: str,
    dados: ClassificarEvento,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evento = db.query(Evento).filter(Evento.id == evento_id, Evento.usuario_id == usuario.id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento nao encontrado")
    n = classificar_evento_service(db, usuario, evento, dados.categoria_id)
    return {"ok": True, "eventos_atualizados_pela_memoria": n}
