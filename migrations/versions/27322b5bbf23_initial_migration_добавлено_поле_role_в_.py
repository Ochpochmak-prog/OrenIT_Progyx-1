"""Initial migration: добавлено поле role в модель User

Revision ID: 27322b5bbf23
Revises: 
Create Date: 2025-02-15 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии, используемые Alembic
revision = '27322b5bbf23'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Добавляем столбец 'role' с server_default='user'
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('role', sa.String(length=20), nullable=False, server_default='user')
        )
    # Если вы не хотите, чтобы в будущем для новых вставок использовался server_default,
    # можно сразу удалить его (опционально):
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('role', server_default=None)

def downgrade():
    # При откате удаления столбца 'role'
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('role')
