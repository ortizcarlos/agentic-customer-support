import os
from typing import Union
from managers.conversation_manager import ConversationManager
from managers.conversation_manager_s3 import ConversationManagerS3


class ConversationManagerFactory:
    """
    Factory pattern to dynamically instantiate the appropriate conversation manager
    based on environment variables.
    """

    @staticmethod
    def create() -> Union[ConversationManager, ConversationManagerS3]:
        """
        Create and return the appropriate conversation manager instance.

        Environment variables:
        - CONVERSATION_STORAGE: "sqlite" (default) or "s3"
        - SQLITE_DB_PATH: Path to SQLite database (default: "conversations.db")
        - S3_BUCKET_NAME: S3 bucket name (required if using S3)
        - S3_REGION: AWS region (default: "us-east-1")
        - S3_PREFIX: S3 prefix for conversations (default: "conversations/")

        Returns:
            ConversationManager or ConversationManagerS3 instance

        Raises:
            ValueError: If S3 is selected but S3_BUCKET_NAME is not set
        """
        storage_type = os.getenv('CONVERSATION_STORAGE', 'sqlite').lower()

        if storage_type == 's3':
            bucket_name = os.getenv('S3_BUCKET_NAME')
            if not bucket_name:
                raise ValueError(
                    "S3_BUCKET_NAME environment variable is required when "
                    "CONVERSATION_STORAGE='s3'"
                )

            region = os.getenv('S3_REGION', 'us-east-1')
            prefix = os.getenv('S3_PREFIX', 'conversations/')

            return ConversationManagerS3(
                bucket_name=bucket_name,
                aws_region=region,
                prefix=prefix
            )

        elif storage_type == 'sqlite':
            db_path = os.getenv('SQLITE_DB_PATH', 'conversations.db')
            return ConversationManager(db_path=db_path)

        else:
            raise ValueError(
                f"Unknown storage type: {storage_type}. "
                "Must be 'sqlite' or 's3'"
            )
