#!/usr/bin/env python3
import requests
import json
import sys
import time
from multiprocessing import Process


def start_server():
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="error")


def test_api():
    time.sleep(5)

    print("Testing /api/health...")
    response = requests.get("http://localhost:8000/api/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

    print("\nTesting /api/query...")
    payload = {
        "query": "What are the penalties for data breach under DPDPA?",
        "conversation_history": []
    }
    response = requests.post("http://localhost:8000/api/query", json=payload)
    print(f"  Status: {response.status_code}")
    result = response.json()
    print(f"  Risk Level: {result.get('risk_level')}")
    print(f"  Confidence: {result.get('confidence')}")
    print(f"  Answer (first 200 chars): {result.get('answer', '')[:200]}...")

    print("\nTesting /api/metrics...")
    response = requests.get("http://localhost:8000/api/metrics")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")


if __name__ == "__main__":
    server = Process(target=start_server)
    server.start()

    try:
        test_api()
    finally:
        server.terminate()
        server.join()