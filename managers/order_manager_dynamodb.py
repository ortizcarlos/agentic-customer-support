# order_manager_dynamodb.py

import boto3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    PREPARING = "Being prepared"
    READY = "Ready for pickup"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class OrderManagerDynamoDB:
    """
    Manages order storage and retrieval using AWS DynamoDB.
    Handles order creation, updates, status tracking, and queries.
    Provides cloud-native operations for scalable order management.
    """

    def __init__(self, table_name: str = "orders", region: str = "us-east-1"):
        """
        Initialize the order manager with DynamoDB.

        Args:
            table_name: Name of the DynamoDB table
            region: AWS region (default: us-east-1)
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def _serialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python types to DynamoDB types."""
        serialized = {}
        for key, value in item.items():
            if isinstance(value, float):
                serialized[key] = Decimal(str(value))
            elif isinstance(value, dict):
                serialized[key] = value
            elif isinstance(value, list):
                serialized[key] = value
            else:
                serialized[key] = value
        return serialized

    def _deserialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB types back to Python types."""
        deserialized = {}
        for key, value in item.items():
            if isinstance(value, Decimal):
                # Preserve as float for compatibility
                deserialized[key] = float(value)
            else:
                deserialized[key] = value
        return deserialized

    def create_order(self, order_id: str, customer_id: str, customer_name: str,
                    items: List[Dict[str, Any]], total_price: float,
                    conversation_id: str = None, estimated_ready_time: str = None,
                    metadata: Dict[str, Any] = None) -> bool:
        """
        Create a new order in DynamoDB.

        Args:
            order_id: Unique order identifier
            customer_id: Customer ID
            customer_name: Customer name
            items: List of items with format: [{"item_name": str, "quantity": int, "unit_price": float}]
            total_price: Total order price
            conversation_id: Associated conversation ID
            estimated_ready_time: Estimated time when order will be ready
            metadata: Optional additional metadata

        Returns:
            True if order was created successfully
        """
        try:
            now = datetime.now().isoformat()

            order_item = {
                'order_id': order_id,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'total_price': Decimal(str(total_price)),
                'status': OrderStatus.PENDING.value,
                'created_at': now,
                'updated_at': now,
                'items': items,
            }

            if estimated_ready_time:
                order_item['estimated_ready_time'] = estimated_ready_time

            if metadata:
                order_item['metadata'] = metadata

            if conversation_id:
                order_item['conversation_id'] = conversation_id

            self.table.put_item(Item=order_item)
            return True

        except Exception as e:
            print(f"Error creating order: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a complete order with all its items.

        Args:
            order_id: The order ID

        Returns:
            Order details including items, or None if not found
        """
        try:
            response = self.table.get_item(Key={'order_id': order_id})

            if 'Item' not in response:
                return None

            item = response['Item']
            return self._deserialize_item(item)

        except Exception as e:
            print(f"Error getting order: {e}")
            return None

    def get_customer_orders(self, customer_name: str, limit: int = None,
                           status: str = None) -> List[Dict[str, Any]]:
        """
        Get all orders for a specific customer.

        Args:
            customer_name: The customer name
            limit: Optional limit on number of orders
            status: Optional filter by order status

        Returns:
            List of orders ordered by most recent first
        """
        try:
            query_params = {
                'IndexName': 'customer_name_index',
                'KeyConditionExpression': 'customer_name = :cn',
                'ExpressionAttributeValues': {':cn': customer_name},
                'ScanIndexForward': False,  # Descending order (most recent first)
            }

            if limit:
                query_params['Limit'] = limit

            response = self.table.query(**query_params)

            items = [self._deserialize_item(item) for item in response.get('Items', [])]

            # Filter by status if provided
            if status:
                items = [item for item in items if item.get('status') == status]

            return items

        except Exception as e:
            print(f"Error getting customer orders: {e}")
            return []

    def get_customer_last_order(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent order from a customer.

        Args:
            customer_id: The customer ID

        Returns:
            Last order details or None
        """
        try:
            response = self.table.query(
                IndexName='customer_id_index',
                KeyConditionExpression='customer_id = :ci',
                ExpressionAttributeValues={':ci': customer_id},
                ScanIndexForward=False,  # Descending order
                Limit=1
            )

            items = response.get('Items', [])
            if not items:
                return None

            return self._deserialize_item(items[0])

        except Exception as e:
            print(f"Error getting customer last order: {e}")
            return None

    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """
        Update the status of an order.

        Args:
            order_id: The order ID
            status: New status (use OrderStatus enum)

        Returns:
            True if updated successfully
        """
        try:
            now = datetime.now().isoformat()

            self.table.update_item(
                Key={'order_id': order_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status.value,
                    ':updated_at': now,
                },
                ReturnValues='NONE'
            )
            return True

        except Exception as e:
            print(f"Error updating order status: {e}")
            return False

    def update_order_ready_time(self, order_id: str, estimated_ready_time: str) -> bool:
        """
        Update the estimated ready time of an order.

        Args:
            order_id: The order ID
            estimated_ready_time: New estimated time (ISO format)

        Returns:
            True if updated successfully
        """
        try:
            now = datetime.now().isoformat()

            self.table.update_item(
                Key={'order_id': order_id},
                UpdateExpression='SET estimated_ready_time = :ert, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':ert': estimated_ready_time,
                    ':updated_at': now,
                },
                ReturnValues='NONE'
            )
            return True

        except Exception as e:
            print(f"Error updating order ready time: {e}")
            return False

    def get_orders_by_status(self, status: OrderStatus, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all orders with a specific status.

        Args:
            status: Order status filter
            limit: Optional limit on number of results

        Returns:
            List of orders
        """
        try:
            query_params = {
                'IndexName': 'status_index',
                'KeyConditionExpression': '#status = :status',
                'ExpressionAttributeNames': {'#status': 'status'},
                'ExpressionAttributeValues': {':status': status.value},
                'ScanIndexForward': True,  # Ascending order (oldest first)
            }

            if limit:
                query_params['Limit'] = limit

            response = self.table.query(**query_params)

            return [self._deserialize_item(item) for item in response.get('Items', [])]

        except Exception as e:
            print(f"Error getting orders by status: {e}")
            return []

    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Get order statistics via table scan.

        Returns:
            Dictionary with order stats
        """
        try:
            # Scan the entire table
            response = self.table.scan()
            items = response.get('Items', [])

            total_orders = len(items)
            total_revenue = 0.0
            status_counts = {}
            unique_customers = set()

            for item in items:
                item = self._deserialize_item(item)
                total_revenue += item.get('total_price', 0.0)

                order_status = item.get('status', 'Unknown')
                status_counts[order_status] = status_counts.get(order_status, 0) + 1

                if item.get('customer_id'):
                    unique_customers.add(item['customer_id'])

            # Handle pagination if needed
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items = response.get('Items', [])

                for item in items:
                    item = self._deserialize_item(item)
                    total_revenue += item.get('total_price', 0.0)

                    order_status = item.get('status', 'Unknown')
                    status_counts[order_status] = status_counts.get(order_status, 0) + 1

                    if item.get('customer_id'):
                        unique_customers.add(item['customer_id'])

            return {
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "status_breakdown": status_counts,
                "unique_customers": len(unique_customers)
            }

        except Exception as e:
            print(f"Error getting order statistics: {e}")
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "status_breakdown": {},
                "unique_customers": 0
            }

    def delete_order(self, order_id: str) -> bool:
        """
        Delete an order from DynamoDB.

        Args:
            order_id: The order ID

        Returns:
            True if deleted successfully
        """
        try:
            self.table.delete_item(Key={'order_id': order_id})
            return True

        except Exception as e:
            print(f"Error deleting order: {e}")
            return False

    def clear_all_orders(self):
        """
        Delete all orders. Use with caution!
        """
        try:
            response = self.table.scan()
            items = response.get('Items', [])

            for item in items:
                self.table.delete_item(Key={'order_id': item['order_id']})

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items = response.get('Items', [])

                for item in items:
                    self.table.delete_item(Key={'order_id': item['order_id']})

        except Exception as e:
            print(f"Error clearing all orders: {e}")

    def format_order_summary(self, order_id: str) -> str:
        """
        Format an order as a readable summary string.

        Args:
            order_id: The order ID

        Returns:
            Formatted order summary
        """
        order = self.get_order(order_id)
        if not order:
            return "Order not found."

        summary = f"""
ORDER #{order['order_id']}
Customer: {order['customer_name']} (ID: {order['customer_id']})
Status: {order['status']}
Created: {order['created_at']}

Items:
"""
        for item in order.get("items", []):
            summary += f"  - {item['item_name']} x{item['quantity']} @ ${item['unit_price']:.2f} = ${item['quantity'] * item['unit_price']:.2f}\n"

        summary += f"\nTotal: ${order['total_price']:.2f}"
        if order.get("estimated_ready_time"):
            summary += f"\nEstimated Ready: {order['estimated_ready_time']}"

        return summary
