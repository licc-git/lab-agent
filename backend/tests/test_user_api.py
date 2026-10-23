"""
用户管理模块前后端联调测试（对应前端页面 frontend/src/views/User.vue）

覆盖场景：
1. 管理员登录（admin01）获取 token
2. 未登录访问受保护接口 → 401
3. 分页查询用户列表（page / page_size）
4. 账号 / 昵称模糊搜索
5. 新增用户 + 负向用例（重复账号、非法手机号）
6. 编辑用户并回查验证
7. 删除用户 + 负向用例（删除自己、删除不存在用户）
8. 批量删除用户（含自己被过滤、重复 id 去重、空列表/不存在 id）
9. 非法路径参数回归用例（PUT /api/user/null → 422，
   对应前端修复前页面加载时误发的请求）

运行方式：cd backend && python tests/test_user_api.py
"""
import time

import requests

BASE = "http://127.0.0.1:8088"
ADMIN = {"username": "admin01", "password": "123456"}

passed = []
failed = []


def check(name, cond, detail=""):
    """记录单条用例结果"""
    if cond:
        passed.append(name)
        print(f"  PASS  {name}")
    else:
        failed.append(name)
        print(f"  FAIL  {name}  {detail}")


def main():
    # ---------- 1. 登录 ----------
    print("\n[1] 管理员登录")
    resp = requests.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=10)
    body = resp.json()
    check("登录返回 code=200", body.get("code") == 200, f"resp={body}")
    token = body.get("data", {}).get("token", "")
    admin_id = body.get("data", {}).get("user", {}).get("id")
    check("返回 token 非空", bool(token), f"token={token!r}")
    check("角色为 admin", body.get("data", {}).get("user", {}).get("role") == "admin")
    auth = {"Authorization": f"Bearer {token}"}

    # 错误密码（后端限制密码 6-12 位，故用 8 位错误密码验证业务逻辑而非参数校验）
    resp = requests.post(
        f"{BASE}/api/auth/login",
        json={"username": "admin01", "password": "wrong123"},
        timeout=10,
    )
    body = resp.json()
    check("错误密码登录被拒绝", body.get("code") == 500 and "账号或密码错误" in body.get("message", ""), f"resp={body}")

    # ---------- 2. 未登录访问受保护接口 ----------
    print("\n[2] 鉴权校验")
    resp = requests.get(f"{BASE}/api/user/list", timeout=10)
    check("未登录访问列表返回 401", resp.status_code == 401, f"status={resp.status_code} body={resp.text[:120]}")

    # ---------- 3. 分页查询 ----------
    print("\n[3] 分页查询用户列表")
    resp = requests.get(f"{BASE}/api/user/list", params={"page": 1, "page_size": 10}, headers=auth, timeout=10)
    body = resp.json()
    check("列表返回 code=200", body.get("code") == 200, f"resp={body}")
    total = body.get("data", {}).get("total", -1)
    rows = body.get("data", {}).get("data", [])
    check(f"total>0（实际 total={total}）", total > 0)
    check("单页条数不超过 page_size", len(rows) <= 10, f"len={len(rows)}")
    check("返回字段完整", all(("id" in r and "username" in r and "status" in r) for r in rows))

    # page_size 合法性校验（后端限制 ge=10）
    resp = requests.get(
        f"{BASE}/api/user/list", params={"page": 1, "page_size": 5}, headers=auth, timeout=10
    )
    check("page_size<10 被拒绝（422）", resp.status_code == 422, f"status={resp.status_code}")

    # ---------- 4. 模糊搜索 ----------
    print("\n[4] 模糊搜索")
    resp = requests.get(
        f"{BASE}/api/user/list",
        params={"page": 1, "page_size": 10, "username": "stu"},
        headers=auth,
        timeout=10,
    )
    body = resp.json()
    rows = body.get("data", {}).get("data", [])
    check("按账号模糊搜索 code=200", body.get("code") == 200, f"resp={body}")
    check("搜索结果都包含关键字 stu", all("stu" in r["username"] for r in rows), f"rows={[r['username'] for r in rows]}")

    resp = requests.get(
        f"{BASE}/api/user/list",
        params={"page": 1, "page_size": 10, "name": "不存在的昵称xyz"},
        headers=auth,
        timeout=10,
    )
    body = resp.json()
    check("搜索不存在的昵称返回空列表", body.get("data", {}).get("data") == [] and body.get("data", {}).get("total") == 0, f"resp={body}")

    # ---------- 5. 新增用户 ----------
    print("\n[5] 新增用户")
    suffix = str(int(time.time()))[-6:]
    new_user = {
        "username": f"tuser{suffix}",
        "password": "123456",
        "name": "联调测试",
        "phone": "13800000000",
        "email": "tuser@test.com",
        "role": "student",
        "status": 1,
    }
    resp = requests.post(f"{BASE}/api/user", json=new_user, headers=auth, timeout=10)
    body = resp.json()
    check("新增用户 code=200", body.get("code") == 200, f"resp={body}")
    new_id = body.get("data", {}).get("id")
    check("返回新用户 id", isinstance(new_id, int), f"id={new_id!r}")

    # 重复账号
    resp = requests.post(f"{BASE}/api/user", json=new_user, headers=auth, timeout=10)
    body = resp.json()
    check("重复账号被拒绝", body.get("code") != 200 and "已存在" in body.get("message", ""), f"resp={body}")

    # 非法手机号（前端已拦截 10/11 开头，这里验证后端同样拦截）
    bad = dict(new_user, username=f"tbad{suffix}", phone="10000000000")
    resp = requests.post(f"{BASE}/api/user", json=bad, headers=auth, timeout=10)
    check("非法手机号被拒绝（422）", resp.status_code == 422, f"status={resp.status_code} body={resp.text[:120]}")

    # ---------- 6. 编辑用户 ----------
    print("\n[6] 编辑用户")
    resp = requests.put(
        f"{BASE}/api/user/{new_id}",
        json={"name": "联调已改", "phone": "13900000000", "email": "tuser-upd@test.com"},
        headers=auth,
        timeout=10,
    )
    body = resp.json()
    check("编辑用户 code=200", body.get("code") == 200, f"resp={body}")
    check("编辑后昵称生效", body.get("data", {}).get("name") == "联调已改", f"name={body.get('data', {}).get('name')!r}")
    check("编辑后手机号生效", body.get("data", {}).get("phone") == "13900000000")

    # 回查列表确认落库
    resp = requests.get(
        f"{BASE}/api/user/list",
        params={"page": 1, "page_size": 10, "username": f"tuser{suffix}"},
        headers=auth,
        timeout=10,
    )
    rows = resp.json().get("data", {}).get("data", [])
    check("回查列表能看到修改结果", len(rows) == 1 and rows[0]["name"] == "联调已改", f"rows={rows}")

    # 编辑不存在用户（路径参数上限 9999，用范围内不存在的 id）
    resp = requests.put(
        f"{BASE}/api/user/9999",
        json={"name": "幽灵"},
        headers=auth,
        timeout=10,
    )
    body = resp.json()
    check("编辑不存在用户被拒绝", body.get("code") != 200 and "不存在" in body.get("message", ""), f"resp={body}")

    # 回归用例：PUT /api/user/null（前端修复前页面加载会误发该请求）
    resp = requests.put(f"{BASE}/api/user/null", json={"name": "x"}, headers=auth, timeout=10)
    check("PUT /api/user/null 被拒绝（422）", resp.status_code == 422, f"status={resp.status_code}")

    # ---------- 7. 删除用户 ----------
    print("\n[7] 删除用户")
    resp = requests.delete(f"{BASE}/api/user/{admin_id}", headers=auth, timeout=10)
    body = resp.json()
    check("删除自己被拒绝", body.get("code") != 200 and "不能删除" in body.get("message", ""), f"resp={body}")

    resp = requests.delete(f"{BASE}/api/user/{new_id}", headers=auth, timeout=10)
    body = resp.json()
    check("删除测试用户 code=200", body.get("code") == 200, f"resp={body}")

    resp = requests.delete(f"{BASE}/api/user/{new_id}", headers=auth, timeout=10)
    body = resp.json()
    check("重复删除提示用户不存在", body.get("code") != 200 and "不存在" in body.get("message", ""), f"resp={body}")

    # ---------- 8. 批量删除用户 ----------
    print("\n[8] 批量删除用户")
    suffix2 = str(int(time.time()))[-6:]
    ids_to_del = []
    for i in range(1, 3):
        resp = requests.post(
            f"{BASE}/api/user",
            json={
                "username": f"tdel{i}{suffix2}",
                "password": "123456",
                "name": "批删",
                "role": "student",
                "status": 1,
            },
            headers=auth,
            timeout=10,
        )
        body = resp.json()
        check(f"准备数据：创建批删用户{i} code=200", body.get("code") == 200, f"resp={body}")
        ids_to_del.append(body.get("data", {}).get("id"))

    # 空 ids
    resp = requests.delete(f"{BASE}/api/user/batch", json={"ids": []}, headers=auth, timeout=10)
    check("空 ids 被拒绝（422）", resp.status_code == 422, f"status={resp.status_code}")

    # 包含自己的 id：应自动过滤，只删别人
    resp = requests.delete(
        f"{BASE}/api/user/batch", json={"ids": ids_to_del + [admin_id]}, headers=auth, timeout=10
    )
    body = resp.json()
    check("含自己 id 的批量删除 code=200", body.get("code") == 200, f"resp={body}")
    check("自己被过滤，仅删除其他 2 个", body.get("data", {}).get("deleted") == 2, f"resp={body}")

    resp = requests.get(
        f"{BASE}/api/user/list",
        params={"page": 1, "page_size": 10, "username": suffix2},
        headers=auth,
        timeout=10,
    )
    body = resp.json()
    check("回查列表批删用户已消失", body.get("data", {}).get("total") == 0, f"resp={body}")
    resp = requests.get(
        f"{BASE}/api/user/list",
        params={"page": 1, "page_size": 10, "username": "admin01"},
        headers=auth,
        timeout=10,
    )
    body = resp.json()
    check("当前登录账号仍存在", body.get("data", {}).get("total") == 1, f"resp={body}")

    # 重复 id 去重
    resp = requests.post(
        f"{BASE}/api/user",
        json={"username": f"tdup{suffix2}", "password": "123456", "role": "student", "status": 1},
        headers=auth,
        timeout=10,
    )
    dup_id = resp.json().get("data", {}).get("id")
    resp = requests.delete(
        f"{BASE}/api/user/batch", json={"ids": [dup_id, dup_id]}, headers=auth, timeout=10
    )
    body = resp.json()
    check("重复 id 去重后只删 1 个", body.get("code") == 200 and body.get("data", {}).get("deleted") == 1, f"resp={body}")

    # 只包含不存在的 id：幂等返回 deleted=0
    resp = requests.delete(f"{BASE}/api/user/batch", json={"ids": [9999]}, headers=auth, timeout=10)
    body = resp.json()
    check("不存在 id 返回 deleted=0", body.get("code") == 200 and body.get("data", {}).get("deleted") == 0, f"resp={body}")

    # ---------- 汇总 ----------
    print(f"\n========== 结果：{len(passed)} 通过，{len(failed)} 失败 ==========")
    if failed:
        for name in failed:
            print(f"  失败用例: {name}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
