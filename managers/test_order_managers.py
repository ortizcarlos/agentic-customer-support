# test_order_managers.py
"""
Example usage and comparison of SQLite and DynamoDB order managers.
This script demonstrates how both managers implement the same interface.
"""

from order_manager import OrderManager, OrderStatus
from order_manager_dynamodb import OrderManagerDynamoDB
from order_manager_factory import OrderManagerFactory, OrderManagerType


def test_sqlite_manager():
    """Test SQLite order manager"""
    print("\n" + "="*60)
    print("Testing SQLite Order Manager")
    print("="*60)

    manager = OrderManager(db_path=":memory:")  # Use in-memory for testing

    # Create an order
    success = manager.create_order(
        order_id="ORD-001",
        customer_id="CUST-001",
        customer_name="Alice Johnson",
        items=[
            {"item_name": "Coffee", "quantity": 2, "unit_price": 3.50},
            {"item_name": "Sandwich", "quantity": 1, "unit_price": 8.99}
        ],
        total_price=16.99,
        estimated_ready_time="2024-11-22T15:30:00",
        metadata={"table": "5"}
    )
    print(f"Order created: {success}")

    # Retrieve the order
    order = manager.get_order("ORD-001")
    print(f"\nOrder retrieved: {order['order_id']}")
    print(f"Status: {order['status']}")
    print(f"Total: ${order['total_price']}")

    # Update status
    manager.update_order_status("ORD-001", OrderStatus.CONFIRMED)
    updated_order = manager.get_order("ORD-001")
    print(f"\nStatus updated to: {updated_order['status']}")

    # Format summary
    print("\nOrder Summary:")
    print(manager.format_order_summary("ORD-001"))

    # Get statistics
    stats = manager.get_order_statistics()
    print(f"\nStatistics: {stats}")


def test_dynamodb_manager():
    """Test DynamoDB order manager (requires AWS credentials)"""
    print("\n" + "="*60)
    print("Testing DynamoDB Order Manager")
    print("="*60)

    try:
        # Note: This requires AWS credentials and valid DynamoDB access
        manager = OrderManagerDynamoDB(table_name="orders-test", region="us-east-1")

        # Create an order
        success = manager.create_order(
            order_id="ORD-002",
            customer_id="CUST-002",
            customer_name="Bob Smith",
            items=[
                {"item_name": "Burger", "quantity": 1, "unit_price": 12.99},
                {"item_name": "Fries", "quantity": 2, "unit_price": 3.99}
            ],
            total_price=20.97,
            estimated_ready_time="2024-11-22T16:00:00",
            metadata={"delivery": "yes"}
        )
        print(f"Order created: {success}")

        # Retrieve the order
        order = manager.get_order("ORD-002")
        if order:
            print(f"\nOrder retrieved: {order['order_id']}")
            print(f"Status: {order['status']}")
            print(f"Total: ${order['total_price']}")

            # Update status
            manager.update_order_status("ORD-002", OrderStatus.PREPARING)
            updated_order = manager.get_order("ORD-002")
            print(f"\nStatus updated to: {updated_order['status']}")

            # Format summary
            print("\nOrder Summary:")
            print(manager.format_order_summary("ORD-002"))

    except Exception as e:
        print(f"DynamoDB test skipped: {e}")
        print("(This is expected if AWS credentials are not configured)")


def test_factory():
    """Test the factory pattern"""
    print("\n" + "="*60)
    print("Testing Order Manager Factory")
    print("="*60)

    # Create SQLite manager via factory
    sqlite_manager = OrderManagerFactory.create(
        OrderManagerType.SQLITE,
        db_path=":memory:"
    )
    print(f"Created SQLite manager: {type(sqlite_manager).__name__}")

    # Create DynamoDB manager via factory (would require AWS credentials)
    # dynamodb_manager = OrderManagerFactory.create(
    #     OrderManagerType.DYNAMODB,
    #     table_name="orders",
    #     region="us-east-1"
    # )
    # print(f"Created DynamoDB manager: {type(dynamodb_manager).__name__}")


if __name__ == "__main__":
    print("\nOrder Manager Testing Suite")
    print("Testing both SQLite and DynamoDB implementations")

    # Test SQLite (always works)
    test_sqlite_manager()

    # Test Factory pattern
    test_factory()

    # Test DynamoDB (requires AWS setup)
    # Uncomment to test if you have AWS credentials configured
    # test_dynamodb_manager()

    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)
