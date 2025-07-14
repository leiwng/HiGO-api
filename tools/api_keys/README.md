# Tools 目录说明

这个目录包含用于生成和测试 API Key 的工具。

## 工具列表

### 1. generate_api_key.py - API Key 生成工具
生成测试用的 API Key，包括创建测试用户和账户。

**使用方法:**
```bash
cd tools
python generate_api_key.py
```

**功能:**
- 创建测试用户
- 创建测试账户（含余额）
- 生成API Key
- 设置配额和限制
- 保存到文件供后续使用

### 2. test_api_client.py - API 客户端测试工具
使用生成的API Key测试API服务。

**使用方法:**
```bash
cd tools
python test_api_client.py
```

**测试内容:**
- 健康检查
- OpenAI兼容的聊天API
- 传统聊天API
- 速率限制测试
- 响应时间测试

### 3. api_key_manager.py - API Key 管理工具
管理测试环境中的API Key。

**使用方法:**
```bash
cd tools
python api_key_manager.py
```

**功能:**
- 列出所有API Key
- 撤销/激活API Key
- 删除API Key
- 重置使用统计
- 清理已撤销的Key

## 快速开始

1. **生成API Key:**
```bash
python generate_api_key.py
```

2. **测试API:**
```bash
python test_api_client.py
```

3. **管理API Key:**
```bash
python api_key_manager.py
```

## 文件说明

- `generated_api_key.txt` - 保存最近生成的API Key
- 工具会自动从这个文件读取API Key进行测试

## 注意事项

1. 确保API服务正在运行 (默认: http://localhost:8000)
2. 确保MongoDB连接正常
3. 生成的API Key仅用于测试环境
4. 生产环境请通过正式API管理页面创建API Key