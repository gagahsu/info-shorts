import {parseSrt, type Caption} from '@remotion/captions';
import React, {useEffect, useState} from 'react';
import {cancelRender, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {useTheme} from './ThemeContext';

/** 字幕層：讀 public-dir 下的 srt（由 tts.py 產生，已切成 ≤14 字），置中、半透明黑底圓角條，固定在 captionY。 */
export const Captions: React.FC<{file: string}> = ({file}) => {
  const [captions, setCaptions] = useState<Caption[] | null>(null);
  const [handle] = useState(() => delayRender(`load captions ${file}`));
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {theme} = useTheme();

  useEffect(() => {
    fetch(staticFile(file))
      .then((r) => {
        if (!r.ok) throw new Error(`captions ${file}: HTTP ${r.status}`);
        return r.text();
      })
      .then((input) => {
        setCaptions(parseSrt({input}).captions);
        continueRender(handle);
      })
      .catch((e) => cancelRender(e));
  }, [file, handle]);

  if (!captions) return null;
  const ms = (frame / fps) * 1000;
  const active = captions.find((c) => ms >= c.startMs && ms < c.endMs);
  if (!active) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: theme.captionY,
        left: theme.pad,
        right: theme.pad,
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          background: theme.captionBg,
          color: theme.text,
          fontFamily: theme.fontDisplay,
          fontSize: theme.captionSize,
          fontWeight: 700,
          lineHeight: theme.lineHeight,
          padding: '14px 36px',
          borderRadius: theme.radius / 2,
          textAlign: 'center',
          maxWidth: '100%',
        }}
      >
        {active.text}
      </div>
    </div>
  );
};
