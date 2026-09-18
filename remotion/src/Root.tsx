import React from 'react';
import {Composition} from 'remotion';
import {sampleProps} from './sample';
import {Short} from './Short';
import type {ShortProps} from './types';

export const Root: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    fps={sampleProps.fps}
    width={sampleProps.width}
    height={sampleProps.height}
    durationInFrames={sampleProps.durationInFrames}
    defaultProps={sampleProps}
    calculateMetadata={({props}: {props: ShortProps}) => ({
      fps: props.fps,
      width: props.width,
      height: props.height,
      durationInFrames: props.durationInFrames,
    })}
  />
);
