#!/usr/bin/env python3
"""
Test script for Editorial Engine Platform
"""

import os
import sys
import requests
import time
from typing import Dict, Any

def test_orchestrator_health():
    """Test orchestrator health endpoint."""
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Orchestrator health check passed")
            return True
        else:
            print(f"❌ Orchestrator health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Orchestrator health check failed: {e}")
        return False

def test_search_api():
    """Test search API endpoint."""
    try:
        payload = {
            "query": "test search query",
            "k": 5,
            "hybrid": True
        }
        
        response = requests.post(
            "http://localhost:3000/api/search",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Search API endpoint accessible")
            return True
        else:
            print(f"❌ Search API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Search API test failed: {e}")
        return False

def test_0711_connection():
    """Test connection to 0711 Agent System."""
    try:
        seven011_url = os.getenv("SEVEN011_BASE_URL", "http://34.40.104.64:8000")
        response = requests.get(f"{seven011_url}/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ 0711 Agent System connection successful")
            return True
        else:
            print(f"❌ 0711 connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 0711 connection test failed: {e}")
        return False

def test_flower_dashboard():
    """Test Flower dashboard accessibility."""
    try:
        response = requests.get("http://localhost:5555", timeout=5)
        if response.status_code == 200:
            print("✅ Flower dashboard accessible")
            return True
        else:
            print(f"❌ Flower dashboard failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Flower dashboard test failed: {e}")
        return False

def test_prometheus():
    """Test Prometheus metrics endpoint."""
    try:
        response = requests.get("http://localhost:9090/-/healthy", timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus is healthy")
            return True
        else:
            print(f"❌ Prometheus health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Prometheus test failed: {e}")
        return False

def test_grafana():
    """Test Grafana accessibility."""
    try:
        response = requests.get("http://localhost:3001/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Grafana is accessible")
            return True
        else:
            print(f"❌ Grafana health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Grafana test failed: {e}")
        return False

def main():
    """Run all platform tests."""
    print("🧪 Testing Editorial Engine Platform...")
    print("=" * 50)
    
    # Load environment variables if .env exists
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
    
    tests = [
        ("Orchestrator Health", test_orchestrator_health),
        ("Search API", test_search_api),
        ("0711 Connection", test_0711_connection),
        ("Flower Dashboard", test_flower_dashboard),
        ("Prometheus", test_prometheus),
        ("Grafana", test_grafana),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
        
        if not result:
            print(f"   Retrying in 5 seconds...")
            time.sleep(5)
            result = test_func()
            results[-1] = (test_name, result)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Platform is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())