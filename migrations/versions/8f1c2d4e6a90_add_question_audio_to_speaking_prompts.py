"""add question_audio to speaking_prompts

Revision ID: 8f1c2d4e6a90
Revises: 360ebd76b012
Create Date: 2026-11-26 17:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f1c2d4e6a90'
down_revision = '360ebd76b012'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('speaking_prompts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('question_audio', sa.LargeBinary(), nullable=True))


def downgrade():
    with op.batch_alter_table('speaking_prompts', schema=None) as batch_op:
        batch_op.drop_column('question_audio')
