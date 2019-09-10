"""empty message

Revision ID: e0fb376ce06f
Revises: 06796c02da24
Create Date: 2019-09-10 22:07:52.084291

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0fb376ce06f'
down_revision = '06796c02da24'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contracts', sa.Column('weekly_hours', sa.Integer(), nullable=True))
    op.drop_column('contracts', 'monthly_hours')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contracts', sa.Column('monthly_hours', sa.INTEGER(), nullable=True))
    op.drop_column('contracts', 'weekly_hours')
    # ### end Alembic commands ###
