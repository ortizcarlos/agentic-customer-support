# agent_menu.py

from agents import Agent
from tools.get_menu import get_menu

# Create the specialized agent for menu inquiries
agent_menu = Agent(
    name="MenuAgent",
    instructions=(
        "You are a restaurant menu assistant. Your job is to answer customer questions "
        "about dishes, ingredients, prices, recommendations, dietary options, and menu details. "
        "Only answer questions related to the menu.\n\n"
        "Use the get_menu tool to retrieve menu items. You can filter by category (Pizza, Pasta, Salad, Dessert) "
        "or get the entire menu. Always provide helpful information about dishes, including ingredients and prices."
    ),
    model="gpt-4.1-mini",
    tools=[get_menu],  # Use the get_menu tool to dynamically fetch menu data
)
