# integration_example.py
"""
Real-world integration example showing how to use the order managers
in your agentic customer support platform.
"""

import os
from typing import Optional, Dict, Any
from enum import Enum
from order_manager_factory import OrderManagerFactory, OrderManagerType
from order_manager import OrderStatus


class OrderManagementService:
    """
    High-level service for order management.
    Abstracts away database selection and provides business logic.
    """

    def __init__(self):
        """Initialize with manager from environment or default to SQLite."""
        self.manager = OrderManagerFactory.create_from_env(
            env_var='ORDER_MANAGER_TYPE',
            # Additional config can be passed here
        )
        print(f"Initialized order manager: {type(self.manager).__name__}")

    def process_new_order(
        self,
        customer_id: str,
        customer_name: str,
        items: list,
        total_price: float,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Process a new order from the customer support agent.

        Args:
            customer_id: Customer identifier
            customer_name: Customer name
            items: List of items [{"item_name": str, "quantity": int, "unit_price": float}]
            total_price: Order total
            conversation_id: Associated conversation ID
            metadata: Additional data (order source, preferences, etc.)

        Returns:
            order_id if successful, None otherwise
        """
        import uuid
        from datetime import datetime, timedelta

        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        # Calculate estimated ready time (15 minutes from now)
        estimated_ready = (datetime.now() + timedelta(minutes=15)).isoformat()

        # Create the order
        success = self.manager.create_order(
            order_id=order_id,
            customer_id=customer_id,
            customer_name=customer_name,
            items=items,
            total_price=total_price,
            conversation_id=conversation_id,
            estimated_ready_time=estimated_ready,
            metadata=metadata or {}
        )

        if success:
            print(f"Order {order_id} created successfully")
            return order_id
        else:
            print(f"Failed to create order {order_id}")
            return None

    def get_order_status(self, order_id: str) -> Optional[str]:
        """Get the current status of an order."""
        order = self.manager.get_order(order_id)
        if order:
            return order.get('status')
        return None

    def get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get complete order details."""
        return self.manager.get_order(order_id)

    def get_customer_active_orders(self, customer_name: str) -> list:
        """Get all non-completed orders for a customer."""
        active_statuses = [
            OrderStatus.PENDING.value,
            OrderStatus.CONFIRMED.value,
            OrderStatus.PREPARING.value,
            OrderStatus.READY.value,
        ]

        all_orders = self.manager.get_customer_orders(customer_name)
        return [o for o in all_orders if o['status'] in active_statuses]

    def get_customer_order_history(self, customer_name: str, limit: int = 10) -> list:
        """Get customer's order history."""
        return self.manager.get_customer_orders(customer_name, limit=limit)

    def mark_order_ready(self, order_id: str) -> bool:
        """Mark an order as ready for pickup."""
        return self.manager.update_order_status(order_id, OrderStatus.READY)

    def mark_order_completed(self, order_id: str) -> bool:
        """Mark an order as completed."""
        return self.manager.update_order_status(order_id, OrderStatus.COMPLETED)

    def mark_order_cancelled(self, order_id: str) -> bool:
        """Cancel an order."""
        return self.manager.update_order_status(order_id, OrderStatus.CANCELLED)

    def get_business_metrics(self) -> Dict[str, Any]:
        """Get business metrics for dashboard/reporting."""
        return self.manager.get_order_statistics()

    def format_order_for_customer(self, order_id: str) -> str:
        """Format order details for customer communication."""
        return self.manager.format_order_summary(order_id)


# Example: Integration with your delivery agent or platform
class DeliveryAgentIntegration:
    """Example of how to integrate with your delivery agent."""

    def __init__(self):
        self.order_service = OrderManagementService()

    def handle_order_placement(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle order placement event from conversation.
        Called when a customer places an order through the agent.
        """
        order_id = self.order_service.process_new_order(
            customer_id=event['customer_id'],
            customer_name=event['customer_name'],
            items=event['items'],
            total_price=event['total_price'],
            conversation_id=event.get('conversation_id'),
            metadata={
                'channel': event.get('channel', 'web'),
                'notes': event.get('special_requests'),
            }
        )

        if order_id:
            return {
                'success': True,
                'order_id': order_id,
                'message': f'Order {order_id} confirmed!',
                'estimated_ready': event.get('estimated_ready_time'),
            }
        else:
            return {
                'success': False,
                'message': 'Failed to create order. Please try again.',
            }

    def handle_order_status_query(self, order_id: str) -> Dict[str, Any]:
        """
        Handle customer query about order status.
        Called when customer asks "where is my order?"
        """
        order = self.order_service.get_order_details(order_id)

        if not order:
            return {
                'found': False,
                'message': f'Order {order_id} not found.',
            }

        return {
            'found': True,
            'order_id': order_id,
            'status': order['status'],
            'customer_name': order['customer_name'],
            'total': order['total_price'],
            'estimated_ready': order.get('estimated_ready_time'),
            'summary': self.order_service.format_order_for_customer(order_id),
        }

    def handle_customer_history(self, customer_name: str) -> Dict[str, Any]:
        """
        Handle customer history request.
        Called when customer asks "show me my orders"
        """
        orders = self.order_service.get_customer_order_history(customer_name, limit=5)

        if not orders:
            return {
                'found': False,
                'message': f'No orders found for {customer_name}.',
            }

        return {
            'found': True,
            'customer_name': customer_name,
            'recent_orders': [
                {
                    'order_id': o['order_id'],
                    'status': o['status'],
                    'total': o['total_price'],
                    'created': o['created_at'],
                }
                for o in orders
            ],
            'count': len(orders),
        }

    def get_business_dashboard(self) -> Dict[str, Any]:
        """Get metrics for business dashboard."""
        stats = self.order_service.get_business_metrics()

        return {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'metrics': stats,
            'summary': f"Total revenue: ${stats['total_revenue']} from {stats['total_orders']} orders",
        }


# Usage example
if __name__ == "__main__":
    print("Order Management Service Integration Examples\n")

    # Initialize the service
    delivery_agent = DeliveryAgentIntegration()

    # Example 1: Process a new order
    print("=" * 60)
    print("Example 1: Processing a new order")
    print("=" * 60)

    order_event = {
        'customer_id': 'CUST-123',
        'customer_name': 'Alice Johnson',
        'items': [
            {'item_name': 'Espresso', 'quantity': 2, 'unit_price': 3.00},
            {'item_name': 'Croissant', 'quantity': 1, 'unit_price': 4.50},
        ],
        'total_price': 10.50,
        'conversation_id': 'CONV-abc123',
        'channel': 'web',
        'special_requests': 'Extra hot, oat milk',
    }

    result = delivery_agent.handle_order_placement(order_event)
    print(f"Result: {result}\n")

    # Save order_id for next examples
    if result['success']:
        order_id = result['order_id']

        # Example 2: Check order status
        print("=" * 60)
        print("Example 2: Checking order status")
        print("=" * 60)

        status_result = delivery_agent.handle_order_status_query(order_id)
        print(f"Result: {status_result}\n")

        # Example 3: Get customer history
        print("=" * 60)
        print("Example 3: Getting customer order history")
        print("=" * 60)

        history_result = delivery_agent.handle_customer_history('Alice Johnson')
        print(f"Result: {history_result}\n")

        # Example 4: Get business metrics
        print("=" * 60)
        print("Example 4: Getting business dashboard metrics")
        print("=" * 60)

        dashboard = delivery_agent.get_business_dashboard()
        print(f"Result: {dashboard}\n")

    print("=" * 60)
    print("Integration examples complete!")
    print("=" * 60)
