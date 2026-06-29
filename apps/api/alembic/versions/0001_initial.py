"""schema inicial multiusuario

Revision ID: 0001
Revises:
Create Date: 2026-06-29
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False, server_default=""),
        sa.Column("senha_hash", sa.String(), nullable=False),
        sa.Column("apelidos_proprios", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "conexoes_pluggy",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("instituicao", sa.String(), server_default=""),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_conexoes_pluggy_usuario_id", "conexoes_pluggy", ["usuario_id"])

    op.create_table(
        "contas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("pluggy_account_id", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), server_default=""),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("instituicao", sa.String(), server_default=""),
        sa.Column("saldo", sa.Float(), server_default="0"),
        sa.Column("moeda", sa.String(), server_default="BRL"),
    )
    op.create_index("ix_contas_usuario_id", "contas", ["usuario_id"])

    op.create_table(
        "transacoes_brutas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("pluggy_transaction_id", sa.String(), server_default=""),
        sa.Column("hash", sa.String(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("importado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_transacoes_brutas_usuario_id", "transacoes_brutas", ["usuario_id"])
    op.create_index("ix_transacoes_brutas_hash", "transacoes_brutas", ["hash"], unique=True)

    op.create_table(
        "eventos",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("transacao_bruta_id", sa.String(), sa.ForeignKey("transacoes_brutas.id"), nullable=False),
        sa.Column("conta_id", sa.String(), sa.ForeignKey("contas.id"), nullable=False),
        sa.Column("data", sa.String(), nullable=False),
        sa.Column("descricao", sa.Text(), server_default=""),
        sa.Column("descricao_raw", sa.Text(), server_default=""),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("natureza", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("categoria_id", sa.String(), server_default="nao_classificado"),
        sa.Column("categoria_fonte", sa.String(), server_default="REGRA"),
        sa.Column("categoria_confianca", sa.Float(), nullable=True),
        sa.Column("afeta_patrimonio", sa.Boolean(), server_default=sa.true()),
        sa.Column("contraparte", sa.String(), nullable=True),
        sa.Column("parcela_numero", sa.Integer(), nullable=True),
        sa.Column("parcela_total", sa.Integer(), nullable=True),
        sa.Column("tags", postgresql.JSONB(), server_default="[]"),
    )
    op.create_index("ix_eventos_usuario_id", "eventos", ["usuario_id"])
    op.create_index("ix_eventos_conta_id", "eventos", ["conta_id"])

    op.create_table(
        "memoria_categoria",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("chave", sa.String(), nullable=False),
        sa.Column("categoria_id", sa.String(), nullable=False),
        sa.UniqueConstraint("usuario_id", "chave", name="uq_memoria_usuario_chave"),
    )
    op.create_index("ix_memoria_categoria_usuario_id", "memoria_categoria", ["usuario_id"])


def downgrade() -> None:
    op.drop_table("memoria_categoria")
    op.drop_table("eventos")
    op.drop_table("transacoes_brutas")
    op.drop_table("contas")
    op.drop_table("conexoes_pluggy")
    op.drop_table("usuarios")
