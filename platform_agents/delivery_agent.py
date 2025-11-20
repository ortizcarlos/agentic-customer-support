# agent_order_status.py

from agents import Agent
from tools.get_order_status import get_order_status

# Create the specialized agent for order status inquiries
agent_order_status = Agent(
    name="OrderStatusAgent",
    instructions=(
        "You are an agent specialized in retrieving the status of customer orders. "
        "Your only responsibility is to receive an ID number (cedula) and use the "
        "`get_order_status` tool to obtain the order status. "
        "Do not invent information and do not answer questions outside of this domain."
    ),
    model="gpt-4.1-mini",
    tools=[get_order_status],
)
