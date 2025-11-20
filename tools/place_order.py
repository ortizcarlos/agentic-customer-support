# place_order.py

from typing_extensions import TypedDict
from agents import function_tool
from datetime import datetime, timedelta
import uuid

from managers.order_manager import OrderManager, OrderStatus
from utils.constants import MENU_PRICES

# Initialize OrderManager for SQLite persistence
order_manager = OrderManager()

# Order item schema
class OrderItem(TypedDict):
    item_name: str
    quantity: int
    unit_price: float

# Order schema
class Order(TypedDict):
    order_id: str
    customer_id: str
    customer_name: str
    items: list[OrderItem]
    total_price: float
    status: str
    created_at: str

# Menu prices for validation
MENU_PRICES = {
    "Margherita Pizza": 12.00,
    "Pepperoni Pizza": 14.00,
    "Chicken Alfredo Pasta": 16.00,
    "Caesar Salad": 10.00,
    "Chocolate Lava Cake": 8.00
}

# Input schema for order items
class OrderItemInput(TypedDict):
    item_name: str
    quantity: int

@function_tool
def place_order(customer_name: str, items: list[OrderItemInput]) -> dict: 
    """
    Places a new order for a customer.

    Args:
        customer_name: The full name of the customer.
        items: A list of items to order, each containing item_name and quantity.

    Returns:
        A dictionary with order confirmation details including order_id, total price, and status.
    """

    # Validate inputs
    if not customer_name:
        return {
            "success": False,
            "message": "Customer  name is required."
        }

    if not items or len(items) == 0:
        return {
            "success": False,
            "message": "At least one item must be ordered."
        }

    # Process order items and calculate total
    order_items = []
    total_price = 0.0
    invalid_items = []

    for item in items:
        item_name = item.get("item_name", "").strip()
        quantity = item.get("quantity", 0)

        # Validate item name and quantity
        if not item_name:
            invalid_items.append("Empty item name provided")
            continue

        if not isinstance(quantity, int) or quantity <= 0:
            invalid_items.append(f"Invalid quantity for '{item_name}'. Quantity must be a positive integer.")
            continue

        # Check if item exists in menu
        if item_name not in MENU_PRICES:
            invalid_items.append(f"'{item_name}' is not available in the menu.")
            continue

        unit_price = MENU_PRICES[item_name]
        order_items.append({
            "item_name": item_name,
            "quantity": quantity,
            "unit_price": unit_price
        })
        total_price += unit_price * quantity

    # Return error if there were invalid items
    if invalid_items:
        return {
            "success": False,
            "message": "Order could not be placed due to the following issues:",
            "errors": invalid_items
        }

    # Create the order
    order_id = str(uuid.uuid4())[:8].upper()
    total_price_rounded = round(total_price, 2)

    # Estimate order ready time (15 minutes from now)
    estimated_ready_time = (datetime.now() + timedelta(minutes=15)).isoformat()

    # Save order to SQLite using OrderManager
    success = order_manager.create_order(
        order_id=order_id,
        customer_id="",  # Will be updated if customer provides ID later
        customer_name=customer_name,
        items=order_items,
        total_price=total_price_rounded,
        estimated_ready_time=estimated_ready_time,
        metadata={
            "source": "place_order_tool",
            "platform": "restaurant_assistant"
        }
    )

    if not success:
        return {
            "success": False,
            "message": "Failed to create order in database. Please try again."
        }

    return {
        "success": True,
        "order_id": order_id,
        "customer_name": customer_name,
        "items_ordered": [
            {
                "name": item["item_name"],
                "quantity": item["quantity"],
                "price_per_unit": item["unit_price"],
                "subtotal": round(item["unit_price"] * item["quantity"], 2)
            }
            for item in order_items
        ],
        "total_price": total_price_rounded,
        "status": OrderStatus.PENDING.value,
        "estimated_ready_time": estimated_ready_time,
        "message": f"Order {order_id} has been successfully placed! Your order will be ready in approximately 15 minutes."
    }
