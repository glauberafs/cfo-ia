import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.sync_service import reaplicar_memoria, sincronizar_demo, sincronizar_pluggy
from ..db import get_db
from ..models import ConexaoPluggy, Usuario
from ..security import get_current_user

router = APIRouter(prefix="/sync", tags=["sync"])

DEMO_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "sample_transactions.json"


@router.post("/demo")
def sync_demo(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Carrega transacoes de exemplo, sem credenciais Pluggy (para validar o pipeline)."""
    with open(DEMO_FIXTURE, encoding="utf-8") as f:
        dados = json.load(f)
    n = sincronizar_demo(db, usuario, dados)
    return {"novos_eventos": n}


@router.post("")
def sync_real(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    conexoes = db.query(ConexaoPluggy).filter(ConexaoPluggy.usuario_id == usuario.id).all()
    if not conexoes:
        raise HTTPException(status_code=400, detail="Nenhuma conexao Pluggy cadastrada. Use /contas/conexoes.")
    total = 0
    for conexao in conexoes:
        total += sincronizar_pluggy(db, usuario, conexao.item_id)
    return {"novos_eventos": total}


@router.post("/reaplicar-memoria")
def reaplicar(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    n = reaplicar_memoria(db, usuario)
    return {"eventos_atualizados": n}
