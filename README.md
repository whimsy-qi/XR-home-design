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

<img width="1639" height="923" alt="16a0c4c55fb3f29d658cb590f207d359" src="https://github.com/user-attachments/assets/f83ca941-071c-4169-822c-63e34f129a26" />
<img width="1641" height="921" alt="10ce42a2b2b750280b4c273bc1d7ec40" src="https://github.com/user-attachments/assets/69b7093a-ef49-46dd-8d93-cf376f88c6c3" />
<img width="1640" height="921" alt="c90e031035148251dbefcb77258d717f" src="https://github.com/user-attachments/assets/affebc30-5451-44ad-9809-9612ce2f7af7" />
<img width="1641" height="924" alt="f1fec3580eb248a124cd5e9631a7d8c1" src="https://github.com/user-attachments/assets/dc237402-d4b4-4f3a-957e-fcd8c4ee3632" />
<img width="1638" height="921" alt="78e97c98bd0747ffaa2fefbb21a009a4" src="https://github.com/user-attachments/assets/b75d9268-614d-4b7c-82e1-a2cca682ec8d" />
<img width="1640" height="917" alt="3278eef64c9143e3971e46282b934344" src="https://github.com/user-attachments/assets/248938f9-cd34-4184-bda9-62a3d4c06675" />
<img width="1641" height="921" alt="f71da4dddf348d5f8bbbfa89a162e259" src="https://github.com/user-attachments/assets/fc70112a-2610-4a44-9210-30be2316cee2" />



