"""quitar precio_referencia

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-22 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('precio_referencia')


def downgrade() -> None:
    op.create_table('precio_referencia',
    sa.Column('municipio', sa.String(length=128), nullable=False),
    sa.Column('mediana_eur_m2', sa.Float(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('municipio')
    )
