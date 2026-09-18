import React from 'react';
import {Easing, interpolate, useCurrentFrame} from 'remotion';
import {deltaColor} from '../theme';
import {useTheme} from '../ThemeContext';
import type {StatProps} from '../types';
import {SceneFrame} from './SceneFrame';

const COUNT_FRAMES = 24; // counting-up 0.8s @ 30fps

/** 把 "23,456"、"190+"、"-1.25%"、12.5 拆成 前綴/數值/小數位數/後綴，讓數字可以從 0 數上去、格式維持原樣。 */
const parseNumeric = (raw: string | number | null): {prefix: string; value: number; decimals: number; grouped: boolean; suffix: string} | null => {
  if (raw === null || raw === undefined) return null;
  const s = String(raw).trim();
  const m = s.match(/^([^\d]*?)(-?)(\d[\d,]*)(?:\.(\d+))?(.*)$/);
  if (!m) return null;
  const [, prefix, sign, intPart, frac, suffix] = m;
  const value = Number(`${sign}${intPart.replace(/,/g, '')}${frac ? '.' + frac : ''}`);
  if (!Number.isFinite(value)) return null;
  return {prefix, value, decimals: frac ? frac.length : 0, grouped: intPart.includes(','), suffix};
};

const formatNumber = (n: number, decimals: number, grouped: boolean): string => {
  const fixed = Math.abs(n).toFixed(decimals);
  const [i, f] = fixed.split('.');
  const int = grouped ? i.replace(/\B(?=(\d{3})+(?!\d))/g, ',') : i;
  return `${n < 0 ? '-' : ''}${int}${f ? '.' + f : ''}`;
};

/** 數字 counting-up；非數字（"—"、"N/A"）原樣顯示。 */
const CountUp: React.FC<{raw: string | number | null}> = ({raw}) => {
  const frame = useCurrentFrame();
  const parsed = parseNumeric(raw);
  if (!parsed) return <>{raw === null || raw === undefined || raw === '' ? '—' : String(raw)}</>;
  const t = interpolate(frame, [0, COUNT_FRAMES], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  return <>{`${parsed.prefix}${formatNumber(parsed.value * t, parsed.decimals, parsed.grouped)}${parsed.suffix}`}</>;
};

export const Stat: React.FC<StatProps & {durationInFrames: number}> = ({label, value, delta, deltaDirection, unit, durationInFrames}) => {
  const {theme, kind} = useTheme();
  const color = deltaColor(theme, kind, deltaDirection);
  const arrow = deltaDirection === 'up' ? '▲' : deltaDirection === 'down' ? '▼' : '';
  const hasDelta = delta !== null && delta !== undefined && delta !== '';
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
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        <CountUp raw={value} />
        {value !== null && unit ? <span style={{fontSize: theme.sizeBody, marginLeft: 12, color: theme.muted}}>{unit}</span> : null}
      </div>
      {hasDelta ? (
        <div style={{fontFamily: theme.fontMono, fontSize: theme.sizeBody, color, marginTop: 24}}>
          {arrow} {String(delta)}
          {unit && !String(delta).endsWith('%') ? unit : ''}
        </div>
      ) : null}
    </SceneFrame>
  );
};
