import React from 'react';
import {useTheme} from '../ThemeContext';
import type {QuoteProps} from '../types';
import {SceneFrame} from './SceneFrame';

export const Quote: React.FC<QuoteProps & {durationInFrames: number}> = ({text, source, durationInFrames}) => {
  const {theme} = useTheme();
  return (
    <SceneFrame durationInFrames={durationInFrames}>
      <div style={{fontSize: 120, color: theme.accent, lineHeight: 1, fontWeight: 700}}>“</div>
      <div style={{fontSize: 68, fontWeight: 700, marginTop: 8}}>{text}</div>
      {source ? <div style={{fontSize: theme.sizeSmall, color: theme.muted, marginTop: 40}}>— {source}</div> : null}
    </SceneFrame>
  );
};
