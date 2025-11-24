import boto3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


class ConversationManagerS3:
    """
    Manages conversation history using AWS S3 for persistence.
    Stores messages and conversations as JSON files in S3.
    """

    def __init__(self, bucket_name: str, aws_region: str = "us-east-1",
                 prefix: str = "conversations/"):
        """
        Initialize the conversation manager with S3.

        Args:
            bucket_name: Name of the S3 bucket
            aws_region: AWS region
            prefix: S3 prefix/folder for storing conversations
        """
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.s3_client = boto3.client('s3', region_name=aws_region)

    def _get_conversation_key(self, conversation_id: str) -> str:
        """Get S3 key for conversation metadata."""
        return f"{self.prefix}{conversation_id}/metadata.json"

    def _get_messages_key(self, conversation_id: str) -> str:
        """Get S3 key for conversation messages."""
        return f"{self.prefix}{conversation_id}/messages.json"

    def _load_json_from_s3(self, key: str) -> Optional[Dict[str, Any]]:
        """Load and parse JSON file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except self.s3_client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            print(f"Error loading {key}: {str(e)}")
            return None

    def _save_json_to_s3(self, key: str, data: Dict[str, Any]) -> bool:
        """Save JSON data to S3."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            print(f"Error saving to {key}: {str(e)}")
            return False

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
        key = self._get_conversation_key(conversation_id)

        # Check if conversation already exists
        if self._load_json_from_s3(key) is not None:
            print("Conversation already exists")
            return False

        now = datetime.now().isoformat()
        conversation_data = {
            "id": conversation_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {}
        }

        # Create empty messages file
        messages_key = self._get_messages_key(conversation_id)
        self._save_json_to_s3(messages_key, {"messages": []})

        return self._save_json_to_s3(key, conversation_data)

    def add_message(self, conversation_id: str, sender_type: str, content: str,
                   sender_name: str = None, metadata: Dict[str, Any] = None) -> str:
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
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Load existing messages
        messages_key = self._get_messages_key(conversation_id)
        messages_data = self._load_json_from_s3(messages_key)

        if messages_data is None:
            messages_data = {"messages": []}

        # Add new message
        message = {
            "id": message_id,
            "conversation_id": conversation_id,
            "timestamp": timestamp,
            "sender_type": sender_type,
            "sender_name": sender_name,
            "content": content,
            "metadata": metadata or {}
        }
        messages_data["messages"].append(message)

        # Save messages
        self._save_json_to_s3(messages_key, messages_data)

        # Update conversation's updated_at timestamp
        conv_key = self._get_conversation_key(conversation_id)
        conversation = self._load_json_from_s3(conv_key)
        if conversation:
            conversation["updated_at"] = datetime.now().isoformat()
            self._save_json_to_s3(conv_key, conversation)

        return message_id

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation details.

        Args:
            conversation_id: The conversation ID

        Returns:
            Conversation details or None if not found
        """
        key = self._get_conversation_key(conversation_id)
        return self._load_json_from_s3(key)

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
        messages_key = self._get_messages_key(conversation_id)
        messages_data = self._load_json_from_s3(messages_key)

        if messages_data is None:
            return []

        messages = messages_data.get("messages", [])

        # Apply offset and limit
        if offset > 0:
            messages = messages[offset:]
        if limit:
            messages = messages[:limit]

        return messages

    def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent N messages from a conversation.

        Args:
            conversation_id: The conversation ID
            limit: Number of recent messages to retrieve

        Returns:
            List of recent messages (newest last)
        """
        messages_key = self._get_messages_key(conversation_id)
        messages_data = self._load_json_from_s3(messages_key)

        if messages_data is None:
            return []

        all_messages = messages_data.get("messages", [])
        # Get last N messages (newest last)
        return all_messages[-limit:] if len(all_messages) > 0 else []

    def get_customer_conversations(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a specific customer.

        Args:
            customer_id: The customer ID

        Returns:
            List of conversations ordered by most recent first
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

            conversations = []
            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    key = obj['Key']
                    # Only process metadata.json files
                    if key.endswith('metadata.json'):
                        conv_data = self._load_json_from_s3(key)
                        if conv_data and conv_data.get('customer_id') == customer_id:
                            conversations.append(conv_data)

            # Sort by updated_at descending
            conversations.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            return conversations

        except Exception as e:
            print(f"Error listing conversations: {str(e)}")
            return []

    def get_customer_last_order(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the last order placed by a customer.

        Args:
            customer_id: The customer ID

        Returns:
            Last order metadata or None
        """
        conversations = self.get_customer_conversations(customer_id)

        # Search messages in all conversations for the most recent order
        for conversation in conversations:
            messages_key = self._get_messages_key(conversation['id'])
            messages_data = self._load_json_from_s3(messages_key)

            if messages_data is None:
                continue

            all_messages = messages_data.get("messages", [])

            # Search messages in reverse order (newest first)
            for message in reversed(all_messages):
                if 'order_id' in message.get('metadata', {}):
                    return message.get('metadata', {}).get('order_data')

        return None

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
            sender = msg.get("sender_name") or msg.get("sender_type", "UNKNOWN").upper()
            history_text += f"{sender}: {msg.get('content', '')}\n"

        return history_text

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: The conversation ID

        Returns:
            True if deleted, False if not found
        """
        try:
            # Check if conversation exists
            conv_key = self._get_conversation_key(conversation_id)
            if self._load_json_from_s3(conv_key) is None:
                return False

            # Delete metadata file
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=conv_key)

            # Delete messages file
            messages_key = self._get_messages_key(conversation_id)
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=messages_key)

            return True
        except Exception as e:
            print(f"Error deleting conversation: {str(e)}")
            return False

    def clear_all_data(self):
        """
        Delete all conversations and messages. Use with caution!
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=obj['Key'])

        except Exception as e:
            print(f"Error clearing data: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get S3-based statistics.

        Returns:
            Dictionary with conversation and message counts
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

            conversation_count = 0
            message_count = 0
            unique_customers = set()

            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('metadata.json'):
                        conversation_count += 1
                        conv_data = self._load_json_from_s3(key)
                        if conv_data and conv_data.get('customer_id'):
                            unique_customers.add(conv_data['customer_id'])

                    elif key.endswith('messages.json'):
                        messages_data = self._load_json_from_s3(key)
                        if messages_data:
                            message_count += len(messages_data.get("messages", []))

            return {
                "total_conversations": conversation_count,
                "total_messages": message_count,
                "unique_customers": len(unique_customers)
            }

        except Exception as e:
            print(f"Error getting statistics: {str(e)}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "unique_customers": 0
            }
