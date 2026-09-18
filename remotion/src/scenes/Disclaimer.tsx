import React from 'react';
import {useTheme} from '../ThemeContext';
import type {DisclaimerProps} from '../types';
import {Card, Tag} from './Card';
import {SceneFrame} from './SceneFrame';

export const Disclaimer: React.FC<DisclaimerProps & {durationInFrames: number}> = ({text, durationInFrames}) => {
  const {theme} = useTheme();
  return (
    <SceneFrame durationInFrames={durationInFrames}>
      <Card>
        <Tag>免責聲明</Tag>
        <div style={{fontSize: theme.sizeBody, color: theme.muted, marginTop: 24}}>{text}</div>
      </Card>
    </SceneFrame>
  );
};
