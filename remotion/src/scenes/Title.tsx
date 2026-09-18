import React from 'react';
import {useTheme} from '../ThemeContext';
import type {TitleProps} from '../types';
import {Divider} from './Card';
import {SceneFrame} from './SceneFrame';

export const Title: React.FC<TitleProps & {durationInFrames: number}> = ({title, subtitle, date, durationInFrames}) => {
  const {theme} = useTheme();
  const [l, r] = theme.headerDecor;
  const framed = theme.cardBorder > 0;
  return (
    <SceneFrame durationInFrames={durationInFrames}>
      <div style={{textAlign: framed ? 'center' : 'left'}}>
        {date ? (
          <div style={{fontFamily: theme.fontMono, fontSize: theme.sizeSmall, color: framed ? theme.muted : theme.accent, marginBottom: 32}}>
            {framed ? date.replace(/-/g, '.') : date}
          </div>
        ) : null}
        <div style={{fontSize: theme.sizeTitle, fontWeight: 700, letterSpacing: 2}}>
          {l}
          {title}
          {r}
        </div>
        {subtitle ? <div style={{fontSize: theme.sizeBody, color: theme.muted, marginTop: 28}}>{subtitle}</div> : null}
        {framed ? (
          <Divider style={{marginTop: 56}} />
        ) : (
          <div style={{width: 120, height: 8, background: theme.accent, borderRadius: 4, marginTop: 56}} />
        )}
      </div>
    </SceneFrame>
  );
};
