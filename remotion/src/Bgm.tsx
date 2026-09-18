import React from 'react';
import {Audio, interpolate, staticFile, useVideoConfig} from 'remotion';

const RAMP = 8; // ducking 淡入淡出 frame 數（約 0.27s）
const FADE_OUT = 30; // 片尾 1s 淡出

/**
 * 背景音樂：循環播放、片尾淡出；旁白區間（voiceRanges）自動壓低到 duckVolume。
 * 音量是 frame 的函數，Remotion 逐 frame 求值，不需要預先算 envelope。
 */
export const Bgm: React.FC<{file: string; volume: number; duckVolume: number; voiceRanges: number[][]}> = ({
  file,
  volume,
  duckVolume,
  voiceRanges,
}) => {
  const {durationInFrames} = useVideoConfig();
  const volumeAt = (f: number): number => {
    let duck = 0; // 0 = 沒旁白，1 = 完全壓低
    for (const [start, end] of voiceRanges) {
      const inRamp = interpolate(f, [start - RAMP, start], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
      const outRamp = interpolate(f, [end, end + RAMP], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
      duck = Math.max(duck, Math.min(inRamp, outRamp));
    }
    const base = volume + (duckVolume - volume) * duck;
    const fade = interpolate(f, [durationInFrames - FADE_OUT, durationInFrames], [1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return Math.max(0, base * fade);
  };
  return <Audio src={staticFile(file)} volume={volumeAt} loop />;
};
