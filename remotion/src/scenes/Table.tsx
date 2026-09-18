import React from 'react';
import {deltaColor} from '../theme';
import {useTheme} from '../ThemeContext';
import type {TableProps} from '../types';
import {Card, Divider} from './Card';
import {SceneFrame, useStagger} from './SceneFrame';

const cell = (v: string | number | null): string => (v === null || v === undefined || v === '' ? '—' : String(v));
/** '+0.61%' / '-120' 這類帶號數值 → up/down，其餘 null（不上色） */
const signOf = (v: string | number | null): 'up' | 'down' | null => {
  const s = cell(v);
  if (/^\+\s*\d/.test(s)) return 'up';
  if (/^-\s*\d/.test(s)) return 'down';
  return null;
};

const Row: React.FC<{index: number; cells: (string | number | null)[]; last: boolean}> = ({index, cells, last}) => {
  const {theme, kind} = useTheme();
  const style = useStagger(index + 1);
  const framed = theme.cardBorder > 0;
  return (
    <div
      style={{
        display: 'flex',
        padding: framed ? '20px 8px' : '24px 32px',
        background: !framed && index % 2 === 0 ? theme.surface : 'transparent',
        borderBottom: framed && !last ? `2px ${theme.dividerStyle} ${theme.muted}` : 'none',
        borderRadius: framed ? 0 : theme.radius / 2,
        fontSize: theme.sizeBody,
        ...style,
      }}
    >
      {cells.map((c, i) => (
        <div
          key={i}
          style={{
            flex: i === 0 ? 1.4 : 1,
            fontFamily: i === 0 ? theme.fontDisplay : theme.fontMono,
            fontWeight: i === 0 ? 400 : 700,
            textAlign: i === 0 ? 'left' : 'right',
            color: i > 0 && signOf(c) ? deltaColor(theme, kind, signOf(c)) : theme.text,
          }}
        >
          {cell(c)}
        </div>
      ))}
    </div>
  );
};

export const Table: React.FC<TableProps & {durationInFrames: number}> = ({heading, columns, rows, durationInFrames}) => {
  const {theme} = useTheme();
  const framed = theme.cardBorder > 0;
  return (
    <SceneFrame durationInFrames={durationInFrames} align="top">
      <Card>
        {heading ? (
          <div style={{fontSize: framed ? 60 : theme.sizeTitle, fontWeight: 700, marginBottom: framed ? 0 : 48}}>{heading}</div>
        ) : null}
        {heading && framed ? <Divider style={{margin: '20px 0 8px'}} /> : null}
        {columns.length ? (
          <div style={{display: 'flex', padding: framed ? '12px 8px 4px' : '0 32px 20px', color: theme.muted, fontSize: theme.sizeSmall}}>
            {columns.map((c, i) => (
              <div key={i} style={{flex: i === 0 ? 1.4 : 1, textAlign: i === 0 ? 'left' : 'right'}}>
                {c}
              </div>
            ))}
          </div>
        ) : null}
        {rows.map((r, i) => (
          <Row key={i} index={i} cells={r} last={i === rows.length - 1} />
        ))}
      </Card>
    </SceneFrame>
  );
};
