# gradio_client.py

"""
Gradio client for Restaurant Assistant API
"""

import gradio as gr
import httpx
import asyncio
from typing import Optional
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30


class RestaurantAssistantClient:
    """Client for interacting with the Restaurant Assistant API"""

    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.chat_history = []

    async def send_message(self, customer_name: str, message: str) -> dict:
        """Send a message to the API and get response"""
        try:
            response = await self.client.post(
                f"{self.api_url}/message",
                json={
                    "customer_name": customer_name,
                    "content": message
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {
                "message": f"Connection error: {str(e)}",
                "conversation_id": "",
                "success": False
            }
        except httpx.HTTPStatusError as e:
            return {
                "message": f"API error: {str(e)}",
                "conversation_id": "",
                "success": False
            }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global client instance
_client = RestaurantAssistantClient()


async def process_message(
    customer_name: str,
    user_message: str,
    chat_history: list
) -> tuple[list, str]:
    """
    Process user message and update chat history

    Args:
        customer_name: Name of the customer
        user_message: Message from user
        chat_history: Previous chat history

    Returns:
        Updated chat history and status message
    """
    if not customer_name.strip():
        return chat_history, "❌ Please enter your name"

    if not user_message.strip():
        return chat_history, "❌ Please enter a message"

    # Add user message to history
    chat_history.append([user_message, None])

    # Send to API
    response = await _client.send_message(customer_name, user_message)

    if response.get("success"):
        assistant_message = response.get("message", "No response")
        chat_history[-1][1] = assistant_message
        status = f"✅ Message sent (Conversation: {response.get('conversation_id', '')[:8]})"
    else:
        error_msg = response.get("message", "Unknown error")
        chat_history[-1][1] = f"🚫 {error_msg}"
        status = "❌ Error processing message"

    return chat_history, status


def create_interface():
    """Create and return the Gradio interface"""

    with gr.Blocks(
        title="Restaurant Assistant",
        theme=gr.themes.Soft(),
        css="""
        .container { max-width: 900px; margin: auto; }
        .chat-container { height: 500px; overflow-y: auto; }
        .header { text-align: center; margin-bottom: 20px; }
        .input-section { gap: 10px; }
        .status-message {
            font-size: 12px;
            margin-top: 10px;
            padding: 8px;
            border-radius: 4px;
        }
        .section-title {
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #333;
        }
        """
    ) as interface:

        # Header
        gr.HTML("""
        <div class="header">
            <h1>🍽️ Restaurant Customer Support</h1>
            <p>Chat with our AI assistant about our menu, orders, and more</p>
        </div>
        """)

        # Customer Info Section
        gr.HTML('<div class="section-title">👤 Customer Info</div>')
        customer_name = gr.Textbox(
            label="Your Name",
            placeholder="Enter your name",
            interactive=True,
            scale=1
        )

        # Chat interface
        gr.HTML('<div class="section-title">💬 Chat History</div>')
        chatbot = gr.Chatbot(
            height=400,
            show_copy_button=True,
            scale=1
        )

        # Send Message Section
        gr.HTML('<div class="section-title">✉️ Send Message</div>')
        with gr.Row():
            message_input = gr.Textbox(
                label="Message",
                placeholder="Ask about our menu, place an order, or check status...",
                interactive=True,
                scale=4
            )
            send_btn = gr.Button(
                "Send",
                variant="primary",
                scale=1
            )

        status_output = gr.Markdown(
            value="Ready to chat!"
        )

        # Setup event handlers
        async def on_send(name: str, msg: str, history: list):
            updated_history, status = await process_message(name, msg, history)
            return updated_history, "", status

        send_btn.click(
            on_send,
            inputs=[customer_name, message_input, chatbot],
            outputs=[chatbot, message_input, status_output]
        )

        # Allow sending with Enter key
        message_input.submit(
            on_send,
            inputs=[customer_name, message_input, chatbot],
            outputs=[chatbot, message_input, status_output]
        )

        # Example section
        gr.HTML("""
        <details>
            <summary style="cursor: pointer; font-weight: bold;">💡 Example Questions</summary>
            <ul>
                <li>"What pizzas do you have?"</li>
                <li>"I want to order a Margherita Pizza"</li>
                <li>"What's the status of my order?"</li>
                <li>"Do you have any salads?"</li>
                <li>"What are your prices?"</li>
            </ul>
        </details>
        """)

        # Footer
        gr.HTML("""
        <hr>
        <p style="text-align: center; color: #888; font-size: 12px;">
            🔗 API running on http://localhost:8000<br>
            💬 Conversations are saved and can be retrieved by name
        </p>
        """)

    return interface


def launch(
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
    share: bool = False,
    debug: bool = True,
):
    """
    Launch the Gradio interface

    Args:
        server_name: Server host
        server_port: Server port
        share: Whether to create a public link
        debug: Enable debug mode
    """
    print("\n" + "=" * 70)
    print("🍽️  RESTAURANT ASSISTANT - GRADIO UI")
    print("=" * 70)
    print(f"\n🌐 Interface: http://{server_name}:{server_port}")
    print(f"📡 API: http://localhost:8000")
    print("\n" + "=" * 70 + "\n")

    interface = create_interface()
    interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        debug=debug,
    )


if __name__ == "__main__":
    launch()
