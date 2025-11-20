# db_query.py

"""
Database Query Tool
Direct SQL query interface for advanced database operations
"""

import sqlite3
from typing import List, Tuple
from tabulate import tabulate


class DatabaseQuery:
    """Utility class for executing SQL queries on the database"""

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path

    def execute_query(self, sql: str, params: Tuple = None) -> List[Tuple]:
        """Execute a SELECT query and return results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"\n❌ Error executing query: {e}\n")
            return []

    def execute_update(self, sql: str, params: Tuple = None) -> int:
        """Execute an INSERT, UPDATE, or DELETE query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            print(f"\n❌ Error executing update: {e}\n")
            return 0

    def get_schema(self) -> str:
        """Display database schema"""
        schema_info = """
╔════════════════════════════════════════════════════════════════════════════╗
║                        DATABASE SCHEMA                                     ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 TABLE: conversations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - id TEXT (PRIMARY KEY): Unique conversation identifier
  - customer_id TEXT: Customer's ID
  - customer_name TEXT: Customer's name
  - created_at TEXT: When the conversation started
  - updated_at TEXT: Last update time
  - metadata TEXT: JSON metadata


💬 TABLE: messages
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - id INTEGER (PRIMARY KEY): Unique message ID
  - conversation_id TEXT (FOREIGN KEY): Links to conversations.id
  - timestamp TEXT: When the message was sent
  - sender_type TEXT: 'user', 'agent', or 'system'
  - sender_name TEXT: Name of the sender
  - content TEXT: Message content
  - metadata TEXT: JSON metadata


🛒 TABLE: orders
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - order_id TEXT (PRIMARY KEY): Unique order identifier
  - customer_id TEXT: Customer's ID
  - customer_name TEXT: Customer's name
  - total_price REAL: Total order amount
  - status TEXT: Order status (Pending/Confirmed/Being prepared/Ready/etc)
  - created_at TEXT: When the order was placed
  - updated_at TEXT: Last update time
  - estimated_ready_time TEXT: When the order will be ready
  - conversation_id TEXT (FOREIGN KEY): Links to conversations.id
  - metadata TEXT: JSON metadata


📦 TABLE: order_items
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - id INTEGER (PRIMARY KEY): Unique item ID
  - order_id TEXT (FOREIGN KEY): Links to orders.order_id
  - item_name TEXT: Name of the menu item
  - quantity INTEGER: Quantity ordered
  - unit_price REAL: Price per unit
  - subtotal REAL: quantity * unit_price
"""
        return schema_info

    def show_table_info(self, table_name: str):
        """Show detailed info about a table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                if not columns:
                    print(f"\n❌ Table '{table_name}' not found.\n")
                    return

                print(f"\n📋 TABLE: {table_name}\n")
                data = [
                    [col[1], col[2], "PRIMARY KEY" if col[5] else ""]
                    for col in columns
                ]
                print(tabulate(data, headers=["Column", "Type", "Constraints"], tablefmt="grid"))
                print()
        except sqlite3.Error as e:
            print(f"\n❌ Error: {e}\n")


def run_custom_query():
    """Interactive SQL query executor"""
    query_tool = DatabaseQuery()

    print("\n" + "="*70)
    print("🔍 DATABASE QUERY TOOL - Restaurant Assistant")
    print("="*70)

    while True:
        print("\nOptions:")
        print("  1. View database schema")
        print("  2. View table info")
        print("  3. Execute SELECT query")
        print("  4. Execute UPDATE/INSERT/DELETE query")
        print("  5. Common queries (templates)")
        print("  0. Exit")
        print()

        choice = input("Select option (0-5): ").strip()

        if choice == "0":
            print("\n👋 Goodbye!\n")
            break

        elif choice == "1":
            print(query_tool.get_schema())

        elif choice == "2":
            table = input("Enter table name (conversations/messages/orders/order_items): ").strip()
            query_tool.show_table_info(table)

        elif choice == "3":
            sql = input("\nEnter SELECT query:\n> ").strip()
            if sql:
                results = query_tool.execute_query(sql)
                if results:
                    print(f"\n✅ Found {len(results)} rows:\n")
                    # Try to format as table if we have uniform columns
                    try:
                        print(tabulate(results, tablefmt="grid"))
                    except:
                        for row in results:
                            print(row)
                    print()
                else:
                    print("\n⚠️  No results found.\n")

        elif choice == "4":
            sql = input("\nEnter UPDATE/INSERT/DELETE query:\n> ").strip()
            if sql:
                affected = query_tool.execute_update(sql)
                print(f"\n✅ Query executed. Rows affected: {affected}\n")

        elif choice == "5":
            print_common_queries()

        else:
            print("\n❌ Invalid option.\n")


def print_common_queries():
    """Print common query templates"""
    templates = """
╔════════════════════════════════════════════════════════════════════════════╗
║                     COMMON QUERY TEMPLATES                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 CONVERSATIONS:
──────────────────────────────────────────────────────────────────────────────

1. Count conversations by customer:
   SELECT customer_id, COUNT(*) as count
   FROM conversations
   GROUP BY customer_id
   ORDER BY count DESC;

2. Find conversations created in last 24 hours:
   SELECT id, customer_name, created_at
   FROM conversations
   WHERE created_at > datetime('now', '-1 day');

3. Find customers with most messages:
   SELECT c.customer_id, c.customer_name, COUNT(m.id) as message_count
   FROM conversations c
   LEFT JOIN messages m ON c.id = m.conversation_id
   GROUP BY c.id
   ORDER BY message_count DESC;


