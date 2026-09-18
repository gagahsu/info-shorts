# STYLE — 中性置位風格（neutral）

目前的目標是「不難看、不搶戲、之後可整組替換」。所有值放在 `remotion/src/theme.ts`，元件只引用 token。

## Token

```ts
export const themes = {
  neutral: {
    bg: "#0F1115",           // 深灰底（直式短片在手機上省眼）
    surface: "#1A1D24",
    text: "#F2F3F5",
    muted: "#9AA0A6",
    accent: "#4F8CFF",       // 單一強調色
    up: "#2ECC71", down: "#E74C3C",   // 漲跌（台股習慣紅漲綠跌 → 由 adapter 決定 semantic，theme 只給色）
    fontDisplay: "Noto Sans TC",
    fontMono: "JetBrains Mono",
    radius: 24,
    pad: 72,                 // 左右內距（1080 寬）
    safeTop: 250, safeBottom: 300,   // IG Reels UI 遮擋區
    captionBg: "rgba(0,0,0,0.55)",
    captionSize: 56, captionY: 1500, // 字幕基線（距頂）
    sizeTitle: 88, sizeNumber: 160, sizeBody: 52, sizeSmall: 40, lineHeight: 1.35,
    enterFrames: 12, exitFrames: 8,  // 進場 spring 0.4s、退場淡出 0.25s（30fps）
  }
} as const;
```
（實際定義以 `remotion/src/theme.ts` 為準；元件內不可出現任何色碼，`grep -n '#' src/scenes` 應為空。）

## 版面規則

- 畫布 1080×1920，內容區 = 扣掉 safeTop/safeBottom。
- 每個 scene 一個主視覺，不放第二焦點。
- 字級：標題 88、數字 160、內文 52、字幕 56。中文行高 1.35。
- 字幕：置中、白字、半透明黑底圓角條、最多 2 行；與畫面文字不重疊（字幕區固定在 captionY）。
- 動畫：進場 `spring` 0.4s，退場淡出 0.25s；數字用 counting-up 0.8s；不用旋轉、不用彈跳。
- 漲跌顏色：台股語境「紅漲綠跌」。adapter 產 `delta_direction: "up"|"down"`，元件依 `kind` 決定用哪個色（briefing/company → 紅漲綠跌；generic → 綠漲紅跌），這個對應寫在 `theme.ts` 的 `deltaColor(kind, dir)`。

## 之後換風格

新增 `themes.<name>`，props.theme 指到它即可。不改 scene 元件是驗收條件。
