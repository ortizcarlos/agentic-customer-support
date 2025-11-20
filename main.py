# main.py

"""
Main entry point for the Agentic Customer Support System
"""

import asyncio
import os
from dotenv import load_dotenv
from core.assistant import RestaurantAssistant

# Load environment variables
load_dotenv()


async def main():
    """Main CLI loop for the restaurant assistant"""

    # Initialize the assistant
    assistant = RestaurantAssistant(
        customer_name="User",  # Can be updated with user input
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
            user_input = input("You: ").strip()

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


def run():
    """Wrapper to run the async main function"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
