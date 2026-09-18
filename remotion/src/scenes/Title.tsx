import React from 'react';
import {useTheme} from '../ThemeContext';
import type {TitleProps} from '../types';
import {SceneFrame} from './SceneFrame';

export const Title: React.FC<TitleProps & {durationInFrames: number}> = ({title, subtitle, date, durationInFrames}) => {
  const {theme} = useTheme();
  return (
    <SceneFrame durationInFrames={durationInFrames}>
      {date ? (
        <div style={{fontFamily: theme.fontMono, fontSize: theme.sizeSmall, color: theme.accent, marginBottom: 32}}>{date}</div>
      ) : null}
      <div style={{fontSize: theme.sizeTitle, fontWeight: 700, letterSpacing: 2}}>{title}</div>
      {subtitle ? <div style={{fontSize: theme.sizeBody, color: theme.muted, marginTop: 28}}>{subtitle}</div> : null}
      <div style={{width: 120, height: 8, background: theme.accent, borderRadius: 4, marginTop: 56}} />
    </SceneFrame>
  );
};
