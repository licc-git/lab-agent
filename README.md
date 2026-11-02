# 智能实验室预约系统说明

## 1. 项目介绍

本项目是一个前后端分离的智能实验室预约系统。用户可以查询实验室和设备、提交预约并查看预约状态；管理员可以维护实验室和设备信息、管理用户并审核预约。系统还提供基于知识库的 AI 问答功能。

### 主要功能

- **账号与用户**：用户注册、登录、个人资料和密码管理；管理员可管理用户。
- **实验室管理**：查询实验室及其开放状态，管理员可新增、编辑和删除实验室。
- **设备管理**：查询实验室设备，管理员可维护设备信息。
- **预约管理**：用户提交或取消预约、查询预约记录；管理员审核预约。
- **预约自动处理**：后端定时检查并处理过期的待审核预约。
- **AI 问答**：调用 DeepSeek 模型回答问题，并从项目知识库中检索相关内容作为参考。

### 技术组成

| 部分 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Element Plus、Axios |
| 后端 | Python 3.12、FastAPI、SQLAlchemy |
| 数据库 | MySQL |
| AI 与知识检索 | DeepSeek、LangChain、ChromaDB、Sentence Transformers |

### 目录说明

```text
backend/   FastAPI 后端、数据库模型与接口、知识库和上传文件
frontend/  Vue 前端
docs/      项目文档
```

## 2. 环境准备

启动项目前请准备：

- Python 3.12
- [uv](https://docs.astral.sh/uv/) Python 包管理器
- Node.js 22.18 及以上（或 24.12 及以上）和 npm
- MySQL
- DeepSeek API Key（仅使用 AI 问答功能时需要）

## 3. 初始化数据库

在项目根目录执行以下命令，使用 MySQL 管理员账号运行初始化脚本：

```bash
mysql -u root -p < backend/init.sql
```

脚本会创建项目数据库和本地数据库用户。若要使用其他数据库名或账号，请相应调整 `backend/init.sql` 和后端环境变量。

## 4. 配置并运行后端

在终端 A 中执行：

```bash
cd backend
cp .env.example .env
```

编辑 `backend/.env`，将 MySQL 连接配置改为与本机数据库一致：

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=lab_agent
MYSQL_PASSWORD=替换为数据库用户密码
MYSQL_DATABASE=lab_agent_db

JWT_SECRET_KEY=请设置一个随机密钥

DEEPSEEK_API_KEY=你的DeepSeek_API_Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash
```

安装后端依赖并启动：

```bash
uv sync
uv run uvicorn main:app --host 127.0.0.1 --port 8088 --reload
```

后端默认监听 `http://127.0.0.1:8088`。服务启动时会根据 SQLAlchemy 模型创建缺失的数据表；已有数据库升级时，请检查并按需执行 `backend/migrations/` 中对应的迁移脚本。

接口文档地址：<http://127.0.0.1:8088/docs>

## 5. 配置并运行前端

在终端 B 中执行：

```bash
cd frontend
npm ci
npm run dev
```

打开终端输出中显示的 Vite 地址，通常为 <http://localhost:5173>。

开发服务器会将 `/api` 和 `/uploads` 请求代理到 `http://127.0.0.1:8088`。如需为前端设置 API 基础地址，可在 `frontend/.env.development` 中配置 `VITE_API_BASE_URL`；使用本地开发代理时保持该值为空即可。

## 6. 页面预览

以下截图按登录角色分类，均为成功登录后的页面。可点击页面名称查看截图，完整清单见[截图索引](./docs/screenshots/README.md)。

### 管理员

[系统首页](./docs/screenshots/admin/01-dashboard.png) ·
[AI 助手](./docs/screenshots/admin/02-ai-assistant.png) ·
[实验室管理](./docs/screenshots/admin/03-lab-management.png) ·
[设备管理](./docs/screenshots/admin/04-equipment-management.png) ·
[预约审核](./docs/screenshots/admin/05-reservation-review.png) ·
[用户管理](./docs/screenshots/admin/06-user-management.png) ·
[个人中心](./docs/screenshots/admin/07-profile.png) ·
[密码管理](./docs/screenshots/admin/08-password.png)

### 学生

[系统首页](./docs/screenshots/student/01-dashboard.png) ·
[AI 助手](./docs/screenshots/student/02-ai-assistant.png) ·
[实验室列表](./docs/screenshots/student/03-lab-list.png) ·
[实验室详情与设备清单](./docs/screenshots/student/04-lab-equipment-detail.png) ·
[我的预约](./docs/screenshots/student/05-my-reservations.png) ·
[个人中心](./docs/screenshots/student/06-profile.png) ·
[密码管理](./docs/screenshots/student/07-password.png)

## 7. 常用命令

在 `frontend/` 目录下：

```bash
npm run build       # 构建生产版本，输出到 dist/
npm run preview     # 本地预览生产构建
```

## 8. 使用提示

- 前端和后端都需要运行；前端请求失败时，先确认后端已在 8088 端口启动。
- AI 问答需要有效的 DeepSeek API Key。首次使用知识检索时，Sentence Transformers 可能需要下载模型，请确保网络可用并预留磁盘空间。
- 后端上传文件通过 `/uploads` 提供访问；上传内容保存在 `backend/uploads/`。
