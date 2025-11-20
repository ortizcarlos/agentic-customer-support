# agent_planner.py

from agents import Agent
from .menu_agent import agent_menu
from .delivery_agent import agent_order_status
from .order_agent import agent_order

# Planner agent routes user requests to the correct specialized agent
planner_agent = Agent(
    name="PlannerAgent",
    instructions=(
        "You are the central planner agent for a restaurant multi-agent system. "
        "Your job is to analyze the user's request and decide which specialized agent "
        "should handle it.\n\n"
        "ROUTING RULES:\n"
        "- If the request is about menu items, ingredients, dishes, prices, or recommendations, "
        "route the task to the MenuAgent.\n"
        "- If the request is about placing a new order or ordering food, route the task to the OrderAgent.\n"
        "- If the request is about the status of an order, delivery time, or anything requiring "
        "a lookup by customer ID, route the task to the OrderStatusAgent.\n"
        "- Do NOT answer questions yourself. Always delegate.\n"
        "- Never invent information. Always choose the appropriate agent.\n"
        "- If the user request does not fall into any known category, ask them to clarify.\n"
    ),
    # Give the planner access to the specialized agents
    handoffs=[agent_menu, agent_order, agent_order_status],
)
