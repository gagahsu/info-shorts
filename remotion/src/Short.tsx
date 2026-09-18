import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Sequence, cancelRender, continueRender, delayRender, staticFile} from 'remotion';
import {Captions} from './Captions';
import {fontsReady} from './fonts';
import {getTheme} from './theme';
import {ThemeProvider} from './ThemeContext';
import {Bullets} from './scenes/Bullets';
import {Disclaimer} from './scenes/Disclaimer';
import {Quote} from './scenes/Quote';
import {Stat} from './scenes/Stat';
import {Table} from './scenes/Table';
import {Title} from './scenes/Title';
import type {Scene, ShortProps} from './types';

const renderScene = (s: Scene, durationInFrames: number): React.ReactNode => {
  switch (s.type) {
    case 'title':
      return <Title {...s.props} durationInFrames={durationInFrames} />;
    case 'stat':
      return <Stat {...s.props} durationInFrames={durationInFrames} />;
    case 'bullets':
      return <Bullets {...s.props} durationInFrames={durationInFrames} />;
    case 'table':
      return <Table {...s.props} durationInFrames={durationInFrames} />;
    case 'quote':
      return <Quote {...s.props} durationInFrames={durationInFrames} />;
    case 'disclaimer':
      return <Disclaimer {...s.props} durationInFrames={durationInFrames} />;
    default:
      return null;
  }
};

export const Short: React.FC<ShortProps> = (props) => {
  const theme = getTheme(props.theme);
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    fontsReady()
      .then(() => continueRender(handle))
      .catch((e) => cancelRender(e));
  }, [handle]);

  return (
    <ThemeProvider theme={theme} kind={props.kind}>
      <AbsoluteFill style={{backgroundColor: theme.bg}}>
        {props.scenes.map((s, i) => {
          const len = Math.max(1, s.endFrame - s.startFrame);
          return (
            <Sequence key={i} from={s.startFrame} durationInFrames={len} name={`${i} ${s.type}`}>
              {renderScene(s, len)}
            </Sequence>
          );
        })}
        {props.audio.voice ? <Audio src={staticFile(props.audio.voice)} /> : null}
        {props.audio.bgm ? <Audio src={staticFile(props.audio.bgm)} volume={props.audio.bgmVolume} loop /> : null}
        {props.captions ? <Captions file={props.captions} /> : null}
      </AbsoluteFill>
    </ThemeProvider>
  );
};
