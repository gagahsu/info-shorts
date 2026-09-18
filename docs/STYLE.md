# STYLE — 視覺規範

所有值放在 `remotion/src/theme.ts`，元件只引用 token（`grep -n '#' src/scenes` 應為空）。
目前兩個 theme：**`paper`（預設）** 與 `neutral`；`--theme` 切換，元件不改（驗收條件）。

## paper — 米白手繪風（2026-09-19 起預設，ADR-017）

參考使用者的 IG 圖卡：米白底、黑色粗框圓角卡片、黃色標籤膠囊、虛線分隔、紅漲。

```ts
paper: {
  bg: "#F5F0E8", surface: "#FFFFFF", text: "#1B1B1B", muted: "#7A7A7A", accent: "#1B1B1B",
  up: "#2E9E5B", down: "#D62828",          // 台股語境（briefing/company/closing）紅漲綠跌，由 deltaColor 決定
  cardBorder: 4, cardBorderColor: "#1B1B1B", cardPad: 44, radius: 28,
  frameBorder: 4, frameInset: 36,           // 整張畫面的外框
  tagBg: "#FFE45C", tagText: "#1B1B1B",     // stat 標籤、bullets 編號、免責標籤
  divider: "#1B1B1B", dividerStyle: "dashed",
  showHeader: true, headerDecor: ["彡 ", " ミ"],   // 每頁頁首「彡 標題 ｜ 日期 ミ」＋「n / N ｜ 小標」＋虛線；頁尾「品牌 ｜ 非投資建議」
  captionBg: "#FFFFFF", captionText: "#1B1B1B", captionBorder: 4,   // 白底黑框字幕條
  sizeTitle: 84, sizeNumber: 150, sizeBody: 50, sizeSmall: 38, captionSize: 56,
}
```

- 頁首標題太長會自動縮字（中文 1em、英數 0.6em 估寬）。
- 頁尾品牌字來自 `content.brand`（company adapter 用 payload 的 `brand_name`；其他來源可在 content.json 填）；`disclaimer: true` 時加「非投資建議」。
- 表格：paper 用虛線分列、不做斑馬紋；neutral 相反。

## neutral — 深灰置位風（ADR-005 原版，保留）

```ts
neutral: {
  bg: "#0F1115", surface: "#1A1D24", text: "#F2F3F5", muted: "#9AA0A6", accent: "#4F8CFF",
  up: "#2ECC71", down: "#E74C3C", cardBorder: 0, frameBorder: 0, tagBg: null, showHeader: false,
  captionBg: "rgba(0,0,0,0.55)", captionText: "#F2F3F5", captionBorder: 0,
  sizeTitle: 88, sizeNumber: 160, sizeBody: 52, sizeSmall: 40, captionSize: 56,
}
```

## 兩個 theme 共用的版面規則

- 畫布 1080×1920；`safeTop: 250`、`safeBottom: 300`（IG Reels UI 遮擋區）；paper 有頁首時內容從頁首下方開始。
- 每個 scene 一個主視覺（一張卡片），不放第二焦點。
- 字幕：置中、最多 2 行、固定在 `captionY: 1500`；顯示數字（47,160）而旁白唸中文（見 ADR-018）。
- 動畫：進場 `spring` 0.4s，退場淡出 0.25s；數字 counting-up 0.8s；列表逐條錯開 4 frame；不用旋轉、不用彈跳。
- 漲跌顏色：`deltaColor(theme, kind, dir)`；台股語境紅漲綠跌，generic 綠漲紅跌。

## 之後換風格

新增 `themes.<name>`（型別 `Theme` 會要求補齊所有 token），`--theme <name>` 即可；不改 scene 元件是驗收條件。
