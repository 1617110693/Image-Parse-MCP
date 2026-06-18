# Image Parse MCP

[![中文文档](https://img.shields.io/badge/文档-中文-orange)](README_zh.md)

A multimodal image analysis MCP server that connects to **any OpenAI-compatible vision API**. Provide an image (URL, local path, or base64) and a prompt — get back a detailed analysis from the multimodal LLM of your choice.

## Supported Providers

Any provider with an OpenAI-compatible chat completions endpoint:

- **OpenAI** — GPT-4o, GPT-4-vision, GPT-4.1-mini
- **Anthropic** (via compatible proxy / gateway)
- **Google Gemini** (via OpenAI-compatible endpoint)
- **Azure OpenAI**
- **Local models** (Ollama, vLLM, LM Studio with OpenAI-compatible servers)
- **Alibaba Bailian** — Qwen-VL (via OpenAI-compatible endpoint)
- **Third-party** (DeepSeek, Groq, Together.ai, OpenRouter, etc.)

## Configuration

Set these environment variables before launching the server:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IMAGE_PARSE_API_KEY` | **Yes** | — | API key for your provider |
| `IMAGE_PARSE_BASE_URL` | No | `https://api.openai.com/v1` | API base URL |
| `IMAGE_PARSE_MODEL` | No | `gpt-4o` | Multimodal model name |

### Example: OpenAI

```bash
export IMAGE_PARSE_API_KEY=sk-...
export IMAGE_PARSE_BASE_URL=https://api.openai.com/v1
export IMAGE_PARSE_MODEL=gpt-4o
```

### Example: Google Gemini (via AI Studio)

```bash
export IMAGE_PARSE_API_KEY=your-gemini-api-key
export IMAGE_PARSE_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
export IMAGE_PARSE_MODEL=gemini-2.5-flash
```

### Example: Ollama (local)

```bash
export IMAGE_PARSE_API_KEY=ollama
export IMAGE_PARSE_BASE_URL=http://localhost:11434/v1
export IMAGE_PARSE_MODEL=llava
```

### Example: Azure OpenAI

```bash
export IMAGE_PARSE_API_KEY=your-azure-api-key
export IMAGE_PARSE_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
export IMAGE_PARSE_MODEL=gpt-4o
```

### Example: Alibaba Bailian (Qwen-VL)

```bash
export IMAGE_PARSE_API_KEY=your-dashscope-api-key
export IMAGE_PARSE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export IMAGE_PARSE_MODEL=qwen-vl-max
```

### Example: DeepSeek

```bash
export IMAGE_PARSE_API_KEY=your-deepseek-api-key
export IMAGE_PARSE_BASE_URL=https://api.deepseek.com/v1
export IMAGE_PARSE_MODEL=deepseek-chat
```

## Install & Run

```bash
# Clone or enter the project directory
cd image-parse

# Run directly (uv handles venv + deps automatically)
uv run image-parse-mcp
```

### Claude Code Configuration

Add to your Claude Code MCP config (`~/.claude/claude.json` or project `.mcp.json`):

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

## Tool: `analyze_image`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `image_source` | Yes | URL, local file path, base64 string, or data URI |
| `prompt` | Yes | What to analyze / extract from the image |
| `mime_type` | No | Override auto-detected MIME type (e.g. `image/webp`) |

### What agents use it for

- Describe the contents of an image
- Extract text from a screenshot (OCR)
- Read and interpret charts, graphs, data visualizations
- Analyze UI screenshots (layout, elements, issues)
- Identify objects, colours, people, or scenes in photos
- Compare visual information across multiple images
- Diagnose errors from error screenshots

### Input forms for `image_source`

```
# URL
https://example.com/screenshot.png

# Local file path (on the host machine)
/Users/me/Downloads/chart.png

# Base64 data URI
data:image/png;base64,iVBORw0KGgo...

# Raw base64
iVBORw0KGgo...
```

## Development

```bash
# Create venv and install deps
uv venv
uv pip install -e .

# Run tests
uv run python -m pytest
```
