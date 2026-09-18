/**
 * 視覺風格唯一來源（docs/STYLE.md）。scene 元件只能引用這裡的 token，不可寫死顏色／字級。
 * 換風格：新增 themes.<name>，props.theme 指到它。
 */
import type {ContentKind, DeltaDirection} from './types';

export const themes = {
  neutral: {
    bg: '#0F1115',
    surface: '#1A1D24',
    text: '#F2F3F5',
    muted: '#9AA0A6',
    accent: '#4F8CFF',
    up: '#2ECC71',
    down: '#E74C3C',
    fontDisplay: 'Noto Sans TC',
    fontMono: 'JetBrains Mono',
    radius: 24,
    pad: 72,
    safeTop: 250,
    safeBottom: 300,
    captionSize: 56,
    captionY: 1500,
    // 字級（docs/STYLE.md）
    sizeTitle: 88,
    sizeNumber: 160,
    sizeBody: 52,
    sizeSmall: 40,
    lineHeight: 1.35,
    // 動畫（frame @ 30fps）
    enterFrames: 12, // spring 0.4s
    exitFrames: 8, // 淡出 0.25s
  },
} as const;

export type ThemeName = keyof typeof themes;
export type Theme = (typeof themes)[ThemeName];

export const getTheme = (name: string): Theme => {
  const t = (themes as Record<string, Theme>)[name];
  if (!t) {
    throw new Error(`未知 theme：${name}（可用：${Object.keys(themes).join(', ')}）`);
  }
  return t;
};

/**
 * 漲跌顏色。台股語境（briefing / company）紅漲綠跌；generic 綠漲紅跌。
 * 方向由 adapter 給的 delta_direction 決定，theme 只給色。
 */
export const deltaColor = (theme: Theme, kind: ContentKind, dir: DeltaDirection): string => {
  if (dir === 'flat' || dir === null) return theme.muted;
  const twStyle = kind === 'briefing' || kind === 'company';
  if (dir === 'up') return twStyle ? theme.down : theme.up;
  return twStyle ? theme.up : theme.down;
};
