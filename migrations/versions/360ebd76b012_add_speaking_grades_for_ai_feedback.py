"""add speaking_grades for AI speaking feedback

Revision ID: 360ebd76b012
Revises: 64e4c132d761
Create Date: 2026-11-26 16:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '360ebd76b012'
down_revision = '64e4c132d761'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('speaking_grades',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('prompt_id', sa.Integer(), nullable=False),
    sa.Column('transcript', sa.Text(), nullable=False),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('feedback', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['prompt_id'], ['speaking_prompts.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('speaking_grades', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_speaking_grades_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_speaking_grades_user_id'), ['user_id'], unique=False)


def downgrade():
    with op.batch_alter_table('speaking_grades', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_speaking_grades_user_id'))
        batch_op.drop_index(batch_op.f('ix_speaking_grades_created_at'))

    op.drop_table('speaking_grades')
