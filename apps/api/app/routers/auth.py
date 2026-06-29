from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Usuario
from ..schemas import Token, UsuarioCriar, UsuarioLogin, UsuarioOut
from ..security import criar_access_token, hash_senha, verificar_senha

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar(dados: UsuarioCriar, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(status_code=400, detail="Email ja cadastrado")
    usuario = Usuario(
        email=dados.email,
        nome=dados.nome,
        senha_hash=hash_senha(dados.senha),
        apelidos_proprios=dados.apelidos_proprios,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha invalidos")
    return Token(access_token=criar_access_token(usuario.id))
