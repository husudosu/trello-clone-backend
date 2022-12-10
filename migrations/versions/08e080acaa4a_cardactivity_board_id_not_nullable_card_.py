"""CardActivity board_id not nullable, card_id nullable

Revision ID: 08e080acaa4a
Revises: 11769a2dc303
Create Date: 2022-12-10 10:16:36.394804

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08e080acaa4a'
down_revision = '11769a2dc303'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card_activity', schema=None) as batch_op:
        batch_op.alter_column('board_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('card_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card_activity', schema=None) as batch_op:
        batch_op.alter_column('card_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('board_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###
