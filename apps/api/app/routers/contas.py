from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Conta, ConexaoPluggy, Usuario
from ..schemas import ConexaoPluggyCriar
from ..security import get_current_user

router = APIRouter(prefix="/contas", tags=["contas"])


@router.get("")
def listar(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    contas = db.query(Conta).filter(Conta.usuario_id == usuario.id).all()
    return [
        {"id": c.id, "nome": c.nome, "tipo": c.tipo, "instituicao": c.instituicao, "saldo": c.saldo}
        for c in contas
    ]


@router.post("/conexoes", status_code=201)
def conectar_pluggy(
    dados: ConexaoPluggyCriar,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra o item_id da conexao Open Finance do usuario (feita no MeuPluggy/widget)."""
    conexao = ConexaoPluggy(usuario_id=usuario.id, item_id=dados.item_id, instituicao=dados.instituicao)
    db.add(conexao)
    db.commit()
    db.refresh(conexao)
    return {"id": conexao.id, "item_id": conexao.item_id, "instituicao": conexao.instituicao}


@router.get("/conexoes")
def listar_conexoes(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    conexoes = db.query(ConexaoPluggy).filter(ConexaoPluggy.usuario_id == usuario.id).all()
    return [{"id": c.id, "item_id": c.item_id, "instituicao": c.instituicao} for c in conexoes]
