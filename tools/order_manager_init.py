# order_manager_init.py
"""
Shared order manager initialization for all tools.
Uses factory pattern to support both SQLite (local) and DynamoDB (cloud).
"""

from managers.order_manager_factory import OrderManagerFactory

# Initialize manager based on environment
# - ORDER_MANAGER_TYPE=sqlite (default): Uses SQLite for local development
# - ORDER_MANAGER_TYPE=dynamodb: Uses DynamoDB for cloud production
order_manager = OrderManagerFactory.create_from_env()
