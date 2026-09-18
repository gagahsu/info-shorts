import React from 'react';
import {useTheme} from '../ThemeContext';
import type {BulletsProps} from '../types';
import {Card, Divider} from './Card';
import {SceneFrame, useStagger} from './SceneFrame';

const Item: React.FC<{index: number; text: string}> = ({index, text}) => {
  const {theme} = useTheme();
  const style = useStagger(index + 1);
  const framed = theme.cardBorder > 0;
  return (
    <div style={{display: 'flex', alignItems: 'flex-start', gap: 28, marginTop: index === 0 ? 0 : 36, ...style}}>
      <div
        style={{
          flex: 'none',
          width: 60,
          height: 60,
          borderRadius: 30,
          background: framed ? (theme.tagBg ?? theme.surface) : theme.surface,
          border: framed ? `3px solid ${theme.cardBorderColor}` : 'none',
          color: framed ? theme.tagText : theme.accent,
          fontFamily: theme.fontMono,
          fontSize: theme.sizeSmall,
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: 4,
        }}
      >
        {index + 1}
      </div>
      <div style={{fontSize: theme.sizeBody}}>{text}</div>
    </div>
  );
};

export const Bullets: React.FC<BulletsProps & {durationInFrames: number}> = ({heading, items, durationInFrames}) => {
  const {theme} = useTheme();
  const framed = theme.cardBorder > 0;
  return (
    <SceneFrame durationInFrames={durationInFrames} align="top">
      <Card>
        {heading ? (
          <div style={{fontSize: framed ? 60 : theme.sizeTitle, fontWeight: 700, marginBottom: framed ? 0 : 64}}>{heading}</div>
        ) : null}
        {heading && framed ? <Divider style={{margin: '24px 0 36px'}} /> : null}
        {items.map((t, i) => (
          <Item key={i} index={i} text={t} />
        ))}
      </Card>
    </SceneFrame>
  );
};
