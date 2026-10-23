"""实验室表测试数据填充脚本

用法（在 backend 目录下执行）：
    ./.venv/bin/python tests/seed_labs.py

说明：
- 复用应用自身的配置（app.config 自动读取 .env 中的数据库连接）
- 共 20 条数据
- 封面图：从 Bing 图片搜索结果下载，直接保存到 uploads/ 根目录
  （文件名 lab_{序号}_{slug}.jpg），img 字段存 /uploads/lab_xxx.jpg
- 幂等：按 name（唯一键）去重，已存在的记录跳过；img 会统一回填覆盖
"""

import sys
import html
import json
import re
from datetime import time
from pathlib import Path

# 保证从任意目录运行时都能导入 app 包
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from app.config import UPLOAD_DIR  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.lab import Lab  # noqa: E402

# 20 条测试数据：(名称, 位置, 容纳人数, 每日开放开始, 每日开放结束, 简介, 状态)
LABS = [
    ("网络安全实验室", "实验楼 A305", 60, "08:00", "22:00", "配备防火墙、渗透测试平台，支持网络攻防实训。", 1),
    ("人工智能实验室", "实验楼 B201", 80, "08:00", "22:00", "GPU 服务器集群，支撑机器学习与深度学习课程实验。", 1),
    ("嵌入式系统实验室", "实验楼 A102", 50, "08:30", "21:00", "单片机、FPGA 开发板齐全，面向嵌入式开发教学。", 1),
    ("云计算实验室", "数据中心 302", 100, "全天", "全天", "基于 OpenStack 的私有云平台，提供虚拟化实验环境。", 1),
    ("软件工程实验室", "教学楼 C505", 70, "08:00", "22:00", "支持敏捷开发、软件测试与项目管理类课程实践。", 1),
    ("物联网实验室", "实验楼 B108", 60, "08:00", "21:00", "传感器、网关与边缘计算设备，开展物联网综合实验。", 1),
    ("大数据分析实验室", "数据中心 101", 90, "08:00", "22:00", "Hadoop/Spark 集群，用于大数据处理与分析实训。", 1),
    ("机器人实验室", "工程训练中心 201", 45, "09:00", "21:00", "机械臂、移动机器人平台，支持RoboMaster备赛训练。", 1),
    ("计算机视觉实验室", "实验楼 A410", 55, "08:00", "22:00", "图像采集与标注平台，开展图像处理与目标检测研究。", 1),
    ("量子计算实验室", "科研楼 701", 30, "09:00", "18:00", "量子计算模拟平台，面向前沿算法研究（建设中）。", 0),
    ("数据库系统实验室", "实验楼 B305", 65, "08:00", "22:00", "主流数据库环境，支持数据库设计与调优课程实验。", 1),
    ("操作系统实验室", "实验楼 A210", 60, "08:00", "22:00", "Linux 内核开发环境，开展操作系统原理实验。", 1),
    ("编译原理实验室", "教学楼 C410", 40, "08:30", "21:00", "支持词法/语法分析器设计与编译器实践。", 1),
    ("图形图像实验室", "实验楼 B402", 50, "08:00", "22:00", "图形工作站，开展渲染、建模与可视化实验。", 1),
    ("移动应用开发实验室", "创客空间 105", 75, "08:00", "22:00", "iOS/Android/鸿蒙真机测试设备齐全。", 1),
    ("区块链实验室", "科研楼 512", 35, "09:00", "18:00", "联盟链平台，开展智能合约与分布式应用实验。", 0),
    ("自然语言处理实验室", "实验楼 A308", 60, "08:00", "22:00", "语料库与大模型微调平台，开展文本挖掘研究。", 1),
    ("信息安全对抗实验室", "实验楼 B115", 48, "08:00", "22:00", "CTF 训练平台，支持安全竞赛与漏洞挖掘实训。", 1),
    ("智能硬件实验室", "工程训练中心 310", 52, "08:30", "21:00", "PCB 制作与 3D 打印设备，支持智能硬件原型开发。", 1),
    ("虚拟现实实验室", "创客空间 208", 40, "09:00", "21:00", "VR 头显与动捕设备，开展虚拟仿真应用实验。", 0),
]

