# Project Structure

## Overview

```
agentic-customer-support/
├── agentic_customer_support/          # Main package
│   ├── __init__.py                    # Package initialization
│   ├── main.py                        # CLI entry point
│   │
│   ├── core/                          # Core orchestration
│   │   ├── __init__.py
│   │   └── assistant.py               # RestaurantAssistant class
│   │
│   ├── agents/                        # Specialized agents
│   │   ├── __init__.py
│   │   ├── planner_agent.py          # Router agent
│   │   ├── menu_agent.py             # Menu specialist
│   │   ├── order_agent.py            # Order placement specialist
│   │   └── delivery_agent.py         # Order status specialist
│   │
│   ├── tools/                         # Agent tools/functions
│   │   ├── __init__.py
│   │   ├── get_menu.py               # Retrieve menu items
│   │   ├── place_order.py            # Create orders
│   │   └── get_order_status.py       # Check order status
│   │
│   ├── managers/                      # Database management
│   │   ├── __init__.py
│   │   ├── conversation_manager.py   # Conversation persistence
│   │   └── order_manager.py          # Order persistence
│   │
│   ├── database/                      # Database utilities
│   │   ├── __init__.py
│   │   ├── viewer.py                 # Interactive data viewer
│   │   └── query.py                  # Query tool with templates
│   │
│   └── utils/                         # Shared utilities
│       ├── __init__.py
│       └── constants.py              # Shared constants
│
├── tests/                             # Unit tests
├── data/                              # Data files
│   └── conversations.db              # SQLite database
│
├── main.py                            # Root entry point
├── pyproject.toml                    # Project configuration
├── uv.lock                           # Dependency lock file
├── .env                              # Environment variables
├── .gitignore                        # Git exclusions
└── README.md                         # Project documentation

```

## Module Descriptions

### `core/`
**Core orchestration and main assistant**
- `RestaurantAssistant`: Main entry point that manages conversation flow and integrates all components

### `agents/`
**Specialized AI agents**
- `planner_agent`: Routes user requests to appropriate specialized agents
- `menu_agent`: Handles menu-related queries
- `order_agent`: Manages new order placement
- `delivery_agent`: Tracks order status

### `tools/`
**Functions available to agents**
- `get_menu()`: Retrieves menu items (with optional category filter)
- `place_order()`: Creates and saves new orders
- `get_order_status()`: Retrieves order status from database

### `managers/`
**Database management and persistence**
- `ConversationManager`: Handles conversation history in SQLite
- `OrderManager`: Handles order storage and retrieval in SQLite

### `database/`
**Database utilities and inspection tools**
- `DatabaseViewer`: Interactive CLI tool for viewing conversations and orders
- `DatabaseQuery`: Advanced SQL query interface with templates

### `utils/`
**Shared utilities and constants**
- `constants.py`: Menu prices, statuses, and other shared constants

## Running the Application

### From Root
```bash
python main.py
```

### From Package
```bash
python -m agentic_customer_support.main
```

### Using UV
```bash
uv run python main.py
uv run python -m agentic_customer_support.main
uv run agentic-customer-support  # If entry point is configured
```

## Database Tools

### View Data
```bash
python -m agentic_customer_support.database.viewer
```

### Query Data
```bash
python -m agentic_customer_support.database.query
```

## Import Examples

```python
# From root entry point
from agentic_customer_support.core.assistant import RestaurantAssistant
from agentic_customer_support.managers import ConversationManager, OrderManager
from agentic_customer_support.tools import get_menu, place_order, get_order_status
from agentic_customer_support.utils import MENU_PRICES
from agentic_customer_support.database import DatabaseViewer, DatabaseQuery
```

## Migration Notes

The project was refactored from a flat structure to a modular one:

### Old Files (Deprecated)
- `conversation_manager.py` → `managers/conversation_manager.py`
- `order_manager.py` → `managers/order_manager.py`
- `db_viewer.py` → `database/viewer.py`
- `db_query.py` → `database/query.py`
- `assistant.py` → `core/assistant.py`
- `tools/` → `agentic_customer_support/tools/`
- `platform_agents/` → `agentic_customer_support/agents/`

Old files can be safely deleted after verifying the new structure works.

## Benefits

✅ **Separation of Concerns**
- Core, agents, tools, and managers are logically separated
- Easier to maintain and extend

✅ **Scalability**
- Easy to add new agents
- Easy to add new tools
- Database structure scales with data

✅ **Testability**
- Each module can be tested independently
- Clear dependencies and imports

✅ **Code Organization**
- Related functionality grouped together
- Clear import paths
- Professional project structure
