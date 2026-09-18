/** props.json 的型別（由 src/infoshorts/props.py 產生）。時間單位：frame。 */

export type DeltaDirection = 'up' | 'down' | 'flat' | null;
export type ContentKind = 'generic' | 'briefing' | 'company';

export type TitleProps = {title: string; subtitle: string | null; date: string | null};
export type StatProps = {
  label: string;
  value: string | number | null;
  delta: string | number | null;
  deltaDirection: DeltaDirection;
  unit: string;
};
export type BulletsProps = {heading: string; items: string[]};
export type TableProps = {heading: string; columns: string[]; rows: (string | number | null)[][]};
export type QuoteProps = {text: string; source: string | null};
export type DisclaimerProps = {text: string};

export type Scene =
  | {type: 'title'; startFrame: number; endFrame: number; props: TitleProps}
  | {type: 'stat'; startFrame: number; endFrame: number; props: StatProps}
  | {type: 'bullets'; startFrame: number; endFrame: number; props: BulletsProps}
  | {type: 'table'; startFrame: number; endFrame: number; props: TableProps}
  | {type: 'quote'; startFrame: number; endFrame: number; props: QuoteProps}
  | {type: 'disclaimer'; startFrame: number; endFrame: number; props: DisclaimerProps};

export type ShortProps = {
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  theme: string;
  kind: ContentKind;
  audio: {
    voice: string | null;
    bgm: string | null;
    bgmVolume: number;
    /** 旁白進行中 BGM 壓低到的音量 */
    duckVolume: number;
    /** 有旁白的 [startFrame, endFrame] 區間 */
    voiceRanges: number[][];
  };
  captions: string | null;
  scenes: Scene[];
};
