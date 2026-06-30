"""Orquestra o pipeline de sincronizacao: Pluggy/demo -> normalizar -> salvar.

Corrige o problema conhecido #4 (memoria de categoria so era reaplicada
manualmente no dashboard): aqui a memoria e aplicada automaticamente em todo
evento novo, dentro do proprio sync.
"""
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Conta, Evento, MemoriaCategoria, TipoConta, TransacaoBruta, Usuario
from .models_const import NEUTRAS_CATEGORIA
from .normalize import chave_memoria, hash_transacao, normalizar
from .pluggy_client import PluggyClient


def _tipo_conta(pluggy_type: str) -> str:
    return TipoConta.CARTAO if pluggy_type == "CREDIT" else TipoConta.CONTA


def _memoria_do_usuario(db: Session, usuario_id: str) -> dict[str, str]:
    rows = db.query(MemoriaCategoria).filter(MemoriaCategoria.usuario_id == usuario_id).all()
    return {r.chave: r.categoria_id for r in rows}


def _processar_transacoes(db: Session, conta: Conta, transacoes: list, usuario: Usuario) -> int:
    memoria = _memoria_do_usuario(db, usuario.id)
    novos = 0
    for t in transacoes:
        h = hash_transacao(t, conta.id)
        if db.query(TransacaoBruta).filter(TransacaoBruta.hash == h).first():
            continue  # dedup

        bruta = TransacaoBruta(
            usuario_id=usuario.id,
            pluggy_transaction_id=t.get("id", ""),
            hash=h,
            payload_json=t,
        )
        db.add(bruta)
        db.flush()

        dados_evento = normalizar(t, conta, bruta.id, usuario.apelidos_proprios)

        # memoria automatica: se o usuario ja classificou esse estabelecimento antes,
        # reaplica direto, sem precisar passar pelo "nao_classificado" de novo.
        chave = chave_memoria(dados_evento["descricao"])
        if chave in memoria:
            dados_evento["categoria_id"] = memoria[chave]
            dados_evento["categoria_fonte"] = "USUARIO"
            dados_evento["categoria_confianca"] = 1.0
            dados_evento["afeta_patrimonio"] = memoria[chave] not in NEUTRAS_CATEGORIA

        db.add(Evento(**dados_evento))
        novos += 1
    db.commit()
    return novos


def sincronizar_pluggy(db: Session, usuario: Usuario, item_id: str) -> int:
    client = PluggyClient(settings.pluggy_client_id, settings.pluggy_client_secret)
    total = 0
    for c in client.listar_contas(item_id):
        conta = (
            db.query(Conta)
            .filter(Conta.usuario_id == usuario.id, Conta.pluggy_account_id == c["id"])
            .first()
        )
        if not conta:
            conta = Conta(
                usuario_id=usuario.id,
                pluggy_account_id=c["id"],
                nome=c.get("name", ""),
                tipo=_tipo_conta(c.get("type", "BANK")),
                instituicao=c.get("marketingName", ""),
                saldo=c.get("balance", 0.0),
            )
            db.add(conta)
        else:
            conta.saldo = c.get("balance", conta.saldo)
        db.flush()
        total += _processar_transacoes(db, conta, client.listar_transacoes(c["id"]), usuario)
    return total


def sincronizar_demo(db: Session, usuario: Usuario, dados: dict) -> int:
    por_id = {c["id"]: c for c in dados["contas"]}
    total = 0
    for acc_id, txs in dados["transacoes"].items():
        c = por_id[acc_id]
        conta = (
            db.query(Conta)
            .filter(Conta.usuario_id == usuario.id, Conta.pluggy_account_id == acc_id)
            .first()
        )
        if not conta:
            conta = Conta(
                usuario_id=usuario.id,
                pluggy_account_id=acc_id,
                nome=c["name"],
                tipo=_tipo_conta(c["type"]),
                instituicao=c["institution"],
                saldo=c["balance"],
            )
            db.add(conta)
            db.flush()
        total += _processar_transacoes(db, conta, txs, usuario)
    return total


def reaplicar_memoria(db: Session, usuario: Usuario) -> int:
    """Aplica a memoria de categoria a TODOS os eventos existentes do usuario."""
    memoria = _memoria_do_usuario(db, usuario.id)
    if not memoria:
        return 0
    n = 0
    eventos = db.query(Evento).filter(Evento.usuario_id == usuario.id).all()
    for ev in eventos:
        cat = memoria.get(chave_memoria(ev.descricao))
        if cat and cat != ev.categoria_id:
            ev.categoria_id = cat
            ev.categoria_fonte = "USUARIO"
            ev.categoria_confianca = 1.0
            ev.afeta_patrimonio = cat not in NEUTRAS_CATEGORIA
            n += 1
    db.commit()
    return n


def classificar_evento(db: Session, usuario: Usuario, evento: Evento, categoria_id: str) -> int:
    """Classifica um evento e grava na memoria; reaplica a todo o historico do usuario."""
    evento.categoria_id = categoria_id
    evento.categoria_fonte = "USUARIO"
    evento.categoria_confianca = 1.0
    # categorias neutras (pagamento de fatura, neutro) nao sao despesa/receita real
    evento.afeta_patrimonio = categoria_id not in NEUTRAS_CATEGORIA

    chave = chave_memoria(evento.descricao)
    if chave:
        mem = (
            db.query(MemoriaCategoria)
            .filter(MemoriaCategoria.usuario_id == usuario.id, MemoriaCategoria.chave == chave)
            .first()
        )
        if mem:
            mem.categoria_id = categoria_id
        else:
            db.add(MemoriaCategoria(usuario_id=usuario.id, chave=chave, categoria_id=categoria_id))
    db.commit()
    return reaplicar_memoria(db, usuario)
