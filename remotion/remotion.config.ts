import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// GPU 等級不高：CPU render，並行數由 CLI --concurrency 控制（預設 2）。
Config.setChromiumOpenGlRenderer('swangle');
