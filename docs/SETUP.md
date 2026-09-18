# SETUP — WSL2

與 trip-cut 相同基礎（WSL2 Ubuntu、Node 22、Python 3.11、Kinocut），差別：**不裝 Whisper**，多裝 edge-tts。

## 1. 系統
```bash
sudo apt update && sudo apt install -y ffmpeg python3.11 python3.11-venv build-essential \
  libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 libasound2 libxshmfence1 fonts-noto-cjk
```

## 2. Python
```bash
cd ~/info-shorts && python3.11 -m venv .venv && source .venv/bin/activate
pip install -U pip edge-tts jsonschema typer pydantic ruff pyright pytest kinocut
pip install -e .
edge-tts --list-voices | grep zh-TW
```

## 3. Node / Remotion
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs
cd remotion && npm install && npx remotion browser ensure
npm i @remotion/captions   # 字幕層
```
字體：`fonts-noto-cjk` 已裝；Remotion 內用 `@remotion/google-fonts` 或本機字體皆可，render 時確認中文不變豆腐。

## 4. Kinocut MCP
同 trip-cut：`.mcp.json` 為 placeholder，Phase 0 依 README 確認啟動指令。

## 5. Kokoro TTS（edge-tts 備援）
```bash
pip install kokoro soundfile   # 依 https://github.com/hexgrad/kokoro README，中文需要對應 voice pack
```
只在 edge-tts 失效時啟用；`tts.py` 以 `--engine kokoro` 切換。

## 6. GPU 備註
本專案不需要 GPU。Remotion render 用 CPU，`--concurrency=2`。

## 驗證
- [ ] `edge-tts` 能產 zh-TW mp3 + srt
- [ ] `npx remotion studio` 可開，中文字體正常
- [ ] Claude Code `/mcp` 看到 kinocut
