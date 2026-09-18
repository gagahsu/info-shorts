import React from 'react';
import {AbsoluteFill} from 'remotion';
import {HEADER_HEIGHT} from './scenes/SceneFrame';
import {Divider} from './scenes/Card';
import {useTheme} from './ThemeContext';
import type {Meta} from './types';

/** 整張畫面的外框（paper theme）。 */
export const Frame: React.FC = () => {
  const {theme} = useTheme();
  if (!theme.frameBorder) return null;
  return (
    <AbsoluteFill style={{padding: theme.frameInset, pointerEvents: 'none'}}>
      <div
        style={{
          width: '100%',
          height: '100%',
          border: `${theme.frameBorder}px solid ${theme.cardBorderColor}`,
          borderRadius: theme.radius * 1.6,
        }}
      />
    </AbsoluteFill>
  );
};

/** 每頁頁首：「彡 標題 ｜ 日期 ミ」＋「2/8 ｜ 本頁小標」＋虛線。 */
export const Header: React.FC<{meta: Meta; index: number; total: number; label: string | null}> = ({
  meta,
  index,
  total,
  label,
}) => {
  const {theme} = useTheme();
  if (!theme.showHeader) return null;
  const [l, r] = theme.headerDecor;
  const dateText = meta.date ? meta.date.replace(/-/g, '.') : null;
  // 標題太長就縮字：中文字算 1em、英數算 0.6em，塞進內容寬度（1080 - 2*pad）
  const full = `${l}${meta.title}${dateText ? ` ｜ ${dateText}` : ''}${r}`;
  const units = [...full].reduce((n, ch) => n + (ch.charCodeAt(0) > 0x2e7f ? 1 : 0.6), 0);
  const titleSize = Math.min(54, Math.floor((1080 - theme.pad * 2) / units));
  return (
    <div
      style={{
        position: 'absolute',
        top: theme.frameInset + 40,
        left: theme.pad,
        right: theme.pad,
        height: HEADER_HEIGHT,
        color: theme.text,
        fontFamily: theme.fontDisplay,
        textAlign: 'center',
      }}
    >
      <div style={{fontSize: titleSize, fontWeight: 700, letterSpacing: 2, whiteSpace: 'nowrap'}}>
        {l}
        {meta.title}
        {dateText ? <span style={{fontFamily: theme.fontMono}}> ｜ {dateText}</span> : null}
        {r}
      </div>
      <div style={{fontSize: theme.sizeSmall, color: theme.muted, marginTop: 6}}>
        <span style={{fontFamily: theme.fontMono}}>
          {index + 1} / {total}
        </span>
        {label ? ` ｜ ${label}` : ''}
      </div>
      <Divider style={{marginTop: 26}} />
    </div>
  );
};

/** 頁尾：「品牌 ｜ 非投資建議」，靠右小字。 */
export const Footer: React.FC<{meta: Meta}> = ({meta}) => {
  const {theme} = useTheme();
  if (!theme.showHeader) return null;
  const parts = [meta.brand, meta.disclaimer ? '非投資建議' : null].filter(Boolean);
  if (!parts.length) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: theme.pad,
        right: theme.pad,
        top: theme.captionY - 72,
        textAlign: 'right',
        fontSize: 30,
        color: theme.muted,
        fontFamily: theme.fontDisplay,
      }}
    >
      {parts.join(' ｜ ')}
    </div>
  );
};
