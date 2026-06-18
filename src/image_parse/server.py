"""
MCP Server: Image Parse — multimodal image analysis via OpenAI-compatible APIs.

Configure via environment variables:
  IMAGE_PARSE_BASE_URL  — API base URL (default: https://api.openai.com/v1)
  IMAGE_PARSE_API_KEY   — API key (required)
  IMAGE_PARSE_MODEL     — Model name (default: gpt-4o)

Usage (stdio):
  uv run image-parse-mcp
"""

import os
import base64
import re
from pathlib import Path
from typing import Optional

import httpx
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# ── Configuration (OpenAI-compatible) ────────────────────────────────────────
BASE_URL = os.getenv("IMAGE_PARSE_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("IMAGE_PARSE_API_KEY", "")
MODEL = os.getenv("IMAGE_PARSE_MODEL", "gpt-4o")

mcp = FastMCP("image_parse_mcp")

# ── Pydantic input model ────────────────────────────────────────────────────


class AnalyzeImageInput(BaseModel):
    """Input model for the analyze_image tool."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    image_source: str = Field(
        ...,
        description=(
            "Image to analyze. Accepted forms:\n"
            "1) URL — 'https://example.com/photo.jpg'\n"
            "2) Local file path — '/Users/me/Downloads/chart.png'\n"
            "3) Base64 data URI — 'data:image/png;base64,iVBORw0K…'\n"
            "4) Raw base64 string — 'iVBORw0K…'"
        ),
        min_length=1,
    )
    prompt: str = Field(
        ...,
        description=(
            "What to analyze, extract, or understand from the image. "
            "Be specific — e.g. 'Describe every element in this UI screenshot', "
            "'Extract the text from this document', "
            "'What objects are in this photo and how are they arranged?', "
            "'Read the numbers from this chart and identify trends'."
        ),
        min_length=1,
        max_length=8000,
    )
    mime_type: Optional[str] = Field(
        default=None,
        description=(
            "MIME type of the image (e.g. 'image/png', 'image/jpeg', 'image/webp'). "
            "Auto-detected from the source when omitted — provide only when the "
            "auto-detection guesses wrong."
        ),
        pattern=r"^image/\w+$",
    )


# ── Helpers ──────────────────────────────────────────────────────────────────


def _detect_mime_type(source: str) -> str:
    """Best-effort MIME type detection from an image source string."""
    # 1) Data-URI header: data:image/png;base64,…
    m = re.match(r"^data:(image/[\w+.-]+);", source)
    if m:
        return m.group(1)

    # 2) Common image file extensions (URL or file path)
    ext_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".svg": "image/svg+xml",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".ico": "image/x-icon",
    }
    # Strip query / fragment for URLs
    stem = source.split("?")[0].split("#")[0].lower()
    for ext, mime in ext_map.items():
        if stem.endswith(ext):
            return mime

    # 3) Fallback
    return "image/png"


def _load_image_b64(source: str, mime_type: Optional[str] = None) -> str:
    """Convert *source* into a ``data:<mime>;base64,<payload>`` string."""
    # --- raw base64 (no data-uri prefix, no file / url pattern) ---
    if not re.match(r"^(data:|https?://|[a-zA-Z]:|/|\./)", source):
        mime = mime_type or _detect_mime_type(source)
        return f"data:{mime};base64,{source}"

    # --- data-uri: already complete ---
    if source.startswith("data:"):
        if mime_type:
            # Replace the mime part while keeping the base64 payload
            payload = source.split(",", 1)[1]
            return f"data:{mime_type};base64,{payload}"
        return source

    # --- URL ---
    if re.match(r"^https?://", source):
        mime = mime_type or _detect_mime_type(source)
        # OpenAI-compatible vision API accepts direct URLs too, but data-uri
        # is more portable across providers. Use the URL as-is for providers
        # that support it, and also provide it as image_url.
        # We keep the URL as-is — the API call helper will decide.
        return source

    # --- local file path ---
    path = Path(source).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Path is not a file: {path}")

    mime = mime_type or _detect_mime_type(path.name)
    data = path.read_bytes()
    payload = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{payload}"


def _build_vision_message(prompt: str, image_source: str) -> dict:
    """Build an OpenAI-compatible vision user message.

    Returns a dict that can be JSON-serialised into the ``messages`` array.
    """
    content: list[dict] = [
        {"type": "text", "text": prompt},
    ]

    # If the source is already a data URI or URL use it; otherwise treat as data URI
    content.append(
        {
            "type": "image_url",
            "image_url": {"url": image_source},
        }
    )

    return {"role": "user", "content": content}


def _handle_api_error(e: Exception) -> str:
    """Produce a human-readable error from an httpx / API failure."""
    if isinstance(e, httpx.HTTPStatusError):
        detail = ""
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:500]
        return (
            f"API error {e.response.status_code}: {detail}\n\n"
            f"Hint: check your IMAGE_PARSE_API_KEY, IMAGE_PARSE_BASE_URL, "
            f"and IMAGE_PARSE_MODEL env vars."
        )
    if isinstance(e, httpx.TimeoutException):
        return "Request timed out — the model may be overloaded. Try again later."
    if isinstance(e, httpx.ConnectError):
        return (
            f"Cannot reach {BASE_URL}. "
            "Check IMAGE_PARSE_BASE_URL and your network."
        )
    return f"Unexpected error: {type(e).__name__}: {e}"


# ── Tool ─────────────────────────────────────────────────────────────────────


@mcp.tool(
    name="analyze_image",
    annotations={
        "title": "Analyze Image with Multimodal LLM",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def analyze_image(params: AnalyzeImageInput) -> str:
    """Analyze an image with a multimodal LLM (GPT-4o, Claude, Gemini, etc.).

    Provide an image (URL, local path, or base64) and a description of what
    you want to know.  The tool calls an OpenAI-compatible vision API and
    returns the model's text response.

    Use this tool whenever you have an image and need to:
    - Describe its contents
    - Extract text / OCR
    - Understand a chart, diagram, or data visualization
    - Analyse a UI screenshot (layout, elements, issues)
    - Identify objects, colours, people, or scenes in a photo
    - Compare or summarise visual information

    Args:
        params (AnalyzeImageInput):
            - image_source (str): URL, local file path, or base64 image data.
            - prompt (str): What to analyze or extract from the image.
            - mime_type (Optional[str]): Override auto-detected MIME type.

    Returns:
        str: The multimodal model's analysis as plain text / Markdown.
    """
    if not API_KEY:
        return (
            "Error: IMAGE_PARSE_API_KEY environment variable is not set.\n\n"
            "Configure the API key before using this tool:\n"
            "  export IMAGE_PARSE_API_KEY=sk-…\n\n"
            "You can also set IMAGE_PARSE_BASE_URL and IMAGE_PARSE_MODEL "
            "to customise the provider."
        )

    # ── 1. Convert image source to a format the vision API accepts ────────
    try:
        image_uri = _load_image_b64(
            params.image_source, mime_type=params.mime_type
        )
    except FileNotFoundError as e:
        return f"Error: {e}"
    except IsADirectoryError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error loading image: {type(e).__name__}: {e}"

    # ── 2. Build the request ─────────────────────────────────────────────
    message = _build_vision_message(params.prompt, image_uri)
    payload = {
        "model": MODEL,
        "messages": [message],
        "max_tokens": 4096,
    }

    # ── 3. Call the API ──────────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # ── 4. Extract & return the assistant reply ─────────────────────
        choices = data.get("choices", [])
        if not choices:
            return "The model returned an empty response — try rephrasing your prompt."

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            finish = choices[0].get("finish_reason", "unknown")
            return (
                f"Model returned empty content (finish_reason={finish}). "
                "The image may have been rejected by the provider's safety filter."
            )

        return content

    except Exception as e:
        return _handle_api_error(e)


# ── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server on stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
