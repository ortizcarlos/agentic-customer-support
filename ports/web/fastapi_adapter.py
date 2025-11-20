# fastapi_adapter.py

"""
FastAPI adapter - Simple REST API with single endpoint for messaging
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import uuid
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from assistant import RestaurantAssistant
from managers.conversation_manager import ConversationManager
from ports.web.models import UserMessage, AssistantResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
_conversation_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    global _conversation_manager
    logger.info("Starting Restaurant Assistant API...")
    _conversation_manager = ConversationManager()
    yield
    logger.info("Shutting down Restaurant Assistant API...")


# Create FastAPI app
app = FastAPI(
    title="Restaurant Customer Support API",
    description="Simple API for restaurant customer support",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/message",
    response_model=AssistantResponse,
    tags=["Messages"],
)
async def send_message(request: UserMessage):
    """
    Send a message and get a response from the assistant.

    Simply provide your name and message. The conversation history
    is automatically managed based on your name.

    - **customer_name**: Your name (required)
    - **content**: Your message (required)
    """
    try:
        customer_name = request.customer_name
        message = request.content

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

        # Create assistant for this request
        assistant = RestaurantAssistant(
            conversation_id=conversation_id,
            customer_id=customer_name,
            customer_name=customer_name,
        )

        # Run assistant
        response = await assistant.run(message)

        return AssistantResponse(
            message=response,
            conversation_id=conversation_id,
            timestamp=datetime.now(),
            success=True,
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return AssistantResponse(
            message=f"Error: {str(e)}",
            conversation_id="",
            timestamp=datetime.now(),
            success=False,
        )
