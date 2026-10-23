"""实验室设备表测试数据填充脚本

用法（在 backend 目录下执行）：
    ./.venv/bin/python tests/seed_equipment.py

说明：
- 复用应用自身的配置（app.config 自动读取 .env 中的数据库连接）
- 共 50 条数据，分摊到 labs 表的 20 个实验室（每实验室 1~3 条）
- 图片：复用 seed_labs.py 的 Bing 图片下载机制，保存到 uploads/ 根目录
  （文件名 equ_{序号}_{slug}.jpg），img 字段存 /uploads/equ_xxx.jpg
- 幂等：按 (lab_id, name) 去重，已存在的记录跳过；img 会统一回填覆盖
- 前置：先运行 seed_labs.py 灌入实验室数据
"""

import sys
from pathlib import Path

# 保证从任意目录运行时都能导入 app 包与同目录的 seed_labs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import requests  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from app.config import UPLOAD_DIR  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.equipment import Equipment  # noqa: E402
from app.models.lab import Lab  # noqa: E402
from seed_labs import _download, _search_image_urls  # noqa: E402  复用 Bing 搜索/下载

# 50 条测试数据：(所属实验室名称, 设备名称, 型号规格, 数量, 状态, 说明)
EQUIPMENTS = [
    # 网络安全实验室
    ("网络安全实验室", "下一代防火墙", "深信服 AF-2000", 4, 1, "网络边界防护，支持入侵防御与流量审计。"),
    ("网络安全实验室", "渗透测试平台主机", "Kali Linux 定制整机", 20, 1, "预装渗透测试工具链，用于攻防实训。"),
    ("网络安全实验室", "核心路由器", "思科 ISR-4451", 6, 1, "实验网络核心路由，支持 VLAN 与 VPN 实验。"),
    # 人工智能实验室
    ("人工智能实验室", "GPU 训练服务器", "NVIDIA DGX A100", 2, 1, "8 卡 A100，用于大模型训练与推理实验。"),
    ("人工智能实验室", "深度学习工作站", "RTX 4090 / i9", 8, 1, "单卡训练小型模型，供课程实验使用。"),
    ("人工智能实验室", "数据标注一体机", "LabelStudio 定制机", 10, 1, "图像/文本标注平台终端。"),
    # 嵌入式系统实验室
    ("嵌入式系统实验室", "嵌入式开发板", "STM32F407 探索者", 30, 1, "ARM Cortex-M4 开发板，配套例程齐全。"),
    ("嵌入式系统实验室", "FPGA 开发板", "Xilinx Zynq-7020", 15, 1, "SoC FPGA，支持数字系统设计实验。"),
    ("嵌入式系统实验室", "数字示波器", "泰克 TBS2104", 6, 0, "100MHz 四通道，一台故障待修。"),
    # 云计算实验室
    ("云计算实验室", "机架式服务器", "Dell PowerEdge R740", 24, 1, "OpenStack 计算节点，双路至强。"),
    ("云计算实验室", "超融合管理节点", "华为 FusionCube", 2, 1, "虚拟化管理与调度控制面。"),
    ("云计算实验室", "SAN 存储阵列", "华为 OceanStor 5300", 4, 1, "块存储资源池，承载虚拟机镜像。"),
    # 软件工程实验室
    ("软件工程实验室", "软件开发工作站", "i7-13700 / 32G", 40, 1, "日常编码与构建环境终端。"),
    ("软件工程实验室", "智能交互白板", "MAXHUB 86 寸", 4, 1, "敏捷开发看板与需求评审使用。"),
    ("软件工程实验室", "持续集成服务器", "Jenkins CI 节点", 2, 1, "流水线构建与自动化测试。"),
    # 物联网实验室
    ("物联网实验室", "树莓派实验套件", "Raspberry Pi 4B", 25, 1, "含传感器配件包，用于边缘计算实验。"),
    ("物联网实验室", "物联网智能网关", "研华 ECU-1251", 10, 1, "支持 Modbus/MQTT 协议转换。"),
    ("物联网实验室", "多传感器实验箱", "定制传感器套件", 20, 1, "温湿度、光照、红外等传感器集成。"),
    # 大数据分析实验室
    ("大数据分析实验室", "Spark 集群节点", "Hadoop/Spark 定制", 12, 1, "大数据处理集群工作节点。"),
    ("大数据分析实验室", "数据可视化大屏", "利亚德 P1.8 LED", 2, 1, "实时数据大屏展示。"),
    ("大数据分析实验室", "数据采集网关节点", "Flume/Kafka 节点", 6, 0, "两台网卡故障，维修中。"),
    # 机器人实验室
    ("机器人实验室", "协作机械臂", "UR5 CB 系列", 4, 1, "六轴协作臂，支持 ROS 控制。"),
    ("机器人实验室", "轮式移动机器人", "TurtleBot3 汉堡版", 8, 1, "SLAM 与导航算法实验平台。"),
    ("机器人实验室", "RoboMaster 战车", "大疆 RM 步兵", 6, 1, "机器人竞赛训练用车。"),
    # 计算机视觉实验室
    ("计算机视觉实验室", "工业相机", "Basler acA1300", 10, 1, " GigE 接口，用于图像采集实验。"),
    ("计算机视觉实验室", "深度相机", "Intel RealSense D435", 8, 1, "深度/双目视觉与点云实验。"),
    ("计算机视觉实验室", "目标检测实验平台", "Jetson Orin Nano", 10, 1, "边缘端模型推理部署实验。"),
    # 量子计算实验室（建设中）
    ("量子计算实验室", "量子计算模拟服务器", "Qiskit 仿真集群", 2, 1, "量子线路与算法仿真平台。"),
    ("量子计算实验室", "低温实验控制柜", "定制恒温控制", 1, 1, "低温电子学实验环境控制。"),
    # 数据库系统实验室
    ("数据库系统实验室", "数据库服务器", "MySQL/PG 双环境", 8, 1, "数据库原理与调优课程实验机。"),
    ("数据库系统实验室", "磁盘阵列", "Dell MD3600F", 4, 1, "RAID 实验与数据存储。"),
    # 操作系统实验室
    ("操作系统实验室", "内核开发实验机", "Linux 定制整机", 30, 1, "内核编译与调试环境。"),
    ("操作系统实验室", "USB 串口调试器", "FT232 模块", 10, 1, "串口通信与内核日志查看。"),
    # 编译原理实验室
    ("编译原理实验室", "程序设计实训终端", "i5 / 16G", 40, 1, "词法/语法分析器开发环境。"),
    # 图形图像实验室
    ("图形图像实验室", "图形渲染工作站", "RTX A5000 / i9", 10, 1, "三维渲染与建模专用终端。"),
    ("图形图像实验室", "三维扫描仪", "EinScan Pro 2X", 2, 1, "实物三维重建与点云处理。"),
    # 移动应用开发实验室
    ("移动应用开发实验室", "iPhone 测试机", "iPhone 14 / 15", 10, 1, "iOS 应用真机调试。"),
    ("移动应用开发实验室", "Android 真机测试机", "小米/华为混编", 15, 1, "Android 应用兼容性测试。"),
    ("移动应用开发实验室", "鸿蒙开发板", "润和 HiSpark", 8, 1, "鸿蒙原生应用与设备开发。"),
    # 区块链实验室（建设中）
    ("区块链实验室", "区块链服务器节点", "Hyperledger 定制", 6, 1, "联盟链节点部署实验。"),
    ("区块链实验室", "密码学实验箱", "定制实验套件", 10, 0, "一台电源故障，维修中。"),
    # 自然语言处理实验室
    ("自然语言处理实验室", "NLP 训练服务器", "A800 单卡节点", 4, 1, "语料训练与大模型微调。"),
    ("自然语言处理实验室", "语料存储服务器", "NAS 48TB", 2, 1, "语料库集中存储与分发。"),
    # 信息安全对抗实验室
    ("信息安全对抗实验室", "CTF 竞赛主机", "定制竞赛平台", 20, 1, "CTF 训练与校内赛专用。"),
    ("信息安全对抗实验室", "无线安全审计设备", "WiFi Pineapple", 5, 1, "无线网络安全评估实验。"),
    # 智能硬件实验室
    ("智能硬件实验室", "桌面级 3D 打印机", "拓竹 X1 Carbon", 6, 1, "结构原型快速打印。"),
    ("智能硬件实验室", "PCB 刻板机", "意创 QC-3040", 3, 1, "电路板快速制版。"),
    ("智能硬件实验室", "防静电焊接工作站", "白光 936 定制", 10, 1, "贴片焊接与返修工位。"),
    # 虚拟现实实验室
    ("虚拟现实实验室", "VR 一体机头显", "Meta Quest 3", 8, 1, "虚拟仿真应用开发与体验。"),
    ("虚拟现实实验室", "光学动作捕捉系统", "OptiTrack Prime", 1, 0, "定位相机故障，返厂维修。"),
]

