import os
import time
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory product catalog with ample stock for testing
products_db = {
    1: {"id": 1, "name": "Apple MacBook Pro", "price": 1999.99, "stock": 50000},
    2: {"id": 2, "name": "Google Pixel 8", "price": 799.99, "stock": 50000},
    3: {"id": 3, "name": "Sony WH-1000XM5 Headphones", "price": 349.99, "stock": 50000},
    4: {"id": 4, "name": "Logitech MX Master 3S Mouse", "price": 99.99, "stock": 50000},
    5: {"id": 5, "name": "Dell UltraSharp 27 Monitor", "price": 549.99, "stock": 50000}
}

def simulate_cpu_work(iterations=4000):
    """Simulates realistic microservice data validation / query processing"""
    data = b"inventory_query_compute"
    for _ in range(iterations):
        data = hashlib.sha256(data).digest()
    return data.hex()[:16]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "service": "inventory-service",
        "status": "UP",
        "timestamp": time.time()
    }), 200

@app.route('/products', methods=['GET'])
def get_products():
    return jsonify({
        "total": len(products_db),
        "products": list(products_db.values())
    }), 200

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = products_db.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200

@app.route('/products/<int:product_id>/reserve', methods=['POST'])
def reserve_stock(product_id):
    simulate_cpu_work(4000)
    data = request.get_json() or {}
    quantity = int(data.get("quantity", 1))

    product = products_db.get(product_id)
    if not product:
        return jsonify({"error": f"Product {product_id} not found"}), 404

    if product["stock"] < quantity:
        return jsonify({
            "error": "Insufficient stock",
            "available": product["stock"],
            "requested": quantity
        }), 400

    product["stock"] -= quantity

    return jsonify({
        "status": "RESERVED",
        "product_id": product_id,
        "product_name": product["name"],
        "unit_price": product["price"],
        "quantity_reserved": quantity,
        "remaining_stock": product["stock"]
    }), 200

@app.route('/products/<int:product_id>/restock', methods=['POST'])
def restock(product_id):
    data = request.get_json() or {}
    quantity = int(data.get("quantity", 1))

    product = products_db.get(product_id)
    if not product:
        return jsonify({"error": f"Product {product_id} not found"}), 404

    product["stock"] += quantity
    return jsonify({
        "status": "RESTOCKED",
        "product_id": product_id,
        "new_stock": product["stock"]
    }), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
