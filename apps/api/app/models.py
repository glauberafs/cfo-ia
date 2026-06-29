"""Modelos ORM (multiusuario). Espelham a spec do Evento Financeiro v1.0."""
import uuid

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .db import Base
from .core.models_const import Natureza, Status, TipoConta, NEUTRAS_PATRIMONIO  # noqa: F401  (re-exportado)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    nome = Column(String, nullable=False, default="")
    senha_hash = Column(String, nullable=False)
    # nomes/CPFs que identificam o proprio usuario, usados para distinguir
    # transferencia entre contas proprias (neutra) de transferencia a terceiro.
    apelidos_proprios = Column(JSONB, nullable=False, default=list)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    contas = relationship("Conta", back_populates="usuario", cascade="all, delete-orphan")
    conexoes = relationship("ConexaoPluggy", back_populates="usuario", cascade="all, delete-orphan")


class ConexaoPluggy(Base):
    """Uma conexao Open Finance (item) de um usuario com uma instituicao."""
    __tablename__ = "conexoes_pluggy"

    id = Column(String, primary_key=True, default=gen_uuid)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False, index=True)
    item_id = Column(String, nullable=False)
    instituicao = Column(String, default="")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="conexoes")


class Conta(Base):
    __tablename__ = "contas"

    id = Column(String, primary_key=True, default=gen_uuid)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False, index=True)
    pluggy_account_id = Column(String, nullable=False)
    nome = Column(String, default="")
    tipo = Column(String, nullable=False)
    instituicao = Column(String, default="")
    saldo = Column(Float, default=0.0)
    moeda = Column(String, default="BRL")

    usuario = relationship("Usuario", back_populates="contas")
    eventos = relationship("Evento", back_populates="conta", cascade="all, delete-orphan")


class TransacaoBruta(Base):
    __tablename__ = "transacoes_brutas"

    id = Column(String, primary_key=True, default=gen_uuid)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False, index=True)
    pluggy_transaction_id = Column(String, default="")
    hash = Column(String, unique=True, nullable=False, index=True)
    payload_json = Column(JSONB, nullable=False)
    importado_em = Column(DateTime(timezone=True), server_default=func.now())


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(String, primary_key=True, default=gen_uuid)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False, index=True)
    transacao_bruta_id = Column(String, ForeignKey("transacoes_brutas.id"), nullable=False)
    conta_id = Column(String, ForeignKey("contas.id"), nullable=False, index=True)
    data = Column(String, nullable=False)
    descricao = Column(Text, default="")
    descricao_raw = Column(Text, default="")
    valor = Column(Float, nullable=False)
    natureza = Column(String, nullable=False)
    status = Column(String, nullable=False)
    categoria_id = Column(String, default="nao_classificado")
    categoria_fonte = Column(String, default="REGRA")
    categoria_confianca = Column(Float, nullable=True)
    afeta_patrimonio = Column(Boolean, default=True)
    contraparte = Column(String, nullable=True)
    parcela_numero = Column(Integer, nullable=True)
    parcela_total = Column(Integer, nullable=True)
    tags = Column(JSONB, default=list)

    conta = relationship("Conta", back_populates="eventos")


class MemoriaCategoria(Base):
    """Aprendizado: chave normalizada da descricao -> categoria escolhida pelo usuario."""
    __tablename__ = "memoria_categoria"

    id = Column(String, primary_key=True, default=gen_uuid)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False, index=True)
    chave = Column(String, nullable=False)
    categoria_id = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("usuario_id", "chave", name="uq_memoria_usuario_chave"),)


class Orcamento(Base):
    """Limite de gasto por categoria. mes=0 representa orcamento ANUAL daquele ano
    (usado como fallback /12 quando nao ha orcamento mensal especifico)."""
    __tablename__ = "orcamentos"

    id = Column(String, primary_key=True, default=gen_uuid)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False, index=True)
    categoria_id = Column(String, nullable=False)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False, default=0)  # 0 = anual, 1-12 = mensal
    valor = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("usuario_id", "categoria_id", "ano", "mes", name="uq_orcamento_usuario_cat_ano_mes"),
    )


class PerfilAposentadoria(Base):
    """Parametros de planejamento de longo prazo, um por usuario."""
    __tablename__ = "perfis_aposentadoria"

    usuario_id = Column(String, ForeignKey("usuarios.id"), primary_key=True)
    idade_atual = Column(Integer, nullable=False)
    idade_aposentadoria = Column(Integer, nullable=False)
    renda_desejada_mensal = Column(Float, nullable=False)
    taxa_retorno_anual_pct = Column(Float, nullable=False, default=4.0)  # real, acima da inflacao
    aporte_mensal = Column(Float, nullable=False, default=0.0)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AtivoPatrimonio(Base):
    """Patrimonio cadastrado manualmente (investimentos, imoveis etc) -- nao
    capturado automaticamente via Pluggy. Soma-se ao saldo das contas para
    compor o patrimonio total usado na projecao de aposentadoria."""
    __tablename__ = "ativos_patrimonio"

    id = Column(String, primary_key=True, default=gen_uuid)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False, index=True)
    nome = Column(String, nullable=False)
    categoria = Column(String, nullable=False, default="outro")  # investimento | imovel | outro
    valor_atual = Column(Float, nullable=False, default=0.0)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    movimentos = relationship("MovimentoPatrimonio", back_populates="ativo", cascade="all, delete-orphan")


class MovimentoPatrimonio(Base):
    """Historico de aportes, retiradas e ajustes de valor de um ativo."""
    __tablename__ = "movimentos_patrimonio"

    id = Column(String, primary_key=True, default=gen_uuid)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=False, index=True)
    ativo_id = Column(String, ForeignKey("ativos_patrimonio.id"), nullable=False, index=True)
    tipo = Column(String, nullable=False)  # APORTE | RETIRADA | AJUSTE_VALOR
    valor = Column(Float, nullable=False)
    data = Column(String, nullable=False)
    observacao = Column(String, nullable=False, default="")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    ativo = relationship("AtivoPatrimonio", back_populates="movimentos")
