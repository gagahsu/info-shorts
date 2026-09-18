import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {useTheme} from '../ThemeContext';

/**
 * 每個 scene 的共用外框：內容區 = safeTop 到字幕條上方；進場 spring 0.4s（上移+淡入），退場淡出 0.25s。
 * 動畫只用 Remotion API（useCurrentFrame / interpolate / spring），不用 CSS transition。
 */
export const SceneFrame: React.FC<React.PropsWithChildren<{durationInFrames: number; align?: 'center' | 'top'}>> = ({
  durationInFrames,
  align = 'center',
  children,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {theme} = useTheme();

  const enter = spring({frame, fps, durationInFrames: theme.enterFrames, config: {damping: 200}});
  const exit = interpolate(frame, [durationInFrames - theme.exitFrames, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const opacity = Math.min(enter, exit);
  const translateY = interpolate(enter, [0, 1], [40, 0]);

  return (
    <AbsoluteFill
      style={{
        paddingLeft: theme.pad,
        paddingRight: theme.pad,
        paddingTop: theme.safeTop,
        paddingBottom: 1920 - theme.captionY + 40,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: align === 'center' ? 'center' : 'flex-start',
        opacity,
        transform: `translateY(${translateY}px)`,
        color: theme.text,
        fontFamily: theme.fontDisplay,
        lineHeight: theme.lineHeight,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

/** 列表逐條進場：第 i 條延遲 i*4 frame。 */
export const useStagger = (index: number, gap = 4): {opacity: number; transform: string} => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {theme} = useTheme();
  const s = spring({frame: frame - index * gap, fps, durationInFrames: theme.enterFrames, config: {damping: 200}});
  return {opacity: s, transform: `translateX(${interpolate(s, [0, 1], [24, 0])}px)`};
};
