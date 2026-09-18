import React from 'react';
import {useTheme} from '../ThemeContext';
import type {TableProps} from '../types';
import {SceneFrame, useStagger} from './SceneFrame';

const cell = (v: string | number | null): string => (v === null || v === undefined || v === '' ? '—' : String(v));

const Row: React.FC<{index: number; cells: (string | number | null)[]}> = ({index, cells}) => {
  const {theme} = useTheme();
  const style = useStagger(index + 1);
  return (
    <div
      style={{
        display: 'flex',
        padding: '24px 32px',
        background: index % 2 === 0 ? theme.surface : 'transparent',
        borderRadius: theme.radius / 2,
        fontSize: theme.sizeBody,
        ...style,
      }}
    >
      {cells.map((c, i) => (
        <div key={i} style={{flex: i === 0 ? 1.4 : 1, fontFamily: i === 0 ? theme.fontDisplay : theme.fontMono, textAlign: i === 0 ? 'left' : 'right'}}>
          {cell(c)}
        </div>
      ))}
    </div>
  );
};

export const Table: React.FC<TableProps & {durationInFrames: number}> = ({heading, columns, rows, durationInFrames}) => {
  const {theme} = useTheme();
  return (
    <SceneFrame durationInFrames={durationInFrames} align="top">
      {heading ? <div style={{fontSize: theme.sizeTitle, fontWeight: 700, marginBottom: 48}}>{heading}</div> : null}
      {columns.length ? (
        <div style={{display: 'flex', padding: '0 32px 20px', color: theme.muted, fontSize: theme.sizeSmall}}>
          {columns.map((c, i) => (
            <div key={i} style={{flex: i === 0 ? 1.4 : 1, textAlign: i === 0 ? 'left' : 'right'}}>
              {c}
            </div>
          ))}
        </div>
      ) : null}
      {rows.map((r, i) => (
        <Row key={i} index={i} cells={r} />
      ))}
    </SceneFrame>
  );
};
