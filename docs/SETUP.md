# SETUP

> 2026-09-18 定案（ADR-008）：**Windows 原生**執行，不走 WSL2。repo 在 `C:\Users\<you>\workspace\info-shorts`，
> Claude Code 也在 Windows 跑；WSL 沒有 sudo 免密碼、沒 node、沒 ffmpeg，而 Windows 側全部都有。
> 程式碼本身跨平台（只靠 uv / node / ffmpeg 在 PATH 或可定位），之後要搬去 WSL/Linux 只需照 §7 裝依賴。

## 1. 需要的東西（Windows）

| 工具 | 版本 | 來源 | 檢查 |
|---|---|---|---|
| uv | 0.12+ | https://docs.astral.sh/uv/ | `uv --version` |
| Python | 3.11（uv 會自己抓） | `uv python install 3.11` | `uv run python --version` |
| Node.js | 22+ | nvm-windows / nodejs.org | `node --version` |
| FFmpeg | **6+**（Kinocut 硬性要求） | `winget install Gyan.FFmpeg` | 見 §4 |
| 字型 | 不用裝 | Remotion 用 `@remotion/google-fonts`（Noto Sans TC）render 時自動抓 | — |

不需要 GPU、不需要 Chrome（Remotion 自帶 headless shell）。

## 2. Python（uv）

```powershell
cd C:\Users\<you>\workspace\info-shorts
uv sync            # 建 .venv、裝 edge-tts / kinocut / typer / jsonschema / pydantic + dev（ruff/pyright/pytest）
uv run infoshorts doctor
uv run infoshorts voices     # 列 zh-TW 聲音
```

`uv sync` 會裝 `kinocut`（Python 套件內含 `kino` CLI 與 MCP server）。

## 3. Node / Remotion

```powershell
cd remotion
npm install
npx remotion browser ensure   # 下載 headless shell（約 110 MB，一次）
npx remotion studio           # 預覽（用 src/sample.ts 的假資料）
```

## 4. FFmpeg 版本陷阱（重要）

Windows 上 PATH 常被 miniconda 的 FFmpeg **4.x** 搶先，Kinocut 會判定「too old」。
本專案的 `src/infoshorts/ffmpeg.py` 會自己找夠新的版本，順序：

1. 環境變數 `INFOSHORTS_FFMPEG_DIR`（含 ffmpeg.exe 的目錄）
2. 環境變數 `KINOCUT_FFMPEG_EXECUTABLE` 所在目錄
3. `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin`
4. PATH 上的 `ffmpeg`

並在呼叫 Kinocut 前設定 `KINOCUT_FFMPEG_EXECUTABLE` / `KINOCUT_FFPROBE_EXECUTABLE`。
`uv run infoshorts doctor` 會印出實際選到的路徑。

## 5. Kinocut MCP（給 Claude Code 用）

`.mcp.json` 已設定：`uvx --from kinocut kino --mcp`，並透過 `env` 指定 FFmpeg 8 的路徑
（用 `${VAR:-default}` 語法，換機器時設環境變數 `KINOCUT_FFMPEG_EXECUTABLE` 即可覆蓋）。
Claude Code 內 `/mcp` 應看到 `kinocut`，196 個 tools。

pipeline 的 `qa.py` **不走 MCP**，直接 import `kinocut` 的 Python API（probe / quality_check / metric_qc），
MCP 只是給 Claude 互動用。

## 6. Kokoro TTS（edge-tts 備援）

```powershell
uv sync --group kokoro        # kokoro + misaki[zh] + soundfile + torch(CPU)，約 300 MB
uv run infoshorts build ... --engine kokoro [--voice zf_xiaobei]
```
第一次使用會從 Hugging Face 下載 `hexgrad/Kokoro-82M`（約 330 MB）到 `%USERPROFILE%\.cache\huggingface`。
中文聲音：`zf_xiaobei`（預設）、`zf_xiaoni`、`zf_xiaoxiao`、`zf_xiaoyi`、`zm_yunjian`、`zm_yunxi`、`zm_yunxia`、`zm_yunyang`。
中文 pipeline 沒有逐詞時間碼，字幕時間是在每個句子內依字數等比估算（ADR-013），精度比 edge-tts 差但可用。

## 7. 若要改在 WSL2 / Linux 跑

```bash
sudo apt install -y ffmpeg nodejs npm fonts-noto-cjk libnss3 libatk-bridge2.0-0 libgbm1 libasound2
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync && (cd remotion && npm install && npx remotion browser ensure)
```
Ubuntu 24.04 的 apt ffmpeg 是 6.1，符合 Kinocut。程式碼不用改。

## 驗證清單

- [x] `uv run infoshorts --help` / `doctor`
- [x] `edge-tts` 能產 zh-TW mp3 + WordBoundary 時間碼（`tts.py` 用 Python API，不用 CLI）
- [x] `npx tsc --noEmit` 通過；`npx remotion render` 可出 1080×1920 mp4
- [x] Kinocut MCP 以 stdio 啟動、`tools/list` 回 196 個 tools
- [x] `uv run pytest`
