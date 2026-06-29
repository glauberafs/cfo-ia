"""patrimonio manual: ativos e movimentos

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ativos_patrimonio",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("categoria", sa.String(), nullable=False, server_default="outro"),
        sa.Column("valor_atual", sa.Float(), nullable=False, server_default="0"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ativos_patrimonio_usuario_id", "ativos_patrimonio", ["usuario_id"])

    op.create_table(
        "movimentos_patrimonio",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("ativo_id", sa.String(), sa.ForeignKey("ativos_patrimonio.id"), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("data", sa.String(), nullable=False),
        sa.Column("observacao", sa.String(), nullable=False, server_default=""),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_movimentos_patrimonio_usuario_id", "movimentos_patrimonio", ["usuario_id"])
    op.create_index("ix_movimentos_patrimonio_ativo_id", "movimentos_patrimonio", ["ativo_id"])


def downgrade() -> None:
    op.drop_table("movimentos_patrimonio")
    op.drop_table("ativos_patrimonio")
