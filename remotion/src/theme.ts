/**
 * 視覺風格唯一來源（docs/STYLE.md）。scene 元件只能引用這裡的 token，不可寫死顏色／字級。
 * 換風格：新增 themes.<name>，props.theme 指到它。
 *
 * - paper：米白手繪風（預設，ADR-017）：卡片黑框、黃色標籤、虛線分隔、外框、每頁頁首。
 * - neutral：深灰置位風（ADR-005 的原始版本），無卡片框。
 */
import type {ContentKind, DeltaDirection} from './types';

export type Theme = {
  bg: string;
  surface: string;
  text: string;
  muted: string;
  accent: string;
  up: string;
  down: string;
  fontDisplay: string;
  fontMono: string;
  radius: number;
  pad: number;
  safeTop: number;
  safeBottom: number;
  /** 卡片：邊框粗細（0 = 沒有卡片感）、邊框色、內距 */
  cardBorder: number;
  cardBorderColor: string;
  cardPad: number;
  /** 整張畫面的外框（0 = 無）與內縮 */
  frameBorder: number;
  frameInset: number;
  /** stat 標籤膠囊；tagBg 為 null 時只顯示文字 */
  tagBg: string | null;
  tagText: string;
  /** 分隔線 */
  divider: string;
  dividerStyle: 'dashed' | 'solid';
  /** 每頁頁首（標題｜日期）與頁尾（品牌｜非投資建議） */
  showHeader: boolean;
  headerDecor: [string, string];
  /** 字幕條 */
  captionBg: string;
  captionText: string;
  captionBorder: number;
  captionSize: number;
  captionY: number;
  /** 字級（docs/STYLE.md） */
  sizeTitle: number;
  sizeNumber: number;
  sizeBody: number;
  sizeSmall: number;
  lineHeight: number;
  /** 動畫（frame @ 30fps） */
  enterFrames: number;
  exitFrames: number;
};

export const themes: Record<'paper' | 'neutral', Theme> = {
  paper: {
    bg: '#F5F0E8',
    surface: '#FFFFFF',
    text: '#1B1B1B',
    muted: '#7A7A7A',
    accent: '#1B1B1B',
    up: '#2E9E5B',
    down: '#D62828',
    fontDisplay: 'Noto Sans TC',
    fontMono: 'JetBrains Mono',
    radius: 28,
    pad: 84,
    safeTop: 250,
    safeBottom: 300,
    cardBorder: 4,
    cardBorderColor: '#1B1B1B',
    cardPad: 44,
    frameBorder: 4,
    frameInset: 36,
    tagBg: '#FFE45C',
    tagText: '#1B1B1B',
    divider: '#1B1B1B',
    dividerStyle: 'dashed',
    showHeader: true,
    headerDecor: ['彡 ', ' ミ'],
    captionBg: '#FFFFFF',
    captionText: '#1B1B1B',
    captionBorder: 4,
    captionSize: 56,
    captionY: 1500,
    sizeTitle: 84,
    sizeNumber: 150,
    sizeBody: 50,
    sizeSmall: 38,
    lineHeight: 1.35,
    enterFrames: 12,
    exitFrames: 8,
  },
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
    cardBorder: 0,
    cardBorderColor: 'transparent',
    cardPad: 0,
    frameBorder: 0,
    frameInset: 0,
    tagBg: null,
    tagText: '#9AA0A6',
    divider: '#1A1D24',
    dividerStyle: 'solid',
    showHeader: false,
    headerDecor: ['', ''],
    captionBg: 'rgba(0,0,0,0.55)',
    captionText: '#F2F3F5',
    captionBorder: 0,
    captionSize: 56,
    captionY: 1500,
    sizeTitle: 88,
    sizeNumber: 160,
    sizeBody: 52,
    sizeSmall: 40,
    lineHeight: 1.35,
    enterFrames: 12,
    exitFrames: 8,
  },
};

export type ThemeName = keyof typeof themes;
export const DEFAULT_THEME: ThemeName = 'paper';

export const getTheme = (name: string): Theme => {
  const t = (themes as Record<string, Theme>)[name];
  if (!t) {
    throw new Error(`未知 theme：${name}（可用：${Object.keys(themes).join(', ')}）`);
  }
  return t;
};

/**
 * 漲跌顏色。台股語境（briefing / company / closing）紅漲綠跌；generic 綠漲紅跌。
 * 方向由 adapter 給的 delta_direction 決定，theme 只給色。
 */
export const deltaColor = (theme: Theme, kind: ContentKind, dir: DeltaDirection): string => {
  if (dir === 'flat' || dir === null) return theme.muted;
  const twStyle = kind === 'briefing' || kind === 'company' || kind === 'closing';
  if (dir === 'up') return twStyle ? theme.down : theme.up;
  return twStyle ? theme.up : theme.down;
};
