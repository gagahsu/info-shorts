import React from 'react';
import {useTheme} from '../ThemeContext';
import type {DisclaimerProps} from '../types';
import {SceneFrame} from './SceneFrame';

export const Disclaimer: React.FC<DisclaimerProps & {durationInFrames: number}> = ({text, durationInFrames}) => {
  const {theme} = useTheme();
  return (
    <SceneFrame durationInFrames={durationInFrames}>
      <div style={{fontSize: theme.sizeSmall, color: theme.muted, letterSpacing: 4, marginBottom: 24}}>免責聲明</div>
      <div style={{fontSize: theme.sizeBody, color: theme.muted, background: theme.surface, padding: 48, borderRadius: theme.radius}}>{text}</div>
    </SceneFrame>
  );
};
