# everyday-github-trending
每日拉取github trending, 整理格式后发送给用户

在同目录创建 `.env` 并设置 `TRENDING_COUNT`、`TOP_N` 或 `COUNT`，脚本会按该数量抓取热门项目；如果当天项目不足，会按实际数量输出。

`extract_summary.py` 仅读取环境变量 `WEIXIN_WEBHOOK`，可参考下面的 `.env` 示例：

```env
TRENDING_COUNT=10
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=你的OpenAI密钥
OPENAI_MODEL=gpt-4.1-mini
WEIXIN_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的企业微信机器人key
```

## .env 示例
```
TRENDING_COUNT=10
OPENAI_BASE_URL=https://api.xiaomimimo.com/v1
OPENAI_API_KEY=
OPENAI_MODEL=mimo-v2-flash
```
