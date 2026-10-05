import os
import time
import uuid
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory payments ledger
payments_db = {}

def simulate_cpu_work(iterations=5000):
    """Simulates payment encryption / token hashing"""
    data = b"payment_cryptographic_nonce"
    for _ in range(iterations):
        data = hashlib.sha256(data).digest()
    return data.hex()[:16]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "service": "payment-service",
        "status": "UP",
        "timestamp": time.time()
    }), 200

@app.route('/payments', methods=['POST'])
def process_payment():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    amount = data.get("amount")
    payment_method = data.get("payment_method", "credit_card")

    if not order_id or amount is None:
        return jsonify({"error": "order_id and amount are required"}), 400

    if float(amount) <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400

    # Simulate cryptographic verification
    auth_token = simulate_cpu_work(5000)

    payment_id = f"PAY-{uuid.uuid4().hex[:10].upper()}"
    receipt = {
        "payment_id": payment_id,
        "order_id": order_id,
        "amount": round(float(amount), 2),
        "currency": "USD",
        "payment_method": payment_method,
        "status": "SUCCESS",
        "auth_token": auth_token,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    payments_db[payment_id] = receipt

    return jsonify({
        "message": "Payment processed successfully",
        "payment": receipt
    }), 200

@app.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    receipt = payments_db.get(payment_id)
    if not receipt:
        return jsonify({"error": "Payment receipt not found"}), 404
    return jsonify(receipt), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5002))
    app.run(host='0.0.0.0', port=port)
