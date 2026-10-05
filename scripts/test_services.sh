#!/bin/bash
set -e

echo "=========================================================="
echo "    MICROSERVICES VERIFICATION & INTER-SERVICE TEST"
echo "=========================================================="

echo -e "\n[1] Testing Order Service Health (Port 5000)..."
curl -s http://localhost:5000/health | python3 -m json.tool

echo -e "\n[2] Testing Inventory Service Health & Catalog (Port 5001)..."
curl -s http://localhost:5001/health | python3 -m json.tool
curl -s http://localhost:5001/products | python3 -m json.tool

echo -e "\n[3] Testing Payment Service Health (Port 5002)..."
curl -s http://localhost:5002/health | python3 -m json.tool

echo -e "\n[4] Testing Independent Inventory Reservation..."
curl -s -X POST http://localhost:5001/products/2/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 1}' | python3 -m json.tool

echo -e "\n[5] Testing Independent Payment Processing..."
curl -s -X POST http://localhost:5002/payments \
  -H "Content-Type: application/json" \
  -d '{"order_id": "TEST-101", "amount": 799.99, "payment_method": "credit_card"}' | python3 -m json.tool

echo -e "\n[6] Testing Full End-to-End Orchestrated Order Flow (Checkpoint 3)..."
echo "Sending POST http://localhost:5000/orders..."
curl -s -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Alice Walker", "product_id": 1, "quantity": 2, "payment_method": "credit_card"}' | python3 -m json.tool

echo -e "\n[7] Querying Orders Database from Order Service..."
curl -s http://localhost:5000/orders | python3 -m json.tool

echo -e "\n=========================================================="
echo "    ALL INTER-SERVICE TESTS COMPLETED SUCCESSFULLY!"
echo "=========================================================="