💬 MESSAGES:
──────────────────────────────────────────────────────────────────────────────

4. Get all agent responses:
   SELECT conversation_id, sender_name, content, timestamp
   FROM messages
   WHERE sender_type = 'agent'
   ORDER BY timestamp DESC;

5. Messages by conversation in last hour:
   SELECT conversation_id, COUNT(*) as message_count
   FROM messages
   WHERE timestamp > datetime('now', '-1 hour')
   GROUP BY conversation_id;


🛒 ORDERS:
──────────────────────────────────────────────────────────────────────────────

6. Total revenue by customer:
   SELECT customer_id, customer_name, COUNT(*) as orders, SUM(total_price) as revenue
   FROM orders
   GROUP BY customer_id
   ORDER BY revenue DESC;

7. Orders by status:
   SELECT status, COUNT(*) as count, SUM(total_price) as total_revenue
   FROM orders
   GROUP BY status;

8. Most expensive orders:
   SELECT order_id, customer_name, total_price, created_at
   FROM orders
   ORDER BY total_price DESC
   LIMIT 10;

9. Orders created today:
   SELECT order_id, customer_name, total_price, status, created_at
   FROM orders
   WHERE DATE(created_at) = DATE('now')
   ORDER BY created_at DESC;


📦 ORDER ITEMS:
──────────────────────────────────────────────────────────────────────────────

10. Most popular items:
    SELECT item_name, SUM(quantity) as times_ordered, SUM(subtotal) as total_revenue
    FROM order_items
    GROUP BY item_name
    ORDER BY times_ordered DESC;

11. Average order items:
    SELECT AVG(item_count) as avg_items_per_order
    FROM (
        SELECT COUNT(*) as item_count FROM order_items GROUP BY order_id
    );


🔗 COMBINED:
──────────────────────────────────────────────────────────────────────────────

12. Conversations with orders:
    SELECT c.id, c.customer_name, COUNT(DISTINCT o.order_id) as order_count
    FROM conversations c
    LEFT JOIN orders o ON c.id = o.conversation_id
    GROUP BY c.id
    HAVING order_count > 0;

13. Customer journey (conversations + orders):
    SELECT c.customer_name, COUNT(DISTINCT c.id) as conversations,
           COUNT(DISTINCT o.order_id) as orders, SUM(o.total_price) as total_spent
    FROM conversations c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
    ORDER BY total_spent DESC;
"""
    print(templates)
    query = input("\nEnter a query number (1-13) or paste custom query (or press Enter to skip): ").strip()

    if query and query.isdigit() and 1 <= int(query) <= 13:
        # Map numbers to actual queries
        queries_map = {
            "1": "SELECT customer_id, COUNT(*) as count FROM conversations GROUP BY customer_id ORDER BY count DESC;",
            "2": "SELECT id, customer_name, created_at FROM conversations WHERE created_at > datetime('now', '-1 day');",
            "3": "SELECT c.customer_id, c.customer_name, COUNT(m.id) as message_count FROM conversations c LEFT JOIN messages m ON c.id = m.conversation_id GROUP BY c.id ORDER BY message_count DESC;",
            "4": "SELECT conversation_id, sender_name, content, timestamp FROM messages WHERE sender_type = 'agent' ORDER BY timestamp DESC;",
            "5": "SELECT conversation_id, COUNT(*) as message_count FROM messages WHERE timestamp > datetime('now', '-1 hour') GROUP BY conversation_id;",
            "6": "SELECT customer_id, customer_name, COUNT(*) as orders, SUM(total_price) as revenue FROM orders GROUP BY customer_id ORDER BY revenue DESC;",
            "7": "SELECT status, COUNT(*) as count, SUM(total_price) as total_revenue FROM orders GROUP BY status;",
            "8": "SELECT order_id, customer_name, total_price, created_at FROM orders ORDER BY total_price DESC LIMIT 10;",
            "9": "SELECT order_id, customer_name, total_price, status, created_at FROM orders WHERE DATE(created_at) = DATE('now') ORDER BY created_at DESC;",
            "10": "SELECT item_name, SUM(quantity) as times_ordered, SUM(subtotal) as total_revenue FROM order_items GROUP BY item_name ORDER BY times_ordered DESC;",
            "11": "SELECT AVG(item_count) as avg_items_per_order FROM (SELECT COUNT(*) as item_count FROM order_items GROUP BY order_id);",
            "12": "SELECT c.id, c.customer_name, COUNT(DISTINCT o.order_id) as order_count FROM conversations c LEFT JOIN orders o ON c.id = o.conversation_id GROUP BY c.id HAVING order_count > 0;",
            "13": "SELECT c.customer_name, COUNT(DISTINCT c.id) as conversations, COUNT(DISTINCT o.order_id) as orders, SUM(o.total_price) as total_spent FROM conversations c LEFT JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id ORDER BY total_spent DESC;"
        }
        sql = queries_map.get(query)
        if sql:
            query_tool = DatabaseQuery()
            print(f"\n📝 Executing query {query}...\n")
            results = query_tool.execute_query(sql)
            if results:
                print(f"✅ Found {len(results)} rows:\n")
                print(tabulate(results, tablefmt="grid"))
            else:
                print("⚠️  No results found.")
            print()


if __name__ == "__main__":
    run_custom_query()
