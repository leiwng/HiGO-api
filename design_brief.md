# 项目核心实现简报

## 项目架构概览

该项目采用了清晰的分层架构：

### 核心组件

1. **API 层** (app/api/v1/)
   - `chat.py` - 实现文本和图片咨询的流式 API 端点
   - `login.py` - JWT 认证端点

2. **业务逻辑层** (app/services/)
   - `ChatService` - 核心聊天业务逻辑，处理文本和图片咨询流程
   - `LLMService` - 调用 ds-vet-answer-32B 文本模型
   - `MultiModalService` - 调用 ds-vet-vl-72B 多模态模型
   - `PetInfoService` - 获取宠物信息
   - `MongoService` - MongoDB 对话历史存储

3. **配置和工具层**
   - `Settings` - 统一配置管理，支持环境变量
   - `AsyncHttpClient` - 异步 HTTP 客户端
   - `generate_signature` - HMAC-SHA256 签名工具

## 核心技术实现

### 1. 流式响应处理
使用 FastAPI 的 `StreamingResponse` 实现 Server-Sent Events：

```python
return StreamingResponse(
    response_stream,
    media_type="text/event-stream",
    headers={
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }
)
```

### 2. 多模态 API 集成
支持 6 种图片分析类型：
- `EMOTION` - 情绪识别
- `FECES` - 粪便分析
- `SKIN` - 皮肤分析
- `URINE` - 尿液分析
- `VOMITUS` - 呕吐物分析
- `EAR_CANAL` - 耳道分析

### 3. 认证与安全
- JWT Token 认证机制
- HMAC-SHA256 签名验证（用于多模态 API）
- 基于 Redis 的速率限制

### 4. 异步处理
全面采用 `async/await` 模式，使用 `asyncio.gather()` 并发处理多个异步任务

### 5. 错误处理与日志
- 全局异常处理器
- 使用 Loguru 进行结构化日志记录
- 请求追踪中间件

## 数据流程

### 文本咨询流程：
1. 并发获取宠物信息和对话历史
2. 执行 RAG 知识检索（当前为模拟实现）
3. 构建综合提示词
4. 调用 LLM 进行流式响应
5. 保存对话历史到 MongoDB

### 图片咨询流程：
1. 并发获取宠物信息和对话历史
2. 使用多模态模型分析所有图片
3. 结合图片分析结果和 RAG 知识构建提示词
4. 调用 LLM 进行流式响应
5. 保存对话历史

## 外部服务集成

- **文本模型**: ds-vet-answer-32B (通过 OpenAI 兼容接口)
- **多模态模型**: ds-vet-vl-72B (自定义 HMAC 签名认证)
- **数据存储**: MongoDB + Redis
- **宠物信息**: 第三方 API (HMAC-SHA256 认证)

## 配置管理

使用 Pydantic Settings 从 .env 文件 加载配置，支持开发和生产环境分离。

## 容器化部署

提供了 Dockerfile 实现 Docker 化部署，适用于云环境。

项目整体实现非常完善，遵循了现代 Python Web 服务的最佳实践，具有良好的可扩展性和维护性。