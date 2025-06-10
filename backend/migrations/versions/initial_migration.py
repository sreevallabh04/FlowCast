"""initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('storage_temp', sa.Float(), nullable=True),
        sa.Column('storage_humidity', sa.Float(), nullable=True),
        sa.Column('shelf_life', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )

    # Create stores table
    op.create_table('stores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lng', sa.Float(), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('store_id')
    )

    # Create inventory table
    op.create_table('inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('store_id', sa.Integer(), nullable=True),
        sa.Column('current_stock', sa.Integer(), nullable=True),
        sa.Column('safety_stock', sa.Integer(), nullable=True),
        sa.Column('reorder_point', sa.Integer(), nullable=True),
        sa.Column('last_restock', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('store_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('transaction_type', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('weather_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('economic_indicators', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create routes table
    op.create_table('routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.String(), nullable=True),
        sa.Column('store_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('distance', sa.Float(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('weather_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('traffic_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('route_polyline', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create webhooks table
    op.create_table('webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('events', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('secret', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_triggered', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('webhooks')
    op.drop_table('routes')
    op.drop_table('transactions')
    op.drop_table('inventory')
    op.drop_table('stores')
    op.drop_table('products')
    op.drop_table('api_keys')
    op.drop_table('users') 