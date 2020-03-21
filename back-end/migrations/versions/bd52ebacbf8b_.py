"""empty message

Revision ID: bd52ebacbf8b
Revises: bff55cfe6d54
Create Date: 2020-03-20 15:15:05.037303

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd52ebacbf8b'
down_revision = 'bff55cfe6d54'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('payload_json', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.Float(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_timestamp'), 'notifications', ['timestamp'], unique=False)
    op.add_column('users', sa.Column('last_followeds_posts_read_time', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_follows_read_time', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_likes_read_time', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_recived_comments_read_time', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'last_recived_comments_read_time')
    op.drop_column('users', 'last_likes_read_time')
    op.drop_column('users', 'last_follows_read_time')
    op.drop_column('users', 'last_followeds_posts_read_time')
    op.drop_index(op.f('ix_notifications_timestamp'), table_name='notifications')
    op.drop_table('notifications')
    # ### end Alembic commands ###
