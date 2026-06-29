"""perfil de aposentadoria

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "perfis_aposentadoria",
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), primary_key=True),
        sa.Column("idade_atual", sa.Integer(), nullable=False),
        sa.Column("idade_aposentadoria", sa.Integer(), nullable=False),
        sa.Column("renda_desejada_mensal", sa.Float(), nullable=False),
        sa.Column("taxa_retorno_anual_pct", sa.Float(), nullable=False, server_default="4.0"),
        sa.Column("aporte_mensal", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("perfis_aposentadoria")
