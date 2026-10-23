"""实验室管理 API 集成测试（TestClient 进程内运行，无需启动服务器）

用法（在 backend 目录下执行）：
    ./.venv/bin/python tests/test_lab_api.py

覆盖场景：
1. 管理员登录 + 错误密码拒绝
2. 分页查询 + 关键词模糊搜索
3. 新增实验室 + 重复名称拒绝
4. 编辑实验室 + 回查 + 不存在实验室拒绝
5. 删除实验室（单个）+ 不存在实验室
6. 批量删除（正常、空 ids、无匹配）——含路由顺序回归
   （/batch 必须注册在 /{lab_id} 之前，否则 "batch" 会被当成 lab_id 校验报 422）
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)

passed = failed = 0


def check(name: str, cond: bool, detail: str = ""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name}  {detail}")


def main() -> None:
    auth = {}

    # ---------- 1. 登录 ----------
    print("\n[1] 管理员登录")
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin01", "password": "123456"},
    )
    body = resp.json()
    check("登录 code=200", body.get("code") == 200, f"resp={body}")
    token = body.get("data", {}).get("token", "")
    auth = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/auth/login",
        json={"username": "admin01", "password": "wrong123"},
    )
    check("错误密码被拒绝", resp.json().get("code") != 200, f"resp={resp.json()}")

    # ---------- 2. 分页查询 ----------
    print("\n[2] 分页查询")
    resp = client.get("/api/lab/list", params={"page": 1, "page_size": 10}, headers=auth)
    body = resp.json()
    check("列表 code=200", body.get("code") == 200, f"resp={body}")
    total = body.get("data", {}).get("total", 0)
    check(f"种子数据存在（total={total} >= 20）", total >= 20, f"resp={body}")
    check("返回条数 = page_size", len(body.get("data", {}).get("data", [])) == 10, f"resp={body}")

    resp = client.get(
        "/api/lab/list", params={"page": 1, "page_size": 10, "keywords": "人工智能"}, headers=auth
    )
    body = resp.json()
    rows = body.get("data", {}).get("data", [])
    check("关键词搜索命中", body.get("code") == 200 and len(rows) >= 1, f"resp={body}")
    check(
        "搜索结果包含关键词",
        any("人工智能" in (r.get("name") or "") or "人工智能" in (r.get("location") or "") for r in rows),
        f"rows={rows}",
    )

    resp = client.get("/api/lab/list", params={"page": 1, "page_size": 10}, timeout=None)
    check("未登录访问列表被拒绝（401）", resp.status_code == 401, f"status={resp.status_code}")

    # ---------- 3. 新增 ----------
    print("\n[3] 新增实验室")
    suffix = str(int(time.time()))[-6:]
    lab_name = f"测试实验室{suffix}"
    resp = client.post(
        "/api/lab",
        json={
            "name": lab_name,
            "location": "测试楼 101",
            "capacity": 42,
            "open_time": "08:30",
            "close_time": "22:00",
            "open_days": [0, 2, 4],
            "status": 1,
        },
        headers=auth,
    )
    body = resp.json()
    check("新增 code=200", body.get("code") == 200, f"resp={body}")
    lab_id = body.get("data", {}).get("id")
    check("每日开放时间正确保存", body.get("data", {}).get("open_time") == "08:30:00"
          and body.get("data", {}).get("close_time") == "22:00:00", f"resp={body}")
    check("每周开放日正确保存", body.get("data", {}).get("open_days") == [0, 2, 4], f"resp={body}")

    resp = client.post(
        "/api/lab",
        json={"name": lab_name, "location": "重复名称", "capacity": 1, "status": 1},
        headers=auth,
    )
    check("重复名称被拒绝", resp.json().get("code") != 200, f"resp={resp.json()}")

    # ---------- 4. 编辑 ----------
    print("\n[4] 编辑实验室")
    resp = client.put(
        f"/api/lab/{lab_id}",
        json={
            "name": lab_name,
            "location": "测试楼 202",
            "capacity": 50,
            "open_time": "09:00",
            "close_time": "18:00",
            "open_days": [1, 3, 5],
            "status": 0,
        },
        headers=auth,
    )
    body = resp.json()
    check("编辑 code=200", body.get("code") == 200, f"resp={body}")
    check("编辑已生效", body.get("data", {}).get("location") == "测试楼 202", f"resp={body}")
    check("开放安排编辑已生效",
          body.get("data", {}).get("open_time") == "09:00:00"
          and body.get("data", {}).get("close_time") == "18:00:00"
          and body.get("data", {}).get("open_days") == [1, 3, 5], f"resp={body}")

    resp = client.put("/api/lab/999999", json={"name": "幽灵实验室"}, headers=auth)
    check("编辑不存在的实验室被拒绝", resp.json().get("code") != 200, f"resp={resp.json()}")

    # ---------- 5. 单个删除 ----------
    print("\n[5] 删除实验室")
    resp = client.delete(f"/api/lab/{lab_id}", headers=auth)
    check("删除 code=200", resp.json().get("code") == 200, f"resp={resp.json()}")

    resp = client.delete("/api/lab/999999", headers=auth)
    check("删除不存在的实验室被拒绝", resp.json().get("code") != 200, f"resp={resp.json()}")

    # ---------- 6. 批量删除 ----------
    print("\n[6] 批量删除实验室")
    ids_to_del = []
    for i in range(1, 3):
        resp = client.post(
            "/api/lab",
            json={"name": f"批删实验室{i}{suffix}", "capacity": 10, "status": 1},
            headers=auth,
        )
        body = resp.json()
        check(f"准备数据：创建批删实验室{i} code=200", body.get("code") == 200, f"resp={body}")
        ids_to_del.append(body.get("data", {}).get("id"))

    # httpx 0.28 起 .delete() 不再支持 json 参数，统一用 request()
    resp = client.request("DELETE", "/api/lab/batch", json={"ids": []}, headers=auth)
    check("空 ids 被拒绝（422）", resp.status_code == 422, f"status={resp.status_code}")

    resp = client.request("DELETE", "/api/lab/batch", json={"ids": ids_to_del}, headers=auth)
    body = resp.json()
    check("批量删除 code=200", body.get("code") == 200, f"resp={body}")
    check("提示删除 2 个", "2" in body.get("message", ""), f"resp={body}")

    # 用本轮唯一后缀搜索，避免误匹配其他轮次残留的数据
    resp = client.get(
        "/api/lab/list", params={"page": 1, "page_size": 10, "keywords": suffix}, headers=auth
    )
    body = resp.json()
    check("回查列表批删实验室已消失", body.get("data", {}).get("total") == 0, f"resp={body}")

    resp = client.request("DELETE", "/api/lab/batch", json={"ids": [999999]}, headers=auth)
    check("无匹配时提示错误", resp.json().get("code") != 200, f"resp={resp.json()}")

    # ---------- 汇总 ----------
    print(f"\n{'=' * 40}")
    print(f"测试完成：通过 {passed} / 失败 {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
