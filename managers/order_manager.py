# order_manager.py

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    PREPARING = "Being prepared"
    READY = "Ready for pickup"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class OrderManager:
    """
    Manages order storage and retrieval using SQLite.
    Handles order creation, updates, status tracking, and queries.
    """

    def __init__(self, db_path: str = "conversations.db"):
        """
        Initialize the order manager with SQLite database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    customer_name TEXT,
                    total_price REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    estimated_ready_time TEXT,
                    conversation_id TEXT,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            # Order items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            """)

            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_customer_id
                ON orders(customer_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_status
                ON orders(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_created_at
                ON orders(created_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_order_items_order_id
                ON order_items(order_id)
            """)

            conn.commit()

    def create_order(self, order_id: str, customer_id: str, customer_name: str,
                    items: List[Dict[str, Any]], total_price: float,
                    conversation_id: str = None, estimated_ready_time: str = None,
                    metadata: Dict[str, Any] = None) -> bool:
        """
        Create a new order in the database.

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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                metadata_json = json.dumps(metadata) if metadata else "{}"

                # Insert order
                cursor.execute("""
                    INSERT INTO orders
                    (order_id, customer_id, customer_name, total_price, status, created_at, updated_at,
                     estimated_ready_time, conversation_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (order_id, customer_id, customer_name, total_price, OrderStatus.PENDING.value,
                      now, now, estimated_ready_time, conversation_id, metadata_json))

                # Insert order items
                for item in items:
                    subtotal = item["unit_price"] * item["quantity"]
                    cursor.execute("""
                        INSERT INTO order_items
                        (order_id, item_name, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (order_id, item["item_name"], item["quantity"],
                          item["unit_price"], subtotal))

                conn.commit()
                return True

        except sqlite3.IntegrityError:
            return False

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a complete order with all its items.

        Args:
            order_id: The order ID

        Returns:
            Order details including items, or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get order details
            cursor.execute("""
                SELECT order_id, customer_id, customer_name, total_price, status, created_at,
                       updated_at, estimated_ready_time, conversation_id, metadata
                FROM orders
                WHERE order_id = ?
            """, (order_id,))

            row = cursor.fetchone()
            if not row:
                return None

            order_data = {
                "order_id": row[0],
                "customer_id": row[1],
                "customer_name": row[2],
                "total_price": row[3],
                "status": row[4],
                "created_at": row[5],
                "updated_at": row[6],
                "estimated_ready_time": row[7],
                "conversation_id": row[8],
                "metadata": json.loads(row[9]) if row[9] else {}
            }

            # Get order items
            cursor.execute("""
                SELECT item_name, quantity, unit_price, subtotal
                FROM order_items
                WHERE order_id = ?
                ORDER BY id ASC
            """, (order_id,))

            items = [
                {
                    "item_name": row[0],
                    "quantity": row[1],
                    "unit_price": row[2],
                    "subtotal": row[3]
                }
                for row in cursor.fetchall()
            ]

            order_data["items"] = items
            return order_data

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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if status:
                query = """
                    SELECT order_id, customer_id, customer_name, total_price, status, created_at,
                           updated_at, estimated_ready_time, conversation_id, metadata
                    FROM orders
                    WHERE customer_name = ? AND status = ?
                    ORDER BY created_at DESC
                """
                params = (customer_name, status)
            else:
                query = """
                    SELECT order_id, customer_id, customer_name, total_price, status, created_at,
                           updated_at, estimated_ready_time, conversation_id, metadata
                    FROM orders
                    WHERE customer_name = ?
                    ORDER BY created_at DESC
                """
                params = (customer_name,)

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            orders = []
            for row in rows:
                order = {
                    "order_id": row[0],
                    "customer_id": row[1],
                    "customer_name": row[2],
                    "total_price": row[3],
                    "status": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "estimated_ready_time": row[7],
                    "conversation_id": row[8],
                    "metadata": json.loads(row[9]) if row[9] else {}
                }
                orders.append(order)

            return orders

    def get_customer_last_order(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent order from a customer.

        Args:
            customer_id: The customer ID

        Returns:
            Last order details or None
        """
        orders = self.get_customer_orders(customer_id, limit=1)
        return orders[0] if orders else None

    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """
        Update the status of an order.

        Args:
            order_id: The order ID
            status: New status (use OrderStatus enum)

        Returns:
            True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("""
                UPDATE orders
                SET status = ?, updated_at = ?
                WHERE order_id = ?
            """, (status.value, now, order_id))

            conn.commit()
            return cursor.rowcount > 0

    def update_order_ready_time(self, order_id: str, estimated_ready_time: str) -> bool:
        """
        Update the estimated ready time of an order.

        Args:
            order_id: The order ID
            estimated_ready_time: New estimated time (ISO format)

        Returns:
            True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("""
                UPDATE orders
                SET estimated_ready_time = ?, updated_at = ?
                WHERE order_id = ?
            """, (estimated_ready_time, now, order_id))

            conn.commit()
            return cursor.rowcount > 0

    def get_orders_by_status(self, status: OrderStatus, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all orders with a specific status.

        Args:
            status: Order status filter
            limit: Optional limit on number of results

        Returns:
            List of orders
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT order_id, customer_id, customer_name, total_price, status, created_at,
                       updated_at, estimated_ready_time, conversation_id, metadata
                FROM orders
                WHERE status = ?
                ORDER BY created_at ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (status.value,))
            rows = cursor.fetchall()

            return [
                {
                    "order_id": row[0],
                    "customer_id": row[1],
                    "customer_name": row[2],
                    "total_price": row[3],
                    "status": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "estimated_ready_time": row[7],
                    "conversation_id": row[8],
                    "metadata": json.loads(row[9]) if row[9] else {}
                }
                for row in rows
            ]

    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Get order statistics.

        Returns:
            Dictionary with order stats
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM orders")
            total_orders = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(total_price) FROM orders")
            total_revenue = cursor.fetchone()[0] or 0.0

            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM orders
                GROUP BY status
            """)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT COUNT(DISTINCT customer_id) FROM orders
                WHERE customer_id IS NOT NULL
            """)
            unique_customers = cursor.fetchone()[0]

            return {
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "status_breakdown": status_counts,
                "unique_customers": unique_customers
            }

    def delete_order(self, order_id: str) -> bool:
        """
        Delete an order and its items.

        Args:
            order_id: The order ID

        Returns:
            True if deleted successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))

            conn.commit()
            return cursor.rowcount > 0

    def clear_all_orders(self):
        """
        Delete all orders and items. Use with caution!
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM order_items")
            cursor.execute("DELETE FROM orders")
            conn.commit()

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
        for item in order["items"]:
            summary += f"  - {item['item_name']} x{item['quantity']} @ ${item['unit_price']:.2f} = ${item['subtotal']:.2f}\n"

        summary += f"\nTotal: ${order['total_price']:.2f}"
        if order["estimated_ready_time"]:
            summary += f"\nEstimated Ready: {order['estimated_ready_time']}"

        return summary