# 设备名称 → (文件名 slug, Bing 搜索关键词)
EQUIP_IMAGES = {
    "下一代防火墙": ("01_firewall", "防火墙 网络安全 设备 机房"),
    "渗透测试平台主机": ("02_pentest", "渗透测试 Kali 黑客 电脑"),
    "核心路由器": ("03_router", "思科 路由器 机架 网络设备"),
    "GPU 训练服务器": ("04_gpu_server", "GPU 服务器 AI 深度学习 机柜"),
    "深度学习工作站": ("05_dl_workstation", "深度学习 工作站 RTX 电脑"),
    "数据标注一体机": ("06_annotation", "数据标注 人工智能 屏幕"),
    "嵌入式开发板": ("07_mcu_board", "STM32 开发板 单片机"),
    "FPGA 开发板": ("08_fpga_board", "FPGA 开发板 Xilinx 电路"),
    "数字示波器": ("09_oscilloscope", "泰克 数字示波器 实验室"),
    "机架式服务器": ("10_rack_server", "机架式服务器 数据中心"),
    "超融合管理节点": ("11_hci_node", "超融合 服务器 数据中心"),
    "SAN 存储阵列": ("12_san_storage", "存储阵列 数据中心 硬盘"),
    "软件开发工作站": ("13_dev_pc", "程序员 开发 电脑 多屏幕"),
    "智能交互白板": ("14_smart_board", "智能交互白板 会议 触摸屏"),
    "持续集成服务器": ("15_ci_server", "服务器机房 Linux 运维"),
    "树莓派实验套件": ("16_raspi_kit", "树莓派 开发板 传感器"),
    "物联网智能网关": ("17_iot_gateway", "物联网 网关 工业设备"),
    "多传感器实验箱": ("18_sensor_box", "传感器 实验箱 电子 模块"),
    "Spark 集群节点": ("19_spark_node", "服务器集群 大数据 机房"),
    "数据可视化大屏": ("20_led_wall", "数据可视化 大屏 LED 指挥中心"),
    "数据采集网关节点": ("21_collect_node", "服务器 机柜 网线 数据中心"),
    "协作机械臂": ("22_robot_arm", "UR 机械臂 协作机器人"),
    "轮式移动机器人": ("23_mobile_robot", "轮式机器人 SLAM 传感器"),
    "RoboMaster 战车": ("24_robomaster", "RoboMaster 机器人 比赛"),
    "工业相机": ("25_industrial_cam", "工业相机 机器视觉 Basler"),
    "深度相机": ("26_depth_cam", "深度相机 RealSense 3D"),
    "目标检测实验平台": ("27_jetson", "Jetson 边缘计算 开发板"),
    "量子计算模拟服务器": ("28_quantum_sim", "量子计算 服务器 科研"),
    "低温实验控制柜": ("29_cryostat", "低温 实验 设备 实验室"),
    "数据库服务器": ("30_db_server", "数据库 服务器 机房"),
    "磁盘阵列": ("31_disk_array", "磁盘阵列 存储 服务器"),
    "内核开发实验机": ("32_kernel_pc", "Linux 内核 开发 代码 屏幕"),
    "USB 串口调试器": ("33_usb_serial", "串口调试 USB 电子工具"),
    "程序设计实训终端": ("34_training_pc", "计算机教室 学生 电脑"),
    "图形渲染工作站": ("35_render_pc", "图形工作站 渲染 3D 建模"),
    "三维扫描仪": ("36_3d_scanner", "三维扫描仪 3D 扫描"),
    "iPhone 测试机": ("37_iphone", "iPhone 手机 测试 桌面"),
    "Android 真机测试机": ("38_android", "安卓 手机 测试 多台"),
    "鸿蒙开发板": ("39_harmony_board", "鸿蒙 开发板 物联网"),
    "区块链服务器节点": ("40_blockchain", "区块链 服务器 分布式"),
    "密码学实验箱": ("41_crypto_box", "密码学 实验 电子 设备"),
    "NLP 训练服务器": ("42_nlp_server", "AI 服务器 机器学习 机柜"),
    "语料存储服务器": ("43_nas", "NAS 存储 硬盘阵列"),
    "CTF 竞赛主机": ("44_ctf_pc", "黑客 竞赛 电脑 代码"),
    "无线安全审计设备": ("45_wifi_audit", "无线安全 WiFi 天线 设备"),
    "桌面级 3D 打印机": ("46_3d_printer", "3D 打印机 桌面 打印"),
    "PCB 刻板机": ("47_pcb_machine", "PCB 电路板 制造 机器"),
    "防静电焊接工作站": ("48_soldering", "电烙铁 焊接 电子 工作台"),
    "VR 一体机头显": ("49_vr_headset", "VR 头显 虚拟现实 Quest"),
    "光学动作捕捉系统": ("50_mocap", "动作捕捉 相机 光学"),
}

