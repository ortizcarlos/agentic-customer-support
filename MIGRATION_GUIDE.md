# Migration Guide - New Structure

## Summary

The project has been successfully refactored from a flat structure to a modular, organized package structure. All functionality remains the same, but the code is now better organized and more maintainable.

## What Changed

### Directory Structure

**Before:**
```
agentic-customer-support/
├── assistant.py
├── conversation_manager.py
├── order_manager.py
├── db_viewer.py
├── db_query.py
├── main.py
├── platform_agents/
│   ├── planner_agent.py
│   ├── menu_agent.py
│   ├── order_agent.py
│   └── delivery_agent.py
└── tools/
    ├── get_menu.py
    ├── place_order.py
    └── tool_repository.py
```

**After:**
```
agentic-customer-support/
├── agentic_customer_support/
│   ├── core/
│   │   └── assistant.py
│   ├── agents/
│   │   ├── planner_agent.py
│   │   ├── menu_agent.py
│   │   ├── order_agent.py
│   │   └── delivery_agent.py
│   ├── tools/
│   │   ├── get_menu.py
│   │   ├── place_order.py
│   │   └── get_order_status.py
│   ├── managers/
│   │   ├── conversation_manager.py
│   │   └── order_manager.py
│   ├── database/
│   │   ├── viewer.py
│   │   └── query.py
│   ├── utils/
│   │   └── constants.py
│   └── main.py
└── main.py (wrapper)
```

### Old Files

The following files can be safely deleted (they've been copied to new locations with updated imports):

```bash
rm assistant.py
rm conversation_manager.py
rm order_manager.py
rm db_viewer.py
rm db_query.py
rm -rf platform_agents/
rm -rf tools/
```

Keep `main.py` at root (it's now a wrapper).

### Import Changes

#### Old Imports (Deprecated)
```python
from assistant import RestaurantAssistant
from conversation_manager import ConversationManager
from order_manager import OrderManager
from db_viewer import DatabaseViewer
from db_query import DatabaseQuery
from tools.get_menu import get_menu
from platform_agents.planner_agent import planner_agent
```

#### New Imports (Use These)
```python
from agentic_customer_support.core.assistant import RestaurantAssistant
from agentic_customer_support.managers import ConversationManager, OrderManager
from agentic_customer_support.database import DatabaseViewer, DatabaseQuery
from agentic_customer_support.tools import get_menu, get_order_status, place_order
from agentic_customer_support.agents import planner_agent
from agentic_customer_support.utils import MENU_PRICES
```

## How to Run

### Development
```bash
# Ensure dependencies are installed
uv sync

# Run the application
python main.py

# Or directly
python -m agentic_customer_support.main
```

### Using UV
```bash
# Run directly
uv run python main.py

# Or via module
uv run python -m agentic_customer_support.main
```

### Database Tools
```bash
# View database contents
python -m agentic_customer_support.database.viewer

# Query database
python -m agentic_customer_support.database.query
```

## Configuration

No changes needed to:
- `.env` file - stays in root
- `conversations.db` - stays in root (or in `data/` if you prefer)
- `pyproject.toml` - no changes needed, UV auto-discovers the package

## What Stayed the Same

✅ All functionality is identical
✅ Database schema unchanged
✅ Agent behavior unchanged
✅ Tool implementations unchanged
✅ All configurations work the same

## Benefits of New Structure

1. **Better Organization** - Related code grouped logically
2. **Easier Testing** - Each module can be tested independently
3. **Scalability** - Easy to add new agents, tools, or managers
4. **Professional** - Follows Python packaging best practices
5. **Easier Onboarding** - Clear structure for new developers
6. **Better IDE Support** - IDEs better understand package imports

## Cleanup (Optional)

Once you've verified everything works, you can delete the old files:

```bash
# Delete old root-level files
rm assistant.py
rm conversation_manager.py
rm order_manager.py
rm db_viewer.py
rm db_query.py

# Delete old directories
rm -rf platform_agents
rm -rf tools

# The old main.py is now a wrapper - keep it
```

## Verification Checklist

- [ ] All files exist in `agentic_customer_support/` directory
- [ ] `python main.py` runs without import errors
- [ ] Database tools work: `python -m agentic_customer_support.database.viewer`
- [ ] Conversation history still saved correctly
- [ ] Orders still saved correctly
- [ ] All agents respond correctly
- [ ] Import paths updated in any external scripts

## Support

If you have any import issues, check:
1. Are you using the new import paths?
2. Is the file in the correct subdirectory?
3. Does the `__init__.py` export the symbol?
4. Is `agentic_customer_support/` a valid Python package?

## Next Steps

1. Delete old files after verification
2. Update any external integrations to use new import paths
3. Consider adding more agents or tools using the new modular structure
4. Set up proper testing with the new package structure
