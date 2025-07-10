# Meddy API Hub

```shell
 ███            █████████  ██████████ ██████   ██████ █████ ██████   █████ █████
░░░███         ███░░░░░███░░███░░░░░█░░██████ ██████ ░░███ ░░██████ ░░███ ░░███
  ░░░███      ███     ░░░  ░███  █ ░  ░███░█████░███  ░███  ░███░███ ░███  ░███
    ░░░███   ░███          ░██████    ░███░░███ ░███  ░███  ░███░░███░███  ░███
     ███░    ░███    █████ ░███░░█    ░███ ░░░  ░███  ░███  ░███ ░░██████  ░███
   ███░      ░░███  ░░███  ░███ ░   █ ░███      ░███  ░███  ░███  ░░█████  ░███
 ███░         ░░█████████  ██████████ █████     █████ █████ █████  ░░█████ █████
░░░            ░░░░░░░░░  ░░░░░░░░░░ ░░░░░     ░░░░░ ░░░░░ ░░░░░    ░░░░░ ░░░░░
```

## 项目概述

使用 Python + FastAPI 开发一个宠物疾病问答的聊天 API 服务，支持文本咨询和图片咨询两种模式。

## 项目结构概览

```tree
    1 .
    2 ├── app/                  # FastAPI应用核心代码
    3 │   ├── api/              # API路由和端点
    4 │   ├── core/             # 配置、日志、安全
    5 │   ├── models/           # Pydantic数据模型
    6 │   ├── services/         # 业务逻辑服务
    7 │   └── utils/            # 辅助工具
    8 ├── .env                  # 环境变量配置
    9 ├── Dockerfile            # Docker容器化配置
   10 ├── pet_breed_0dd7f7.json # 宠物品种ID映射
   11 ├── requirements.txt      # Python依赖列表
   12 └── GEMINI.md             # 您的原始需求文档
```

## 文件结构

```tree
    1 .
    2 ├── app/
    3 │   ├── api/
    4 │   │   ├── __init__.py
    5 │   │   └── v1/
    6 │   │       ├── __init__.py
    7 │   │       ├── endpoints/
    8 │   │       │   ├── __init__.py
    9 │   │       │   ├── chat.py         # 聊天API路由
   10 │   │       │   └── login.py        # 认证API路由
   11 │   │       └── api.py              # API路由聚合
   12 │   ├── core/
   13 │   │   ├── __init__.py
   14 │   │   ├── config.py               # 配置管理
   15 │   │   ├── logging.py              # 日志配置
   16 │   │   └── security.py             # 安全和认证
   17 │   ├── models/
   18 │   │   ├── __init__.py
   19 │   │   ├── chat.py                 # 聊天相关的Pydantic模型
   20 │   │   ├── pet.py                  # 宠物相关的Pydantic模型
   21 │   │   ├── token.py                # Token相关的Pydantic模型
   22 │   │   └── user.py                 # 用户相关的Pydantic模型
   23 │   ├── services/
   24 │   │   ├── __init__.py
   25 │   │   ├── chat_service.py         # 聊天核心业务逻辑
   26 │   │   ├── external/
   27 │   │   │   ├── __init__.py
   28 │   │   │   ├── llm_service.py      # 文本大模型服务
   29 │   │   │   ├── multimodal_service.py # 多模态模型服务
   30 │   │   │   └── pet_info_service.py # 宠物信息服务
   31 │   │   └── storage/
   32 │   │       ├── __init__.py
   33 │   │       └── mongo_service.py    # MongoDB服务
   34 │   ├── utils/
   35 │   │   ├── __init__.py
   36 │   │   ├── http_client.py          # 异步HTTP客户端
   37 │   │   └── signature.py            # HMAC签名工具
   38 │   ├── __init__.py
   39 │   └── main.py                     # FastAPI应用入口
   40 ├── .env                            # 环境变量
   41 ├── Dockerfile                      # Docker配置文件
   42 ├── pet_breed_0dd7f7.json           # 宠物品种数据
   43 └── requirements.txt                # Python依赖
```

## 核心功能实现摘要

- **API 端点:** 在 app/api/v1/endpoints/ 中实现了文本 (chat.py) 和图片 (chat.py) 咨询接口，以及 JWT 认证 (login.py)。
- **配置管理:** app/core/config.py 使用 Pydantic 从 .env 文件加载所有配置，实现开发和生产环境的轻松分离。
- **外部服务调用:** 在 app/services/external/ 中，分别封装了对大语言模型、多模态模型和宠物信息服务的调用逻辑，包含了签名认证和错误处理。
- **异步处理:** 整个应用基于 asyncio 和 FastAPI 构建，外部 API 调用使用 httpx.AsyncClient，确保了高并发性能。
- **流式响应:** 聊天接口使用 StreamingResponse 和 text/event-stream，实现了对大模型结果的流式输出。
- **日志与错误处理:** 在 app/main.py 和 app/core/logging.py 中配置了全局日志、异常捕获和请求日志中间件。

## 运行和部署

1. 环境准备:

- 安装 Python: 请确保您的系统上已安装 Python (推荐 3.8 或更高版本)，并且 python 和 pip 命令在您的终端或命令提示符中可用。
- 安装 Docker (可选): 如果您打算使用 Dockerfile 来运行此服务，请确保已安装并运行 Docker Desktop (https://www.docker.com/products/docker-desktop/)。
- 启动依赖服务: 本项目需要 MongoDB 和 Redis。请确保它们正在运行。如果您使用 Docker，可以很方便地通过 docker-compose 来启动这两个服务。

1. 安装依赖包:

请在项目根目录 (D:\Prj\github\gemini-cli-deployment) 打开您的终端，然后运行以下命令来安装所有必需的 Python 库：

pip install -r requirements.txt

如果您有多个 Python 版本，建议使用 `python -m pip install -r requirements.txt`

1. 启动 API 服务:

安装完依赖后，运行以下命令来启动 FastAPI 应用：

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

1. 访问服务:

服务启动后，您可以：

- 访问 API 文档: 在浏览器中打开 <http://localhost:8000/api/v1/openapi.json> (<http://localhost:8000/api/v1/openapi.json>) 查看交互式 API 文档 (Swagger UI)。在这里您可以浏览所有 API 端点、它们的参数，并直接进行测试。
- 查看根路径: 访问 <http://localhost:8000/> (<http://localhost:8000/>) 会看到欢迎信息。