assert len(EQUIPMENTS) == 50, f"设备条数应为 50，当前 {len(EQUIPMENTS)}"
assert len({name for _, name, *_ in EQUIPMENTS}) == 50, "设备名称必须全局唯一（保证图片映射不冲突）"


def equip_img_url(name: str) -> str:
    slug, _ = EQUIP_IMAGES[name]
    return f"/uploads/equ_{slug}.jpg"


def ensure_images() -> None:
    """从 Bing 下载设备图片，保存到 uploads/ 根目录；已存在的跳过"""
    for name, (slug, query) in EQUIP_IMAGES.items():
        path = UPLOAD_DIR / f"equ_{slug}.jpg"
        if path.exists() and path.stat().st_size > 0:
            continue
        try:
            candidates = _search_image_urls(query)
        except requests.RequestException:
            print(f"  搜索失败：{name}")
            continue
        for url in candidates:
            content = _download(url)
            if content:
                path.write_bytes(content)
                print(f"  图片就绪：{name} -> {path.name} ({len(content) // 1024}KB)")
                break
        else:
            print(f"  下载失败：{name}，该条 img 保持为空")


def seed() -> None:
    print("[1/3] 从 Bing 下载设备图片（已存在的跳过）")
    ensure_images()

    db = SessionLocal()
    try:
        print("[2/3] 写入设备数据")
        lab_ids = {name: id for name, id in db.query(Lab.name, Lab.id).all()}
        missing = {lab for lab, *_ in EQUIPMENTS} - set(lab_ids)
        if missing:
            raise SystemExit(f"labs 表缺少以下实验室，请先运行 seed_labs.py：{missing}")

        existing = {
            (lab_id, name)
            for lab_id, name in db.query(Equipment.lab_id, Equipment.name).all()
        }
        created, skipped = 0, 0
        for lab_name, name, spec, quantity, status, desc in EQUIPMENTS:
            if (lab_ids[lab_name], name) in existing:
                skipped += 1
                continue
            db.add(
                Equipment(
                    lab_id=lab_ids[lab_name],
                    name=name,
                    spec=spec,
                    quantity=quantity,
                    status=status,
                    description=desc,
                    img=equip_img_url(name),
                )
            )
            created += 1
        db.commit()

        print("[3/3] 回填 img（统一覆盖为最新路径）")
        for name in EQUIP_IMAGES:
            row = db.query(Equipment).filter(Equipment.name == name).first()
            if row:
                row.img = equip_img_url(name)
        db.commit()
    except IntegrityError:
        db.rollback()
        print("写入失败：数据库约束冲突，已回滚")
        raise
    finally:
        db.close()

    total = 0
    db = SessionLocal()
    try:
        total = db.query(Equipment).count()
    finally:
        db.close()

    print(f"完成：新增 {created} 条，跳过（已存在）{skipped} 条，equipments 表当前共 {total} 条")


if __name__ == "__main__":
    seed()
