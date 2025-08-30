import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def log_crm_heartbeat():
    """Log a heartbeat message every 5 minutes, verifying GraphQL hello field."""

    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Configure GraphQL client
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Try querying hello field
    graphql_alive = False
    try:
        query = gql("{ hello }")
        result = client.execute(query)
        if "hello" in result:
            graphql_alive = True
    except Exception:
        graphql_alive = False

    # Build log message
    msg = f"{timestamp} CRM is alive"
    msg += " - GraphQL OK" if graphql_alive else " - GraphQL unavailable"

    # Append log
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(msg + "\n")


def update_low_stock():
    """Run GraphQL mutation to restock low stock products and log updates."""

    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # GraphQL client
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Mutation
    mutation = gql("""
    mutation {
      updateLowStockProducts {
        updatedProducts {
          id
          name
          stock
        }
        message
      }
    }
    """)

    try:
        result = client.execute(mutation)
        updates = result["updateLowStockProducts"]["updatedProducts"]

        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            f.write(f"{timestamp} - {len(updates)} products updated\n")
            for p in updates:
                f.write(f"  {p['name']} new stock: {p['stock']}\n")

    except Exception as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            f.write(f"{timestamp} - Error running mutation: {e}\n")
