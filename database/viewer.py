# db_viewer.py

"""
Database Viewer and Query Tool
Utilities to inspect, visualize, and query SQLite data from conversations and orders
"""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from tabulate import tabulate
from ..managers.conversation_manager import ConversationManager
from ..managers.order_manager import OrderManager
import json


class DatabaseViewer:
    """Utility class for viewing and querying database contents"""

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.conversation_manager = ConversationManager(db_path)
        self.order_manager = OrderManager(db_path)

    # ==================== CONVERSATIONS ====================

    def show_all_conversations(self):
        """Display all conversations in a formatted table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, customer_id, customer_name, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
            """)
            rows = cursor.fetchall()

            if not rows:
                print("\n❌ No conversations found.\n")
                return

            headers = ["Conversation ID", "Customer ID", "Customer Name", "Created", "Updated"]
            print("\n📋 CONVERSATIONS\n")
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            print(f"\nTotal: {len(rows)} conversations\n")

    def show_customer_conversations(self, customer_id: str):
        """Display all conversations for a specific customer"""
        conversations = self.conversation_manager.get_customer_conversations(customer_id)

        if not conversations:
            print(f"\n❌ No conversations found for customer {customer_id}\n")
            return

        data = [
            [conv["id"], conv["customer_name"], conv["created_at"], conv["updated_at"]]
            for conv in conversations
        ]

        headers = ["Conversation ID", "Customer Name", "Created", "Updated"]
        print(f"\n📋 CONVERSATIONS FOR CUSTOMER {customer_id}\n")
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print(f"\nTotal: {len(conversations)} conversations\n")

    def show_conversation_messages(self, conversation_id: str, limit: int = None):
        """Display all messages in a specific conversation"""
        messages = self.conversation_manager.get_conversation_messages(conversation_id, limit=limit)

        if not messages:
            print(f"\n❌ No messages found in conversation {conversation_id}\n")
            return

        print(f"\n💬 MESSAGES FOR CONVERSATION {conversation_id}\n")
        for idx, msg in enumerate(messages, 1):
            sender = msg["sender_name"] or msg["sender_type"].upper()
            timestamp = msg["timestamp"]
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]

            print(f"{idx}. [{timestamp}] {sender}:")
            print(f"   {content}\n")

        print(f"Total: {len(messages)} messages\n")

    # ==================== ORDERS ====================

    def show_all_orders(self):
        """Display all orders in a formatted table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT order_id, customer_name, customer_id, total_price, status, created_at, updated_at
                FROM orders
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()

            if not rows:
                print("\n❌ No orders found.\n")
                return

            headers = ["Order ID", "Customer", "Customer ID", "Total", "Status", "Created", "Updated"]
            print("\n🛒 ALL ORDERS\n")
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            print(f"\nTotal: {len(rows)} orders\n")

    def show_customer_orders(self, customer_id: str):
        """Display all orders for a specific customer"""
        orders = self.order_manager.get_customer_orders(customer_id)

        if not orders:
            print(f"\n❌ No orders found for customer {customer_id}\n")
            return

        data = [
            [ord["order_id"], ord["customer_name"], ord["total_price"], ord["status"], ord["created_at"]]
            for ord in orders
        ]

        headers = ["Order ID", "Customer", "Total Price", "Status", "Created"]
        print(f"\n🛒 ORDERS FOR CUSTOMER {customer_id}\n")
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print(f"\nTotal: {len(orders)} orders\n")

    def show_order_details(self, order_id: str):
        """Display detailed information about a specific order"""
        order = self.order_manager.get_order(order_id)

        if not order:
            print(f"\n❌ Order {order_id} not found.\n")
            return

        print(f"\n🛒 ORDER DETAILS: {order_id}\n")
        print(f"Customer: {order['customer_name']} (ID: {order['customer_id']})")
        print(f"Status: {order['status']}")
        print(f"Total: ${order['total_price']:.2f}")
        print(f"Created: {order['created_at']}")
        print(f"Updated: {order['updated_at']}")
        if order['estimated_ready_time']:
            print(f"Estimated Ready: {order['estimated_ready_time']}")

        print("\n📦 Items:")
        item_data = [
            [item['item_name'], item['quantity'], f"${item['unit_price']:.2f}",
             f"${item['subtotal']:.2f}"]
            for item in order['items']
        ]
        print(tabulate(item_data, headers=["Item", "Qty", "Unit Price", "Subtotal"], tablefmt="grid"))
        print()

    def show_orders_by_status(self, status: str):
        """Display all orders with a specific status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT order_id, customer_name, customer_id, total_price, created_at
                FROM orders
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status,))
            rows = cursor.fetchall()

            if not rows:
                print(f"\n❌ No orders found with status '{status}'.\n")
                return

            headers = ["Order ID", "Customer", "Customer ID", "Total", "Created"]
            print(f"\n🛒 ORDERS WITH STATUS: {status}\n")
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            print(f"\nTotal: {len(rows)} orders\n")

    # ==================== STATISTICS ====================

    def show_conversation_stats(self):
        """Display conversation statistics"""
        stats = self.conversation_manager.get_statistics()

        print("\n📊 CONVERSATION STATISTICS\n")
        print(f"Total Conversations: {stats['total_conversations']}")
        print(f"Total Messages: {stats['total_messages']}")
        print(f"Unique Customers: {stats['unique_customers']}")
        print()

    def show_order_stats(self):
        """Display order statistics"""
        stats = self.order_manager.get_order_statistics()

        print("\n📊 ORDER STATISTICS\n")
        print(f"Total Orders: {stats['total_orders']}")
        print(f"Total Revenue: ${stats['total_revenue']:.2f}")
        print(f"Unique Customers: {stats['unique_customers']}")
        print(f"\nOrders by Status:")

        status_data = [
            [status, count] for status, count in stats['status_breakdown'].items()
        ]
        print(tabulate(status_data, headers=["Status", "Count"], tablefmt="grid"))
        print()

    def show_full_stats(self):
        """Display all statistics"""
        self.show_conversation_stats()
        self.show_order_stats()

    # ==================== EXPORT ====================

    def export_conversations_to_json(self, filename: str = "conversations_export.json"):
        """Export all conversations to JSON file"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, customer_id, customer_name, created_at, updated_at, metadata FROM conversations")
            conversations = cursor.fetchall()

            data = []
            for conv in conversations:
                conv_data = {
                    "id": conv[0],
                    "customer_id": conv[1],
                    "customer_name": conv[2],
                    "created_at": conv[3],
                    "updated_at": conv[4],
                    "metadata": json.loads(conv[5]) if conv[5] else {}
                }
                data.append(conv_data)

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"\n✅ Exported {len(data)} conversations to {filename}\n")

    def export_orders_to_json(self, filename: str = "orders_export.json"):
        """Export all orders to JSON file"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT order_id, customer_id, customer_name, total_price, status, created_at,
                       updated_at, estimated_ready_time, metadata
                FROM orders
            """)
            orders_db = cursor.fetchall()

            data = []
            for order in orders_db:
                order_data = {
                    "order_id": order[0],
                    "customer_id": order[1],
                    "customer_name": order[2],
                    "total_price": order[3],
                    "status": order[4],
                    "created_at": order[5],
                    "updated_at": order[6],
                    "estimated_ready_time": order[7],
                    "metadata": json.loads(order[8]) if order[8] else {}
                }
                data.append(order_data)

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"\n✅ Exported {len(data)} orders to {filename}\n")

    # ==================== CLEANUP ====================

    def delete_conversation(self, conversation_id: str):
        """Delete a conversation and all its messages"""
        success = self.conversation_manager.delete_conversation(conversation_id)
        if success:
            print(f"\n✅ Deleted conversation {conversation_id} and all its messages.\n")
        else:
            print(f"\n❌ Failed to delete conversation {conversation_id}.\n")

    def delete_order(self, order_id: str):
        """Delete an order and all its items"""
        success = self.order_manager.delete_order(order_id)
        if success:
            print(f"\n✅ Deleted order {order_id} and all its items.\n")
        else:
            print(f"\n❌ Failed to delete order {order_id}.\n")

    def clear_all_data(self, confirm: bool = False):
        """Clear all data from database (destructive!)"""
        if not confirm:
            response = input("\n⚠️  WARNING: This will delete ALL conversations and orders. Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                print("Cancelled.\n")
                return

        self.conversation_manager.clear_all_data()
        self.order_manager.clear_all_orders()
        print("\n✅ All data cleared.\n")


def main():
    """Interactive menu for database viewer"""
    viewer = DatabaseViewer()

    while True:
        print("\n" + "="*60)
        print("🗄️  DATABASE VIEWER - Restaurant Assistant")
        print("="*60)
        print("\n📋 CONVERSATIONS:")
        print("  1. Show all conversations")
        print("  2. Show conversations for a customer")
        print("  3. Show messages in a conversation")
        print("\n🛒 ORDERS:")
        print("  4. Show all orders")
        print("  5. Show orders for a customer")
        print("  6. Show order details")
        print("  7. Show orders by status")
        print("\n📊 STATISTICS:")
        print("  8. Show conversation statistics")
        print("  9. Show order statistics")
        print("  10. Show all statistics")
        print("\n💾 EXPORT:")
        print("  11. Export conversations to JSON")
        print("  12. Export orders to JSON")
        print("\n🗑️  CLEANUP:")
        print("  13. Delete a conversation")
        print("  14. Delete an order")
        print("  15. Clear all data (⚠️ DESTRUCTIVE)")
        print("\n  0. Exit")
        print("\n" + "="*60)

        choice = input("Select an option (0-15): ").strip()

        if choice == "0":
            print("\n👋 Goodbye!\n")
            break

        elif choice == "1":
            viewer.show_all_conversations()

        elif choice == "2":
            customer_id = input("Enter customer ID: ").strip()
            viewer.show_customer_conversations(customer_id)

        elif choice == "3":
            conv_id = input("Enter conversation ID: ").strip()
            viewer.show_conversation_messages(conv_id)

        elif choice == "4":
            viewer.show_all_orders()

        elif choice == "5":
            customer_id = input("Enter customer ID: ").strip()
            viewer.show_customer_orders(customer_id)

        elif choice == "6":
            order_id = input("Enter order ID: ").strip()
            viewer.show_order_details(order_id)

        elif choice == "7":
            status = input("Enter order status (Pending/Confirmed/Being prepared/Ready for pickup/Completed/Cancelled): ").strip()
            viewer.show_orders_by_status(status)

        elif choice == "8":
            viewer.show_conversation_stats()

        elif choice == "9":
            viewer.show_order_stats()

        elif choice == "10":
            viewer.show_full_stats()

        elif choice == "11":
            filename = input("Enter filename (default: conversations_export.json): ").strip()
            filename = filename if filename else "conversations_export.json"
            viewer.export_conversations_to_json(filename)

        elif choice == "12":
            filename = input("Enter filename (default: orders_export.json): ").strip()
            filename = filename if filename else "orders_export.json"
            viewer.export_orders_to_json(filename)

        elif choice == "13":
            conv_id = input("Enter conversation ID to delete: ").strip()
            viewer.delete_conversation(conv_id)

        elif choice == "14":
            order_id = input("Enter order ID to delete: ").strip()
            viewer.delete_order(order_id)

        elif choice == "15":
            viewer.clear_all_data()

        else:
            print("\n❌ Invalid option. Please try again.\n")

        input("Press Enter to continue...")


if __name__ == "__main__":
    main()
