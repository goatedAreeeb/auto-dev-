import httpx
import sys

BASE = "http://localhost:8000"

# Assuming you have the exact app running
try:
    resp = httpx.get(f"{BASE}/grade/t1_config")
    print("t1_config:", resp.status_code, resp.json())

    resp = httpx.get(f"{BASE}/grade/t2_port")
    print("t2_port:", resp.status_code, resp.json())
except Exception as e:
    print(e)
