# Order Manager - SQLite & DynamoDB Implementation

This module provides two implementations of order management for the agentic customer support platform:
- **OrderManager**: Local SQLite-based storage (development)
- **OrderManagerDynamoDB**: Cloud-native AWS DynamoDB storage (production)

Both implementations share the same interface, allowing seamless switching between local and cloud deployments.

## Features

### OrderManager (SQLite)
- Local file-based database storage
- Suitable for development and testing
- No external dependencies beyond Python stdlib (sqlite3)
- Uses indexed queries for efficient lookups

### OrderManagerDynamoDB
- Fully managed AWS DynamoDB storage
- Horizontally scalable for production workloads
- Global Secondary Indexes for fast queries by customer, status, or customer name
- Automatic schema management

## Installation

### SQLite (Built-in)
No additional installation required. SQLite is included in Python.

### DynamoDB
Install the boto3 AWS SDK:
```bash
pip install boto3
```

## Quick Start

### Using SQLite (Default)
```python
from managers import OrderManager

# Create manager (auto-initializes database)
order_manager = OrderManager(db_path="conversations.db")

# Create an order
order_manager.create_order(
    order_id="ORD-001",
    customer_id="CUST-001",
    customer_name="John Doe",
    items=[
        {"item_name": "Coffee", "quantity": 2, "unit_price": 3.50},
        {"item_name": "Sandwich", "quantity": 1, "unit_price": 8.99}
    ],
    total_price=16.99,
    estimated_ready_time="2024-11-22T15:30:00",
    metadata={"table": "5"}
)

# Get order
order = order_manager.get_order("ORD-001")
print(order_manager.format_order_summary("ORD-001"))
```

### Using DynamoDB
```python
from managers import OrderManagerDynamoDB

# Create manager (auto-initializes DynamoDB table)
order_manager = OrderManagerDynamoDB(
    table_name="orders",
    region="us-east-1"
)

# Create an order (same API as SQLite)
order_manager.create_order(
    order_id="ORD-001",
    customer_id="CUST-001",
    customer_name="John Doe",
    items=[
        {"item_name": "Coffee", "quantity": 2, "unit_price": 3.50},
        {"item_name": "Sandwich", "quantity": 1, "unit_price": 8.99}
    ],
    total_price=16.99,
    estimated_ready_time="2024-11-22T15:30:00",
    metadata={"table": "5"}
)

# Get order (identical API)
order = order_manager.get_order("ORD-001")
print(order_manager.format_order_summary("ORD-001"))
```

## Using the Factory Pattern

The `OrderManagerFactory` simplifies switching between implementations:

```python
from managers.order_manager_factory import OrderManagerFactory, OrderManagerType

# Create SQLite manager
sqlite_manager = OrderManagerFactory.create(
    OrderManagerType.SQLITE,
    db_path="conversations.db"
)

# Create DynamoDB manager
dynamodb_manager = OrderManagerFactory.create(
    OrderManagerType.DYNAMODB,
    table_name="orders",
    region="us-east-1"
)
```

### Using Environment Variables

Configure the manager type via environment variable:

```python
import os

# Set in environment
os.environ['ORDER_MANAGER_TYPE'] = 'dynamodb'

# Create from environment
from managers.order_manager_factory import OrderManagerFactory

manager = OrderManagerFactory.create_from_env(region='us-west-2')
```

Or via shell:
```bash
export ORDER_MANAGER_TYPE=dynamodb
export AWS_REGION=us-east-1
python your_app.py
```

## API Reference

Both managers implement the same interface:

### Core Methods

#### `create_order(order_id, customer_id, customer_name, items, total_price, conversation_id=None, estimated_ready_time=None, metadata=None) -> bool`
Creates a new order.

**Parameters:**
- `order_id` (str): Unique order identifier
- `customer_id` (str): Customer ID
- `customer_name` (str): Customer name
- `items` (List[Dict]): Items in format `[{"item_name": str, "quantity": int, "unit_price": float}]`
- `total_price` (float): Total order price
- `conversation_id` (str, optional): Associated conversation ID
- `estimated_ready_time` (str, optional): ISO format timestamp
- `metadata` (Dict, optional): Custom metadata

**Returns:** `True` if successful, `False` otherwise

#### `get_order(order_id) -> Optional[Dict]`
Retrieves a complete order with all items.

**Returns:** Order dict or `None` if not found

#### `get_customer_orders(customer_name, limit=None, status=None) -> List[Dict]`
Gets all orders for a customer, ordered by most recent first.

**Parameters:**
- `customer_name` (str): Customer name
- `limit` (int, optional): Maximum number of orders to return
- `status` (str, optional): Filter by OrderStatus

**Returns:** List of order dicts

#### `get_customer_last_order(customer_id) -> Optional[Dict]`
Gets the most recent order from a customer.

**Returns:** Order dict or `None`

#### `update_order_status(order_id, status) -> bool`
Updates an order's status.

**Parameters:**
- `order_id` (str): Order ID
- `status` (OrderStatus): New status (use enum value)

**Returns:** `True` if successful

#### `update_order_ready_time(order_id, estimated_ready_time) -> bool`
Updates the estimated ready time.

**Parameters:**
- `order_id` (str): Order ID
- `estimated_ready_time` (str): ISO format timestamp

