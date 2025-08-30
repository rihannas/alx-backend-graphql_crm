import requests
from datetime import datetime

from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

@shared_task
def generate_crm_report():
    """Fetch CRM stats via GraphQL and log a weekly report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # GraphQL query
    query = gql("""
    query {
        totalCustomers: customersCount
        totalOrders: ordersCount
        totalRevenue: totalRevenue
    }
    """)

    try:
        result = client.execute(query)
        report = f"{timestamp} - Report: {result['totalCustomers']} customers, " \
                 f"{result['totalOrders']} orders, {result['totalRevenue']} revenue"

        with open("/tmp/crm_report_log.txt", "a") as f:
            f.write(report + "\n")

    except Exception as e:
        with open("/tmp/crm_report_log.txt", "a") as f:
            f.write(f"{timestamp} - Error generating report: {e}\n")
