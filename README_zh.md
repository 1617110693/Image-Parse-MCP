# Image Parse MCP

[![English Docs](https://img.shields.io/badge/Docs-English-blue)](README.md)

一个多模态图片分析 MCP 服务器，可接入**任意兼容 OpenAI 接口格式的大模型厂商**。传入图片（URL、本地路径或 Base64）和分析提示词，即可获取多模态大模型返回的详细分析结果。

## 支持的厂商

任何提供 OpenAI 兼容 chat completions 接口的厂商均可接入：

- **OpenAI** — GPT-4o、GPT-4-vision、GPT-4.1-mini
- **Anthropic**（通过兼容代理/网关）
- **Google Gemini**（通过 OpenAI 兼容接口）
- **Azure OpenAI**
- **本地模型**（Ollama、vLLM、LM Studio 等支持 OpenAI 兼容接口的服务）
- **第三方**（DeepSeek、Groq、Together.ai、OpenRouter 等）

## 配置

启动服务器前，设置以下环境变量：

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `IMAGE_PARSE_API_KEY` | **是** | — | 厂商 API 密钥 |
| `IMAGE_PARSE_BASE_URL` | 否 | `https://api.openai.com/v1` | API 基础地址 |
| `IMAGE_PARSE_MODEL` | 否 | `gpt-4o` | 多模态模型名称 |

### 示例：OpenAI

```bash
export IMAGE_PARSE_API_KEY=sk-...
export IMAGE_PARSE_BASE_URL=https://api.openai.com/v1
export IMAGE_PARSE_MODEL=gpt-4o
```

### 示例：Google Gemini（通过 AI Studio）

```bash
export IMAGE_PARSE_API_KEY=你的-gemini-api-key
export IMAGE_PARSE_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
export IMAGE_PARSE_MODEL=gemini-2.5-flash
```

### 示例：Ollama（本地）

```bash
export IMAGE_PARSE_API_KEY=ollama
export IMAGE_PARSE_BASE_URL=http://localhost:11434/v1
export IMAGE_PARSE_MODEL=llava
```

### 示例：Azure OpenAI

```bash
export IMAGE_PARSE_API_KEY=你的-azure-api-key
export IMAGE_PARSE_BASE_URL=https://你的资源名.openai.azure.com/openai/deployments/你的部署名
export IMAGE_PARSE_MODEL=gpt-4o
```

### 示例：阿里云百炼（通义千问）

```bash
export IMAGE_PARSE_API_KEY=你的-dashscope-api-key
export IMAGE_PARSE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export IMAGE_PARSE_MODEL=qwen-vl-max
```

### 示例： DeepSeek

```bash
export IMAGE_PARSE_API_KEY=你的-deepseek-api-key
export IMAGE_PARSE_BASE_URL=https://api.deepseek.com/v1
export IMAGE_PARSE_MODEL=deepseek-chat
```

## 安装与运行

```bash
# 进入项目目录
cd image-parse

# 直接运行（uv 会自动处理虚拟环境和依赖）
uv run image-parse-mcp
```

### Claude Code 配置

在 Claude Code 的 MCP 配置文件中添加（`~/.claude/claude.json` 或项目中的 `.mcp.json`）：

```json
{
  "mcpServers": {
    "image-parse": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "path/to/image-parse", "image-parse-mcp"],
      "env": {
        "IMAGE_PARSE_API_KEY": "sk-...",
        "IMAGE_PARSE_BASE_URL": "https://api.openai.com/v1",
        "IMAGE_PARSE_MODEL": "gpt-4o"
      }
    }
  }
}
```

## 工具：`analyze_image`

| 参数 | 必填 | 说明 |
|------|------|------|
| `image_source` | 是 | 图片 URL、本地文件路径、Base64 字符串或 data URI |
| `prompt` | 是 | 需要分析/提取的内容描述 |
| `mime_type` | 否 | 手动指定 MIME 类型（如 `image/webp`），不填则自动检测 |

### 适用场景

- 描述图片内容
- 从截图中提取文字（OCR）
- 解读图表、图形、数据可视化
- 分析 UI 截图（布局、元素、问题）
- 识别照片中的物体、颜色、人物或场景
- 对比多张图片中的视觉信息
- 根据错误截图诊断问题

### `image_source` 支持的输入格式

```
# URL
https://example.com/screenshot.png

# 本地文件路径（服务器所在主机）
/Users/me/Downloads/chart.png

# Base64 data URI
data:image/png;base64,iVBORw0KGgo...

# 原始 Base64
iVBORw0KGgo...
```

## 开发

```bash
# 创建虚拟环境并安装依赖
uv venv
uv pip install -e .

# 运行测试
uv run python -m pytest
```
