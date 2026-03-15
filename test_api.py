import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    print("[*] Testing /health...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            print("   [OK] UP:", r.json())
            return True
        else:
            print("   [FAIL] DOWN:", r.status_code, r.text)
    except Exception as e:
        print(f"   [!] Error: {e}")
    return False

def test_chat():
    print("[*] Testing /api/chat...")
    payload = {"query": "Wach howa l farq bin Stack w Heap?"}
    try:
        r = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        if r.status_code == 200:
            print("   [OK] Response:", r.json())
        else:
            print("   [FAIL] Error:", r.status_code, r.text)
    except Exception as e:
        print(f"   [!] Error: {e}")

def test_ingest():
    print("[*] Testing /api/ingest...")
    payload = {"course_id": "TEST_101", "drive_folder_id": "12345"}
    try:
        r = requests.post(f"{BASE_URL}/api/ingest", json=payload, timeout=5)
        if r.status_code == 200:
            print("   [OK] Queued:", r.json())
        else:
            print("   [FAIL] Error:", r.status_code, r.text)
    except Exception as e:
        print(f"   [!] Error: {e}")

if __name__ == "__main__":
    print("--- TalebAI API Tester ---")
    if test_health():
        time.sleep(1)
        test_ingest()
        time.sleep(1)
        test_chat()
    else:
        print("[!] API is not ready yet. Please wait for the model download to finish.")
