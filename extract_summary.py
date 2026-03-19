import argparse
import json
import os
import re
import sys
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from open_ai_api import translate_project_description


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def strip_markdown(text):
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    return text


def extract_intro(readme):
    lines = [line.strip() for line in readme.splitlines()]
    cleaned = []
    for line in lines:
        if not line:
            if cleaned:
                break
            continue
        if line.startswith("![") or line.startswith("[!["):
            continue
        if line.startswith("#"):
            continue
        cleaned.append(line)
        if len(cleaned) >= 3:
            break
    return strip_markdown(" ".join(cleaned))


def find_section(readme, keywords):
    lines = readme.splitlines()
    current = []
    capture = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().lower()
            if any(keyword.lower() in heading for keyword in keywords):
                capture = True
                current = []
                continue
            if capture:
                break
        if capture:
            if stripped:
                current.append(stripped)
            if len(current) >= 6:
                break
    return current


def extract_stack(readme, language):
    candidates = find_section(readme, ["tech stack", "technology", "stack", "built with", "技术栈", "技术选型"])
    items = []
    for line in candidates:
        if line.startswith(("-", "*", "•")):
            items.append(strip_markdown(line.lstrip("-*• ").strip()))
        elif line[:2].isdigit() and line[1] == ".":
            items.append(strip_markdown(line[2:].strip()))
        if len(items) >= 5:
            break
    if not items and candidates:
        items = [strip_markdown(candidates[0])]
    if language:
        if not items:
            items.append(language)
        elif language not in " ".join(items):
            items.insert(0, language)
    return "、".join([item for item in items if item])


def summarize_item(item):
    description = item.get("description") or "暂无公开描述"
    readme = item.get("readme") or ""
    stack = extract_stack(readme, item.get("language"))
    stars = item.get("stargazers_count") or 0
    name = item.get("name")
    lines = [
        f"{item.get('rank')}. {name}",
        f"项目简介：{description}",
        f"技术栈：{stack or '暂无公开信息'}",
        f"Star 数量：{stars}",
        f"项目地址：{item.get('html_url')}",
    ]
    return "\n".join(lines)


def build_message(data):
    date_str = datetime.now().strftime("%Y-%m-%d")
    items = data.get("items", [])
    header = f"今日 GitHub Trending Top {len(items)}（{date_str}）"
    body = "\n\n".join(summarize_item(item) for item in items)
    return f"{header}\n\n{body}".strip()


def send_wecom(webhook, content):
    payload = {"msgtype": "text", "text": {"content": content}}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(webhook, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="trending_top5.json")
    parser.add_argument("--webhook", default=os.getenv("WEIXIN_WEBHOOK"))
    args = parser.parse_args()

    if not args.webhook:
        print("发送失败: 请先在环境变量 WEIXIN_WEBHOOK 中配置企业微信 webhook", file=sys.stderr)
        raise SystemExit(1)

    try:
        data = read_json(args.input)
        content = build_message(data)
        try:
            content = translate_project_description(content)
        except Exception as exc:
            print(f"翻译失败，已使用原文发送: {exc}", file=sys.stderr)
        result = send_wecom(args.webhook, content)
    except (HTTPError, URLError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"发送失败: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(result)


if __name__ == "__main__":
    main()