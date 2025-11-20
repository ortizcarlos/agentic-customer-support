# get_order_status.py

from typing import TypedDict
from agents import function_tool
from datetime import datetime

from managers.order_manager import OrderManager

# Initialize OrderManager for SQLite persistence
order_manager = OrderManager()

# Input schema for the tool
class OrderStatusInput(TypedDict):
    customer_id: str

# Tool using the latest OpenAI Agents SDK decorator
@function_tool
def get_order_status(customer_name: str) -> dict:
    """
    Retrieves the status of the most recent order using the customer's name.
    Returns the current status and estimated completion time.

    Args:
        customer_name: The customer's name

    Returns:
        Dictionary with order status information
    """
    # Get the most recent order for this customer from SQLite
    order = order_manager.get_customer_last_order(customer_name)

    if not order:
        return {
            "found": False,
            "message": f"No orders found for customer : {customer_name}"
        }

    # Calculate estimated time remaining
    if order.get("estimated_ready_time"):
        try:
            ready_time = datetime.fromisoformat(order["estimated_ready_time"])
            now = datetime.now()
            time_remaining = ready_time - now

            if time_remaining.total_seconds() > 0:
                minutes = int(time_remaining.total_seconds() / 60)
                estimated_time = f"{minutes} minutes" if minutes > 0 else "Ready now"
            else:
                estimated_time = "Ready for pickup"
        except:
            estimated_time = "Unknown"
    else:
        estimated_time = "Unknown"

    return {
        "found": True,
        "order_id": order["order_id"],
        "customer_name": order["customer_name"],
        "status": order["status"],
        "estimated_time": estimated_time,
        "total_price": order["total_price"],
        "items_count": len(order.get("items", []))
    }