# 名称 → (文件名 slug, Bing 搜索关键词)
LAB_IMAGES = {
    "网络安全实验室": ("01_network_security", "大学 网络安全实验室 机房 电脑"),
    "人工智能实验室": ("02_ai_lab", "人工智能实验室 GPU 服务器"),
    "嵌入式系统实验室": ("03_embedded", "嵌入式系统 实验室 开发板 电路"),
    "云计算实验室": ("04_cloud", "云计算 数据中心 服务器机房"),
    "软件工程实验室": ("05_software", "大学 软件工程 实验室 电脑 教室"),
    "物联网实验室": ("06_iot", "物联网 实验室 传感器 设备"),
    "大数据分析实验室": ("07_bigdata", "大数据 分析 实验室 数据大屏"),
    "机器人实验室": ("08_robotics", "机器人 实验室 机械臂"),
    "计算机视觉实验室": ("09_computer_vision", "计算机视觉 实验室 摄像头 研究"),
    "量子计算实验室": ("10_quantum", "量子计算 实验室 设备"),
    "数据库系统实验室": ("11_database", "大学 计算机机房 教室 整齐"),
    "操作系统实验室": ("12_os", "大学 计算机 实验室 Linux 代码"),
    "编译原理实验室": ("13_compiler", "大学 程序设计 教室 电脑 屏幕"),
    "图形图像实验室": ("14_graphics", "3D建模 图形工作站 显示器"),
    "移动应用开发实验室": ("15_mobile", "移动应用开发 手机 测试 实验"),
    "区块链实验室": ("16_blockchain", "区块链 技术 网络 概念图"),
    "自然语言处理实验室": ("17_nlp", "自然语言处理 人工智能 文本"),
    "信息安全对抗实验室": ("18_ctf", "CTF 网络安全 黑客 竞赛"),
    "智能硬件实验室": ("19_smart_hardware", "智能硬件 创客空间 3D打印"),
    "虚拟现实实验室": ("20_virtual_reality", "虚拟现实 VR 实验室 头显"),
}

# 直接存 uploads/ 根目录，不建子目录
# 注意：用 images/async 接口（images/search 主页有时返回无结果的 JS 壳页面）
BING_SEARCH_URL = "https://www.bing.com/images/async"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def lab_img_url(name: str) -> str:
    slug, _ = LAB_IMAGES[name]
    return f"/uploads/lab_{slug}.jpg"


def _search_image_urls(query: str, limit: int = 5) -> list[str]:
    """Bing 图片搜索，返回候选原图 URL（murl）与缩略图 URL（turl）"""
    resp = requests.get(
        BING_SEARCH_URL,
        params={"q": query, "first": 0, "count": 35, "mmasync": 1},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    candidates = []
    # 结果页每个缩略图节点带 m 属性，内含 HTML 转义的 JSON（murl=原图，turl=缩略图）
    for raw in re.findall(r'\sm="(\{[^"]+\})"', resp.text):
        try:
            info = json.loads(html.unescape(raw))
        except json.JSONDecodeError:
            continue
        for key in ("murl", "turl"):
            url = info.get(key)
            if url and url not in candidates:
                candidates.append(url)
        if len(candidates) >= limit * 2:
            break
    return candidates


def _download(url: str) -> bytes | None:
    try:
        resp = requests.get(url, headers={**HEADERS, "Referer": url}, timeout=15)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if not content_type.startswith("image/") or len(resp.content) < 5 * 1024:
            return None
        return resp.content
    except requests.RequestException:
        return None


def ensure_images() -> None:
    """从 Bing 下载每个实验室的封面图，直接保存到 uploads/ 根目录；已存在的跳过"""
    for name, (slug, query) in LAB_IMAGES.items():
        path = UPLOAD_DIR / f"lab_{slug}.jpg"
        if path.exists() and path.stat().st_size > 0:
            continue
        try:
            candidates = _search_image_urls(query)
        except requests.RequestException as e:
            print(f"  搜索失败：{name}（{e}）")
            continue
        for url in candidates:
            content = _download(url)
            if content:
                path.write_bytes(content)
                print(f"  封面就绪：{name} -> {path.name} ({len(content) // 1024}KB)")
                break
        else:
            print(f"  下载失败：{name}，该条 img 保持为空")


def seed() -> None:
    print("[1/3] 从 Bing 下载实验室封面图（已存在的跳过）")
    ensure_images()

    db = SessionLocal()
    try:
        print("[2/3] 写入实验室数据")
        created, skipped = 0, 0
        existing = {name for (name,) in db.query(Lab.name).all()}
        for name, location, capacity, open_t, close_t, desc, status in LABS:
            if name in existing:
                skipped += 1
                continue
            db.add(
                Lab(
                    name=name,
                    location=location,
                    capacity=capacity,
                    open_time=time.fromisoformat(open_t) if open_t != "全天" else time(0, 0),
                    close_time=time.fromisoformat(close_t) if close_t != "全天" else time(23, 59),
                    description=desc,
                    img=lab_img_url(name),
                    status=status,
                )
            )
            created += 1
        db.commit()

        print("[3/3] 回填 img（统一覆盖为最新路径）")
        for name in LAB_IMAGES:
            row = db.query(Lab).filter(Lab.name == name).first()
            if row:
                row.img = lab_img_url(name)
        db.commit()
    except IntegrityError:
        db.rollback()
        print("写入失败：存在重复的实验室名称，已回滚")
        raise
    finally:
        db.close()

    total = 0
    db = SessionLocal()
    try:
        total = db.query(Lab).count()
    finally:
        db.close()

    print(f"完成：新增 {created} 条，跳过（已存在）{skipped} 条，labs 表当前共 {total} 条")


if __name__ == "__main__":
    seed()
