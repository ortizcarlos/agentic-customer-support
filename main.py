# main.py

"""
Main entry point for the Agentic Customer Support System
"""

import asyncio
import os
import uuid
from dotenv import load_dotenv
from core.assistant import RestaurantAssistant
from managers.conversation_manager_factory import ConversationManagerFactory

# Load environment variables
load_dotenv()

# Global state
_conversation_manager = ConversationManagerFactory.create()
_user_id = 'Carlos'

async def main():
    """Main CLI loop for the restaurant assistant"""

    #Get conversation
    conversation_id = get_conversation(_user_id)

    # Initialize the assistant
    assistant = RestaurantAssistant(
        customer_name=_user_id,
        conversation_id=conversation_id
    )

    print("\n" + "="*70)
    print("🍽️  RESTAURANT CUSTOMER SUPPORT ASSISTANT")
    print("="*70)
    print("\nWelcome! I'm your restaurant assistant. Ask me about our menu,")
    print("place an order, or check your order status.")
    print("\nType 'exit' or 'quit' to end the conversation.\n")
    print("="*70 + "\n")

    while True:
        try:
            # Get user input
            user_input = input(f"{_user_id}: ").strip()

            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n👋 Thank you for visiting! Goodbye!\n")
                break

            # Skip empty inputs
            if not user_input:
                continue

            # Run the assistant
            response = await assistant.run(user_input)
            print(f"\nAssistant: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            print("Please try again.\n")

def get_conversation(customer_name:str):
    # Get or create conversation for this customer
    conversations = _conversation_manager.get_customer_conversations(customer_name)

    if conversations:
        # Use most recent conversation
        conversation_id = conversations[0]["id"]
        print(conversations)
    else:
        # Create new conversation
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        _conversation_manager.create_conversation(
            conversation_id,
            customer_id=customer_name,
            customer_name=customer_name,
        )
    
    return conversation_id

def run():
    """Wrapper to run the async main function"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
