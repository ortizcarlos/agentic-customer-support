# get_menu.py

from typing import TypedDict, Optional
from agents import function_tool

from utils.constants import MENU_PRICES

# Menu item schema
class MenuItem(TypedDict):
    name: str
    price: float
    ingredients: list[str]
    category: str

# Complete restaurant menu database
RESTAURANT_MENU: dict[str, MenuItem] = {
    "margherita_pizza": {
        "name": "Margherita Pizza",
        "price": 12.00,
        "ingredients": ["tomato sauce", "mozzarella", "basil"],
        "category": "Pizza"
    },
    "pepperoni_pizza": {
        "name": "Pepperoni Pizza",
        "price": 14.00,
        "ingredients": ["tomato sauce", "mozzarella", "pepperoni"],
        "category": "Pizza"
    },
    "chicken_alfredo_pasta": {
        "name": "Chicken Alfredo Pasta",
        "price": 16.00,
        "ingredients": ["fettuccine", "grilled chicken", "Alfredo sauce"],
        "category": "Pasta"
    },
    "caesar_salad": {
        "name": "Caesar Salad",
        "price": 10.00,
        "ingredients": ["romaine lettuce", "croutons", "parmesan", "Caesar dressing"],
        "category": "Salad"
    },
    "chocolate_lava_cake": {
        "name": "Chocolate Lava Cake",
        "price": 8.00,
        "ingredients": ["dark chocolate", "flour", "butter", "sugar"],
        "category": "Dessert"
    }
}

# Input schema for the tool
class GetMenuInput(TypedDict):
    category: Optional[str]

# Tool to retrieve the full menu or filter by category
@function_tool
def get_menu(category: Optional[str] = None):
    """
    Retrieves the restaurant menu. Can optionally filter by category.

    Args:
        category: Optional category to filter by (e.g., "Pizza", "Pasta", "Salad", "Dessert").
                 If not provided, returns the entire menu.

    Returns:
        A dictionary containing menu items with their details (name, price, ingredients, category).
    """
    if not category:
        # Return entire menu
        menu_items = list(RESTAURANT_MENU.values())
        return {
            "found": True,
            "category": "All",
            "items": menu_items,
            "total_items": len(menu_items)
        }

    # Filter menu by category (case-insensitive)
    filtered_items = [
        item for item in RESTAURANT_MENU.values()
        if item["category"].lower() == category.lower()
    ]

    if not filtered_items:
        return {
            "found": False,
            "category": category,
            "message": f"No items found in the '{category}' category. Available categories: Pizza, Pasta, Salad, Dessert."
        }

    return {
        "found": True,
        "category": category,
        "items": filtered_items,
        "total_items": len(filtered_items)
    }
