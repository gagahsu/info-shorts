import {loadFont as loadNotoSansTC} from '@remotion/google-fonts/NotoSansTC';
import {loadFont as loadJetBrainsMono} from '@remotion/google-fonts/JetBrainsMono';

// 中文字型的 unicode-range 切片很多，Remotion 會警告請求數過多；這是 CJK 的常態，關掉警告即可。
const noto = loadNotoSansTC('normal', {
  weights: ['400', '700'],
  subsets: ['chinese-traditional', 'latin'],
  ignoreTooManyRequestsWarning: true,
});
const mono = loadJetBrainsMono('normal', {weights: ['400', '700'], subsets: ['latin']});

export const fontDisplay = noto.fontFamily;
export const fontMono = mono.fontFamily;
export const fontsReady = (): Promise<void> => Promise.all([noto.waitUntilDone(), mono.waitUntilDone()]).then(() => undefined);
