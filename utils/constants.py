# constants.py

"""Shared constants used across the application"""

# Menu prices - used for validation and calculations
MENU_PRICES = {
    "Margherita Pizza": 12.00,
    "Pepperoni Pizza": 14.00,
    "Chicken Alfredo Pasta": 16.00,
    "Caesar Salad": 10.00,
    "Chocolate Lava Cake": 8.00
}

# Order statuses
ORDER_STATUSES = [
    "Pending",
    "Confirmed",
    "Being prepared",
    "Ready for pickup",
    "Completed",
    "Cancelled"
]

# Database configuration
DEFAULT_DB_PATH = "conversations.db"

# Agent models
DEFAULT_MODEL = "gpt-4.1-mini"
