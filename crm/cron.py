import datetime
import requests

def log_crm_heartbeat():
    """Log a heartbeat message every 5 minutes, optionally verifying GraphQL."""
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Optional: Ping GraphQL endpoint to confirm it's alive
    graphql_alive = False
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ hello }"},
            timeout=5,
        )
        if response.status_code == 200 and "hello" in response.text:
            graphql_alive = True
    except Exception:
        graphql_alive = False

    # Build log message
    msg = f"{timestamp} CRM is alive"
    if graphql_alive:
        msg += " - GraphQL OK"
    else:
        msg += " - GraphQL unavailable"

    # Append to log file
    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(msg + "\n")
