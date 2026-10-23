"""用户表测试数据填充脚本

用法（在 backend 目录下执行）：
    ./.venv/bin/python tests/seed_users.py

说明：
- 共 50 条数据：3 个管理员（admin01~03）+ 47 个学生（stu001~047）
- 密码统一 123456（bcrypt，复用应用自身的哈希函数，保证能正常登录）
- 头像：从项目根目录 avatars/（35 张）轮转取用，按 app/api/files.py 的命名
  规范（{毫秒时间戳}_{uuid8}{原后缀}）复制到 backend/uploads/avatars/
- avatar 字段存 /uploads/avatars/{disk_name}
- 幂等：按 username 去重，已存在的记录跳过；手机号用固定随机种子保证可复现
"""

import random
import shutil
import sys
import time
import uuid
from pathlib import Path

# 保证从任意目录运行时都能导入 app 包
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.exc import IntegrityError  # noqa: E402

from app.config import UPLOAD_DIR  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utils.password import hash_password  # noqa: E402

# 项目根目录下的头像素材（35 张，jpg/png/jpeg 混合）
AVATAR_SOURCE_DIR = Path(__file__).resolve().parents[2] / "avatars"
AVATAR_UPLOAD_DIR = UPLOAD_DIR / "avatars"

# (角色, 姓名)；管理员在前 3 位，其余为学生
USERS = [
    ("admin", "张伟"),
    ("admin", "李静"),
    ("admin", "王浩然"),
    ("student", "刘思远"), ("student", "陈雨桐"), ("student", "杨子墨"),
    ("student", "赵一鸣"), ("student", "黄晓彤"), ("student", "周子轩"),
    ("student", "吴佳琪"), ("student", "徐志远"), ("student", "孙浩宇"),
    ("student", "马欣然"), ("student", "朱文博"), ("student", "胡雅婷"),
    ("student", "郭俊辰"), ("student", "何雨欣"), ("student", "高天佑"),
    ("student", "林诗涵"), ("student", "罗志强"), ("student", "郑晓峰"),
    ("student", "梁静怡"), ("student", "谢文轩"), ("student", "宋佳音"),
    ("student", "唐子豪"), ("student", "韩雨薇"), ("student", "冯俊杰"),
    ("student", "董思琪"), ("student", "萧景行"), ("student", "程语汐"),
    ("student", "曹阳"), ("student", "袁明轩"), ("student", "邓紫涵"),
    ("student", "许博文"), ("student", "傅婉清"), ("student", "沈天翊"),
    ("student", "曾梓萱"), ("student", "彭浩然"), ("student", "吕佳琪"),
    ("student", "苏景琛"), ("student", "卢晓萌"), ("student", "蒋文韬"),
    ("student", "贾静雯"), ("student", "丁一凡"), ("student", "魏子涵"),
    ("student", "薛皓轩"), ("student", "叶芷晴"), ("student", "阎泽宇"),
    ("student", "余思涵"), ("student", "潘俊驰"),
]

assert len(USERS) == 50, f"用户条数应为 50，当前 {len(USERS)}"

# 常见手机号段，固定随机种子保证重复运行结果一致
PHONE_PREFIXES = ["138", "139", "150", "151", "152", "155", "158", "159",
                  "166", "176", "177", "178", "180", "181", "182", "185",
                  "186", "187", "188", "189", "193", "195", "198"]
random.seed(42)


def build_usernames() -> list[str]:
    """admin01~03 + stu001~047"""
    return [f"admin{i:02d}" for i in range(1, 4)] + [f"stu{i:03d}" for i in range(1, 48)]


def gen_phones(count: int) -> list[str]:
    """生成不重复的手机号"""
    phones = set()
    while len(phones) < count:
        phones.add(random.choice(PHONE_PREFIXES) + "".join(random.choices("0123456789", k=8)))
    return list(phones)


def copy_avatar(idx: int) -> str:
    """按 files.py 命名规范复制头像，返回 /uploads/avatars/xx 路径"""
    files = sorted(p for p in AVATAR_SOURCE_DIR.iterdir() if p.is_file())
    src = files[idx % len(files)]  # 35 张轮转给 50 个用户
    ext = src.suffix.lower()
    disk_name = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}{ext}"
    AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, AVATAR_UPLOAD_DIR / disk_name)
    return f"/uploads/avatars/{disk_name}"


def seed() -> None:
    assert AVATAR_SOURCE_DIR.exists(), f"头像目录不存在：{AVATAR_SOURCE_DIR}"

    print("[1/3] 校验头像素材")
    avatar_count = len([p for p in AVATAR_SOURCE_DIR.iterdir() if p.is_file()])
    print(f"  可用头像 {avatar_count} 张（50 个用户轮转使用）")

    db = SessionLocal()
    try:
        print("[2/3] 写入用户数据")
        existing = {name for (name,) in db.query(User.username).all()}
        usernames = build_usernames()
        phones = gen_phones(len(usernames))
        # 同一密码只做一次哈希（bcrypt 较慢，50 次全量哈希没有必要）
        password_hash = hash_password("123456")

        created, skipped = 0, 0
        for idx, (role, name) in enumerate(USERS):
            username = usernames[idx]
            if username in existing:
                skipped += 1
                continue
            db.add(
                User(
                    username=username,
                    password=password_hash,
                    name=name,
                    email=f"{username}@stu.univ.edu.cn" if role == "student" else f"{username}@univ.edu.cn",
                    phone=phones[idx],
                    avatar=copy_avatar(idx),
                    role=role,
                    status=1,
                )
            )
            created += 1
        db.commit()
    except IntegrityError:
        db.rollback()
        print("写入失败：存在重复的用户名，已回滚")
        raise
    finally:
        db.close()

    total = 0
    db = SessionLocal()
    try:
        total = db.query(User).count()
        admins = db.query(User).filter(User.role == "admin").count()
    finally:
        db.close()

    print(f"完成：新增 {created} 条，跳过（已存在）{skipped} 条；"
          f"users 表当前共 {total} 条（管理员 {admins}，学生 {total - admins}）")


if __name__ == "__main__":
    seed()
