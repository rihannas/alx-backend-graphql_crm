#!/usr/bin/env python3
import datetime
import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure logging
logging.basicConfig(
    filename="/tmp/order_reminders_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# GraphQL endpoint
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=True,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# Calculate last 7 days
seven_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

# GraphQL query
query = gql("""
query GetRecentOrders($since: Date!) {
  orders(orderDate_Gte: $since, status: "PENDING") {
    id
    customer {
      email
    }
  }
}
""")

# Execute query
params = {"since": seven_days_ago}
result = client.execute(query, variable_values=params)

orders = result.get("orders", [])

# Log each order
for order in orders:
    order_id = order["id"]
    customer_email = order["customer"]["email"]
    logging.info(f"Reminder: Order {order_id} for customer {customer_email}")

print("Order reminders processed!")
