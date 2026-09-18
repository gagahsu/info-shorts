import React from 'react';
import {useTheme} from '../ThemeContext';

/** 卡片容器：paper theme 有黑框白底；neutral 的 cardBorder=0 → 透明、無內距（維持原本置位風）。 */
export const Card: React.FC<React.PropsWithChildren<{style?: React.CSSProperties}>> = ({children, style}) => {
  const {theme} = useTheme();
  const framed = theme.cardBorder > 0;
  return (
    <div
      style={{
        background: framed ? theme.surface : 'transparent',
        border: framed ? `${theme.cardBorder}px solid ${theme.cardBorderColor}` : 'none',
        borderRadius: theme.radius,
        padding: theme.cardPad,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/** stat 標籤／小標：paper 是黃色膠囊，neutral 是灰字。 */
export const Tag: React.FC<React.PropsWithChildren> = ({children}) => {
  const {theme} = useTheme();
  if (!theme.tagBg) {
    return <div style={{fontSize: theme.sizeBody, color: theme.tagText}}>{children}</div>;
  }
  return (
    <div
      style={{
        display: 'inline-block',
        background: theme.tagBg,
        color: theme.tagText,
        border: `${Math.max(2, theme.cardBorder - 1)}px solid ${theme.cardBorderColor}`,
        borderRadius: 14,
        padding: '4px 22px',
        fontSize: theme.sizeSmall,
        fontWeight: 700,
      }}
    >
      {children}
    </div>
  );
};

/** 分隔線（paper 虛線、neutral 實線） */
export const Divider: React.FC<{style?: React.CSSProperties}> = ({style}) => {
  const {theme} = useTheme();
  return <div style={{borderTop: `3px ${theme.dividerStyle} ${theme.divider}`, ...style}} />;
};
