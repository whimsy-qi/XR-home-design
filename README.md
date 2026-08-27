# XR Home Design

XR Home Design 是一个面向家装设计场景的前后端项目，包含 Vue 3 前端、Django REST 后端，以及本地集成的 SAM2 相关视觉能力代码。

## 项目结构

```text
.
├── vision/                 # Vue 3 + Vite 前端
│   ├── public/             # 静态资源
│   └── src/                # 前端源码、路由、状态和页面组件
├── XRdjangoProject/         # Django 后端工程
│   ├── accounts/           # 用户账号模块
│   ├── ai_generator/       # AI 生成相关接口和任务
│   ├── main/               # 业务主模块
│   ├── sam2_core/          # SAM2 视觉分割相关代码
│   ├── templates/          # Django 模板
│   └── XRdjangoProject/    # Django 项目配置
├── .env.example            # 后端环境变量模板
└── XR项目工程归档说明文档.docx
```

## 后端启动

```bash
cd XRdjangoProject
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

启动前需要在 `.env` 中补全数据库、OSS、AI 服务等实际配置。

## 前端启动

```bash
cd vision
npm install
npm run dev
```

前端默认调用本地后端地址 `http://127.0.0.1:8000` 或 `http://localhost:8000`。

## 仓库说明

- `HomeXR0718.zip` 是本地归档压缩包，体积约 25GB，不适合提交到 GitHub。
- `.env`、虚拟环境、`node_modules`、构建产物、模型权重和运行时上传文件已通过 `.gitignore` 排除。
- `vision` 原本包含独立 `.git` 目录，已备份为 `vision/.git-backup-before-root-import/`，根仓库会直接管理前端源码。
