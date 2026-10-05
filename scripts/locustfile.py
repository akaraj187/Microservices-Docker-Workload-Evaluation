import random
from locust import HttpUser, task, between

class ECommerceLoadTester(HttpUser):
    """
    Locust load testing suite for the Order Processing Microservice.
    Simulates real-world user workflows: placing orders and checking order statuses.
    """
    wait_time = between(0.05, 0.2)

    @task(4)
    def place_order_e2e(self):
        """
        Triggers the full end-to-end multi-service transaction:
        Client -> Order Service -> Inventory Service -> Payment Service
        """
        payload = {
            "customer_name": f"User_{random.randint(1, 10000)}",
            "product_id": random.randint(1, 5),
            "quantity": 1,
            "payment_method": "credit_card"
        }
        self.client.post(
            "/orders",
            json=payload,
            name="POST /orders [End-to-End Orchestration]"
        )

    @task(1)
    def query_orders(self):
        """Queries the order ledger database."""
        self.client.get("/orders", name="GET /orders")

    @task(1)
    def check_health(self):
        """Verifies order service health."""
        self.client.get("/health", name="GET /health")
