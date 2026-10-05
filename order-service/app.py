import os
import time
import uuid
import hashlib
import sqlite3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:5001")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:5002")
DB_PATH = os.getenv("DB_PATH", "/app/orders.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            total_amount REAL,
            payment_id TEXT,
            status TEXT,
            signature TEXT,
            latency_ms REAL,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def simulate_cpu_work(iterations=5000):
    """Simulates realistic microservice CPU processing (e.g. token validation, hashing)"""
    data = b"order_signature_payload"
    for _ in range(iterations):
        data = hashlib.sha256(data).digest()
    return data.hex()[:16]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "service": "order-service",
        "status": "UP",
        "timestamp": time.time()
    }), 200

@app.route('/orders', methods=['GET'])
def list_orders():
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify({
        "total_orders": len(orders),
        "orders": [dict(ix) for ix in orders]
    }), 200

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(dict(order)), 200

@app.route('/orders', methods=['POST'])
def create_order():
    start_time = time.time()
    data = request.get_json() or {}

    customer_name = data.get("customer_name", "Anonymous Customer")
    product_id = int(data.get("product_id", 1))
    quantity = int(data.get("quantity", 1))
    payment_method = data.get("payment_method", "credit_card")

    # Simulate internal compute
    signature = simulate_cpu_work(6000)

    # Step 1: Inter-service call -> Inventory Service to reserve stock
    try:
        inv_response = requests.post(
            f"{INVENTORY_SERVICE_URL}/products/{product_id}/reserve",
            json={"quantity": quantity},
            timeout=5.0
        )
        if inv_response.status_code != 200:
            return jsonify({
                "error": "Inventory reservation failed",
                "details": inv_response.json()
            }), inv_response.status_code
        inv_data = inv_response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Failed to communicate with Inventory Service",
            "message": str(e)
        }), 503

    unit_price = inv_data.get("unit_price", 100.0)
    total_amount = round(unit_price * quantity, 2)
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    # Step 2: Inter-service call -> Payment Service to process payment
    try:
        pay_response = requests.post(
            f"{PAYMENT_SERVICE_URL}/payments",
            json={
                "order_id": order_id,
                "amount": total_amount,
                "payment_method": payment_method
            },
            timeout=5.0
        )
        if pay_response.status_code != 200:
            # Compensating transaction: roll back inventory if payment fails
            requests.post(
                f"{INVENTORY_SERVICE_URL}/products/{product_id}/restock",
                json={"quantity": quantity},
                timeout=3.0
            )
            return jsonify({
                "error": "Payment processing failed",
                "details": pay_response.json()
            }), pay_response.status_code
        pay_data = pay_response.json()
        payment_id = pay_data.get("payment_id") or pay_data.get("payment", {}).get("payment_id")
    except requests.exceptions.RequestException as e:
        # Compensating transaction: rollback inventory
        requests.post(
            f"{INVENTORY_SERVICE_URL}/products/{product_id}/restock",
            json={"quantity": quantity},
            timeout=3.0
        )
        return jsonify({
            "error": "Failed to communicate with Payment Service",
            "message": str(e)
        }), 503

    # Step 3: Record and finalize order
    order_record = {
        "order_id": order_id,
        "customer_name": customer_name,
        "product_id": product_id,
        "product_name": inv_data.get("product_name"),
        "quantity": quantity,
        "total_amount": total_amount,
        "payment_id": payment_id,
        "status": "CONFIRMED",
        "signature": signature,
        "latency_ms": round((time.time() - start_time) * 1000, 2),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO orders (order_id, customer_name, product_id, product_name, quantity, total_amount, payment_id, status, signature, latency_ms, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_record["order_id"],
        order_record["customer_name"],
        order_record["product_id"],
        order_record["product_name"],
        order_record["quantity"],
        order_record["total_amount"],
        order_record["payment_id"],
        order_record["status"],
        order_record["signature"],
        order_record["latency_ms"],
        order_record["created_at"]
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order placed successfully",
        "order": order_record
    }), 201

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
