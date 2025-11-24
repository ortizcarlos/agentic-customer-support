# lambda_handler.py
"""
AWS Lambda handler for the Agentic Customer Support Platform.
Adapts the FastAPI application to work with AWS Lambda using Mangum.
"""

import os
from mangum import Mangum
from main import app

# Set environment variables for Lambda execution
os.environ.setdefault('ORDER_MANAGER_TYPE', 'dynamodb')
os.environ.setdefault('CONVERSATION_MANAGER_TYPE', 's3')

# Export Mangum handler for Lambda
# lifespan="off" disables FastAPI lifespan management which is not compatible with Lambda's request/response model
handler = Mangum(app, lifespan="off")
