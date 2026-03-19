import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OPENAI_BASE_URL = ""
DEFAULT_OPENAI_MODEL = ""
SYSTEM_PROMPT = (
    "你是一个严格的文本翻译器。"
    "你的任务是仅对用户提供内容中的项目简介部分进行汉化为简体中文。"
    "必须保持原文中的其他内容、字段顺序、项目名、技术栈、数字、链接、代码片段、标点和换行不变。"
    "如果输入中没有明显的项目简介字段，也只翻译可识别的项目简介语句，不要改写其他内容。"
    "只输出处理后的结果，不要解释，不要添加前缀、后缀、标题或代码块。"
)


def load_env_file(path):
    values = {}
    if not path.exists():
        return values

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    return values


def get_openai_config():
    base_dir = Path(__file__).resolve().parent
    env_values = load_env_file(base_dir / ".env")
    base_url = os.getenv("OPENAI_BASE_URL") or env_values.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE_URL
    api_key = os.getenv("OPENAI_API_KEY") or env_values.get("OPENAI_API_KEY") or ""
    model = os.getenv("OPENAI_MODEL") or env_values.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "model": model,
    }


def call_openai_chat_completion(prompt_text):
    config = get_openai_config()
    if not config["api_key"]:
        raise ValueError("缺少 OPENAI_API_KEY，请在同目录 .env 中配置")

    url = f"{config['base_url']}/chat/completions"
    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text},
        ],
        "temperature": 0,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8", errors="replace"))
    return result["choices"][0]["message"]["content"].strip()


def translate_project_description(summarize: str):
    if not summarize or not summarize.strip():
        return ""
    return call_openai_chat_completion(summarize.strip())

        
    