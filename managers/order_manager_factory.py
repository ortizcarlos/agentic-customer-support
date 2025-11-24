# order_manager_factory.py

from enum import Enum
from typing import Union
from .order_manager import OrderManager
from .order_manager_dynamodb import OrderManagerDynamoDB


class OrderManagerType(Enum):
    """Supported order manager implementations"""
    SQLITE = "sqlite"
    DYNAMODB = "dynamodb"


class OrderManagerFactory:
    """
    Factory for creating order manager instances.
    Supports both SQLite (local development) and DynamoDB (cloud production).
    """

    @staticmethod
    def create(
        manager_type: OrderManagerType,
        **kwargs
    ) -> Union[OrderManager, OrderManagerDynamoDB]:
        """
        Create an order manager instance of the specified type.

        Args:
            manager_type: Type of manager to create (SQLITE or DYNAMODB)
            **kwargs: Configuration parameters specific to the manager type
                - For SQLITE: db_path (default: "conversations.db")
                - For DYNAMODB: table_name (default: "orders"), region (default: "us-east-1")

        Returns:
            An OrderManager or OrderManagerDynamoDB instance

        Raises:
            ValueError: If manager_type is not supported
        """
        if manager_type == OrderManagerType.SQLITE:
            db_path = kwargs.get('db_path', 'conversations.db')
            return OrderManager(db_path=db_path)

        elif manager_type == OrderManagerType.DYNAMODB:
            table_name = kwargs.get('table_name', 'orders')
            region = kwargs.get('region', 'us-east-1')
            return OrderManagerDynamoDB(table_name=table_name, region=region)

        else:
            raise ValueError(f"Unsupported manager type: {manager_type}")

    @staticmethod
    def create_from_env(
        env_var: str = 'ORDER_MANAGER_TYPE',
        **kwargs
    ) -> Union[OrderManager, OrderManagerDynamoDB]:
        """
        Create an order manager instance based on environment variable.

        Args:
            env_var: Environment variable name to read manager type from (default: ORDER_MANAGER_TYPE)
            **kwargs: Configuration parameters (passed to create())

        Returns:
            An OrderManager or OrderManagerDynamoDB instance

        Example:
            # Assuming ORDER_MANAGER_TYPE=dynamodb in environment
            manager = OrderManagerFactory.create_from_env(region='us-west-2')
        """
        import os

        manager_type_str = os.getenv(env_var, OrderManagerType.SQLITE.value).lower()

        try:
            manager_type = OrderManagerType(manager_type_str)
        except ValueError:
            raise ValueError(
                f"Invalid manager type '{manager_type_str}'. "
                f"Must be one of: {', '.join([t.value for t in OrderManagerType])}"
            )

        return OrderManagerFactory.create(manager_type, **kwargs)
