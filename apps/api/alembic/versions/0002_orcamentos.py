"""tabela de orcamentos por categoria

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orcamentos",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("usuario_id", sa.String(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("categoria_id", sa.String(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.UniqueConstraint("usuario_id", "categoria_id", "ano", "mes", name="uq_orcamento_usuario_cat_ano_mes"),
    )
    op.create_index("ix_orcamentos_usuario_id", "orcamentos", ["usuario_id"])


def downgrade() -> None:
    op.drop_table("orcamentos")