**Returns:** `True` if successful

#### `get_orders_by_status(status, limit=None) -> List[Dict]`
Gets all orders with a specific status.

**Parameters:**
- `status` (OrderStatus): Status filter
- `limit` (int, optional): Maximum results

**Returns:** List of order dicts

#### `get_order_statistics() -> Dict`
Gets aggregated order statistics.

**Returns:** Dict with `total_orders`, `total_revenue`, `status_breakdown`, `unique_customers`

#### `delete_order(order_id) -> bool`
Deletes an order.

**Returns:** `True` if successful

#### `clear_all_orders()`
Deletes all orders. **Use with caution!**

#### `format_order_summary(order_id) -> str`
Formats an order as a readable summary string.

**Returns:** Formatted summary string

## OrderStatus Enum

```python
class OrderStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    PREPARING = "Being prepared"
    READY = "Ready for pickup"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
```

## Data Structure

### Order Record
```python
{
    "order_id": str,
    "customer_id": str,
    "customer_name": str,
    "total_price": float,
    "status": str,  # OrderStatus value
    "created_at": str,  # ISO format
    "updated_at": str,  # ISO format
    "estimated_ready_time": str,  # ISO format (optional)
    "conversation_id": str,  # (optional)
    "metadata": dict,  # Custom data (optional)
    "items": [
        {
            "item_name": str,
            "quantity": int,
            "unit_price": float,
            "subtotal": float
        }
    ]
}
```

## DynamoDB Configuration

### Table Schema
- **Partition Key**: `order_id`
- **Global Secondary Indexes**:
  - `customer_id_index`: Query by customer ID
  - `status_index`: Query by order status
  - `customer_name_index`: Query by customer name

### Capacity Settings
- **Billing Mode**: Provisioned
- **Read Capacity**: 10 RCU (table) + 5 RCU (each GSI)
- **Write Capacity**: 10 WCU (table) + 5 WCU (each GSI)

To adjust capacity for your workload:
```python
manager = OrderManagerDynamoDB(table_name="orders")
# Modify provisioned throughput via AWS Console or boto3
```

### AWS Prerequisites
1. AWS account with DynamoDB access
2. AWS credentials configured (environment variables or ~/.aws/credentials)
3. IAM permissions for DynamoDB operations:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "dynamodb:CreateTable",
                   "dynamodb:GetItem",
                   "dynamodb:PutItem",
                   "dynamodb:UpdateItem",
                   "dynamodb:DeleteItem",
                   "dynamodb:Query",
                   "dynamodb:Scan",
                   "dynamodb:DescribeTable"
               ],
               "Resource": "arn:aws:dynamodb:*:*:table/orders*"
           }
       ]
   }
   ```

## Migration from SQLite to DynamoDB

To migrate existing orders from SQLite to DynamoDB:

```python
from managers import OrderManager, OrderManagerDynamoDB

# Source (SQLite)
sqlite_manager = OrderManager(db_path="conversations.db")

# Destination (DynamoDB)
dynamodb_manager = OrderManagerDynamoDB(table_name="orders", region="us-east-1")

# Get all orders and migrate
response = sqlite_manager.table.query()  # For SQLite
stats = sqlite_manager.get_order_statistics()

# Note: SQLite doesn't have a direct "query all" method, so iterate:
# Use get_orders_by_status for each status, or scan with your business logic
```

## Performance Considerations

### SQLite
- Good for development and small deployments
- File I/O can be a bottleneck with high concurrency
- No scaling beyond single machine

### DynamoDB
- **On-Demand Billing**: Available for variable workloads (auto-scaling)
- **Provisioned Billing**: Better for predictable workloads
- Query patterns use Global Secondary Indexes for fast lookups
- Consider partition key design for hot partitions (order_id is naturally distributed)

## Troubleshooting

### DynamoDB Connection Issues
```python
# Check AWS credentials
import boto3
try:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.meta.client.describe_table(TableName='orders')
except Exception as e:
    print(f"Connection error: {e}")
```

### Table Already Exists Error
The `_initialize_table()` method checks if the table exists before creating it. If you get errors:
1. Verify the table name matches `table_name` parameter
2. Ensure IAM permissions include `dynamodb:DescribeTable`

### Decimal Type Issues
DynamoDB stores numbers as `Decimal` objects. The managers automatically convert to/from Python `float`.

## Integration Example

```python
from managers.order_manager_factory import OrderManagerFactory, OrderManagerType
from managers import OrderStatus

# Initialize based on environment
manager = OrderManagerFactory.create_from_env()

# Create order
manager.create_order(
    order_id="ORD-12345",
    customer_id="CUST-67890",
    customer_name="Alice Johnson",
    items=[
        {"item_name": "Espresso", "quantity": 1, "unit_price": 3.00},
        {"item_name": "Pastry", "quantity": 2, "unit_price": 4.50}
    ],
    total_price=12.00
)

# Update status
manager.update_order_status("ORD-12345", OrderStatus.PREPARING)

# Get summary
print(manager.format_order_summary("ORD-12345"))

# Get stats
stats = manager.get_order_statistics()
print(f"Total revenue: ${stats['total_revenue']}")
```

## License

Same as parent project
