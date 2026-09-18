import React from 'react';
import {useTheme} from '../ThemeContext';
import type {BulletsProps} from '../types';
import {SceneFrame, useStagger} from './SceneFrame';

const Item: React.FC<{index: number; text: string}> = ({index, text}) => {
  const {theme} = useTheme();
  const style = useStagger(index + 1);
  return (
    <div style={{display: 'flex', alignItems: 'flex-start', gap: 28, marginTop: index === 0 ? 0 : 40, ...style}}>
      <div
        style={{
          flex: 'none',
          width: 64,
          height: 64,
          borderRadius: 32,
          background: theme.surface,
          color: theme.accent,
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
  return (
    <SceneFrame durationInFrames={durationInFrames} align="top">
      {heading ? <div style={{fontSize: theme.sizeTitle, fontWeight: 700, marginBottom: 64}}>{heading}</div> : null}
      {items.map((t, i) => (
        <Item key={i} index={i} text={t} />
      ))}
    </SceneFrame>
  );
};
