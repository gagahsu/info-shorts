import React from 'react';
import {deltaColor} from '../theme';
import {useTheme} from '../ThemeContext';
import type {StatProps} from '../types';
import {SceneFrame} from './SceneFrame';

const show = (v: string | number | null): string => (v === null || v === undefined || v === '' ? '—' : String(v));

export const Stat: React.FC<StatProps & {durationInFrames: number}> = ({label, value, delta, deltaDirection, unit, durationInFrames}) => {
  const {theme, kind} = useTheme();
  const color = deltaColor(theme, kind, deltaDirection);
  const arrow = deltaDirection === 'up' ? '▲' : deltaDirection === 'down' ? '▼' : '';
  return (
    <SceneFrame durationInFrames={durationInFrames}>
      <div style={{fontSize: theme.sizeBody, color: theme.muted}}>{label}</div>
      <div
        style={{
          fontFamily: theme.fontMono,
          fontSize: theme.sizeNumber,
          fontWeight: 700,
          lineHeight: 1.1,
          marginTop: 24,
          wordBreak: 'break-all',
        }}
      >
        {show(value)}
        {value !== null && unit ? <span style={{fontSize: theme.sizeBody, marginLeft: 12, color: theme.muted}}>{unit}</span> : null}
      </div>
      {delta !== null && delta !== undefined && delta !== '' ? (
        <div style={{fontFamily: theme.fontMono, fontSize: theme.sizeBody, color, marginTop: 24}}>
          {arrow} {String(delta)}
          {unit && !String(delta).endsWith('%') ? unit : ''}
        </div>
      ) : null}
    </SceneFrame>
  );
};
