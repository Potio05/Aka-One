import requests
import json

IP = "100.80.201.113"

try:
    print(f"Testing root / ...")
    r0 = requests.get(f"http://{IP}:8000/")
    print("Root status:", r0.status_code, r0.text)
except Exception as e:
    print("Root failed:", e)

try:
    print(f"Fetching OpenAPI spec from http://{IP}:8000/openapi.json ...")
    res = requests.get(f"http://{IP}:8000/openapi.json", timeout=10)
    if res.status_code == 200:
        data = res.json()
        paths = list(data.get("paths", {}).keys())
        print("Available Routes on port 8000:")
        for p in paths:
            print("-", p)
    else:
        print("Failed to get OpenAPI spec:", res.status_code, res.text)
except Exception as e:
    print("Error:", e)
