import type {ShortProps} from './types';

/** Studio 預覽用的預設 props（無音訊／字幕）。實際 render 由 CLI 以 --props 覆蓋。 */
export const sampleProps: ShortProps = {
  fps: 30,
  width: 1080,
  height: 1920,
  durationInFrames: 30 * 16,
  theme: 'neutral',
  kind: 'generic',
  audio: {voice: null, bgm: null, bgmVolume: 0.25, duckVolume: 0.08, voiceRanges: []},
  captions: null,
  scenes: [
    {type: 'title', startFrame: 0, endFrame: 90, props: {title: '本週三件事', subtitle: 'AI 影片工具速覽', date: '2026-09-20'}},
    {type: 'stat', startFrame: 90, endFrame: 180, props: {label: 'Kinocut MCP tools', value: '190+', delta: '+12', deltaPct: '+6.7%', deltaDirection: 'up', unit: ''}},
    {type: 'bullets', startFrame: 180, endFrame: 300, props: {heading: '為什麼重要', items: ['不用猜 ffmpeg 參數', '內建品質檢查', '本機免費']}},
    {
      type: 'table',
      startFrame: 300,
      endFrame: 390,
      props: {heading: '美股三大指數', columns: ['指數', '收盤', '漲跌%'], rows: [['道瓊', '42,100', '+0.5%'], ['標普', '5,700', '-0.2%'], ['那斯達克', null, null]]},
    },
    {type: 'quote', startFrame: 390, endFrame: 450, props: {text: '先把 Kinocut 用起來，再談 Remotion。', source: null}},
    {type: 'disclaimer', startFrame: 450, endFrame: 480, props: {text: '以上內容僅供參考，不構成任何投資建議。'}},
  ],
};
