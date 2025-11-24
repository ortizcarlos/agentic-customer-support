# restaurant_assistant.py

import uuid
from agents import Runner
from platform_agents.planner_agent import planner_agent
from managers.conversation_manager import ConversationManager



class RestaurantAssistant:
    """
    Entry point for the multi-agent restaurant assistant.
    Execution starts directly with the planner agent,
    which delegates to other agents based on user intent.
    Includes conversation history persistence with SQLite.
    """

    def __init__(self, conversation_id: str = None, customer_id: str = None,
                 customer_name: str = None):
        """
        Initialize the RestaurantAssistant with conversation management.

        Args:
            conversation_id: Optional conversation ID. If not provided, a new one is generated.
            customer_id: Optional customer ID for tracking.
            customer_name: Optional customer name for personalization.
            db_path: Path to the SQLite database file.
        """
        self.planner = planner_agent  # The orchestrator
        self.conversation_manager = ConversationManager()

        # Use provided conversation_id or generate a new one
        self.conversation_id = conversation_id
        self.customer_id = customer_id
        self.customer_name = customer_name

    async def run(self, message: str) -> str:
        """
        Sends a user message to the planner agent and returns the response.
        The planner will delegate to the menu or order-status agents.
        Stores conversation history in SQLite.

        Args:
            message: The user's message

        Returns:
            The agent's response
        """
        # Save user message to conversation history
        self.conversation_manager.add_message(
            self.conversation_id,
            sender_type="user",
            content=message
        )

        # Get conversation history for context
        history = self.conversation_manager.format_history_for_context(
            self.conversation_id,
            limit=10
        )

        print(f'History: {history}')

        # Prepare prompt with history context
        prompt = f"{history}\n\nNew Query: {message}"

        # Run the planner agent
        result = await Runner.run(
            planner_agent,
            prompt,
        )

        agent_response = result.final_output

        # Save agent response to conversation history
        self.conversation_manager.add_message(
            self.conversation_id,
            sender_type="agent",
            sender_name="RestaurantAssistant",
            content=agent_response
        )

        return agent_response

    def get_conversation_history(self, limit: int = 10) -> str:
        """
        Get formatted conversation history.

        Args:
            limit: Number of recent messages to retrieve

        Returns:
            Formatted conversation history
        """
        return self.conversation_manager.format_history_for_context(
            self.conversation_id,
            limit=limit
        )

    def get_customer_context(self) -> dict:
        """
        Get customer context for personalization.

        Returns:
            Dictionary with customer information
        """
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "conversation_id": self.conversation_id
        }
