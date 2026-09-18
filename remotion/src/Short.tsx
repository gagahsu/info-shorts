import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Sequence, cancelRender, continueRender, delayRender, staticFile} from 'remotion';
import {Bgm} from './Bgm';
import {Captions} from './Captions';
import {Footer, Frame, Header} from './Chrome';
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

/** 頁首小標：每個 scene 自己的標題 */
const sceneLabel = (s: Scene): string | null => {
  switch (s.type) {
    case 'stat':
      return s.props.label || null;
    case 'bullets':
    case 'table':
      return s.props.heading || null;
    case 'quote':
      return '結語';
    case 'disclaimer':
      return '免責聲明';
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
  const total = props.scenes.length;

  return (
    <ThemeProvider theme={theme} kind={props.kind}>
      <AbsoluteFill style={{backgroundColor: theme.bg}}>
        <Frame />
        {props.scenes.map((s, i) => {
          const len = Math.max(1, s.endFrame - s.startFrame);
          return (
            <Sequence key={i} from={s.startFrame} durationInFrames={len} name={`${i} ${s.type}`}>
              {s.type !== 'title' ? <Header meta={props.meta} index={i} total={total} label={sceneLabel(s)} /> : null}
              {renderScene(s, len)}
            </Sequence>
          );
        })}
        <Footer meta={props.meta} />
        {props.audio.voice ? <Audio src={staticFile(props.audio.voice)} /> : null}
        {props.audio.bgm ? (
          <Bgm
            file={props.audio.bgm}
            volume={props.audio.bgmVolume}
            duckVolume={props.audio.duckVolume}
            voiceRanges={props.audio.voiceRanges}
          />
        ) : null}
        {props.captions ? <Captions file={props.captions} /> : null}
      </AbsoluteFill>
    </ThemeProvider>
  );
};
