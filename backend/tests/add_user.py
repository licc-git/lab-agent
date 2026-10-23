import requests

BASE = "http://localhost:8088"  # 后端地址

for i in range(1, 50):
    resp = requests.post(
        f"{BASE}/api/auth/register",
        json={
            "username": f"stu{i:03d}",
            "password": "123456",
        },
    )
    print(f"stu{i:03d}: {resp.json().get('code')}")
