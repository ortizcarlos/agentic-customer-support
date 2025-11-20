# Restaurant Assistant API Documentation

## Overview

The Restaurant Customer Support System now includes a FastAPI REST API interface available through `/ports/in`. This allows you to interact with the restaurant assistant via HTTP requests.

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Start the API Server

```bash
python api.py
```

Or with UV:

```bash
uv run python api.py
```

The API will be available at `http://localhost:8000`

### 3. Access API Documentation

- **Interactive Swagger UI**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## API Endpoints

### Health & Status

#### Health Check
```
GET /health
```
Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-20T17:30:00"
}
```

#### Get Status
```
GET /status
```
Get detailed API status and statistics.

**Response:**
```json
{
  "status": "running",
  "active_conversations": 5,
  "timestamp": "2025-11-20T17:30:00"
}
```

---

### Conversations

#### Create Conversation
```
POST /conversations
```
Start a new conversation with the restaurant assistant.

**Request:**
```json
{
  "customer_name": "Juan García",
  "customer_id": "123456789",
  "conversation_id": null
}
```

**Response:**
```json
{
  "conversation_id": "conv_a1b2c3d4",
  "customer_name": "Juan García",
  "customer_id": "123456789",
  "created_at": "2025-11-20T17:30:00"
}
```

#### Send Message
```
POST /conversations/{conversation_id}/messages
```
Send a message to the assistant in a conversation.

**Request:**
```json
{
  "content": "What pizzas do you have?",
  "customer_id": "123456789",
  "customer_name": "Juan García",
  "conversation_id": "conv_a1b2c3d4"
}
```

**Response:**
```json
{
  "message": "We have Margherita Pizza ($12) and Pepperoni Pizza ($14)...",
  "conversation_id": "conv_a1b2c3d4",
  "timestamp": "2025-11-20T17:30:00",
  "success": true
}
```

#### Get Conversation Details
```
GET /conversations/{conversation_id}
```
Get details about a specific conversation.

**Response:**
```json
{
  "id": "conv_a1b2c3d4",
  "customer_id": "123456789",
  "customer_name": "Juan García",
  "created_at": "2025-11-20T17:30:00",
  "updated_at": "2025-11-20T17:35:00",
  "metadata": {}
}
```

#### Get Conversation History
```
GET /conversations/{conversation_id}/history?limit=20
```
Get message history for a conversation.

**Query Parameters:**
- `limit` (int, default: 20) - Maximum number of messages to retrieve

**Response:**
```json
{
  "conversation_id": "conv_a1b2c3d4",
  "messages": [
    {
      "id": 1,
      "timestamp": "2025-11-20T17:30:00",
      "sender_type": "user",
      "sender_name": null,
      "content": "What pizzas do you have?"
    },
    {
      "id": 2,
      "timestamp": "2025-11-20T17:30:05",
      "sender_type": "agent",
      "sender_name": "RestaurantAssistant",
      "content": "We have Margherita Pizza ($12) and Pepperoni Pizza ($14)..."
    }
  ],
  "total_messages": 2
}
```

---

### Customers

#### Get Customer Conversations
```
GET /customers/{customer_id}/conversations
```
Get all conversations for a specific customer.

**Response:**
```json
{
  "customer_id": "123456789",
  "total_conversations": 3,
  "conversations": [
    {
      "id": "conv_a1b2c3d4",
      "customer_name": "Juan García",
      "created_at": "2025-11-20T17:30:00",
      "updated_at": "2025-11-20T17:35:00"
    }
  ]
}
```

#### Get Customer Orders
```
GET /customers/{customer_id}/orders
```
Get all orders for a specific customer.

**Response:**
```json
{
  "customer_id": "123456789",
  "total_orders": 2,
  "orders": [
    {
      "order_id": "ORD12345",
      "customer_name": "Juan García",
      "total_price": 34.00,
      "status": "Completed",
      "created_at": "2025-11-20T16:00:00"
    }
  ]
}
```

---

### Orders

#### Get Order Details
```
GET /orders/{order_id}
```
Get details about a specific order.

**Response:**
```json
{
  "order_id": "ORD12345",
  "customer_id": "123456789",
  "customer_name": "Juan García",
  "total_price": 34.00,
  "status": "Ready for pickup",
  "created_at": "2025-11-20T16:00:00",
  "items": [
    {
      "item_name": "Margherita Pizza",
      "quantity": 2,
      "unit_price": 12.00,
      "subtotal": 24.00
    }
  ]
}
```

---

### Statistics

#### Get System Statistics
```
GET /statistics
```
Get overall statistics about conversations and orders.

**Response:**
```json
{
  "conversations": {
    "total_conversations": 10,
    "total_messages": 150,
    "unique_customers": 8
  },
  "orders": {
    "total_orders": 20,
    "total_revenue": 450.50,
    "status_breakdown": {
      "Pending": 2,
      "Completed": 18
    },
    "unique_customers": 8
  },
  "active_assistants": 5,
  "timestamp": "2025-11-20T17:30:00"
}
```

---

## Configuration

Configure the API via environment variables in `.env`:

```env
# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_LOG_LEVEL=info

# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///conversations.db
```

Or pass them when running:

```bash
API_PORT=3000 API_RELOAD=false python api.py
```

---

## Usage Examples

### Using cURL

#### Create Conversation
```bash
curl -X POST "http://localhost:8000/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Juan García",
    "customer_id": "123456789"
  }'
```

#### Send Message
```bash
curl -X POST "http://localhost:8000/conversations/conv_a1b2c3d4/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I want to order a pizza"
  }'
```

#### Get History
```bash
curl "http://localhost:8000/conversations/conv_a1b2c3d4/history?limit=10"
```

### Using Python

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Create conversation
        response = await client.post(
            "http://localhost:8000/conversations",
            json={
                "customer_name": "Juan García",
                "customer_id": "123456789"
            }
        )
        conversation = response.json()
        conv_id = conversation["conversation_id"]

        # Send message
        response = await client.post(
            f"http://localhost:8000/conversations/{conv_id}/messages",
            json={"content": "What pizzas do you have?"}
        )
        print(response.json())

asyncio.run(main())
```

### Using JavaScript/Fetch

```javascript
// Create conversation
const createResponse = await fetch("http://localhost:8000/conversations", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    customer_name: "Juan García",
    customer_id: "123456789"
  })
});

const conversation = await createResponse.json();
const convId = conversation.conversation_id;

// Send message
const messageResponse = await fetch(
  `http://localhost:8000/conversations/${convId}/messages`,
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content: "What pizzas do you have?"
    })
  }
);

const response = await messageResponse.json();
console.log(response.message);
```

---

## Error Handling

All errors return appropriate HTTP status codes:

- **200 OK** - Request successful
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error

**Error Response Format:**
```json
{
  "error": "Conversation not found",
  "detail": "The specified conversation ID does not exist",
  "timestamp": "2025-11-20T17:30:00"
}
```

---

## Architecture

The API is built using **Hexagonal Architecture (Ports & Adapters)**:

```
ports/
├── in/                          # Input ports (REST API)
│   ├── fastapi_adapter.py      # FastAPI implementation
│   ├── models.py               # Request/Response models
│   └── api.py                  # Server configuration
└── out/                         # (Future) Output ports
```

This pattern allows:
- ✅ Easy API changes without affecting core logic
- ✅ Multiple interfaces (REST, GraphQL, WebSocket, etc.)
- ✅ Clean separation of concerns
- ✅ Easy testing and mocking

---

## Running Alongside CLI

You can run both the CLI and API simultaneously:

```bash
# Terminal 1: Run CLI
python main.py

# Terminal 2: Run API
python api.py
```

Both share the same database and managers, so conversations created in one are accessible in the other.

---

## Next Steps

- Implement WebSocket for real-time conversations
- Add authentication/authorization
- Create `/ports/out` for external integrations
- Add GraphQL interface
- Implement conversation streaming
- Add rate limiting
- Deploy to production (Docker, Kubernetes, etc.)
