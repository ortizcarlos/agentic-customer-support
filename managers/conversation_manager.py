# conversation_manager.py

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

class ConversationManager:
    """
    Manages conversation history using SQLite for persistence.
    Stores messages, conversations, and customer context.
    """

    def __init__(self, db_path: str = "conversations.db"):
        """
        Initialize the conversation manager with SQLite database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    customer_name TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sender_type TEXT NOT NULL,
                    sender_name TEXT,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_id
                ON messages(conversation_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_id
                ON conversations(customer_id)
            """)

            conn.commit()

    def create_conversation(self, conversation_id: str, customer_id: str = None,
                           customer_name: str = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Create a new conversation.

        Args:
            conversation_id: Unique identifier for the conversation
            customer_id: Optional customer identifier
            customer_name: Optional customer name
            metadata: Optional additional metadata

        Returns:
            True if conversation was created, False if it already exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                metadata_json = json.dumps(metadata) if metadata else "{}"

                cursor.execute("""
                    INSERT INTO conversations
                    (id, customer_id, customer_name, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (conversation_id, customer_id, customer_name, now, now, metadata_json))

                conn.commit()
                return True
        except sqlite3.IntegrityError:
            print("Conversation already exists")
            return False

    def add_message(self, conversation_id: str, sender_type: str, content: str,
                   sender_name: str = None, metadata: Dict[str, Any] = None) -> int:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The conversation ID
            sender_type: Type of sender ('user', 'agent', 'system')
            content: The message content
            sender_name: Optional name of the sender (e.g., agent name)
            metadata: Optional additional metadata

        Returns:
            The message ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            metadata_json = json.dumps(metadata) if metadata else "{}"

            cursor.execute("""
                INSERT INTO messages
                (conversation_id, timestamp, sender_type, sender_name, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (conversation_id, timestamp, sender_type, sender_name,content, metadata_json))

            # Update conversation's updated_at timestamp
            now = datetime.now().isoformat()
            cursor.execute("""
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
            """, (now, conversation_id))

            conn.commit()
            return cursor.lastrowid

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation details.

        Args:
            conversation_id: The conversation ID

        Returns:
            Conversation details or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, customer_id, customer_name, created_at, updated_at, metadata
                FROM conversations
                WHERE id = ?
            """, (conversation_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "customer_id": row[1],
                "customer_name": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "metadata": json.loads(row[5]) if row[5] else {}
            }

    def get_conversation_messages(self, conversation_id: str, limit: int = None,
                                  offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all messages from a conversation.

        Args:
            conversation_id: The conversation ID
            limit: Optional limit on number of messages
            offset: Optional offset for pagination

        Returns:
            List of messages ordered by timestamp
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if limit:
                cursor.execute("""
                    SELECT id, conversation_id, timestamp, sender_type, sender_name, content, metadata
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ? OFFSET ?
                """, (conversation_id, limit, offset))
            else:
                cursor.execute("""
                    SELECT id, conversation_id, timestamp, sender_type, sender_name, content, metadata
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """, (conversation_id,))

            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "conversation_id": row[1],
                    "timestamp": row[2],
                    "sender_type": row[3],
                    "sender_name": row[4],
                    "content": row[5],
                    "metadata": json.loads(row[6]) if row[6] else {}
                }
                for row in rows
            ]

    def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent N messages from a conversation.

        Args:
            conversation_id: The conversation ID
            limit: Number of recent messages to retrieve

        Returns:
            List of recent messages (newest last)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, conversation_id, timestamp, sender_type, sender_name, content, metadata
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, limit))

            rows = cursor.fetchall()
            # Reverse to get oldest first
            messages = [
                {
                    "id": row[0],
                    "conversation_id": row[1],
                    "timestamp": row[2],
                    "sender_type": row[3],
                    "sender_name": row[4],
                    "content": row[5],
                    "metadata": json.loads(row[6]) if row[6] else {}
                }
                for row in reversed(rows)
            ]
            return messages

    def get_customer_conversations(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a specific customer.

        Args:
            customer_id: The customer ID

        Returns:
            List of conversations ordered by most recent first
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, customer_id, customer_name, created_at, updated_at, metadata
                FROM conversations
                WHERE customer_id = ?
                ORDER BY updated_at DESC
            """, (customer_id,))

            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "customer_id": row[1],
                    "customer_name": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {}
                }
                for row in rows
            ]

    def get_customer_last_order(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the last order placed by a customer.

        Args:
            customer_id: The customer ID

        Returns:
            Last order metadata or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT metadata
                FROM messages
                WHERE conversation_id IN (
                    SELECT id FROM conversations WHERE customer_id = ?
                )
                AND metadata LIKE '%order_id%'
                ORDER BY timestamp DESC
                LIMIT 1
            """, (customer_id,))

            row = cursor.fetchone()
            if not row:
                return None

            metadata = json.loads(row[0])
            return metadata.get("order_data")

    def format_history_for_context(self, conversation_id: str, limit: int = 10) -> str:
        """
        Format conversation history as a string for agent context.

        Args:
            conversation_id: The conversation ID
            limit: Number of recent messages to include

        Returns:
            Formatted conversation history
        """
        messages = self.get_recent_messages(conversation_id, limit)

        if not messages:
            return "No conversation history."

        history_text = "CONVERSATION HISTORY:\n"
        for msg in messages:
            sender = msg["sender_name"] or msg["sender_type"].upper()
            history_text += f"{sender}: {msg['content']}\n"

        return history_text

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: The conversation ID

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Delete messages first (due to foreign key)
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

            conn.commit()
            return cursor.total_changes > 0

    def clear_all_data(self):
        """
        Delete all conversations and messages. Use with caution!
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM conversations")
            conn.commit()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with conversation and message counts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM conversations")
            conversation_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(DISTINCT customer_id) FROM conversations
                WHERE customer_id IS NOT NULL
            """)
            customer_count = cursor.fetchone()[0]

            return {
                "total_conversations": conversation_count,
                "total_messages": message_count,
                "unique_customers": customer_count
            }
