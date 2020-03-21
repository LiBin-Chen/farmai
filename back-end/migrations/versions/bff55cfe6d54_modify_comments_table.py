"""modify comments table

Revision ID: bff55cfe6d54
Revises: 6a63185558d6
Create Date: 2020-03-20 10:10:01.423190

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bff55cfe6d54'
down_revision = '6a63185558d6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comment_likes',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('comment', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['comment'], ['comments.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('comment_likes')
    # ### end Alembic commands ###