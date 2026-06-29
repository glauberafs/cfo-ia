"""Patrimonio manual: ativos que o usuario cadastra a mao (investimentos,
imoveis etc) -- a Pluggy pessoal so traz movimentacao de conta/cartao, nao
posicao de carteira. Cada ativo tem um valor atual editavel a qualquer
momento (aporte, retirada ou ajuste direto de valor), com historico.
"""
from datetime import date

from sqlalchemy.orm import Session

from ..models import AtivoPatrimonio, Conta, MovimentoPatrimonio, Usuario


def criar_ativo(db: Session, usuario: Usuario, nome: str, categoria: str, valor_inicial: float) -> AtivoPatrimonio:
    ativo = AtivoPatrimonio(usuario_id=usuario.id, nome=nome, categoria=categoria, valor_atual=valor_inicial)
    db.add(ativo)
    db.commit()
    db.refresh(ativo)
    if valor_inicial:
        db.add(MovimentoPatrimonio(
            usuario_id=usuario.id, ativo_id=ativo.id, tipo="APORTE",
            valor=valor_inicial, data=date.today().isoformat(), observacao="Valor inicial do cadastro",
        ))
        db.commit()
    return ativo


def listar_ativos(db: Session, usuario: Usuario) -> list[AtivoPatrimonio]:
    return db.query(AtivoPatrimonio).filter(AtivoPatrimonio.usuario_id == usuario.id).order_by(AtivoPatrimonio.nome).all()


def remover_ativo(db: Session, usuario: Usuario, ativo_id: str) -> bool:
    ativo = (
        db.query(AtivoPatrimonio)
        .filter(AtivoPatrimonio.id == ativo_id, AtivoPatrimonio.usuario_id == usuario.id)
        .first()
    )
    if not ativo:
        return False
    db.delete(ativo)
    db.commit()
    return True


def registrar_movimento(
    db: Session, usuario: Usuario, ativo: AtivoPatrimonio, tipo: str, valor: float, data_mov: str | None, observacao: str
) -> AtivoPatrimonio:
    data_mov = data_mov or date.today().isoformat()

    if tipo == "APORTE":
        ativo.valor_atual += valor
        valor_registrado = valor
    elif tipo == "RETIRADA":
        ativo.valor_atual -= valor
        valor_registrado = -valor
    elif tipo == "AJUSTE_VALOR":
        valor_registrado = valor - ativo.valor_atual
        ativo.valor_atual = valor
    else:
        raise ValueError(f"tipo de movimento invalido: {tipo}")

    db.add(MovimentoPatrimonio(
        usuario_id=usuario.id, ativo_id=ativo.id, tipo=tipo,
        valor=valor_registrado, data=data_mov, observacao=observacao,
    ))
    db.commit()
    db.refresh(ativo)
    return ativo


def listar_movimentos(db: Session, usuario: Usuario, ativo_id: str) -> list[MovimentoPatrimonio]:
    return (
        db.query(MovimentoPatrimonio)
        .filter(MovimentoPatrimonio.usuario_id == usuario.id, MovimentoPatrimonio.ativo_id == ativo_id)
        .order_by(MovimentoPatrimonio.data.desc(), MovimentoPatrimonio.criado_em.desc())
        .all()
    )


def resumo(db: Session, usuario: Usuario) -> dict:
    contas = round(sum(c.saldo for c in db.query(Conta).filter(Conta.usuario_id == usuario.id).all()), 2)
    ativos_manuais = round(sum(a.valor_atual for a in listar_ativos(db, usuario)), 2)
    return {"contas": contas, "ativos_manuais": ativos_manuais, "total": round(contas + ativos_manuais, 2)}
